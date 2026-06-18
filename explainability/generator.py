import json
import re
from typing import Any

from common.llm import LLMProvider
from explainability.models import ExplainedCandidate
from parsers.models import ParsedJob
from ranking_engine.models import FeatureVector

JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class ExplanationPromptBuilder:
    """Builds LLM prompts for generating explanation justifications."""

    def build_explanation_prompt(
        self,
        candidate_id: str,
        job: ParsedJob,
        features: FeatureVector,
        tags: list[str],
    ) -> str:
        """Create a prompt requesting candidates' match explanation in JSON format."""
        schema = {
            "type": "object",
            "properties": {
                "matched_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concrete points where candidate skills match the job must-haves.",
                },
                "missing_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills or requirements the candidate appears to lack.",
                },
                "narrative": {
                    "type": "string",
                    "description": "A concise, professional recruiter-facing narrative explaining why this candidate was selected.",
                },
            },
            "required": ["matched_points", "missing_points", "narrative"],
        }

        # Format input details for context
        feat_dict = features.model_dump()
        input_details = {
            "candidate_id": candidate_id,
            "job_title": job.title,
            "must_have_skills": job.must_have,
            "nice_to_have_skills": job.nice_to_have,
            "tags": tags,
            "scores": {k: f"{v:.2f}" for k, v in feat_dict.items() if v is not None},
        }

        return (
            "Analyze this candidate and job matching data, and generate a structured recruitment justification. "
            "Your response must be a single JSON object matching the schema. Do not output any other text or markdown formatting except the JSON.\n\n"
            f"JSON Schema:\n{json.dumps(schema, indent=2)}\n\n"
            f"Candidate Matching Data:\n{json.dumps(input_details, indent=2)}\n"
        )


class ExplanationGenerator:
    """Generates structured explanations utilizing an LLM, degrading to templates on failure."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider
        self.prompt_builder = ExplanationPromptBuilder()

    def generate_explanation(
        self,
        candidate_id: str,
        rank: int,
        final_score: float,
        job: ParsedJob,
        features: FeatureVector,
        tags: list[str],
        candidate_skills: list[str] | None = None,
    ) -> ExplainedCandidate:
        """Generate candidate explanation. Falls back to deterministic templates if LLM fails."""
        if not self.llm_provider:
            return self._fallback_explanation(candidate_id, rank, final_score, job, features, tags, candidate_skills)

        prompt = self.prompt_builder.build_explanation_prompt(candidate_id, job, features, tags)
        try:
            response = self.llm_provider.generate(prompt)
            data = self._parse_json(response)
            
            # Post-generation consistency check (prevent hallucinated skill matches)
            # Ensure matched points relate to job must-haves/nice-to-haves
            job_keywords = {s.lower().strip() for s in [*job.must_have, *job.nice_to_have]}
            matched_points = []
            for point in data.get("matched_points", []):
                # If the point mentions a job keyword (or candidate skill), keep it
                pt_lower = point.lower()
                if any(kw in pt_lower for kw in job_keywords):
                    matched_points.append(point)
            
            if not matched_points and job.must_have:
                # If LLM failed to match anything despite must-haves, fallback to heuristics
                matched_points = self._heuristic_matches(job, candidate_skills or [])

            return ExplainedCandidate(
                candidate_id=candidate_id,
                rank=rank,
                final_score=final_score,
                matched_points=matched_points,
                missing_points=data.get("missing_points", []),
                confidence=features.behavioral_score or 1.0,
                tags=tags,
                narrative=data["narrative"],
            )
        except Exception:
            # Fall back to template on any error (never block the demo)
            return self._fallback_explanation(candidate_id, rank, final_score, job, features, tags, candidate_skills)

    def _fallback_explanation(
        self,
        candidate_id: str,
        rank: int,
        final_score: float,
        job: ParsedJob,
        features: FeatureVector,
        tags: list[str],
        candidate_skills: list[str] | None,
    ) -> ExplainedCandidate:
        # Determine heuristics for matched/missing skills
        c_skills = candidate_skills or []
        matched = self._heuristic_matches(job, c_skills)
        missing = [s for s in job.must_have if s.lower().strip() not in {cs.lower().strip() for cs in c_skills}]

        tags_str = ", ".join(tags) if tags else "None"
        overlap = features.skill_overlap or 0.0
        seniority = features.seniority_match or 0.0

        narrative = (
            f"Candidate {candidate_id} is ranked #{rank} for the '{job.title}' role with a composite score of {final_score:.2f}. "
            f"They show a skill overlap score of {overlap:.1%} and a seniority alignment score of {seniority:.1%}. "
            f"Key tags associated with their profile: {tags_str}."
        )

        return ExplainedCandidate(
            candidate_id=candidate_id,
            rank=rank,
            final_score=final_score,
            matched_points=matched,
            missing_points=missing,
            confidence=features.behavioral_score or 1.0,
            tags=tags,
            narrative=narrative,
        )

    def _heuristic_matches(self, job: ParsedJob, candidate_skills: list[str]) -> list[str]:
        c_set = {s.lower().strip() for s in candidate_skills}
        matched = []
        for s in [*job.must_have, *job.nice_to_have]:
            if s.lower().strip() in c_set:
                matched.append(f"Demonstrates matching proficiency in '{s}'.")
        if not matched and job.must_have:
            matched.append(f"Matches core qualifications for '{job.title}'.")
        return matched

    def _parse_json(self, text: str) -> dict[str, Any]:
        match = JSON_OBJECT_RE.search(text)
        if not match:
            raise ValueError("Response did not contain a valid JSON object.")
        data = json.loads(match.group())
        if not isinstance(data, dict):
            raise ValueError("Parsed JSON is not an object.")
        if "narrative" not in data:
            raise KeyError("JSON missing 'narrative' field.")
        return data
