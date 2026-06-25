import json
import math
from datetime import datetime
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class BehavioralProfile(BaseModel):
    candidate_id: str = Field(min_length=1)
    contribution_frequency: float = 0.0
    recency_score: float = 0.0
    learning_velocity: float = 0.0
    open_source_breadth: float = 0.0
    signal_confidence: float = 1.0
    availability_score: float = 0.0
    engagement_score: float = 0.0
    trust_score: float = 0.0
    honeypot_flags: list[str] = Field(default_factory=list)
    honeypot_score: float = 0.0


class HoneypotDetector:
    """Detects internally-inconsistent candidate profiles (honeypots)."""

    def detect_honeypots(
        self,
        skills: list[dict[str, Any]] | str | None,
        career_history: list[dict[str, Any]] | str | None,
        experience_years: float | None,
    ) -> list[str]:
        """Run checks and return a list of flags/reasons if candidate is a honeypot."""
        # Parse JSON if input is a string
        parsed_skills = []
        if isinstance(skills, str):
            try:
                parsed_skills = json.loads(skills)
            except json.JSONDecodeError:
                pass
        elif isinstance(skills, list):
            parsed_skills = skills

        parsed_career = []
        if isinstance(career_history, str):
            try:
                parsed_career = json.loads(career_history)
            except json.JSONDecodeError:
                pass
        elif isinstance(career_history, list):
            parsed_career = career_history

        flags = []

        # 1. Expert proficiency skill with 0 duration
        if parsed_skills:
            for s in parsed_skills:
                prof = str(s.get("proficiency", "")).lower().strip()
                duration = s.get("duration_months")
                if prof == "expert" and duration == 0:
                    flags.append(
                        f"expert_skill_zero_duration: Skill "
                        f"'{s.get('name')}' is expert but has "
                        f"0 months duration"
                    )

        # 2. YoE inconsistent with sum of career history duration
        if experience_years is not None and experience_years > 0:
            if not parsed_career:
                flags.append(
                    "inconsistent_experience_years: Declared YoE > 0 "
                    "but career history is empty"
                )
            else:
                total_months = sum(item.get("duration_months") or 0 for item in parsed_career)
                history_years = total_months / 12.0
                diff = abs(experience_years - history_years)
                if history_years == 0 or diff > max(3.0, 0.5 * experience_years):
                    flags.append(
                        f"inconsistent_experience_years: Declared YoE "
                        f"{experience_years}, but history sum is "
                        f"{history_years:.2f} years"
                    )

        return flags


class BehavioralSignalExtractor:
    """Extract and normalize behavioral signals from candidate metadata."""

    def __init__(self, current_date_str: str = "2026-06-17", half_life_days: float = 90.0) -> None:
        self.current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        # Lambda for exponential decay: exp(-lambda * half_life) = 0.5
        self.decay_lambda = -math.log(0.5) / half_life_days

    def extract_raw_profile(
        self,
        candidate_id: str,
        metadata: dict[str, Any],
        github_url: str | None = None,
        skills: list[dict[str, Any]] | str | None = None,
        career_history: list[dict[str, Any]] | str | None = None,
        experience_years: float | None = None,
    ) -> dict[str, Any]:
        """Compute un-normalized behavioral metrics from a candidate's raw metadata."""
        # Clean sentinel values (-1) from metadata to prevent leaking
        cleaned_meta = {}
        if metadata:
            for k, v in metadata.items():
                if v == -1 or v == -1.0:
                    cleaned_meta[k] = None
                else:
                    cleaned_meta[k] = v

        # Check if we have any behavioral signals
        has_signals = bool(cleaned_meta) or bool(github_url)
        if not has_signals:
            # Run honeypot detector even for empty signals if skills/career exist
            detector = HoneypotDetector()
            honeypot_flags = detector.detect_honeypots(skills, career_history, experience_years)
            honeypot_score = 1.0 if honeypot_flags else 0.0

            return {
                "candidate_id": candidate_id,
                "contribution_frequency": 0.0,
                "recency_score": 0.0,
                "learning_velocity": 0.0,
                "open_source_breadth": 0.0,
                "signal_confidence": 0.3,  # Low confidence due to missing metadata
                "availability_score": 0.0,
                "engagement_score": 0.0,
                "trust_score": 0.0,
                "honeypot_flags": honeypot_flags,
                "honeypot_score": honeypot_score,
            }

        # 1. Recency Score
        last_active = cleaned_meta.get("last_active_date") or cleaned_meta.get("last_activity_date")
        recency = self.compute_recency_score(last_active)

        # 2. Contribution Frequency
        timeline = cleaned_meta.get("timeline", [])
        freq = self.compute_contribution_frequency(timeline)

        # 3. Learning Velocity
        skills_timeline = cleaned_meta.get("skills_over_time", [])
        velocity = self.compute_learning_velocity(skills_timeline)

        # 4. Open Source Breadth
        breadth = self.compute_open_source_breadth(github_url, timeline)

        # 5. Availability Score
        open_to_work = cleaned_meta.get("open_to_work_flag")
        open_to_work_val = 1.0 if open_to_work is True else (0.5 if open_to_work is None else 0.0)
        notice_days = cleaned_meta.get("notice_period_days")
        if notice_days is not None:
            if notice_days < 30:
                notice_score = 1.0
            elif notice_days <= 60:
                notice_score = 0.5
            elif notice_days <= 90:
                notice_score = 0.2
            else:
                notice_score = 0.0
        else:
            notice_score = 0.5
        availability = 0.4 * recency + 0.4 * open_to_work_val + 0.2 * notice_score

        # 6. Engagement Score
        resp_rate = cleaned_meta.get("recruiter_response_rate")
        resp_rate_val = float(resp_rate) if resp_rate is not None else 0.5
        resp_time = cleaned_meta.get("avg_response_time_hours")
        if resp_time is not None:
            resp_time_score = 1.0 / (1.0 + float(resp_time) / 24.0)
        else:
            resp_time_score = 0.5
        int_completion = cleaned_meta.get("interview_completion_rate")
        int_completion_val = float(int_completion) if int_completion is not None else 0.5
        engagement = 0.4 * resp_rate_val + 0.3 * resp_time_score + 0.3 * int_completion_val

        # 7. Trust Score
        email_val = 1.0 if cleaned_meta.get("verified_email") is True else 0.0
        phone_val = 1.0 if cleaned_meta.get("verified_phone") is True else 0.0
        li_val = 1.0 if cleaned_meta.get("linkedin_connected") is True else 0.0

        parsed_skills = []
        if isinstance(skills, str):
            try:
                parsed_skills = json.loads(skills)
            except json.JSONDecodeError:
                pass
        elif isinstance(skills, list):
            parsed_skills = skills

        num_skills = len(parsed_skills) if parsed_skills else 1
        endorsements = cleaned_meta.get("endorsements_received")
        if endorsements is not None:
            endorse_score = min(1.0, float(endorsements) / max(1.0, float(num_skills)) / 5.0)
        else:
            endorse_score = 0.5
        trust = 0.2 * email_val + 0.2 * phone_val + 0.2 * li_val + 0.4 * endorse_score

        # 8. Honeypot check
        detector = HoneypotDetector()
        honeypot_flags = detector.detect_honeypots(skills, career_history, experience_years)
        honeypot_score = 1.0 if honeypot_flags else 0.0

        # Confidence is high (1.0) unless essential metrics are completely missing
        confidence = 1.0
        missing_count = sum(1 for v in [last_active, timeline, skills_timeline] if not v)
        if missing_count > 0:
            confidence = max(0.4, 1.0 - (0.2 * missing_count))

        return {
            "candidate_id": candidate_id,
            "contribution_frequency": freq,
            "recency_score": recency,
            "learning_velocity": velocity,
            "open_source_breadth": breadth,
            "signal_confidence": confidence,
            "availability_score": availability,
            "engagement_score": engagement,
            "trust_score": trust,
            "honeypot_flags": honeypot_flags,
            "honeypot_score": honeypot_score,
        }

    def compute_recency_score(self, last_activity_date_str: str | None) -> float:
        """Calculate recency score using exponential time decay."""
        if not last_activity_date_str:
            return 0.5  # Neutral default for missing value
        try:
            active_date = datetime.strptime(str(last_activity_date_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            return 0.5

        delta = (self.current_date - active_date).days
        if delta < 0:
            delta = 0  # clamp future dates
        return float(math.exp(-self.decay_lambda * delta))

    def compute_contribution_frequency(self, timeline: list[dict[str, Any]] | None) -> float:
        """Compute the total activity count in the timeline."""
        if not timeline:
            return 0.0
        # Sum counts or fallback to 1 per timeline event
        return float(sum(float(event.get("count", 1.0)) for event in timeline))

    def compute_learning_velocity(self, skills_over_time: list[dict[str, Any]] | None) -> float:
        """Rate of new skills acquired (number of unique skills added over time)."""
        if not skills_over_time or len(skills_over_time) < 2:
            return 0.0

        # Sort by date
        sorted_timeline = sorted(
            skills_over_time,
            key=lambda x: datetime.strptime(x.get("date", "2000-01-01"), "%Y-%m-%d")
        )

        initial_skills = set(sorted_timeline[0].get("skills", []))
        all_skills = set(initial_skills)
        for state in sorted_timeline[1:]:
            all_skills.update(state.get("skills", []))

        added_skills_count = len(all_skills - initial_skills)

        # Calculate time span in years
        try:
            start_date = datetime.strptime(sorted_timeline[0]["date"], "%Y-%m-%d")
            end_date = datetime.strptime(sorted_timeline[-1]["date"], "%Y-%m-%d")
            years = (end_date - start_date).days / 365.25
        except (ValueError, KeyError, ZeroDivisionError):
            years = 0.0

        if years <= 0.1:
            return float(added_skills_count)  # return flat count if no time span

        return float(added_skills_count / years)

    def compute_open_source_breadth(
        self,
        github_url: str | None,
        timeline: list[dict[str, Any]] | None,
    ) -> float:
        """Measure open source contribution diversity."""
        score = 0.0
        if github_url:
            score += 0.4  # base score for active GitHub profile

        if timeline:
            # count distinct project names or repositories if specified
            repos = {event.get("repo") for event in timeline if event.get("repo")}
            score += 0.1 * len(repos)

        return float(min(1.0, score))


class SignalNormalizer:
    """Normalize raw signal profiles relative to the population."""

    def normalize_population(self, raw_profiles: list[dict[str, Any]]) -> list[BehavioralProfile]:
        if not raw_profiles:
            return []

        # Extract values for columns to normalize
        metrics = [
            "contribution_frequency",
            "recency_score",
            "learning_velocity",
            "open_source_breadth",
            "availability_score",
            "engagement_score",
            "trust_score",
        ]
        raw_data = {m: [p.get(m, 0.0) for p in raw_profiles] for m in metrics}

        normalized_data = {}
        for metric in metrics:
            vals = np.array(raw_data[metric], dtype=np.float32)
            val_min = float(np.min(vals))
            val_max = float(np.max(vals))
            diff = val_max - val_min

            if diff > 0:
                normalized_data[metric] = ((vals - val_min) / diff).tolist()
            else:
                # If all values are the same, give them a neutral/base score
                normalized_data[metric] = [0.5] * len(vals)

        profiles = []
        for idx, p in enumerate(raw_profiles):
            profiles.append(
                BehavioralProfile(
                    candidate_id=p["candidate_id"],
                    contribution_frequency=normalized_data["contribution_frequency"][idx],
                    recency_score=normalized_data["recency_score"][idx],
                    learning_velocity=normalized_data["learning_velocity"][idx],
                    open_source_breadth=normalized_data["open_source_breadth"][idx],
                    signal_confidence=p.get("signal_confidence", 1.0),
                    availability_score=normalized_data["availability_score"][idx],
                    engagement_score=normalized_data["engagement_score"][idx],
                    trust_score=normalized_data["trust_score"][idx],
                    honeypot_flags=p.get("honeypot_flags", []),
                    honeypot_score=p.get("honeypot_score", 0.0),
                )
            )

        return profiles

