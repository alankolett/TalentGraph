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
