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
python scripts/seed_sample_data.py --raw-dir data/raw
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

## Phase 4 Knowledge Graph

After Phase 3 has produced parsed JSONL files, run:

```powershell
python scripts/process_phase4.py --processed-dir data/processed --graph-dir data/knowledge_graph
```

The graph builder writes `skill_ontology.json` and `candidate_kg.gpickle`.
It normalizes skill synonyms/typos, adds candidate skill and career-history
edges, adds job skill-requirement edges, and supports skill-distance lookups.

## Phase 5 Embedding Pipeline

After Phase 3 has produced parsed JSONL files, run:

```powershell
python scripts/process_phase5.py --processed-dir data/processed --embeddings-dir data/embeddings
```

By default this uses a deterministic local hashing backend for fast offline
verification. Use `--backend sentence-transformers` for real model embeddings.
The pipeline writes candidate/job embedding parquet files and upserts candidate
vectors into a Qdrant-shaped index interface.

## Phase 6 Hybrid Retrieval Pipeline

After Phase 5 has produced candidate embedding files and indexed them, run:

```powershell
python scripts/process_phase6.py --processed-dir data/processed --embeddings-dir data/embeddings
```

This merges dense vector similarity search, BM25 keyword matching, and hard metadata masks (location, seniority, must-have skills) using Reciprocal Rank Fusion (RRF). It outputs the ranked shortlist of candidate matches for each job description.

## Phase 7 Behavioral Signal Engineering

After Phase 2 has cleaned and validated the datasets, run:

```powershell
python scripts/process_phase7.py --processed-dir data/processed
```

This extracts behavioral profiles for each candidate (activity recency time decay, contribution frequency, skills learning velocity, open source breadth) and normalizes the scores relative to the population. The output is written to `data/processed/behavioral_profiles.jsonl`.

## Docker

```powershell
Copy-Item config\.env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

Docker Compose starts the API, Qdrant, and Ollama. Claude support is optional
and is enabled by setting `LLM_PROVIDER=claude` plus `ANTHROPIC_API_KEY`.
