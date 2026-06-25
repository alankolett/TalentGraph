"""
rank.py
-------
The graded artifact. Produces submission.csv from candidates.jsonl.

Usage:
    python rank.py --candidates ./data/raw/redrob_challenge/candidates.jsonl \
                    --out ./submission.csv

Constraints this script is designed to respect (see Section 0 of the roadmap):
  - CPU only, no GPU
  - No network calls of any kind (no hosted LLM/API calls)
  - <= 16 GB RAM
  - <= 5 minutes wall-clock for the full run, including the one-time cache build

If a cache already exists at --cache (default ./data/processed/candidates_flat.pkl),
loading it is fast; if not, this run builds it -- so the very first run will be slower
than later ones. Time both separately when checking your budget.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import time
from collections import defaultdict
from pathlib import Path

from flatten_candidates import load_and_cache
from honeypot_detector import detect_honeypots
from jd_rubric import score_candidate

# ---------------------------------------------------------------------------
# The one fixed job description this challenge ranks against.
# Pulled from job_description.docx -- update only if the organizers change it.
# ---------------------------------------------------------------------------
JOB_TEXT = """
Senior AI Engineer Founding Team Redrob AI. We need someone with production
experience building embeddings, retrieval, ranking, ann vector search, hybrid
search, recommendation systems, evaluation frameworks ndcg mrr map a/b testing,
python, machine learning, deep learning, natural language processing, large
language models, RAG, vector databases, qdrant, pinecone, weaviate, scalable
backend systems, search infrastructure, real time inference, model serving.
"""

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Index:
    """Minimal Okapi BM25 over an inverted index. Pure Python + stdlib only --
    deliberately has zero third-party dependencies so it can't fail to install
    in a fresh, network-free environment."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.inverted: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self.doc_len: list[int] = []
        self.idf: dict[str, float] = {}
        self.N = 0
        self.avgdl = 0.0

    def build(self, texts: list[str]) -> None:
        total_len = 0
        for i, text in enumerate(texts):
            tokens = tokenize(text)
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            tf: dict[str, int] = defaultdict(int)
            for t in tokens:
                tf[t] += 1
            for term, freq in tf.items():
                self.inverted[term].append((i, freq))
        self.N = len(texts)
        self.avgdl = total_len / max(self.N, 1)
        for term, postings in self.inverted.items():
            df = len(postings)
            self.idf[term] = math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def score_query(self, query_text: str) -> list[float]:
        scores = [0.0] * self.N
        for term in set(tokenize(query_text)):
            postings = self.inverted.get(term)
            if not postings:
                continue
            idf = self.idf[term]
            for doc_idx, tf in postings:
                dl = self.doc_len[doc_idx]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[doc_idx] += idf * (tf * (self.k1 + 1)) / denom
        return scores


def normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


# ---------------------------------------------------------------------------
# Reasoning generation: grounded templates, NOT an LLM call. Every claim below
# traces directly to a real computed field -- see Phase 10 in the roadmap for
# why this approach was chosen over calling a model inside the timed step.
# ---------------------------------------------------------------------------

POSITIVE_PHRASES = {
    "production_retrieval_experience": "hands-on production retrieval/ranking experience",
    "eval_framework_experience": "experience with ranking evaluation (NDCG/MAP-style metrics)",
    "hr_tech_exposure": "prior HR-tech / recruiting-platform exposure",
    "open_source_validation": "externally-validated work (open-source or public activity)",
    "india_or_relocate": "based in India or open to relocation",
}

DISQUALIFIER_NOTES = {
    "consulting_only": "career has been entirely consulting-firm based",
    "pure_research_only": "background is research-only with no production deployment found",
    "recent_ai_only": "AI/ML exposure looks recent (<=12mo) with no earlier ML background",
    "architect_no_recent_code": "current role reads as architect/lead with no recent hands-on coding signal",
    "job_hopper": "average tenure under 18 months across recent roles",
    "cv_speech_robotics_only": "background is CV/speech/robotics with no NLP/IR signal found",
    "closed_source_no_validation": "5+ yrs experience with no external validation signal found",
}


def generate_reasoning(flat: dict, rubric, bm25_norm: float, rank: int) -> str:
    title = flat["current_title"]
    years = flat["years_of_experience"]
    base = f"{title}, {years:.1f} yrs experience"

    pos = [POSITIVE_PHRASES[p] for p in rubric.positive_hits[:2]]
    if pos:
        base += "; " + " and ".join(pos)

    if rubric.disqualifier_hits:
        note = DISQUALIFIER_NOTES[rubric.disqualifier_hits[0]]
        base += f". Concern: {note}"
    elif bm25_norm < 0.15 and not pos:
        base += ". Thin signal overall -- ranked primarily on absence of red flags, not strong positive match"
    elif rank <= 10:
        base += ". Strong overall alignment with the role"
    else:
        base += ". Reasonable but partial alignment with the role"

    return base


def build_submission(candidates: list[dict], top_n: int = 100) -> list[dict]:
    texts = [c["all_text"] for c in candidates]

    bm25 = BM25Index()
    bm25.build(texts)
    bm25_scores = bm25.score_query(JOB_TEXT)
    bm25_norm = normalize(bm25_scores)

    rows = []
    for i, flat in enumerate(candidates):
        flags = detect_honeypots(flat)
        rubric = score_candidate(flat)

        composite = (
            0.40 * bm25_norm[i]
            + 0.30 * rubric.positive_score
            + 0.15 * rubric.notice_bonus
            + 0.15 * (1.0 if flat["verified_email"] and flat["verified_phone"] else 0.5)
        )
        composite *= rubric.disqualifier_multiplier
        if flags:
            composite *= 0.0  # push honeypots to the very bottom, never into top 100

        rows.append({
            "candidate_id": flat["candidate_id"],
            "score": composite,
            "flat": flat,
            "rubric": rubric,
            "bm25_norm": bm25_norm[i],
            "honeypot": bool(flags),
        })

    rows.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    top = rows[:top_n]

    n_honeypots_in_top = sum(1 for r in top if r["honeypot"])
    print(f"[rank.py] honeypots in top {top_n}: {n_honeypots_in_top} "
          f"({n_honeypots_in_top / top_n * 100:.1f}% -- must stay <= 10%)")

    out = []
    for rank_idx, r in enumerate(top, start=1):
        out.append({
            "candidate_id": r["candidate_id"],
            "rank": rank_idx,
            "score": round(r["score"], 6),
            "reasoning": generate_reasoning(r["flat"], r["rubric"], r["bm25_norm"], rank_idx),
        })
    return out


def write_submission_csv(rows: list[dict], out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="./data/raw/redrob_challenge/candidates.jsonl")
    parser.add_argument("--cache", default="./data/processed/candidates_flat.pkl")
    parser.add_argument("--out", default="./submission.csv")
    parser.add_argument("--force-rebuild-cache", action="store_true")
    args = parser.parse_args()

    t0 = time.time()
    candidates = load_and_cache(args.candidates, args.cache, force_rebuild=args.force_rebuild_cache)
    t1 = time.time()
    print(f"[rank.py] candidates loaded: {len(candidates)} in {t1 - t0:.1f}s")

    submission = build_submission(candidates, top_n=100)
    t2 = time.time()
    print(f"[rank.py] scoring + ranking complete in {t2 - t1:.1f}s")

    write_submission_csv(submission, args.out)
    t3 = time.time()
    print(f"[rank.py] wrote {len(submission)} rows to {args.out}")
    print(f"[rank.py] TOTAL elapsed: {t3 - t0:.1f}s (budget: 300s)")
    if t3 - t0 > 240:
        print("[rank.py] WARNING: within 60s of the 5-minute budget -- investigate before submitting.")


if __name__ == "__main__":
    main()
