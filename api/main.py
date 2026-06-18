import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware

from api.database import DatabaseManager
from api.orchestrator import RankingOrchestrator
from common.settings import Settings, get_settings
from embeddings.models import EmbeddingConfig
from embeddings.service import EmbeddingService
from preprocessing.cleaning import DataCleaner
from preprocessing.models import CandidateRecord, JobRecord
from preprocessing.validation import SchemaValidator
from reranking.reranker import CrossEncoderReranker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model singletons once at startup
    settings = get_settings()
    app.state.db = DatabaseManager()
    
    # Initialize embedding service with default config
    app.state.embeddings = EmbeddingService(EmbeddingConfig(dimension=128))
    
    # Initialize cross-encoder
    app.state.reranker = CrossEncoderReranker(backend="mock")
    
    # Setup orchestrator
    app.state.orchestrator = RankingOrchestrator(
        db=app.state.db,
        embedding_service=app.state.embeddings,
        cross_encoder=app.state.reranker,
    )
    yield


app = FastAPI(title="TalentGraph API", lifespan=lifespan)

# Add CORS Middleware to allow Next.js requests from localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "qdrant_url": settings.qdrant_url,
        "sqlite_path": str(settings.sqlite_path),
        "has_anthropic": str(settings.has_anthropic_credentials),
        "has_groq": str(settings.has_groq_credentials),
        "has_gemini": str(settings.has_gemini_credentials),
    }


@app.get("/jobs")
def get_jobs() -> dict[str, Any]:
    jobs = app.state.db.get_all_jobs()
    return {"status": "success", "jobs": jobs}


@app.get("/candidates")
def get_candidates() -> dict[str, Any]:
    candidates = app.state.db.get_all_candidates()
    return {"status": "success", "candidates": candidates}


@app.post("/jobs", status_code=201)
def add_job(job: JobRecord) -> dict[str, Any]:
    app.state.db.save_job(job.model_dump())
    return {"status": "success", "job_id": job.id}


@app.post("/candidates/bulk-upload", status_code=201)
async def upload_candidates(
    request: Request,
    file: UploadFile = File(None),
    candidates: list[CandidateRecord] | None = None,
) -> dict[str, Any]:
    # Dynamic JSON payload fallback when standard parsing fails due to multipart configuration
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, list):
                candidates = [CandidateRecord.model_validate(c) for c in body]
            elif isinstance(body, dict) and "candidates" in body:
                candidates = [CandidateRecord.model_validate(body_c) for body_c in body["candidates"]]
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse JSON body: {exc}")

    # Support file upload (CSV or JSON)
    if file:
        content = await file.read()
        ext = Path(file.filename).suffix.lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(io.BytesIO(content))
            elif ext in {".json", ".jsonl", ".ndjson"}:
                df = pd.read_json(io.BytesIO(content), lines=(ext != ".json"))
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or JSON.")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

        # Process through Phase 2 cleaner and validator
        cleaner = DataCleaner()
        validator = SchemaValidator()

        cleaned = cleaner.clean_candidates(df)
        valid_df, _ = validator.validate_candidates(cleaned, file.filename)

        for _, row in valid_df.iterrows():
            # Convert row series to dictionary
            cand_dict = row.to_dict()
            app.state.db.save_candidate(cand_dict)

        return {"status": "success", "count": len(valid_df)}

    # Support JSON list payload
    if candidates:
        for cand in candidates:
            app.state.db.save_candidate(cand.model_dump(mode="json"))
        return {"status": "success", "count": len(candidates)}

    raise HTTPException(status_code=400, detail="Provide a 'file' upload or a JSON list of 'candidates'.")


@app.post("/rank/{job_id}")
def run_ranking(
    job_id: str,
    alpha: float = 0.5,
    top_n: int = 20,
    provider: str | None = None,
) -> dict[str, Any]:
    try:
        results = app.state.orchestrator.orchestrate_ranking(
            job_id=job_id, alpha=alpha, top_n=top_n, provider=provider
        )
        return {"status": "success", "results": results}
    except ValueError as exc:
        # 404 for missing job or candidates
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/rank/{job_id}/results")
def get_ranking_results(job_id: str) -> dict[str, Any]:
    results = app.state.db.get_rankings(job_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No rankings found for job '{job_id}'")
    return {"status": "success", "results": results}


@app.get("/candidates/{id}")
def get_candidate(id: str) -> dict[str, Any]:
    cand = app.state.db.get_candidate(id)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{id}' not found.")
    return {"status": "success", "candidate": cand}
