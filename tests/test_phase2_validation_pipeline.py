import pandas as pd

from preprocessing.pipeline import Phase2Pipeline
from preprocessing.validation import SchemaValidator


def test_schema_validator_quarantines_invalid_rows() -> None:
    validator = SchemaValidator()
    candidates = pd.DataFrame(
        [
            {
                "id": "c1",
                "raw_resume_text": "Python engineer with data systems experience.",
                "skills_raw": ["Python"],
                "experience_years": 4,
                "education": None,
                "location": None,
                "github_url": None,
                "activity_metadata": {},
            },
            {
                "id": "c2",
                "raw_resume_text": "",
                "skills_raw": [],
                "experience_years": None,
                "education": None,
                "location": None,
                "github_url": None,
                "activity_metadata": {},
            },
        ]
    )

    accepted, rejected = validator.validate_candidates(candidates, "synthetic")

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected.iloc[0]["record_id"] == "c2"
    assert "raw_resume_text" in rejected.iloc[0]["reason"]


def test_phase2_pipeline_writes_valid_parquet_outputs(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "resume": "Python engineer with ML systems and API experience.",
                "skills": "Python, FastAPI",
                "years_experience": 5,
                "github": "https://github.com/example",
            },
            {
                "candidate_id": "c2",
                "resume": "",
                "skills": "SQL",
            },
            {
                "candidate_id": "c1",
                "resume": "Python engineer with ML systems and API experience.",
                "skills": "Python, FastAPI",
            },
        ]
    ).to_csv(raw_dir / "candidates.csv", index=False)

    pd.DataFrame(
        [
            {
                "job_id": "j1",
                "job_title": "Backend Engineer",
                "description": "Build robust APIs and data workflows for ranking candidates.",
                "required_skills": "Python, FastAPI",
                "preferred_skills": "Qdrant",
            },
            {
                "job_id": "j2",
                "job_title": "Tiny JD",
                "description": "Too short",
            },
        ]
    ).to_csv(raw_dir / "jobs.csv", index=False)

    result = Phase2Pipeline().run(raw_dir, processed_dir)

    candidates = pd.read_parquet(result.candidates_path)
    jobs = pd.read_parquet(result.jobs_path)
    rejected = pd.read_parquet(result.rejected_path)

    assert result.candidate_count == 1
    assert result.job_count == 1
    assert result.rejected_count == 3
    assert list(candidates["id"]) == ["c1"]
    assert list(jobs["id"]) == ["j1"]
    assert set(rejected["record_type"]) == {"candidate", "job"}
