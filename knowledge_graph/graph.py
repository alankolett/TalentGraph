from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import networkx as nx

from knowledge_graph.ontology import SkillOntologyBuilder
from parsers.models import ParsedJob, ParsedResume


class KnowledgeGraphBuilder:
    def __init__(self, ontology_builder: SkillOntologyBuilder | None = None) -> None:
        self.ontology_builder = ontology_builder or SkillOntologyBuilder()

    def build_skill_graph(self, ontology: dict[str, Any]) -> nx.DiGraph:
        graph = nx.DiGraph()
        for skill, metadata in ontology.get("skills", {}).items():
            graph.add_node(skill, kind="skill", aliases=metadata.get("aliases", []))

        for skill, implied_skills in ontology.get("implications", {}).items():
            source = self.ontology_builder.normalize_skill(skill)
            graph.add_node(source, kind="skill")
            for implied in implied_skills:
                target = self.ontology_builder.normalize_skill(implied)
                graph.add_node(target, kind="skill")
                graph.add_edge(source, target, kind="SKILL_IMPLIES", weight=1.0)
        return graph

    def add_candidate_to_graph(self, graph: nx.DiGraph, parsed_resume: ParsedResume) -> nx.DiGraph:
        candidate_node = self._candidate_node(parsed_resume.candidate_id)
        graph.add_node(candidate_node, kind="candidate", candidate_id=parsed_resume.candidate_id)

        for raw_skill in parsed_resume.raw_skills:
            skill = self.ontology_builder.normalize_skill(raw_skill)
            if not skill:
                continue
            graph.add_node(skill, kind="skill")
            graph.add_edge(candidate_node, skill, kind="HAS_SKILL", weight=1.0)

        previous_role_node: str | None = None
        for index, entry in enumerate(parsed_resume.experience_entries):
            role_node = self._role_node(parsed_resume.candidate_id, index, entry.title)
            company_node = self._company_node(entry.company) if entry.company else None
            graph.add_node(
                role_node,
                kind="role",
                title=entry.title,
                start=entry.start,
                end=entry.end,
                duration_months=entry.duration_months,
            )
            graph.add_edge(candidate_node, role_node, kind="WORKED_AS", weight=1.0)
            if company_node:
                graph.add_node(company_node, kind="company", name=entry.company)
                graph.add_edge(role_node, company_node, kind="AT_COMPANY", weight=1.0)
            if previous_role_node:
                graph.add_edge(previous_role_node, role_node, kind="TRANSITIONED_TO", weight=1.0)
            previous_role_node = role_node

        return graph

    def add_job_to_graph(self, graph: nx.DiGraph, parsed_job: ParsedJob) -> nx.DiGraph:
        job_node = self._job_node(parsed_job.job_id)
        graph.add_node(job_node, kind="job", title=parsed_job.title, seniority=parsed_job.seniority)
        for raw_skill in parsed_job.must_have:
            skill = self.ontology_builder.normalize_skill(raw_skill)
            graph.add_node(skill, kind="skill")
            graph.add_edge(job_node, skill, kind="REQUIRES_SKILL", weight=1.0)
        for raw_skill in parsed_job.nice_to_have:
            skill = self.ontology_builder.normalize_skill(raw_skill)
            graph.add_node(skill, kind="skill")
            graph.add_edge(job_node, skill, kind="PREFERS_SKILL", weight=0.5)
        return graph

    def skill_distance(self, graph: nx.DiGraph, source_skill: str, target_skill: str) -> int | None:
        source = self.ontology_builder.normalize_skill(source_skill)
        target = self.ontology_builder.normalize_skill(target_skill)
        if source == target:
            return 0
        if source not in graph or target not in graph:
            return None
        if not hasattr(graph, "_undirected"):
            graph._undirected = graph.to_undirected()
        try:
            lengths = nx.single_source_shortest_path_length(graph._undirected, source, cutoff=3)
            return lengths.get(target)
        except nx.NodeNotFound:
            return None

    def save_graph(self, graph: nx.DiGraph, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            pickle.dump(graph, handle)
        return path

    def load_graph(self, path: str | Path) -> nx.DiGraph:
        with Path(path).open("rb") as handle:
            graph = pickle.load(handle)
        if not isinstance(graph, nx.DiGraph):
            raise TypeError("Loaded object is not a NetworkX DiGraph.")
        return graph

    def _candidate_node(self, candidate_id: str) -> str:
        return f"candidate:{candidate_id}"

    def _job_node(self, job_id: str) -> str:
        return f"job:{job_id}"

    def _role_node(self, candidate_id: str, index: int, title: str) -> str:
        slug = self.ontology_builder._canonical_text(title).replace(" ", "_")
        return f"role:{candidate_id}:{index}:{slug}"

    def _company_node(self, company: str | None) -> str:
        slug = self.ontology_builder._canonical_text(company or "").replace(" ", "_")
        return f"company:{slug}"
