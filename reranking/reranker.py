from typing import Any

from rapidfuzz import fuzz


class CrossEncoderReranker:
    """Wraps Cross-Encoder model scoring, with a deterministic mock fallback."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", backend: str = "mock") -> None:
        self.model_name = model_name
        self.backend = backend
        self._model: Any = None

    def build_reranker_pairs(self, job_text: str, candidate_texts: list[str]) -> list[tuple[str, str]]:
        """Combine job text and candidate texts into query-document pairs."""
        return [(job_text, text) for text in candidate_texts]

    def rerank(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Generate similarity scores for each query-document pair."""
        if not pairs:
            return []

        if self.backend == "sentence-transformers":
            return self._rerank_sentence_transformers(pairs)
        return self._rerank_mock(pairs)

    def _rerank_sentence_transformers(self, pairs: list[tuple[str, str]]) -> list[float]:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)

        scores = self._model.predict(pairs)
        # Apply sigmoid to map raw logits to [0.0, 1.0] range
        import numpy as np

        scores_arr = np.array(scores, dtype=np.float32)
        sigm = 1.0 / (1.0 + np.exp(-scores_arr))
        return sigm.tolist()

    def _rerank_mock(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = []
        for job_text, candidate_text in pairs:
            # Simulate context limits by truncating candidate text to 1000 characters
            truncated = candidate_text[:1000]
            # Normalize token set ratio to [0.0, 1.0]
            ratio = fuzz.token_set_ratio(job_text, truncated) / 100.0
            scores.append(float(ratio))
        return scores


class ScoreBlender:
    """Blends initial composite feature scores with reranker scores."""

    def blend_scores(
        self, composite_score: float, reranker_score: float, alpha: float = 0.5
    ) -> float:
        """Blend the initial composite relevance score and the reranker score."""
        return float(alpha * reranker_score + (1.0 - alpha) * composite_score)
