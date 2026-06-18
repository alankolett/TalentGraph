import json
import sys
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from evaluation.harness import EvaluationHarness
from evaluation.models import RelevanceJudgment
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
    parser = ArgumentParser(description="Run Phase 11 Evaluation Metrics Harness.")
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
        "--output-path",
        default="data/processed/evaluation_report.json",
        help="Output JSON path for comparative results.",
    )
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    graph_dir = Path(args.graph_dir)
    embeddings_dir = Path(args.embeddings_dir)
    output_path = Path(args.output_path)

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

    # 2. Setup retrievers & ranking pipeline
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

    # Load parsed jobs
    jobs_path = processed_dir / "parsed_jobs.jsonl"
    jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jobs.append(ParsedJob.model_validate(json.loads(line)))

    # 3. Setup hand-labeled relevance judgments (0-3 rating)
    # Job j1: Senior Backend Engineer (expected match is c1)
    # Job j2: Data Engineer (expected match is c2)
    judgments = [
        RelevanceJudgment(job_id="j1", candidate_id="c1", relevance=3),
        RelevanceJudgment(job_id="j1", candidate_id="c2", relevance=1),
        RelevanceJudgment(job_id="j1", candidate_id="c3", relevance=0),
        RelevanceJudgment(job_id="j2", candidate_id="c2", relevance=3),
        RelevanceJudgment(job_id="j2", candidate_id="c1", relevance=1),
        RelevanceJudgment(job_id="j2", candidate_id="c3", relevance=0),
    ]

    harness = EvaluationHarness()

    # 4. Run calculations
    baseline_recs = harness.run_baseline(jobs, list(resumes.values()))
    system_recs = harness.run_full_system(
        jobs=jobs,
        hybrid_retriever=hybrid,
        feature_builder=feature_builder,
        scoring_engine=scoring_engine,
        reranker=reranker,
        blender=blender,
        resumes=resumes,
        kg=kg,
        behav_profiles=behav_profiles,
        candidates_meta=candidates_meta,
    )

    results = harness.compare(baseline_recs, system_recs, judgments, k=2)

    # 5. Output results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_dict = [res.model_dump(mode="json") for res in results]
    output_path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")

    print("\n================== TalentGraph Evaluation Metrics Benchmarks ==================")
    print(f"Computed over {len(jobs)} jobs and {len(resumes)} candidates (k=2)")
    print(f"Results written to {output_path}\n")
    print(f"{'Metric Name':<20} | {'Baseline Score':<15} | {'System Score':<15} | {'Delta':<10}")
    print("-" * 68)
    for res in results:
        print(
            f"{res.metric_name:<20} | "
            f"{res.baseline_score:<15.4f} | "
            f"{res.system_score:<15.4f} | "
            f"{res.delta:+.4f}"
        )
    print("\nIndividual Rankings Comparison:")
    for job in jobs:
        base = ", ".join(baseline_recs.get(job.job_id, []))
        sys_rec = ", ".join(system_recs.get(job.job_id, []))
        print(f"\n  Job ID: {job.job_id} | Title: {job.title}")
        print(f"    - Baseline recommendation ranks: [{base}]")
        print(f"    - System recommendation ranks:   [{sys_rec}]")


if __name__ == "__main__":
    main()
