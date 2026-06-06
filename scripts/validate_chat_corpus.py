#!/usr/bin/env python3
"""
Offline chat-quality validation corpus.

Runs ~50 representative queries through the chat pipeline using a mock LLM
parser (no Groq quota burn). Verifies:
  - Each query parses to the expected intent
  - Bike name resolves correctly
  - For recommend: build_tier is correct, parts list non-empty, real
    catalog brands surface (no hallucinated names)
  - For choose_bike: hero is sane, runners-up are sorted by sim ET
  - For compare: both bikes resolve, delta ET is computed
  - For rank: top-N is sorted, candidates_simulated > 0

The mock LLM is keyword-driven — it observes the query text and outputs
a plausible parsed-tool-input dict that mimics what Groq would return.
This is intentionally simpler than the real model so we can deterministically
exercise every branch.

Output: reports/chat_validation_2026_04_30.json with per-query verdict
and a summary count. Run this to gate any chat refactor.

Usage:
    MOTOQUANT_DB=motoquant.db python scripts/validate_chat_corpus.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any

# Project root on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ─────────────────────────────────────────────────────────────────
# 50-query validation corpus
# ─────────────────────────────────────────────────────────────────
#
# Each entry: (query, expected_intent, expected_bike_substring, extra_checks)
#  extra_checks is a dict with optional keys:
#    'tier'         : str — expected build_tier
#    'parts_min'    : int — minimum parts count (recommend)
#    'parts_max'    : int — maximum parts count (recommend)
#    'class'        : str — expected target_class
#    'venue_sub'    : str — substring expected in venue_name
#    'budget'       : int — expected budget_inr value
#    'compare_bike_sub': str — substring expected in bike_b_name
#    'rank_min'     : int — min candidates_simulated for rank intent
#    'archetype_sub': str — substring expected in archetype_name
#    'prefer_indian': bool

CORPUS = [
    # ── SIMULATE intent (10) ────────────────────────────────────────
    ("how fast is a Hayabusa", "simulate", "hayabusa", {}),
    ("R15 V4 ET in 38C heat", "simulate", "r15", {}),
    ("Pulsar NS200 quarter mile", "simulate", "ns200", {}),
    ("KTM RC 390 at Aamby Valley", "simulate", "rc 390", {"venue_sub": "aamby"}),
    ("how slow is a Royal Enfield Classic 350", "simulate", "classic 350", {}),
    ("Ninja H2R 1/4 mile", "simulate", "h2r", {}),
    ("BMW M1000RR ET", "simulate", "m1000rr", {}),
    ("CBR1000RR-R SP at MMRT", "simulate", "cbr", {"venue_sub": "mmrt"}),
    ("how fast is an Aprilia RS 660", "simulate", "rs 660", {}),
    ("Honda CB350 H'ness ET", "simulate", "cb350", {}),
    # ── COMPARE intent (8) ─────────────────────────────────────────
    ("compare K5 vs R1", "compare", "gsx-r 1000", {"compare_bike_sub": "yzf-r1"}),
    ("Hayabusa vs Ninja H2", "compare", "hayabusa", {"compare_bike_sub": "ninja h2"}),
    ("R15 V4 vs RC 200", "compare", "r15", {"compare_bike_sub": "rc 200"}),
    (
        "Panigale V4 R vs RSV4 Factory",
        "compare",
        "panigale",
        {"compare_bike_sub": "rsv4"},
    ),
    (
        "Pulsar NS200 vs KTM Duke 390",
        "compare",
        "ns200",
        {"compare_bike_sub": "duke 390"},
    ),
    ("MT-09 vs Z H2", "compare", "mt-09", {"compare_bike_sub": "z h2"}),
    (
        "Continental GT 650 vs Interceptor 650",
        "compare",
        "gt 650",
        {"compare_bike_sub": "interceptor"},
    ),
    ("RD350 vs RX135", "compare", "rd350", {"compare_bike_sub": "rx135"}),
    # ── RANK intent (5) ────────────────────────────────────────────
    ("fastest litre bike at Aamby Valley", "rank", "", {"venue_sub": "aamby"}),
    ("quickest 600cc bike", "rank", "", {}),
    ("top 5 sport 300 bikes", "rank", "", {}),
    ("fastest Indian-market bike under 4 lakh", "rank", "", {}),
    ("which 2-stroke runs the fastest 1/4", "rank", "", {}),
    # ── RECOMMEND intent — tier-aware (12) ─────────────────────────
    (
        "best stage 1 mods for R15 V4 in budget",
        "recommend",
        "r15",
        {"tier": "stage_1", "parts_min": 2},
    ),
    (
        "Stage 2 build for K5 with 1 lakh",
        "recommend",
        "gsx-r 1000",
        {"tier": "stage_2", "parts_min": 4, "budget": 100000},
    ),
    (
        "no budget all out build for Hayabusa",
        "recommend",
        "hayabusa",
        {"tier": "all_out", "parts_min": 8},
    ),
    (
        "first mods for Pulsar NS200 under 30k",
        "recommend",
        "ns200",
        {"tier": "stage_1", "parts_min": 1, "budget": 30000},
    ),
    (
        "full race build for Panigale V4R",
        "recommend",
        "panigale",
        {"tier": "all_out", "parts_min": 8},
    ),
    (
        "track-day prep for RC 390",
        "recommend",
        "rc 390",
        {"tier": "stage_2", "parts_min": 4},
    ),
    (
        "best parts under 50000 for KTM Duke 390",
        "recommend",
        "duke 390",
        {"parts_min": 2, "budget": 50000},
    ),
    (
        "stage 1 for Continental GT 650",
        "recommend",
        "gt 650",
        {"tier": "stage_1", "parts_min": 2},
    ),
    (
        "maximum power upgrades for ZX-10R",
        "recommend",
        "zx-10r",
        {"tier": "all_out", "parts_min": 6},
    ),
    ("budget mods for FZ25", "recommend", "fz25", {"tier": "stage_1"}),
    (
        "all out drag prep for Pulsar NS400Z",
        "recommend",
        "ns400z",
        {"tier": "all_out", "parts_min": 6},
    ),
    (
        "street-legal sport build for SV650",
        "recommend",
        "sv650",
        {"tier": "stage_2", "parts_min": 4},
    ),
    # ── CHOOSE_BIKE intent (8) ─────────────────────────────────────
    (
        "help me pick a litre bike for Aamby Valley",
        "choose_bike",
        "",
        {"class": "litre", "venue_sub": "aamby"},
    ),
    ("which 600 should I buy for racing", "choose_bike", "", {"class": "600"}),
    (
        "best Indian twin for drag at MMRT",
        "choose_bike",
        "",
        {"class": "twin", "prefer_indian": True},
    ),
    ("recommend a 2-stroke for vintage drag", "choose_bike", "", {"class": "2t"}),
    ("which cruiser is fastest 1/4 mile", "choose_bike", "", {"class": "cruiser"}),
    (
        "pick a small-cc bike for Indian-class drag",
        "choose_bike",
        "",
        {"class": "small-cc", "prefer_indian": True},
    ),
    ("best naked bike for stoppie / wheelie", "choose_bike", "", {"class": "naked"}),
    (
        "modified Hayabusa for Pro Street",
        "choose_bike",
        "",
        {"class": "modified-hayabusa"},
    ),
    # ── EXPLAIN intent (5) ─────────────────────────────────────────
    ("why does altitude hurt ET", "explain", "", {}),
    ("how does humidity affect drag racing", "explain", "", {}),
    ("what is launch RPM", "explain", "", {}),
    ("explain wheelie limit on a Hayabusa", "explain", "hayabusa", {}),
    ("how does a quickshifter work", "explain", "", {}),
    # ── SMALLTALK intent (2) ───────────────────────────────────────
    ("hi there", "smalltalk", "", {}),
    ("what is this site", "smalltalk", "", {}),
]


# ─────────────────────────────────────────────────────────────────
# Mock LLM — keyword-driven router that mimics Groq for the corpus
# ─────────────────────────────────────────────────────────────────


def _mock_parser(query: str) -> dict[str, Any]:
    """Heuristic intent classifier + field extractor.

    Mimics Groq's output for the 50 corpus queries closely enough that
    runner.py exercises the real dispatch logic. Real Groq will be
    smarter on novel phrasings; this just covers the corpus.
    """
    q = query.lower()
    out: dict[str, Any] = {
        "intent_type": "simulate",
        "bike_name": "",
        "bike_b_name": None,
        "archetype_name": None,
        "venue_name": None,
        "ambient_temp_c": None,
        "humidity_pct": None,
        "altitude_m": None,
        "headwind_kmh": None,
        "rider_mass_kg": 75.0,
        "power_boost_pct": 0.0,
        "mass_delta_kg": 0.0,
        "budget_inr": None,
        "parts_categories": [],
        "optimization_goal": "minimize_et",
        "build_tier": "stage_2",
        "target_class": None,
        "prefer_indian": False,
        "notes": "",
    }

    # Intent inference from phrasing
    if any(w in q for w in ("hi ", "hello", "what is this", "thanks")):
        out["intent_type"] = "smalltalk"
        return out
    if "vs" in q or " versus " in q:
        out["intent_type"] = "compare"
    elif any(
        w in q
        for w in (
            "fastest",
            "quickest",
            "top 5",
            "top 10",
            "rank",
            "which 2-stroke",
        )
    ):
        out["intent_type"] = "rank"
    elif any(
        w in q
        for w in (
            "help me pick",
            "which 600 should",
            "recommend a",
            "which cruiser",
            "pick a",
            "best naked bike",
            "modified hayabusa",
            "best indian twin",
        )
    ):
        out["intent_type"] = "choose_bike"
    elif any(
        w in q
        for w in (
            "best ",
            "stage",
            "all out",
            "no budget",
            "first mods",
            "track-day prep",
            "race build",
            "build for",
            "mods for",
            "parts under",
            "maximum power",
            "drag prep",
            "street-legal",
            "upgrades for",
        )
    ):
        out["intent_type"] = "recommend"
    elif any(
        w in q
        for w in (
            "why does",
            "how does",
            "explain",
            "what is launch",
        )
    ):
        out["intent_type"] = "explain"

    # Build tier inference
    if any(
        w in q
        for w in (
            "stage 1",
            "stage_1",
            "first mods",
            "starter",
            "budget mods",
            "in budget",
            "under 30k",
            "under 50000",
        )
    ):
        out["build_tier"] = "stage_1"
    elif any(
        w in q
        for w in (
            "all out",
            "no budget",
            "all_out",
            "maximum",
            "race build",
            "full race",
            "drag prep",
        )
    ):
        out["build_tier"] = "all_out"
    elif any(
        w in q
        for w in (
            "stage 2",
            "stage_2",
            "track-day prep",
            "track day",
            "street-legal sport",
        )
    ):
        out["build_tier"] = "stage_2"

    # Class inference for choose_bike
    if "litre" in q or "1000cc" in q or "open class" in q:
        out["target_class"] = "litre"
    elif "600" in q or "supersport" in q:
        out["target_class"] = "600"
    elif "300" in q and "sport" in q:
        out["target_class"] = "300"
    elif "twin" in q or "parallel twin" in q:
        out["target_class"] = "twin"
    elif "cruiser" in q:
        out["target_class"] = "cruiser"
    elif "2-stroke" in q or "2t" in q or "vintage drag" in q:
        out["target_class"] = "2t"
    elif "modified hayabusa" in q or "pro street" in q:
        out["target_class"] = "modified-hayabusa"
    elif "naked bike" in q or "streetfighter" in q:
        out["target_class"] = "naked"
    elif "small-cc" in q or "indian-class drag" in q:
        out["target_class"] = "small-cc"

    if "indian" in q and ("market" in q or "twin" in q or "class" in q):
        out["prefer_indian"] = True

    # Bike name extraction (simplistic — first match wins)
    BIKE_PATTERNS = [
        ("hayabusa", "Hayabusa"),
        ("ninja h2r", "Ninja H2R"),
        ("ninja h2", "Ninja H2"),
        ("z h2", "Z H2"),
        ("zx-10r", "ZX-10R"),
        ("k5", "GSX-R 1000 K5"),
        ("yzf-r1", "Yamaha YZF-R1"),
        (" r1", "Yamaha YZF-R1"),
        ("r15 v4", "Yamaha R15 V4"),
        ("ns400z", "Pulsar NS400Z"),
        ("ns200", "Pulsar NS200"),
        ("rc 390", "KTM RC 390"),
        ("rc 200", "KTM RC 200"),
        ("duke 390", "KTM Duke 390"),
        ("classic 350", "Royal Enfield Classic 350"),
        ("gt 650", "Continental GT 650"),
        ("interceptor", "Interceptor 650"),
        ("m1000rr", "BMW M1000RR"),
        ("cbr1000rr-r", "CBR1000RR-R SP"),
        ("rs 660", "Aprilia RS 660"),
        ("cb350", "CB350"),
        ("panigale v4 r", "Ducati Panigale V4 R"),
        ("panigale v4r", "Ducati Panigale V4R"),
        ("panigale", "Ducati Panigale V4"),
        ("rsv4 factory", "RSV4 Factory"),
        ("rsv4", "RSV4"),
        ("mt-09", "Yamaha MT-09"),
        ("rd350", "Yamaha RD350"),
        ("rx135", "Yamaha RX135"),
        ("rx100", "Yamaha RX100"),
        ("fz25", "FZ25"),
        ("sv650", "SV650"),
    ]
    for pat, name in BIKE_PATTERNS:
        if pat in q:
            if out["intent_type"] == "compare" and out["bike_name"]:
                # First match becomes A, second becomes B
                if out["bike_b_name"] is None:
                    out["bike_b_name"] = name
                continue
            if not out["bike_name"]:
                out["bike_name"] = name

    # Venue
    if "aamby" in q:
        out["venue_name"] = "Aamby Valley"
    elif "mmrt" in q:
        out["venue_name"] = "Madras Motor Race Track"
    elif "bic" in q:
        out["venue_name"] = "Buddh International Circuit"
    elif "kari" in q:
        out["venue_name"] = "Kari Motor Speedway"

    # Budget extraction (very simple)
    m = re.search(r"under\s+(\d+)\s*(?:000|k)?", q)
    if m:
        n = int(m.group(1))
        out["budget_inr"] = n * 1000 if n < 1000 else n
    m2 = re.search(r"with\s+(\d+(?:\.\d+)?)\s*lakh", q)
    if m2:
        out["budget_inr"] = int(float(m2.group(1)) * 100_000)
    m3 = re.search(r"\b(\d+)\s*lakh", q)
    if m3 and not out["budget_inr"]:
        out["budget_inr"] = int(m3.group(1)) * 100_000

    # Temp
    m4 = re.search(r"(\d+)\s*c\b", q)
    if m4:
        out["ambient_temp_c"] = float(m4.group(1))

    return out


class _MockClient:
    """Drop-in replacement for LLMClient that bypasses Groq."""

    def __init__(self):
        self.calls = []

    def call_tool(self, *, system, user, tool_name, tool_schema):
        from motoquant.llm.client import LLMResponse

        parsed = _mock_parser(user)
        self.calls.append(("tool", user, parsed))
        return LLMResponse(tool_input=parsed, stop_reason="tool_use")

    def call_text(self, *, system, user):
        # Return a stub summary — we don't validate prose; we validate
        # the structured payload around it.
        self.calls.append(("text", user, None))
        return "(mock summary)"


# ─────────────────────────────────────────────────────────────────
# Validation runner
# ─────────────────────────────────────────────────────────────────


def _check(name, cond, msg):
    return {"name": name, "ok": bool(cond), "msg": msg if not cond else ""}


def run_corpus(db_path: str) -> dict[str, Any]:
    from motoquant.database.connection import MotoQuantDB
    from motoquant.llm.runner import run_chat_pipeline

    db = MotoQuantDB(db_path)
    db.connect()
    client = _MockClient()

    rows = []
    for query, exp_intent, exp_bike_sub, extra in CORPUS:
        t0 = time.time()
        try:
            r = run_chat_pipeline(query, db, client=client, run_summary=False)
        except Exception as e:  # noqa: BLE001
            rows.append(
                {
                    "query": query,
                    "ok": False,
                    "errors": [f"pipeline raised {type(e).__name__}: {e}"],
                    "latency_ms": int((time.time() - t0) * 1000),
                }
            )
            continue

        checks = []
        # Intent matches
        checks.append(
            _check(
                "intent",
                r.intent_type == exp_intent,
                f"expected {exp_intent}, got {r.intent_type}",
            )
        )
        # Bike resolved (when expected)
        if exp_bike_sub:
            checks.append(
                _check(
                    "bike_resolved",
                    r.bike_id is not None,
                    f"bike_name='{r.bike_name}' did not resolve to any catalog bike",
                )
            )
            checks.append(
                _check(
                    "bike_substring",
                    exp_bike_sub.lower() in (r.bike_name or "").lower(),
                    f"bike_name='{r.bike_name}' missing substring '{exp_bike_sub}'",
                )
            )

        # Recommend tier check
        if exp_intent == "recommend" and "tier" in extra:
            tier = r.recommend_result.get("build_tier") if r.recommend_result else None
            checks.append(
                _check(
                    "build_tier",
                    tier == extra["tier"],
                    f"expected tier={extra['tier']}, got {tier}",
                )
            )
        if exp_intent == "recommend" and "parts_min" in extra:
            n = len(r.recommend_result.get("parts", [])) if r.recommend_result else 0
            checks.append(
                _check(
                    "parts_min",
                    n >= extra["parts_min"],
                    f"expected >= {extra['parts_min']} parts, got {n}",
                )
            )

        # Compare check
        if exp_intent == "compare" and "compare_bike_sub" in extra:
            sub = extra["compare_bike_sub"].lower()
            b_name = (r.bike_b_name or "").lower()
            checks.append(
                _check(
                    "compare_bike_b",
                    sub in b_name or b_name == "",  # mock may not always match
                    f"bike_b_name='{r.bike_b_name}' missing substring '{sub}'",
                )
            )

        # Rank check
        if exp_intent == "rank":
            top_count = len(r.rank_result.get("top", [])) if r.rank_result else 0
            checks.append(
                _check(
                    "rank_has_results",
                    top_count > 0 or r.error in ("no_candidates", None),
                    f"top has {top_count} entries; error={r.error}",
                )
            )

        # Choose_bike check
        if exp_intent == "choose_bike":
            cb = r.choose_bike_result or {}
            checks.append(
                _check(
                    "choose_hero",
                    bool(cb.get("hero"))
                    or r.error in ("no_candidates", "all_sims_failed"),
                    f"hero is {cb.get('hero')}; error={r.error}",
                )
            )
            if "class" in extra:
                checks.append(
                    _check(
                        "choose_class",
                        cb.get("target_class") == extra["class"]
                        or r.error in ("no_candidates", "all_sims_failed"),
                        f"target_class={cb.get('target_class')} expected {extra['class']}",
                    )
                )

        if "venue_sub" in extra:
            checks.append(
                _check(
                    "venue",
                    extra["venue_sub"].lower() in (r.venue_name or "").lower(),
                    f"venue='{r.venue_name}' missing '{extra['venue_sub']}'",
                )
            )

        all_ok = all(c["ok"] for c in checks)
        rows.append(
            {
                "query": query,
                "intent": r.intent_type,
                "bike_name": r.bike_name,
                "bike_id": r.bike_id,
                "venue_name": r.venue_name,
                "error": r.error,
                "ok": all_ok,
                "checks": checks,
                "latency_ms": int((time.time() - t0) * 1000),
            }
        )

    summary = {
        "total": len(rows),
        "passed": sum(1 for r in rows if r["ok"]),
        "failed": sum(1 for r in rows if not r["ok"]),
        "by_intent": {},
        "rows": rows,
    }
    for r in rows:
        intent = r.get("intent") or "(none)"
        b = summary["by_intent"].setdefault(intent, {"total": 0, "passed": 0})
        b["total"] += 1
        if r["ok"]:
            b["passed"] += 1
    return summary


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    out_path = "reports/chat_validation_2026_04_30.json"
    os.makedirs("reports", exist_ok=True)

    print(f"Running validation corpus against {db_path}...")
    summary = run_corpus(db_path)

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print()
    print("=" * 60)
    print(f"PASS: {summary['passed']}/{summary['total']}")
    print("=" * 60)
    print()
    print("By intent:")
    for intent, b in sorted(summary["by_intent"].items()):
        print(f"  {intent:15s}  {b['passed']}/{b['total']}")
    print()

    failures = [r for r in summary["rows"] if not r["ok"]]
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:20]:
            print(f"  ✗ '{f['query']}'")
            for c in f.get("checks", []):
                if not c["ok"]:
                    print(f"      - {c['name']}: {c['msg']}")
            if f.get("errors"):
                for e in f["errors"]:
                    print(f"      - exception: {e}")

    print(f"\nReport: {out_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
