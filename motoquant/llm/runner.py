"""
Chat pipeline — orchestrates parse → resolve → dispatch-by-intent → summarize.

Intents (set by parse_query.py via the LLM tool-use call):
  simulate  : run the physics engine for one specific bike
  compare   : run two bikes side-by-side
  rank      : list top-N bikes filtered by criteria (catalog query, no sim)
  recommend : suggest parts/mods for a bike + budget (calls recommend_build)
  explain   : LLM answers a tuning/physics question; bike_id optional
  smalltalk : minimal LLM response, no sim

This module is the single source of truth shared by:
  - CLI: `python -m motoquant chat "..."` (motoquant/run.py::cmd_chat)
  - HTTP: POST /api/chat (motoquant/api.py)

Both call run_chat_pipeline() with structured input and consume the typed
ChatResult — no printing or HTTP coupling lives in this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from ..constants import MS_TO_KMH, MS_TO_MPH
from ..physics import MotoQuantEngine
from .client import LLMClient, LLMNotConfiguredError
from .parse_query import ParsedSimRequest, parse_query
from .summarize import summarize_result

__all__ = ["ChatResult", "run_chat_pipeline"]


# ───────────────────────────────────────────────────────────────────
# ChatResult — structured return value
# ───────────────────────────────────────────────────────────────────


@dataclass
class ChatResult:
    """End-to-end result of a chat query.

    Sentinel semantics:
      error == None and intent_type / payload populated → success
      error == "bike_not_found"          → use bike_suggestions
      error == "llm_not_configured"      → API key missing
      error == "parse_failed"            → LLM refused / bad response
      error == "sim_failed"              → physics blew up
    """

    raw_query: str
    intent_type: str = "simulate"

    # Common parse fields
    bike_name: str = ""
    bike_id: int | None = None
    bike_b_name: str | None = None
    bike_b_id: int | None = None
    venue_name: str | None = None
    venue_id: int | None = None
    parsed_notes: str = ""
    optimization_goal: str = "minimize_et"

    # bike_not_found path
    bike_suggestions: list[dict[str, Any]] = field(default_factory=list)

    # Intent-specific payloads
    sim_result: dict[str, Any] | None = None  # simulate
    compare_result: dict[str, Any] | None = None  # compare
    rank_result: dict[str, Any] | None = None  # rank
    recommend_result: dict[str, Any] | None = None  # recommend
    explain_result: dict[str, Any] | None = None  # explain

    summary: str | None = None

    error: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ───────────────────────────────────────────────────────────────────
# Public entry point
# ───────────────────────────────────────────────────────────────────


def run_chat_pipeline(
    query: str,
    db: Any,
    *,
    client: LLMClient | None = None,
    run_summary: bool = True,
    suggestion_limit: int = 5,
) -> ChatResult:
    """End-to-end: parse → resolve → dispatch on intent → summarize."""
    result = ChatResult(raw_query=query)

    # ── 1. Parse ────────────────────────────────────────────────────
    try:
        parsed = parse_query(query, db=db, client=client)
    except LLMNotConfiguredError as e:
        result.error = "llm_not_configured"
        result.error_detail = str(e)
        return result
    except Exception as e:  # noqa: BLE001
        result.error = "parse_failed"
        result.error_detail = f"{type(e).__name__}: {e}"
        return result

    # Plumb fields onto result
    result.intent_type = parsed.intent_type
    result.bike_name = parsed.bike_name
    result.bike_id = parsed.bike_id
    result.bike_b_name = parsed.bike_b_name
    result.bike_b_id = parsed.bike_b_id
    result.venue_name = parsed.venue_name
    result.venue_id = parsed.venue_id
    result.parsed_notes = parsed.notes
    result.optimization_goal = parsed.optimization_goal

    # ── 2. Dispatch on intent ───────────────────────────────────────
    intent = parsed.intent_type
    if intent == "smalltalk":
        return _run_smalltalk(parsed, client, result)
    if intent == "explain":
        return _run_explain(parsed, db, client, result, run_summary=run_summary)
    if intent == "rank":
        return _run_rank(parsed, db, client, result, run_summary=run_summary)
    if intent == "compare":
        return _run_compare(
            parsed, db, client, result,
            run_summary=run_summary, suggestion_limit=suggestion_limit,
        )
    if intent == "recommend":
        return _run_recommend(
            parsed, db, client, result,
            run_summary=run_summary, suggestion_limit=suggestion_limit,
        )
    # default → simulate
    return _run_simulate(
        parsed, db, client, result,
        run_summary=run_summary, suggestion_limit=suggestion_limit,
    )


# ───────────────────────────────────────────────────────────────────
# Intent: SIMULATE  (one bike, run physics engine)
# ───────────────────────────────────────────────────────────────────


def _run_simulate(
    parsed: ParsedSimRequest,
    db: Any,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
    suggestion_limit: int,
) -> ChatResult:
    if parsed.bike_id is None:
        result.error = "bike_not_found"
        result.error_detail = (
            f"Could not match '{parsed.bike_name}' to any bike in the catalog."
        )
        result.bike_suggestions = _bike_suggestions(
            db, parsed.bike_name, limit=suggestion_limit
        )
        return result

    sim_dict = _run_one_sim(parsed.bike_id, parsed, db)
    if isinstance(sim_dict, str):
        result.error = "sim_failed"
        result.error_detail = sim_dict
        return result

    result.sim_result = sim_dict

    if run_summary:
        try:
            result.summary = summarize_result(parsed, sim_dict, client=client)
        except Exception as e:  # noqa: BLE001
            result.summary = f"(summary failed: {type(e).__name__}: {e})"

    return result


# ───────────────────────────────────────────────────────────────────
# Intent: COMPARE  (two bikes side-by-side)
# ───────────────────────────────────────────────────────────────────


def _run_compare(
    parsed: ParsedSimRequest,
    db: Any,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
    suggestion_limit: int,
) -> ChatResult:
    # Need both bikes resolved
    missing = []
    if parsed.bike_id is None:
        missing.append(("A", parsed.bike_name))
    if parsed.bike_b_id is None:
        missing.append(("B", parsed.bike_b_name or "(none)"))

    if missing:
        result.error = "bike_not_found"
        result.error_detail = "Could not match bike: " + ", ".join(
            f"{slot}='{name}'" for slot, name in missing
        )
        # Combine suggestions for whichever side is missing
        sugg: list[dict[str, Any]] = []
        for slot, name in missing:
            sugg.extend(_bike_suggestions(db, name, limit=suggestion_limit))
        seen: set[int] = set()
        result.bike_suggestions = [
            r for r in sugg
            if r.get("id") and not (r["id"] in seen or seen.add(r["id"]))
        ][:suggestion_limit]
        return result

    sim_a = _run_one_sim(parsed.bike_id, parsed, db)
    sim_b = _run_one_sim(parsed.bike_b_id, parsed, db)
    if isinstance(sim_a, str):
        result.error = "sim_failed"
        result.error_detail = f"Bike A sim failed: {sim_a}"
        return result
    if isinstance(sim_b, str):
        result.error = "sim_failed"
        result.error_detail = f"Bike B sim failed: {sim_b}"
        return result

    delta_et = sim_a["et_quarter_s"] - sim_b["et_quarter_s"]
    delta_trap = sim_a["trap_speed_kmh"] - sim_b["trap_speed_kmh"]
    if delta_et < 0:
        faster = "A"
    elif delta_et > 0:
        faster = "B"
    else:
        faster = "tie"

    result.compare_result = {
        "a": {
            "bike_id": parsed.bike_id,
            "bike_name": parsed.bike_name,
            "sim": sim_a,
        },
        "b": {
            "bike_id": parsed.bike_b_id,
            "bike_name": parsed.bike_b_name,
            "sim": sim_b,
        },
        "delta_et_s": round(delta_et, 4),
        "delta_trap_kmh": round(delta_trap, 1),
        "faster": faster,
    }

    if run_summary:
        try:
            result.summary = _summarize_compare(parsed, result.compare_result, client)
        except Exception as e:  # noqa: BLE001
            result.summary = f"(compare summary failed: {type(e).__name__}: {e})"

    return result


# ───────────────────────────────────────────────────────────────────
# Intent: RANK  (catalog query, no sim)
# ───────────────────────────────────────────────────────────────────


def _run_rank(
    parsed: ParsedSimRequest,
    db: Any,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
) -> ChatResult:
    """Catalog filter + actual sims on top candidates.

    1. Parse query for displacement/category/'stock'/'modded' keywords.
    2. Fetch matching catalog rows.
    3. Take top-N by power-to-weight (rough first cut).
    4. RUN REAL SIMS on those N bikes via MotoQuantEngine — venue-aware.
    5. Sort by sim ET ascending; return top 10 with sim numbers.

    This is slower than a pure-DB query (~80-150ms per sim × 12-15 candidates
    = ~1.5-2s) but gives physics-correct ranking that handles cases where
    raw P/W misleads (e.g., supercharged H2 with launch traction limits,
    or year-newer revs where peak_power_hp is similar but gearing changed).
    """
    try:
        rq = (parsed.raw_query or "").lower()
        kw: dict[str, Any] = {"limit": 400}

        # ── Displacement keywords (order matters: longer matches first) ──
        disp_filters = [
            # exact-cc
            ("125cc", 110, 135),
            ("150cc", 140, 170),
            ("200cc", 180, 220),
            ("250cc", 220, 280),
            ("300cc", 280, 350),
            ("400cc", 380, 460),
            ("450cc", 420, 500),
            ("500cc", 480, 560),
            ("600cc", 580, 700),
            ("650cc", 630, 720),
            ("750cc", 720, 800),
            ("1000cc", 950, 1100),
            ("1300cc", 1250, 1400),
            # class names — 'litre/liter' = stock 1000cc; user query example
            # "fastest litre class" should map to 950-1100, EXCLUDING 1340cc Hayabusa.
            ("litre class", 950, 1100),
            ("liter class", 950, 1100),
            ("litre", 950, 1100),
            ("liter", 950, 1100),
            ("open class", 950, 1400),  # MotoGP "open" historically up to 1000+
            ("middleweight", 580, 800),
            ("supersport", 580, 800),
            ("hyperbike", 1100, 1500),
            ("muscle", 1500, 2500),
        ]
        for needle, lo, hi in disp_filters:
            if needle in rq:
                kw["displacement_min"] = lo
                kw["displacement_max"] = hi
                break

        # ── Category keywords ──
        for needle, cat in [
            ("naked", "naked"), ("cruiser", "cruiser"),
            ("adventure", "adventure"), ("touring", "touring"),
            ("scooter", "scooter"), ("sport", "sport"),
        ]:
            if needle in rq:
                kw["category"] = cat
                break

        rows = db.bikes.search(**kw) or []

        # ── Pre-rank: power-to-weight ascending (best P/W first) ──
        def _ptw(r):
            hp = r.get("peak_power_hp") or 0
            mass = r.get("dry_mass_kg") or 999
            try:
                return float(hp) / max(float(mass), 1.0)
            except (TypeError, ValueError):
                return 0.0

        rows.sort(key=_ptw, reverse=True)
        top_pool = rows[:15]  # candidates we will actually simulate

        # ── Run real sims on each candidate ──
        env = None
        if parsed.venue_id is not None:
            try:
                env = db.venues.to_environment(
                    parsed.venue_id, month=datetime.now().month
                )
            except Exception:
                env = None

        sim_rows: list[dict[str, Any]] = []
        for r in top_pool:
            bike_id = r["id"]
            try:
                config_row = db.bikes.get_current_config(bike_id)
                if config_row is None:
                    # No config seeded for this bike — fall back to validation_et_s
                    et = r.get("validation_et_s")
                    sim_rows.append(
                        {**r, "sim_et_s": float(et) if et else None,
                         "sim_trap_kmh": None, "sim_source": "validation"}
                    )
                    continue
                config = db.bikes.to_config(config_row["id"], environment=env)
                if config is None:
                    sim_rows.append({**r, "sim_et_s": None, "sim_source": "no-config"})
                    continue
                _apply_env_overrides(config, parsed)
                _apply_archetype(config, parsed, db)
                _apply_power_boost(config, parsed)
                engine = MotoQuantEngine(config)
                sim = engine.run()
                sim_rows.append({
                    **r,
                    "sim_et_s": round(float(sim.time_quarter), 3),
                    "sim_trap_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
                    "sim_60ft_s": round(float(sim.time_60ft), 3),
                    "sim_source": "engine",
                })
            except Exception:
                # Fall back to validation if sim fails
                et = r.get("validation_et_s")
                sim_rows.append({
                    **r,
                    "sim_et_s": float(et) if et else None,
                    "sim_trap_kmh": None,
                    "sim_source": "validation-fallback",
                })

        # Final sort: by sim_et_s ascending, None last
        def _final_key(r):
            et = r.get("sim_et_s")
            if et is None:
                return (1, 999.0)
            return (0, float(et))

        sim_rows.sort(key=_final_key)
        top_n = sim_rows[:10]

        result.rank_result = {
            "filter": {k: v for k, v in kw.items() if k != "limit"},
            "matches": len(rows),
            "candidates_simulated": len(top_pool),
            "top": [
                {
                    "rank": i + 1,
                    "bike_id": r["id"],
                    "manufacturer": r.get("manufacturer_name"),
                    "model": r.get("model_name"),
                    "year_from": r.get("year_from"),
                    "displacement_cc": r.get("displacement_cc"),
                    "peak_power_hp": r.get("peak_power_hp"),
                    "dry_mass_kg": r.get("dry_mass_kg"),
                    "et_s": r.get("sim_et_s"),
                    "trap_kmh": r.get("sim_trap_kmh"),
                    "et_60ft_s": r.get("sim_60ft_s"),
                    "source": r.get("sim_source"),
                }
                for i, r in enumerate(top_n)
            ],
        }
    except Exception as e:  # noqa: BLE001
        result.error = "rank_failed"
        result.error_detail = f"{type(e).__name__}: {e}"
        return result

    if run_summary:
        try:
            result.summary = _summarize_rank(parsed, result.rank_result, client)
        except Exception as e:  # noqa: BLE001
            result.summary = f"(rank summary failed: {type(e).__name__}: {e})"

    return result


# ───────────────────────────────────────────────────────────────────
# Intent: RECOMMEND  (parts for budget)
# ───────────────────────────────────────────────────────────────────


# Priority categories the recommend handler picks across, in order. The
# tuple is (substring_to_match_in_category_name, display_label_for_prompt).
# We pick at most one part per category — keeps the build sheet focused.
_RECOMMEND_PRIORITY = [
    ("exhaust",          "Exhaust"),
    ("air_filter",       "Air filter"),
    ("ecu",              "ECU flash / piggyback"),
    ("fuel_system",      "Fuel system"),
    ("clutch",           "Clutch / slipper"),
    ("quickshifter",     "Quickshifter"),
    ("sprocket",         "Sprocket"),
    ("chain",            "Chain"),
    ("suspension",       "Suspension"),
    ("brakes",           "Brakes"),
    ("weight_reduction", "Weight reduction"),
    ("battery",          "Lightweight battery"),
]


def _run_recommend(
    parsed: ParsedSimRequest,
    db: Any,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
    suggestion_limit: int,
) -> ChatResult:
    if parsed.bike_id is None:
        result.error = "bike_not_found"
        result.error_detail = (
            f"Need a specific bike to recommend for. "
            f"Could not match '{parsed.bike_name}'."
        )
        result.bike_suggestions = _bike_suggestions(
            db, parsed.bike_name, limit=suggestion_limit
        )
        return result

    try:
        # 1. Pull catalog parts that pass the compatibility check for this bike.
        #    list_compatible_for_bike runs the FitmentMatch engine (manufacturer,
        #    engine config, displacement bounds, chain pitch, stroke type) so
        #    we don't surface a 1340cc Hayabusa exhaust on a 155cc R15.
        try:
            parts = db.parts.list_compatible_for_bike(parsed.bike_id) or []
        except Exception:
            parts = []

        budget = parsed.budget_inr
        if budget is not None:
            parts = [p for p in parts if (p.get("price_inr") or 0) <= budget]

        # 2. Optional category filter from the LLM-parsed query.
        if parsed.parts_categories:
            wanted = {c.lower() for c in parsed.parts_categories}
            parts = [
                p for p in parts
                if any(c in (p.get("category_name") or "").lower() for c in wanted)
            ]

        # 3. Group by canonical category, sort each by price descending so the
        #    "premium-tier" pick lands at the top of each bucket.
        by_cat: dict[str, list[dict[str, Any]]] = {}
        for p in parts:
            cat = (p.get("category_name") or "uncategorized").lower()
            by_cat.setdefault(cat, []).append(p)
        for lst in by_cat.values():
            lst.sort(key=lambda p: -float(p.get("price_inr") or 0))

        # 4. Walk the priority list and pick one part per category until budget
        #    is roughly spent (allow 20 % headroom — better to over-build than
        #    leave the user with a half-finished plan).
        selected: list[dict[str, Any]] = []
        used_budget = 0.0
        budget_cap = (budget * 1.2) if budget else float("inf")
        for cat_key, cat_label in _RECOMMEND_PRIORITY:
            # Find any cat_name in by_cat that contains the priority key
            candidates: list[dict[str, Any]] = []
            for cat_name, lst in by_cat.items():
                if cat_key in cat_name:
                    candidates.extend(lst)
            if not candidates:
                continue
            # Pick the highest-priced compatible candidate that still fits budget.
            for p in candidates:
                price = float(p.get("price_inr") or 0)
                if used_budget + price > budget_cap:
                    continue
                selected.append({"_label": cat_label, **p})
                used_budget += price
                break
            if used_budget >= (budget or 0) * 0.95 > 0:
                break

        # 5. Recommended-tier + drag-prep tire fitments — completely separate
        #    from the parts catalog. These are the BIG ROI swaps for drag day.
        tires: list[dict[str, Any]] = []
        try:
            for ftype in ("recommended", "drag_prep"):
                tires.extend(
                    db.tires.get_bike_fitments(parsed.bike_id, fitment_type=ftype)
                    or []
                )
        except Exception:
            pass
        if budget is not None:
            tires = [t for t in tires if (t.get("price_inr") or 0) <= budget]
        # Dedupe on tire_model_id; keep highest mu_peak first
        seen: set[int] = set()
        uniq: list[dict[str, Any]] = []
        for t in sorted(
            tires, key=lambda t: -float(t.get("mu_peak") or 0.0)
        ):
            tid = t.get("tire_model_id")
            if tid in seen:
                continue
            seen.add(tid)
            uniq.append(t)
        tires = uniq[:4]

        result.recommend_result = {
            "bike_id": parsed.bike_id,
            "bike_name": parsed.bike_name,
            "budget_inr": budget,
            "parts": [
                {
                    "part_id": p["id"],
                    "label": p.get("_label"),
                    "name": p.get("model_name"),
                    "brand": p.get("brand"),
                    "category": p.get("category_name"),
                    "category_display": p.get("category_display"),
                    "price_inr": p.get("price_inr"),
                    "fitment_reason": p.get("fitment_reason"),
                }
                for p in selected
            ],
            "tires": [
                {
                    "tire_model_id": t.get("tire_model_id"),
                    "manufacturer": t.get("tire_manufacturer"),
                    "model": t.get("model_name"),
                    "size": t.get("size_designation"),
                    "compound": t.get("compound_type"),
                    "mu_peak": t.get("mu_peak"),
                    "position": t.get("position"),
                    "fitment_type": t.get("fitment_type"),
                    "price_inr": t.get("price_inr"),
                }
                for t in tires
            ],
            "total_inr": (
                sum(float(p.get("price_inr") or 0) for p in selected)
                + sum(float(t.get("price_inr") or 0) for t in tires)
            ),
        }
    except Exception as e:  # noqa: BLE001
        result.error = "recommend_failed"
        result.error_detail = f"{type(e).__name__}: {e}"
        return result

    if run_summary:
        try:
            result.summary = _summarize_recommend(
                parsed, result.recommend_result, client
            )
        except Exception as e:  # noqa: BLE001
            result.summary = f"(recommend summary failed: {type(e).__name__}: {e})"

    return result


# ───────────────────────────────────────────────────────────────────
# Intent: EXPLAIN  (tuning/physics question)
# ───────────────────────────────────────────────────────────────────


def _run_explain(
    parsed: ParsedSimRequest,
    db: Any,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
) -> ChatResult:
    """Answer a tuning/physics question with optional sim grounding.

    If a specific bike was identified, run a quick sim and use its numbers as
    grounding for the explanation. Otherwise rely purely on the LLM.
    """
    sim_for_context: dict[str, Any] | None = None
    if parsed.bike_id is not None:
        sim = _run_one_sim(parsed.bike_id, parsed, db)
        if isinstance(sim, dict):
            sim_for_context = sim
            result.sim_result = sim

    if run_summary and client is not None:
        try:
            result.summary = _summarize_explain(parsed, sim_for_context, client)
        except Exception as e:  # noqa: BLE001
            result.summary = f"(explain failed: {type(e).__name__}: {e})"
    elif run_summary:
        # No client passed — try the default
        from .client import get_default_client
        try:
            result.summary = _summarize_explain(
                parsed, sim_for_context, get_default_client()
            )
        except Exception as e:  # noqa: BLE001
            result.summary = f"(explain failed: {type(e).__name__}: {e})"

    result.explain_result = {
        "has_sim_grounding": sim_for_context is not None,
        "bike_id": parsed.bike_id,
    }
    return result


# ───────────────────────────────────────────────────────────────────
# Intent: SMALLTALK  (greeting / off-topic)
# ───────────────────────────────────────────────────────────────────


def _run_smalltalk(
    parsed: ParsedSimRequest,
    client: LLMClient | None,
    result: ChatResult,
) -> ChatResult:
    msg = (
        "MotoQuant Pro: I'm a motorcycle drag-racing simulator. Ask me things "
        "like 'how fast is a Hayabusa', 'compare K5 vs R1', 'what's the fastest "
        "300cc bike', or 'best mods for R15 V4 under 30k'. I can simulate any of "
        "327 bikes across 20 venues with real physics."
    )
    result.summary = msg
    return result


# ───────────────────────────────────────────────────────────────────
# Sim helpers (shared by simulate/compare/explain)
# ───────────────────────────────────────────────────────────────────


def _run_one_sim(
    bike_id: int, parsed: ParsedSimRequest, db: Any
) -> dict[str, Any] | str:
    """Run a single sim for `bike_id` with `parsed`'s overrides applied.

    Returns a sim_dict on success or an error string on failure.
    """
    try:
        config_row = db.bikes.get_current_config(bike_id)
    except Exception as e:  # noqa: BLE001
        return f"db.bikes.get_current_config: {e}"
    if config_row is None:
        return f"No bike_configs row for bike_id {bike_id}"

    env = None
    if parsed.venue_id is not None:
        try:
            env = db.venues.to_environment(parsed.venue_id, month=datetime.now().month)
        except Exception:
            env = None

    try:
        config = db.bikes.to_config(config_row["id"], environment=env)
    except Exception as e:  # noqa: BLE001
        return f"db.bikes.to_config: {e}"
    if config is None:
        return f"to_config returned None for {config_row['id']}"

    _apply_env_overrides(config, parsed)
    _apply_archetype(config, parsed, db)
    _apply_power_boost(config, parsed)

    try:
        engine = MotoQuantEngine(config)
        sim = engine.run()
    except Exception as e:  # noqa: BLE001
        return f"MotoQuantEngine.run: {type(e).__name__}: {e}"

    out: dict[str, Any] = {
        # NOTE: key names are pinned by the frontend UIs (web ChatPanel +
        # desktop ChatBox). Do NOT rename — both surfaces look these up by
        # exact name.
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
        "trap_speed_mph": round(float(sim.speed_quarter) * MS_TO_MPH, 1),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "peak_accel_g": round(float(np.max(sim.a)), 2),
        # Bike + condition context for the summary prompt
        "bike_name": "",  # filled in by caller after _run_one_sim returns
    }
    for attr, key in (
        ("time_330ft", "et_330ft_s"),
        ("time_eighth", "et_eighth_s"),
        ("time_1000ft", "et_1000ft_s"),
    ):
        val = getattr(sim, attr, None)
        if val is not None:
            try:
                out[key] = round(float(val), 4)
            except (TypeError, ValueError):
                pass
    return out


def _apply_env_overrides(config: Any, parsed: ParsedSimRequest) -> None:
    """Mutate config.environment in place from parsed query overrides."""
    if parsed.ambient_temp_c is not None:
        config.environment.ambient_temp_c = float(parsed.ambient_temp_c)
    if parsed.humidity_pct is not None:
        config.environment.relative_humidity_pct = float(parsed.humidity_pct)
    if parsed.altitude_m is not None:
        config.environment.altitude_m = float(parsed.altitude_m)
    if parsed.headwind_kmh is not None:
        config.environment.wind_speed_ms = float(parsed.headwind_kmh) / 3.6
        config.environment.wind_direction_deg = 0


def _apply_power_boost(config: Any, parsed: ParsedSimRequest) -> None:
    """Scale stock power/torque by parsed.power_boost_pct."""
    if not parsed.power_boost_pct:
        return
    factor = 1.0 + float(parsed.power_boost_pct) / 100.0
    if hasattr(config.engine, "peak_power_hp") and config.engine.peak_power_hp:
        config.engine.peak_power_hp *= factor
    if hasattr(config.engine, "peak_torque_nm") and config.engine.peak_torque_nm:
        config.engine.peak_torque_nm *= factor
    dyno = getattr(config.engine, "dyno_curve", None)
    if dyno is not None and getattr(dyno, "torque_nm", None) is not None:
        dyno.torque_nm = [t * factor for t in dyno.torque_nm]


# ───────────────────────────────────────────────────────────────────
# Suggestion ranking
# ───────────────────────────────────────────────────────────────────


def _bike_suggestions(
    db: Any, bike_name: str, *, limit: int = 5
) -> list[dict[str, Any]]:
    """Top-N best matches for a bike-name query (uses smart resolver)."""
    if not bike_name or db is None:
        return []
    try:
        from .resolver import resolve_bike
        _, suggestions = resolve_bike(bike_name, db)
    except Exception:
        suggestions = []

    out = []
    for r in suggestions[:limit]:
        out.append({
            "id": r.get("id"),
            "manufacturer": r.get("manufacturer_name"),
            "model": r.get("model_name"),
            "year_range": _format_year_range(r),
        })
    return out


def _format_year_range(row: dict[str, Any]) -> str | None:
    start = row.get("year_from")
    end = row.get("year_to")
    if not start:
        return None
    if end and end != start:
        return f"{start}-{end}"
    return str(start)


# ───────────────────────────────────────────────────────────────────
# Intent-specific summarizers (LLM follow-up calls)
# ───────────────────────────────────────────────────────────────────


def _llm_text(client: LLMClient | None, system: str, user: str) -> str:
    """Call the LLM for a plain-text response. Falls back gracefully."""
    if client is None:
        from .client import get_default_client
        client = get_default_client()
    return client.call_text(system=system, user=user)


def _summarize_compare(
    parsed: ParsedSimRequest, comp: dict[str, Any], client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant. Summarize a compare-two-bikes simulation result in "
        "2-3 sentences. Use INR for money. End with one concrete suggestion."
    )
    a, b = comp["a"], comp["b"]
    user = (
        f"User asked: {parsed.raw_query}\n\n"
        f"Bike A: {a['bike_name']} -> ET {a['sim']['et_quarter_s']:.3f}s, "
        f"trap {a['sim']['trap_speed_kmh']:.1f} km/h, 60ft {a['sim']['et_60ft_s']:.3f}s\n"
        f"Bike B: {b['bike_name']} -> ET {b['sim']['et_quarter_s']:.3f}s, "
        f"trap {b['sim']['trap_speed_kmh']:.1f} km/h, 60ft {b['sim']['et_60ft_s']:.3f}s\n"
        f"Δ ET = {comp['delta_et_s']:+.3f}s, Δ trap = {comp['delta_trap_kmh']:+.1f} km/h, "
        f"faster = bike {comp['faster']}\n"
    )
    return _llm_text(client, sys_p, user)


def _summarize_rank(
    parsed: ParsedSimRequest, rank: dict[str, Any], client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant. Summarize a ranked list of fastest bikes in 3-4 "
        "sentences. Mention top 3 by name with their predicted ET. The ET "
        "numbers come from running the actual physics engine on each bike, "
        "so they are physics-grounded. End with one practical takeaway about "
        "what makes the #1 bike fastest in this class."
    )
    top = rank.get("top", [])[:5]
    if not top:
        return "No bikes matched the filter — try broadening the criteria."
    lines = []
    for r in top:
        et = r.get("et_s")
        trap = r.get("trap_kmh")
        et_str = f"{et:.2f}s" if et else "-"
        trap_str = f", trap {trap:.0f} km/h" if trap else ""
        lines.append(
            f"  #{r['rank']}: {r['manufacturer']} {r['model']} "
            f"({r.get('displacement_cc') or '?'}cc, "
            f"{r.get('peak_power_hp') or '?'} hp) -> ET {et_str}{trap_str}"
        )
    user = (
        f"User asked: {parsed.raw_query}\n\n"
        f"Filter applied: {rank.get('filter')}\n"
        f"Total catalog matches: {rank.get('matches')}\n"
        f"Bikes simulated: {rank.get('candidates_simulated', '?')}\n\n"
        f"Top results (sorted by physics-engine ET):\n" + "\n".join(lines)
    )
    return _llm_text(client, sys_p, user)


def _summarize_recommend(
    parsed: ParsedSimRequest, rec: dict[str, Any], client: LLMClient | None
) -> str:
    """Build a strict, hallucination-resistant build-sheet prompt.

    The system prompt forbids inventing brands or prices — only the rows
    we pass in the user message are allowed. This stops Llama / Gemini
    from defaulting to "Akrapovic or Yoshimura" when the catalog already
    has a specific Red Rooster Performance / Big Bird Customs / KustomHub
    pipe for the user\'s actual bike.
    """
    sys_p = (
        "You are MotoQuant, a drag-racing tuner. Build a concrete bike-specific "
        "upgrade plan from the catalog rows below. STRICT RULES: "
        "(1) Use ONLY the exact parts and tires listed below — DO NOT invent "
        "any brand, model, or price. If you don\'t know a number, omit it. "
        "(2) Every line must cite brand + model + INR price exactly as given. "
        "(3) Group by category in this order: Exhaust, ECU, Air filter, Fuel "
        "system, Tire, Clutch, Sprockets/Chain, Other. Skip categories that "
        "have no row. (4) For each part, add a short reason (1 short clause) "
        "explaining what it changes (e.g. \'+8 hp top-end\', \'cuts launch "
        "wheelspin\'). (5) End with two lines: \'Total: ₹X\' and (if a budget "
        "was given) \'Budget remaining: ₹Y\'. (6) No generic preamble. No "
        "\'consider also...\' suggestions for products not in the data. Keep it "
        "tight — markdown bullets, no fluff."
    )

    parts = rec.get("parts") or []
    tires = rec.get("tires") or []
    bike = rec.get("bike_name") or "(unknown bike)"
    budget = rec.get("budget_inr")

    # Group parts by category for the prompt
    grouped: dict[str, list[dict[str, Any]]] = {}
    for p in parts:
        label = p.get("label") or p.get("category_display") or p.get("category") or "Other"
        grouped.setdefault(label, []).append(p)

    cat_blocks = []
    for label, items in grouped.items():
        lines = []
        for p in items:
            brand = p.get("brand") or "?"
            name = p.get("name") or "?"
            price = int(p.get("price_inr") or 0)
            reason = p.get("fitment_reason") or ""
            lines.append(
                f"  - {brand} {name} — ₹{price:,}"
                + (f"   [{reason}]" if reason else "")
            )
        cat_blocks.append(f"{label}:\n" + "\n".join(lines))

    # Tire block
    if tires:
        tire_lines = []
        for t in tires:
            mfr = t.get("manufacturer") or "?"
            model = t.get("model") or "?"
            size = t.get("size") or ""
            mu = t.get("mu_peak")
            pos = t.get("position") or ""
            ftype = t.get("fitment_type") or ""
            price = int(t.get("price_inr") or 0)
            mu_txt = f" mu_peak={mu:.2f}" if mu else ""
            tire_lines.append(
                f"  - {mfr} {model} {size} ({pos}, {ftype}){mu_txt}"
                + (f" — ₹{price:,}" if price else "")
            )
        cat_blocks.append("Tires (recommended/drag-prep fitments):\n" + "\n".join(tire_lines))

    parts_section = "\n\n".join(cat_blocks) if cat_blocks else "(no compatible parts found)"

    user = (
        f"User asked: {parsed.raw_query}\n"
        f"Bike: {bike}\n"
        f"Budget: ₹{budget:,}\n" if budget else f"Budget: (unspecified)\n"
    )
    user = (
        f"User asked: {parsed.raw_query}\n"
        f"Bike: {bike}\n"
        f"Budget: " + (f"₹{budget:,}" if budget else "(unspecified)") + "\n\n"
        f"Catalog rows for this bike:\n\n{parts_section}\n\n"
        f"Total of selected items: ₹{int(rec.get('total_inr') or 0):,}"
    )
    return _llm_text(client, sys_p, user)


def _summarize_explain(
    parsed: ParsedSimRequest,
    sim_context: dict[str, Any] | None,
    client: LLMClient | None,
) -> str:
    sys_p = (
        "You are MotoQuant, an expert motorcycle drag-racing tuner. Answer "
        "the user's question in 3-5 sentences. Be concrete and physics-based. "
        "If sim numbers are provided, ground your answer in them. Use Indian "
        "context (INR, Aamby Valley/MMRT/BIC/Kari) where relevant. Avoid "
        "generic platitudes — give a specific number, ratio, or technique."
    )
    user = f"User asked: {parsed.raw_query}\n"
    if sim_context:
        user += (
            f"\nFor context, here's a sim of the mentioned bike:\n"
            f"  ET = {sim_context['et_quarter_s']:.3f}s\n"
            f"  Trap = {sim_context['trap_speed_kmh']:.1f} km/h\n"
            f"  60ft = {sim_context['et_60ft_s']:.3f}s\n"
        )
    return _llm_text(client, sys_p, user)


# ───────────────────────────────────────────────────────────────────
# Archetype delta application
# ───────────────────────────────────────────────────────────────────


def _apply_archetype(config: Any, parsed: ParsedSimRequest, db: Any) -> None:
    """Layer a bike_archetypes row's deltas onto `config` in place.

    Applied AFTER env overrides but BEFORE power_boost so the user's
    explicit power_boost_pct stacks on top of an archetype's boost
    (e.g. "TTS Hayabusa with +10% power" = TTS multiplier x 1.10).

    Silent on miss / DB errors so a broken archetype lookup never breaks
    a sim that would otherwise run fine on the base bike.
    """
    if parsed.archetype_id is None or db is None:
        return
    try:
        row = db._conn.execute(
            """SELECT power_multiplier, peak_power_hp_override,
                      peak_torque_nm_override, mass_delta_kg, cd_delta,
                      frontal_area_delta_m2, sprocket_front_override,
                      sprocket_rear_override, chain_pitch_override,
                      tire_mu_override
                 FROM bike_archetypes
                WHERE id = ?""",
            (parsed.archetype_id,),
        ).fetchone()
    except Exception:
        return
    if row is None:
        return

    eng = getattr(config, "engine", None)
    if eng is not None:
        if row["peak_power_hp_override"] is not None:
            try:
                eng.peak_power_hp = float(row["peak_power_hp_override"])
            except Exception:
                pass
        if row["peak_torque_nm_override"] is not None:
            try:
                eng.peak_torque_nm = float(row["peak_torque_nm_override"])
            except Exception:
                pass
        mult = row["power_multiplier"]
        if mult and abs(mult - 1.0) > 1e-6:
            try:
                if getattr(eng, "peak_power_hp", None):
                    eng.peak_power_hp *= float(mult)
                if getattr(eng, "peak_torque_nm", None):
                    eng.peak_torque_nm *= float(mult)
                dyno = getattr(eng, "dyno_curve", None)
                if dyno is not None and getattr(dyno, "torque_nm", None):
                    dyno.torque_nm = [t * float(mult) for t in dyno.torque_nm]
            except Exception:
                pass

    chassis = getattr(config, "chassis", None)
    if chassis is not None and row["mass_delta_kg"]:
        try:
            chassis.dry_mass_kg = (chassis.dry_mass_kg or 0.0) + float(row["mass_delta_kg"])
        except Exception:
            pass

    aero = getattr(config, "aero", None)
    if aero is not None:
        if row["cd_delta"]:
            try:
                aero.cd = (aero.cd or 0.0) + float(row["cd_delta"])
            except Exception:
                pass
        if row["frontal_area_delta_m2"]:
            try:
                aero.frontal_area_m2 = (aero.frontal_area_m2 or 0.0) + float(row["frontal_area_delta_m2"])
            except Exception:
                pass

    dt = getattr(config, "drivetrain", None)
    if dt is not None:
        if row["sprocket_front_override"] is not None:
            try:
                dt.front_sprocket = int(row["sprocket_front_override"])
            except Exception:
                pass
        if row["sprocket_rear_override"] is not None:
            try:
                dt.rear_sprocket = int(row["sprocket_rear_override"])
            except Exception:
                pass
        if row["chain_pitch_override"]:
            try:
                dt.chain_pitch = str(row["chain_pitch_override"])
            except Exception:
                pass

    tires = getattr(config, "tires", None)
    if tires is not None and row["tire_mu_override"] is not None:
        try:
            tires.mu_peak = float(row["tire_mu_override"])
        except Exception:
            pass
