from pydantic import BaseModel, Field


class RerankedCandidate(BaseModel):
    candidate_id: str = Field(min_length=1)
    reranker_score: float
    original_rank: int = Field(ge=1)
    new_rank: int = Field(ge=1)
    score_delta: float
