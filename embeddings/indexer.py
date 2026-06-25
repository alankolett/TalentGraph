from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np

from embeddings.models import CandidateVectorPoint, VectorSearchResult


class QdrantIndexer:
    """Qdrant-shaped vector index with an in-memory backend for local pipelines/tests."""

    def __init__(self, collection_name: str = "candidates", vector_size: int = 128) -> None:
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._points: dict[str, CandidateVectorPoint] = {}

    def upsert_candidates(self, batch: Iterable[CandidateVectorPoint]) -> None:
        for point in batch:
            if len(point.vector) != self.vector_size:
                raise ValueError(
                    f"Vector for {point.id} has dimension {len(point.vector)}, "
                    f"expected {self.vector_size}."
                )
            self._points[point.id] = point

    def search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        if not self._points:
            return []

        valid_points = []
        for point in self._points.values():
            if filters and not self._matches_filters(point.payload, filters):
                continue
            valid_points.append(point)

        if not valid_points:
            return []

        vectors = np.array([p.vector for p in valid_points], dtype=np.float32)
        query = np.array(query_vector, dtype=np.float32)

        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            scores = np.zeros(len(valid_points), dtype=np.float32)
        else:
            norms = np.linalg.norm(vectors, axis=1)
            norms[norms == 0] = 1.0
            dots = np.dot(vectors, query)
            scores = dots / (norms * query_norm)

        results = []
        for idx, point in enumerate(valid_points):
            results.append(VectorSearchResult(id=point.id, score=float(scores[idx]), payload=point.payload))

        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]

    def count(self) -> int:
        return len(self._points)

    def _cosine(self, left: np.ndarray, right: np.ndarray) -> float:
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        if denominator == 0:
            return 0.0
        return float(np.dot(left, right) / denominator)

    def _matches_filters(self, payload: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            actual = payload.get(key)
            if isinstance(expected, dict):
                if "min" in expected and (actual is None or actual < expected["min"]):
                    return False
                if "max" in expected and (actual is None or actual > expected["max"]):
                    return False
            elif actual != expected:
                return False
        return True
