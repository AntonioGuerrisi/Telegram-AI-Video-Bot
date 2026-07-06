import os
import pytest
from bot.config import load_settings, Settings


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("OPENROUTER_PROMPT_KEY", "test_prompt_key")
    settings = load_settings()
    assert settings.bot_token == "test_token"
    assert settings.openrouter_api_key == "test_key"
    assert settings.openrouter_prompt_key == "test_prompt_key"
    assert settings.log_level == "INFO"


def test_load_settings_missing_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    empty_env = tmp_path / ".empty_env"
    empty_env.write_text("")
    with pytest.raises(ValueError):
        load_settings(str(empty_env))
