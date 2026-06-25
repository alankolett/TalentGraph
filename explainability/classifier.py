from ranking_engine.models import FeatureVector


class TagClassifier:
    """Classifies candidates into descriptive tags based on feature vectors.

    Thresholds are calibrated against production feature distributions observed
    in Phase 9 output:
      - behavioral_score: 0.49 – 0.56
      - skill_overlap:    0.03 – 0.07
      - dense_similarity: 0.0  (offline hash-based embeddings)
      - seniority_match:  1.0  (all shortlisted candidates are Senior-level)
      - trajectory_alignment: computed via scoring engine (typically 0.3 – 0.7)
    """

    def classify_tags(self, features: FeatureVector) -> list[str]:
        """Classify candidate into tags using deterministic threshold rules."""
        tags = []

        behavioral = features.behavioral_score or 0.0
        dense = features.dense_similarity or 0.0
        trajectory = features.trajectory_alignment or 0.0
        overlap = features.skill_overlap or 0.0
        seniority = features.seniority_match or 0.0
        honeypot = features.honeypot_score or 0.0
        bm25 = features.bm25_score or 0.0

        # 1. Strong Seniority Fit — seniority perfectly aligned
        if seniority >= 0.9:
            tags.append("Strong Seniority Fit")

        # 2. High Engagement — above-median behavioral score
        if behavioral >= 0.5:
            tags.append("High Engagement")

        # 3. Hidden Gem — engaged profile but low direct keyword/vector match
        #    (lowered dense threshold since offline embeddings are hash-based ~0.0)
        if behavioral >= 0.5 and bm25 < 0.3 and dense < 0.3:
            tags.append("Hidden Gem")

        # 4. Fast Learner — active profile with meaningful career trajectory
        if behavioral >= 0.5 and trajectory >= 0.3:
            tags.append("Fast Learner")

        # 5. Career Switcher — career momentum but narrow direct skill overlap
        if trajectory >= 0.4 and overlap < 0.1:
            tags.append("Career Switcher")

        # 6. Skill Gap Risk — very low skill overlap with job requirements
        if overlap < 0.05:
            tags.append("Skill Gap Risk")

        # 7. Verified Profile — no honeypot signals detected
        if honeypot == 0.0:
            tags.append("Verified Profile")

        return tags
