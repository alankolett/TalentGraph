import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from preprocessing.cleaning import DataCleaner, flatten_candidate
from preprocessing.loading import DataLoader
from preprocessing.models import RejectedRecord
from preprocessing.validation import (
    JDStructurer,
    SchemaValidator,
    validate_against_schema,
)


@dataclass
class PipelineResult:
    candidates_path: Path
    jobs_path: Path
    rejected_path: Path
    candidate_count: int
    job_count: int
    rejected_count: int


class Phase2Pipeline:
    def __init__(
        self,
        loader: DataLoader | None = None,
        cleaner: DataCleaner | None = None,
        validator: SchemaValidator | None = None,
    ) -> None:
        self.loader = loader or DataLoader()
        self.cleaner = cleaner or DataCleaner()
        self.validator = validator or SchemaValidator()

    def run(self, raw_dir: str | Path, processed_dir: str | Path) -> PipelineResult:
        raw_dir = Path(raw_dir)
        processed_dir = Path(processed_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)

        candidates_source = self.loader.find_dataset_file(raw_dir, "candidates")
        is_jsonl = candidates_source.suffix.lower() in {".jsonl", ".ndjson"}

        jd_docx_path = raw_dir / "job_description.docx"
        has_jd_docx = jd_docx_path.exists()

        if is_jsonl:
            valid_candidates = []
            rejected_records = []

            # Helper to stream JSONL
            def stream_jsonl(path: Path):
                with open(path, "r", encoding="utf-8") as f:
                    for idx, line in enumerate(f):
                        if line.strip():
                            yield idx, json.loads(line)

            for idx, record in stream_jsonl(candidates_source):
                is_valid, reason = validate_against_schema(record)
                if is_valid:
                    flat = flatten_candidate(record)
                    valid_candidates.append(flat)
                else:
                    rejected_records.append(
                        RejectedRecord(
                            source=str(candidates_source),
                            row_index=idx,
                            record_type="candidate",
                            record_id=str(record.get("candidate_id", "")),
                            reason=reason or "schema_validation_failed",
                            payload=record,
                        ).model_dump(mode="json")
                    )

            # Structure the job description from docx or fall back
            valid_jobs = []
            if has_jd_docx:
                structurer = JDStructurer()
                job = structurer.structure_jd(jd_docx_path)

                # Write individual job json to data/processed/job_redrob_senior_ai_engineer.json
                job_json_path = processed_dir / "job_redrob_senior_ai_engineer.json"
                with open(job_json_path, "w", encoding="utf-8") as jf:
                    json.dump(job.model_dump(mode="json"), jf, indent=2, sort_keys=True)

                valid_jobs.append(job.model_dump(mode="json"))
            else:
                jobs_source = self.loader.find_dataset_file(raw_dir, "jobs")
                raw_jobs = self.loader.load_raw_dataset(jobs_source)
                cleaned_jobs = self.cleaner.clean_jobs(raw_jobs)
                deduped_jobs, _ = self.cleaner.deduplicate_jobs(cleaned_jobs)
                valid_jobs_df, _ = self.validator.validate_jobs(deduped_jobs, str(jobs_source))
                valid_jobs = valid_jobs_df.to_dict(orient="records")

            valid_candidates_df = pd.DataFrame(valid_candidates)
            rejected_df = pd.DataFrame(rejected_records)
            valid_jobs_df = pd.DataFrame(valid_jobs)

            candidates_path = processed_dir / "candidates.parquet"
            jobs_path = processed_dir / "jobs.parquet"
            rejected_path = processed_dir / "rejected.parquet"

            self._parquet_ready(valid_candidates_df).to_parquet(candidates_path, index=False)
            valid_jobs_df.to_parquet(jobs_path, index=False)
            self._parquet_ready(rejected_df).to_parquet(rejected_path, index=False)

            return PipelineResult(
                candidates_path=candidates_path,
                jobs_path=jobs_path,
                rejected_path=rejected_path,
                candidate_count=len(valid_candidates_df),
                job_count=len(valid_jobs_df),
                rejected_count=len(rejected_df),
            )
        else:
            # Fallback for the original backward compatibility test suite
            jobs_source = self.loader.find_dataset_file(raw_dir, "jobs")

            raw_candidates = self.loader.load_raw_dataset(candidates_source)
            raw_jobs = self.loader.load_raw_dataset(jobs_source)

            cleaned_candidates = self.cleaner.clean_candidates(raw_candidates)
            cleaned_jobs = self.cleaner.clean_jobs(raw_jobs)

            deduped_candidates, duplicate_candidates = self.cleaner.deduplicate_candidates(
                cleaned_candidates
            )
            deduped_jobs, duplicate_jobs = self.cleaner.deduplicate_jobs(cleaned_jobs)

            valid_candidates, rejected_candidates = self.validator.validate_candidates(
                deduped_candidates, str(candidates_source)
            )
            valid_jobs, rejected_jobs = self.validator.validate_jobs(deduped_jobs, str(jobs_source))

            rejected = pd.concat(
                [
                    self._dedupe_rejections(
                        duplicate_candidates, "candidate", str(candidates_source)
                    ),
                    self._dedupe_rejections(duplicate_jobs, "job", str(jobs_source)),
                    rejected_candidates,
                    rejected_jobs,
                ],
                ignore_index=True,
            )

            candidates_path = processed_dir / "candidates.parquet"
            jobs_path = processed_dir / "jobs.parquet"
            rejected_path = processed_dir / "rejected.parquet"

            self._parquet_ready(valid_candidates).to_parquet(candidates_path, index=False)
            valid_jobs.to_parquet(jobs_path, index=False)
            self._parquet_ready(rejected).to_parquet(rejected_path, index=False)

            return PipelineResult(
                candidates_path=candidates_path,
                jobs_path=jobs_path,
                rejected_path=rejected_path,
                candidate_count=len(valid_candidates),
                job_count=len(valid_jobs),
                rejected_count=len(rejected),
            )

    def _dedupe_rejections(self, df: pd.DataFrame, record_type: str, source: str) -> pd.DataFrame:
        rows = []
        for _, row in df.iterrows():
            payload = row.get("payload", {})
            rows.append(
                RejectedRecord(
                    source=source,
                    row_index=int(row.get("row_index", -1)),
                    record_type=record_type,
                    record_id=str(payload.get("id")) if payload.get("id") else None,
                    reason=str(row.get("reason", "duplicate")),
                    payload=payload,
                ).model_dump(mode="json")
            )
        return pd.DataFrame(rows)

    def _parquet_ready(self, df: pd.DataFrame) -> pd.DataFrame:
        prepared = df.copy()
        for column in prepared.columns:
            if prepared[column].map(lambda value: isinstance(value, dict)).any():
                prepared[column] = prepared[column].map(self._json_dump)
        return prepared

    def _json_dump(self, value: Any) -> str:
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True)
        return str(value)
