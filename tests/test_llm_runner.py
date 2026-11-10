"""
Tests for motoquant.llm.runner (run_chat_pipeline) and POST /api/chat.

The runner exercises real DB + real physics, mocking ONLY the LLM client.
The API endpoint test uses FastAPI TestClient with dependency_overrides
to inject the mock client.

Run with:  python -m pytest tests/test_llm_runner.py -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from typing import Any
from unittest.mock import MagicMock

# Point the API at an isolated DB BEFORE importing api / runner.
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="mq_chat_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.database.seed import seed_all  # noqa: E402
from motoquant.llm import (  # noqa: E402
    ChatResult,
    LLMClient,
    run_chat_pipeline,
)


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run.

    The import-time override above executes at COLLECTION time, so by the
    time these tests actually run an alphabetically-earlier module
    (test_jobs_api, test_api…) has pointed MOTOQUANT_DB at ITS tmp copy and
    then RESTORED the session value in its tearDownModule — leaving this
    module's ``/api/chat`` calls reading the tracked motoquant.db.

    That leak is not hypothetical: while classic-mode chat sims were metered
    (2026-07-25 → 2026-10-23), ``pytest tests/test_api.py
    tests/test_llm_runner.py`` wrote real sim_usage rows into the shipped
    catalog. The meter is gone, but any future route-level writer would leak
    the same way. Same class of leak as commit e873308; same fix as
    tests/test_jobs_api.py.
    """
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    api_mod = sys.modules.get("motoquant.api")
    if api_mod is not None:
        api_mod._db_conn = None
        api_mod._db_facade = None


def tearDownModule():
    """Close handles, drop the tmp DB, restore the env for later modules."""
    global _SHARED_DB
    if _SHARED_DB is not None:
        try:
            _SHARED_DB.close()
        except Exception:  # noqa: BLE001
            pass
        _SHARED_DB = None
    api_mod = sys.modules.get("motoquant.api")
    if api_mod is not None:
        if getattr(api_mod, "_db_conn", None) is not None:
            try:
                api_mod._db_conn.close()
            except Exception:  # noqa: BLE001
                pass
        api_mod._db_conn = None
        api_mod._db_facade = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


# ───────────────────────────────────────────────────────────────────
# Shared fixtures
# ───────────────────────────────────────────────────────────────────


_SHARED_DB: MotoQuantDB | None = None


def _get_shared_db() -> MotoQuantDB:
    """Lazy seed -- spinning up the full catalog takes ~5 s, so do it once."""
    global _SHARED_DB
    if _SHARED_DB is not None:
        return _SHARED_DB
    db = MotoQuantDB(_TMP_DB_PATH)
    db.initialize()
    seed_all(db)
    _SHARED_DB = db
    return db


def _make_mock_client(
    parsed_payload: dict[str, Any] | None = None,
    summary_text: str = "Stub summary text.",
) -> tuple[LLMClient, list[dict[str, Any]]]:
    """LLMClient with scripted tool + text responses; calls is the audit log."""
    calls: list[dict[str, Any]] = []
    payload = parsed_payload or {
        "bike_name": "Suzuki GSX-R 1000",
        "optimization_goal": "minimize_et",
    }

    def fake(kind: str, kwargs: dict[str, Any]):
        calls.append({"kind": kind, **kwargs})
        if kind == "tool":
            return payload
        if kind == "text":
            return summary_text
        raise AssertionError(f"unexpected kind: {kind}")

    return LLMClient(_call_override=fake), calls


# ───────────────────────────────────────────────────────────────────
# run_chat_pipeline -- happy + error paths
# ───────────────────────────────────────────────────────────────────


class TestRunChatPipelineSuccess(unittest.TestCase):
    """Exercises real DB + real physics. Slowest test class -- ~3 s."""

    @classmethod
    def setUpClass(cls):
        cls.db = _get_shared_db()

    def test_resolves_bike_runs_sim_returns_summary(self):
        client, calls = _make_mock_client(
            parsed_payload={
                "bike_name": "GSX-R 1000",
                "optimization_goal": "minimize_et",
            },
            summary_text="K5 ran cleanly.",
        )
        result = run_chat_pipeline("how fast is the K5", self.db, client=client)
        self.assertIsInstance(result, ChatResult)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.bike_id)
        self.assertIsNotNone(result.sim_result)
        # Key was renamed to et_quarter_s to match frontend contract
        self.assertIn("et_quarter_s", result.sim_result)
        self.assertGreater(result.sim_result["et_quarter_s"], 5.0)
        self.assertLess(result.sim_result["et_quarter_s"], 30.0)
        self.assertEqual(result.summary, "K5 ran cleanly.")
        # Both LLM calls happened: tool (parse) + text (summarize)
        kinds = [c["kind"] for c in calls]
        self.assertEqual(kinds, ["tool", "text"])

    def test_run_summary_false_skips_summarization(self):
        client, calls = _make_mock_client(
            parsed_payload={
                "bike_name": "Hayabusa",
                "optimization_goal": "minimize_et",
            }
        )
        result = run_chat_pipeline(
            "Hayabusa quarter mile", self.db, client=client, run_summary=False
        )
        self.assertIsNone(result.error)
        self.assertIsNone(result.summary)
        self.assertEqual([c["kind"] for c in calls], ["tool"])  # no text call

    def test_env_overrides_passed_through(self):
        client, _ = _make_mock_client(
            parsed_payload={
                "bike_name": "Hayabusa",
                "ambient_temp_c": 40.0,
                "humidity_pct": 80.0,
                "headwind_kmh": 12.0,
                "optimization_goal": "minimize_et",
            },
            summary_text="hot and humid",
        )
        result = run_chat_pipeline("...", self.db, client=client)
        self.assertIsNone(result.error)
        # We can't introspect the config from outside the runner cleanly,
        # but at minimum the run shouldn't crash and ET should be sensible.
        self.assertGreater(result.sim_result["et_quarter_s"], 8.0)


class TestRunChatPipelineErrors(unittest.TestCase):
    """Mocked DB -- no physics involved. Fast path."""

    def test_llm_not_configured_returns_typed_error(self):
        from motoquant.llm.client import LLMNotConfiguredError

        def fake(kind, kwargs):
            raise LLMNotConfiguredError("no API key here")

        client = LLMClient(_call_override=fake)
        db = MagicMock()
        result = run_chat_pipeline("hi", db, client=client)
        self.assertEqual(result.error, "llm_not_configured")
        self.assertIn("no API key", result.error_detail)
        self.assertIsNone(result.sim_result)

    def test_parse_failed_returns_typed_error(self):
        def fake(kind, kwargs):
            raise RuntimeError("Claude refused")

        client = LLMClient(_call_override=fake)
        db = MagicMock()
        result = run_chat_pipeline("hi", db, client=client)
        self.assertEqual(result.error, "parse_failed")
        self.assertIn("RuntimeError", result.error_detail)

    def test_bike_not_found_returns_suggestions(self):
        client, _ = _make_mock_client(
            parsed_payload={
                "bike_name": "Some Mythical Bike",
                "optimization_goal": "minimize_et",
            }
        )
        db = MagicMock()
        # First search (full name) returns nothing; subsequent token searches
        # also return nothing -- the runner should give up cleanly.
        db.bikes.search.return_value = []
        db.venues.get_by_name.return_value = None

        result = run_chat_pipeline("...", db, client=client)
        self.assertEqual(result.error, "bike_not_found")
        self.assertEqual(result.bike_suggestions, [])
        self.assertIsNone(result.sim_result)

    def test_bike_not_found_returns_top_n_suggestions(self):
        client, _ = _make_mock_client(
            parsed_payload={
                "bike_name": "Nonexistent Yamaha 999",
                "optimization_goal": "minimize_et",
            }
        )
        db = MagicMock()

        yamaha_rows = [
            {
                "id": 1,
                "manufacturer_name": "Yamaha",
                "model_name": "YZF-R1",
                "year_from": 2009,
                "year_to": 2014,
            },
            {
                "id": 2,
                "manufacturer_name": "Yamaha",
                "model_name": "YZF-R6",
                "year_from": 2008,
                "year_to": None,
            },
        ]

        def search_side_effect(*args, **kwargs):
            blob = " ".join(
                str(v).lower() for v in (list(args) + list(kwargs.values())) if v
            )
            if "nonexistent" in blob and "yamaha" not in blob:
                return []
            if "yamaha" in blob:
                return yamaha_rows
            return []

        db.bikes.search.side_effect = search_side_effect
        db.venues.get_by_name.return_value = None

        result = run_chat_pipeline("...", db, client=client)
        self.assertEqual(result.error, "bike_not_found")
        self.assertGreaterEqual(len(result.bike_suggestions), 1)
        self.assertEqual(result.bike_suggestions[0]["manufacturer"], "Yamaha")


# ───────────────────────────────────────────────────────────────────
# POST /api/chat -- FastAPI integration
# ───────────────────────────────────────────────────────────────────


class TestChatEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure the seeded DB is available for the API to read.
        _get_shared_db()
        # NOTE: storing get_llm_client as cls.get_llm_client would turn it
        # into a bound method on instance access, breaking FastAPI's
        # dependency-key lookup. Hold the api MODULE instead and read
        # `self.api.get_llm_client` -- that returns the unbound function.
        from fastapi.testclient import TestClient

        import motoquant.api as _api_module

        cls.api = _api_module
        cls.client = TestClient(_api_module.app)

    def setUp(self):
        # Reset overrides between tests
        self.api.app.dependency_overrides.clear()

    def _override_llm(self, parsed_payload: dict[str, Any], summary_text: str = "stub"):
        """Plug a mock LLMClient into the get_llm_client dependency."""
        cli, _ = _make_mock_client(parsed_payload, summary_text)
        self.api.app.dependency_overrides[self.api.get_llm_client] = lambda: cli

    def test_happy_path_returns_200_with_sim_result(self):
        self._override_llm(
            {
                "bike_name": "Hayabusa",
                "optimization_goal": "minimize_et",
            },
            summary_text="Hayabusa ran cleanly.",
        )
        r = self.client.post(
            "/api/chat", json={"query": "how fast is my Hayabusa", "mode": "classic"}
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIsNone(body["error"])
        self.assertIsNotNone(body["bike_id"])
        self.assertIsNotNone(body["sim_result"])
        # Key was renamed to et_quarter_s to match frontend contract
        self.assertIn("et_quarter_s", body["sim_result"])
        self.assertEqual(body["summary"], "Hayabusa ran cleanly.")

    def test_run_summary_false_omits_summary(self):
        self._override_llm(
            {"bike_name": "Hayabusa", "optimization_goal": "minimize_et"}
        )
        r = self.client.post(
            "/api/chat",
            json={"query": "Hayabusa", "run_summary": False, "mode": "classic"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIsNone(body["summary"])
        self.assertIsNotNone(body["sim_result"])

    def test_bike_not_found_returns_200_with_error_field(self):
        self._override_llm(
            {
                # Use a string that no DB row substring-matches:
                # avoids tokens like "bike", "exist", etc. that fuzzy-hit.
                "bike_name": "Zzqwxv-9999",
                "optimization_goal": "minimize_et",
            }
        )
        r = self.client.post(
            "/api/chat", json={"query": "fake bike query", "mode": "classic"}
        )
        # Recoverable error -- still HTTP 200 so frontend can render suggestions
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["error"], "bike_not_found")
        self.assertIsNone(body["sim_result"])
        # bike_suggestions should be a list (possibly empty)
        self.assertIsInstance(body["bike_suggestions"], list)

    def test_llm_not_configured_returns_200_with_error(self):
        from motoquant.llm.client import LLMNotConfiguredError

        def fake(kind, kwargs):
            raise LLMNotConfiguredError("ANTHROPIC_API_KEY missing")

        self.api.app.dependency_overrides[self.api.get_llm_client] = lambda: LLMClient(
            _call_override=fake
        )
        r = self.client.post("/api/chat", json={"query": "anything", "mode": "classic"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["error"], "llm_not_configured")
        self.assertIsNone(body["sim_result"])
        self.assertIn("ANTHROPIC_API_KEY", body["error_detail"])

    def test_empty_query_rejected_by_pydantic(self):
        r = self.client.post("/api/chat", json={"query": ""})
        self.assertEqual(r.status_code, 422)  # pydantic validation error

    def test_oversize_query_rejected_by_pydantic(self):
        r = self.client.post("/api/chat", json={"query": "x" * 5000})
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
