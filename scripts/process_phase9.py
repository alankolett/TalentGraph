import json
import sys
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from embeddings.text import build_candidate_text, build_job_text
from feature_engineering.behavioral import BehavioralProfile
from knowledge_graph.graph import KnowledgeGraphBuilder
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.features import FeatureBuilder
from ranking_engine.scoring import ScoringEngine
from reranking.reranker import CrossEncoderReranker, ScoreBlender
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever


def main() -> None:
    parser = ArgumentParser(description="Run Phase 9 Cross-Encoder Reranking.")
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
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Blending ratio between initial composite score and reranker score.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of final candidates to output.",
    )
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    graph_dir = Path(args.graph_dir)
    embeddings_dir = Path(args.embeddings_dir)

    # 1. Load intermediate files
    resumes = {}
    resumes_path = processed_dir / "parsed_resumes.jsonl"
    if resumes_path.exists():
        for line in resumes_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                res = ParsedResume.model_validate(json.loads(line))
                resumes[res.candidate_id] = res

    candidates_meta = {}
    meta_path = processed_dir / "candidates.parquet"
    if meta_path.exists():
        df = pd.read_parquet(meta_path)
        for _, row in df.iterrows():
            candidates_meta[str(row["id"])] = float(row["experience_years"]) if pd.notna(row["experience_years"]) else 0.0

    behav_profiles = {}
    behav_path = processed_dir / "behavioral_profiles.jsonl"
    if behav_path.exists():
        for line in behav_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                prof = BehavioralProfile.model_validate(json.loads(line))
                behav_profiles[prof.candidate_id] = prof

    kg_builder = KnowledgeGraphBuilder()
    kg_path = graph_dir / "candidate_kg.gpickle"
    kg = kg_builder.load_graph(kg_path) if kg_path.exists() else None

    bm25 = BM25Index()
    bm25.build_bm25_index(list(resumes.values()))

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

    # 2. Setup systems
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

    reranker = CrossEncoderReranker(backend="mock")
    blender = ScoreBlender()

    # 3. Load jobs & run ranking
    jobs_path = processed_dir / "parsed_jobs.jsonl"
    jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jobs.append(ParsedJob.model_validate(json.loads(line)))

    print("\n================== TalentGraph Reranking & Score Blending ==================")
    for job in jobs:
        print(f"\nJob ID: {job.job_id} | Title: {job.title} | Seniority: {job.seniority} | Location: {job.location}")

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

            f_vector = feature_builder.build_feature_vector(
                parsed_resume=resume,
                job=job,
                kg=kg,
                behavioral_profile=behav_profiles.get(cid),
                retrieval_scores={"dense": match.dense_score, "bm25": match.bm25_score},
                experience_years=candidates_meta.get(cid),
            )
            scored = scoring_engine.score_candidate(cid, f_vector)
            scored_candidates.append(scored)

        # Sort by initial score descending to assign original ranks
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)
        original_rank_map = {sc.candidate_id: idx for idx, sc in enumerate(scored_candidates, start=1)}

        # Build query-candidate pairs for cross-encoder reranker
        job_text = build_job_text(job)
        cand_ids = [sc.candidate_id for sc in scored_candidates]
        cand_texts = [build_candidate_text(resumes[cid]) for cid in cand_ids]

        pairs = reranker.build_reranker_pairs(job_text, cand_texts)
        rerank_scores = reranker.rerank(pairs)

        # Blend scores
        reranked_results = []
        for idx, sc in enumerate(scored_candidates):
            cid = sc.candidate_id
            ce_score = rerank_scores[idx]
            blended_score = blender.blend_scores(sc.final_score, ce_score, alpha=args.alpha)
            reranked_results.append({
                "candidate_id": cid,
                "initial_score": sc.final_score,
                "reranker_score": ce_score,
                "blended_score": blended_score,
                "original_rank": original_rank_map[cid],
            })

        # Sort by blended score descending
        reranked_results.sort(key=lambda x: x["blended_score"], reverse=True)

        for idx, item in enumerate(reranked_results[:args.top_n], start=1):
            cid = item["candidate_id"]
            delta = item["blended_score"] - item["initial_score"]
            print(
                f"  Rank {idx}. Candidate ID: {cid} | "
                f"Blended Score: {item['blended_score']:.4f} | "
                f"Initial Rank: {item['original_rank']} -> New Rank: {idx} | "
                f"Score Delta: {delta:+.4f} (Reranker: {item['reranker_score']:.3f})"
            )


if __name__ == "__main__":
    main()
