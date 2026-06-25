import json
import sys
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from feature_engineering.behavioral import BehavioralProfile
from knowledge_graph.graph import KnowledgeGraphBuilder
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.features import FeatureBuilder
from ranking_engine.scoring import ScoringEngine
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever


def main() -> None:
    parser = ArgumentParser(description="Run Phase 8 Ranking Engine (Feature Building & Composite Scoring).")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing cleaned datasets.",
    )
    parser.add_argument(
        "--graph-dir",
        default="data/knowledge_graph",
        help="Directory containing Knowledge Graph.",
    )
    parser.add_argument(
        "--embeddings-dir",
        default="data/embeddings",
        help="Directory containing embeddings.",
    )
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    graph_dir = Path(args.graph_dir)
    embeddings_dir = Path(args.embeddings_dir)

    # 1. Load intermediate files
    # Resumes
    resumes = {}
    resumes_path = processed_dir / "parsed_resumes.jsonl"
    if resumes_path.exists():
        for line in resumes_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                res = ParsedResume.model_validate(json.loads(line))
                resumes[res.candidate_id] = res

    # Metadata (experience years and other fields)
    candidates_meta = {}
    candidates_meta_dicts = {}
    meta_path = processed_dir / "candidates.parquet"
    if meta_path.exists():
        df = pd.read_parquet(meta_path)
        for _, row in df.iterrows():
            cid = str(row["id"])
            candidates_meta[cid] = float(row["experience_years"]) if pd.notna(row["experience_years"]) else 0.0

            # Parse activity_metadata if it is a JSON string
            act_meta = {}
            if "activity_metadata" in row and pd.notna(row["activity_metadata"]):
                val = row["activity_metadata"]
                if isinstance(val, str):
                    try:
                        act_meta = json.loads(val)
                    except Exception:
                        pass
                elif isinstance(val, dict):
                    act_meta = val

            # Also parse redrob_signals if present
            if not act_meta and "redrob_signals" in row and pd.notna(row["redrob_signals"]):
                val = row["redrob_signals"]
                if isinstance(val, str):
                    try:
                        act_meta = json.loads(val)
                    except Exception:
                        pass
                elif isinstance(val, dict):
                    act_meta = val

            # Construct cand_meta
            candidates_meta_dicts[cid] = {
                "location": row.get("location") if pd.notna(row.get("location")) else "",
                "willing_to_relocate": act_meta.get("willing_to_relocate"),
                "notice_period_days": act_meta.get("notice_period_days"),
                "github_activity_score": act_meta.get("github_activity_score", -1),
                "total_career_months": float(row.get("total_career_months")) if pd.notna(row.get("total_career_months")) else 0.0,
                "num_employers": int(row.get("num_employers")) if pd.notna(row.get("num_employers")) else 0,
                "github_url": row.get("github_url") if pd.notna(row.get("github_url")) else None,
            }

    # Behavioral Profiles
    behav_profiles = {}
    behav_path = processed_dir / "behavioral_profiles.jsonl"
    if behav_path.exists():
        for line in behav_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                prof = BehavioralProfile.model_validate(json.loads(line))
                behav_profiles[prof.candidate_id] = prof

    # Knowledge Graph
    kg_builder = KnowledgeGraphBuilder()
    kg_path = graph_dir / "candidate_kg.gpickle"
    kg = kg_builder.load_graph(kg_path) if kg_path.exists() else None

    # BM25 Index
    bm25 = BM25Index()
    bm25.build_bm25_index(list(resumes.values()))

    # Qdrant Indexer
    indexer = QdrantIndexer(vector_size=128)
    embeddings_path = embeddings_dir / "candidate_embeddings.parquet"
    if embeddings_path.exists():
        df = pd.read_parquet(embeddings_path)
        points = []
        for _, row in df.iterrows():
            points.append(
                CandidateVectorPoint(
                    id=str(row["id"]),
                    vector=list(row["vector"]),
                    payload=json.loads(row["payload"]),
                )
            )
        indexer.upsert_candidates(points)

    # 2. Setup retrievers & scoring engine
    service = EmbeddingService(EmbeddingConfig(dimension=128))
    dense = DenseRetriever(indexer)
    metadata_filter = MetadataFilter()
    hybrid = HybridRetriever(
        bm25_index=bm25,
        dense_retriever=dense,
        metadata_filter=metadata_filter,
        embedding_service=service,
    )

    feature_builder = FeatureBuilder()
    scoring_engine = ScoringEngine()

    # 3. Load jobs & run ranking
    jobs_path = processed_dir / "parsed_jobs.jsonl"
    jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jobs.append(ParsedJob.model_validate(json.loads(line)))

    print("\n================== TalentGraph Final Ranking Results ==================")
    for job in jobs:
        print(f"\nJob ID: {job.job_id} | Title: {job.title} | Seniority: {job.seniority} | Location: {job.location}")

        # Retrieve candidate shortlist
        shortlist = hybrid.retrieve_hybrid(job, top_k=100)
        if not shortlist:
            print("  No candidate matches pass hard filters.")
            continue

        scored_candidates = []
        for match in shortlist:
            cid = match.candidate_id
            resume = resumes.get(cid)
            if not resume:
                continue

            retrieval_scores = {
                "dense": match.dense_score,
                "bm25": match.bm25_score,
            }

            # Build feature vector
            f_vector = feature_builder.build_feature_vector(
                parsed_resume=resume,
                job=job,
                kg=kg,
                behavioral_profile=behav_profiles.get(cid),
                retrieval_scores=retrieval_scores,
                experience_years=candidates_meta.get(cid),
                metadata=candidates_meta_dicts.get(cid),
            )

            # Score candidate
            scored = scoring_engine.score_candidate(cid, f_vector)
            scored_candidates.append(scored)

        # Sort by final score descending
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)

        for idx, sc in enumerate(scored_candidates, start=1):
            print(f"\n  Rank {idx}. Candidate ID: {sc.candidate_id} | COMPOSITE SCORE: {sc.final_score:.4f}")
            print("    Score Breakdown:")
            for feature_name, weighted_val in sc.score_breakdown.items():
                raw_val = getattr(sc.features, feature_name)
                if isinstance(raw_val, float | int) and not isinstance(raw_val, bool):
                    raw_str = f"{raw_val:.3f}" if raw_val is not None else "None"
                else:
                    raw_str = str(raw_val)
                print(f"      - {feature_name:<20}: {weighted_val:.4f} (raw value: {raw_str})")


if __name__ == "__main__":
    main()
