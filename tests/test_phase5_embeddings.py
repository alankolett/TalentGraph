import json

import pandas as pd

from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.pipeline import Phase5Pipeline
from embeddings.service import EmbeddingService
from parsers.models import ExperienceEntry, ParsedJob, ParsedResume


def test_embedding_dimension_matches_config() -> None:
    service = EmbeddingService(EmbeddingConfig(dimension=64))
    resume = ParsedResume(candidate_id="c1", raw_skills=["Python"], sections={})

    vector = service.embed_candidate(resume)

    assert len(vector) == 64


def test_near_duplicate_resumes_have_high_cosine_similarity() -> None:
    service = EmbeddingService(EmbeddingConfig(dimension=128))
    first = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI", "Qdrant"],
        sections={"summary": "Backend engineer building ranking APIs."},
    )
    second = ParsedResume(
        candidate_id="c2",
        raw_skills=["Python", "FastAPI", "Qdrant"],
        sections={"summary": "Backend engineer building ranking APIs."},
    )

    similarity = service.cosine_similarity(
        service.embed_candidate(first),
        service.embed_candidate(second),
    )

    assert similarity > 0.9


def test_indexed_candidate_retrievable_by_job_equivalent_query() -> None:
    service = EmbeddingService(EmbeddingConfig(dimension=128))
    indexer = QdrantIndexer(vector_size=128)
    candidate = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI", "Qdrant"],
        sections={"summary": "Backend engineer for ranking APIs."},
        experience_entries=[
            ExperienceEntry(title="Backend Engineer", description="Built FastAPI services.")
        ],
    )
    job = ParsedJob(
        job_id="j1",
        title="Backend Engineer",
        must_have=["Python", "FastAPI"],
        nice_to_have=["Qdrant"],
        responsibilities=["Build ranking APIs"],
        raw_text="Build FastAPI ranking services with Qdrant.",
    )
    indexer.upsert_candidates(
        [
            CandidateVectorPoint(
                id=candidate.candidate_id,
                vector=service.embed_candidate(candidate),
                payload={"skills": candidate.raw_skills},
            )
        ]
    )

    results = indexer.search_by_vector(service.embed_job(job), top_k=10)

    assert results[0].id == "c1"


def test_phase5_pipeline_writes_embeddings_and_indexes_candidates(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    embeddings_dir = tmp_path / "embeddings"
    processed_dir.mkdir()
    resume = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI"],
        sections={"summary": "Backend engineer."},
    )
    job = ParsedJob(
        job_id="j1",
        title="Backend Engineer",
        must_have=["Python"],
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
    pd.DataFrame(
        [
            {
                "id": "c1",
                "location": "Remote",
                "experience_years": 5.0,
            }
        ]
    ).to_parquet(processed_dir / "candidates.parquet", index=False)

    result = Phase5Pipeline.from_config(EmbeddingConfig(dimension=64)).run(
        processed_dir,
        embeddings_dir,
    )

    candidate_embeddings = pd.read_parquet(result.candidate_embeddings_path)
    job_embeddings = pd.read_parquet(result.job_embeddings_path)

    assert result.indexed_count == 1
    assert len(candidate_embeddings.iloc[0]["vector"]) == 64
    assert len(job_embeddings.iloc[0]["vector"]) == 64
