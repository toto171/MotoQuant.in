"""
tests/test_observability.py
===========================
Guards for the env-gated Sentry integration in ``motoquant.observability``.

The whole point of the observability layer is that it is **invisible** unless a
``SENTRY_DSN`` is supplied. These tests pin that contract:

  * ``init_sentry()`` is a silent no-op (returns ``False``, raises nothing) when
    ``SENTRY_DSN`` is unset -- the default for local dev and CI;
  * it is idempotent;
  * the env-parsing helpers degrade gracefully on malformed input;
  * importing ``motoquant.api`` (which calls ``init_sentry`` at module load)
    does not error and does not initialise Sentry when no DSN is present.

These run with zero network and without ``sentry-sdk`` having to do anything
real -- the no-DSN path returns before any ``sentry_sdk.init`` call.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

import motoquant.observability as obs


@pytest.fixture(autouse=True)
def _reset_observability(monkeypatch):
    """Each test starts from a clean, DSN-free observability module."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("SENTRY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SENTRY_TRACES_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    monkeypatch.delenv("SENTRY_SEND_PII", raising=False)
    # Reset the module-level "already initialised" latch so each test is
    # independent regardless of import order.
    obs._INITIALISED = False
    yield
    obs._INITIALISED = False


def test_init_sentry_noop_without_dsn():
    """No DSN -> returns False, raises nothing, initialises nothing."""
    assert obs.init_sentry() is False
    assert obs._INITIALISED is False


def test_init_sentry_noop_with_blank_dsn(monkeypatch):
    """A blank/whitespace DSN is treated as 'not set'."""
    monkeypatch.setenv("SENTRY_DSN", "   ")
    assert obs.init_sentry() is False
    assert obs._INITIALISED is False


def test_init_sentry_idempotent_without_dsn():
    """Calling it repeatedly without a DSN is harmless."""
    assert obs.init_sentry() is False
    assert obs.init_sentry() is False
    assert obs._INITIALISED is False


def test_init_sentry_already_initialised_short_circuits():
    """If the latch is set, init returns True immediately without touching env."""
    obs._INITIALISED = True
    assert obs.init_sentry() is True


def test_safe_float_defaults_and_parsing(monkeypatch):
    monkeypatch.delenv("X_RATE", raising=False)
    assert obs._safe_float("X_RATE", 0.05) == 0.05
    monkeypatch.setenv("X_RATE", "0.25")
    assert obs._safe_float("X_RATE", 0.05) == 0.25
    monkeypatch.setenv("X_RATE", "not-a-float")
    assert obs._safe_float("X_RATE", 0.05) == 0.05  # malformed -> default
    monkeypatch.setenv("X_RATE", "   ")
    assert obs._safe_float("X_RATE", 0.05) == 0.05  # blank -> default


def test_tag_app_adds_app_tag():
    event = {"tags": {"existing": "v"}}
    out = obs._tag_app(event, "motoquant-api")
    assert out["tags"]["app"] == "motoquant-api"
    assert out["tags"]["existing"] == "v"


def test_tag_app_handles_missing_or_non_dict_tags():
    # No tags key
    out = obs._tag_app({}, "motoquant-api")
    assert out["tags"]["app"] == "motoquant-api"
    # Non-dict tags (defensive path)
    out = obs._tag_app({"tags": "weird"}, "motoquant-api")
    assert out["tags"] == {"app": "motoquant-api"}


def test_importing_api_does_not_initialise_sentry_without_dsn():
    """The API module calls init_sentry() at import. Without a DSN that must be
    a no-op -- importing the API must never raise nor spin up Sentry."""
    obs._INITIALISED = False
    try:
        import motoquant.api  # noqa: F401
    except Exception as exc:  # pragma: no cover - import must not raise
        pytest.fail(f"Importing motoquant.api raised unexpectedly: {exc!r}")
    assert obs._INITIALISED is False


# ─────────────────────────────────────────────────────────────────────────
# Activation visibility (2026-07-17, re-implementation of PR #88's content):
# a successful init MUST land an exact marker line on STDOUT (Render surfaces
# stdout; log.info is invisible without a logging config), and a DSN with a
# missing sentry-sdk must say so. DSN-free runs stay completely silent.
# ─────────────────────────────────────────────────────────────────────────


class TestActivationVisibility:
    def test_no_dsn_stays_completely_silent(self, capsys):
        assert obs.init_sentry() is False
        assert obs.is_initialised() is False
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""

    def test_dsn_and_sdk_prints_exact_active_line(self, capsys, monkeypatch):
        pytest.importorskip("sentry_sdk")
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        monkeypatch.setenv("SENTRY_ENVIRONMENT", "unittest")
        monkeypatch.setenv("SENTRY_RELEASE", "motoquant-api@test")
        with patch("sentry_sdk.init") as mock_init:
            assert obs.init_sentry(app_name="motoquant-api") is True
        mock_init.assert_called_once()
        assert obs.is_initialised() is True
        out, _ = capsys.readouterr()
        assert out.strip() == (
            "[observability] Sentry active — "
            "environment=unittest release=motoquant-api@test"
        )

    def test_dsn_but_sdk_missing_prints_exact_not_active_line(
        self, capsys, monkeypatch
    ):
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        # None in sys.modules makes `import sentry_sdk` raise ImportError --
        # the production missing-package branch, without uninstalling anything.
        monkeypatch.setitem(sys.modules, "sentry_sdk", None)
        assert obs.init_sentry() is False
        assert obs.is_initialised() is False
        out, _ = capsys.readouterr()
        assert out.strip() == "[observability] Sentry NOT active — sentry-sdk missing"

    def test_active_line_fires_once_across_repeat_calls(self, capsys, monkeypatch):
        pytest.importorskip("sentry_sdk")
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        with patch("sentry_sdk.init") as mock_init:
            assert obs.init_sentry() is True
            assert obs.init_sentry() is True
        mock_init.assert_called_once()
        out, _ = capsys.readouterr()
        assert out.count("[observability] Sentry active") == 1

    def test_llm_sdk_auto_integrations_are_disabled(self, monkeypatch):
        """The Anthropic auto-integration would capture provider errors (and
        request data) before llm/client.py translates and redacts them, so
        init_sentry must disable it. The OpenAI one is disabled too when it
        can load at all (openai is no longer a dependency)."""
        pytest.importorskip("sentry_sdk")
        from sentry_sdk.integrations.anthropic import AnthropicIntegration

        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        with patch("sentry_sdk.init") as mock_init:
            assert obs.init_sentry() is True
        disabled = mock_init.call_args.kwargs.get("disabled_integrations")
        assert disabled, "init_sentry no longer passes disabled_integrations"
        disabled_types = {type(i) for i in disabled}
        assert AnthropicIntegration in disabled_types
        try:
            from sentry_sdk.integrations.openai import OpenAIIntegration
        except Exception:  # noqa: BLE001 - DidNotEnable without openai
            return
        assert OpenAIIntegration in disabled_types

    def test_init_survives_an_integration_that_cannot_load(self, monkeypatch):
        """Without the openai package, importing sentry's OpenAI integration
        raises DidNotEnable (not ImportError); init_sentry must still start."""
        pytest.importorskip("sentry_sdk")
        import sys
        import types

        from sentry_sdk.integrations import DidNotEnable

        broken = types.ModuleType("sentry_sdk.integrations.openai")

        def _raise(name):
            raise DidNotEnable("OpenAI not installed")

        broken.__getattr__ = _raise
        monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.openai", broken)
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        with patch("sentry_sdk.init") as mock_init:
            assert obs.init_sentry() is True
        assert mock_init.called


@pytest.fixture()
def client():
    try:
        from fastapi.testclient import TestClient

        from motoquant.api import app
    except ImportError:
        pytest.skip("fastapi not installed")
    return TestClient(app, raise_server_exceptions=False)


class TestSentryTestRoute:
    """GET /api/debug/sentry-test — 404 unless MOTOQUANT_SENTRY_SELFTEST is
    truthy; when enabled it raises RuntimeError (surfaced as 500 here) so the
    FastAPI Sentry integration reports a real event."""

    def test_404_by_default(self, client, monkeypatch):
        monkeypatch.delenv("MOTOQUANT_SENTRY_SELFTEST", raising=False)
        res = client.get("/api/debug/sentry-test")
        assert res.status_code == 404

    def test_404_on_falsy_value(self, client, monkeypatch):
        monkeypatch.setenv("MOTOQUANT_SENTRY_SELFTEST", "0")
        res = client.get("/api/debug/sentry-test")
        assert res.status_code == 404

    def test_500_when_enabled(self, client, monkeypatch):
        monkeypatch.setenv("MOTOQUANT_SENTRY_SELFTEST", "1")
        res = client.get("/api/debug/sentry-test")
        assert res.status_code == 500


# ── Key scrubbing (visitor Anthropic keys must never reach Sentry) ─────────


def _key(tag: str = "k") -> str:
    # Built at runtime: the secret scan flags a literal sk-ant- + 32 chars.
    return "sk-ant-" + "api03-" + tag * 40


class TestScrubEvent:
    def test_credential_headers_are_removed(self):
        k = _key()
        event = {
            "request": {
                "headers": {
                    "X-Anthropic-Key": k,
                    "x_anthropic_key": k,
                    "Authorization": "Bearer abc",
                    "X-Api-Key": "abc",
                    "Content-Type": "application/json",
                }
            }
        }
        out = obs.scrub_event(event)
        assert out["request"]["headers"] == {"Content-Type": "application/json"}

    def test_every_key_substring_is_redacted(self):
        k1, k2 = _key("a"), _key("b")
        event = {
            "message": f"failed with {k1}",
            "exception": {
                "values": [
                    {
                        "value": f"AuthenticationError: {k2}",
                        "stacktrace": {
                            "frames": [{"vars": {"visitor_key": f"'{k1}'"}}]
                        },
                    }
                ]
            },
            "breadcrumbs": {"values": [{"message": f"key={k2}"}]},
            "request": {"data": {"nested": [k1, ("x", k2)]}},
            "extra": {"headers": [["x-anthropic-key", "anything"], ["accept", "*/*"]]},
        }
        out = obs.scrub_event(event)
        dumped = repr(out)
        assert k1 not in dumped and k2 not in dumped
        assert "sk-ant-" not in dumped
        assert out["extra"]["headers"][0] == ["x-anthropic-key", "[redacted]"]
        assert out["extra"]["headers"][1] == ["accept", "*/*"]

    def test_before_send_scrubs_and_tags_even_with_send_pii(self, monkeypatch):
        pytest.importorskip("sentry_sdk")
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        monkeypatch.setenv("SENTRY_SEND_PII", "true")
        with patch("sentry_sdk.init") as mock_init:
            assert obs.init_sentry() is True
        kwargs = mock_init.call_args.kwargs
        assert kwargs["send_default_pii"] is True
        k = _key()
        event = {
            "message": k,
            "request": {"headers": {"x-anthropic-key": k, "Accept": "*/*"}},
        }
        sent = kwargs["before_send"](event, {})
        assert k not in repr(sent)
        assert "x-anthropic-key" not in sent["request"]["headers"]
        assert sent["tags"]["app"] == "motoquant-api"
        tx = kwargs["before_send_transaction"](
            {"request": {"headers": {"Authorization": "Bearer x"}}, "message": k}, {}
        )
        assert tx["request"]["headers"] == {}
        assert k not in repr(tx)
