import pandas as pd

from preprocessing.cleaning import DataCleaner, clean_text


def test_clean_text_normalizes_html_whitespace_and_encoding() -> None:
    assert clean_text(" Senior&nbsp;<b>Python</b>\n\nEngineer ") == "Senior Python Engineer"


def test_candidate_cleaning_and_deduplication() -> None:
    cleaner = DataCleaner()
    raw = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "resume": "Python engineer with ML systems experience.",
                "skills": "Python, ML",
            },
            {
                "candidate_id": "c1",
                "resume": "Python engineer with ML systems experience.",
                "skills": "Python, ML",
            },
        ]
    )

    cleaned = cleaner.clean_candidates(raw)
    accepted, rejected = cleaner.deduplicate_candidates(cleaned)

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected.iloc[0]["reason"] == "duplicate_id"
    assert accepted.iloc[0]["skills_raw"] == ["Python", "ML"]
