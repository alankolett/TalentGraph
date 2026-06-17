from pathlib import Path

from common.settings import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "TalentGraph"
    assert settings.llm_provider == "ollama"
    assert settings.sqlite_path == Path("data/talentgraph.sqlite3")


def test_settings_can_load_env_file(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=TalentGraphTest\nLLM_PROVIDER=claude\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    settings = Settings()

    assert settings.app_name == "TalentGraphTest"
    assert settings.llm_provider == "claude"
