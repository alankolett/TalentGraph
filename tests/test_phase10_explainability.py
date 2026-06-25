
from explainability.classifier import TagClassifier
from explainability.generator import ExplanationGenerator
from explainability.models import ExplainedCandidate
from parsers.models import ParsedJob
from ranking_engine.models import FeatureVector


class MockLLMProvider:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    def generate(self, prompt: str) -> str:
        return self.response_text


def test_tag_classifier_hidden_gem() -> None:
    classifier = TagClassifier()
    # High behavioral (0.8) + Low bm25 (0.1) + Low dense (0.1) => Hidden Gem
    f = FeatureVector(behavioral_score=0.8, bm25_score=0.1, dense_similarity=0.1)
    tags = classifier.classify_tags(f)
    assert "Hidden Gem" in tags
    assert "Career Switcher" not in tags


def test_tag_classifier_fast_learner() -> None:
    classifier = TagClassifier()
    # High behavioral (0.65) + trajectory (0.7) + high skill overlap to avoid Career Switcher
    f = FeatureVector(
        behavioral_score=0.65,
        trajectory_alignment=0.7,
        skill_overlap=0.5,
        bm25_score=0.5,  # above 0.3 so Hidden Gem does NOT fire
        dense_similarity=0.5,
    )
    tags = classifier.classify_tags(f)
    assert "Fast Learner" in tags
    assert "Hidden Gem" not in tags
    assert "Career Switcher" not in tags


def test_tag_classifier_career_switcher() -> None:
    classifier = TagClassifier()
    # High trajectory alignment (0.8) + Very low skill overlap (0.05 < 0.1)
    # behavioral=0.0 so High Engagement & Hidden Gem do NOT fire
    f = FeatureVector(trajectory_alignment=0.8, skill_overlap=0.05, behavioral_score=0.0)
    tags = classifier.classify_tags(f)
    assert "Career Switcher" in tags
    assert "High Engagement" not in tags
    assert "Hidden Gem" not in tags


def test_explanation_generator_fallback() -> None:
    generator = ExplanationGenerator(llm_provider=None)
    job = ParsedJob(
        job_id="j1",
        title="Python Engineer",
        must_have=["Python", "FastAPI"],
        raw_text="Requires Python",
    )
    features = FeatureVector(skill_overlap=0.5, seniority_match=1.0)
    tags = ["Fast Learner"]

    explained = generator.generate_explanation(
        candidate_id="c1",
        rank=1,
        final_score=0.85,
        job=job,
        features=features,
        tags=tags,
        candidate_skills=["Python"],
    )

    assert isinstance(explained, ExplainedCandidate)
    assert explained.candidate_id == "c1"
    assert explained.rank == 1
    assert explained.final_score == 0.85
    assert "Python" in [s.split("'")[1] for s in explained.matched_points if "'" in s]
    assert "FastAPI" in explained.missing_points
    assert "Fast Learner" in explained.tags
    assert "ranked #1" in explained.narrative
    assert "Python Engineer" in explained.narrative


def test_explanation_generator_llm_success() -> None:
    response_json = """
    {
      "matched_points": ["Matches requirement for 'Python'.", "Matches requirement for 'FastAPI'."],
      "missing_points": ["Lacks Docker experience."],
      "narrative": "Candidate shows excellent programming skills."
    }
    """
    mock_llm = MockLLMProvider(response_json)
    generator = ExplanationGenerator(mock_llm)

    job = ParsedJob(
        job_id="j1",
        title="Python Engineer",
        must_have=["Python", "FastAPI"],
        raw_text="Requires Python",
    )
    features = FeatureVector(behavioral_score=0.9)

    explained = generator.generate_explanation(
        candidate_id="c1",
        rank=2,
        final_score=0.78,
        job=job,
        features=features,
        tags=["Hidden Gem"],
    )

    assert explained.candidate_id == "c1"
    assert explained.rank == 2
    assert explained.final_score == 0.78
    assert len(explained.matched_points) == 2
    assert "Docker" in explained.missing_points[0]
    assert explained.narrative == "Candidate shows excellent programming skills."
    assert explained.confidence == 0.9


def test_explanation_generator_llm_hallucination_filter() -> None:
    # LLM hallucinates matching 'Rust' when the job does not require it
    response_json = """
    {
      "matched_points": ["Matches requirement for 'Python'.", "Matches requirement for 'Rust'."],
      "missing_points": [],
      "narrative": "Decent candidate."
    }
    """
    mock_llm = MockLLMProvider(response_json)
    generator = ExplanationGenerator(mock_llm)

    job = ParsedJob(
        job_id="j1",
        title="Python Engineer",
        must_have=["Python"],
        raw_text="Requires Python",
    )
    features = FeatureVector(behavioral_score=0.8)

    explained = generator.generate_explanation(
        candidate_id="c1",
        rank=1,
        final_score=0.90,
        job=job,
        features=features,
        tags=[],
    )

    # 'Rust' match should be filtered out because the job only asks for 'Python'
    assert len(explained.matched_points) == 1
    assert "Python" in explained.matched_points[0]
    assert "Rust" not in "".join(explained.matched_points)
