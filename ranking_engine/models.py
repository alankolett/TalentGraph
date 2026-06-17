from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    skill_overlap: float | None = 0.0
    kg_skill_distance: float | None = 0.0
    dense_similarity: float | None = 0.0
    bm25_score: float | None = 0.0
    trajectory_alignment: float | None = 0.0
    behavioral_score: float | None = 0.0
    seniority_match: float | None = 0.0


class ScoredCandidate(BaseModel):
    candidate_id: str = Field(min_length=1)
    final_score: float
    features: FeatureVector
    score_breakdown: dict[str, float] = Field(default_factory=dict)
