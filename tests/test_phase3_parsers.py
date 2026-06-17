import json

from common.llm import LLMProvider
from preprocessing.models import CandidateRecord

from parsers.experience import ExperienceExtractor
from parsers.jobs import JDStructuredExtractor
from parsers.models import ParsedJob
from parsers.resumes import ResumeParser
from parsers.sections import ResumeSectionSplitter


class MalformedThenValidLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "{not valid json"
        return json.dumps(
            {
                "job_id": "j1",
                "title": "Senior Backend Engineer",
                "seniority": "senior",
                "must_have": ["Python", "FastAPI"],
                "nice_to_have": ["Qdrant"],
                "responsibilities": ["Build APIs", "Improve ranking workflows"],
                "raw_text": "Build APIs and improve ranking workflows.",
            }
        )


def test_split_sections_handles_missing_headers_and_skills_only() -> None:
    splitter = ResumeSectionSplitter()

    assert splitter.split_sections("Python, SQL, FastAPI, Qdrant") == {
        "skills": "Python, SQL, FastAPI, Qdrant"
    }
    assert splitter.split_sections("Built data platforms for recruiting teams.") == {
        "summary": "Built data platforms for recruiting teams."
    }


def test_resume_parser_extracts_sections_skills_and_experience() -> None:
    candidate = CandidateRecord(
        id="c1",
        raw_resume_text=(
            "Skills\nPython, FastAPI, Qdrant\n"
            "Experience\n"
            "Senior Engineer at Acme, Jan 2020 - Mar 2022\n"
            "- Built ranking APIs.\n"
            "Engineer at Beta, 2018 - 2019\n"
            "- Shipped data pipelines."
        ),
        skills_raw=[],
    )

    parsed = ResumeParser().parse(candidate)

    assert parsed.candidate_id == "c1"
    assert parsed.raw_skills == ["Python", "FastAPI", "Qdrant"]
    assert len(parsed.experience_entries) == 2
    assert parsed.experience_entries[0].title == "Senior Engineer"
    assert parsed.experience_entries[0].company == "Acme"


def test_experience_extractor_handles_bullet_only_resume() -> None:
    entries = ExperienceExtractor().extract_experience_entries(
        "- Backend Engineer at Acme 2020 - Present built APIs\n"
        "- Data Engineer at Beta 2018 - 2020 built pipelines"
    )

    assert len(entries) == 2
    assert entries[0].title == "Backend Engineer"


def test_jd_extractor_repairs_malformed_llm_json() -> None:
    llm: LLMProvider = MalformedThenValidLLM()
    extractor = JDStructuredExtractor(llm_provider=llm)

    parsed = extractor.llm_extract_job_requirements(
        job_id="j1",
        title="Senior Backend Engineer",
        jd_text="Build APIs and improve ranking workflows.",
        must_have_skills=["Python"],
    )

    assert isinstance(parsed, ParsedJob)
    assert parsed.seniority == "senior"
    assert parsed.must_have == ["Python", "FastAPI"]

