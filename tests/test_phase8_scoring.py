import networkx as nx
import pytest

from feature_engineering.behavioral import BehavioralProfile
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.features import FeatureBuilder
from ranking_engine.models import FeatureVector
from ranking_engine.scoring import ScoringEngine


def test_scoring_weighted_sum_computes_correctly() -> None:
    engine = ScoringEngine()

    # If all features are 1.0, the score must be exactly 1.0 (since weights sum to 1.0)
    features_perfect = FeatureVector(
        skill_overlap=1.0,
        kg_skill_distance=1.0,
        dense_similarity=1.0,
        bm25_score=1.0,
        trajectory_alignment=1.0,
        behavioral_score=1.0,
        seniority_match=1.0,
    )
    result = engine.score_candidate("c1", features_perfect)
    assert result.final_score == pytest.approx(1.0)
    assert result.score_breakdown["skill_overlap"] == 0.25
    assert result.score_breakdown["kg_skill_distance"] == 0.20
    assert result.score_breakdown["dense_similarity"] == 0.20
    assert result.score_breakdown["bm25_score"] == 0.10
    assert result.score_breakdown["trajectory_alignment"] == 0.10
    assert result.score_breakdown["behavioral_score"] == 0.10
    assert result.score_breakdown["seniority_match"] == 0.05


def test_monotonicity_sanity_checks() -> None:
    engine = ScoringEngine()

    # Verify that increasing a single feature score strictly increases the final score
    f1 = FeatureVector(
        skill_overlap=0.5,
        kg_skill_distance=0.5,
        dense_similarity=0.5,
        bm25_score=0.5,
        trajectory_alignment=0.5,
        behavioral_score=0.5,
        seniority_match=0.5,
    )
    f2 = FeatureVector(
        skill_overlap=0.8,  # increased from 0.5 to 0.8
        kg_skill_distance=0.5,
        dense_similarity=0.5,
        bm25_score=0.5,
        trajectory_alignment=0.5,
        behavioral_score=0.5,
        seniority_match=0.5,
    )

    r1 = engine.score_candidate("c1", f1)
    r2 = engine.score_candidate("c1", f2)

    assert r2.final_score > r1.final_score
    # Difference should be weight (0.25) * delta (0.3) = 0.075
    assert r2.final_score - r1.final_score == pytest.approx(0.075)


def test_renormalization_for_missing_features() -> None:
    engine = ScoringEngine()

    # If skill_overlap is missing (set to None), its weight (0.25) is ignored.
    # Total active weight becomes 0.75.
    # If all other features are 1.0, the final score should still renormalize to 1.0.
    features_missing = FeatureVector(
        skill_overlap=None,  # missing
        kg_skill_distance=1.0,
        dense_similarity=1.0,
        bm25_score=1.0,
        trajectory_alignment=1.0,
        behavioral_score=1.0,
        seniority_match=1.0,
    )

    result = engine.score_candidate("c1", features_missing)
    assert result.final_score == pytest.approx(1.0)
    # The weight of dense_similarity should be normalized: 0.20 / 0.75 = 0.2667
    assert result.score_breakdown["dense_similarity"] == pytest.approx(0.20 / 0.75)
    assert result.score_breakdown["skill_overlap"] == 0.0


def test_feature_builder_jaccard_and_seniority() -> None:
    builder = FeatureBuilder()
    kg = nx.DiGraph()

    resume = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI"],
        sections={},
    )
    job = ParsedJob(
        job_id="j1",
        title="Senior Developer",
        seniority="senior",
        must_have=["Python"],
        raw_text="Required: Python. Preferred: Django.",
    )

    # Experience YoE = 6.0 (meets Senior YoE requirement of >= 5.0)
    f_vector = builder.build_feature_vector(
        parsed_resume=resume,
        job=job,
        kg=kg,
        behavioral_profile=None,
        retrieval_scores={},
        experience_years=6.0,
    )

    assert f_vector.seniority_match == 1.0
    # Union skills normalized: {'python', 'django'}. Intersection: {'python'}. Jaccard = 1/2 = 0.5
    assert f_vector.skill_overlap == 0.5

    # Test experience mismatch: expected YoE = 5.0, candidate has YoE = 2.5
    f_vector_low = builder.build_feature_vector(
        parsed_resume=resume,
        job=job,
        kg=kg,
        behavioral_profile=None,
        retrieval_scores={},
        experience_years=2.5,
    )
    assert f_vector_low.seniority_match == pytest.approx(0.5)  # 1.0 - (5.0 - 2.5)/5.0 = 0.5


def test_rubric_features_are_computed() -> None:
    builder = FeatureBuilder()
    kg = nx.DiGraph()
    resume = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "RAG", "Qdrant"],
        experience_entries=[],
        sections={},
    )
    job = ParsedJob(
        job_id="j1",
        title="Senior AI Engineer",
        seniority="senior",
        must_have=["Python"],
        raw_text="Required: Python, embeddings, Qdrant.",
    )
    # Passed metadata satisfies:
    # - location inside India (mumbai) -> +1 positive signal
    # - notice_period_days < 30 (15) -> +1 positive signal
    # Total positive signal count should be > 0.
    # No disqualifiers.
    f_vector = builder.build_feature_vector(
        parsed_resume=resume,
        job=job,
        kg=kg,
        behavioral_profile=None,
        retrieval_scores={},
        experience_years=6.0,
        metadata={
            "location": "Mumbai",
            "willing_to_relocate": True,
            "notice_period_days": 15,
            "github_activity_score": 10,
            "total_career_months": 72,
            "num_employers": 2,
        },
    )
    assert f_vector.jd_positive_signal_count >= 2
    assert len(f_vector.jd_disqualifier_flags) == 0


def test_honeypot_score_is_populated() -> None:
    builder = FeatureBuilder()
    kg = nx.DiGraph()
    resume = ParsedResume(candidate_id="c1", raw_skills=[], sections={})
    job = ParsedJob(job_id="j1", title="AI Engineer", must_have=[], raw_text="We are hiring.")
    
    behav = BehavioralProfile(candidate_id="c1", honeypot_score=1.0)
    
    f_vector = builder.build_feature_vector(
        parsed_resume=resume,
        job=job,
        kg=kg,
        behavioral_profile=behav,
        retrieval_scores={},
        experience_years=3.0,
        metadata=None,
    )
    assert f_vector.honeypot_score == 1.0


def test_disqualifier_penalties_are_applied() -> None:
    engine = ScoringEngine()

    # Case 1: 2 disqualifiers, positive signal count is low (< 5)
    # Penalty: 0.5 ** 2 = 0.25
    features_low_pos = FeatureVector(
        skill_overlap=1.0,
        kg_skill_distance=1.0,
        dense_similarity=1.0,
        bm25_score=1.0,
        trajectory_alignment=1.0,
        behavioral_score=1.0,
        seniority_match=1.0,
        jd_positive_signal_count=2,
        jd_disqualifier_flags=["disqualifier_job_hopper", "disqualifier_consulting_only"],
        honeypot_score=0.0,
    )
    res_low = engine.score_candidate("c1", features_low_pos)
    assert res_low.final_score == pytest.approx(1.0 * 0.25)

    # Case 2: 2 disqualifiers, positive signal count is high (>= 5)
    # Penalty: 1.0 - 0.1 * 2 = 0.8
    features_high_pos = FeatureVector(
        skill_overlap=1.0,
        kg_skill_distance=1.0,
        dense_similarity=1.0,
        bm25_score=1.0,
        trajectory_alignment=1.0,
        behavioral_score=1.0,
        seniority_match=1.0,
        jd_positive_signal_count=6,
        jd_disqualifier_flags=["disqualifier_job_hopper", "disqualifier_consulting_only"],
        honeypot_score=0.0,
    )
    res_high = engine.score_candidate("c1", features_high_pos)
    assert res_high.final_score == pytest.approx(1.0 * 0.8)


def test_honeypot_penalty_is_applied() -> None:
    engine = ScoringEngine()

    features_honeypot = FeatureVector(
        skill_overlap=1.0,
        kg_skill_distance=1.0,
        dense_similarity=1.0,
        bm25_score=1.0,
        trajectory_alignment=1.0,
        behavioral_score=1.0,
        seniority_match=1.0,
        jd_positive_signal_count=0,
        jd_disqualifier_flags=[],
        honeypot_score=1.0,
    )
    res = engine.score_candidate("c1", features_honeypot)
    assert res.final_score == pytest.approx(1.0 * 0.01)

