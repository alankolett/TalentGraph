import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd


def main() -> None:
    parser = ArgumentParser(description="Create small sample raw datasets for local pipeline runs.")
    parser.add_argument(
        "--raw-dir", default="data/raw", help="Directory to write sample CSV files."
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "resume": (
                    "Summary\nBackend engineer focused on ranking systems.\n"
                    "Skills\nPython, FastAPI, Qdrant, SQL\n"
                    "Experience\nSenior Backend Engineer at Acme, Jan 2020 - Mar 2023\n"
                    "- Built candidate ranking APIs and vector search workflows."
                ),
                "skills": "Python, FastAPI, Qdrant, SQL",
                "years_experience": 6,
                "location": "Remote",
                "github": "https://github.com/example-c1",
            },
            {
                "candidate_id": "c2",
                "resume": (
                    "Summary\nData engineer with strong ETL and analytics experience.\n"
                    "Skills\nPython, SQL, Airflow, Pandas\n"
                    "Experience\nData Engineer at Beta, 2019 - 2022\n"
                    "- Shipped data pipelines and reporting models."
                ),
                "skills": "Python, SQL, Airflow, Pandas",
                "years_experience": 5,
                "location": "Bengaluru",
                "github": "https://github.com/example-c2",
            },
            {
                "candidate_id": "c3",
                "resume": (
                    "Summary\nFrontend engineer building recruiter-facing dashboards.\n"
                    "Skills\nReact, TypeScript, CSS, APIs\n"
                    "Experience\nFrontend Engineer at Gamma, 2021 - Present\n"
                    "- Built high-signal workflow interfaces."
                ),
                "skills": "React, TypeScript, CSS, APIs",
                "years_experience": 4,
                "location": "Pune",
                "github": "https://github.com/example-c3",
            },
        ]
    )
    jobs = pd.DataFrame(
        [
            {
                "job_id": "j1",
                "job_title": "Senior Backend Engineer",
                "description": (
                    "Own candidate ranking APIs and semantic search workflows. "
                    "Required skills: Python, FastAPI, Qdrant. Preferred skills: SQL."
                ),
                "required_skills": "Python, FastAPI, Qdrant",
                "preferred_skills": "SQL",
                "seniority": "senior",
                "location": "Remote",
            },
            {
                "job_id": "j2",
                "job_title": "Data Engineer",
                "description": (
                    "Build robust ETL pipelines and analytics datasets for recruiting intelligence. "
                    "Required skills: Python, SQL. Preferred skills: Airflow, Pandas."
                ),
                "required_skills": "Python, SQL",
                "preferred_skills": "Airflow, Pandas",
                "seniority": "mid",
                "location": "Bengaluru",
            },
        ]
    )

    candidates.to_csv(raw_dir / "candidates.csv", index=False)
    jobs.to_csv(raw_dir / "jobs.csv", index=False)
    print(f"wrote {raw_dir / 'candidates.csv'}")
    print(f"wrote {raw_dir / 'jobs.csv'}")


if __name__ == "__main__":
    main()
