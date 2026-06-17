import json
from dataclasses import dataclass
from pathlib import Path

from knowledge_graph.graph import KnowledgeGraphBuilder
from knowledge_graph.ontology import SkillOntologyBuilder
from parsers.models import ParsedJob, ParsedResume


@dataclass
class Phase4Result:
    ontology_path: Path
    graph_path: Path
    node_count: int
    edge_count: int


class Phase4Pipeline:
    def __init__(
        self,
        ontology_builder: SkillOntologyBuilder | None = None,
        graph_builder: KnowledgeGraphBuilder | None = None,
    ) -> None:
        self.ontology_builder = ontology_builder or SkillOntologyBuilder()
        self.graph_builder = graph_builder or KnowledgeGraphBuilder(self.ontology_builder)

    def run(self, processed_dir: str | Path, graph_dir: str | Path) -> Phase4Result:
        processed_dir = Path(processed_dir)
        graph_dir = Path(graph_dir)
        graph_dir.mkdir(parents=True, exist_ok=True)

        resumes = self._read_jsonl(processed_dir / "parsed_resumes.jsonl", ParsedResume)
        jobs = self._read_jsonl(processed_dir / "parsed_jobs.jsonl", ParsedJob)
        raw_skills = [skill for resume in resumes for skill in resume.raw_skills] + [
            skill for job in jobs for skill in [*job.must_have, *job.nice_to_have]
        ]

        ontology = self.ontology_builder.build_ontology(raw_skills)
        graph = self.graph_builder.build_skill_graph(ontology)
        for resume in resumes:
            self.graph_builder.add_candidate_to_graph(graph, resume)
        for job in jobs:
            self.graph_builder.add_job_to_graph(graph, job)

        ontology_path = self.ontology_builder.save(graph_dir / "skill_ontology.json", ontology)
        graph_path = self.graph_builder.save_graph(graph, graph_dir / "candidate_kg.gpickle")
        return Phase4Result(
            ontology_path=ontology_path,
            graph_path=graph_path,
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
        )

    def _read_jsonl(self, path: Path, model: type[ParsedResume] | type[ParsedJob]):
        rows = []
        if not path.exists():
            return rows
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(model.model_validate(json.loads(line)))
        return rows
