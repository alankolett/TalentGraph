import argparse
import csv
import json
import pickle
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from embeddings.text import build_candidate_text, build_job_text, clean_text
from explainability.classifier import TagClassifier
from explainability.generator import ExplanationGenerator
from feature_engineering.behavioral import BehavioralProfile
from knowledge_graph.graph import KnowledgeGraphBuilder
from parsers.models import ParsedJob, ParsedResume
from ranking_engine.features import FeatureBuilder
from ranking_engine.scoring import ScoringEngine
from reranking.reranker import CrossEncoderReranker, ScoreBlender
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever
from retrieval.models import RetrievalResult


class LightExperienceEntry:
    def __init__(self, d: dict):
        self.title = d.get("title", "")
        self.company = d.get("company", "")
        self.description = d.get("description", "")


class LightParsedResume:
    def __init__(self, d: dict):
        self.candidate_id = d.get("candidate_id")
        self.raw_skills = d.get("raw_skills", [])
        self.sections = d.get("sections", {})
        self.experience_entries = [LightExperienceEntry(e) for e in d.get("experience_entries", [])]


def build_candidate_text_dict(data: dict) -> str:
    """Fast candidate text representation builder bypassing Pydantic overhead."""
    skills = ", ".join(data.get("raw_skills", []))
    summary = data.get("sections", {}).get("summary", "")
    recent_roles = []
    for entry in data.get("experience_entries", [])[:3]:
        parts = [entry.get("title", "")]
        if entry.get("company"):
            parts.append(f"at {entry.get('company')}")
        if entry.get("description"):
            parts.append(entry.get("description"))
        recent_roles.append(" ".join(parts))

    components = [
        f"Skills: {skills}" if skills else "",
        f"Recent roles: {' | '.join(recent_roles)}" if recent_roles else "",
        f"Summary: {summary}" if summary else "",
    ]
    text = clean_text(" ".join(component for component in components if component))
    return text or clean_text(skills) or "Candidate profile"


def main() -> None:
    parser = argparse.ArgumentParser(description="Explainable Candidate Ranking Engine CLI.")
    parser.add_argument(
        "--candidates",
        default="data/raw/redrob_challenge/candidates.jsonl",
        help="Path to candidates JSONL file.",
    )
    parser.add_argument(
        "--out",
        default="submission.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    processed_dir = Path("data/processed")
    graph_dir = Path("data/knowledge_graph")
    embeddings_dir = Path("data/embeddings")

    # 1. Load the structured job description
    job_desc_path = processed_dir / "job_redrob_senior_ai_engineer.json"
    if job_desc_path.exists():
        with open(job_desc_path, encoding="utf-8") as f:
            job_data = json.load(f)
            job = ParsedJob(
                job_id=job_data["id"],
                title=job_data["title"],
                location=job_data["location"],
                must_have=job_data["must_have_skills"],
                nice_to_have=job_data["nice_to_have_skills"],
                raw_text=job_data["raw_description"],
                seniority=job_data.get("seniority", "Senior"),
            )
    else:
        # Fallback to hardcoded job definition
        job = ParsedJob(
            job_id="job_redrob_senior_ai_engineer",
            title="Senior AI Engineer — Founding Team",
            location="Pune/Noida, India",
            must_have=[
                "embeddings-based retrieval systems",
                "vector databases",
                "hybrid search infrastructure",
                "Python",
                "evaluation frameworks for ranking systems"
            ],
            nice_to_have=[
                "LLM fine-tuning",
                "learning-to-rank models",
                "HR-tech",
                "recruiting tech",
                "marketplace products",
                "distributed systems",
                "large-scale inference optimization",
                "open-source contributions"
            ],
            raw_text="Job Description: Senior AI Engineer — Founding Team",
            seniority="Senior",
        )

    print("Loading candidate metadata and identifiers...")

    # 2. Read candidate IDs (optimizing default run using candidates.parquet)
    candidate_ids = []
    candidates_path = Path(args.candidates)
    is_default = (candidates_path.resolve() == Path("data/raw/redrob_challenge/candidates.jsonl").resolve())

    if is_default and Path("data/processed/candidates.parquet").exists():
        # Fast path: read IDs directly from parquet (takes 1-2 seconds)
        df = pd.read_parquet("data/processed/candidates.parquet")
        candidate_ids = df["id"].astype(str).tolist()
    elif candidates_path.exists():
        # Slow path: read candidate IDs from custom file
        with open(candidates_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        cand_obj = json.loads(line)
                        cid = cand_obj.get("candidate_id") or cand_obj.get("id")
                        if cid:
                            candidate_ids.append(cid)
                    except Exception:
                        pass
    candidate_ids_set = set(candidate_ids)

    # 3. Load precomputed candidates metadata
    candidates_meta = {}
    candidates_meta_dicts = {}
    meta_path = processed_dir / "candidates.parquet"
    if meta_path.exists():
        df = pd.read_parquet(meta_path)
        records = df.to_dict(orient="records")
        for row in records:
            cid = str(row["id"])
            if cid not in candidate_ids_set:
                continue
            candidates_meta[cid] = (
                float(row["experience_years"]) if pd.notna(row["experience_years"]) else 0.0
            )

            # Parse activity_metadata if it is a JSON string
            act_meta = {}
            val = row.get("activity_metadata")
            if val and pd.notna(val):
                if isinstance(val, str):
                    try:
                        act_meta = json.loads(val)
                    except Exception:
                        pass
                elif isinstance(val, dict):
                    act_meta = val

            # Also parse redrob_signals if present
            if not act_meta:
                val_red = row.get("redrob_signals")
                if val_red and pd.notna(val_red):
                    if isinstance(val_red, str):
                        try:
                            act_meta = json.loads(val_red)
                        except Exception:
                            pass
                    elif isinstance(val_red, dict):
                        act_meta = val_red

            # Construct cand_meta
            candidates_meta_dicts[cid] = {
                "location": row.get("location") if pd.notna(row.get("location")) else "",
                "willing_to_relocate": act_meta.get("willing_to_relocate"),
                "notice_period_days": act_meta.get("notice_period_days"),
                "github_activity_score": act_meta.get("github_activity_score", -1),
                "total_career_months": (
                    float(row.get("total_career_months"))
                    if pd.notna(row.get("total_career_months"))
                    else 0.0
                ),
                "num_employers": (
                    int(row.get("num_employers")) if pd.notna(row.get("num_employers")) else 0
                ),
                "github_url": row.get("github_url") if pd.notna(row.get("github_url")) else None,
            }

    # Fill fallback metadata for dynamic IDs
    for cid in candidate_ids:
        if cid not in candidates_meta:
            candidates_meta[cid] = 0.0
        if cid not in candidates_meta_dicts:
            candidates_meta_dicts[cid] = {
                "location": "",
                "willing_to_relocate": False,
                "notice_period_days": None,
                "github_activity_score": -1,
                "total_career_months": 0.0,
                "num_employers": 0,
                "github_url": None,
            }

    # 4. Load Knowledge Graph and Embeddings
    print("Loading Knowledge Graph and candidate embeddings...")
    kg_builder = KnowledgeGraphBuilder()
    kg_path = graph_dir / "candidate_kg.gpickle"
    kg = kg_builder.load_graph(kg_path) if kg_path.exists() else nx.DiGraph()

    indexer = QdrantIndexer(vector_size=128)
    points = []
    embeddings_path = embeddings_dir / "candidate_embeddings.parquet"
    if embeddings_path.exists():
        emb_df = pd.read_parquet(embeddings_path)
        emb_records = emb_df.to_dict(orient="records")
        for row in emb_records:
            cid = str(row["id"])
            if cid not in candidate_ids_set:
                continue
            vector = row["vector"]
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            payload_val = row["payload"]
            if isinstance(payload_val, str):
                payload = json.loads(payload_val)
            else:
                payload = payload_val
            points.append(CandidateVectorPoint(id=cid, vector=vector, payload=payload))

    indexed_ids = {p.id for p in points}
    for cid in candidate_ids:
        if cid not in indexed_ids:
            points.append(
                CandidateVectorPoint(
                    id=cid,
                    vector=[0.0] * 128,
                    payload={
                        "skills": [],
                        "experience_years": 0.0,
                        "location": "",
                    },
                )
            )
    indexer.upsert_candidates(points)

    # 5. Load or build BM25 Index
    bm25 = BM25Index()
    bm25_cache_path = processed_dir / "bm25_index.pkl"

    if is_default and bm25_cache_path.exists():
        print("Loading precomputed BM25 index...")
        try:
            with open(bm25_cache_path, "rb") as f:
                bm25 = pickle.load(f)
        except Exception:
            is_default = False  # Trigger fallback build

    if not bm25.candidate_ids:
        # Load resumes dict to build BM25 index dynamically (only if cache missed or custom run)
        print("Building BM25 index dynamically...")
        resumes_dict = {}
        resumes_path = processed_dir / "parsed_resumes.jsonl"
        if resumes_path.exists():
            with open(resumes_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            cid = data["candidate_id"]
                            if cid in candidate_ids_set:
                                resumes_dict[cid] = data
                        except Exception:
                            pass

        corpus_parsed_resumes = []
        for cid in candidate_ids:
            if cid in resumes_dict:
                res_obj = LightParsedResume(resumes_dict[cid])
                corpus_parsed_resumes.append(res_obj)
            else:
                fallback = LightParsedResume({
                    "candidate_id": cid,
                    "sections": {},
                    "raw_skills": [],
                    "experience_entries": [],
                })
                corpus_parsed_resumes.append(fallback)
        bm25.build_bm25_index(corpus_parsed_resumes)

        if is_default:
            try:
                with open(bm25_cache_path, "wb") as f:
                    pickle.dump(bm25, f)
            except Exception:
                pass

    # 6. Initialize Hybrid Retriever
    service = EmbeddingService(EmbeddingConfig(dimension=128))
    dense = DenseRetriever(indexer)
    metadata_filter = MetadataFilter()
    hybrid = HybridRetriever(
        bm25_index=bm25,
        dense_retriever=dense,
        metadata_filter=metadata_filter,
        embedding_service=service,
    )

    print("Running hybrid retrieval...")
    shortlist = hybrid.retrieve_hybrid(job, top_k=500)

    # If shortlist is less than 100, pad it from general hybrid search
    if len(shortlist) < 100:
        print(f"Warning: Only {len(shortlist)} candidates passed hard filters. Padding...")
        query_vector = service.embed_job(job)
        dense_results = dense.retrieve_dense(query_vector, top_k=1000)
        bm25_results = bm25.retrieve_bm25(job, top_k=1000)
        fused_scores = hybrid.fuse(bm25_results, dense_results)

        existing_ids = {r.candidate_id for r in shortlist}
        for item in fused_scores:
            if len(shortlist) >= 100:
                break
            cid = item["candidate_id"]
            if cid not in existing_ids:
                shortlist.append(
                    RetrievalResult(
                        candidate_id=cid,
                        bm25_score=item["bm25_score"],
                        dense_score=item["dense_score"],
                        passes_hard_filters=True,
                        fused_score=item["fused_score"],
                    )
                )

    # 7. Lazy-load parsed resumes and behavioral profiles for shortlisted candidates ONLY
    print("Loading details for shortlisted candidates...")
    shortlist_cids = {match.candidate_id for match in shortlist}
    shortlist_resumes = {}
    resumes_path = processed_dir / "parsed_resumes.jsonl"
    if resumes_path.exists():
        with open(resumes_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        cid = line.split('"', 4)[3]
                        if cid in shortlist_cids:
                            shortlist_resumes[cid] = ParsedResume.model_validate(json.loads(line))
                    except Exception:
                        pass

    shortlist_behav = {}
    behav_path = processed_dir / "behavioral_profiles.jsonl"
    if behav_path.exists():
        with open(behav_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        cid = line.split('"', 4)[3]
                        if cid in shortlist_cids:
                            shortlist_behav[cid] = BehavioralProfile.model_validate(json.loads(line))
                    except Exception:
                        pass

    # 8. Score shortlisted candidates
    print("Scoring candidates...")
    feature_builder = FeatureBuilder()
    scoring_engine = ScoringEngine()

    scored_candidates = []
    for match in shortlist:
        cid = match.candidate_id
        resume = shortlist_resumes.get(cid) or ParsedResume(
            candidate_id=cid,
            sections={},
            raw_skills=[],
            experience_entries=[],
        )
        behav = shortlist_behav.get(cid)

        f_vector = feature_builder.build_feature_vector(
            parsed_resume=resume,
            job=job,
            kg=kg,
            behavioral_profile=behav,
            retrieval_scores={"dense": match.dense_score, "bm25": match.bm25_score},
            experience_years=candidates_meta.get(cid),
            metadata=candidates_meta_dicts.get(cid),
        )
        scored = scoring_engine.score_candidate(cid, f_vector)
        scored_candidates.append(scored)

    # Sort to assign original ranks
    scored_candidates.sort(key=lambda x: x.final_score, reverse=True)

    # 9. Rerank top candidates
    print("Running cross-encoder reranking...")
    reranker = CrossEncoderReranker(backend="mock")
    blender = ScoreBlender()

    cand_ids = [sc.candidate_id for sc in scored_candidates]
    cand_texts = [build_candidate_text(shortlist_resumes.get(cid) or ParsedResume(
        candidate_id=cid, sections={}, raw_skills=[], experience_entries=[]
    )) for cid in cand_ids]

    job_text = build_job_text(job)
    pairs = reranker.build_reranker_pairs(job_text, cand_texts)
    ce_scores = reranker.rerank(pairs)

    blended_results = []
    for idx, sc in enumerate(scored_candidates):
        cid = sc.candidate_id
        blend = blender.blend_scores(sc.final_score, ce_scores[idx], alpha=0.5)
        blended_results.append((cid, blend, sc.features))

    # Sort by blended score descending, using candidate_id ascending as tiebreaker
    blended_results.sort(key=lambda x: (-x[1], x[0]))

    # Slice top 100
    top_100 = blended_results[:100]

    # 10. Generate Explanations & Format CSV
    print("Generating grounded justifications...")
    explanation_generator = ExplanationGenerator(llm_provider=None)
    tag_classifier = TagClassifier()

    output_rows = []
    for idx, (cid, score, f_vector) in enumerate(top_100, start=1):
        tags = tag_classifier.classify_tags(f_vector)
        resume = shortlist_resumes.get(cid)
        skills = resume.raw_skills if resume else []

        explained = explanation_generator.generate_explanation(
            candidate_id=cid,
            rank=idx,
            final_score=score,
            job=job,
            features=f_vector,
            tags=tags,
            candidate_skills=skills,
            metadata=candidates_meta_dicts.get(cid),
        )
        output_rows.append({
            "candidate_id": cid,
            "rank": idx,
            "score": score,
            "reasoning": explained.narrative,
        })

    # Save to CSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for row in output_rows:
            writer.writerow([row["candidate_id"], row["rank"], f"{row['score']:.6f}", row["reasoning"]])

    print(f"Successfully generated validation-clean submission CSV: {out_path.resolve()}")


if __name__ == "__main__":
    main()
