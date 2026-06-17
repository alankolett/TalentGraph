# TalentGraph Architecture

Phase 1 implements the foundation described in `structures plan.pdf`.

## Services

- FastAPI API: exposes `/health` and hosts later ranking workflows.
- Qdrant: vector database for dense and hybrid retrieval.
- Ollama: local LLM runtime, defaulting to `qwen3:8b`.
- Claude: optional remote LLM provider when `ANTHROPIC_API_KEY` is configured.
- Streamlit: placeholder UI container for later demo workflows.

## Core Interfaces

- `Settings`: central environment-driven configuration.
- `LLMProvider`: protocol with `generate(prompt: str) -> str`.
- `OllamaProvider`: local provider with actionable connection errors.
- `ClaudeProvider`: optional Anthropic provider.
- `get_llm_provider(name)`: provider factory with Claude-to-Ollama fallback when no API key exists.

