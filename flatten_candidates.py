"""
flatten_candidates.py
----------------------
Phase 2: streaming loader + schema validation + feature flattening for the
Redrob "candidates.jsonl" dataset (100,000 records, ~487MB).

Design notes:
- Streams the file line-by-line. NEVER do json.load() on the whole file.
- Validation is hand-written against candidate_schema.json's exact rules rather
  than depending on a jsonschema/pydantic package, so this has zero third-party
  dependencies and can't drift from what's actually in the file.
- Heavy work (parsing + validating + flattening all 100K records) happens here,
  offline, with no time limit. rank.py just loads the cached pickle this module
  produces -- that's what keeps the timed online step fast.
- Sentinel values (-1) for github_activity_score / offer_acceptance_rate are
  preserved as-is here, NOT coerced to 0. Downstream code must check for -1
  explicitly before treating these as real scores.
"""
from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import Iterator

VALID_COMPANY_SIZES = {"1-10", "11-50", "51-200", "201-500", "501-1000",
                        "1001-5000", "5001-10000", "10001+"}
VALID_PROFICIENCY = {"beginner", "intermediate", "advanced", "expert"}
VALID_EDU_TIER = {"tier_1", "tier_2", "tier_3", "tier_4", "unknown"}
VALID_WORK_MODE = {"remote", "hybrid", "onsite", "flexible"}

import re
CANDIDATE_ID_RE = re.compile(r"^CAND_[0-9]{7}$")


def stream_jsonl(path: str | Path) -> Iterator[dict]:
    """Yield one parsed JSON object per line. Never loads the full file at once."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def validate_record(rec: dict) -> list[str]:
    """Return a list of validation error strings. Empty list = valid record."""
    errors = []

    cid = rec.get("candidate_id", "")
    if not CANDIDATE_ID_RE.match(cid):
        errors.append(f"candidate_id '{cid}' does not match CAND_XXXXXXX pattern")

    profile = rec.get("profile")
    if not profile:
        errors.append("missing profile")
    else:
        if profile.get("current_company_size") not in VALID_COMPANY_SIZES:
            errors.append(f"invalid current_company_size: {profile.get('current_company_size')}")
        yoe = profile.get("years_of_experience")
        if not isinstance(yoe, (int, float)) or not (0 <= yoe <= 50):
            errors.append(f"invalid years_of_experience: {yoe}")

    history = rec.get("career_history")
    if not history or not (1 <= len(history) <= 10):
        errors.append(f"career_history must have 1-10 entries, got {len(history) if history else 0}")
    else:
        for i, ch in enumerate(history):
            if ch.get("company_size") not in VALID_COMPANY_SIZES:
                errors.append(f"career_history[{i}] invalid company_size: {ch.get('company_size')}")
            if not isinstance(ch.get("duration_months"), int) or ch["duration_months"] < 0:
                errors.append(f"career_history[{i}] invalid duration_months")

    for i, edu in enumerate(rec.get("education", [])):
        if edu.get("tier") not in VALID_EDU_TIER:
            errors.append(f"education[{i}] invalid tier: {edu.get('tier')}")

    for i, sk in enumerate(rec.get("skills", [])):
        if sk.get("proficiency") not in VALID_PROFICIENCY:
            errors.append(f"skills[{i}] invalid proficiency: {sk.get('proficiency')}")

    sig = rec.get("redrob_signals")
    if not sig:
        errors.append("missing redrob_signals")
    else:
        if sig.get("preferred_work_mode") not in VALID_WORK_MODE:
            errors.append(f"invalid preferred_work_mode: {sig.get('preferred_work_mode')}")
        gh = sig.get("github_activity_score")
        if not (gh == -1 or 0 <= gh <= 100):
            errors.append(f"invalid github_activity_score: {gh}")
        oar = sig.get("offer_acceptance_rate")
        if not (oar == -1 or 0 <= oar <= 1):
            errors.append(f"invalid offer_acceptance_rate: {oar}")
        npd = sig.get("notice_period_days")
        if not isinstance(npd, int) or not (0 <= npd <= 180):
            errors.append(f"invalid notice_period_days: {npd}")

    return errors


def flatten_candidate(rec: dict) -> dict:
    """
    Produce a flat dict with engineered scalar features ON TOP of the original
    nested structures (career_history, skills, education, redrob_signals are kept
    as-is, since jd_rubric.py and honeypot_detector.py need to scan them directly).
    """
    profile = rec["profile"]
    history = rec["career_history"]
    skills = rec.get("skills", [])
    sig = rec["redrob_signals"]

    total_career_months = sum(ch["duration_months"] for ch in history)
    employers = [ch["company"].strip() for ch in history]
    current_role = next((ch for ch in history if ch["is_current"]), history[-1])

    text_parts = [profile.get("headline", ""), profile.get("summary", "")]
    for ch in history:
        text_parts.append(ch.get("title", ""))
        text_parts.append(ch.get("description", ""))
    all_text = " ".join(text_parts)

    return {
        # identity / direct profile fields
        "candidate_id": rec["candidate_id"],
        "current_title": profile["current_title"],
        "current_company": profile["current_company"],
        "current_industry": profile["current_industry"],
        "years_of_experience": profile["years_of_experience"],
        "location": profile["location"],
        "country": profile["country"],

        # engineered scalars
        "total_career_months": total_career_months,
        "num_employers": len(employers),
        "employers": employers,
        "current_role_duration_months": current_role["duration_months"],
        "current_role_description": current_role.get("description", ""),
        "all_text": all_text,
        "all_text_lower": all_text.lower(),
        "num_skills": len(skills),
        "num_expert_skills": sum(1 for s in skills if s["proficiency"] == "expert"),

        # behavioral signals, passed through with sentinels intact
        "notice_period_days": sig["notice_period_days"],
        "willing_to_relocate": sig["willing_to_relocate"],
        "preferred_work_mode": sig["preferred_work_mode"],
        "recruiter_response_rate": sig["recruiter_response_rate"],
        "interview_completion_rate": sig["interview_completion_rate"],
        "github_activity_score": sig["github_activity_score"],       # -1 = no GitHub
        "offer_acceptance_rate": sig["offer_acceptance_rate"],       # -1 = no history
        "open_to_work_flag": sig["open_to_work_flag"],
        "last_active_date": sig["last_active_date"],
        "verified_email": sig["verified_email"],
        "verified_phone": sig["verified_phone"],
        "linkedin_connected": sig["linkedin_connected"],
        "profile_completeness_score": sig["profile_completeness_score"],
        "endorsements_received": sig["endorsements_received"],

        # raw nested structures, kept for deep rule-checking downstream
        "career_history": history,
        "skills": skills,
        "education": rec.get("education", []),
        "redrob_signals": sig,
    }


def load_and_cache(
    jsonl_path: str | Path,
    cache_path: str | Path,
    force_rebuild: bool = False,
) -> list[dict]:
    """
    Load, validate, and flatten all candidates -- using a pickle cache so repeated
    dev runs (and the actual rank.py invocation) skip re-parsing the 487MB file.
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not force_rebuild:
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    t0 = time.time()
    flattened = []
    n_errors = 0
    for rec in stream_jsonl(jsonl_path):
        errors = validate_record(rec)
        if errors:
            n_errors += 1
            if n_errors <= 5:
                print(f"  [validation] {rec.get('candidate_id', '?')}: {errors}")
            continue
        flattened.append(flatten_candidate(rec))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(flattened, f)

    elapsed = time.time() - t0
    print(f"[flatten_candidates] loaded {len(flattened)} valid candidates "
          f"({n_errors} failed validation) in {elapsed:.1f}s -> cached at {cache_path}")
    return flattened


if __name__ == "__main__":
    import sys
    jsonl = sys.argv[1] if len(sys.argv) > 1 else "./data/raw/redrob_challenge/candidates.jsonl"
    cache = sys.argv[2] if len(sys.argv) > 2 else "./data/processed/candidates_flat.pkl"
    data = load_and_cache(jsonl, cache, force_rebuild=True)
    print(f"Done. {len(data)} candidates ready at {cache}")
