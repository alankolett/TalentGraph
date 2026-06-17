import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from parsers.models import ParsedJob, ParsedResume


@dataclass
class Phase5Result:
    candidate_embeddings_path: Path
    job_embeddings_path: Path
    indexed_count: int
    candidate_count: int
    job_count: int


class Phase5Pipeline:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        indexer: QdrantIndexer | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.indexer = indexer or QdrantIndexer(vector_size=self.embedding_service.config.dimension)

    def run(
        self,
        processed_dir: str | Path,
        embeddings_dir: str | Path,
        candidate_metadata_path: str | Path | None = None,
    ) -> Phase5Result:
        processed_dir = Path(processed_dir)
        embeddings_dir = Path(embeddings_dir)
        embeddings_dir.mkdir(parents=True, exist_ok=True)

        resumes = self._read_jsonl(processed_dir / "parsed_resumes.jsonl", ParsedResume)
        jobs = self._read_jsonl(processed_dir / "parsed_jobs.jsonl", ParsedJob)
        if not resumes:
            raise FileNotFoundError(
                "No parsed resumes found. Run `python scripts/process_phase3.py "
                "--processed-dir data/processed` before Phase 5."
            )
        metadata = self._load_candidate_metadata(
            candidate_metadata_path or processed_dir / "candidates.parquet"
        )

        candidate_points = [
            CandidateVectorPoint(
                id=resume.candidate_id,
                vector=self.embedding_service.embed_candidate(resume),
                payload=self._candidate_payload(resume, metadata.get(resume.candidate_id, {})),
            )
            for resume in resumes
        ]
        job_rows = [
            {
                "id": job.job_id,
                "vector": self.embedding_service.embed_job(job),
                "payload": json.dumps(
                    {
                        "title": job.title,
                        "seniority": job.seniority,
                        "must_have": job.must_have,
                        "nice_to_have": job.nice_to_have,
                    },
                    sort_keys=True,
                ),
            }
            for job in jobs
        ]

        self.indexer.upsert_candidates(candidate_points)

        candidate_embeddings_path = embeddings_dir / "candidate_embeddings.parquet"
        job_embeddings_path = embeddings_dir / "job_embeddings.parquet"
        pd.DataFrame(
            [
                {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": json.dumps(point.payload, sort_keys=True),
                }
                for point in candidate_points
            ]
        ).to_parquet(candidate_embeddings_path, index=False)
        pd.DataFrame(job_rows).to_parquet(job_embeddings_path, index=False)

        return Phase5Result(
            candidate_embeddings_path=candidate_embeddings_path,
            job_embeddings_path=job_embeddings_path,
            indexed_count=self.indexer.count(),
            candidate_count=len(candidate_points),
            job_count=len(job_rows),
        )

    @classmethod
    def from_config(cls, config: EmbeddingConfig) -> "Phase5Pipeline":
        service = EmbeddingService(config)
        return cls(service, QdrantIndexer(vector_size=config.dimension))

    def _read_jsonl(self, path: Path, model: type[ParsedResume] | type[ParsedJob]):
        rows = []
        if not path.exists():
            return rows
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(model.model_validate(json.loads(line)))
        return rows

    def _load_candidate_metadata(self, path: str | Path) -> dict[str, dict[str, Any]]:
        path = Path(path)
        if not path.exists():
            return {}
        df = pd.read_parquet(path)
        return {str(row["id"]): row for row in df.to_dict(orient="records")}

    def _candidate_payload(self, resume: ParsedResume, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "skills": resume.raw_skills,
            "seniority": metadata.get("seniority"),
            "location": metadata.get("location"),
            "experience_years": metadata.get("experience_years"),
            "kg_node_id": f"candidate:{resume.candidate_id}",
        }
