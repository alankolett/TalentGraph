from parsers.experience import ExperienceExtractor
from parsers.models import ParsedResume
from parsers.sections import ResumeSectionSplitter
from preprocessing.cleaning import split_skills
from preprocessing.models import CandidateRecord


class ResumeParser:
    def __init__(
        self,
        splitter: ResumeSectionSplitter | None = None,
        experience_extractor: ExperienceExtractor | None = None,
    ) -> None:
        self.splitter = splitter or ResumeSectionSplitter()
        self.experience_extractor = experience_extractor or ExperienceExtractor()

    def parse(self, candidate: CandidateRecord) -> ParsedResume:
        sections = self.splitter.split_sections(candidate.raw_resume_text)
        experience_text = sections.get("experience") or candidate.raw_resume_text
        entries = self.experience_extractor.extract_experience_entries(experience_text)
        return ParsedResume(
            candidate_id=candidate.id,
            sections=sections,
            raw_skills=candidate.skills_raw or split_skills(sections.get("skills")),
            experience_entries=entries,
        )
