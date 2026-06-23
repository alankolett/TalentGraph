import re
from pathlib import Path
from typing import Any, Literal, TypeVar

import docx
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

from preprocessing.models import CandidateRecord, JobRecord, RejectedRecord

ModelT = TypeVar("ModelT", bound=BaseModel)


class ProfileModel(BaseModel):
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float = Field(ge=0, le=50)
    current_title: str
    current_company: str
    current_company_size: Literal[
        "1-10",
        "11-50",
        "51-200",
        "201-500",
        "501-1000",
        "1001-5000",
        "5001-10000",
        "10001+",
    ]
    current_industry: str


class CareerEntryModel(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str | None
    duration_months: int = Field(ge=0)
    is_current: bool
    industry: str
    company_size: Literal[
        "1-10",
        "11-50",
        "51-200",
        "201-500",
        "501-1000",
        "1001-5000",
        "5001-10000",
        "10001+",
    ]
    description: str


class EducationEntryModel(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int = Field(ge=1970, le=2030)
    end_year: int = Field(ge=1970, le=2035)
    grade: str | None = None
    tier: Literal["tier_1", "tier_2", "tier_3", "tier_4", "unknown"]


class SkillEntryModel(BaseModel):
    name: str
    proficiency: Literal["beginner", "intermediate", "advanced", "expert"]
    endorsements: int = Field(ge=0)
    duration_months: int | None = Field(default=None, ge=0)


class CertificationEntryModel(BaseModel):
    name: str
    issuer: str
    year: int


class LanguageEntryModel(BaseModel):
    language: str
    proficiency: Literal["basic", "conversational", "professional", "native"]


class ExpectedSalaryModel(BaseModel):
    min: float = Field(ge=0)
    max: float = Field(ge=0)


class RedrobSignalsModel(BaseModel):
    profile_completeness_score: float = Field(ge=0, le=100)
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int = Field(ge=0)
    applications_submitted_30d: int = Field(ge=0)
    recruiter_response_rate: float = Field(ge=0, le=1)
    avg_response_time_hours: float = Field(ge=0)
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(ge=0)
    endorsements_received: int = Field(ge=0)
    notice_period_days: int = Field(ge=0, le=180)
    expected_salary_range_inr_lpa: ExpectedSalaryModel
    preferred_work_mode: Literal["remote", "hybrid", "onsite", "flexible"]
    willing_to_relocate: bool
    github_activity_score: float = Field(ge=-1, le=100)
    search_appearance_30d: int = Field(ge=0)
    saved_by_recruiters_30d: int = Field(ge=0)
    interview_completion_rate: float = Field(ge=0, le=1)
    offer_acceptance_rate: float = Field(ge=-1, le=1)
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool


class CandidateSchemaValidator(BaseModel):
    candidate_id: str
    profile: ProfileModel
    career_history: list[CareerEntryModel] = Field(min_length=1, max_length=10)
    education: list[EducationEntryModel] = Field(max_length=5)
    skills: list[SkillEntryModel]
    certifications: list[CertificationEntryModel] | None = None
    languages: list[LanguageEntryModel] | None = None
    redrob_signals: RedrobSignalsModel

    @field_validator("candidate_id")
    @classmethod
    def check_candidate_id(cls, v: str) -> str:
        if not re.match(r"^CAND_[0-9]{7}$", v):
            raise ValueError("Invalid candidate ID format. Must match CAND_XXXXXXX.")
        return v


def validate_against_schema(record: dict[str, Any]) -> tuple[bool, str | None]:
    try:
        CandidateSchemaValidator.model_validate(record)
        return True, None
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        return False, "; ".join(messages)


class JDStructurer:
    """Structure raw job description docx into JobRecord."""

    def structure_jd(self, docx_path: str | Path) -> JobRecord:
        doc = docx.Document(docx_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])

        title = "Senior AI Engineer — Founding Team"
        seniority = "Senior"
        location = "Pune/Noida, India"

        must_have = [
            "embeddings-based retrieval systems",
            "vector databases",
            "hybrid search infrastructure",
            "Python",
            "evaluation frameworks for ranking systems",
        ]

        nice_to_have = [
            "LLM fine-tuning",
            "learning-to-rank models",
            "HR-tech",
            "recruiting tech",
            "marketplace products",
            "distributed systems",
            "large-scale inference optimization",
            "open-source contributions",
        ]

        return JobRecord(
            id="job_redrob_senior_ai_engineer",
            title=title,
            raw_description=full_text,
            must_have_skills=must_have,
            nice_to_have_skills=nice_to_have,
            seniority=seniority,
            location=location,
        )


class SchemaValidator:
    """Validate cleaned rows against canonical pydantic models."""

    def validate_schema(
        self,
        df: pd.DataFrame,
        model: type[ModelT],
        record_type: str,
        source: str,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for index, row in df.reset_index(drop=True).iterrows():
            payload = row.to_dict()
            try:
                record = model.model_validate(payload)
            except ValidationError as exc:
                rejected.append(
                    RejectedRecord(
                        source=source,
                        row_index=index,
                        record_type=record_type,
                        record_id=str(payload.get("id")) if payload.get("id") else None,
                        reason=self._format_error(exc),
                        payload=payload,
                    ).model_dump(mode="json")
                )
                continue
            accepted.append(record.model_dump(mode="json"))

        return pd.DataFrame(accepted), pd.DataFrame(rejected)

    def validate_candidates(
        self, df: pd.DataFrame, source: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self.validate_schema(df, CandidateRecord, "candidate", source)

    def validate_jobs(self, df: pd.DataFrame, source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self.validate_schema(df, JobRecord, "job", source)

    def _format_error(self, exc: ValidationError) -> str:
        messages = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        return "; ".join(messages)
