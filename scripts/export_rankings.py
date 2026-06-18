import json
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.database import DatabaseManager
from api.orchestrator import RankingOrchestrator
from embeddings.service import EmbeddingService
from embeddings.models import EmbeddingConfig
from reranking.reranker import CrossEncoderReranker

def seed_sample_data(db: DatabaseManager):
    """Seed sample data from raw CSV files into SQLite database."""
    print("Seeding SQLite database with baseline jobs and candidates...")
    
    # 1. Load sample jobs
    jobs_csv = Path("data/raw/jobs.csv")
    if jobs_csv.exists():
        jobs_df = pd.read_csv(jobs_csv)
        for _, row in jobs_df.iterrows():
            job_data = {
                "id": row["job_id"],
                "title": row["job_title"],
                "raw_text": row["description"],
                "must_have": [s.strip() for s in str(row["required_skills"]).split(",") if s.strip()],
                "nice_to_have": [s.strip() for s in str(row["preferred_skills"]).split(",") if s.strip()] if pd.notna(row["preferred_skills"]) else [],
                "seniority": row["seniority"],
                "location": row["location"]
            }
            db.save_job(job_data)
            
    # 2. Load sample candidates
    candidates_csv = Path("data/raw/candidates.csv")
    if candidates_csv.exists():
        candidates_df = pd.read_csv(candidates_csv)
        for _, row in candidates_df.iterrows():
            cand_data = {
                "id": row["candidate_id"],
                "raw_resume_text": row["resume"],
                "skills_raw": [s.strip() for s in str(row["skills"]).split(",") if s.strip()],
                "experience_years": float(row["years_experience"]) if pd.notna(row["years_experience"]) else 0.0,
                "location": row["location"],
                "github_url": row["github"] if pd.notna(row["github"]) else None,
                "activity_metadata": json.loads(row["activity_metadata"]) if pd.notna(row["activity_metadata"]) and row["activity_metadata"].strip() else {}
            }
            db.save_candidate(cand_data)

def main():
    db = DatabaseManager()
    
    jobs = db.get_all_jobs()
    candidates = db.get_all_candidates()
    
    # Seed if database is empty
    if not jobs or not candidates:
        seed_sample_data(db)
        jobs = db.get_all_jobs()
        candidates = db.get_all_candidates()
        
    print(f"Loaded {len(jobs)} jobs and {len(candidates)} candidates from SQLite.")
    
    # Initialize pipeline modules
    embeddings = EmbeddingService(EmbeddingConfig(dimension=128))
    reranker = CrossEncoderReranker(backend="mock")
    orchestrator = RankingOrchestrator(
        db=db,
        embedding_service=embeddings,
        cross_encoder=reranker,
    )
    
    final_output = {}
    for job in jobs:
        job_id = job["job_id"]
        print(f"Processing candidate rankings for Job ID: {job_id}...")
        rankings = orchestrator.orchestrate_ranking(job_id=job_id, alpha=0.5, top_n=10)
        final_output[job_id] = rankings
        
    # Export results to JSON
    output_path = Path("data/final_rankings.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Custom serializer to handle set/float NaN if any
    def custom_serializer(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
        
    output_path.write_text(json.dumps(final_output, indent=2, default=custom_serializer), encoding="utf-8")
    print(f"Successfully exported final rankings output to: {output_path.resolve()}")

if __name__ == "__main__":
    main()
