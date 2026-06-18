import math


class MetricCalculator:
    """Computes information retrieval metrics (Precision, MRR, NDCG)."""

    def compute_precision_at_k(self, recommendations: list[str], relevant_set: set[str], k: int) -> float:
        """Compute Precision@k."""
        if not recommendations or k <= 0:
            return 0.0
        top_k = recommendations[:k]
        hits = sum(1 for cid in top_k if cid in relevant_set)
        return float(hits / k)

    def compute_mrr(self, recommendations: list[str], relevant_set: set[str]) -> float:
        """Compute Mean Reciprocal Rank (MRR)."""
        for idx, cid in enumerate(recommendations, start=1):
            if cid in relevant_set:
                return float(1.0 / idx)
        return 0.0

    def compute_ndcg_at_k(
        self, recommendations: list[str], candidate_to_relevance: dict[str, int], k: int
    ) -> float:
        """Compute NDCG@k using exponential relevance decay."""
        if not recommendations or k <= 0:
            return 0.0

        # DCG@k
        relevances = [candidate_to_relevance.get(cid, 0) for cid in recommendations[:k]]
        dcg = sum(
            float((2**rel - 1) / math.log2(idx + 1)) for idx, rel in enumerate(relevances, start=1)
        )

        # IDCG@k (Ideal DCG sorted descending)
        ideal_relevances = sorted(candidate_to_relevance.values(), reverse=True)[:k]
        idcg = sum(
            float((2**rel - 1) / math.log2(idx + 1))
            for idx, rel in enumerate(ideal_relevances, start=1)
        )

        if idcg <= 0.0:
            return 0.0
        return float(dcg / idcg)
