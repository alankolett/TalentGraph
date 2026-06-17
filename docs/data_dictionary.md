# Data Dictionary

Phase 2 defines the canonical cleaned records consumed by parsing, embedding,
retrieval, and ranking phases.

## CandidateRecord

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Stable candidate identifier. |
| `raw_resume_text` | string | yes | Cleaned resume text with HTML decoded and whitespace collapsed. |
| `skills_raw` | list[string] | no | Raw skill mentions split from comma- or pipe-delimited source values. |
| `experience_years` | float | no | Non-negative years of experience when available. |
| `education` | string | no | Raw cleaned education summary. |
| `location` | string | no | Raw cleaned candidate location. |
| `github_url` | URL | no | GitHub profile URL when available. |
| `activity_metadata` | object | no | Source-specific activity fields retained for later feature engineering. |

## JobRecord

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Stable job identifier. |
| `title` | string | yes | Cleaned job title. |
| `raw_description` | string | yes | Cleaned job description; descriptions shorter than 20 characters are quarantined. |
| `must_have_skills` | list[string] | no | Required skill mentions. |
| `nice_to_have_skills` | list[string] | no | Preferred skill mentions. |
| `seniority` | string | no | Raw seniority/level label. |
| `location` | string | no | Raw job location. |

## Outputs

- `data/processed/candidates.parquet`: valid `CandidateRecord` rows.
- `data/processed/jobs.parquet`: valid `JobRecord` rows.
- `data/processed/rejected.parquet`: rows quarantined with `source`, `row_index`,
  `record_type`, `record_id`, `reason`, and original `payload`.

## Cleaning Rules

- Decode HTML entities and strip HTML tags.
- Normalize Unicode with NFKC.
- Collapse repeated whitespace.
- Split skills on comma or pipe delimiters.
- Quarantine duplicate IDs and near-duplicate text.
- Quarantine rows that fail pydantic schema validation.

## ParsedResume

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `candidate_id` | string | yes | References `CandidateRecord.id`. |
| `sections` | object[string,string] | no | Coarse resume sections such as `summary`, `skills`, `experience`, `education`. |
| `raw_skills` | list[string] | no | Skills from Phase 2 or the detected skills section. |
| `experience_entries` | list[ExperienceEntry] | no | Rule-extracted work history entries. |

## ExperienceEntry

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `title` | string | yes | Role title inferred from a heading, bullet, or date-range line. |
| `company` | string | no | Company when detected from `title at company` or `title @ company`. |
| `start` | string | no | Raw start date token. |
| `end` | string | no | Raw end date token, including `Present` or `Current`. |
| `duration_months` | integer | no | Parsed month span when dates are interpretable. |
| `description` | string | no | Source text for the extracted entry. |

## ParsedJob

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `job_id` | string | yes | References `JobRecord.id`. |
| `title` | string | yes | Cleaned job title. |
| `seniority` | string | no | Explicit or inferred seniority label. |
| `must_have` | list[string] | no | Required skills from Phase 2, LLM extraction, or heuristics. |
| `nice_to_have` | list[string] | no | Preferred skills from Phase 2, LLM extraction, or heuristics. |
| `responsibilities` | list[string] | no | Action-oriented responsibilities extracted from the job description. |
| `raw_text` | string | yes | Cleaned source job description. |
