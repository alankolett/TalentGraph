import pytest

from reranking.models import RerankedCandidate
from reranking.reranker import CrossEncoderReranker, ScoreBlender


def test_score_blender_math() -> None:
    blender = ScoreBlender()

    # alpha = 0.5: middle blend
    assert blender.blend_scores(0.6, 0.8, alpha=0.5) == pytest.approx(0.7)

    # alpha = 1.0: only reranker score
    assert blender.blend_scores(0.6, 0.8, alpha=1.0) == pytest.approx(0.8)

    # alpha = 0.0: only initial score
    assert blender.blend_scores(0.6, 0.8, alpha=0.0) == pytest.approx(0.6)


def test_cross_encoder_rerank_pairs() -> None:
    reranker = CrossEncoderReranker(backend="mock")
    job_text = "Requires Python and FastAPI."
    cand_texts = [
        "Backend developer matching Python and FastAPI.",
        "Frontend developer building React web interfaces.",
    ]

    pairs = reranker.build_reranker_pairs(job_text, cand_texts)
    assert len(pairs) == 2
    assert pairs[0] == (job_text, cand_texts[0])

    scores = reranker.rerank(pairs)
    assert len(scores) == 2
    # First candidate should have higher match ratio
    assert scores[0] > scores[1]


def test_truncation_for_long_candidate_resumes() -> None:
    reranker = CrossEncoderReranker(backend="mock")
    job_text = "Requires Python."
    # Candidate text > 1000 characters
    long_cand_text = "Python engineer. " + ("word " * 300)
    assert len(long_cand_text) > 1000

    pairs = [(job_text, long_cand_text)]
    scores = reranker.rerank(pairs)
    assert len(scores) == 1
    assert isinstance(scores[0], float)


def test_wrong_seniority_candidate_drops_after_rerank() -> None:
    reranker = CrossEncoderReranker(backend="mock")
    blender = ScoreBlender()

    job_text = "Senior Python Backend Engineer. Required: Python, FastAPI. Experience: Senior (5+ years)."
    
    # Candidate A: Senior, matches job details
    cand_a_text = "Senior Backend Engineer. Skills: Python, FastAPI. 6 years YoE at Acme."
    # Candidate B: Junior, but matches many words/keywords (high BM25 potential)
    cand_b_text = "Junior developer. Skills: Python, FastAPI. 1 year YoE at Acme."

    pairs = [(job_text, cand_a_text), (job_text, cand_b_text)]
    rerank_scores = reranker.rerank(pairs)

    # Joint attention should give Candidate A (who matches "Senior" context) a higher score
    assert rerank_scores[0] > rerank_scores[1]

    # Let's say Candidate B had a slightly higher initial score due to keyword stuffing:
    # Candidate A initial = 0.70, Candidate B initial = 0.75
    blend_a = blender.blend_scores(0.70, rerank_scores[0], alpha=0.6)
    blend_b = blender.blend_scores(0.75, rerank_scores[1], alpha=0.6)

    # After blending, Candidate A should rank higher than Candidate B
    assert blend_a > blend_b
