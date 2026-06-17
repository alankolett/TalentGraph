from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CandidateRecord(BaseModel):
    id: str = Field(min_length=1)
    raw_resume_text: str = Field(min_length=1)
    skills_raw: list[str] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0)
    education: str | None = None
    location: str | None = None
    github_url: HttpUrl | None = None
    activity_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("skills_raw", mode="before")
    @classmethod
    def split_skills(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]
        return [str(value).strip()]


class JobRecord(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    raw_description: str = Field(min_length=20)
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    seniority: str | None = None
    location: str | None = None

    @field_validator("must_have_skills", "nice_to_have_skills", mode="before")
    @classmethod
    def split_skills(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]
        return [str(value).strip()]


class RejectedRecord(BaseModel):
    source: str
    row_index: int
    record_type: str
    record_id: str | None = None
    reason: str
    payload: dict[str, Any]

