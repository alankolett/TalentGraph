from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from rapidfuzz import fuzz

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: Any) -> str:
    if text is None or pd.isna(text):
        return ""
    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = html.unescape(normalized)
    normalized = TAG_RE.sub(" ", normalized)
    normalized = normalized.replace("\u00a0", " ")
    return WHITESPACE_RE.sub(" ", normalized).strip()


def normalize_optional_text(text: Any) -> str | None:
    cleaned = clean_text(text)
    return cleaned or None


def split_skills(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := clean_text(item))]
    if pd.isna(value):
        return []
    return [
        cleaned for item in str(value).replace("|", ",").split(",") if (cleaned := clean_text(item))
    ]


def first_present(row: pd.Series, aliases: tuple[str, ...], default: Any = None) -> Any:
    for alias in aliases:
        if alias in row and not is_missing(row[alias]):
            return row[alias]
    return default


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list | dict):
        return False
    return bool(pd.isna(value))


@dataclass
class DataCleaner:
    duplicate_threshold: int = 99
    candidate_aliases: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "id": ("id", "candidate_id", "uid"),
            "raw_resume_text": ("raw_resume_text", "resume", "resume_text", "raw_text"),
            "skills_raw": ("skills_raw", "skills", "skill_list"),
            "experience_years": ("experience_years", "years_experience", "yoe"),
            "education": ("education", "degree"),
            "location": ("location", "city"),
            "github_url": ("github_url", "github", "github_profile"),
            "activity_metadata": ("activity_metadata", "metadata"),
        }
    )
    job_aliases: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "id": ("id", "job_id", "requisition_id"),
            "title": ("title", "job_title", "role"),
            "raw_description": ("raw_description", "description", "job_description"),
            "must_have_skills": ("must_have_skills", "required_skills", "must_haves"),
            "nice_to_have_skills": ("nice_to_have_skills", "preferred_skills", "nice_haves"),
            "seniority": ("seniority", "level"),
            "location": ("location", "city"),
        }
    )

    def clean_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": clean_text(first_present(row, self.candidate_aliases["id"])),
                    "raw_resume_text": clean_text(
                        first_present(row, self.candidate_aliases["raw_resume_text"])
                    ),
                    "skills_raw": split_skills(
                        first_present(row, self.candidate_aliases["skills_raw"])
                    ),
                    "experience_years": self._to_float(
                        first_present(row, self.candidate_aliases["experience_years"])
                    ),
                    "education": normalize_optional_text(
                        first_present(row, self.candidate_aliases["education"])
                    ),
                    "location": normalize_optional_text(
                        first_present(row, self.candidate_aliases["location"])
                    ),
                    "github_url": normalize_optional_text(
                        first_present(row, self.candidate_aliases["github_url"])
                    ),
                    "activity_metadata": self._metadata(
                        first_present(row, self.candidate_aliases["activity_metadata"], {})
                    ),
                }
            )
        return pd.DataFrame(rows)

    def clean_jobs(self, df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": clean_text(first_present(row, self.job_aliases["id"])),
                    "title": clean_text(first_present(row, self.job_aliases["title"])),
                    "raw_description": clean_text(
                        first_present(row, self.job_aliases["raw_description"])
                    ),
                    "must_have_skills": split_skills(
                        first_present(row, self.job_aliases["must_have_skills"])
                    ),
                    "nice_to_have_skills": split_skills(
                        first_present(row, self.job_aliases["nice_to_have_skills"])
                    ),
                    "seniority": normalize_optional_text(
                        first_present(row, self.job_aliases["seniority"])
                    ),
                    "location": normalize_optional_text(
                        first_present(row, self.job_aliases["location"])
                    ),
                }
            )
        return pd.DataFrame(rows)

    def deduplicate_candidates(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self._deduplicate(df, key_columns=("id",), fuzzy_column="raw_resume_text")

    def deduplicate_jobs(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self._deduplicate(df, key_columns=("id",), fuzzy_column="raw_description")

    def _deduplicate(
        self, df: pd.DataFrame, key_columns: tuple[str, ...], fuzzy_column: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for index, row in df.reset_index(drop=True).iterrows():
            payload = row.to_dict()
            key = tuple(payload.get(column) for column in key_columns)
            if key in seen_keys:
                rejected.append({"row_index": index, "reason": "duplicate_id", "payload": payload})
                continue

            is_near_duplicate = any(
                fuzz.token_set_ratio(
                    str(payload.get(fuzzy_column, "")),
                    str(item.get(fuzzy_column, "")),
                )
                >= self.duplicate_threshold
                for item in accepted
            )
            if is_near_duplicate:
                rejected.append(
                    {
                        "row_index": index,
                        "reason": "near_duplicate_text",
                        "payload": payload,
                    }
                )
                continue

            seen_keys.add(key)
            accepted.append(payload)

        return pd.DataFrame(accepted), pd.DataFrame(rejected)

    def _to_float(self, value: Any) -> float | None:
        if value is None or is_missing(value) or clean_text(value) == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _metadata(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if value is None or is_missing(value) or clean_text(value) == "":
            return {}
        return {"raw": clean_text(value)}
