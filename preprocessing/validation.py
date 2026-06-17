from typing import Any, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError

from preprocessing.models import CandidateRecord, JobRecord, RejectedRecord

ModelT = TypeVar("ModelT", bound=BaseModel)


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
