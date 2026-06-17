from __future__ import annotations

import re
from datetime import date

from parsers.models import ExperienceEntry
from preprocessing.cleaning import clean_text

try:
    import dateparser
except ImportError:  # pragma: no cover - exercised only in minimal environments
    dateparser = None


DATE_TOKEN = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*\d{4}|Present|Current"
DATE_RANGE_RE = re.compile(
    rf"(?P<start>{DATE_TOKEN})\s*(?:-|to|–|—)\s*(?P<end>{DATE_TOKEN})",
    re.IGNORECASE,
)
ROLE_RE = re.compile(
    rf"^(?P<title>[^@\n|,]+?)\s*(?:@| at |\|)\s*(?P<company>.+?)"
    rf"(?:[,| ]+(?P<range>{DATE_TOKEN}\s*(?:-|to|–|—)\s*{DATE_TOKEN}).*)?$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[-*•]\s*")


class ExperienceExtractor:
    """Extract coarse experience entries with date-range and role heuristics."""

    def extract_experience_entries(self, section_text: str) -> list[ExperienceEntry]:
        blocks = self._candidate_blocks(section_text)
        entries = [entry for block in blocks if (entry := self._parse_block(block))]
        return entries

    def _candidate_blocks(self, text: str) -> list[str]:
        lines = [line.strip() for line in str(text).splitlines() if clean_text(line)]
        if not lines:
            return []

        blocks: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            starts_new_role = bool(ROLE_RE.search(line) or DATE_RANGE_RE.search(line))
            if current and starts_new_role:
                blocks.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append(current)

        if len(blocks) == 1 and not self._parse_block("\n".join(blocks[0])):
            return [line for line in lines if BULLET_RE.search(line) or DATE_RANGE_RE.search(line)]

        return ["\n".join(block) for block in blocks]

    def _parse_block(self, block: str) -> ExperienceEntry | None:
        cleaned = clean_text(block)
        if not cleaned:
            return None

        role_match = ROLE_RE.search(cleaned)
        date_match = DATE_RANGE_RE.search(cleaned)

        title = None
        company = None
        if role_match:
            title = BULLET_RE.sub("", clean_text(role_match.group("title"))).strip()
            company = self._clean_company(role_match.group("company"))
        elif date_match:
            title = clean_text(cleaned[: date_match.start()]).strip("-|, ")

        if not title:
            title = self._infer_title(cleaned)
        if not title:
            return None

        start = date_match.group("start") if date_match else None
        end = date_match.group("end") if date_match else None
        return ExperienceEntry(
            title=title,
            company=company or None,
            start=start,
            end=end,
            duration_months=self._duration_months(start, end),
            description=cleaned,
        )

    def _infer_title(self, text: str) -> str | None:
        compact = BULLET_RE.sub("", text).strip()
        if not compact:
            return None
        return compact.split(".")[0][:80].strip()

    def _clean_company(self, value: str) -> str:
        without_date = DATE_RANGE_RE.sub("", value)
        return clean_text(without_date).strip(",-| ")

    def _duration_months(self, start: str | None, end: str | None) -> int | None:
        start_date = self._parse_date(start)
        end_date = (
            date.today() if end and end.lower() in {"present", "current"} else self._parse_date(end)
        )
        if not start_date or not end_date or end_date < start_date:
            return None
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month

    def _parse_date(self, value: str | None) -> date | None:
        if not value or value.lower() in {"present", "current"}:
            return None
        if dateparser:
            parsed = dateparser.parse(value, settings={"PREFER_DAY_OF_MONTH": "first"})
            return parsed.date() if parsed else None
        year_match = re.search(r"\d{4}", value)
        return date(int(year_match.group()), 1, 1) if year_match else None
