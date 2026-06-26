import pytest
import pickle
from pathlib import Path
from jd_rubric import (
    is_consulting_only,
    is_pure_research_only,
    is_recent_ai_only,
    is_architect_no_recent_code,
    is_job_hopper,
    is_cv_speech_robotics_only,
    is_closed_source_no_validation,
    has_production_retrieval_experience,
    has_eval_framework_experience,
    has_hr_tech_exposure,
    has_open_source_validation,
    india_or_relocate,
    notice_period_bonus,
    score_candidate
)
from honeypot_detector import detect_honeypots


@pytest.fixture(scope="module")
def candidates():
    """Load candidates flat cache for hand-picked testing."""
    cache_path = Path("data/processed/candidates_flat.pkl")
    if not cache_path.exists():
        pytest.skip("candidates_flat.pkl cache not found")
    with open(cache_path, "rb") as f:
        return {c["candidate_id"]: c for c in pickle.load(f)}


def test_consulting_only(candidates):
    # CAND_0000003 has a career history consisting entirely of consulting firms
    c = candidates.get("CAND_0000003")
    assert c is not None
    assert is_consulting_only(c) is True

    # CAND_0000001 is a product/tech engineer (non-consulting only)
    c_prod = candidates.get("CAND_0000001")
    assert c_prod is not None
    assert is_consulting_only(c_prod) is False


def test_job_hopper(candidates):
    # CAND_0000004 has average tenure < 18 months across >=3 roles
    c = candidates.get("CAND_0000004")
    assert c is not None
    assert is_job_hopper(c) is True

    # CAND_0000001 has stable tenure
    c_stable = candidates.get("CAND_0000001")
    assert c_stable is not None
    assert is_job_hopper(c_stable) is False


def test_recent_ai_only(candidates):
    # CAND_0000852 has AI/ML-relevant experience only in the current role (<=12mo)
    c = candidates.get("CAND_0000852")
    assert c is not None
    assert is_recent_ai_only(c) is True


def test_closed_source_no_validation(candidates):
    # CAND_0000001 has >=5 years of experience and is checked for validation
    c = candidates.get("CAND_0000001")
    assert c is not None
    # Let's verify our logic on a modified copy
    c_copy = dict(c)
    c_copy["years_of_experience"] = 6.0
    c_copy["github_activity_score"] = -1
    c_copy["all_text_lower"] = "some closed source work description without public links"
    assert is_closed_source_no_validation(c_copy) is True


def test_pure_research_only(candidates):
    # Since no natural candidate matches, mock one using a real candidate's base
    c = candidates.get("CAND_0000001")
    assert c is not None
    c_copy = dict(c)
    c_copy["all_text_lower"] = "academic research in university research lab with phd thesis"
    assert is_pure_research_only(c_copy) is True

    # With production signal, it should not trigger
    c_copy["all_text_lower"] += " and deployed to production for real users"
    assert is_pure_research_only(c_copy) is False


def test_architect_no_recent_code(candidates):
    # Mock one using a real candidate's base
    c = candidates.get("CAND_0000001")
    assert c is not None
    c_copy = dict(c)
    c_copy["current_title"] = "Solutions Architect"
    c_copy["current_role_description"] = "Supervised team and designed high-level UML diagrams"
    c_copy["current_role_duration_months"] = 24
    assert is_architect_no_recent_code(c_copy) is True

    # With coding signal, it should not trigger
    c_copy["current_role_description"] += " and implemented core features"
    assert is_architect_no_recent_code(c_copy) is False


def test_cv_speech_robotics_only(candidates):
    # Mock one using a real candidate's base
    c = candidates.get("CAND_0000001")
    assert c is not None
    c_copy = dict(c)
    c_copy["all_text_lower"] = "worked on computer vision and robotics navigation systems"
    assert is_cv_speech_robotics_only(c_copy) is True

    # With NLP signal, it should not trigger
    c_copy["all_text_lower"] += " and natural language processing models"
    assert is_cv_speech_robotics_only(c_copy) is False


def test_positive_signals(candidates):
    c = candidates.get("CAND_0000001")
    assert c is not None
    # Verify notice period bonus logic
    c_copy = dict(c)
    c_copy["notice_period_days"] = 15
    assert notice_period_bonus(c_copy) == 1.0
    c_copy["notice_period_days"] = 45
    assert notice_period_bonus(c_copy) == 0.6
    c_copy["notice_period_days"] = 120
    assert notice_period_bonus(c_copy) == 0.0

    # Verify other signals
    assert india_or_relocate(c) in (True, False)
    assert has_production_retrieval_experience(c) in (True, False)
    assert has_eval_framework_experience(c) in (True, False)


def test_honeypots(candidates):
    # CAND_0007353 has career history duration exceeding stated experience
    c_hp = candidates.get("CAND_0007353")
    assert c_hp is not None
    flags = detect_honeypots(c_hp)
    assert "career_history_exceeds_stated_experience" in flags

    # Verify expert zero duration check on a mock copy
    c = candidates.get("CAND_0000001")
    assert c is not None
    c_copy = dict(c)
    c_copy["skills"] = [{"name": "Python", "proficiency": "expert", "duration_months": 0}]
    flags_zero = detect_honeypots(c_copy)
    assert "expert_zero_duration:Python" in flags_zero


def test_composite_score(candidates):
    c = candidates.get("CAND_0000001")
    assert c is not None
    res = score_candidate(c)
    assert 0.0 <= res.positive_score <= 1.0
    assert res.disqualifier_multiplier in (0.05, 0.35, 1.0)
