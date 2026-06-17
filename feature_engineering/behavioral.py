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


class BehavioralSignalExtractor:
    """Extract and normalize behavioral signals from candidate metadata."""

    def __init__(self, current_date_str: str = "2026-06-17", half_life_days: float = 90.0) -> None:
        self.current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        # Lambda for exponential decay: exp(-lambda * half_life) = 0.5
        self.decay_lambda = -math.log(0.5) / half_life_days

    def extract_raw_profile(self, candidate_id: str, metadata: dict[str, Any], github_url: str | None = None) -> dict[str, Any]:
        """Compute un-normalized behavioral metrics from a candidate's raw metadata."""
        # Check if we have any behavioral signals
        has_signals = bool(metadata) or bool(github_url)
        if not has_signals:
            return {
                "candidate_id": candidate_id,
                "contribution_frequency": 0.0,
                "recency_score": 0.0,
                "learning_velocity": 0.0,
                "open_source_breadth": 0.0,
                "signal_confidence": 0.3,  # Low confidence due to missing metadata
            }

        # 1. Recency Score
        last_active = metadata.get("last_activity_date")
        recency = self.compute_recency_score(last_active)

        # 2. Contribution Frequency
        timeline = metadata.get("timeline", [])
        freq = self.compute_contribution_frequency(timeline)

        # 3. Learning Velocity
        skills_timeline = metadata.get("skills_over_time", [])
        velocity = self.compute_learning_velocity(skills_timeline)

        # 4. Open Source Breadth
        breadth = self.compute_open_source_breadth(github_url, timeline)

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

    def compute_open_source_breadth(self, github_url: str | None, timeline: list[dict[str, Any]] | None) -> float:
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
        metrics = ["contribution_frequency", "recency_score", "learning_velocity", "open_source_breadth"]
        raw_data = {m: [p[m] for p in raw_profiles] for m in metrics}

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
                    signal_confidence=p["signal_confidence"],
                )
            )

        return profiles
