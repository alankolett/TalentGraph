from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from common.llm import LLMProvider
from parsers.models import ParsedJob
from preprocessing.cleaning import clean_text, split_skills

JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
SENIORITY_RE = re.compile(r"\b(intern|junior|mid|senior|staff|principal|lead)\b", re.I)
RESPONSIBILITY_RE = re.compile(r"\b(build|own|design|lead|manage|improve|develop|ship)\b", re.I)


class JDStructuredExtractor:
    """Extract schema-valid job requirements, using an LLM when provided."""

    def __init__(self, llm_provider: LLMProvider | None = None, max_attempts: int = 2) -> None:
        self.llm_provider = llm_provider
        self.max_attempts = max_attempts

    def llm_extract_job_requirements(
        self,
        job_id: str,
        title: str,
        jd_text: str,
        must_have_skills: list[str] | None = None,
        nice_to_have_skills: list[str] | None = None,
        seniority: str | None = None,
        location: str | None = None,
    ) -> ParsedJob:
        base_payload = self._heuristic_payload(
            job_id=job_id,
            title=title,
            jd_text=jd_text,
            must_have_skills=must_have_skills,
            nice_to_have_skills=nice_to_have_skills,
            seniority=seniority,
            location=location,
        )
        if not self.llm_provider:
            return ParsedJob.model_validate(base_payload)

        prompt = self._prompt(base_payload)
        last_error: Exception | None = None
        for _ in range(self.max_attempts):
            try:
                response = self.llm_provider.generate(prompt)
                payload = self._load_json_object(response)
                repaired = {**base_payload, **payload}
                return ParsedJob.model_validate(repaired)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
                prompt = self._repair_prompt(prompt, str(exc))

        if last_error:
            return ParsedJob.model_validate(base_payload)
        return ParsedJob.model_validate(base_payload)

    def _heuristic_payload(
        self,
        job_id: str,
        title: str,
        jd_text: str,
        must_have_skills: list[str] | None,
        nice_to_have_skills: list[str] | None,
        seniority: str | None,
        location: str | None,
    ) -> dict[str, Any]:
        text = clean_text(jd_text)
        inferred_seniority = seniority or self._infer_seniority(title, text)
        responsibilities = self._extract_responsibilities(text)
        return {
            "job_id": job_id,
            "title": clean_text(title),
            "seniority": inferred_seniority,
            "location": clean_text(location) if location else None,
            "must_have": must_have_skills or self._infer_skills(text, "required"),
            "nice_to_have": nice_to_have_skills or self._infer_skills(text, "preferred"),
            "responsibilities": responsibilities,
            "raw_text": text,
        }

    def _infer_seniority(self, title: str, text: str) -> str | None:
        match = SENIORITY_RE.search(f"{title} {text}")
        return match.group(1).lower() if match else None

    def _extract_responsibilities(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+|;|\n", text)
        selected = [
            clean_text(sentence) for sentence in sentences if RESPONSIBILITY_RE.search(sentence)
        ]
        return selected[:8] or [text[:160]]

    def _infer_skills(self, text: str, marker: str) -> list[str]:
        pattern = re.compile(rf"{marker}[^:.]*[:.]\s*(?P<skills>[^.;\n]+)", re.I)
        match = pattern.search(text)
        if not match:
            return []
        return split_skills(match.group("skills"))

    def _prompt(self, payload: dict[str, Any]) -> str:
        schema = ParsedJob.model_json_schema()
        return (
            "Extract this job description into JSON matching the schema. "
            "Return only JSON.\n"
            f"Schema: {json.dumps(schema)}\n"
            f"Job: {json.dumps(payload)}"
        )

    def _repair_prompt(self, prompt: str, error: str) -> str:
        return f"{prompt}\nThe previous JSON was invalid: {error}. Return corrected JSON only."

    def _load_json_object(self, response: str) -> dict[str, Any]:
        match = JSON_OBJECT_RE.search(response)
        if not match:
            raise ValueError("LLM response did not contain a JSON object.")
        payload = json.loads(match.group())
        if not isinstance(payload, dict):
            raise ValueError("LLM response JSON was not an object.")
        return payload
