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

    candidates = [
        {
            "candidate_id": f"c{i}",
            "resume": f"Candidate {i} built production systems with skill family {i}.",
            "skills": f"Python, Skill{i}",
            "years_experience": i,
        }
        for i in range(1, 11)
    ]
    candidates.extend(
        [
            {"candidate_id": "c11", "resume": "", "skills": "SQL"},
            {
                "candidate_id": "c1",
                "resume": "Candidate 1 built production systems with skill family 1.",
                "skills": "Python, Skill1",
            },
        ]
    )
    pd.DataFrame(candidates).to_csv(raw_dir / "candidates.csv", index=False)

    jobs = [
        {
            "job_id": f"j{i}",
            "job_title": f"Engineer {i}",
            "description": (
                f"Own service area {i}, build robust APIs, and improve ranking workflows."
            ),
            "required_skills": "Python, FastAPI",
            "preferred_skills": "Qdrant",
        }
        for i in range(1, 8)
    ]
    jobs.append({"job_id": "j8", "job_title": "Tiny JD", "description": "Too short"})
    pd.DataFrame(jobs).to_csv(raw_dir / "jobs.csv", index=False)

    result = Phase2Pipeline().run(raw_dir, processed_dir)

    candidates = pd.read_parquet(result.candidates_path)
    jobs = pd.read_parquet(result.jobs_path)
    rejected = pd.read_parquet(result.rejected_path)

    assert len(candidates) + len(jobs) + len(rejected) == 20
    assert result.candidate_count == 10
    assert result.job_count == 7
    assert result.rejected_count == 3
    assert list(candidates["id"])[:2] == ["c1", "c2"]
    assert list(jobs["id"])[:2] == ["j1", "j2"]
    assert set(rejected["record_type"]) == {"candidate", "job"}
