from __future__ import annotations

import re

from preprocessing.cleaning import clean_text


HEADING_ALIASES = {
    "summary": {"summary", "profile", "objective", "about"},
    "skills": {"skills", "technical skills", "technologies", "tooling"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
    },
    "education": {"education", "academic background"},
    "projects": {"projects", "selected projects"},
    "certifications": {"certifications", "certificates"},
}

HEADING_LOOKUP = {
    alias: canonical for canonical, aliases in HEADING_ALIASES.items() for alias in aliases
}
HEADING_RE = re.compile(r"^\s*([A-Za-z][A-Za-z /&-]{1,40})\s*:?\s*$")


class ResumeSectionSplitter:
    """Split cleaned resume text into coarse sections using heading heuristics."""

    def split_sections(self, text: str) -> dict[str, str]:
        lines = [line.rstrip() for line in str(text).splitlines()]
        sections: dict[str, list[str]] = {}
        current = "summary"
        found_heading = False

        for line in lines:
            heading = self._canonical_heading(line)
            if heading:
                current = heading
                sections.setdefault(current, [])
                found_heading = True
                continue
            if clean_text(line):
                sections.setdefault(current, []).append(line)

        if not found_heading:
            compact = clean_text(text)
            if self._looks_skills_only(compact):
                return {"skills": compact}
            return {"summary": compact}

        return {
            section: "\n".join(clean_text(line) for line in content if clean_text(line))
            for section, content in sections.items()
            if clean_text("\n".join(content))
        }

    def _canonical_heading(self, line: str) -> str | None:
        match = HEADING_RE.match(line)
        if not match:
            return None
        normalized = clean_text(match.group(1)).lower()
        return HEADING_LOOKUP.get(normalized)

    def _looks_skills_only(self, text: str) -> bool:
        if not text:
            return False
        separators = text.count(",") + text.count("|") + text.count(";")
        words = text.split()
        return separators >= 3 and len(words) <= 40
