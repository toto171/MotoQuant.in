"""The Anthropic provider honours ANTHROPIC_MODEL, like Gemini/Groq do."""

import pytest

from motoquant.llm.client import _PROVIDERS, LLMClient


@pytest.fixture
def anthropic_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)


def test_default_model_is_current(anthropic_env):
    client = LLMClient()
    assert client._model == _PROVIDERS["anthropic"]["model"]
    assert client._model != "claude-sonnet-4-6"


def test_anthropic_model_env_override(anthropic_env, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    assert LLMClient()._model == "claude-haiku-5-5"
