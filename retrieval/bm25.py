import re
from typing import Any

from rank_bm25 import BM25Okapi

from embeddings.text import build_candidate_text, build_job_text
from parsers.models import ParsedJob, ParsedResume

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Index:
    """Okapi BM25 index wrapper for candidate retrieval."""

    def __init__(self) -> None:
        self.bm25: BM25Okapi | None = None
        self.candidate_ids: list[str] = []

    def build_bm25_index(self, corpus: list[ParsedResume]) -> None:
        """Build the index once from a corpus of candidates."""
        self.candidate_ids = []
        tokenized_corpus = []
        for resume in corpus:
            self.candidate_ids.append(resume.candidate_id)
            text = build_candidate_text(resume)
            tokenized_corpus.append(tokenize(text))

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def retrieve_bm25(self, query: str | ParsedJob, top_k: int = 100) -> list[dict[str, Any]]:
        """Retrieve top_k candidates matching the query."""
        if not self.bm25 or not self.candidate_ids:
            return []

        if isinstance(query, ParsedJob):
            query_str = build_job_text(query)
        else:
            query_str = str(query)

        tokenized_query = tokenize(query_str)
        scores = self.bm25.get_scores(tokenized_query)

        results = []
        for idx, candidate_id in enumerate(self.candidate_ids):
            results.append({
                "candidate_id": candidate_id,
                "score": float(scores[idx]),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
