"""
Tests for the chat agent (motoquant/llm/agent.py) + LLMClient.call_tools +
the agent-mode /api/chat + /api/jobs/chat routes.

Real DB (copy of the shipped catalog) + real physics; ONLY the LLM is
scripted via the _call_override seam — the same offline pattern as
tests/test_llm_runner.py, extended to the "tools" kind.

Run with:  python -m pytest tests/test_agent.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

# Point the API at an isolated copy of the SHIPPED catalog DB before any
# motoquant.api import (agent tests need real bikes/parts/tires/fitments).
_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(prefix="mq_agent_test_", suffix=".db", delete=False)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
# Env is asserted in setUpModule (run time), NOT at import/collection time —
# import-time writes poison sibling modules' _PRIOR captures and cascade
# deleted-tmp paths through the suite (July-3 lesson).
_OLD_ENV_DB = None

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.llm.agent import (  # noqa: E402
    AGENT_TOOLS,
    BUILD_TIERS,
    FULL_SIM_BUDGET,
    HEAVY_OP_BUDGET,
    _clip_history,
    resolve_build_tier,
    run_agent_chat,
)
from motoquant.llm.client import (  # noqa: E402
    AgentStep,
    LLMClient,
    LLMRateLimitError,
    ToolCall,
)

_SHARED_DB: MotoQuantDB | None = None


def _get_db() -> MotoQuantDB:
    global _SHARED_DB
    if _SHARED_DB is None:
        _SHARED_DB = MotoQuantDB(_tmp.name)
    return _SHARED_DB


def _scripted_client(script):
    """LLMClient whose call_tools follows `script`: a list where each entry
    is either a str (final text) or a list of (name, args) tool calls.
    Callables receive the kwargs dict and return an entry."""
    state = {"i": 0, "kwargs_log": []}

    def override(kind, kwargs):
        assert kind == "tools", f"unexpected kind {kind}"
        state["kwargs_log"].append(kwargs)
        i = min(state["i"], len(script) - 1)
        state["i"] += 1
        entry = script[i]
        if callable(entry):
            entry = entry(kwargs)
        if isinstance(entry, str):
            return entry
        return {
            "tool_calls": [
                {"id": f"c{i}_{j}", "name": name, "arguments": args}
                for j, (name, args) in enumerate(entry)
            ]
        }

    return LLMClient(_call_override=override), state


def _last_tool_payload(kwargs_log, tool_name):
    """Extract the last tool-result payload the model saw for `tool_name`."""
    for kwargs in reversed(kwargs_log):
        for m in reversed(kwargs["messages"]):
            if m.get("role") == "tool" and m.get("name") == tool_name:
                return json.loads(m["content"])
    return None


# ───────────────────────────────────────────────────────────────────
# call_tools message-format conversion (pure functions)
# ───────────────────────────────────────────────────────────────────


class TestNeutralFormatConversion(unittest.TestCase):
    NEUTRAL = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "checking",
            "tool_calls": [{"id": "t1", "name": "foo", "arguments": {"x": 1}}],
        },
        {"role": "tool", "tool_call_id": "t1", "name": "foo", "content": '{"y":2}'},
        {"role": "assistant", "content": "done"},
    ]

    def test_anthropic_conversion(self):
        out = LLMClient._neutral_to_anthropic(self.NEUTRAL)
        self.assertEqual(out[0], {"role": "user", "content": "hi"})
        blocks = out[1]["content"]
        self.assertEqual(blocks[0]["type"], "text")
        self.assertEqual(blocks[1]["type"], "tool_use")
        self.assertEqual(blocks[1]["id"], "t1")
        self.assertEqual(blocks[1]["input"], {"x": 1})
        # tool result lands inside a user turn
        self.assertEqual(out[2]["role"], "user")
        self.assertEqual(out[2]["content"][0]["type"], "tool_result")
        self.assertEqual(out[2]["content"][0]["tool_use_id"], "t1")

    def test_anthropic_merges_consecutive_tool_results(self):
        msgs = [
            {"role": "tool", "tool_call_id": "a", "name": "f", "content": "1"},
            {"role": "tool", "tool_call_id": "b", "name": "g", "content": "2"},
        ]
        out = LLMClient._neutral_to_anthropic(msgs)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]["content"]), 2)

    def test_openai_conversion(self):
        out = LLMClient._neutral_to_openai(self.NEUTRAL)
        self.assertEqual(out[0], {"role": "user", "content": "hi"})
        tc = out[1]["tool_calls"][0]
        self.assertEqual(tc["type"], "function")
        self.assertEqual(tc["function"]["name"], "foo")
        self.assertEqual(json.loads(tc["function"]["arguments"]), {"x": 1})
        self.assertEqual(out[2]["role"], "tool")
        self.assertEqual(out[2]["tool_call_id"], "t1")

    def test_override_str_becomes_final_text(self):
        client = LLMClient(_call_override=lambda k, kw: "final answer")
        step = client.call_tools("sys", [{"role": "user", "content": "q"}], [])
        self.assertIsInstance(step, AgentStep)
        self.assertEqual(step.text, "final answer")
        self.assertEqual(step.tool_calls, [])

    def test_override_dict_becomes_tool_calls(self):
        client = LLMClient(
            _call_override=lambda k, kw: {
                "tool_calls": [{"name": "foo", "arguments": {"a": 1}}]
            }
        )
        step = client.call_tools("sys", [{"role": "user", "content": "q"}], [])
        self.assertEqual(len(step.tool_calls), 1)
        self.assertIsInstance(step.tool_calls[0], ToolCall)
        self.assertEqual(step.tool_calls[0].name, "foo")


# ───────────────────────────────────────────────────────────────────
# Groq/Llama tool_use_failed flake salvage (Sentry MOTOQUANT-API-1)
# ───────────────────────────────────────────────────────────────────


class _FlakeErr(Exception):
    """Shape-compatible stand-in for openai.BadRequestError on the Groq
    tool_use_failed 400 (carries the payload on .body like the SDK does)."""

    def __init__(self, failed_generation):
        self.body = {
            "error": {
                "code": "tool_use_failed",
                "failed_generation": failed_generation,
            }
        }
        super().__init__("Error code: 400 - tool_use_failed")


def _fake_sdk_client(create_fn):
    from types import SimpleNamespace

    client = LLMClient(provider="groq", api_key="fake-key-for-tests")
    client._sdk_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn))
    )
    return client


_A_TOOL = [
    {
        "name": "search_bikes",
        "description": "",
        "input_schema": {"type": "object", "properties": {}},
    }
]
_A_MSG = [{"role": "user", "content": "how fast is a zx14r?"}]

# The EXACT failed_generation Groq returned in production (MOTOQUANT-API-1).
_PROD_FAILED_GEN = '<function=search_bikes{"query": "zx14r"}</function>'


class TestGroqFlakeSalvage(unittest.TestCase):
    def test_parse_prod_payload(self):
        from motoquant.llm.client import _parse_failed_generation

        self.assertEqual(
            _parse_failed_generation(_PROD_FAILED_GEN),
            [("search_bikes", {"query": "zx14r"})],
        )

    def test_parse_variants(self):
        from motoquant.llm.client import _parse_failed_generation

        self.assertEqual(
            _parse_failed_generation("<function=list_venues{}"),
            [("list_venues", {})],
        )
        self.assertEqual(
            _parse_failed_generation(
                '<function=a{"x":1}</function><function=b{"y":2}</function>'
            ),
            [("a", {"x": 1}), ("b", {"y": 2})],
        )
        # Half-formed JSON must NOT be guessed at — empty means "retry".
        self.assertEqual(_parse_failed_generation('<function=a{"x":'), [])

    def test_error_extraction_body_and_str(self):
        from motoquant.llm.client import _failed_generation_from_error

        self.assertEqual(
            _failed_generation_from_error(_FlakeErr(_PROD_FAILED_GEN)),
            _PROD_FAILED_GEN,
        )
        self.assertIsNone(_failed_generation_from_error(ValueError("boom")))

    def test_salvage_recovers_the_intended_call(self):
        attempts = {"n": 0}

        def raise_flake(**kw):
            attempts["n"] += 1
            raise _FlakeErr(_PROD_FAILED_GEN)

        step = _fake_sdk_client(raise_flake).call_tools("sys", _A_MSG, _A_TOOL)
        self.assertEqual(attempts["n"], 1)  # salvage, not retry
        self.assertEqual(step.tool_calls[0].name, "search_bikes")
        self.assertEqual(step.tool_calls[0].arguments, {"query": "zx14r"})

    def test_unsalvageable_flake_retries_then_succeeds(self):
        from types import SimpleNamespace

        state = {"n": 0}

        def flaky_then_ok(**kw):
            state["n"] += 1
            if state["n"] < 3:
                raise _FlakeErr('<function=broken{"x":')
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="recovered", tool_calls=None),
                        finish_reason="stop",
                    )
                ]
            )

        step = _fake_sdk_client(flaky_then_ok).call_tools("s", _A_MSG, _A_TOOL)
        self.assertEqual(step.text, "recovered")
        self.assertEqual(state["n"], 3)

    def test_persistent_flake_raises_after_retries(self):
        state = {"n": 0}

        def always_flake(**kw):
            state["n"] += 1
            raise _FlakeErr('<function=broken{"x":')

        with self.assertRaises(_FlakeErr):
            _fake_sdk_client(always_flake).call_tools("s", _A_MSG, _A_TOOL)
        self.assertEqual(state["n"], 3)

    def test_unrelated_errors_raise_immediately(self):
        state = {"n": 0}

        def real_error(**kw):
            state["n"] += 1
            raise ValueError("schema invalid")

        with self.assertRaises(ValueError):
            _fake_sdk_client(real_error).call_tools("s", _A_MSG, _A_TOOL)
        self.assertEqual(state["n"], 1)


# ───────────────────────────────────────────────────────────────────
# Build-tier glossary
# ───────────────────────────────────────────────────────────────────


class TestBuildTiers(unittest.TestCase):
    def test_four_stages_exist(self):
        for t in ("stage_1", "stage_2", "stage_3", "stage_4"):
            self.assertIn(t, BUILD_TIERS)

    def test_outlaw_aliases_map_to_stage_4(self):
        self.assertEqual(resolve_build_tier("outlaw"), "stage_4")
        self.assertEqual(resolve_build_tier("open_class"), "stage_4")
        self.assertEqual(resolve_build_tier("all_out"), "stage_4")
        self.assertEqual(resolve_build_tier("Stage-4"), "stage_4")

    def test_unknown_tier_defaults_stage_2(self):
        self.assertEqual(resolve_build_tier("bananas"), "stage_2")
        self.assertEqual(resolve_build_tier(None), "stage_2")

    def test_stage_4_is_unlimited_full_race(self):
        self.assertIsNone(BUILD_TIERS["stage_4"]["default_budget_inr"])
        self.assertEqual(BUILD_TIERS["stage_4"]["profile"], "full_race")

    def test_budgets_ascend(self):
        b1 = BUILD_TIERS["stage_1"]["default_budget_inr"]
        b2 = BUILD_TIERS["stage_2"]["default_budget_inr"]
        b3 = BUILD_TIERS["stage_3"]["default_budget_inr"]
        self.assertLess(b1, b2)
        self.assertLess(b2, b3)

    def test_runner_recipes_are_progressive(self):
        from motoquant.llm.runner import _TIER_RECIPES

        keys = {
            t: {k for k, _ in _TIER_RECIPES[t]}
            for t in ("stage_1", "stage_2", "stage_3", "stage_4")
        }
        self.assertTrue(keys["stage_1"] < keys["stage_2"])
        self.assertTrue(keys["stage_2"] < keys["stage_3"])
        self.assertTrue(keys["stage_3"] < keys["stage_4"])
        # outlaw hardware only in stage_4
        self.assertIn("swingarm", keys["stage_4"])
        self.assertIn("boost", keys["stage_4"])
        self.assertNotIn("boost", keys["stage_2"])

    def test_parse_schema_has_new_tiers(self):
        from motoquant.llm.parse_query import TOOL_SCHEMA

        enum = TOOL_SCHEMA["properties"]["build_tier"]["enum"]
        for t in ("stage_1", "stage_2", "stage_3", "stage_4", "all_out"):
            self.assertIn(t, enum)


# ───────────────────────────────────────────────────────────────────
# Agent loop against real DB + physics
# ───────────────────────────────────────────────────────────────────


class TestAgentLoop(unittest.TestCase):
    def test_search_then_simulate_then_answer(self):
        def pick_and_sim(kwargs):
            data = None
            for m in reversed(kwargs["messages"]):
                if m.get("role") == "tool" and m.get("name") == "search_bikes":
                    data = json.loads(m["content"])
                    break
            bid = (data.get("best_match") or data["candidates"][0])["bike_id"]
            return [("run_simulation", {"bike_id": bid})]

        client, state = _scripted_client(
            [
                [("search_bikes", {"query": "hayabusa"})],
                pick_and_sim,
                "It runs the ET in the sim block.",
            ]
        )
        res = run_agent_chat("how fast is a hayabusa?", _get_db(), client=client)
        self.assertIsNone(res.error)
        self.assertEqual(res.sims_run, 1)
        sim = res.last_block("sim_result")
        self.assertIsNotNone(sim)
        self.assertGreater(sim["et_quarter_s"], 8.0)
        self.assertLess(sim["et_quarter_s"], 12.0)
        self.assertIn("Hayabusa", sim["bike_name"])
        self.assertEqual(res.reply, "It runs the ET in the sim block.")
        self.assertTrue(all(t["ok"] for t in res.tool_trace))

    def test_unknown_tool_is_error_data_not_crash(self):
        client, _ = _scripted_client([[("no_such_tool", {})], "recovered gracefully"])
        res = run_agent_chat("hi", _get_db(), client=client)
        self.assertIsNone(res.error)
        self.assertEqual(res.reply, "recovered gracefully")
        self.assertFalse(res.tool_trace[0]["ok"])
        self.assertIn("unknown tool", res.tool_trace[0]["error"])

    def test_sim_budget_enforced(self):
        # One giant multi-call round exceeding the budget: executor must
        # reject the overflow calls with an error payload, not run them.
        calls = [("run_simulation", {"bike_id": 11})] * (FULL_SIM_BUDGET + 3)
        client, state = _scripted_client([calls, "done"])
        res = run_agent_chat("spam sims", _get_db(), client=client)
        self.assertEqual(res.sims_run, FULL_SIM_BUDGET)
        errs = [t for t in res.tool_trace if not t["ok"]]
        self.assertEqual(len(errs), 3)
        self.assertIn("budget exhausted", errs[0]["error"])

    def test_heavy_op_budget_enforced(self):
        calls = [("autotune_setup", {"bike_id": 999999})] * (HEAVY_OP_BUDGET + 2)
        client, _ = _scripted_client([calls, "done"])
        res = run_agent_chat("spam autotune", _get_db(), client=client)
        errs = [
            t
            for t in res.tool_trace
            if not t["ok"] and "optimizer budget" in (t["error"] or "")
        ]
        self.assertEqual(len(errs), 2)

    def test_meter_quota_blocks_sims(self):
        client, _ = _scripted_client(
            [[("run_simulation", {"bike_id": 11})], "quota message relayed"]
        )
        res = run_agent_chat(
            "sim it",
            _get_db(),
            client=client,
            meter_cb=lambda n: False,
        )
        self.assertEqual(res.sims_run, 0)
        self.assertFalse(res.tool_trace[0]["ok"])
        self.assertIn("quota", res.tool_trace[0]["error"])

    def test_rate_limit_is_typed(self):
        def boom(kind, kwargs):
            raise LLMRateLimitError("429 slow down")

        client = LLMClient(_call_override=boom)
        res = run_agent_chat("hello", _get_db(), client=client)
        self.assertEqual(res.error, "rate_limited")

    def test_iteration_budget_forces_final_answer(self):
        # Model that never stops calling tools: after max_iterations the
        # loop strips the tools and demands a final text (mirrors real
        # provider behavior — no tools param means no tool calls possible).
        def entry(kwargs):
            if not kwargs["tools"]:
                return "forced final"
            return [("get_catalog_stats", {})]

        client, _ = _scripted_client([entry] * 25)
        res = run_agent_chat("loop forever", _get_db(), client=client, max_iterations=3)
        self.assertEqual(res.iterations, 3)
        self.assertEqual(res.reply, "forced final")

    def test_estimated_bike_path(self):
        spec = {
            "manufacturer": "TestMake",
            "model_name": "AgentTest 1000",
            "displacement_cc": 999,
            "peak_power_hp": 180,
            "peak_power_rpm": 12500,
            "peak_torque_nm": 110,
            "peak_torque_rpm": 10000,
            "dry_mass_kg": 175,
            "cylinders": 4,
            "category": "sport",
            "gears": 6,
        }
        client, _ = _scripted_client(
            [[("simulate_estimated_bike", {"spec": spec})], "estimate shown"]
        )
        res = run_agent_chat("how fast is the AgentTest?", _get_db(), client=client)
        est = res.last_block("estimated_sim")
        self.assertIsNotNone(est)
        self.assertTrue(est["estimated"])
        self.assertGreater(est["et_quarter_s"], 8.5)
        self.assertLess(est["et_quarter_s"], 12.5)
        self.assertGreater(est["confidence"], 0.0)
        self.assertLess(est["confidence"], 0.9)
        self.assertIn("top_speed_kmh", est)

    def test_estimated_bike_rejects_nonsense(self):
        spec = {
            "manufacturer": "X",
            "model_name": "Y",
            "displacement_cc": 90000,
            "peak_power_hp": 9000,
            "dry_mass_kg": 5,
        }
        client, state = _scripted_client(
            [[("simulate_estimated_bike", {"spec": spec})], "rejected"]
        )
        res = run_agent_chat("sim nonsense", _get_db(), client=client)
        payload = _last_tool_payload(state["kwargs_log"], "simulate_estimated_bike")
        self.assertIn("validation", payload["error"])
        self.assertIsNone(res.last_block("estimated_sim"))

    def test_sim_modification_knobs_are_live(self):
        """Every run_simulation modifier must MOVE the ET — pins the class
        of bug where a knob writes a phantom attribute nothing reads
        (rider_mass_kg originally wrote RiderParams.rider_mass_kg, which
        does not exist — physics reads chassis.rider_mass_kg)."""
        from motoquant.llm.agent import (
            AgentChatResult,
            AgentContext,
            _build_config_for,
        )
        from motoquant.physics import MotoQuantEngine

        db = _get_db()

        def et(args):
            ctx = AgentContext(db=db, result=AgentChatResult(raw_query=""))
            config, _ = _build_config_for(ctx, {"bike_id": 11, **args})
            return MotoQuantEngine(config).run().time_quarter

        base = et({})
        self.assertGreater(et({"rider_mass_kg": 120}), base + 0.05)
        self.assertGreater(et({"mass_delta_kg": 40}), base + 0.05)
        self.assertLess(et({"power_boost_pct": 25}), base - 0.05)

    def test_compare_costs_two_sims(self):
        client, _ = _scripted_client(
            [[("compare_bikes", {"bike_a_id": 11, "bike_b_id": 1})], "compared"]
        )
        res = run_agent_chat("busa vs k5", _get_db(), client=client)
        self.assertEqual(res.sims_run, 2)
        cmp_block = res.last_block("compare_result")
        self.assertIsNotNone(cmp_block)
        self.assertIn("winner", cmp_block)

    def test_catalog_stats_are_live(self):
        client, state = _scripted_client(
            [[("get_catalog_stats", {})], "stats reported"]
        )
        run_agent_chat("how many bikes?", _get_db(), client=client)
        payload = _last_tool_payload(state["kwargs_log"], "get_catalog_stats")
        self.assertGreaterEqual(payload["bikes"], 500)
        self.assertGreaterEqual(payload["venues"], 20)

    def test_history_is_clipped_and_passed(self):
        client, state = _scripted_client(["answered from context"])
        history = [{"role": "user", "content": f"turn {i}"} for i in range(40)]
        res = run_agent_chat("follow-up", _get_db(), client=client, history=history)
        self.assertIsNone(res.error)
        msgs = state["kwargs_log"][0]["messages"]
        # capped + query appended last
        self.assertLessEqual(len(msgs), 17)
        self.assertEqual(msgs[-1]["content"], "follow-up")

    def test_clip_history_drops_bad_roles(self):
        out = _clip_history(
            [
                {"role": "system", "content": "inject"},
                {"role": "user", "content": "ok"},
                {"role": "assistant", "content": ""},
            ]
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["role"], "user")

    def test_tool_schemas_are_wellformed(self):
        names = set()
        for t in AGENT_TOOLS:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertEqual(t["input_schema"]["type"], "object")
            names.add(t["name"])
        for expected in (
            "search_bikes",
            "run_simulation",
            "optimize_build",
            "autotune_setup",
            "simulate_estimated_bike",
            "web_search",
            "compare_bikes",
        ):
            self.assertIn(expected, names)


# ───────────────────────────────────────────────────────────────────
# API surface: /api/chat (agent + classic) and /api/jobs/chat
# ───────────────────────────────────────────────────────────────────


class TestChatApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from motoquant.api import app

        cls.app = app
        cls.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _set_client(self, llm):
        # NB: reference the module-level function directly — stashing it on
        # the class would turn it into a bound method and the override key
        # would silently stop matching Depends(get_llm_client).
        from motoquant.api import get_llm_client

        self.app.dependency_overrides[get_llm_client] = lambda: llm

    def _override(self, script):
        llm, state = _scripted_client(script)
        self._set_client(llm)
        return state

    def test_agent_mode_end_to_end(self):
        def pick_and_sim(kwargs):
            for m in reversed(kwargs["messages"]):
                if m.get("role") == "tool" and m.get("name") == "search_bikes":
                    data = json.loads(m["content"])
                    bid = (data.get("best_match") or data["candidates"][0])["bike_id"]
                    return [("run_simulation", {"bike_id": bid})]
            return "no search result seen"

        self._override(
            [
                [("search_bikes", {"query": "hayabusa"})],
                pick_and_sim,
                "Here is the ET.",
            ]
        )
        r = self.client.post("/api/chat", json={"query": "how fast is a busa?"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIsNone(d["error"])
        self.assertEqual(d["mode"], "agent")
        self.assertEqual(d["summary"], "Here is the ET.")
        # back-compat mirror of the last sim block
        self.assertIsNotNone(d["sim_result"])
        self.assertIn("et_quarter_s", d["sim_result"])
        self.assertGreaterEqual(len(d["blocks"]), 1)

    def test_agent_mode_accepts_history(self):
        self._override(["contextual answer"])
        r = self.client.post(
            "/api/chat",
            json={
                "query": "and at Aamby Valley?",
                "messages": [
                    {"role": "user", "content": "how fast is a hayabusa?"},
                    {"role": "assistant", "content": "10.223s @ 243 km/h"},
                ],
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["summary"], "contextual answer")

    def test_classic_mode_still_works_and_carries_intent(self):
        def classic_override(kind, kwargs):
            if kind == "tool":
                return {"intent_type": "smalltalk"}
            return "hello!"

        llm = LLMClient(_call_override=classic_override)
        self._set_client(llm)
        r = self.client.post("/api/chat", json={"query": "hi", "mode": "classic"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["mode"], "classic")
        self.assertEqual(d["intent_type"], "smalltalk")
        # live smalltalk counts (was hardcoded '327 bikes')
        self.assertNotIn("327", d["summary"])

    def test_invalid_mode_rejected(self):
        r = self.client.post("/api/chat", json={"query": "hi", "mode": "turbo"})
        self.assertEqual(r.status_code, 422)

    def test_job_chat_lifecycle(self):
        import time

        self._override(["job answer"])
        r = self.client.post("/api/jobs/chat", json={"query": "quick one"})
        self.assertEqual(r.status_code, 202)
        jid = r.json()["job_id"]
        for _ in range(200):
            time.sleep(0.05)
            jr = self.client.get(f"/api/jobs/{jid}").json()
            if jr["status"] in ("done", "error", "cancelled"):
                break
        self.assertEqual(jr["status"], "done")
        self.assertEqual(jr["result"]["summary"], "job answer")

    def test_rate_limited_error_is_typed_in_classic(self):
        def boom(kind, kwargs):
            raise LLMRateLimitError("429")

        llm = LLMClient(_call_override=boom)
        self._set_client(llm)
        r = self.client.post("/api/chat", json={"query": "hi", "mode": "classic"})
        self.assertEqual(r.json()["error"], "rate_limited")


def setUpModule():
    global _OLD_ENV_DB
    _OLD_ENV_DB = os.environ.get("MOTOQUANT_DB")
    """Re-assert this module's tmp DB right before its tests run.

    Module-level MOTOQUANT_DB overrides execute at COLLECTION time, so a
    sibling module imported after this one leaves the env pointing at ITS
    tmp DB by the time these tests actually run. Re-asserting here (plus
    nulling the api singletons) makes collection ordering irrelevant —
    same pattern as tests/test_api.py.
    """
    os.environ["MOTOQUANT_DB"] = _tmp.name
    try:
        import motoquant.api as _api_mod

        _api_mod._db_conn = None
        _api_mod._db_facade = None
    except Exception:  # noqa: BLE001
        pass


def tearDownModule():
    # Restore the env + null the api singletons so later TestClient-backed
    # modules reconnect to their own DB, not this deleted tmp path.
    try:
        import motoquant.api as _api_mod

        if _api_mod._db_conn is not None:
            try:
                _api_mod._db_conn.close()
            except Exception:  # noqa: BLE001
                pass
        _api_mod._db_conn = None
        _api_mod._db_facade = None
    except Exception:  # noqa: BLE001
        pass
    if _OLD_ENV_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _OLD_ENV_DB
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass


if __name__ == "__main__":
    unittest.main()
