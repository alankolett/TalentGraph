import json

import pandas as pd

from parsers.pipeline import Phase3Pipeline


def test_phase3_pipeline_writes_schema_valid_jsonl(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    pd.DataFrame(
        [
            {
                "id": "c1",
                "raw_resume_text": (
                    "Skills\nPython, SQL\nExperience\n" "Engineer at Acme, 2020 - 2021\nBuilt APIs."
                ),
                "skills_raw": ["Python", "SQL"],
                "experience_years": 2.0,
                "education": None,
                "location": None,
                "github_url": None,
                "activity_metadata": "{}",
            }
        ]
    ).to_parquet(processed_dir / "candidates.parquet", index=False)
    pd.DataFrame(
        [
            {
                "id": "j1",
                "title": "Senior Backend Engineer",
                "raw_description": "Own backend services. Required skills: Python, FastAPI.",
                "must_have_skills": ["Python", "FastAPI"],
                "nice_to_have_skills": [],
                "seniority": "senior",
                "location": None,
            }
        ]
    ).to_parquet(processed_dir / "jobs.parquet", index=False)

    result = Phase3Pipeline().run(processed_dir)

    resume = json.loads(result.parsed_resumes_path.read_text(encoding="utf-8").splitlines()[0])
    job = json.loads(result.parsed_jobs_path.read_text(encoding="utf-8").splitlines()[0])

    assert result.resume_count == 1
    assert result.job_count == 1
    assert resume["candidate_id"] == "c1"
    assert resume["experience_entries"]
    assert job["job_id"] == "j1"
    assert job["must_have"] == ["Python", "FastAPI"]
