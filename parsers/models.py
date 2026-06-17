from pydantic import BaseModel, Field, field_validator


class ExperienceEntry(BaseModel):
    title: str = Field(min_length=1)
    company: str | None = None
    start: str | None = None
    end: str | None = None
    duration_months: int | None = Field(default=None, ge=0)
    description: str = ""


class ParsedResume(BaseModel):
    candidate_id: str = Field(min_length=1)
    sections: dict[str, str] = Field(default_factory=dict)
    raw_skills: list[str] = Field(default_factory=list)
    experience_entries: list[ExperienceEntry] = Field(default_factory=list)


class ParsedJob(BaseModel):
    job_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    seniority: str | None = None
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    raw_text: str = Field(min_length=1)

    @field_validator("must_have", "nice_to_have", "responsibilities", mode="before")
    @classmethod
    def normalize_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]
        return [str(value).strip()]

