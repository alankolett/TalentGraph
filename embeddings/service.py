from __future__ import annotations

import hashlib
import math
import re
from functools import cached_property

import numpy as np

from embeddings.models import EmbeddingConfig
from embeddings.text import build_candidate_text, build_job_text
from parsers.models import ParsedJob, ParsedResume

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")


class EmbeddingService:
    """Generate dense vectors with instruction prefixes and dimension truncation."""

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config or EmbeddingConfig()

    def embed_candidate(self, parsed_resume: ParsedResume) -> list[float]:
        text = build_candidate_text(parsed_resume)
        return self.embed_text(text, instruction=self.config.candidate_instruction)

    def embed_job(self, parsed_job: ParsedJob) -> list[float]:
        text = build_job_text(parsed_job)
        return self.embed_text(text, instruction=self.config.job_instruction)

    def embed_text(self, text: str, instruction: str = "") -> list[float]:
        prepared = self._prepare_text(text, instruction)
        if self.config.backend == "sentence-transformers":
            vector = self._embed_with_sentence_transformers(prepared)
        else:
            vector = self._embed_with_hashing(prepared)
        return self._truncate_and_normalize(vector).tolist()

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        left_array = np.array(left, dtype=np.float32)
        right_array = np.array(right, dtype=np.float32)
        denominator = np.linalg.norm(left_array) * np.linalg.norm(right_array)
        if denominator == 0:
            return 0.0
        return float(np.dot(left_array, right_array) / denominator)

    @cached_property
    def _sentence_model(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.config.model_name)

    def _embed_with_sentence_transformers(self, text: str) -> np.ndarray:
        vector = self._sentence_model.encode(text, normalize_embeddings=True)
        return np.array(vector, dtype=np.float32)

    def _embed_with_hashing(self, text: str) -> np.ndarray:
        vector = np.zeros(self.config.dimension, dtype=np.float32)
        tokens = TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.config.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return vector

    def _prepare_text(self, text: str, instruction: str) -> str:
        prepared = f"{instruction.strip()} {text.strip()}".strip()
        tokens = prepared.split()
        if len(tokens) > self.config.max_tokens:
            prepared = " ".join(tokens[-self.config.max_tokens :])
        return prepared

    def _truncate_and_normalize(self, vector: np.ndarray) -> np.ndarray:
        if vector.shape[0] > self.config.dimension:
            vector = vector[: self.config.dimension]
        elif vector.shape[0] < self.config.dimension:
            vector = np.pad(vector, (0, self.config.dimension - vector.shape[0]))

        norm = np.linalg.norm(vector)
        if math.isclose(float(norm), 0.0):
            return vector.astype(np.float32)
        return (vector / norm).astype(np.float32)
