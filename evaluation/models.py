from pydantic import BaseModel, Field


class RelevanceJudgment(BaseModel):
    job_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    relevance: int = Field(ge=0, le=3)  # Relevance score from 0 (irrelevant) to 3 (perfect)


class EvaluationResult(BaseModel):
    metric_name: str = Field(min_length=1)
    baseline_score: float
    system_score: float
    delta: float
