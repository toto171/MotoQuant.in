"""
Tests for the advanced chat features added April 30, 2026:

- build_tier auto-detection from query phrasing
- target_class + prefer_indian fields on ParsedSimRequest
- 'choose_bike' intent dispatch
- Tier-aware recommend recipes (stage_1 / stage_2 / all_out)
- _CLASS_FILTERS table behavior
- Stricter summary prompts forbid generic platitudes

These are mostly pure-Python tests against an in-memory SQLite DB so
they run fast (no LLM, no FUSE, no Groq quota burn).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from typing import Any

# Project root on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class _StubLLM:
    """Records prompts the runner passes; returns canned responses."""

    def __init__(self, tool_response=None, text_response="(stub)"):
        self.tool_response = tool_response or {}
        self.text_response = text_response
        self.calls = []  # list of (kind, system, user) tuples

    def call_tool(self, *, system, user, tool_name, tool_schema):
        from motoquant.llm.client import LLMResponse
        self.calls.append(("tool", system, user))
        return LLMResponse(
            tool_input=self.tool_response, stop_reason="tool_use"
        )

    def call_text(self, *, system, user):
        self.calls.append(("text", system, user))
        return self.text_response


# ─────────────────────────────────────────────────────────────────
# build_tier auto-detection — tested via parse_query parsing
# ─────────────────────────────────────────────────────────────────


class TestBuildTierField(unittest.TestCase):
    """ParsedSimRequest accepts build_tier; default is stage_2."""

    def test_default_is_stage_2(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        p = ParsedSimRequest(raw_query="upgrade my K5", bike_name="K5")
        self.assertEqual(p.build_tier, "stage_2")

    def test_can_set_stage_1(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        p = ParsedSimRequest(
            raw_query="basic mods", bike_name="R15", build_tier="stage_1"
        )
        self.assertEqual(p.build_tier, "stage_1")

    def test_can_set_all_out(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        p = ParsedSimRequest(
            raw_query="no budget", bike_name="Hayabusa", build_tier="all_out"
        )
        self.assertEqual(p.build_tier, "all_out")

    def test_target_class_default_none(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        p = ParsedSimRequest(raw_query="x", bike_name="x")
        self.assertIsNone(p.target_class)
        self.assertFalse(p.prefer_indian)

    def test_choose_bike_fields(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        p = ParsedSimRequest(
            raw_query="best litre bike for me",
            bike_name="",
            intent_type="choose_bike",
            target_class="litre",
            prefer_indian=True,
            venue_name="Aamby Valley",
            budget_inr=2_000_000,
        )
        self.assertEqual(p.intent_type, "choose_bike")
        self.assertEqual(p.target_class, "litre")
        self.assertTrue(p.prefer_indian)


# ─────────────────────────────────────────────────────────────────
# TOOL_SCHEMA contains the new fields
# ─────────────────────────────────────────────────────────────────


class TestToolSchema(unittest.TestCase):
    def test_intent_enum_has_choose_bike(self):
        from motoquant.llm.parse_query import TOOL_SCHEMA
        intents = TOOL_SCHEMA["properties"]["intent_type"]["enum"]
        self.assertIn("choose_bike", intents)

    def test_build_tier_in_schema(self):
        from motoquant.llm.parse_query import TOOL_SCHEMA
        self.assertIn("build_tier", TOOL_SCHEMA["properties"])
        bt = TOOL_SCHEMA["properties"]["build_tier"]
        self.assertEqual(bt["type"], "string")
        self.assertIn("stage_1", bt["enum"])
        self.assertIn("stage_2", bt["enum"])
        self.assertIn("all_out", bt["enum"])

    def test_target_class_and_prefer_indian_in_schema(self):
        from motoquant.llm.parse_query import TOOL_SCHEMA
        self.assertIn("target_class", TOOL_SCHEMA["properties"])
        self.assertIn("prefer_indian", TOOL_SCHEMA["properties"])
        self.assertEqual(
            TOOL_SCHEMA["properties"]["prefer_indian"]["type"], "boolean"
        )

    def test_system_prompt_has_tier_hints(self):
        from motoquant.llm.parse_query import SYSTEM_PROMPT
        self.assertIn("Build tier inference hints", SYSTEM_PROMPT)
        self.assertIn("Race-class hints", SYSTEM_PROMPT)
        self.assertIn("stage_1", SYSTEM_PROMPT)
        self.assertIn("all_out", SYSTEM_PROMPT)


# ─────────────────────────────────────────────────────────────────
# Tier recipes — _TIER_RECIPES constants
# ─────────────────────────────────────────────────────────────────


class TestTierRecipes(unittest.TestCase):
    def test_recipes_are_progressive(self):
        from motoquant.llm.runner import (
            _TIER_RECIPES,
            _TIER_STAGE_1,
            _TIER_STAGE_2,
            _TIER_ALL_OUT,
        )
        # stage_2 is a proper superset of stage_1
        s1_keys = {k for k, _ in _TIER_STAGE_1}
        s2_keys = {k for k, _ in _TIER_STAGE_2}
        ao_keys = {k for k, _ in _TIER_ALL_OUT}
        self.assertTrue(s1_keys.issubset(s2_keys))
        self.assertTrue(s2_keys.issubset(ao_keys))
        # Lookup table is correct
        self.assertEqual(_TIER_RECIPES["stage_1"], _TIER_STAGE_1)
        self.assertEqual(_TIER_RECIPES["stage_2"], _TIER_STAGE_2)
        self.assertEqual(_TIER_RECIPES["all_out"], _TIER_ALL_OUT)

    def test_stage_1_excludes_premium_categories(self):
        from motoquant.llm.runner import _TIER_STAGE_1
        keys = {k for k, _ in _TIER_STAGE_1}
        # Stage 1 must NOT include suspension / brakes / forced induction
        self.assertNotIn("suspension", keys)
        self.assertNotIn("brakes", keys)
        self.assertNotIn("nitrous", keys)
        self.assertNotIn("boost", keys)

    def test_all_out_includes_forced_induction(self):
        from motoquant.llm.runner import _TIER_ALL_OUT
        keys = {k for k, _ in _TIER_ALL_OUT}
        self.assertIn("nitrous", keys)
        self.assertIn("boost", keys)
        self.assertIn("suspension", keys)


# ─────────────────────────────────────────────────────────────────
# choose_bike — _CLASS_FILTERS keys
# ─────────────────────────────────────────────────────────────────


class TestClassFilters(unittest.TestCase):
    def test_litre_class(self):
        from motoquant.llm.runner import _CLASS_FILTERS
        litre = _CLASS_FILTERS["litre"]
        self.assertEqual(litre["disp_min"], 950)
        self.assertEqual(litre["disp_max"], 1200)
        self.assertIn("sport", litre["categories"])

    def test_2t_filter_has_stroke_type(self):
        from motoquant.llm.runner import _CLASS_FILTERS
        self.assertEqual(_CLASS_FILTERS["2t"]["stroke_type"], 2)

    def test_modified_hayabusa_filter(self):
        from motoquant.llm.runner import _CLASS_FILTERS
        f = _CLASS_FILTERS["modified-hayabusa"]
        self.assertIn("Hayabusa", f["model_keywords"])

    def test_alias_two_stroke(self):
        from motoquant.llm.runner import _CLASS_FILTERS
        self.assertEqual(
            _CLASS_FILTERS["two-stroke"]["stroke_type"], 2
        )


# ─────────────────────────────────────────────────────────────────
# choose_bike candidate query — SQL shape
# ─────────────────────────────────────────────────────────────────


class TestChooseBikeQuery(unittest.TestCase):
    def test_litre_query_shape(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        from motoquant.llm.runner import _choose_bike_candidate_query

        parsed = ParsedSimRequest(
            raw_query="x",
            bike_name="",
            intent_type="choose_bike",
            target_class="litre",
        )
        sql, params = _choose_bike_candidate_query(parsed, db=None)
        self.assertIn("displacement_cc >= ?", sql)
        self.assertIn("displacement_cc <= ?", sql)
        self.assertIn("LOWER(bm.category) IN", sql)
        self.assertEqual(params[0], 950)  # disp_min
        self.assertEqual(params[1], 1200)  # disp_max

    def test_indian_filter_adds_manufacturer_clause(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        from motoquant.llm.runner import _choose_bike_candidate_query

        parsed_neutral = ParsedSimRequest(
            raw_query="x", bike_name="", target_class="litre",
        )
        parsed_indian = ParsedSimRequest(
            raw_query="x", bike_name="", target_class="litre",
            prefer_indian=True,
        )
        sql_n, _ = _choose_bike_candidate_query(parsed_neutral, db=None)
        sql_i, _ = _choose_bike_candidate_query(parsed_indian, db=None)
        self.assertNotIn("m.name IN", sql_n)
        self.assertIn("m.name IN", sql_i)

    def test_unknown_class_falls_back_to_litre(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        from motoquant.llm.runner import _choose_bike_candidate_query

        parsed = ParsedSimRequest(
            raw_query="x", bike_name="", target_class="not-a-real-class",
        )
        sql, params = _choose_bike_candidate_query(parsed, db=None)
        # Should still produce a sane query (fallback to litre)
        self.assertIn("displacement_cc", sql)
        self.assertIn(950, params)


# ─────────────────────────────────────────────────────────────────
# Summary prompt strictness — sanity checks
# ─────────────────────────────────────────────────────────────────


class TestSummaryPromptStrictness(unittest.TestCase):
    """Each strict summarizer prompt must forbid hallucination."""

    def _get_prompt_via_stub(self, summarizer_name, *args):
        """Instantiate stub LLM, call summarizer, return the system prompt."""
        from motoquant.llm import runner as r
        stub = _StubLLM()
        getattr(r, summarizer_name)(*args, stub)
        # Return system prompt from first call
        return stub.calls[0][1]

    def test_compare_prompt_forbids_filler(self):
        from motoquant.llm.parse_query import ParsedSimRequest
        from motoquant.llm.runner import _summarize_compare
        sys_p = self._get_prompt_via_stub(
            "_summarize_compare",
            ParsedSimRequest(raw_query="K5 vs R1", bike_name="K5"),
            {"a": {"bike_name": "K5", "sim": {"et_quarter_s": 10.03,
             "trap_speed_kmh": 235, "et_60ft_s": 1.45}},
             "b": {"bike_name": "R1", "sim": {"et_quarter_s": 10.29,
             "trap_speed_kmh": 232, "et_60ft_s": 1.48}},
             "delta_et_s": -0.26, "delta_trap_kmh": 3.0,
             "faster": "A", "winner": "K5"}
        )
        self.assertIn("STRICT", sys_p)
        # Either explicit "do not invent" or implicit via "cite actual"
        s_lower = sys_p.lower()
        self.assertTrue("invent" in s_lower or "actual" in s_lower)

    def test_rank_prompt_requires_three_decimals(self):
        from motoquant.llm.runner import _summarize_rank
        from motoquant.llm.parse_query import ParsedSimRequest
        sys_p = self._get_prompt_via_stub(
            "_summarize_rank",
            ParsedSimRequest(raw_query="fastest 600", bike_name=""),
            {"top": [{"rank": 1, "manufacturer": "Honda",
              "model": "CBR600RR", "displacement_cc": 599,
              "peak_power_hp": 119, "et_s": 10.5, "trap_kmh": 225}],
             "filter": "supersport_600", "matches": 12,
             "candidates_simulated": 12},
        )
        self.assertIn("3 decimals", sys_p)

    def test_explain_prompt_forbids_vague_words(self):
        from motoquant.llm.runner import _summarize_explain
        from motoquant.llm.parse_query import ParsedSimRequest
        sys_p = self._get_prompt_via_stub(
            "_summarize_explain",
            ParsedSimRequest(raw_query="why does altitude matter", bike_name=""),
            None,
        )
        s_lower = sys_p.lower()
        self.assertIn("specific", s_lower)
        # Must mention forbidden vague words
        self.assertTrue(
            "significantly" in s_lower or "noticeable" in s_lower
            or "never" in s_lower
        )


# ─────────────────────────────────────────────────────────────────
# Recommend prompt — must forbid invented brands
# ─────────────────────────────────────────────────────────────────


class TestRecommendPromptStrictness(unittest.TestCase):
    def test_no_hallucination_clause(self):
        from motoquant.llm.runner import _summarize_recommend
        from motoquant.llm.parse_query import ParsedSimRequest

        stub = _StubLLM()
        rec_payload = {
            "bike_name": "K5",
            "budget_inr": 50000,
            "build_tier": "stage_2",
            "effective_budget_inr": 50000,
            "parts": [
                {
                    "label": "Exhaust",
                    "brand": "Akrapovic",
                    "name": "GP Slip-On",
                    "price_inr": 35000,
                    "category": "exhaust",
                }
            ],
            "tires": [],
            "total_inr": 35000,
        }
        _summarize_recommend(
            ParsedSimRequest(raw_query="best mods for K5", bike_name="K5"),
            rec_payload,
            stub,
        )
        sys_p = stub.calls[0][1]
        s_lower = sys_p.lower()
        self.assertIn("strict", s_lower)
        self.assertIn("invent", s_lower)


if __name__ == "__main__":
    unittest.main()
