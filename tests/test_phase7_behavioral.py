import pytest

from feature_engineering.behavioral import BehavioralSignalExtractor, SignalNormalizer


def test_compute_recency_score_decay() -> None:
    extractor = BehavioralSignalExtractor(current_date_str="2026-06-17", half_life_days=90.0)

    # Date is exactly current date: score should be 1.0
    assert extractor.compute_recency_score("2026-06-17") == pytest.approx(1.0)

    # Date is 90 days ago: score should be 0.5
    assert extractor.compute_recency_score("2026-03-19") == pytest.approx(0.5, abs=0.01)

    # Invalid or missing date should return neutral 0.5
    assert extractor.compute_recency_score(None) == 0.5
    assert extractor.compute_recency_score("invalid-date") == 0.5


def test_compute_contribution_frequency() -> None:
    extractor = BehavioralSignalExtractor()

    timeline_with_counts = [
        {"date": "2026-05-01", "count": 10},
        {"date": "2026-06-10", "count": 15},
    ]
    assert extractor.compute_contribution_frequency(timeline_with_counts) == 25.0

    # Timeline with missing counts fallback
    timeline_no_counts = [{"date": "2026-05-01"}, {"date": "2026-06-10"}]
    assert extractor.compute_contribution_frequency(timeline_no_counts) == 2.0

    # Empty timeline
    assert extractor.compute_contribution_frequency([]) == 0.0


def test_compute_learning_velocity() -> None:
    extractor = BehavioralSignalExtractor()

    # 2 skills added over 2 years (2020 to 2022) -> velocity = 1.0 skill/year
    skills_over_time = [
        {"date": "2020-01-01", "skills": ["python"]},
        {"date": "2021-01-01", "skills": ["python", "fastapi"]},
        {"date": "2022-01-01", "skills": ["python", "fastapi", "qdrant"]},
    ]
    assert extractor.compute_learning_velocity(skills_over_time) == pytest.approx(1.0, abs=0.05)

    assert extractor.compute_learning_velocity(
        [{"date": "2020-01-01", "skills": ["python"]}]
    ) == 0.0
    assert extractor.compute_learning_velocity([]) == 0.0


def test_compute_open_source_breadth() -> None:
    extractor = BehavioralSignalExtractor()

    # Has Github and 2 distinct repositories in timeline
    timeline = [{"repo": "repo-a"}, {"repo": "repo-b"}, {"repo": "repo-a"}]
    breadth = extractor.compute_open_source_breadth("https://github.com/c1", timeline)
    # base 0.4 + 0.1 * 2 repos = 0.6
    assert breadth == pytest.approx(0.6)

    # Empty values
    assert extractor.compute_open_source_breadth(None, []) == 0.0


def test_raw_profile_confidence_degradation() -> None:
    extractor = BehavioralSignalExtractor()

    # Full metadata -> confidence = 1.0
    full_metadata = {
        "last_activity_date": "2026-06-10",
        "timeline": [{"date": "2026-06-10", "count": 5}],
        "skills_over_time": [
            {"date": "2020-01-01", "skills": ["python"]},
            {"date": "2022-01-01", "skills": ["python", "ml"]},
        ],
    }
    profile = extractor.extract_raw_profile("c1", full_metadata, "https://github.com/c1")
    assert profile["signal_confidence"] == 1.0

    # Missing metadata -> confidence degrades
    profile_missing = extractor.extract_raw_profile("c2", {}, None)
    assert profile_missing["signal_confidence"] == 0.3


def test_signal_normalization_population() -> None:
    raw_profiles = [
        {
            "candidate_id": "c1",
            "contribution_frequency": 20.0,
            "recency_score": 1.0,
            "learning_velocity": 2.0,
            "open_source_breadth": 0.8,
            "signal_confidence": 1.0,
        },
        {
            "candidate_id": "c2",
            "contribution_frequency": 0.0,
            "recency_score": 0.0,
            "learning_velocity": 0.0,
            "open_source_breadth": 0.0,
            "signal_confidence": 0.5,
        },
    ]

    normalizer = SignalNormalizer()
    profiles = normalizer.normalize_population(raw_profiles)

    assert len(profiles) == 2
    # c1 is max in all, c2 is min in all
    # min-max normalization puts max at 1.0 and min at 0.0
    c1_prof = next(p for p in profiles if p.candidate_id == "c1")
    c2_prof = next(p for p in profiles if p.candidate_id == "c2")

    assert c1_prof.contribution_frequency == 1.0
    assert c1_prof.recency_score == 1.0
    assert c1_prof.learning_velocity == 1.0
    assert c1_prof.open_source_breadth == 1.0
    assert c1_prof.signal_confidence == 1.0

    assert c2_prof.contribution_frequency == 0.0
    assert c2_prof.recency_score == 0.0
    assert c2_prof.learning_velocity == 0.0
    assert c2_prof.open_source_breadth == 0.0
    assert c2_prof.signal_confidence == 0.5


def test_honeypot_detector() -> None:
    from feature_engineering.behavioral import HoneypotDetector

    detector = HoneypotDetector()

    # 1. Test clean profile
    clean_skills = [
        {"name": "Python", "proficiency": "expert", "duration_months": 36},
        {"name": "ML", "proficiency": "intermediate", "duration_months": 12},
    ]
    clean_career = [
        {"company": "Acme", "duration_months": 24},
        {"company": "Beta", "duration_months": 24},
    ]
    assert len(detector.detect_honeypots(clean_skills, clean_career, 4.0)) == 0

    # 2. Test expert skill with 0 duration
    dirty_skills = [
        {"name": "Python", "proficiency": "expert", "duration_months": 0},
    ]
    flags = detector.detect_honeypots(dirty_skills, clean_career, 4.0)
    assert len(flags) > 0
    assert any("expert_skill_zero_duration" in f for f in flags)

    # 3. Test inconsistent YoE
    flags = detector.detect_honeypots(clean_skills, clean_career, 10.0)
    assert len(flags) > 0
    assert any("inconsistent_experience_years" in f for f in flags)

    # 4. Test empty career history with declared YoE
    flags = detector.detect_honeypots(clean_skills, [], 4.0)
    assert len(flags) > 0
    assert any("inconsistent_experience_years" in f for f in flags)


def test_availability_engagement_trust_scores() -> None:
    extractor = BehavioralSignalExtractor(current_date_str="2026-06-17")

    metadata = {
        "last_active_date": "2026-06-17",
        "open_to_work_flag": True,
        "notice_period_days": 15,
        "recruiter_response_rate": 0.9,
        "avg_response_time_hours": 2.0,
        "interview_completion_rate": 0.8,
        "verified_email": True,
        "verified_phone": True,
        "linkedin_connected": True,
        "endorsements_received": 10,
    }

    skills = [{"name": "Python"}]
    career = [{"company": "A", "duration_months": 12}]

    profile = extractor.extract_raw_profile(
        candidate_id="c1",
        metadata=metadata,
        github_url="https://github.com/c1",
        skills=skills,
        career_history=career,
        experience_years=1.0,
    )

    # Check that availability, engagement, trust, honeypot scores are correctly computed
    expected_availability = 0.4 * 1.0 + 0.4 * 1.0 + 0.2 * 1.0
    assert profile["availability_score"] == pytest.approx(expected_availability)

    expected_engagement = (
        0.4 * 0.9 + 0.3 * (1.0 / (1.0 + 2.0 / 24.0)) + 0.3 * 0.8
    )
    assert profile["engagement_score"] == pytest.approx(expected_engagement)

    expected_trust = (
        0.2 * 1.0 + 0.2 * 1.0 + 0.2 * 1.0 + 0.4 * min(1.0, 10.0 / 1.0 / 5.0)
    )
    assert profile["trust_score"] == pytest.approx(expected_trust)
    assert profile["honeypot_score"] == 0.0
    assert len(profile["honeypot_flags"]) == 0

