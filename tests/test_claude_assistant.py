"""
The Claude client and the agent loop against a fake Anthropic SDK.

A fake SDK object is injected as ``LLMClient._sdk_client``, so these tests
drive the REAL request builder, message converter, stop_reason handling and
error translation, and assert on the exact keyword arguments that would go
to ``client.beta.messages.create``. Real DB (a copy of the shipped catalog)
and real physics; no network.

Fake keys are built at runtime: the repo's secret scan flags a literal
``sk-ant-`` followed by 32+ key characters.

Run with:  python -m pytest tests/test_claude_assistant.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import anthropic

from motoquant.database.connection import MotoQuantDB
from motoquant.llm import client as client_mod
from motoquant.llm.agent import (
    AGENT_MAX_TOKENS,
    AGENT_TOOLS,
    MAX_PAUSE_RESUMES,
    STATIC_SYSTEM_PROMPT,
    STRICT_OPTIONAL_PARAM_BUDGET,
    TOOL_RESULT_MAX_CHARS,
    _optional_count,
    compact_json,
    run_agent_chat,
    tool_result_content,
)
from motoquant.llm.client import (
    FALLBACK_BETA,
    LLMClient,
    LLMError,
    LLMKeyRejectedError,
    LLMNotConfiguredError,
    LLMRefusalError,
    echo_blocks,
    looks_like_anthropic_key,
    redact_secrets,
)

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(prefix="mq_claude_test_", suffix=".db", delete=False)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
_DB: MotoQuantDB | None = None


def _db() -> MotoQuantDB:
    global _DB
    if _DB is None:
        _DB = MotoQuantDB(_tmp.name)
    return _DB


def tearDownModule():
    global _DB
    if _DB is not None:
        _DB.close()
        _DB = None
    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(_tmp.name + suffix)
        except OSError:
            pass


def fake_key(tag: str = "v") -> str:
    return "sk-ant-" + "api03-" + tag * 40


# ─── fake SDK ─────────────────────────────────────────────────────────────


def text(t):
    return SimpleNamespace(type="text", text=t)


def tool_use(id_, name, args=None):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=args or {})


def thinking(sig):
    return SimpleNamespace(type="thinking", thinking="", signature=sig)


def fallback():
    return SimpleNamespace(type="fallback")


def msg(content, stop_reason):
    return SimpleNamespace(content=content, stop_reason=stop_reason)


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        r = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if callable(r):
            r = r(kwargs)
        if isinstance(r, Exception):
            raise r
        return r


class FakeSDK:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)
        self.beta = SimpleNamespace(messages=self.messages)
        self.closed = False

    def close(self):
        self.closed = True


def make_client(responses, assistant="mechanic", own_key=True):
    c = LLMClient(assistant, api_key=fake_key(), own_key=own_key)
    sdk = FakeSDK(responses)
    c._sdk_client = sdk
    return c, sdk.messages


def api_error(cls, status, message, body=None):
    try:
        import httpx2 as hx
    except ImportError:  # anthropic < 1.0
        import httpx as hx
    req = hx.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls(message, response=hx.Response(status, request=req), body=body)


def conn_error():
    try:
        import httpx2 as hx
    except ImportError:
        import httpx as hx
    return anthropic.APIConnectionError(
        request=hx.Request("POST", "https://api.anthropic.com/v1/messages")
    )


def _no_repeated_roles(messages):
    roles = [m["role"] for m in messages]
    return all(a != b for a, b in zip(roles, roles[1:], strict=False))


# ─── request shape ────────────────────────────────────────────────────────


class TestRequestShape(unittest.TestCase):
    def test_agent_turn_sends_the_exact_contract_shape(self):
        c, sdk = make_client([msg([text("hello")], "end_turn")])
        res = run_agent_chat("hi", _db(), client=c)
        self.assertIsNone(res.error, res.error_detail)
        self.assertEqual(res.reply, "hello")
        kw = sdk.calls[0]
        self.assertEqual(
            set(kw),
            {
                "model",
                "max_tokens",
                "betas",
                "fallbacks",
                "thinking",
                "output_config",
                "system",
                "messages",
                "cache_control",
                "tools",
            },
        )
        self.assertEqual(kw["model"], "claude-sonnet-5-5")
        self.assertEqual(kw["max_tokens"], AGENT_MAX_TOKENS)
        self.assertEqual(kw["max_tokens"], 16000)
        self.assertEqual(kw["betas"], [FALLBACK_BETA])
        self.assertEqual(kw["betas"], ["server-side-fallback-2026-07-01"])
        self.assertEqual(kw["fallbacks"], "default")
        self.assertEqual(kw["thinking"], {"type": "adaptive"})
        self.assertEqual(kw["output_config"], {"effort": "medium"})
        self.assertEqual(kw["cache_control"], {"type": "ephemeral"})
        # Never sent: forced tool_choice, budget_tokens, sampling params.
        self.assertNotIn("tool_choice", kw)
        dumped = json.dumps(kw, default=str)
        for banned in ("budget_tokens", "temperature", "top_p", "top_k", "disabled"):
            self.assertNotIn(f'"{banned}"', dumped, banned)
        # No assistant prefill: the last message is the user's.
        self.assertEqual(kw["messages"][-1]["role"], "user")

    def test_doctor_runs_opus_with_medium_effort(self):
        c, sdk = make_client([msg([text("ok")], "end_turn")], assistant="doctor")
        run_agent_chat("hi", _db(), client=c)
        self.assertEqual(sdk.calls[0]["model"], "claude-opus-5-5")
        self.assertEqual(sdk.calls[0]["output_config"], {"effort": "medium"})

    def test_system_is_a_frozen_cached_block_plus_a_small_dynamic_block(self):
        c, sdk = make_client([msg([text("ok")], "end_turn")])
        run_agent_chat("hi", _db(), client=c)
        run_agent_chat("hi again", _db(), client=c)
        s1, s2 = sdk.calls[0]["system"], sdk.calls[1]["system"]
        self.assertEqual(len(s1), 2)
        self.assertEqual(s1[0]["text"], STATIC_SYSTEM_PROMPT)
        self.assertEqual(s1[0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", s1[1])
        self.assertIn("Today is", s1[1]["text"])
        self.assertLess(len(s1[1]["text"]), 300)
        # Byte-identical prefix across requests: static block and tools.
        self.assertEqual(s1[0], s2[0])
        self.assertEqual(
            json.dumps(sdk.calls[0]["tools"]), json.dumps(sdk.calls[1]["tools"])
        )
        # Nothing that changes daily or with the catalog in the frozen block.
        self.assertNotIn("Today is", STATIC_SYSTEM_PROMPT)
        self.assertNotIn("Catalog right now", STATIC_SYSTEM_PROMPT)

    def test_build_planner_guidance_is_in_the_system_prompt(self):
        for phrase in (
            "BUILD PLANNER",
            "1.5 lakh",
            "150000",
            "budget_inr",
            "min_et",
            "max_trap",
            "optimize_build",
            "cost_per_tenth_inr",
            "next_upgrade",
        ):
            self.assertIn(phrase, STATIC_SYSTEM_PROMPT, phrase)

    def test_tools_are_sorted_static_and_strict_where_allowed(self):
        names = [t["name"] for t in AGENT_TOOLS]
        self.assertEqual(names, sorted(names))
        by_name = {t["name"]: t for t in AGENT_TOOLS}
        self.assertTrue(by_name["optimize_build"].get("strict"))
        self.assertTrue(by_name["search_bikes"].get("strict"))
        # A free-form spec object cannot be strict.
        self.assertFalse(by_name["simulate_estimated_bike"].get("strict"))
        strict = [t for t in AGENT_TOOLS if t.get("strict")]
        self.assertLessEqual(
            sum(_optional_count(t["input_schema"]) for t in strict),
            STRICT_OPTIONAL_PARAM_BUDGET,
        )

        def check(node):
            if isinstance(node, dict):
                self.assertNotIn("default", node)
                if node.get("type") == "object":
                    self.assertIs(node.get("additionalProperties"), False)
                for v in node.values():
                    check(v)

        for t in strict:
            check(t["input_schema"])

    def test_classic_parse_uses_structured_output_not_a_forced_tool(self):
        payload = {"intent_type": "simulate", "bike_name": "K5"}
        c, sdk = make_client([msg([text(json.dumps(payload))], "end_turn")])
        from motoquant.llm.parse_query import TOOL_SCHEMA, parse_query

        parsed = parse_query("how fast is a K5", client=c)
        self.assertEqual(parsed.bike_name, "K5")
        kw = sdk.calls[0]
        self.assertNotIn("tool_choice", kw)
        self.assertNotIn("tools", kw)
        fmt = kw["output_config"]["format"]
        self.assertEqual(kw["output_config"]["effort"], "medium")
        self.assertEqual(fmt["type"], "json_schema")
        schema = fmt["schema"]
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["required"]), set(TOOL_SCHEMA["properties"]))
        self.assertEqual(kw["betas"], [FALLBACK_BETA])
        self.assertEqual(kw["fallbacks"], "default")
        self.assertEqual(kw["thinking"], {"type": "adaptive"})

    def test_classic_parse_retries_once_on_unusable_json_then_fails(self):
        c, sdk = make_client([msg([text("{not json")], "max_tokens")])
        with self.assertRaises(RuntimeError):
            c.call_tool("sys", "q", "submit_sim_query", {"type": "object"})
        self.assertEqual(len(sdk.calls), 2)

    def test_classic_parse_refusal_is_typed(self):
        c, _ = make_client([msg([], "refusal")])
        with self.assertRaises(LLMRefusalError):
            c.call_tool("sys", "q", "submit_sim_query", {"type": "object"})

    def test_call_text_uses_the_same_base_shape(self):
        c, sdk = make_client([msg([thinking("s"), text(" summary ")], "end_turn")])
        self.assertEqual(c.call_text("sys", "user"), "summary")
        kw = sdk.calls[0]
        self.assertEqual(kw["thinking"], {"type": "adaptive"})
        self.assertEqual(kw["system"][0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("tool_choice", kw)

    def test_forced_tool_choice_is_refused_by_the_builder(self):
        c = LLMClient(api_key=fake_key(), own_key=True)
        for choice in ({"type": "any"}, {"type": "tool", "name": "x"}):
            with self.assertRaises(ValueError):
                c.request_kwargs(system="s", messages=[], tool_choice=choice)


# ─── loop behaviour ───────────────────────────────────────────────────────


class TestAgentLoop(unittest.TestCase):
    def test_assistant_content_is_echoed_verbatim_with_thinking(self):
        sig_block = thinking("sig-1")
        first = [sig_block, text("checking"), tool_use("t1", "get_catalog_stats")]
        c, sdk = make_client(
            [msg(first, "tool_use"), msg([text("there are lots")], "end_turn")]
        )
        res = run_agent_chat("how many bikes?", _db(), client=c)
        self.assertEqual(res.reply, "there are lots")
        second = sdk.calls[1]["messages"]
        self.assertEqual(second[-2]["role"], "assistant")
        echoed = second[-2]["content"]
        self.assertEqual([b.type for b in echoed], ["thinking", "text", "tool_use"])
        self.assertIs(echoed[0], sig_block)
        self.assertEqual(second[-1]["role"], "user")
        result_block = second[-1]["content"][0]
        self.assertEqual(result_block["type"], "tool_result")
        self.assertEqual(result_block["tool_use_id"], "t1")
        self.assertGreaterEqual(json.loads(result_block["content"])["bikes"], 500)

    def test_every_tool_result_goes_back_in_one_user_message(self):
        calls = [tool_use("a", "get_catalog_stats"), tool_use("b", "list_venues")]
        c, sdk = make_client([msg(calls, "tool_use"), msg([text("done")], "end_turn")])
        run_agent_chat("stats and venues", _db(), client=c)
        last = sdk.calls[1]["messages"][-1]
        self.assertEqual(last["role"], "user")
        self.assertEqual(
            [(b["type"], b["tool_use_id"]) for b in last["content"]],
            [("tool_result", "a"), ("tool_result", "b")],
        )
        self.assertTrue(_no_repeated_roles(sdk.calls[1]["messages"]))

    def test_fallback_block_echo_rule(self):
        content = [
            text("before"),
            thinking("declined-model"),
            tool_use("t0", "list_venues"),
            fallback(),
            thinking("fallback-model"),
            text("after"),
            tool_use("t1", "get_catalog_stats"),
        ]
        c, sdk = make_client([msg(content, "tool_use"), msg([text("ok")], "end_turn")])
        res = run_agent_chat("q", _db(), client=c)
        # Only the tool call after the last fallback block runs.
        self.assertEqual([t["tool"] for t in res.tool_trace], ["get_catalog_stats"])
        echoed = sdk.calls[1]["messages"][-2]["content"]
        self.assertEqual(
            [(b.type, getattr(b, "signature", getattr(b, "id", None))) for b in echoed],
            [
                ("text", None),
                ("fallback", None),
                ("thinking", "fallback-model"),
                ("text", None),
                ("tool_use", "t1"),
            ],
        )

    def test_echo_blocks_without_fallback_is_verbatim(self):
        blocks = [thinking("a"), text("b"), tool_use("c", "x")]
        self.assertEqual(echo_blocks(blocks), blocks)

    def test_echo_blocks_uses_the_last_fallback_boundary(self):
        blocks = [
            thinking("1"),
            fallback(),
            thinking("2"),
            tool_use("u", "x"),
            fallback(),
            thinking("3"),
        ]
        kept = echo_blocks(blocks)
        self.assertEqual(
            [(b.type, getattr(b, "signature", None)) for b in kept],
            [("fallback", None), ("fallback", None), ("thinking", "3")],
        )

    def test_refusal_returns_refused_and_runs_no_tools(self):
        c, sdk = make_client(
            [msg([tool_use("t", "run_simulation", {"bike_id": 11})], "refusal")]
        )
        res = run_agent_chat("q", _db(), client=c)
        self.assertEqual(res.error, "refused")
        self.assertEqual(res.tool_trace, [])
        self.assertEqual(res.sims_run, 0)
        self.assertEqual(len(sdk.calls), 1)

    def test_truncated_tool_call_is_not_run_and_is_retried_once(self):
        cut = msg([thinking("x"), tool_use("t", "run_simulation", {})], "max_tokens")
        c, sdk = make_client([cut, msg([text("short answer")], "end_turn")])
        res = run_agent_chat("q", _db(), client=c)
        self.assertIsNone(res.error)
        self.assertEqual(res.reply, "short answer")
        self.assertEqual(res.tool_trace, [])
        self.assertEqual(res.sims_run, 0)
        retry = sdk.calls[1]["messages"]
        # The cut-off assistant turn is not echoed; a short note is added to
        # the user turn instead.
        self.assertEqual([m["role"] for m in retry], ["user"])
        self.assertIn("cut off", json.dumps(retry[-1]["content"]))

    def test_truncated_twice_fails_cleanly(self):
        cut = msg([tool_use("t", "run_simulation", {})], "max_tokens")
        c, sdk = make_client([cut])
        res = run_agent_chat("q", _db(), client=c)
        self.assertEqual(res.error, "agent_failed")
        self.assertEqual(len(sdk.calls), 2)
        self.assertEqual(res.tool_trace, [])

    def test_pause_turn_is_resent_as_is_and_capped(self):
        paused = [text("partial")]
        c, sdk = make_client([msg(paused, "pause_turn")])
        res = run_agent_chat("q", _db(), client=c)
        self.assertEqual(len(sdk.calls), 1 + MAX_PAUSE_RESUMES)
        second = sdk.calls[1]["messages"]
        self.assertEqual(second[-1]["role"], "assistant")
        self.assertEqual(second[-1]["content"], paused)
        self.assertEqual(res.reply, "partial")

    def test_pause_then_finish(self):
        c, sdk = make_client(
            [msg([text("partial")], "pause_turn"), msg([text("done")], "end_turn")]
        )
        res = run_agent_chat("q", _db(), client=c)
        self.assertEqual(res.reply, "done")
        self.assertEqual(len(sdk.calls), 2)

    def test_final_turn_keeps_tools_and_sends_tool_choice_none(self):
        def respond(kw):
            if kw.get("tool_choice") == {"type": "none"}:
                return msg([text("final answer")], "end_turn")
            n = len(kw["messages"])
            return msg([tool_use(f"t{n}", "get_catalog_stats")], "tool_use")

        c, sdk = make_client([respond])
        res = run_agent_chat("loop", _db(), client=c, max_iterations=2)
        self.assertEqual(res.reply, "final answer")
        final = sdk.calls[-1]
        self.assertEqual(final["tool_choice"], {"type": "none"})
        self.assertEqual(final["tools"], sdk.calls[0]["tools"])
        for kw in sdk.calls[:-1]:
            self.assertNotIn("tool_choice", kw)
        last = final["messages"][-1]
        self.assertEqual(last["role"], "user")
        self.assertEqual([b["type"] for b in last["content"]], ["tool_result", "text"])
        self.assertTrue(_no_repeated_roles(final["messages"]))

    def test_unconfigured_client_is_assistant_unavailable(self):
        c = LLMClient(own_key=True, api_key=None)
        res = run_agent_chat("q", _db(), client=c)
        self.assertEqual(res.error, "assistant_unavailable")


# ─── tool results ─────────────────────────────────────────────────────────


def _build_payload(n_parts: int) -> dict:
    parts = [
        {
            "part_id": i,
            "name": f"Part {i} " + "x" * 80,
            "brand": "Brand",
            "category": "exhaust",
            "category_display": "Exhaust",
            "price_inr": 10000.0 + i,
            "delta_et_s": -0.0123456,
            "delta_trap_ms": 0.5,
            "delta_trap_mps": 0.5,
            "roi_score": 1.234567,
            "cost_per_tenth_inr": 81234.5678,
            "is_compatible": True,
            "no_straight_line_effect": False,
        }
        for i in range(n_parts)
    ]
    return {
        "bike_name": "Suzuki GSX-R1000 K5",
        "goal": "min_et",
        "budget_inr": 150000.0,
        "profile": "street_legal",
        "base_et_s": 10.0436,
        "base_trap_kmh": 236.2,
        "optimized_et_s": 9.9,
        "optimized_trap_kmh": 240.1,
        "delta_et_s": -0.1436,
        "delta_trap_kmh": 3.9,
        "total_cost_inr": 140000.0,
        "budget_used_pct": 93.3,
        "cost_per_tenth_inr": 97493.0,
        "parts": parts,
        "synergies": [{"parts": ["a", "b"], "note": "x" * 50}],
        "warnings": ["needs a dyno tune"],
        "next_upgrade": {"name": "Quickshifter", "price_inr": 30000},
        "category_priority": ["exhaust"] * 50,
        "scoring_stats": {"k": list(range(500))},
        "applied_part_ids": list(range(200)),
        "build_tier": "stage_2",
        "tier_label": "Stage 2: bolt-ons + drivetrain",
    }


class TestToolResults(unittest.TestCase):
    def test_optimize_build_summary_has_what_the_planner_explains(self):
        out = json.loads(tool_result_content("optimize_build", _build_payload(3)))
        for key in (
            "base_et_s",
            "optimized_et_s",
            "base_trap_kmh",
            "optimized_trap_kmh",
            "total_cost_inr",
            "parts",
            "warnings",
            "synergies",
            "next_upgrade",
        ):
            self.assertIn(key, out)
        self.assertEqual(
            set(out["parts"][0]),
            {
                "name",
                "brand",
                "category",
                "price_inr",
                "delta_et_s",
                "cost_per_tenth_inr",
            },
        )
        # Internals the model does not need are left out.
        self.assertNotIn("scoring_stats", out)
        self.assertNotIn("applied_part_ids", out)

    def test_large_build_stays_valid_json_under_the_limit(self):
        content = tool_result_content("optimize_build", _build_payload(200))
        self.assertLessEqual(len(content), TOOL_RESULT_MAX_CHARS)
        out = json.loads(content)
        self.assertTrue(out["truncated"])
        self.assertEqual(out["optimized_et_s"], 9.9)

    def test_compact_json_never_cuts_mid_string(self):
        payloads = [
            {"rows": [{"s": "é" * 3000, "n": i} for i in range(100)]},
            {"blob": "y" * 50_000},
            [{"a": "z" * 7000}] * 30,
            {"error": "boom " * 2000, **{f"k{i}": "v" * 300 for i in range(200)}},
        ]
        for p in payloads:
            text_out = compact_json(p)
            self.assertLessEqual(len(text_out), TOOL_RESULT_MAX_CHARS)
            json.loads(text_out)  # must parse

    def test_compact_json_is_compact(self):
        self.assertEqual(compact_json({"a": 1, "b": [1, 2]}), '{"a":1,"b":[1,2]}')

    def test_non_build_payloads_are_passed_through_whole_when_small(self):
        p = {"bikes": 600, "parts": 900}
        self.assertEqual(json.loads(tool_result_content("get_catalog_stats", p)), p)


# ─── keys and errors ──────────────────────────────────────────────────────


class TestKeysAndErrors(unittest.TestCase):
    def setUp(self):
        client_mod.reset_server_key_resting()

    def tearDown(self):
        client_mod.reset_server_key_resting()

    def test_key_format(self):
        self.assertTrue(looks_like_anthropic_key(fake_key()))
        for bad in (
            None,
            "",
            "sk-ant-short",
            "sk-proj-" + "a" * 40,
            fake_key() + " ",
            "sk-ant-" + "a" * 20 + " " + "b" * 10,
            "sk-ant-" + "a" * 400,
            "sk-ant-" + "é" * 30,
        ):
            self.assertFalse(looks_like_anthropic_key(bad), bad)

    def test_redact_replaces_every_key(self):
        k1, k2 = fake_key("a"), fake_key("b")
        out = redact_secrets(f"x {k1} y '{k2}' z")
        self.assertNotIn(k1, out)
        self.assertNotIn(k2, out)
        self.assertEqual(out.count("[redacted]"), 2)

    def test_visitor_client_never_reads_the_env_key(self):
        server = fake_key("s")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": server}):
            c = LLMClient(own_key=True, api_key=None)
            self.assertFalse(c.is_configured)
            with self.assertRaises(LLMKeyRejectedError):
                c._get_sdk()
            bad = LLMClient(own_key=True, api_key="not-a-key")
            self.assertFalse(bad.is_configured)
            built = []
            with mock.patch.object(
                client_mod, "_build_sdk", lambda k, t: built.append(k) or FakeSDK([])
            ):
                visitor = fake_key("v")
                LLMClient(own_key=True, api_key=visitor)._get_sdk()
                LLMClient()._get_sdk()
            self.assertEqual(built[0], visitor)
            self.assertNotIn(visitor, client_mod._SERVER_SDK)
            self.assertIn(server, built)
        client_mod._SERVER_SDK.clear()

    def test_repr_and_close_drop_the_key(self):
        k = fake_key()
        c = LLMClient(own_key=True, api_key=k)
        self.assertNotIn(k, repr(c))
        sdk = FakeSDK([])
        c._sdk_client = sdk
        c.close()
        self.assertTrue(sdk.closed)
        self.assertIsNone(c._api_key)
        self.assertIsNone(c._sdk_client)

    def _err_result(self, exc, own_key=True):
        c, _ = make_client([exc], own_key=own_key)
        return run_agent_chat("q", _db(), client=c)

    def test_visitor_key_rejected(self):
        for cls, status in (
            (anthropic.AuthenticationError, 401),
            (anthropic.PermissionDeniedError, 403),
        ):
            res = self._err_result(api_error(cls, status, "invalid x-api-key"))
            self.assertEqual(res.error, "key_rejected", cls)

    def test_server_key_rejected_is_unavailable(self):
        res = self._err_result(
            api_error(anthropic.AuthenticationError, 401, "invalid"), own_key=False
        )
        self.assertEqual(res.error, "assistant_unavailable")

    def test_server_credit_exhausted_is_resting(self):
        e = api_error(
            anthropic.BadRequestError,
            400,
            "Your credit balance is too low to access the Anthropic API.",
        )
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": fake_key("s")}):
            self.assertTrue(client_mod.free_assistant_available())
            res = self._err_result(e, own_key=False)
            self.assertEqual(res.error, "free_assistant_resting")
            self.assertFalse(client_mod.free_assistant_available())

    def test_spend_limit_and_billing_status_are_resting(self):
        for e in (
            api_error(
                anthropic.BadRequestError,
                400,
                "You have reached your specified API usage limits.",
            ),
            api_error(
                anthropic.APIStatusError,
                402,
                "payment required",
                body={"type": "error", "error": {"type": "billing_error"}},
            ),
        ):
            client_mod.reset_server_key_resting()
            self.assertEqual(
                self._err_result(e, own_key=False).error, "free_assistant_resting"
            )

    def test_visitor_credit_exhausted_is_key_rejected_not_resting(self):
        e = api_error(anthropic.BadRequestError, 400, "Your credit balance is too low")
        self.assertEqual(self._err_result(e).error, "key_rejected")
        self.assertFalse(client_mod.server_key_resting())

    def test_rate_limit_not_found_connection(self):
        self.assertEqual(
            self._err_result(
                api_error(anthropic.RateLimitError, 429, "slow down")
            ).error,
            "rate_limited",
        )
        nf = self._err_result(api_error(anthropic.NotFoundError, 404, "model"))
        self.assertEqual(nf.error, "agent_failed")
        self.assertIn("claude-sonnet-5-5", nf.error_detail)
        conn = self._err_result(conn_error())
        self.assertEqual(conn.error, "agent_failed")
        self.assertIn("reach Anthropic", conn.error_detail)

    def test_error_detail_never_contains_a_key(self):
        k = fake_key("leak")
        for e in (
            api_error(anthropic.BadRequestError, 400, f"bad request near {k}"),
            api_error(anthropic.InternalServerError, 500, f"oops {k}"),
            RuntimeError(f"weird {k}"),
        ):
            res = self._err_result(e)
            self.assertNotIn(k, json.dumps(res.to_dict()))
            self.assertNotIn("sk-ant-", res.error_detail or "")

    def test_llm_errors_redact_on_construction(self):
        k = fake_key()
        for cls in (LLMError, LLMNotConfiguredError, LLMKeyRejectedError):
            self.assertNotIn(k, str(cls(f"x {k}")))

    def test_classic_runner_keeps_typed_codes_and_redacts(self):
        from motoquant.llm.runner import run_chat_pipeline

        k = fake_key()

        def boom(kind, kwargs):
            raise LLMKeyRejectedError(f"refused {k}")

        res = run_chat_pipeline("q", _db(), client=LLMClient(_call_override=boom))
        self.assertEqual(res.error, "key_rejected")
        self.assertNotIn(k, res.error_detail)

    def test_classic_summary_failure_is_redacted(self):
        from motoquant.llm.runner import run_chat_pipeline

        k = fake_key()

        def fake(kind, kwargs):
            if kind == "tool":
                return {"intent_type": "simulate", "bike_name": "Hayabusa"}
            raise RuntimeError(f"summary died {k}")

        res = run_chat_pipeline("busa", _db(), client=LLMClient(_call_override=fake))
        self.assertIsNone(res.error, res.error_detail)
        self.assertIn("summary failed", res.summary)
        self.assertNotIn(k, res.summary)


if __name__ == "__main__":
    unittest.main()


class TestWeightedRateLimit(unittest.TestCase):
    def test_cost_counts_units(self):
        from motoquant import ratelimit

        ratelimit.reset()
        key = "unit-test-weighted:1.2.3.4"
        self.assertEqual(ratelimit.check(key, 3, 60.0, cost=2)[0], True)
        self.assertEqual(ratelimit.check(key, 3, 60.0)[0], True)
        self.assertEqual(ratelimit.check(key, 3, 60.0)[0], False)
        ratelimit.reset()
