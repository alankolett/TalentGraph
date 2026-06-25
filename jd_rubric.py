"""
jd_rubric.py
------------
Phase 8: encodes the actual "Senior AI Engineer -- Founding Team" job description's
explicit rubric as named, independently-testable functions, calibrated against
patterns found by analyzing the real 100K-candidate dataset.

Calibration notes baked into the thresholds below (don't change without re-checking
against the real data):
  - Only 22 of 100,000 candidates have notice_period_days < 30. notice_period_bonus()
    is therefore a SOFT, graded bonus, never a hard filter.
  - Only 569 of 100,000 candidates (0.57%) have any AI/ML/Data-relevant title, and the
    exact title "Senior AI Engineer" appears on only 4 candidates. Positive-signal
    extraction below deliberately scans career_history description text (all_text),
    not just current_title, because title-only matching would miss almost everyone
    who actually fits.
  - Consulting-only career (TCS/Infosys/Wipro/Accenture/Cognizant/Capgemini etc. with
    zero product-company stints) is true for 9.7% of the pool -- real and sizeable,
    not an edge case worth ignoring.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Keyword vocabularies (all matched against lowercased free text)
# ---------------------------------------------------------------------------

CONSULTING_FIRMS = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mindtree",
    "l&t infotech", "ltimindtree", "mphasis",
}

RETRIEVAL_KEYWORDS = {
    "embedding", "embeddings", "vector database", "vector search", "retrieval",
    "ranking", "recommendation system", "recommender", "rag", "qdrant",
    "pinecone", "weaviate", "milvus", "elasticsearch", "opensearch", "faiss",
    "semantic search", "hybrid search", "information retrieval",
}

EVAL_KEYWORDS = {
    "ndcg", "mrr", "map@", "mean average precision", "a/b test", "ab test",
    "offline evaluation", "evaluation framework", "precision@", "recall@",
}

CV_SPEECH_ROBOTICS_KEYWORDS = {
    "computer vision", "image classification", "object detection", "speech recognition",
    "robotics", "slam", "autonomous navigation", "image segmentation",
}

NLP_IR_KEYWORDS = {
    "nlp", "natural language processing", "information retrieval", "text classification",
    "language model", "named entity recognition", "text mining", "topic modeling",
}

ARCHITECT_TITLE_KEYWORDS = {"architect", "tech lead", "engineering manager", "director", "head of", "vp "}

PRODUCTION_SIGNAL_KEYWORDS = {
    "production", "deployed", "real users", "real-time", "at scale", "shipped",
    "launched", "live system",
}

RESEARCH_ONLY_KEYWORDS = {
    "research lab", "academic research", "postdoc", "phd thesis", "university research",
}

HR_TECH_KEYWORDS = {
    "recruiting", "recruitment", "talent acquisition", "hr tech", "hiring platform",
    "job matching", "candidate screening", "marketplace",
}

OPEN_SOURCE_KEYWORDS = {
    "open source", "open-source", "published", "conference talk", "research paper",
    "github.com", "blog post",
}

AI_ROLE_TITLE_KEYWORDS = {"ai engineer", "ml engineer", "machine learning", "data scientist", "research scientist"}


def _text(flat: dict) -> str:
    return flat["all_text_lower"]


# ---------------------------------------------------------------------------
# Disqualifiers (the JD explicitly says these should not move forward)
# ---------------------------------------------------------------------------

def is_consulting_only(flat: dict) -> bool:
    """Entire career at consulting firms, no product-company stint anywhere."""
    employers = [e.strip().lower() for e in flat["employers"]]
    if not employers:
        return False
    return all(any(cf in emp for cf in CONSULTING_FIRMS) for emp in employers)


def is_pure_research_only(flat: dict) -> bool:
    text = _text(flat)
    has_research_signal = any(kw in text for kw in RESEARCH_ONLY_KEYWORDS)
    has_production_signal = any(kw in text for kw in PRODUCTION_SIGNAL_KEYWORDS)
    return has_research_signal and not has_production_signal


def is_recent_ai_only(flat: dict) -> bool:
    """AI/ML-relevant experience exists only in the current role, <=12 months,
    with no earlier role showing any AI/ML/retrieval signal (i.e. no pre-LLM-era
    production ML background)."""
    history = sorted(flat["career_history"], key=lambda c: c["start_date"])
    if not history:
        return False
    current = history[-1]
    is_current_ai = any(
        kw in (current["title"] + " " + current["description"]).lower()
        for kw in RETRIEVAL_KEYWORDS | {"machine learning", "ai ", " ml "}
    )
    if not (is_current_ai and current["duration_months"] <= 12):
        return False
    earlier_ai_signal = any(
        any(kw in (ch["title"] + " " + ch["description"]).lower()
            for kw in RETRIEVAL_KEYWORDS | {"machine learning", "ai ", " ml "})
        for ch in history[:-1]
    )
    return not earlier_ai_signal


def is_architect_no_recent_code(flat: dict) -> bool:
    title_l = flat["current_title"].lower()
    if not any(kw in title_l for kw in ARCHITECT_TITLE_KEYWORDS):
        return False
    desc_l = flat["current_role_description"].lower()
    coding_signal = any(kw in desc_l for kw in {"implemented", "built", "wrote", "coded", "shipped", "developed"})
    return flat["current_role_duration_months"] >= 18 and not coding_signal


def is_job_hopper(flat: dict) -> bool:
    history = flat["career_history"]
    if len(history) < 3:
        return False
    avg_tenure = sum(ch["duration_months"] for ch in history) / len(history)
    return avg_tenure < 18


def is_cv_speech_robotics_only(flat: dict) -> bool:
    text = _text(flat)
    has_cv = any(kw in text for kw in CV_SPEECH_ROBOTICS_KEYWORDS)
    has_nlp = any(kw in text for kw in NLP_IR_KEYWORDS)
    return has_cv and not has_nlp


def is_closed_source_no_validation(flat: dict) -> bool:
    text = _text(flat)
    has_validation = (
        (flat["github_activity_score"] not in (-1,) and flat["github_activity_score"] > 10)
        or any(kw in text for kw in OPEN_SOURCE_KEYWORDS)
    )
    return flat["years_of_experience"] >= 5 and not has_validation


DISQUALIFIERS = {
    "consulting_only": is_consulting_only,
    "pure_research_only": is_pure_research_only,
    "recent_ai_only": is_recent_ai_only,
    "architect_no_recent_code": is_architect_no_recent_code,
    "job_hopper": is_job_hopper,
    "cv_speech_robotics_only": is_cv_speech_robotics_only,
    "closed_source_no_validation": is_closed_source_no_validation,
}


# ---------------------------------------------------------------------------
# Positive signals
# ---------------------------------------------------------------------------

def has_production_retrieval_experience(flat: dict) -> bool:
    return any(kw in _text(flat) for kw in RETRIEVAL_KEYWORDS)


def has_eval_framework_experience(flat: dict) -> bool:
    return any(kw in _text(flat) for kw in EVAL_KEYWORDS)


def has_hr_tech_exposure(flat: dict) -> bool:
    return any(kw in _text(flat) for kw in HR_TECH_KEYWORDS) or "hr" in flat["current_industry"].lower()


def has_open_source_validation(flat: dict) -> bool:
    gh = flat["github_activity_score"]
    return (gh != -1 and gh > 30) or any(kw in _text(flat) for kw in OPEN_SOURCE_KEYWORDS)


def india_or_relocate(flat: dict) -> bool:
    return flat["country"].strip().lower() == "india" or bool(flat["willing_to_relocate"])


def notice_period_bonus(flat: dict) -> float:
    """SOFT bonus -- see module docstring. Never use as a hard filter."""
    days = flat["notice_period_days"]
    if days < 30:
        return 1.0
    if days <= 60:
        return 0.6
    if days <= 90:
        return 0.3
    return 0.0


# Note: Notice period is scored dynamically, other signals are boolean attributes.
POSITIVE_SIGNALS = {
    "production_retrieval_experience": has_production_retrieval_experience,
    "eval_framework_experience": has_eval_framework_experience,
    "hr_tech_exposure": has_hr_tech_exposure,
    "open_source_validation": has_open_source_validation,
    "india_or_relocate": india_or_relocate,
}


# ---------------------------------------------------------------------------
# Composite rubric result
# ---------------------------------------------------------------------------

@dataclass
class RubricResult:
    disqualifier_hits: list[str] = field(default_factory=list)
    positive_hits: list[str] = field(default_factory=list)
    notice_bonus: float = 0.0
    disqualifier_multiplier: float = 1.0   # multiplied into the final composite score
    positive_score: float = 0.0            # 0..1, fraction of positive signals hit


def score_candidate(flat: dict) -> RubricResult:
    disqualifier_hits = [name for name, fn in DISQUALIFIERS.items() if fn(flat)]
    positive_hits = [name for name, fn in POSITIVE_SIGNALS.items() if fn(flat)]

    # A hard disqualifier doesn't necessarily mean zero -- the JD itself says it'll
    # "seriously consider candidates outside the band if other signals are strong" --
    # so this is a steep multiplicative penalty, not an absolute exclusion. Tune
    # NUM_DISQUALIFIERS_TO_GUTTER if you want a harder or softer cutoff.
    if len(disqualifier_hits) >= 2:
        multiplier = 0.05
    elif len(disqualifier_hits) == 1:
        multiplier = 0.35
    else:
        multiplier = 1.0

    return RubricResult(
        disqualifier_hits=disqualifier_hits,
        positive_hits=positive_hits,
        notice_bonus=notice_period_bonus(flat),
        disqualifier_multiplier=multiplier,
        positive_score=len(positive_hits) / len(POSITIVE_SIGNALS),
    )
