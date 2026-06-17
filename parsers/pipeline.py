import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from parsers.jobs import JDStructuredExtractor
from parsers.models import ParsedJob, ParsedResume
from parsers.resumes import ResumeParser
from preprocessing.models import CandidateRecord, JobRecord


@dataclass
class Phase3Result:
    parsed_resumes_path: Path
    parsed_jobs_path: Path
    resume_count: int
    job_count: int


class Phase3Pipeline:
    def __init__(
        self,
        resume_parser: ResumeParser | None = None,
        job_extractor: JDStructuredExtractor | None = None,
    ) -> None:
        self.resume_parser = resume_parser or ResumeParser()
        self.job_extractor = job_extractor or JDStructuredExtractor()

    def run(self, processed_dir: str | Path, output_dir: str | Path | None = None) -> Phase3Result:
        processed_dir = Path(processed_dir)
        output_dir = Path(output_dir) if output_dir else processed_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        candidates = pd.read_parquet(processed_dir / "candidates.parquet")
        jobs = pd.read_parquet(processed_dir / "jobs.parquet")

        parsed_resumes = [
            self.resume_parser.parse(CandidateRecord.model_validate(row))
            for row in candidates.to_dict(orient="records")
        ]
        parsed_jobs = [
            self._parse_job(JobRecord.model_validate(row)) for row in jobs.to_dict(orient="records")
        ]

        resumes_path = output_dir / "parsed_resumes.jsonl"
        jobs_path = output_dir / "parsed_jobs.jsonl"
        self._write_jsonl(resumes_path, parsed_resumes)
        self._write_jsonl(jobs_path, parsed_jobs)

        return Phase3Result(
            parsed_resumes_path=resumes_path,
            parsed_jobs_path=jobs_path,
            resume_count=len(parsed_resumes),
            job_count=len(parsed_jobs),
        )

    def _parse_job(self, job: JobRecord) -> ParsedJob:
        return self.job_extractor.llm_extract_job_requirements(
            job_id=job.id,
            title=job.title,
            jd_text=job.raw_description,
            must_have_skills=job.must_have_skills,
            nice_to_have_skills=job.nice_to_have_skills,
            seniority=job.seniority,
            location=job.location,
        )

    def _write_jsonl(self, path: Path, rows: list[ParsedResume] | list[ParsedJob]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row.model_dump(mode="json"), sort_keys=True) + "\n")
