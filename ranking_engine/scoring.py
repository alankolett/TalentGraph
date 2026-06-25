from ranking_engine.models import FeatureVector, ScoredCandidate

DEFAULT_WEIGHTS = {
    "skill_overlap": 0.25,
    "kg_skill_distance": 0.20,
    "dense_similarity": 0.20,
    "bm25_score": 0.10,
    "trajectory_alignment": 0.10,
    "behavioral_score": 0.10,
    "seniority_match": 0.05,
}


class ScoringEngine:
    """Computes composite explainable scores for candidate profiles using weights."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS

    def score_candidate(self, candidate_id: str, features: FeatureVector) -> ScoredCandidate:
        """Compute the weighted sum score. Renormalizes weights if features are missing."""
        feat_dict = features.model_dump()

        # Identify which features are available (not None)
        available_keys = [
            k for k, v in feat_dict.items() if v is not None and k in self.weights
        ]
        weight_sum = sum(self.weights[k] for k in available_keys)

        if weight_sum <= 0.0:
            return ScoredCandidate(
                candidate_id=candidate_id,
                final_score=0.0,
                features=features,
                score_breakdown={k: 0.0 for k in feat_dict},
            )

        # Renormalize weights of available features so they sum up to 1.0
        renormalized = {k: self.weights[k] / weight_sum for k in available_keys}

        score_breakdown = {}
        final_score = 0.0
        for k, val in feat_dict.items():
            if k in renormalized and val is not None:
                weighted_val = float(val * renormalized[k])
                score_breakdown[k] = weighted_val
                final_score += weighted_val
            else:
                score_breakdown[k] = 0.0

        # Apply Phase 8 penalties
        num_flags = len(features.jd_disqualifier_flags)
        if num_flags > 0:
            if features.jd_positive_signal_count >= 5:
                penalty = max(0.0, 1.0 - 0.1 * num_flags)
            else:
                penalty = 0.5 ** num_flags
            final_score *= penalty

        if features.honeypot_score > 0.0:
            final_score *= 0.01

        return ScoredCandidate(
            candidate_id=candidate_id,
            final_score=final_score,
            features=features,
            score_breakdown=score_breakdown,
        )
