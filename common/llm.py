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


class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        import json
        import urllib.request
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(f"Groq API call failed: {exc}") from exc


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        import json
        import urllib.request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc


def get_llm_provider(name: str | None = None, settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider_name = (name or settings.llm_provider).lower()

    if provider_name == "claude" and settings.has_anthropic_credentials:
        return ClaudeProvider(
            api_key=settings.anthropic_api_key or "",
            model=settings.anthropic_model,
        )

    if provider_name == "groq" and settings.has_groq_credentials:
        return GroqProvider(
            api_key=settings.groq_api_key or "",
            model=settings.groq_model,
        )

    if provider_name == "gemini" and settings.has_gemini_credentials:
        return GeminiProvider(
            api_key=settings.gemini_api_key or "",
            model=settings.gemini_model,
        )

    # Missing credentials fallback to Ollama
    if provider_name in {"claude", "groq", "gemini"}:
        provider_name = "ollama"

    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    raise ValueError(f"Unsupported LLM provider: {provider_name}")
