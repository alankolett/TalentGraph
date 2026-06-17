from typing import Any

from embeddings.service import EmbeddingService
from parsers.models import ParsedJob
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.models import RetrievalResult


class HybridRetriever:
    """Orchestrates hybrid retrieval combining BM25, dense search, and hard filtering."""

    def __init__(
        self,
        bm25_index: BM25Index,
        dense_retriever: DenseRetriever,
        metadata_filter: MetadataFilter,
        embedding_service: EmbeddingService,
    ) -> None:
        self.bm25_index = bm25_index
        self.dense_retriever = dense_retriever
        self.metadata_filter = metadata_filter
        self.embedding_service = embedding_service

    def retrieve_hybrid(self, job: ParsedJob, top_k: int = 100) -> list[RetrievalResult]:
        """Perform hybrid search and filter out disqualified candidates."""
        # 1. Dense retrieval
        query_vector = self.embedding_service.embed_job(job)
        dense_results = self.dense_retriever.retrieve_dense(query_vector, top_k=1000)

        # 2. BM25 retrieval
        bm25_results = self.bm25_index.retrieve_bm25(job, top_k=1000)

        # 3. Reciprocal Rank Fusion
        fused_scores = self.fuse(bm25_results, dense_results)

        # Retrieve all candidate payloads to apply hard filters
        payloads = {}
        indexer = self.dense_retriever.indexer
        if hasattr(indexer, "_points"):
            payloads = {cid: point.payload for cid, point in indexer._points.items()}

        # 4. Filter and return top_k candidates
        retrieval_results = []
        for item in fused_scores:
            cid = item["candidate_id"]
            payload = payloads.get(cid, {})

            # Apply hard filters to check if candidate is disqualified
            passed_list = self.metadata_filter.apply_hard_filters(
                [{"candidate_id": cid, "payload": payload}], job
            )
            passes = len(passed_list) > 0

            retrieval_results.append(
                RetrievalResult(
                    candidate_id=cid,
                    bm25_score=item["bm25_score"],
                    dense_score=item["dense_score"],
                    passes_hard_filters=passes,
                    fused_score=item["fused_score"],
                )
            )

        # Filter out disqualified candidates (passes_hard_filters must be True)
        shortlist = [r for r in retrieval_results if r.passes_hard_filters]
        return shortlist[:top_k]

    def fuse(
        self,
        bm25_results: list[dict[str, Any]],
        dense_results: list[dict[str, Any]],
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Combine retrieval rankings using Reciprocal Rank Fusion (RRF)."""
        ranks: dict[str, dict[str, int]] = {}
        original_scores: dict[str, dict[str, float]] = {}

        for rank, res in enumerate(bm25_results, start=1):
            cid = res["candidate_id"]
            ranks.setdefault(cid, {})["bm25"] = rank
            original_scores.setdefault(cid, {})["bm25"] = res["score"]

        for rank, res in enumerate(dense_results, start=1):
            cid = res["candidate_id"]
            ranks.setdefault(cid, {})["dense"] = rank
            original_scores.setdefault(cid, {})["dense"] = res["score"]

        fused = []
        for cid, r_dict in ranks.items():
            score = 0.0
            if "bm25" in r_dict:
                score += 1.0 / (k + r_dict["bm25"])
            if "dense" in r_dict:
                score += 1.0 / (k + r_dict["dense"])

            fused.append(
                {
                    "candidate_id": cid,
                    "fused_score": score,
                    "bm25_score": original_scores.get(cid, {}).get("bm25", 0.0),
                    "dense_score": original_scores.get(cid, {}).get("dense", 0.0),
                }
            )

        fused.sort(key=lambda x: x["fused_score"], reverse=True)
        return fused
