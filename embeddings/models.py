from typing import Any

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    backend: str = "hash"
    dimension: int = Field(default=128, ge=32, le=1024)
    candidate_instruction: str = "Represent this candidate profile for retrieval:"
    job_instruction: str = "Represent this job description for retrieving matching candidates:"
    max_tokens: int = Field(default=2048, ge=128)


class CandidateVectorPoint(BaseModel):
    id: str
    vector: list[float]
    payload: dict[str, Any] = Field(default_factory=dict)


class VectorSearchResult(BaseModel):
    id: str
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)
