from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import process

from preprocessing.cleaning import clean_text

DEFAULT_SKILL_SYNONYMS = {
    "python": {"python", "py", "python3"},
    "fastapi": {"fastapi", "fast api"},
    "sql": {"sql", "postgres", "postgresql", "sqlite"},
    "qdrant": {"qdrant", "vector db", "vector database"},
    "machine learning": {"machine learning", "ml"},
    "data engineering": {"data engineering", "etl", "data pipelines"},
    "react": {"react", "reactjs", "react.js"},
}

DEFAULT_IMPLICATIONS = {
    "fastapi": {"python"},
    "postgresql": {"sql"},
    "sqlite": {"sql"},
    "qdrant": {"vector database"},
    "machine learning": {"python"},
    "data engineering": {"sql", "python"},
}


@dataclass
class SkillOntologyBuilder:
    synonyms: dict[str, set[str]] = field(
        default_factory=lambda: {key: set(value) for key, value in DEFAULT_SKILL_SYNONYMS.items()}
    )
    implications: dict[str, set[str]] = field(
        default_factory=lambda: {key: set(value) for key, value in DEFAULT_IMPLICATIONS.items()}
    )
    fuzzy_threshold: int = 88

    def normalize_skill(self, raw: str) -> str:
        normalized = self._canonical_text(raw)
        if not normalized:
            return ""

        for canonical, aliases in self.synonyms.items():
            if normalized == canonical or normalized in aliases:
                return canonical

        choices = sorted({alias for aliases in self.synonyms.values() for alias in aliases})
        match = process.extractOne(normalized, choices, score_cutoff=self.fuzzy_threshold)
        if match:
            alias = match[0]
            for canonical, aliases in self.synonyms.items():
                if alias in aliases:
                    return canonical

        return normalized

    def build_ontology(self, raw_skills: list[str]) -> dict[str, dict[str, list[str]]]:
        for raw_skill in raw_skills:
            canonical = self.normalize_skill(raw_skill)
            if canonical:
                self.synonyms.setdefault(canonical, {canonical}).add(
                    self._canonical_text(raw_skill)
                )

        return {
            "skills": {
                skill: {"aliases": sorted(aliases)}
                for skill, aliases in sorted(self.synonyms.items())
            },
            "implications": {
                skill: sorted(targets) for skill, targets in sorted(self.implications.items())
            },
        }

    def save(self, path: str | Path, ontology: dict[str, dict[str, list[str]]]) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ontology, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def _canonical_text(self, value: str) -> str:
        return clean_text(value).lower().replace("_", " ").replace("-", " ")
