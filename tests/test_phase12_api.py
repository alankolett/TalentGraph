import pytest
from fastapi.testclient import TestClient

from api.database import DatabaseManager
from api.main import app


@pytest.fixture
def client(tmp_path):
    """Fixture initializing TestClient and isolating the database path."""
    db_file = tmp_path / "test_talentgraph.sqlite3"
    with TestClient(app) as client:
        # Override the database path dynamically on startup singletons
        client.app.state.db = DatabaseManager(db_path=db_file)
        client.app.state.orchestrator.db = client.app.state.db
        yield client


def test_jobs_endpoint_crud(client) -> None:
    job_payload = {
        "id": "test_j1",
        "title": "Backend Dev",
        "raw_description": "We need a senior python developer with fastapi experience.",
        "must_have_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": ["Qdrant"],
        "seniority": "senior",
        "location": "Remote",
    }

    # Add job
    response = client.post("/jobs", json=job_payload)
    assert response.status_code == 201
    assert response.json() == {"status": "success", "job_id": "test_j1"}

    # Fetch job from SQLite directly via DB manager to confirm persistence
    job = client.app.state.db.get_job("test_j1")
    assert job is not None
    assert job["title"] == "Backend Dev"
    assert "FastAPI" in job["must_have"]


def test_candidates_bulk_upload_endpoint(client) -> None:
    candidates_payload = [
        {
            "id": "test_c1",
            "raw_resume_text": "Senior Backend Developer. Python and FastAPI expert.",
            "skills_raw": ["Python", "FastAPI"],
            "experience_years": 6.0,
            "location": "Remote",
            "github_url": "https://github.com/c1",
        }
    ]

    response = client.post("/candidates/bulk-upload", json=candidates_payload)
    assert response.status_code == 201
    assert response.json() == {"status": "success", "count": 1}

    # Verify retrieval
    response = client.get("/candidates/test_c1")
    assert response.status_code == 200
    assert response.json()["candidate"]["id"] == "test_c1"
    assert response.json()["candidate"]["experience_years"] == 6.0


def test_rank_endpoint_happy_path_and_not_found_handling(client) -> None:
    # 1. Ranking a nonexistent job returns 404
    response = client.post("/rank/missing_job")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

    # Ingest job
    job_payload = {
        "id": "test_j1",
        "title": "Backend Dev",
        "raw_description": "We need a senior python developer with fastapi experience.",
        "must_have_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": ["Qdrant"],
        "seniority": "senior",
        "location": "Remote",
    }
    client.post("/jobs", json=job_payload)

    # 2. Ranking before candidates are ingested returns 404
    response = client.post("/rank/test_j1")
    assert response.status_code == 404
    assert "No candidates ingested" in response.json()["detail"]

    # Ingest candidates
    candidates_payload = [
        {
            "id": "test_c1",
            "raw_resume_text": "Senior Backend Developer. Python and FastAPI expert.",
            "skills_raw": ["Python", "FastAPI"],
            "experience_years": 6.0,
            "location": "Remote",
            "github_url": "https://github.com/c1",
        }
    ]
    client.post("/candidates/bulk-upload", json=candidates_payload)

    # 3. Successful ranking
    response = client.post("/rank/test_j1")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["candidate_id"] == "test_c1"
    assert results[0]["rank"] == 1
    assert len(results[0]["matched_points"]) > 0

    # 4. Fetch results via GET ranking endpoint
    response = client.get("/rank/test_j1/results")
    assert response.status_code == 200
    db_results = response.json()["results"]
    assert len(db_results) == 1
    assert db_results[0]["candidate_id"] == "test_c1"
    assert db_results[0]["rank"] == 1
