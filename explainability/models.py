from pydantic import BaseModel, Field


class ExplainedCandidate(BaseModel):
    candidate_id: str = Field(min_length=1)
    rank: int = Field(ge=1)
    final_score: float
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    narrative: str = Field(min_length=1)
