from common.llm import ClaudeProvider, OllamaProvider, get_llm_provider
from common.settings import Settings


def test_provider_factory_returns_ollama_by_default() -> None:
    settings = Settings(llm_provider="ollama")

    provider = get_llm_provider(settings=settings)

    assert isinstance(provider, OllamaProvider)


def test_provider_factory_returns_claude_when_key_exists() -> None:
    settings = Settings(llm_provider="claude", anthropic_api_key="test-key")

    provider = get_llm_provider(settings=settings)

    assert isinstance(provider, ClaudeProvider)


def test_provider_factory_falls_back_to_ollama_without_claude_key() -> None:
    settings = Settings(llm_provider="claude", anthropic_api_key=None)

    provider = get_llm_provider(settings=settings)

    assert isinstance(provider, OllamaProvider)
