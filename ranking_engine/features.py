from typing import Any
import networkx as nx

from feature_engineering.behavioral import BehavioralProfile
from knowledge_graph.graph import KnowledgeGraphBuilder
from knowledge_graph.ontology import SkillOntologyBuilder
from knowledge_graph.trajectory import CareerTrajectoryAnalyzer
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.models import FeatureVector
from ranking_engine.rubric import JDRubricScorer


class FeatureBuilder:
    """Computes normalized feature vectors for job-candidate pairs."""

    def __init__(
        self,
        ontology_builder: SkillOntologyBuilder | None = None,
        graph_builder: KnowledgeGraphBuilder | None = None,
        trajectory_analyzer: CareerTrajectoryAnalyzer | None = None,
    ) -> None:
        self.ontology_builder = ontology_builder or SkillOntologyBuilder()
        self.graph_builder = graph_builder or KnowledgeGraphBuilder(self.ontology_builder)
        self.trajectory_analyzer = trajectory_analyzer or CareerTrajectoryAnalyzer()

    def build_feature_vector(
        self,
        parsed_resume: ParsedResume,
        job: ParsedJob,
        kg: nx.DiGraph,
        behavioral_profile: BehavioralProfile | None,
        retrieval_scores: dict[str, float],
        experience_years: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureVector:
        """Construct the FeatureVector with values normalized to [0.0, 1.0]."""
        # Normalize candidate skills using the ontology
        c_skills = {self.ontology_builder.normalize_skill(s) for s in parsed_resume.raw_skills}
        c_skills = {s for s in c_skills if s}

        # Normalize job must-have and nice-to-have skills
        j_skills = {self.ontology_builder.normalize_skill(s) for s in [*job.must_have, *job.nice_to_have]}
        j_skills = {s for s in j_skills if s}

        # 1. Skill Overlap (Jaccard similarity)
        skill_overlap = 0.0
        if c_skills or j_skills:
            union = c_skills.union(j_skills)
            intersection = c_skills.intersection(j_skills)
            skill_overlap = len(intersection) / len(union) if union else 0.0

        # 2. KG Skill Distance
        # Average distance from must-have skills to candidate skills in the Graph
        kg_distance_score = 1.0
        must_haves = [self.ontology_builder.normalize_skill(s) for s in job.must_have]
        must_haves = [s for s in must_haves if s]
        if must_haves:
            distances = []
            for req_skill in must_haves:
                min_dist = 3.0  # Max path distance penalty
                for cand_skill in c_skills:
                    d = self.graph_builder.skill_distance(kg, cand_skill, req_skill)
                    if d is not None and d < min_dist:
                        min_dist = float(d)
                distances.append(min_dist)
            avg_dist = sum(distances) / len(distances) if distances else 3.0
            # Scale distance to [0.0, 1.0]: 0 distance = 1.0 score, max distance (3+) = 0.25 score
            kg_distance_score = 1.0 / (1.0 + avg_dist)

        # 3. Dense Similarity (from retrieval score, range expected [-1, 1] -> normalized to [0, 1])
        dense_sim = retrieval_scores.get("dense", 0.0)
        # normalize cosine similarity from [-1, 1] to [0.0, 1.0]
        dense_similarity = float((dense_sim + 1.0) / 2.0)

        # 4. BM25 score (sigmoidal normalization to [0.0, 1.0])
        bm25_raw = retrieval_scores.get("bm25", 0.0)
        bm25_score = float(bm25_raw / (bm25_raw + 8.0) if bm25_raw > 0 else 0.0)

        # 5. Trajectory Alignment (experience duration and role history counts)
        trajectory_alignment = 0.5
        t_vector = self.trajectory_analyzer.compute_trajectory_vector(kg, parsed_resume.candidate_id)
        if t_vector["role_count"] > 0:
            duration_score = min(1.0, t_vector["avg_role_duration_months"] / 24.0)
            role_score = min(1.0, t_vector["role_count"] / 3.0)
            trajectory_alignment = float(0.5 * duration_score + 0.5 * role_score)

        # 6. Behavioral Score
        behavioral_score = 0.5
        if behavioral_profile:
            raw_score = (
                0.4 * behavioral_profile.recency_score
                + 0.3 * behavioral_profile.contribution_frequency
                + 0.2 * behavioral_profile.learning_velocity
                + 0.1 * behavioral_profile.open_source_breadth
            )
            conf = behavioral_profile.signal_confidence
            # Blend with neutral score based on confidence
            behavioral_score = float(raw_score * conf + 0.5 * (1.0 - conf))

        # 7. Seniority Match
        seniority_match = 1.0
        if job.seniority and experience_years is not None:
            expected_yoe = 0.0
            j_sen = str(job.seniority).lower()
            if any(kw in j_sen for kw in ["senior", "lead", "staff", "principal", "sr"]):
                expected_yoe = 5.0
            elif "mid" in j_sen:
                expected_yoe = 3.0

            if expected_yoe > 0:
                if experience_years >= expected_yoe:
                    seniority_match = 1.0
                else:
                    seniority_match = float(max(0.0, 1.0 - (expected_yoe - experience_years) / expected_yoe))

        # 8. Rubric evaluations and Honeypots
        jd_positive_signal_count = 0
        jd_disqualifier_flags = []
        honeypot_score = 0.0

        if metadata is not None:
            scorer = JDRubricScorer()
            gh_url = metadata.get("github_url")
            jd_positive_signal_count, jd_disqualifier_flags = scorer.evaluate_candidate(
                resume=parsed_resume,
                metadata=metadata,
                experience_years=experience_years,
                github_url=gh_url,
            )

        if behavioral_profile is not None:
            honeypot_score = getattr(behavioral_profile, "honeypot_score", 0.0)

        return FeatureVector(
            skill_overlap=skill_overlap,
            kg_skill_distance=kg_distance_score,
            dense_similarity=dense_similarity,
            bm25_score=bm25_score,
            trajectory_alignment=trajectory_alignment,
            behavioral_score=behavioral_score,
            seniority_match=seniority_match,
            jd_positive_signal_count=jd_positive_signal_count,
            jd_disqualifier_flags=jd_disqualifier_flags,
            honeypot_score=honeypot_score,
        )
