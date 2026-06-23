import networkx as nx

from evaluation.metrics import MetricCalculator
from evaluation.models import EvaluationResult, RelevanceJudgment
from feature_engineering.behavioral import BehavioralProfile
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.features import FeatureBuilder
from ranking_engine.scoring import ScoringEngine
from reranking.reranker import CrossEncoderReranker, ScoreBlender
from retrieval.hybrid import HybridRetriever


class EvaluationHarness:
    """Benchmark harness evaluating full-system ranking against keyword baselines."""

    def __init__(self) -> None:
        self.calculator = MetricCalculator()

    def run_baseline(self, jobs: list[ParsedJob], resumes: list[ParsedResume]) -> dict[str, list[str]]:
        """Run naive keyword overlap baseline: counts matching skills."""
        rankings = {}
        for job in jobs:
            j_skills = {s.lower().strip() for s in [*job.must_have, *job.nice_to_have] if s}
            scores = []
            for resume in resumes:
                c_skills = {s.lower().strip() for s in resume.raw_skills if s}
                overlap = len(j_skills.intersection(c_skills))
                scores.append((resume.candidate_id, overlap))

            # Sort descending by overlap, tie-breaker alphabetically by candidate_id
            scores.sort(key=lambda x: (-x[1], x[0]))
            rankings[job.job_id] = [item[0] for item in scores]
        return rankings

    def run_full_system(
        self,
        jobs: list[ParsedJob],
        hybrid_retriever: HybridRetriever,
        feature_builder: FeatureBuilder,
        scoring_engine: ScoringEngine,
        reranker: CrossEncoderReranker,
        blender: ScoreBlender,
        resumes: dict[str, ParsedResume],
        kg: nx.DiGraph,
        behav_profiles: dict[str, BehavioralProfile],
        candidates_meta: dict[str, float],
        alpha: float = 0.5,
    ) -> dict[str, list[str]]:
        """Run the full hybrid retrieval + feature builder + cross-encoder rerank pipeline."""
        rankings = {}
        for job in jobs:
            # 1. Hybrid Retrieval
            shortlist = hybrid_retriever.retrieve_hybrid(job, top_k=100)
            if not shortlist:
                rankings[job.job_id] = []
                continue

            # 2. Build features & score candidates
            scored_candidates = []
            for match in shortlist:
                cid = match.candidate_id
                resume = resumes.get(cid)
                if not resume:
                    continue

                f_vector = feature_builder.build_feature_vector(
                    parsed_resume=resume,
                    job=job,
                    kg=kg,
                    behavioral_profile=behav_profiles.get(cid),
                    retrieval_scores={"dense": match.dense_score, "bm25": match.bm25_score},
                    experience_years=candidates_meta.get(cid),
                )
                scored = scoring_engine.score_candidate(cid, f_vector)
                scored_candidates.append(scored)

            # Sort to get baseline ranks
            scored_candidates.sort(key=lambda x: x.final_score, reverse=True)
            original_ranks = {sc.candidate_id: idx for idx, sc in enumerate(scored_candidates, start=1)}

            # 3. Cross-Encoder Reranking & Score Blending
            cand_ids = [sc.candidate_id for sc in scored_candidates]
            # Construct candidate resume texts
            from embeddings.text import build_candidate_text, build_job_text
            job_text = build_job_text(job)
            cand_texts = [build_candidate_text(resumes[cid]) for cid in cand_ids]

            pairs = reranker.build_reranker_pairs(job_text, cand_texts)
            ce_scores = reranker.rerank(pairs)

            blended_results = []
            for idx, sc in enumerate(scored_candidates):
                cid = sc.candidate_id
                blend = blender.blend_scores(sc.final_score, ce_scores[idx], alpha=alpha)
                blended_results.append((cid, blend))

            # Sort by blended score descending
            blended_results.sort(key=lambda x: (x[1], -original_ranks[x[0]]), reverse=True)
            rankings[job.job_id] = [item[0] for item in blended_results]

        return rankings

    def compare(
        self,
        baseline_recommendations: dict[str, list[str]],
        system_recommendations: dict[str, list[str]],
        judgments: list[RelevanceJudgment],
        k: int = 5,
    ) -> list[EvaluationResult]:
        """Compute metrics for both systems and compare the delta."""
        # Group judgments by job_id
        job_judgments: dict[str, dict[str, int]] = {}
        for j in judgments:
            job_judgments.setdefault(j.job_id, {})[j.candidate_id] = j.relevance

        # Map to relevant sets (relevance >= 1 is considered relevant)
        job_relevant_sets: dict[str, set[str]] = {}
        for job_id, cand_map in job_judgments.items():
            job_relevant_sets[job_id] = {cid for cid, rel in cand_map.items() if rel >= 1}

        metrics = ["Precision@k", "MRR", "NDCG@k"]
        scores_base = {m: [] for m in metrics}
        scores_sys = {m: [] for m in metrics}

        for job_id in job_judgments:
            cand_map = job_judgments[job_id]
            rel_set = job_relevant_sets.get(job_id, set())

            rec_base = baseline_recommendations.get(job_id, [])
            rec_sys = system_recommendations.get(job_id, [])

            # Compute baseline
            scores_base["Precision@k"].append(self.calculator.compute_precision_at_k(rec_base, rel_set, k))
            scores_base["MRR"].append(self.calculator.compute_mrr(rec_base, rel_set))
            scores_base["NDCG@k"].append(self.calculator.compute_ndcg_at_k(rec_base, cand_map, k))

            # Compute system
            scores_sys["Precision@k"].append(self.calculator.compute_precision_at_k(rec_sys, rel_set, k))
            scores_sys["MRR"].append(self.calculator.compute_mrr(rec_sys, rel_set))
            scores_sys["NDCG@k"].append(self.calculator.compute_ndcg_at_k(rec_sys, cand_map, k))

        results = []
        for m in metrics:
            avg_base = sum(scores_base[m]) / len(scores_base[m]) if scores_base[m] else 0.0
            avg_sys = sum(scores_sys[m]) / len(scores_sys[m]) if scores_sys[m] else 0.0
            results.append(
                EvaluationResult(
                    metric_name=m.replace("@k", f"@{k}"),
                    baseline_score=float(avg_base),
                    system_score=float(avg_sys),
                    delta=float(avg_sys - avg_base),
                )
            )
        return results
