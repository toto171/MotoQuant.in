"""The assistant-to-model mapping is fixed on the server.

The client never accepts a raw model id: the API takes "mechanic" or
"doctor", and environment variables from the old multi-provider layer
(ANTHROPIC_MODEL, LLM_PROVIDER) no longer change which model answers.
"""

import pytest

from motoquant.llm.client import ASSISTANTS, DEFAULT_ASSISTANT, LLMClient


@pytest.fixture
def server_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)


def test_mechanic_is_the_default_and_runs_sonnet(server_env):
    assert DEFAULT_ASSISTANT == "mechanic"
    client = LLMClient()
    assert client.assistant == "mechanic"
    assert client.model == "claude-sonnet-5-5"
    assert client.effort == "medium"


def test_doctor_runs_opus(server_env):
    client = LLMClient("doctor")
    assert client.model == "claude-opus-5-5"
    assert client.effort == "medium"


def test_mapping_is_exactly_two_assistants():
    assert {a: s.model for a, s in ASSISTANTS.items()} == {
        "doctor": "claude-opus-5-5",
        "mechanic": "claude-sonnet-5-5",
    }
    assert ASSISTANTS["doctor"].cap_units == 2
    assert ASSISTANTS["mechanic"].cap_units == 1


def test_model_env_vars_do_not_override(server_env, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    assert LLMClient().model == "claude-sonnet-5-5"
    assert LLMClient("doctor").model == "claude-opus-5-5"


def test_unknown_assistant_or_raw_model_id_is_refused():
    with pytest.raises(ValueError):
        LLMClient("claude-opus-5-5")
    with pytest.raises(ValueError):
        LLMClient("groq")
