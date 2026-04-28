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

    delta_et = sim_a["et_s"] - sim_b["et_s"]
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
    """Filter catalog and return top-N.

    Heuristic filtering from the parsed query — extract displacement / category
    hints from raw_query plus optimization_goal, then sort by validation_et_s
    (or peak_power_hp as fallback when ET is missing).
    """
    try:
        # Build search filter from raw query.
        rq = (parsed.raw_query or "").lower()
        kw: dict[str, Any] = {"limit": 200}
        # Crude displacement filter
        for needle, lo, hi in [
            ("125cc", 110, 135),
            ("150cc", 140, 165),
            ("200cc", 180, 220),
            ("250cc", 220, 280),
            ("300cc", 280, 330),
            ("400cc", 380, 460),
            ("450cc", 420, 500),
            ("500cc", 480, 560),
            ("600cc", 580, 700),
            ("650cc", 630, 720),
            ("750cc", 720, 800),
            ("1000cc", 950, 1100),
            ("liter", 950, 1300),
            ("litre", 950, 1300),
            ("1300", 1250, 1350),
        ]:
            if needle in rq:
                kw["displacement_min"] = lo
                kw["displacement_max"] = hi
                break

        # Crude category filter
        for needle, cat in [
            ("naked", "naked"),
            ("cruiser", "cruiser"),
            ("adventure", "adventure"),
            ("sport", "sport"),
            ("touring", "touring"),
            ("scooter", "scooter"),
        ]:
            if needle in rq:
                kw["category"] = cat
                break

        rows = db.bikes.search(**kw) or []

        # Sort: by validation_et_s ascending (fastest first); fall back to power.
        def _key(r: dict[str, Any]):
            et = r.get("validation_et_s")
            if et is not None:
                try:
                    return (0, float(et))
                except (TypeError, ValueError):
                    pass
            # No measured ET → estimate via power-to-weight as a tiebreaker
            hp = r.get("peak_power_hp") or 0
            mass = r.get("dry_mass_kg") or 999
            ptw = float(hp) / max(float(mass), 1.0)
            return (1, -ptw)  # higher P/W = lower sort key

        rows.sort(key=_key)
        top_n = rows[:10]

        result.rank_result = {
            "filter": kw,
            "matches": len(rows),
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
                    "validation_et_s": r.get("validation_et_s"),
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
        # Fetch parts compatible with this bike
        # Avoid heavy recommend_build (which needs running sims) — keep it light.
        parts = db.parts.list_for_bike(parsed.bike_id, limit=200) if hasattr(
            db.parts, "list_for_bike"
        ) else []
        if not parts:
            try:
                parts = db.parts.list_all(limit=200) or []
            except Exception:
                parts = []

        budget = parsed.budget_inr
        # Filter by budget if set
        if budget is not None:
            parts = [
                p for p in parts
                if (p.get("price_inr") or 0) <= budget
            ]
        # Filter by requested categories
        if parsed.parts_categories:
            wanted = {c.lower() for c in parsed.parts_categories}
            parts = [
                p for p in parts
                if (p.get("category_name") or "").lower() in wanted
                or any(c in (p.get("category_name") or "").lower() for c in wanted)
            ]
        # Sort by price-to-improve heuristic: prefer exhausts/ECU/quickshifter
        # high-impact categories at any price; otherwise descending price (more
        # expensive parts usually have higher ET impact).
        priority_cats = {"exhaust", "ecu", "quickshifter", "clutch", "weight_reduction"}

        def _score(p):
            cat = (p.get("category_name") or "").lower()
            cat_pri = 1 if any(pc in cat for pc in priority_cats) else 0
            price = float(p.get("price_inr") or 0)
            return (-cat_pri, -price)

        parts.sort(key=_score)
        top = parts[:8]

        result.recommend_result = {
            "bike_id": parsed.bike_id,
            "bike_name": parsed.bike_name,
            "budget_inr": budget,
            "parts": [
                {
                    "part_id": p["id"],
                    "name": p.get("name") or p.get("model_name"),
                    "category": p.get("category_name"),
                    "manufacturer": p.get("manufacturer_name"),
                    "price_inr": p.get("price_inr"),
                }
                for p in top
            ],
            "total_inr": sum(float(p.get("price_inr") or 0) for p in top),
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
    _apply_power_boost(config, parsed)

    try:
        engine = MotoQuantEngine(config)
        sim = engine.run()
    except Exception as e:  # noqa: BLE001
        return f"MotoQuantEngine.run: {type(e).__name__}: {e}"

    out: dict[str, Any] = {
        "et_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
        "trap_speed_mph": round(float(sim.speed_quarter) * MS_TO_MPH, 1),
        "sixty_foot_s": round(float(sim.time_60ft), 4),
        "peak_accel_g": round(float(np.max(sim.a)), 2),
    }
    for attr, key in (
        ("time_330ft", "330ft_s"),
        ("time_eighth", "eighth_s"),
        ("time_1000ft", "1000ft_s"),
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
        f"Bike A: {a['bike_name']} → ET {a['sim']['et_s']:.3f}s, "
        f"trap {a['sim']['trap_speed_kmh']:.1f} km/h, 60ft {a['sim']['sixty_foot_s']:.3f}s\n"
        f"Bike B: {b['bike_name']} → ET {b['sim']['et_s']:.3f}s, "
        f"trap {b['sim']['trap_speed_kmh']:.1f} km/h, 60ft {b['sim']['sixty_foot_s']:.3f}s\n"
        f"Δ ET = {comp['delta_et_s']:+.3f}s, Δ trap = {comp['delta_trap_kmh']:+.1f} km/h, "
        f"faster = bike {comp['faster']}\n"
    )
    return _llm_text(client, sys_p, user)


def _summarize_rank(
    parsed: ParsedSimRequest, rank: dict[str, Any], client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant. Summarize a list of fastest bikes from the catalog "
        "in 2-3 sentences. Mention top 3 by name. End with one practical takeaway."
    )
    top = rank.get("top", [])[:5]
    if not top:
        return "No bikes matched the filter — try broadening the criteria."
    lines = []
    for r in top:
        et = r.get("validation_et_s")
        et_s = f"{et:.2f}s" if et else "—"
        lines.append(
            f"  #{r['rank']}: {r['manufacturer']} {r['model']} "
            f"({r.get('displacement_cc') or '?'}cc, "
            f"{r.get('peak_power_hp') or '?'} hp, ET {et_s})"
        )
    user = (
        f"User asked: {parsed.raw_query}\n\n"
        f"Filter: {rank.get('filter')}\n"
        f"Total matches: {rank.get('matches')}\n"
        f"Top:\n" + "\n".join(lines)
    )
    return _llm_text(client, sys_p, user)


def _summarize_recommend(
    parsed: ParsedSimRequest, rec: dict[str, Any], client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant. Summarize a parts-recommendation in 2-3 sentences. "
        "Use INR for money. Highlight the most ROI-rich category. End with one "
        "concrete suggestion (e.g. exhaust + ECU combo, or budget pivot)."
    )
    top = rec.get("parts", [])[:6]
    lines = [
        f"  {p.get('manufacturer') or '?'} {p.get('name') or '?'} "
        f"({p.get('category')}) — ₹{int(p.get('price_inr') or 0):,}"
        for p in top
    ]
    user = (
        f"User asked: {parsed.raw_query}\n\n"
        f"Bike: {rec.get('bike_name')} (id {rec.get('bike_id')})\n"
        f"Budget: ₹{rec.get('budget_inr') or '(unspecified)'}\n"
        f"Recommended parts:\n" + "\n".join(lines) + "\n\n"
        f"Total: ₹{int(rec.get('total_inr') or 0):,}"
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
            f"  ET = {sim_context['et_s']:.3f}s\n"
            f"  Trap = {sim_context['trap_speed_kmh']:.1f} km/h\n"
            f"  60ft = {sim_context['sixty_foot_s']:.3f}s\n"
        )
    return _llm_text(client, sys_p, user)
