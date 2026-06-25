import json
import sqlite3
from pathlib import Path
from typing import Any

from common.settings import get_settings


class DatabaseManager:
    """Manages SQLite storage for Jobs, Candidates, and Ranked results."""

    def __init__(self, db_path: Path | None = None) -> None:
        settings = get_settings()
        self.db_path = db_path or settings.sqlite_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    seniority TEXT,
                    location TEXT,
                    must_have TEXT,
                    nice_to_have TEXT,
                    responsibilities TEXT,
                    raw_text TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    raw_resume_text TEXT NOT NULL,
                    skills_raw TEXT,
                    experience_years REAL,
                    education TEXT,
                    location TEXT,
                    github_url TEXT,
                    activity_metadata TEXT,
                    skills TEXT,
                    career_history TEXT
                )
                """
            )
            # Migration check: try adding new columns to an existing table
            try:
                conn.execute("ALTER TABLE candidates ADD COLUMN skills TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE candidates ADD COLUMN career_history TEXT")
            except sqlite3.OperationalError:
                pass

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rankings (
                    job_id TEXT,
                    candidate_id TEXT,
                    rank INTEGER NOT NULL,
                    final_score REAL NOT NULL,
                    tags TEXT,
                    narrative TEXT NOT NULL,
                    matched_points TEXT,
                    missing_points TEXT,
                    features TEXT,
                    PRIMARY KEY (job_id, candidate_id)
                )
                """
            )
            conn.commit()

    def save_job(self, job: dict[str, Any]) -> None:
        job_id = job.get("job_id") or job.get("id")
        raw_text = job.get("raw_text") or job.get("raw_description") or ""
        must_have = job.get("must_have") or job.get("must_have_skills") or []
        nice_to_have = job.get("nice_to_have") or job.get("nice_to_have_skills") or []
        responsibilities = job.get("responsibilities") or []

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (id, title, seniority, location, must_have, nice_to_have, responsibilities, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job["title"],
                    job.get("seniority"),
                    job.get("location"),
                    json.dumps(must_have),
                    json.dumps(nice_to_have),
                    json.dumps(responsibilities),
                    raw_text,
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return {
                "job_id": row["id"],
                "title": row["title"],
                "seniority": row["seniority"],
                "location": row["location"],
                "must_have": json.loads(row["must_have"]),
                "nice_to_have": json.loads(row["nice_to_have"]),
                "responsibilities": json.loads(row["responsibilities"]),
                "raw_text": row["raw_text"],
            }

    def get_all_jobs(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs").fetchall()
            return [
                {
                    "job_id": row["id"],
                    "title": row["title"],
                    "seniority": row["seniority"],
                    "location": row["location"],
                    "must_have": json.loads(row["must_have"]),
                    "nice_to_have": json.loads(row["nice_to_have"]),
                    "responsibilities": json.loads(row["responsibilities"]),
                    "raw_text": row["raw_text"],
                }
                for row in rows
            ]

    def save_candidate(self, cand: dict[str, Any]) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates (
                    id, raw_resume_text, skills_raw, experience_years,
                    education, location, github_url, activity_metadata,
                    skills, career_history
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cand["id"],
                    cand["raw_resume_text"],
                    json.dumps(cand.get("skills_raw", [])),
                    cand.get("experience_years"),
                    cand.get("education"),
                    cand.get("location"),
                    cand.get("github_url"),
                    json.dumps(cand.get("activity_metadata", {})),
                    json.dumps(cand.get("skills", [])),
                    json.dumps(cand.get("career_history", [])),
                ),
            )
            conn.commit()

    def get_candidate(self, cand_id: str) -> dict[str, Any] | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cand_id,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "raw_resume_text": row["raw_resume_text"],
                "skills_raw": json.loads(row["skills_raw"]) if row["skills_raw"] else [],
                "experience_years": row["experience_years"],
                "education": row["education"],
                "location": row["location"],
                "github_url": row["github_url"],
                "activity_metadata": (
                    json.loads(row["activity_metadata"])
                    if row["activity_metadata"]
                    else {}
                ),
                "skills": json.loads(row["skills"]) if row["skills"] else [],
                "career_history": (
                    json.loads(row["career_history"])
                    if row["career_history"]
                    else []
                ),
            }

    def get_all_candidates(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM candidates").fetchall()
            return [
                {
                    "id": row["id"],
                    "raw_resume_text": row["raw_resume_text"],
                    "skills_raw": json.loads(row["skills_raw"]) if row["skills_raw"] else [],
                    "experience_years": row["experience_years"],
                    "education": row["education"],
                    "location": row["location"],
                    "github_url": row["github_url"],
                    "activity_metadata": (
                        json.loads(row["activity_metadata"])
                        if row["activity_metadata"]
                        else {}
                    ),
                    "skills": json.loads(row["skills"]) if row["skills"] else [],
                    "career_history": (
                        json.loads(row["career_history"])
                        if row["career_history"]
                        else []
                    ),
                }
                for row in rows
            ]

    def save_rankings(self, job_id: str, rankings: list[dict[str, Any]]) -> None:
        with self.get_connection() as conn:
            # Delete older rankings for the same job first
            conn.execute("DELETE FROM rankings WHERE job_id = ?", (job_id,))
            for r in rankings:
                conn.execute(
                    """
                    INSERT INTO rankings (job_id, candidate_id, rank, final_score, tags, narrative, matched_points, missing_points, features)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        r["candidate_id"],
                        r["rank"],
                        r["final_score"],
                        json.dumps(r.get("tags", [])),
                        r["narrative"],
                        json.dumps(r.get("matched_points", [])),
                        json.dumps(r.get("missing_points", [])),
                        json.dumps(r.get("features", {})),
                    ),
                )
            conn.commit()

    def get_rankings(self, job_id: str) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM rankings WHERE job_id = ? ORDER BY rank ASC", (job_id,)
            ).fetchall()
            return [
                {
                    "candidate_id": row["candidate_id"],
                    "rank": row["rank"],
                    "final_score": row["final_score"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "narrative": row["narrative"],
                    "matched_points": json.loads(row["matched_points"]) if row["matched_points"] else [],
                    "missing_points": json.loads(row["missing_points"]) if row["missing_points"] else [],
                    "features": json.loads(row["features"]) if row["features"] else {},
                }
                for row in rows
            ]
