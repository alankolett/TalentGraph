from typing import Any

from embeddings.indexer import QdrantIndexer


class DenseRetriever:
    """Retrieves candidates based on vector similarity using QdrantIndexer."""

    def __init__(self, indexer: QdrantIndexer) -> None:
        self.indexer = indexer

    def retrieve_dense(
        self,
        query_vector: list[float],
        top_k: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve top_k candidates matching the query vector and filters."""
        results = self.indexer.search_by_vector(query_vector, top_k=top_k, filters=filters)
        return [
            {
                "candidate_id": res.id,
                "score": res.score,
                "payload": res.payload,
            }
            for res in results
        ]
