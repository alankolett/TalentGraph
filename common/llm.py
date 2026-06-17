from typing import Protocol

from common.settings import Settings, get_settings


class LLMProvider(Protocol):
    """Minimal text-generation interface used by later ranking phases."""

    def generate(self, prompt: str) -> str:
        """Generate a text response for a prompt."""


class OllamaProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            import ollama
        except ImportError as exc:
            raise RuntimeError("Install the 'ollama' package to use OllamaProvider.") from exc

        client = ollama.Client(host=self.base_url)
        try:
            response = client.generate(model=self.model, prompt=prompt)
        except Exception as exc:
            raise RuntimeError(
                "Ollama is not reachable. Start it with `docker compose up ollama` "
                f"or check OLLAMA_BASE_URL={self.base_url}."
            ) from exc

        text = response.get("response")
        if not isinstance(text, str):
            raise RuntimeError("Ollama returned an unexpected response payload.")
        return text


class ClaudeProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install the 'anthropic' package to use ClaudeProvider.") from exc

        client = Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in message.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts).strip()


def get_llm_provider(name: str | None = None, settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider_name = (name or settings.llm_provider).lower()

    if provider_name == "claude" and settings.has_anthropic_credentials:
        return ClaudeProvider(
            api_key=settings.anthropic_api_key or "",
            model=settings.anthropic_model,
        )

    if provider_name == "claude" and not settings.has_anthropic_credentials:
        provider_name = "ollama"

    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    raise ValueError(f"Unsupported LLM provider: {provider_name}")
