# TalentGraph

TalentGraph is a candidate-ranking AI system. Phase 1 establishes the project
foundation: repository structure, environment settings, LLM provider interfaces,
a FastAPI health endpoint, Docker Compose services, and test/lint tooling.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item config\.env.example .env
pytest
uvicorn api.main:app --reload
```

The API health check is available at `http://localhost:8000/health`.

## Phase 2 Data Pipeline

Place raw files at `data/raw/candidates.csv` and `data/raw/jobs.csv` (JSON and
JSONL are also supported), then run:

```powershell
python scripts/process_phase2.py --raw-dir data/raw --processed-dir data/processed
```

The pipeline writes `candidates.parquet`, `jobs.parquet`, and
`rejected.parquet`. Every row either validates against the canonical schema or is
quarantined with a documented reason.

## Phase 3 Parsing Pipeline

After Phase 2 has produced cleaned parquet files, run:

```powershell
python scripts/process_phase3.py --processed-dir data/processed
```

The parser writes `parsed_resumes.jsonl` and `parsed_jobs.jsonl`. Resume parsing
is rule-based by default; job parsing can use the Phase 1 `LLMProvider` but falls
back to deterministic heuristics so local tests do not require a running model.

## Docker

```powershell
Copy-Item config\.env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

Docker Compose starts the API, Qdrant, and Ollama. Claude support is optional
and is enabled by setting `LLM_PROVIDER=claude` plus `ANTHROPIC_API_KEY`.
