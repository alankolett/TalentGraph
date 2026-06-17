from parsers.models import ParsedJob, ParsedResume
from preprocessing.cleaning import clean_text


def build_candidate_text(parsed_resume: ParsedResume) -> str:
    skills = ", ".join(parsed_resume.raw_skills)
    summary = parsed_resume.sections.get("summary", "")
    recent_roles = []
    for entry in parsed_resume.experience_entries[:3]:
        parts = [entry.title]
        if entry.company:
            parts.append(f"at {entry.company}")
        if entry.description:
            parts.append(entry.description)
        recent_roles.append(" ".join(parts))

    components = [
        f"Skills: {skills}" if skills else "",
        f"Recent roles: {' | '.join(recent_roles)}" if recent_roles else "",
        f"Summary: {summary}" if summary else "",
    ]
    text = clean_text(" ".join(component for component in components if component))
    return text or clean_text(skills) or "Candidate profile"


def build_job_text(parsed_job: ParsedJob) -> str:
    components = [
        f"Title: {parsed_job.title}",
        f"Seniority: {parsed_job.seniority}" if parsed_job.seniority else "",
        f"Must have: {', '.join(parsed_job.must_have)}" if parsed_job.must_have else "",
        f"Nice to have: {', '.join(parsed_job.nice_to_have)}" if parsed_job.nice_to_have else "",
        (
            f"Responsibilities: {' | '.join(parsed_job.responsibilities)}"
            if parsed_job.responsibilities
            else ""
        ),
        f"Description: {parsed_job.raw_text}",
    ]
    return clean_text(" ".join(component for component in components if component))
