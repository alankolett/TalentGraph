from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TalentGraph"
    environment: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    llm_provider: Literal["ollama", "claude", "groq", "gemini"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    anthropic_api_key: str | None = Field(default=None, repr=False)
    anthropic_model: str = "claude-3-5-haiku-latest"

    groq_api_key: str | None = Field(default=None, repr=False)
    groq_model: str = "llama-3.1-8b-instant"

    gemini_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-1.5-flash"

    qdrant_url: str = "http://localhost:6333"
    sqlite_path: Path = Path("data/talentgraph.sqlite3")

    @property
    def has_anthropic_credentials(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_groq_credentials(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_gemini_credentials(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
