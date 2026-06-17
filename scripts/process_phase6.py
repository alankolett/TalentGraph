import json
import sys
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from parsers.models import ParsedJob, ParsedResume
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever


def main() -> None:
    parser = ArgumentParser(description="Run Phase 6 Hybrid Retrieval (BM25 + Dense + Filters).")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing parsed resumes/jobs.",
    )
    parser.add_argument(
        "--embeddings-dir",
        default="data/embeddings",
        help="Directory containing candidate embeddings.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of shortlist candidates.")
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    embeddings_dir = Path(args.embeddings_dir)

    # 1. Load candidates & build BM25 Index
    resumes_path = processed_dir / "parsed_resumes.jsonl"
    resumes = []
    if resumes_path.exists():
        for line in resumes_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                resumes.append(ParsedResume.model_validate(json.loads(line)))

    bm25 = BM25Index()
    bm25.build_bm25_index(resumes)
    print(f"Built BM25 index with {len(resumes)} candidates.")

    # 2. Load embeddings & populate Qdrant Indexer
    embeddings_path = embeddings_dir / "candidate_embeddings.parquet"
    indexer = QdrantIndexer(vector_size=128)
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
    print(f"Indexed {indexer.count()} candidates in dense vector space.")

    # 3. Setup retrievers
    service = EmbeddingService(EmbeddingConfig(dimension=128))
    dense = DenseRetriever(indexer)
    metadata_filter = MetadataFilter()
    hybrid = HybridRetriever(
        bm25_index=bm25,
        dense_retriever=dense,
        metadata_filter=metadata_filter,
        embedding_service=service,
    )

    # 4. Load jobs & perform retrieval
    jobs_path = processed_dir / "parsed_jobs.jsonl"
    jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jobs.append(ParsedJob.model_validate(json.loads(line)))

    print("\n--- Hybrid Retrieval Results ---")
    for job in jobs:
        print(f"\nJob ID: {job.job_id} | Title: {job.title} | Seniority: {job.seniority} | Location: {job.location}")
        print(f"Must-have skills: {job.must_have}")
        results = hybrid.retrieve_hybrid(job, top_k=args.top_k)
        if not results:
            print("No matching candidates found passing hard filters.")
            continue
        for idx, res in enumerate(results, start=1):
            print(
                f"  {idx}. Candidate: {res.candidate_id} | "
                f"Fused Score: {res.fused_score:.5f} | "
                f"BM25 Score: {res.bm25_score:.3f} | "
                f"Dense Score: {res.dense_score:.3f}"
            )


if __name__ == "__main__":
    main()
