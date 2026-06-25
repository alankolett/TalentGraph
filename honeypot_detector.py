"""
honeypot_detector.py
---------------------
Phase 7: detects internally-inconsistent ("honeypot") candidate profiles.

These two checks were validated by running them against the full real 100K
dataset before being written here:
  - expert_zero_duration:   84 hits across 21 unique candidates
  - exp_inconsistent:       22 unique candidates

NOTE: a third candidate check (skill duration_months exceeding total career
months) was tested and REJECTED -- it false-positived on ~9,300 of 100,000
candidates, which is far too noisy to be a real signal (the spec implies only
~80 honeypots exist in total). Do not add it back without re-validating against
the full dataset first.

The spec states honeypot rate >10% in your top 100 causes automatic Stage-3
disqualification -- so treat detect_honeypots() as something to keep candidates
OUT of your top 100, not just a minor scoring penalty.

There are likely 1-2 more honeypot archetypes in the data beyond these two.
If you find more by sampling flagged vs. unflagged records, add them as new,
independently-named checks below -- each one should be defensible on its own,
since you may need to explain these exact rules at the Stage 5 interview.
"""
from __future__ import annotations


def detect_honeypots(flat: dict) -> list[str]:
    """
    flat: a flattened candidate dict from flatten_candidates.flatten_candidate().
    Returns a list of flag strings; empty list means no honeypot signal found.
    """
    flags = []

    # Check 1: "expert" proficiency claimed with ~zero time spent on the skill.
    for sk in flat["skills"]:
        if sk["proficiency"] == "expert" and sk.get("duration_months", 0) <= 1:
            flags.append(f"expert_zero_duration:{sk['name']}")

    # Check 2: stated years_of_experience is wildly smaller than the sum of all
    # career_history durations -- i.e. the career history alone implies far more
    # experience than the candidate claims to have.
    total_years = flat["total_career_months"] / 12.0
    if total_years > flat["years_of_experience"] + 3:
        flags.append("career_history_exceeds_stated_experience")

    return flags


def honeypot_rate(flagged_in_topn: int, n: int = 100) -> float:
    """Convenience helper: what fraction of your top-N are honeypot-flagged."""
    return flagged_in_topn / n


if __name__ == "__main__":
    # Quick self-check against the real dataset.
    import sys
    sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
    from flatten_candidates import load_and_cache

    candidates = load_and_cache(
        "./data/raw/redrob_challenge/candidates.jsonl",
        "./data/processed/candidates_flat.pkl",
    )
    flagged = {c["candidate_id"]: detect_honeypots(c) for c in candidates}
    flagged = {k: v for k, v in flagged.items() if v}
    print(f"{len(flagged)} unique candidates flagged out of {len(candidates)}")
    for cid, flags in list(flagged.items())[:10]:
        print(f"  {cid}: {flags}")
