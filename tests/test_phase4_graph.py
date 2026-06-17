import json

from knowledge_graph.graph import KnowledgeGraphBuilder
from knowledge_graph.ontology import SkillOntologyBuilder
from knowledge_graph.pipeline import Phase4Pipeline
from knowledge_graph.trajectory import CareerTrajectoryAnalyzer
from parsers.models import ExperienceEntry, ParsedJob, ParsedResume


def test_normalize_skill_handles_synonyms_and_typos() -> None:
    builder = SkillOntologyBuilder()

    assert builder.normalize_skill("Python3") == "python"
    assert builder.normalize_skill("fast api") == "fastapi"
    assert builder.normalize_skill("Postgres") == "sql"
    assert builder.normalize_skill("pythn") == "python"


def test_skill_graph_distance_and_unseen_skill() -> None:
    ontology_builder = SkillOntologyBuilder()
    ontology = ontology_builder.build_ontology(["Python", "FastAPI", "Qdrant", "Rust"])
    graph_builder = KnowledgeGraphBuilder(ontology_builder)
    graph = graph_builder.build_skill_graph(ontology)

    assert graph_builder.skill_distance(graph, "Python", "python") == 0
    assert graph_builder.skill_distance(graph, "Fast API", "Python") == 1
    assert graph_builder.skill_distance(graph, "Rust", "Python") is None


def test_add_candidate_to_graph_and_trajectory_vector() -> None:
    ontology_builder = SkillOntologyBuilder()
    graph_builder = KnowledgeGraphBuilder(ontology_builder)
    graph = graph_builder.build_skill_graph(ontology_builder.build_ontology(["Python"]))
    resume = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python"],
        sections={},
        experience_entries=[
            ExperienceEntry(
                title="Engineer",
                company="Acme",
                start="2020",
                end="2021",
                duration_months=12,
                description="Engineer at Acme",
            )
        ],
    )

    graph_builder.add_candidate_to_graph(graph, resume)
    vector = CareerTrajectoryAnalyzer().compute_trajectory_vector(graph, "c1")

    assert "candidate:c1" in graph
    assert graph.has_edge("candidate:c1", "python")
    assert vector["role_count"] == 1.0
    assert vector["skill_count"] == 1.0
    assert vector["company_count"] == 1.0


def test_phase4_pipeline_writes_ontology_and_graph(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    graph_dir = tmp_path / "knowledge_graph"
    processed_dir.mkdir()

    resume = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI"],
        sections={},
        experience_entries=[
            ExperienceEntry(title="Engineer", company="Acme", description="Engineer at Acme")
        ],
    )
    job = ParsedJob(
        job_id="j1",
        title="Backend Engineer",
        must_have=["Python"],
        nice_to_have=["Qdrant"],
        responsibilities=["Build APIs"],
        raw_text="Build APIs",
    )
    (processed_dir / "parsed_resumes.jsonl").write_text(
        json.dumps(resume.model_dump(mode="json")) + "\n",
        encoding="utf-8",
    )
    (processed_dir / "parsed_jobs.jsonl").write_text(
        json.dumps(job.model_dump(mode="json")) + "\n",
        encoding="utf-8",
    )

    result = Phase4Pipeline().run(processed_dir, graph_dir)

    assert result.ontology_path.exists()
    assert result.graph_path.exists()
    assert result.node_count >= 5
    assert result.edge_count >= 4
