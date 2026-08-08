"""
Chat tier-gating + chat sim metering (2026-07-25 audit §3.5).

Two defects, both invisible today and both live the moment the operator flips
``MOTOQUANT_BILLING_ENFORCE``:

1. **The pro-gated surfaces were fully exposed through the chat agent.** Build
   Optimizer, ECU Autotune and the Outlaw pipeline each sit behind
   ``require_tier("pro")`` on their own routes, but the agent can invoke all
   three and ``/api/chat`` had no tier gate at all — so after the launch flip
   ``POST /api/optimize/build`` would 401 while *asking the chatbot for the
   same thing* still worked. Settled decision: the executor inherits the
   caller's tier.

2. **Chat sim metering covered only agent-mode single sims.**
   ``docs/CHAT_AGENT.md`` claimed chat sims were metered, but the meter fired
   in exactly one place. Classic mode — client-selectable — could burn 25 full
   RK4 sims per request unmetered, and agent heavy ops (tens of sims apiece)
   likewise.

Both halves are pinned in **both billing modes**. The inert-during-beta half
matters as much as the enforcing half: that is what ships today, and a gate
that quietly closed on anonymous beta users would be a live outage.

Only the LLM is scripted (the ``_call_override`` seam); DB and physics are
real. MOTOQUANT_DB points at a copy of the shipped catalog — the metered paths
write ``sim_usage`` rows and must never touch the tracked motoquant.db.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from typing import Any

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(prefix="mq_chat_gate_", suffix=".db", delete=False)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
_TMP_DB_PATH = _tmp.name
_PRIOR_MOTOQUANT_DB: str | None = None

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.llm.agent import (  # noqa: E402
    HEAVY_OP_SIM_COST,
    OUTLAW_SIM_COST,
    PRO_TOOLS,
    AgentChatResult,
    AgentContext,
    _system_prompt,
    pro_tools_locked,
    run_agent_chat,
)
from motoquant.llm.client import LLMClient  # noqa: E402
from motoquant.llm.runner import run_chat_pipeline  # noqa: E402

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


class _BillingMode:
    """Context manager flipping motoquant.auth.BILLING_ENFORCE.

    The agent reads the flag through the module at call time, which is the
    documented test seam (see motoquant/auth.py).
    """

    def __init__(self, enforce: bool):
        self.enforce = enforce
        self._prior = None

    def __enter__(self):
        from motoquant import auth

        self._prior = auth.BILLING_ENFORCE
        auth.BILLING_ENFORCE = self.enforce
        return self

    def __exit__(self, *exc):
        from motoquant import auth

        auth.BILLING_ENFORCE = self._prior
        return False


def _usage_total() -> int:
    conn = sqlite3.connect(_TMP_DB_PATH)
    try:
        row = conn.execute("SELECT COALESCE(SUM(count), 0) FROM sim_usage").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


def _tool_payload(state, tool_name):
    """The payload the model saw for `tool_name` (tool results are data)."""
    for kwargs in reversed(state["kwargs_log"]):
        for m in reversed(kwargs["messages"]):
            if m.get("role") == "tool" and m.get("name") == tool_name:
                return json.loads(m["content"])
    return None


# ───────────────────────────────────────────────────────────────────
# 1. The tier gate itself
# ───────────────────────────────────────────────────────────────────


class TestProToolGate(unittest.TestCase):
    """Bogus bike ids on purpose: the gate must fire BEFORE the optimizer
    does any work, so these run in milliseconds and a refusal that never
    reaches the physics is exactly what we are asserting."""

    def _run(self, tool, args, tier):
        client, state = _agent_client([[(tool, args)], "done"])
        res = run_agent_chat("go", _get_db(), client=client, tier=tier)
        return res, _tool_payload(state, tool)

    # ── inert during the open beta (what ships today) ──

    def test_beta_leaves_pro_tools_open_to_anonymous(self):
        with _BillingMode(False):
            res, payload = self._run("optimize_build", {"bike_id": 999999}, None)
        self.assertNotEqual(
            payload.get("error"),
            "upgrade_required",
            "the gate is NOT inert during the beta — anonymous chat users "
            "just lost the optimizer",
        )

    def test_beta_leaves_autotune_open_to_anonymous(self):
        with _BillingMode(False):
            _, payload = self._run("autotune_setup", {"bike_id": 999999}, None)
        self.assertNotEqual(payload.get("error"), "upgrade_required")

    def test_pro_tools_locked_predicate_is_inert_in_beta(self):
        with _BillingMode(False):
            for tier in (None, "free", "pro", "studio"):
                self.assertFalse(pro_tools_locked(tier))

    # ── enforcing ──

    def test_anonymous_is_refused_when_enforced(self):
        with _BillingMode(True):
            res, payload = self._run("optimize_build", {"bike_id": 999999}, None)
        self.assertEqual(payload.get("error"), "upgrade_required")
        self.assertEqual(payload.get("required_tier"), "pro")
        self.assertEqual(payload.get("current_tier"), "free")
        self.assertIn("pricing", payload.get("upgrade_url", ""))
        # The refusal is DATA the model relays, not an exception.
        self.assertIn("Pro", payload.get("message", ""))
        self.assertIsNone(res.error)

    def test_free_tier_is_refused_when_enforced(self):
        with _BillingMode(True):
            _, payload = self._run("optimize_build", {"bike_id": 999999}, "free")
        self.assertEqual(payload.get("error"), "upgrade_required")

    def test_pro_tier_passes_when_enforced(self):
        with _BillingMode(True):
            _, payload = self._run("optimize_build", {"bike_id": 999999}, "pro")
        self.assertNotEqual(payload.get("error"), "upgrade_required")

    def test_studio_tier_passes_when_enforced(self):
        with _BillingMode(True):
            _, payload = self._run("autotune_setup", {"bike_id": 999999}, "studio")
        self.assertNotEqual(payload.get("error"), "upgrade_required")

    def test_autotune_is_gated_when_enforced(self):
        with _BillingMode(True):
            _, payload = self._run("autotune_setup", {"bike_id": 999999}, "free")
        self.assertEqual(payload.get("error"), "upgrade_required")

    def test_outlaw_pipeline_is_gated_when_enforced(self):
        """stage_4 routes through optimize_build — the same gate covers it."""
        with _BillingMode(True):
            _, payload = self._run(
                "optimize_build",
                {"bike_id": 999999, "build_tier": "outlaw"},
                "free",
            )
        self.assertEqual(payload.get("error"), "upgrade_required")

    def test_refusal_costs_no_budget_and_no_quota(self):
        """A locked caller must not be charged for work that never ran."""
        charges: list[int] = []
        client, state = _agent_client(
            [[("optimize_build", {"bike_id": 999999})] * 4, "done"]
        )
        with _BillingMode(True):
            res = run_agent_chat(
                "spam",
                _get_db(),
                client=client,
                tier="free",
                meter_cb=lambda n: charges.append(n) or True,
            )
        self.assertEqual(charges, [], "a refused tool still charged the quota")
        self.assertEqual(res.sims_run, 0)
        # All four refused with the SAME reason — none fell through to the
        # per-turn heavy-op budget, which would prove the gate ran late.
        reasons = {t["error"] for t in res.tool_trace}
        self.assertEqual(reasons, {"upgrade_required"})

    def test_free_tools_stay_open_to_locked_callers(self):
        """The gate is surgical: sims/search must still work on free."""
        client, state = _agent_client(
            [[("search_bikes", {"query": "hayabusa"})], "done"]
        )
        with _BillingMode(True):
            res = run_agent_chat("find it", _get_db(), client=client, tier="free")
        payload = _tool_payload(state, "search_bikes")
        self.assertIsNone(res.error)
        self.assertNotEqual(payload.get("error"), "upgrade_required")
        self.assertTrue(payload.get("candidates"))

    def test_system_prompt_warns_the_model_when_locked(self):
        ctx = AgentContext(db=_get_db(), result=AgentChatResult(raw_query="x"))
        with _BillingMode(False):
            self.assertNotIn("ACCESS:", _system_prompt(ctx))
        ctx.tier = "free"
        with _BillingMode(True):
            prompt = _system_prompt(ctx)
        self.assertIn("ACCESS:", prompt)
        for tool in PRO_TOOLS:
            self.assertIn(tool, prompt)


# ───────────────────────────────────────────────────────────────────
# 2. Metering coverage — agent mode
# ───────────────────────────────────────────────────────────────────


class TestAgentMetering(unittest.TestCase):
    def _charges(self, calls, tier=None):
        charged: list[int] = []
        client, _ = _agent_client([calls, "done"])
        run_agent_chat(
            "go",
            _get_db(),
            client=client,
            tier=tier,
            meter_cb=lambda n: charged.append(n) or True,
        )
        return charged

    def test_single_sim_charges_one(self):
        self.assertEqual(self._charges([("run_simulation", {"bike_id": 11})]), [1])

    def test_compare_charges_two(self):
        self.assertEqual(
            self._charges([("compare_bikes", {"bike_a_id": 11, "bike_b_id": 12})]),
            [2],
        )

    def test_heavy_op_charges_its_sim_cost(self):
        """Autotune runs ~18 RK4 sims and used to charge the quota NOTHING."""
        self.assertEqual(
            self._charges([("autotune_setup", {"bike_id": 999999})]),
            [HEAVY_OP_SIM_COST],
        )

    def test_optimizer_charges_its_sim_cost(self):
        self.assertEqual(
            self._charges([("optimize_build", {"bike_id": 999999})]),
            [HEAVY_OP_SIM_COST],
        )

    def test_outlaw_charges_double(self):
        """stage_4 composes an optimizer pass AND an autotune pass."""
        self.assertEqual(
            self._charges(
                [("optimize_build", {"bike_id": 999999, "build_tier": "stage_4"})]
            ),
            [OUTLAW_SIM_COST],
        )

    def test_heavy_op_cost_is_not_one_sim(self):
        """Guards the intent, not just the number."""
        self.assertGreater(HEAVY_OP_SIM_COST, 1)
        self.assertEqual(OUTLAW_SIM_COST, 2 * HEAVY_OP_SIM_COST)

    def test_exhausted_quota_blocks_a_heavy_op_before_it_runs(self):
        client, state = _agent_client(
            [[("autotune_setup", {"bike_id": 11})], "relayed"]
        )
        res = run_agent_chat(
            "tune it", _get_db(), client=client, meter_cb=lambda n: False
        )
        payload = _tool_payload(state, "autotune_setup")
        self.assertIn("quota", payload.get("error", ""))
        self.assertEqual(res.sims_run, 0)

    def test_meter_failure_never_breaks_chat(self):
        def boom(_n):
            raise RuntimeError("metering backend down")

        client, _ = _agent_client([[("run_simulation", {"bike_id": 11})], "done"])
        res = run_agent_chat("go", _get_db(), client=client, meter_cb=boom)
        self.assertIsNone(res.error)
        self.assertEqual(res.sims_run, 1)


# ───────────────────────────────────────────────────────────────────
# 3. Metering coverage — classic mode (the 25-sims-for-free hole)
# ───────────────────────────────────────────────────────────────────


class TestClassicMetering(unittest.TestCase):
    def _charges_allowing(self, parsed, query="go"):
        charged: list[int] = []
        client = _classic_client(parsed)
        res = run_chat_pipeline(
            query,
            _get_db(),
            client=client,
            run_summary=False,
            meter_cb=lambda n: charged.append(n) or True,
        )
        return charged, res

    def _charges_blocking(self, parsed, query="go"):
        """Meter refuses: nothing may run, and we learn the planned batch."""
        charged: list[int] = []
        client = _classic_client(parsed)
        res = run_chat_pipeline(
            query,
            _get_db(),
            client=client,
            run_summary=False,
            meter_cb=lambda n: charged.append(n) or False,
        )
        return charged, res

    def test_simulate_charges_one(self):
        charged, res = self._charges_allowing({"bike_name": "Hayabusa"})
        self.assertEqual(charged, [1])
        self.assertIsNotNone(res.sim_result)

    def test_compare_charges_two(self):
        charged, res = self._charges_allowing(
            {
                "intent_type": "compare",
                "bike_name": "Hayabusa",
                "bike_b_name": "GSX-R 1000",
            }
        )
        self.assertEqual(charged, [2])
        self.assertIsNotNone(res.compare_result)

    def test_rank_reserves_its_whole_batch_before_simulating(self):
        """rank runs up to 15 real sims — the single biggest unmetered path
        after choose_bike. Blocking proves the reservation precedes the CPU."""
        charged, res = self._charges_blocking(
            {"intent_type": "rank"}, query="fastest litre class"
        )
        self.assertEqual(len(charged), 1)
        self.assertGreater(
            charged[0], 1, "rank charged per-sim or not at all, not as a batch"
        )
        self.assertEqual(res.error, "quota_exceeded")
        self.assertIsNone(res.rank_result, "sims ran despite an exhausted quota")

    def test_choose_bike_reserves_its_whole_batch(self):
        charged, res = self._charges_blocking(
            {"intent_type": "choose_bike", "target_class": "litre"},
            query="which litre bike should I buy",
        )
        self.assertEqual(len(charged), 1)
        self.assertGreater(charged[0], 1)
        self.assertEqual(res.error, "quota_exceeded")
        self.assertIsNone(res.choose_bike_result)

    def test_blocked_simulate_runs_nothing(self):
        charged, res = self._charges_blocking({"bike_name": "Hayabusa"})
        self.assertEqual(charged, [1])
        self.assertEqual(res.error, "quota_exceeded")
        self.assertIsNone(res.sim_result)

    def test_blocked_compare_runs_nothing(self):
        charged, res = self._charges_blocking(
            {
                "intent_type": "compare",
                "bike_name": "Hayabusa",
                "bike_b_name": "GSX-R 1000",
            }
        )
        self.assertEqual(charged, [2])
        self.assertEqual(res.error, "quota_exceeded")
        self.assertIsNone(res.compare_result)

    def test_explain_degrades_instead_of_failing(self):
        """Its sim is optional grounding — deliberate exception, pinned."""
        charged, res = self._charges_blocking(
            {"intent_type": "explain", "bike_name": "Hayabusa"},
            query="why does a longer swingarm help",
        )
        self.assertEqual(charged, [1])
        self.assertIsNone(res.error, "explain failed instead of degrading")
        self.assertIsNone(res.sim_result)
        self.assertFalse(res.explain_result["has_sim_grounding"])

    def test_no_meter_cb_is_unmetered(self):
        """The CLI (`python -m motoquant.run chat`) must not need a meter."""
        client = _classic_client({"bike_name": "Hayabusa"})
        res = run_chat_pipeline("go", _get_db(), client=client, run_summary=False)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.sim_result)


# ───────────────────────────────────────────────────────────────────
# 4. The HTTP surface — tier inheritance + metering actually wired
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

    def test_anonymous_chat_is_refused_the_optimizer_when_enforced(self):
        """The audit's exact complaint: after the launch flip, the direct
        route 401s while the chatbot happily does the same work."""
        llm, _ = _agent_client([[("optimize_build", {"bike_id": 999999})], "relayed"])
        self._set_client(llm)
        with _BillingMode(True):
            direct = self.client.post(
                "/api/optimize/build", json={"bike_id": 1, "budget_inr": 50000}
            )
            chat = self.client.post("/api/chat", json={"query": "build me one"})

        self.assertEqual(direct.status_code, 401, "direct pro route is not gated")
        self.assertEqual(chat.status_code, 200)
        trace = chat.json()["tool_trace"]
        self.assertEqual(
            trace[0]["error"],
            "upgrade_required",
            "chat still runs the pro optimizer for an anonymous caller while "
            "the direct route 401s — the two surfaces disagree",
        )

    def test_anonymous_chat_keeps_the_optimizer_during_the_beta(self):
        llm, _ = _agent_client([[("optimize_build", {"bike_id": 999999})], "relayed"])
        self._set_client(llm)
        with _BillingMode(False):
            r = self.client.post("/api/chat", json={"query": "build me one"})
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(r.json()["tool_trace"][0]["error"], "upgrade_required")

    def test_job_chat_inherits_tier_too(self):
        """The job route captures tier on the request thread, not the worker."""
        import time

        llm, _ = _agent_client([[("optimize_build", {"bike_id": 999999})], "relayed"])
        self._set_client(llm)
        with _BillingMode(True):
            r = self.client.post("/api/jobs/chat", json={"query": "build me one"})
            self.assertEqual(r.status_code, 202)
            jid = r.json()["job_id"]
            for _ in range(200):
                time.sleep(0.05)
                jr = self.client.get(f"/api/jobs/{jid}").json()
                if jr["status"] in ("done", "error", "cancelled"):
                    break
        self.assertEqual(jr["status"], "done")
        self.assertEqual(jr["result"]["tool_trace"][0]["error"], "upgrade_required")

    def test_classic_mode_sims_are_metered_through_the_route(self):
        """The wiring fix: /api/chat must hand the meter to classic mode."""
        self._set_client(_classic_client({"bike_name": "Hayabusa"}))
        before = _usage_total()
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
        self.assertEqual(
            _usage_total() - before,
            1,
            "classic-mode chat sims are still unmetered — the meter is not "
            "threaded into run_chat_pipeline",
        )

    def test_agent_mode_sims_are_metered_through_the_route(self):
        llm, _ = _agent_client([[("run_simulation", {"bike_id": 11})], "done"])
        self._set_client(llm)
        before = _usage_total()
        r = self.client.post("/api/chat", json={"query": "sim it"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(_usage_total() - before, 1)


if __name__ == "__main__":
    unittest.main()
