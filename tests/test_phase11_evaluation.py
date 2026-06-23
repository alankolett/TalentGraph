import pytest

from evaluation.harness import EvaluationHarness
from evaluation.metrics import MetricCalculator
from parsers.models import ParsedJob, ParsedResume


def test_metric_calculator_precision_and_mrr() -> None:
    calculator = MetricCalculator()

    recommendations = ["c1", "c2", "c3"]
    relevant_set = {"c2"}

    # Precision@k tests
    assert calculator.compute_precision_at_k(recommendations, relevant_set, k=1) == 0.0
    assert calculator.compute_precision_at_k(recommendations, relevant_set, k=2) == 0.5
    assert calculator.compute_precision_at_k(recommendations, relevant_set, k=3) == pytest.approx(1 / 3)

    # MRR tests
    # First relevant item is c2, which is at rank 2 -> MRR = 1/2 = 0.5
    assert calculator.compute_mrr(recommendations, relevant_set) == 0.5

    # If nothing matches
    assert calculator.compute_mrr(recommendations, {"c4"}) == 0.0


def test_metric_calculator_ndcg_at_k() -> None:
    calculator = MetricCalculator()

    recommendations = ["c1", "c2", "c3"]
    # Relevance judgments: c1 is irrelevant (0), c2 is perfect match (3), c3 is good match (1)
    relevance_judgments = {"c1": 0, "c2": 3, "c3": 1}

    # DCG@2 for ['c1', 'c2']:
    # Rank 1: c1 -> relevance 0 -> (2^0 - 1) / log2(2) = 0.0
    # Rank 2: c2 -> relevance 3 -> (2^3 - 1) / log2(3) = 7.0 / 1.58496 = 4.4165
    # DCG@2 = 4.4165

    # IDCG@2 (ideal is ['c2', 'c3']):
    # Rank 1: c2 -> relevance 3 -> (2^3 - 1) / log2(2) = 7.0
    # Rank 2: c3 -> relevance 1 -> (2^1 - 1) / log2(3) = 1.0 / 1.58496 = 0.6309
    # IDCG@2 = 7.6309

    # NDCG@2 = 4.4165 / 7.6309 = 0.5787
    assert calculator.compute_ndcg_at_k(recommendations, relevance_judgments, k=2) == pytest.approx(0.5787, abs=0.001)


def test_baseline_ranking_logic() -> None:
    harness = EvaluationHarness()

    jobs = [
        ParsedJob(
            job_id="j1",
            title="Dev",
            must_have=["Python", "FastAPI"],
            raw_text="Requires Python",
        )
    ]
    resumes = [
        ParsedResume(candidate_id="c1", raw_skills=["Python"], sections={}),  # 1 match
        ParsedResume(candidate_id="c2", raw_skills=["Python", "FastAPI"], sections={}),  # 2 matches
        ParsedResume(candidate_id="c3", raw_skills=["Python"], sections={}),  # 1 match
    ]

    rankings = harness.run_baseline(jobs, resumes)

    # c2 has 2 matches -> rank 1
    # c1 and c3 both have 1 match -> tie-breaker alphabetically: c1 then c3
    assert rankings["j1"] == ["c2", "c1", "c3"]
