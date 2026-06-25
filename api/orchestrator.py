from typing import Any

from api.database import DatabaseManager
from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint
from embeddings.service import EmbeddingService
from explainability.classifier import TagClassifier
from explainability.generator import ExplanationGenerator
from feature_engineering.behavioral import (
    BehavioralSignalExtractor,
    SignalNormalizer,
)
from knowledge_graph.graph import KnowledgeGraphBuilder
from parsers.models import ParsedJob
from parsers.resumes import ResumeParser
from preprocessing.models import CandidateRecord
from ranking_engine.features import FeatureBuilder
from ranking_engine.scoring import ScoringEngine
from reranking.reranker import CrossEncoderReranker, ScoreBlender
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever


class RankingOrchestrator:
    """Orchestrates candidate retrieval, scoring, reranking, and explainability on database data."""

    def __init__(
        self,
        db: DatabaseManager,
        embedding_service: EmbeddingService,
        cross_encoder: CrossEncoderReranker,
        llm_provider: Any = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.cross_encoder = cross_encoder

        self.resume_parser = ResumeParser()
        self.behavioral_extractor = BehavioralSignalExtractor()
        self.behavioral_normalizer = SignalNormalizer()
        self.kg_builder = KnowledgeGraphBuilder()
        self.feature_builder = FeatureBuilder()
        self.scoring_engine = ScoringEngine()
        self.score_blender = ScoreBlender()
        self.tag_classifier = TagClassifier()
        self.explanation_generator = ExplanationGenerator(llm_provider)

    def orchestrate_ranking(
        self,
        job_id: str,
        alpha: float = 0.5,
        top_n: int = 20,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run the end-to-end ranking and explainability pipeline for a job."""
        # Resolve LLM provider dynamically on each request
        from common.llm import get_llm_provider
        try:
            llm = get_llm_provider(name=provider)
        except Exception:
            llm = None
        self.explanation_generator.llm_provider = llm

        # 1. Fetch job
        job_data = self.db.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job with ID '{job_id}' not found.")
        job = ParsedJob.model_validate(job_data)

        # 2. Fetch and parse candidates
        raw_candidates = self.db.get_all_candidates()
        if not raw_candidates:
            raise ValueError("No candidates ingested. Please upload candidates first.")

        parsed_resumes = []
        parsed_resumes_map = {}
        candidates_meta = {}
        candidates_meta_dicts = {}
        raw_profiles = []
        for cand in raw_candidates:
            record = CandidateRecord.model_validate(cand)
            resume = self.resume_parser.parse(record)
            parsed_resumes.append(resume)
            parsed_resumes_map[record.id] = resume
            candidates_meta[record.id] = record.experience_years or 0.0

            # Construct metadata for JDRubricScorer
            ch = record.career_history or []
            total_months = sum(item.get("duration_months") or 0 for item in ch)
            num_employers = len(ch)
            candidates_meta_dicts[record.id] = {
                "location": record.location or "",
                "willing_to_relocate": record.activity_metadata.get("willing_to_relocate"),
                "notice_period_days": record.activity_metadata.get("notice_period_days"),
                "github_activity_score": record.activity_metadata.get("github_activity_score", -1),
                "total_career_months": total_months,
                "num_employers": num_employers,
                "github_url": str(record.github_url) if record.github_url else None,
            }

            raw_prof = self.behavioral_extractor.extract_raw_profile(
                candidate_id=record.id,
                metadata=record.activity_metadata,
                github_url=str(record.github_url) if record.github_url else None,
                skills=record.skills,
                career_history=record.career_history,
                experience_years=record.experience_years,
            )
            raw_profiles.append(raw_prof)

        # Normalize behavioral profiles
        normalized_behav = self.behavioral_normalizer.normalize_population(raw_profiles)
        behav_profiles = {p.candidate_id: p for p in normalized_behav}

        # 3. Build retrieval indexes dynamically
        # BM25 Index
        bm25_index = BM25Index()
        bm25_index.build_bm25_index(parsed_resumes)

        # Qdrant Indexer
        indexer = QdrantIndexer(vector_size=self.embedding_service.config.dimension)
        candidate_points = []
        for resume in parsed_resumes:
            cid = resume.candidate_id
            payload = {
                "skills": resume.raw_skills,
                "experience_years": candidates_meta.get(cid),
                "location": self.db.get_candidate(cid).get("location"),
            }
            candidate_points.append(
                CandidateVectorPoint(
                    id=cid,
                    vector=self.embedding_service.embed_candidate(resume),
                    payload=payload,
                )
            )
        indexer.upsert_candidates(candidate_points)

        # Candidate Knowledge Graph
        ontology = self.kg_builder.ontology_builder.build_ontology(
            [skill for r in parsed_resumes for skill in r.raw_skills]
            + [*job.must_have, *job.nice_to_have]
        )
        kg = self.kg_builder.build_skill_graph(ontology)
        for resume in parsed_resumes:
            self.kg_builder.add_candidate_to_graph(kg, resume)
        self.kg_builder.add_job_to_graph(kg, job)

        # 4. Hybrid Retrieval
        dense = DenseRetriever(indexer)
        metadata_filter = MetadataFilter()
        hybrid_retriever = HybridRetriever(
            bm25_index=bm25_index,
            dense_retriever=dense,
            metadata_filter=metadata_filter,
            embedding_service=self.embedding_service,
        )
        shortlist = hybrid_retriever.retrieve_hybrid(job, top_k=100)
        if not shortlist:
            return []

        # 5. Build features & score candidates
        scored_candidates = []
        for match in shortlist:
            cid = match.candidate_id
            resume = parsed_resumes_map.get(cid)
            if not resume:
                continue

            f_vector = self.feature_builder.build_feature_vector(
                parsed_resume=resume,
                job=job,
                kg=kg,
                behavioral_profile=behav_profiles.get(cid),
                retrieval_scores={"dense": match.dense_score, "bm25": match.bm25_score},
                experience_years=candidates_meta.get(cid),
                metadata=candidates_meta_dicts.get(cid),
            )
            scored = self.scoring_engine.score_candidate(cid, f_vector)
            scored_candidates.append((scored, f_vector))

        # Sort to get baseline ranks
        scored_candidates.sort(key=lambda x: x[0].final_score, reverse=True)
        original_ranks = {
            item[0].candidate_id: idx
            for idx, item in enumerate(scored_candidates, start=1)
        }

        # 6. Cross-Encoder Reranking & Score Blending
        cand_ids = [item[0].candidate_id for item in scored_candidates]
        from embeddings.text import build_candidate_text, build_job_text

        job_text = build_job_text(job)
        cand_texts = [build_candidate_text(parsed_resumes_map[cid]) for cid in cand_ids]

        pairs = self.cross_encoder.build_reranker_pairs(job_text, cand_texts)
        ce_scores = self.cross_encoder.rerank(pairs)

        blended_results = []
        for idx, (sc, f_vector) in enumerate(scored_candidates):
            cid = sc.candidate_id
            blend = self.score_blender.blend_scores(sc.final_score, ce_scores[idx], alpha=alpha)
            blended_results.append({
                "candidate_id": cid,
                "initial_score": sc.final_score,
                "reranker_score": ce_scores[idx],
                "blended_score": blend,
                "original_rank": original_ranks[cid],
                "f_vector": f_vector,
            })

        # Sort by blended score descending
        blended_results.sort(key=lambda x: (x["blended_score"], -x["original_rank"]), reverse=True)

        # 7. Generate tags & justifications for top N
        final_rankings = []
        for idx, item in enumerate(blended_results[:top_n], start=1):
            cid = item["candidate_id"]
            f_vector = item["f_vector"]
            resume = parsed_resumes_map[cid]

            tags = self.tag_classifier.classify_tags(f_vector)
            explained = self.explanation_generator.generate_explanation(
                candidate_id=cid,
                rank=idx,
                final_score=item["blended_score"],
                job=job,
                features=f_vector,
                tags=tags,
                candidate_skills=resume.raw_skills,
            )

            # Dump feature vector for DB serialization
            feat_dump = f_vector.model_dump()

            final_rankings.append({
                "candidate_id": cid,
                "rank": idx,
                "final_score": item["blended_score"],
                "tags": tags,
                "narrative": explained.narrative,
                "matched_points": explained.matched_points,
                "missing_points": explained.missing_points,
                "features": feat_dump,
            })

        # Save to DB
        self.db.save_rankings(job_id, final_rankings)
        return final_rankings
