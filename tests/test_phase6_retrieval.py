import pytest

from embeddings.indexer import QdrantIndexer
from embeddings.models import CandidateVectorPoint, EmbeddingConfig
from embeddings.service import EmbeddingService
from parsers.models import ParsedJob, ParsedResume
from retrieval.bm25 import BM25Index
from retrieval.dense import DenseRetriever
from retrieval.filter import MetadataFilter
from retrieval.hybrid import HybridRetriever


def test_rrf_math_and_sorting() -> None:
    retriever = HybridRetriever(
        bm25_index=BM25Index(),
        dense_retriever=DenseRetriever(QdrantIndexer()),
        metadata_filter=MetadataFilter(),
        embedding_service=EmbeddingService(),
    )

    # c1 is rank 1 in BM25, rank 2 in dense
    # c2 is rank 2 in BM25, rank 1 in dense
    bm25_results = [{"candidate_id": "c1", "score": 10.0}, {"candidate_id": "c2", "score": 5.0}]
    dense_results = [{"candidate_id": "c2", "score": 0.9}, {"candidate_id": "c1", "score": 0.7}]

    fused = retriever.fuse(bm25_results, dense_results, k=60)

    # c1 and c2 should have the exact same RRF score in this symmetric case
    assert len(fused) == 2
    assert fused[0]["fused_score"] == fused[1]["fused_score"]
    assert fused[0]["fused_score"] == pytest.approx(1 / 61 + 1 / 62)

    # Asymmetric test where c1 dominates
    bm25_results = [{"candidate_id": "c1", "score": 10.0}, {"candidate_id": "c2", "score": 5.0}]
    dense_results = [{"candidate_id": "c1", "score": 0.9}, {"candidate_id": "c2", "score": 0.7}]

    fused = retriever.fuse(bm25_results, dense_results, k=60)
    assert fused[0]["candidate_id"] == "c1"
    assert fused[0]["fused_score"] == pytest.approx(1 / 61 + 1 / 61)
    assert fused[1]["candidate_id"] == "c2"
    assert fused[1]["fused_score"] == pytest.approx(1 / 62 + 1 / 62)


def test_hard_filters_exclusion_rules() -> None:
    job = ParsedJob(
        job_id="j1",
        title="Senior Python Developer",
        seniority="senior",
        location="Bengaluru",
        must_have=["Python", "FastAPI"],
        raw_text="Need a senior developer",
    )

    candidates = [
        # c1: matches all
        {
            "candidate_id": "c1",
            "payload": {
                "skills": ["Python", "FastAPI"],
                "location": "Bengaluru",
                "experience_years": 6.0,
            },
        },
        # c2: location mismatch (Pune vs Bengaluru)
        {
            "candidate_id": "c2",
            "payload": {
                "skills": ["Python", "FastAPI"],
                "location": "Pune",
                "experience_years": 7.0,
            },
        },
        # c3: seniority/yoe mismatch (requires senior: >= 5 years, candidate has 2)
        {
            "candidate_id": "c3",
            "payload": {
                "skills": ["Python", "FastAPI"],
                "location": "Bengaluru",
                "experience_years": 2.0,
            },
        },
        # c4: must-have skills mismatch
        {
            "candidate_id": "c4",
            "payload": {
                "skills": ["Python", "Django"],
                "location": "Bengaluru",
                "experience_years": 6.0,
            },
        },
        # c5: missing values should degrade gracefully (pass)
        {
            "candidate_id": "c5",
            "payload": {
                "skills": ["Python", "FastAPI"],
            },
        },
    ]

    metadata_filter = MetadataFilter()
    passed = metadata_filter.apply_hard_filters(candidates, job)

    passed_ids = {c["candidate_id"] for c in passed}
    assert "c1" in passed_ids
    assert "c5" in passed_ids  # missing details should gracefully pass
    assert "c2" not in passed_ids  # location filter
    assert "c3" not in passed_ids  # seniority filter
    assert "c4" not in passed_ids  # must-have skill filter


def test_hybrid_retriever_end_to_end() -> None:
    # 1. Setup embedding service & indexers
    config = EmbeddingConfig(dimension=64)
    service = EmbeddingService(config)
    indexer = QdrantIndexer(vector_size=64)
    bm25 = BM25Index()

    # 2. Add candidates to indexes
    c1 = ParsedResume(
        candidate_id="c1",
        raw_skills=["Python", "FastAPI"],
        sections={"summary": "Backend developer"},
    )
    c2 = ParsedResume(
        candidate_id="c2",
        raw_skills=["Java", "Spring"],
        sections={"summary": "Enterprise developer"},
    )

    bm25.build_bm25_index([c1, c2])

    indexer.upsert_candidates(
        [
            CandidateVectorPoint(
                id="c1",
                vector=service.embed_candidate(c1),
                payload={"skills": ["Python", "FastAPI"], "experience_years": 6.0},
            ),
            CandidateVectorPoint(
                id="c2",
                vector=service.embed_candidate(c2),
                payload={"skills": ["Java", "Spring"], "experience_years": 4.0},
            ),
        ]
    )

    dense = DenseRetriever(indexer)
    filter_mask = MetadataFilter()

    hybrid = HybridRetriever(
        bm25_index=bm25,
        dense_retriever=dense,
        metadata_filter=filter_mask,
        embedding_service=service,
    )

    job = ParsedJob(
        job_id="j1",
        title="Python Engineer",
        seniority="senior",
        must_have=["Python"],
        raw_text="Python and FastAPI senior developer",
    )

    results = hybrid.retrieve_hybrid(job, top_k=10)

    # c2 is disqualified (missing must-have Python), only c1 should be in the shortlist
    assert len(results) == 1
    assert results[0].candidate_id == "c1"
    assert results[0].passes_hard_filters is True
    assert results[0].fused_score > 0.0
