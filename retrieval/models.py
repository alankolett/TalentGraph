from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    candidate_id: str = Field(min_length=1)
    bm25_score: float = 0.0
    dense_score: float = 0.0
    passes_hard_filters: bool = True
    fused_score: float = 0.0
