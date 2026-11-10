"""
Chat cost fuses (open-source build: no tiers, no quota).

The chat agent can reach the expensive tools (build optimizer, ECU autotune,
outlaw pipeline), so anonymous callers are bounded by:

* the executor's per-message budgets (sims / heavy ops per turn);
* a per-IP heavy-op gate (``heavy_gate``) sharing the optimize/autotune rate
  bucket, so the chatbot cannot out-run the direct routes;
* a per-IP rate limit on every chat route, with a much tighter bucket for
  mode="classic" (which runs up to 25 RK4 sims per request, un-budgeted).

Only the LLM is scripted (the ``_call_override`` seam); DB and physics are
real. MOTOQUANT_DB points at a copy of the shipped catalog so nothing here can
touch the tracked motoquant.db.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(prefix="mq_chat_fuse_", suffix=".db", delete=False)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
_TMP_DB_PATH = _tmp.name
_PRIOR_MOTOQUANT_DB: str | None = None

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.llm.agent import (  # noqa: E402
    HEAVY_OP_BUDGET,
    HEAVY_OP_SIM_COST,
    run_agent_chat,
)
from motoquant.llm.client import LLMClient  # noqa: E402

_SHARED_DB: MotoQuantDB | None = None


def setUpModule():
    global _PRIOR_MOTOQUANT_DB
    _PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    api_mod = sys.modules.get("motoquant.api")
    if api_mod is not None:
        api_mod._db_conn = None
        api_mod._db_facade = None


def tearDownModule():
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
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass


def _get_db() -> MotoQuantDB:
    global _SHARED_DB
    if _SHARED_DB is None:
        _SHARED_DB = MotoQuantDB(_TMP_DB_PATH)
    return _SHARED_DB


def _agent_client(script):
    """LLMClient whose call_tools follows `script` (see tests/test_agent.py)."""
    state = {"i": 0, "kwargs_log": []}

    def override(kind, kwargs):
        assert kind == "tools", f"unexpected kind {kind}"
        state["kwargs_log"].append(kwargs)
        i = min(state["i"], len(script) - 1)
        state["i"] += 1
        entry = script[i]
        if isinstance(entry, str):
            return entry
        return {
            "tool_calls": [
                {"id": f"c{i}_{j}", "name": name, "arguments": args}
                for j, (name, args) in enumerate(entry)
            ]
        }

    return LLMClient(_call_override=override), state


def _classic_client(parsed: dict[str, Any], summary: str = "stub"):
    """LLMClient for the classic pipeline: tool call = parse, text = summary."""

    def fake(kind: str, kwargs: dict[str, Any]):
        if kind == "tool":
            return parsed
        return summary

    return LLMClient(_call_override=fake)


def _tool_payload(state, tool_name):
    """The payload the model saw for `tool_name` (tool results are data)."""
    for kwargs in reversed(state["kwargs_log"]):
        for m in reversed(kwargs["messages"]):
            if m.get("role") == "tool" and m.get("name") == tool_name:
                return json.loads(m["content"])
    return None


# ───────────────────────────────────────────────────────────────────
# 1. Agent: heavy ops are open to anonymous callers but fused
# ───────────────────────────────────────────────────────────────────


class TestAgentHeavyOps(unittest.TestCase):
    def test_optimizer_is_open_with_no_gate(self):
        """No tier: an anonymous library caller reaches the optimizer tool
        (bogus bike id -> a data error, never an upgrade refusal)."""
        client, state = _agent_client([[("optimize_build", {"bike_id": 999999})], "x"])
        res = run_agent_chat("go", _get_db(), client=client)
        payload = _tool_payload(state, "optimize_build")
        self.assertNotIn("upgrade", json.dumps(payload).lower())
        self.assertIsNone(res.error)

    def test_heavy_gate_refuses_before_any_work(self):
        client, state = _agent_client([[("autotune_setup", {"bike_id": 11})], "x"])
        res = run_agent_chat("tune", _get_db(), client=client, heavy_gate=lambda: False)
        payload = _tool_payload(state, "autotune_setup")
        self.assertIn("too many", payload.get("error", ""))
        self.assertEqual(res.sims_run, 0)

    def test_heavy_gate_is_consulted_once_per_heavy_op(self):
        calls: list[int] = []
        client, _ = _agent_client([[("autotune_setup", {"bike_id": 999999})], "x"])
        run_agent_chat(
            "tune",
            _get_db(),
            client=client,
            heavy_gate=lambda: calls.append(1) or True,
        )
        self.assertEqual(len(calls), 1)

    def test_free_tools_never_consult_the_heavy_gate(self):
        calls: list[int] = []
        client, _ = _agent_client([[("run_simulation", {"bike_id": 11})], "x"])
        res = run_agent_chat(
            "go",
            _get_db(),
            client=client,
            heavy_gate=lambda: calls.append(1) or False,
        )
        self.assertEqual(calls, [])
        self.assertEqual(res.sims_run, 1)

    def test_heavy_op_counts_its_nominal_sim_cost(self):
        self.assertGreater(HEAVY_OP_SIM_COST, 1)
        client, _ = _agent_client([[("autotune_setup", {"bike_id": 999999})], "x"])
        res = run_agent_chat("tune", _get_db(), client=client)
        self.assertIn(res.sims_run, (0, HEAVY_OP_SIM_COST))

    def test_per_message_heavy_budget_still_caps_a_turn(self):
        calls = [("autotune_setup", {"bike_id": 999999})] * (HEAVY_OP_BUDGET + 2)
        client, state = _agent_client([calls, "x"])
        run_agent_chat("tune", _get_db(), client=client)
        results = [
            m
            for m in state["kwargs_log"][-1]["messages"]
            if m.get("role") == "tool" and m.get("name") == "autotune_setup"
        ]
        errors = [json.loads(m["content"]).get("error", "") for m in results]
        self.assertTrue(any("budget exhausted" in e for e in errors), errors)


# ───────────────────────────────────────────────────────────────────
# 2. HTTP routes
# ───────────────────────────────────────────────────────────────────


class TestChatRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            import motoquant.api as api_mod

            os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
            api_mod._db_conn = None
            api_mod._db_facade = None
            cls.api_mod = api_mod
            cls.app = api_mod.app
            cls.client = TestClient(api_mod.app)
        except Exception:  # noqa: BLE001
            cls.client = None

    def setUp(self):
        if self.client is None:
            self.skipTest("fastapi not installed")
        from motoquant import ratelimit

        ratelimit.reset()

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _set_client(self, llm):
        from motoquant.api import get_llm_client

        self.app.dependency_overrides[get_llm_client] = lambda: llm

    def test_anonymous_chat_may_run_the_optimizer_tool(self):
        llm, _ = _agent_client([[("optimize_build", {"bike_id": 999999})], "relayed"])
        self._set_client(llm)
        r = self.client.post("/api/chat", json={"query": "build me one"})
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(r.json()["tool_trace"][0]["error"], "upgrade_required")

    def test_job_chat_works_anonymously(self):
        import time

        llm, _ = _agent_client([[("run_simulation", {"bike_id": 11})], "done"])
        self._set_client(llm)
        r = self.client.post("/api/jobs/chat", json={"query": "sim it"})
        self.assertEqual(r.status_code, 202)
        jid = r.json()["job_id"]
        for _ in range(200):
            time.sleep(0.05)
            jr = self.client.get(f"/api/jobs/{jid}").json()
            if jr["status"] in ("done", "error", "cancelled"):
                break
        self.assertEqual(jr["status"], "done")

    def test_chat_heavy_ops_share_the_optimize_bucket(self):
        """Chat's heavy tools draw from the same per-IP bucket as the direct
        optimize/autotune routes (6/60s): the 7th is refused."""
        from motoquant import ratelimit

        for _ in range(6):
            allowed, _ = ratelimit.check("optimize:testclient", 6, 60.0)
            self.assertTrue(allowed)
        llm, _ = _agent_client([[("autotune_setup", {"bike_id": 999999})], "x"])
        self._set_client(llm)
        r = self.client.post("/api/chat", json={"query": "tune"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("too many", r.json()["tool_trace"][0]["error"])

    def test_classic_chat_has_its_own_tight_per_ip_limit(self):
        self._set_client(_classic_client({"bike_name": "Hayabusa"}))
        body = {"query": "how fast is a busa", "mode": "classic", "run_summary": False}
        statuses = [
            self.client.post("/api/chat", json=body).status_code for _ in range(6)
        ]
        self.assertEqual(statuses[:4], [200] * 4, statuses)
        self.assertEqual(statuses[4:], [429, 429], statuses)

    def test_agent_chat_is_not_subject_to_the_classic_bucket(self):
        llm, _ = _agent_client([[("run_simulation", {"bike_id": 11})], "done"])
        self._set_client(llm)
        statuses = [
            self.client.post("/api/chat", json={"query": "sim it"}).status_code
            for _ in range(6)
        ]
        self.assertEqual(statuses, [200] * 6)

    def test_classic_chat_runs_unmetered_sim(self):
        self._set_client(_classic_client({"bike_name": "Hayabusa"}))
        r = self.client.post(
            "/api/chat",
            json={
                "query": "how fast is a busa",
                "mode": "classic",
                "run_summary": False,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIsNone(r.json()["error"], r.text)
        self.assertIsNotNone(r.json()["sim_result"])


if __name__ == "__main__":
    unittest.main()
