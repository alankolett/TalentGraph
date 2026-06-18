from ranking_engine.models import FeatureVector


class TagClassifier:
    """Classifies candidates into descriptive tags based on feature vectors."""

    def classify_tags(self, features: FeatureVector) -> list[str]:
        """Classify candidate into tags using deterministic threshold rules."""
        tags = []

        # 1. Hidden Gem: High behavioral activity/score, but lower bi-encoder similarity matching
        # (meaning they are highly active in open source but might not be standard keyword matches)
        behavioral = features.behavioral_score or 0.0
        dense = features.dense_similarity or 0.0
        if behavioral >= 0.7 and dense < 0.6:
            tags.append("Hidden Gem")

        # 2. Fast Learner: High behavioral score + strong career trajectory alignment
        trajectory = features.trajectory_alignment or 0.0
        if behavioral >= 0.6 and trajectory >= 0.6:
            tags.append("Fast Learner")

        # 3. Career Switcher: High trajectory alignment (progression/duration) but low direct skill overlap
        overlap = features.skill_overlap or 0.0
        if trajectory >= 0.7 and overlap < 0.4:
            tags.append("Career Switcher")

        return tags
