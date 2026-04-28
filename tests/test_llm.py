"""
Tests for motoquant.llm -- Phase A LLM interface layer.

These tests NEVER hit the live Anthropic API. The LLMClient `_call_override`
hook intercepts every call so we can assert on the system/user/tool args and
return canned responses.

Run with:  python -m pytest tests/test_llm.py -v
"""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import MagicMock

from motoquant.llm import (
    LLMClient,
    LLMNotConfiguredError,
    LLMResponse,
    ParsedSimRequest,
    parse_query,
    summarize_result,
)
from motoquant.llm.parse_query import SYSTEM_PROMPT, TOOL_SCHEMA, _resolve_against_db


# ───────────────────────────────────────────────────────────────────
# Helper: build a fake LLMClient with scripted responses
# ───────────────────────────────────────────────────────────────────


def make_mock_client(
    tool_response: dict[str, Any] | LLMResponse | None = None,
    text_response: str = "(stub summary)",
) -> tuple[LLMClient, list[dict[str, Any]]]:
    """Return (client, calls) where calls accumulates every invocation."""
    calls: list[dict[str, Any]] = []

    def fake(kind: str, kwargs: dict[str, Any]):
        calls.append({"kind": kind, **kwargs})
        if kind == "tool":
            return tool_response if tool_response is not None else {
                "bike_name": "Suzuki Hayabusa",
                "optimization_goal": "minimize_et",
            }
        if kind == "text":
            return text_response
        raise AssertionError(f"unexpected kind: {kind}")

    return LLMClient(_call_override=fake), calls


# ───────────────────────────────────────────────────────────────────
# LLMClient -- configuration + override behaviour
# ───────────────────────────────────────────────────────────────────


class TestLLMClient(unittest.TestCase):
    def test_no_api_key_raises_on_call(self):
        """Real call without API key should raise LLMNotConfiguredError."""
        client = LLMClient(api_key=None)
        # bypass the env var if it happens to be set in the test env
        client._api_key = None
        with self.assertRaises(LLMNotConfiguredError):
            client.call_text("system", "user")

    def test_override_bypasses_sdk_for_tool(self):
        """_call_override should be invoked instead of the SDK for tool calls."""
        client, calls = make_mock_client(
            tool_response={"bike_name": "K5", "optimization_goal": "minimize_et"}
        )
        resp = client.call_tool(
            system="sys", user="usr", tool_name="t", tool_schema={"type": "object"}
        )
        self.assertEqual(resp.tool_input["bike_name"], "K5")
        self.assertEqual(resp.stop_reason, "tool_use")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["kind"], "tool")
        self.assertEqual(calls[0]["tool_name"], "t")

    def test_override_returns_llm_response_directly(self):
        """If override returns LLMResponse, it should be passed through."""
        target = LLMResponse(tool_input={"foo": 1}, stop_reason="end_turn")
        client = LLMClient(_call_override=lambda kind, kwargs: target)
        resp = client.call_tool("s", "u", "t", {"type": "object"})
        self.assertIs(resp, target)

    def test_override_invalid_return_type_raises(self):
        """A non-dict / non-LLMResponse override return should TypeError."""
        client = LLMClient(_call_override=lambda kind, kwargs: 42)
        with self.assertRaises(TypeError):
            client.call_tool("s", "u", "t", {"type": "object"})

    def test_override_text_must_return_str(self):
        client = LLMClient(_call_override=lambda kind, kwargs: {"oops": 1})
        with self.assertRaises(TypeError):
            client.call_text("s", "u")

    def test_is_configured_with_override(self):
        client = LLMClient(_call_override=lambda kind, kwargs: "")
        self.assertTrue(client.is_configured)


# ───────────────────────────────────────────────────────────────────
# parse_query -- structured field extraction
# ───────────────────────────────────────────────────────────────────


class TestParseQuery(unittest.TestCase):
    def test_minimal_response_populates_dataclass(self):
        client, _ = make_mock_client(
            tool_response={
                "bike_name": "Suzuki GSX-R 1000 K5",
                "optimization_goal": "minimize_et",
            }
        )
        parsed = parse_query("how fast is my K5", client=client)
        self.assertIsInstance(parsed, ParsedSimRequest)
        self.assertEqual(parsed.bike_name, "Suzuki GSX-R 1000 K5")
        self.assertEqual(parsed.optimization_goal, "minimize_et")
        self.assertEqual(parsed.rider_mass_kg, 75.0)  # default
        self.assertEqual(parsed.power_boost_pct, 0.0)
        self.assertIsNone(parsed.bike_id)  # no DB passed
        self.assertEqual(parsed.parts_categories, [])

    def test_full_response_extracts_all_fields(self):
        client, _ = make_mock_client(
            tool_response={
                "bike_name": "Yamaha YZF-R15 V4",
                "venue_name": "Aamby Valley",
                "ambient_temp_c": 35.0,
                "humidity_pct": 60,
                "altitude_m": 750,
                "headwind_kmh": 8.0,
                "rider_mass_kg": 70,
                "power_boost_pct": 12.5,
                "mass_delta_kg": -5.0,
                "budget_inr": 50000,
                "parts_categories": ["exhaust", "ecu", "weight_reduction"],
                "optimization_goal": "best_budget",
                "notes": "Assumed user means R15 V4.",
            }
        )
        parsed = parse_query("tune my R15 for Aamby...", client=client)
        self.assertEqual(parsed.bike_name, "Yamaha YZF-R15 V4")
        self.assertEqual(parsed.ambient_temp_c, 35.0)
        self.assertEqual(parsed.humidity_pct, 60)
        self.assertEqual(parsed.headwind_kmh, 8.0)
        self.assertEqual(parsed.budget_inr, 50000)
        self.assertEqual(
            parsed.parts_categories, ["exhaust", "ecu", "weight_reduction"]
        )
        self.assertEqual(parsed.optimization_goal, "best_budget")
        self.assertIn("R15 V4", parsed.notes)

    def test_call_args_include_system_prompt_and_schema(self):
        client, calls = make_mock_client()
        parse_query("anything", client=client)
        self.assertEqual(calls[0]["system"], SYSTEM_PROMPT)
        self.assertEqual(calls[0]["tool_schema"], TOOL_SCHEMA)
        self.assertEqual(calls[0]["tool_name"], "submit_sim_query")

    def test_to_quick_sim_kwargs_skips_none(self):
        parsed = ParsedSimRequest(
            raw_query="x",
            bike_name="K5",
            bike_id=42,
            ambient_temp_c=30.0,
            # humidity_pct intentionally None
            power_boost_pct=10.0,
        )
        kw = parsed.to_quick_sim_kwargs()
        self.assertEqual(kw["bike_id"], 42)
        self.assertEqual(kw["ambient_temp_c"], 30.0)
        self.assertNotIn("humidity_pct", kw)
        self.assertNotIn("venue_id", kw)
        self.assertEqual(kw["power_boost_pct"], 10.0)

    def test_handles_null_in_payload(self):
        """LLM may send explicit nulls -- shouldn't crash on float coercion."""
        client, _ = make_mock_client(
            tool_response={
                "bike_name": "K5",
                "optimization_goal": "minimize_et",
                "rider_mass_kg": None,  # explicit null
                "power_boost_pct": None,
                "mass_delta_kg": None,
            }
        )
        parsed = parse_query("...", client=client)
        # Defaults should kick in
        self.assertEqual(parsed.rider_mass_kg, 75.0)
        self.assertEqual(parsed.power_boost_pct, 0.0)
        self.assertEqual(parsed.mass_delta_kg, 0.0)

    def test_db_resolution_populates_ids(self):
        """When db is passed, bike_id and venue_id should be resolved."""
        fake_bike_row = {"id": 7, "manufacturer_name": "Suzuki", "model_name": "Hayabusa"}
        fake_venue = {"id": 3, "name": "Aamby Valley"}

        db = MagicMock()
        db.bikes.search.return_value = [fake_bike_row]
        db.venues.get_by_name.return_value = fake_venue

        client, _ = make_mock_client(
            tool_response={
                "bike_name": "Hayabusa",
                "venue_name": "Aamby Valley",
                "optimization_goal": "minimize_et",
            }
        )
        parsed = parse_query("...", client=client, db=db)
        self.assertEqual(parsed.bike_id, 7)
        self.assertEqual(parsed.venue_id, 3)
        db.bikes.search.assert_called_once_with(name_contains="Hayabusa")
        db.venues.get_by_name.assert_called_once_with("Aamby Valley")

    def test_db_resolution_silent_on_miss(self):
        """No bike match should leave bike_id as None, not raise."""
        db = MagicMock()
        db.bikes.search.return_value = []
        db.venues.get_by_name.return_value = None

        client, _ = make_mock_client(
            tool_response={
                "bike_name": "Nonexistent Bike",
                "venue_name": "Mars Speedway",
                "optimization_goal": "minimize_et",
            }
        )
        parsed = parse_query("...", client=client, db=db)
        self.assertIsNone(parsed.bike_id)
        self.assertIsNone(parsed.venue_id)

    def test_db_resolution_swallows_exceptions(self):
        """If DB throws, parsing should still succeed with bike_id=None."""
        db = MagicMock()
        db.bikes.search.side_effect = RuntimeError("DB blew up")
        db.venues.get_by_name.side_effect = RuntimeError("also blew up")

        client, _ = make_mock_client(
            tool_response={
                "bike_name": "K5",
                "venue_name": "Pomona",
                "optimization_goal": "minimize_et",
            }
        )
        parsed = parse_query("...", client=client, db=db)
        self.assertIsNone(parsed.bike_id)
        self.assertIsNone(parsed.venue_id)

    def test_resolve_against_db_no_bike_name(self):
        """Empty bike_name should not call DB."""
        db = MagicMock()
        parsed = ParsedSimRequest(raw_query="x", bike_name="")
        _resolve_against_db(parsed, db)
        db.bikes.search.assert_not_called()


# ───────────────────────────────────────────────────────────────────
# summarize_result -- prompt construction + return
# ───────────────────────────────────────────────────────────────────


class TestSummarize(unittest.TestCase):
    def test_returns_text_response(self):
        client, _ = make_mock_client(text_response="K5 ran 10.04 s clean.")
        parsed = ParsedSimRequest(raw_query="how fast?", bike_name="K5")
        sim = {"et_s": 10.04, "trap_speed_kmh": 240.0}
        out = summarize_result(parsed, sim, client=client)
        self.assertEqual(out, "K5 ran 10.04 s clean.")

    def test_user_message_includes_headline_numbers(self):
        client, calls = make_mock_client(text_response="ok")
        parsed = ParsedSimRequest(
            raw_query="run my K5",
            bike_name="GSX-R 1000 K5",
            venue_name="Aamby Valley",
            ambient_temp_c=35.0,
            humidity_pct=60.0,
        )
        sim = {
            "et_s": 10.04,
            "trap_speed_kmh": 240.0,
            "sixty_foot_s": 1.65,
            "applied_parts": ["Akrapovic Full System"],
            "build_cost_inr": 295000,
            "delta_et_s": -0.18,
            "peak_accel_g": 1.05,
        }
        summarize_result(parsed, sim, client=client)
        user_msg = calls[0]["user"]
        self.assertIn("10.04", user_msg)
        self.assertIn("240", user_msg)
        self.assertIn("Aamby Valley", user_msg)
        self.assertIn("35", user_msg)  # temp formatted with %g
        self.assertIn("Akrapovic", user_msg)
        self.assertIn("295,000", user_msg)
        self.assertIn("-0.180", user_msg)

    def test_user_message_skips_missing_fields(self):
        client, calls = make_mock_client(text_response="ok")
        parsed = ParsedSimRequest(raw_query="?", bike_name="K5")
        # only ET present
        sim = {"et_s": 10.0}
        summarize_result(parsed, sim, client=client)
        user_msg = calls[0]["user"]
        self.assertIn("10.000", user_msg)
        # should NOT include placeholders for missing fields
        self.assertNotIn("Trap:", user_msg)
        self.assertNotIn("60-ft", user_msg)
        self.assertNotIn("Applied parts", user_msg)
        self.assertNotIn("Build cost", user_msg)

    def test_handles_alternate_field_names(self):
        """sim dict may use api.py names (time_quarter) or chat names (et_s)."""
        client, calls = make_mock_client(text_response="ok")
        parsed = ParsedSimRequest(raw_query="?", bike_name="K5")
        sim = {"time_quarter": 10.04, "time_60ft": 1.65}
        summarize_result(parsed, sim, client=client)
        user_msg = calls[0]["user"]
        self.assertIn("10.040", user_msg)
        self.assertIn("1.650", user_msg)


# ───────────────────────────────────────────────────────────────────
# Schema sanity -- catches future regressions when editing TOOL_SCHEMA
# ───────────────────────────────────────────────────────────────────


class TestToolSchema(unittest.TestCase):
    def test_required_fields_present(self):
        self.assertIn("bike_name", TOOL_SCHEMA["required"])
        self.assertIn("optimization_goal", TOOL_SCHEMA["required"])

    def test_optimization_goal_enum(self):
        enum = TOOL_SCHEMA["properties"]["optimization_goal"]["enum"]
        self.assertEqual(set(enum), {"minimize_et", "maximize_trap", "best_budget"})

    def test_nullable_env_fields(self):
        """Env params should accept null so the model can omit them cleanly."""
        for field_name in ("ambient_temp_c", "humidity_pct", "altitude_m", "headwind_kmh"):
            field_type = TOOL_SCHEMA["properties"][field_name]["type"]
            self.assertIn("null", field_type, f"{field_name} must allow null")


if __name__ == "__main__":
    unittest.main()
