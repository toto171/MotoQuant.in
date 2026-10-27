"""
MotoQuant chat agent — a bounded multi-step tool-calling loop.

This replaces the fixed two-LLM-call pipeline (parse → dispatch → summarize)
with a real agent for the /api/chat surface:

  * multi-turn conversations (client-held message history),
  * free tool selection across the whole product surface (catalog search,
    full RK4 sims, top speed, A/B compare, parts search, the REAL knapsack
    build optimizer, gearing/launch autotune, the composed outlaw pipeline),
  * web lookup fallback (webtools) when the model needs facts it lacks,
  * moderate-accuracy estimated sims for bikes NOT in the catalog
    (estimator: spec dict → validator → spec_to_bike_config → RK4).

Discipline (inherited from the classic pipeline and enforced in the system
prompt + executor):
  * The LLM never invents a physics number — every ET/trap/speed quoted must
    come from a tool result in this conversation.
  * Hard per-turn budgets: MAX_ITERATIONS LLM rounds, FULL_SIM_BUDGET RK4
    sims, HEAVY_OP_BUDGET optimizer/autotune/outlaw runs. Enforced by the
    executor, not by trusting the model.
  * Estimated-bike results are always labelled as estimates with confidence.

The loop is provider-agnostic via LLMClient.call_tools (Anthropic native /
OpenAI-compatible function calling) and fully testable offline through the
``_call_override`` seam ("tools" kind).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from ..constants import MS_TO_KMH, MS_TO_MPH
from .client import (
    AgentStep,
    LLMClient,
    LLMNotConfiguredError,
    LLMRateLimitError,
    ToolCall,
)

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8
FULL_SIM_BUDGET = 20  # RK4 sims per chat turn (sim/topspeed/compare/estimate)
HEAVY_OP_BUDGET = 2  # optimizer / autotune / outlaw runs per chat turn
TOOL_RESULT_MAX_CHARS = 6_000
HISTORY_MAX_MESSAGES = 16
HISTORY_MAX_CHARS = 16_000
AGENT_MAX_TOKENS = 2_048

# ─── Sim-count accounting for heavy ops ───────────────────────────────────
# A heavy op is not one RK4 run: ecu_autotune.autotune's own progress total is
# 1 baseline + (2*gear_span+3 = 9) gearing + (launch_steps+1 = 7) launch + 1
# combined = 18 sims at the default spans, and build_optimizer's verification
# loop full-sims the selected build after surrogate-scoring candidates. Each
# one therefore adds a flat 18 to the turn's reported ``sims_run``; the outlaw
# pipeline composes an optimizer pass AND an autotune pass, so it counts
# double. Nominal by design — the exact count is data-dependent (surrogate
# hit rate, tooth dedup) — but honest to the order of magnitude. This is
# reporting, not a charge: the per-turn CPU fuse is HEAVY_OP_BUDGET above.
HEAVY_OP_SIM_COST = 18
OUTLAW_SIM_COST = 2 * HEAVY_OP_SIM_COST

# ─── Build-tier glossary (single source of truth for chat) ────────────────
# Industry-standard motorcycle drag-build stages. stage_3 is honestly
# approximated: the parts catalog has no engine-internals categories (cams /
# pistons / big-bore), so its recipe leans on nitrous + supporting mods.
BUILD_TIERS: dict[str, dict[str, Any]] = {
    "stage_1": {
        "label": "Stage 1 — bolt-ons",
        "description": "exhaust, high-flow air filter, ECU flash/fuel controller",
        "profile": "street_legal",
        "default_budget_inr": 60_000,
    },
    "stage_2": {
        "label": "Stage 2 — bolt-ons + drivetrain",
        "description": "stage 1 + full exhaust, clutch, quickshifter, "
        "sprockets/chain, lightweight battery, dyno tune",
        "profile": "street_legal",
        "default_budget_inr": 200_000,
    },
    "stage_3": {
        "label": "Stage 3 — serious power",
        "description": "stage 2 + nitrous, upgraded fuel system, suspension; "
        "(engine internals like cams/big-bore are not in the parts catalog, "
        "so stage 3 is approximated with bolt-on power adders)",
        "profile": "full_race",
        "default_budget_inr": 500_000,
    },
    "stage_4": {
        "label": "Stage 4 / Outlaw — full drag prep",
        "description": "stage 3 + forced induction, extended swingarm, "
        "wheelie bar, drag slicks, lockup clutch — open/outlaw class, "
        "no budget limit",
        "profile": "full_race",
        "default_budget_inr": None,  # unlimited (resolved server-side)
    },
}
BUILD_TIER_ALIASES = {
    "outlaw": "stage_4",
    "open_class": "stage_4",
    "open class": "stage_4",
    "all_out": "stage_4",
    "no limit": "stage_4",
    "stage1": "stage_1",
    "stage2": "stage_2",
    "stage3": "stage_3",
    "stage4": "stage_4",
}


def resolve_build_tier(tier: str | None) -> str:
    t = (tier or "stage_2").strip().lower().replace("-", "_")
    return BUILD_TIER_ALIASES.get(t, t if t in BUILD_TIERS else "stage_2")


# ─── Result type ──────────────────────────────────────────────────────────


@dataclass
class AgentChatResult:
    """Result of one agent chat turn."""

    raw_query: str
    reply: str | None = None
    blocks: list[dict[str, Any]] = field(default_factory=list)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    sims_run: int = 0
    iterations: int = 0
    error: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "reply": self.reply,
            "blocks": self.blocks,
            "tool_trace": self.tool_trace,
            "sims_run": self.sims_run,
            "iterations": self.iterations,
            "error": self.error,
            "error_detail": self.error_detail,
        }

    def last_block(self, block_type: str) -> dict[str, Any] | None:
        for b in reversed(self.blocks):
            if b.get("type") == block_type:
                return b.get("payload")
        return None


# ─── Execution context ────────────────────────────────────────────────────


@dataclass
class AgentContext:
    db: Any
    result: AgentChatResult
    progress_cb: Callable[[float, str | None], None] | None = None
    surrogate_getter: Callable[[], tuple[Any, str]] | None = None
    full_sims_left: int = FULL_SIM_BUDGET
    heavy_ops_left: int = HEAVY_OP_BUDGET

    def spend_sims(self, n: int) -> str | None:
        """Reserve n full sims. Returns an error string when over budget."""
        if self.full_sims_left < n:
            return (
                f"per-message simulation budget exhausted "
                f"({FULL_SIM_BUDGET} full sims/turn) — answer with the "
                f"results you already have"
            )
        self.full_sims_left -= n
        self.result.sims_run += n
        return None

    def spend_heavy(self, sim_cost: int = HEAVY_OP_SIM_COST) -> str | None:
        """Reserve one heavy op (per-turn CPU fuse) and add its nominal sim
        count to ``sims_run``."""
        if self.heavy_ops_left < 1:
            return (
                f"per-message optimizer budget exhausted ({HEAVY_OP_BUDGET} "
                f"heavy operations/turn) — answer with what you have"
            )
        self.heavy_ops_left -= 1
        self.result.sims_run += sim_cost
        return None

    def tick(self, frac: float, stage: str | None) -> None:
        if self.progress_cb is not None:
            try:
                self.progress_cb(frac, stage)
            except Exception:  # noqa: BLE001
                pass

    def add_block(self, block_type: str, payload: Any) -> None:
        self.result.blocks.append({"type": block_type, "payload": payload})


# ─── Config-building helpers (agent-local; no ParsedSimRequest needed) ────


def _venue_env(db, venue_id: int | None):
    if venue_id is None:
        return None
    try:
        return db.venues.to_environment(venue_id, month=datetime.now().month)
    except Exception:  # noqa: BLE001
        return None


def _apply_env_args(config, args: dict[str, Any]) -> None:
    env = config.environment
    if args.get("ambient_temp_c") is not None:
        env.ambient_temp_c = float(args["ambient_temp_c"])
    if args.get("humidity_pct") is not None:
        env.relative_humidity_pct = float(args["humidity_pct"])
    if args.get("altitude_m") is not None:
        env.altitude_m = float(args["altitude_m"])
    if args.get("headwind_kmh") is not None:
        env.wind_speed_ms = float(args["headwind_kmh"]) / 3.6
        env.wind_direction_deg = 0


def _apply_power_boost(config, pct: float | None) -> None:
    if not pct:
        return
    factor = 1.0 + float(pct) / 100.0
    if getattr(config.engine, "peak_power_hp", None):
        config.engine.peak_power_hp *= factor
    if getattr(config.engine, "peak_torque_nm", None):
        config.engine.peak_torque_nm *= factor
    dyno = getattr(config.engine, "dyno_curve", None)
    if dyno is not None and getattr(dyno, "torque_nm", None) is not None:
        dyno.torque_nm = [t * factor for t in dyno.torque_nm]


def _bike_display_name(db, bike_id: int) -> str:
    try:
        row = db.conn.execute(
            """SELECT bm.model_name, m.name AS manufacturer
               FROM bike_models bm JOIN manufacturers m
                 ON bm.manufacturer_id = m.id WHERE bm.id = ?""",
            (bike_id,),
        ).fetchone()
        if row:
            r = dict(row)
            return f"{r['manufacturer']} {r['model_name']}"
    except Exception:  # noqa: BLE001
        pass
    return f"bike #{bike_id}"


def _build_config_for(ctx: AgentContext, args: dict[str, Any]):
    """Build a BikeConfig for args {bike_id, venue_id?, env?, mods?}.

    Returns (config, applied_notes list) or raises ValueError with a
    user-meaningful message.
    """
    db = ctx.db
    bike_id = args.get("bike_id")
    if not bike_id:
        raise ValueError("bike_id is required (use search_bikes first)")
    bike_id = int(bike_id)

    config_row = db.bikes.get_current_config(bike_id)
    if config_row is None:
        raise ValueError(
            f"no physics config for bike_id {bike_id} — is the id correct?"
        )
    env = _venue_env(db, args.get("venue_id"))
    config = db.bikes.to_config(config_row["id"], environment=env)
    if config is None:
        raise ValueError(f"config load failed for bike_id {bike_id}")

    notes: list[str] = []
    _apply_env_args(config, args)
    _apply_power_boost(config, args.get("power_boost_pct"))
    if args.get("power_boost_pct"):
        notes.append(f"power {float(args['power_boost_pct']):+g}%")
    if args.get("mass_delta_kg"):
        config.chassis.dry_mass_kg += float(args["mass_delta_kg"])
        notes.append(f"mass {float(args['mass_delta_kg']):+g} kg")
    if args.get("rider_mass_kg"):
        config.rider.mass_kg = float(args["rider_mass_kg"])
        config.chassis.rider_mass_kg = float(args["rider_mass_kg"])

    part_ids = args.get("part_ids") or []
    if part_ids:
        from ..database.parts_repo import PartsRepository

        repo = PartsRepository(db.conn)
        config = repo.apply_multiple([int(p) for p in part_ids], config)
        cost = repo.estimate_build_cost([int(p) for p in part_ids])
        notes.append(f"{len(part_ids)} parts applied (₹{cost.get('total', 0):,.0f})")

    rear_tire_id = args.get("rear_tire_id")
    if rear_tire_id:
        row = db.conn.execute(
            "SELECT mu_peak, pacejka_D FROM tire_models WHERE id=?",
            (int(rear_tire_id),),
        ).fetchone()
        if row:
            r = dict(row)
            mu = r.get("mu_peak") or r.get("pacejka_D")
            if mu and float(mu) > 0:
                config.tires.mu_peak = float(mu)
                notes.append(f"rear tire swap (mu {float(mu):.2f})")

    return config, notes


def _sim_to_dict(sim, bike_name: str, notes: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "bike_name": bike_name,
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
        "trap_speed_mph": round(float(sim.speed_quarter) * MS_TO_MPH, 1),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "peak_accel_g": round(float(np.max(sim.a)), 2),
    }
    for attr, key in (
        ("time_330ft", "et_330ft_s"),
        ("time_eighth", "et_eighth_s"),
        ("time_1000ft", "et_1000ft_s"),
    ):
        val = getattr(sim, attr, None)
        if val:
            out[key] = round(float(val), 4)
    if notes:
        out["modifications"] = notes
    return out


# ─── Tool schemas ─────────────────────────────────────────────────────────

_ENV_PROPS = {
    "venue_id": {
        "type": "integer",
        "description": "Venue id from resolve_venue/list_venues (seasonal weather applied)",
    },
    "ambient_temp_c": {"type": "number"},
    "humidity_pct": {"type": "number"},
    "altitude_m": {"type": "number"},
    "headwind_kmh": {"type": "number"},
}
_MOD_PROPS = {
    "power_boost_pct": {
        "type": "number",
        "description": "Scale engine power/torque by this percent (e.g. 10 = +10%)",
    },
    "mass_delta_kg": {"type": "number"},
    "rider_mass_kg": {"type": "number"},
    "part_ids": {
        "type": "array",
        "items": {"type": "integer"},
        "description": "Catalog part ids (from search_parts) to bolt on before the run",
    },
    "rear_tire_id": {
        "type": "integer",
        "description": "Tire id (from list_tires) to swap onto the rear",
    },
}


def _tool(name: str, description: str, props: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": props,
            "required": required,
        },
    }


AGENT_TOOLS: list[dict[str, Any]] = [
    _tool(
        "search_bikes",
        "Find bikes in the MotoQuant catalog by name (fuzzy). ALWAYS use this "
        "to get a bike_id before simulating. Returns best match + candidates.",
        {
            "query": {
                "type": "string",
                "description": "e.g. 'hayabusa', 'zx-10r 2021'",
            },
            "limit": {"type": "integer", "default": 5},
        },
        ["query"],
    ),
    _tool(
        "get_bike_details",
        "Full catalog specs for one bike: engine, gearing, mass, aero, tires.",
        {"bike_id": {"type": "integer"}},
        ["bike_id"],
    ),
    _tool(
        "run_simulation",
        "Run the full RK4 quarter-mile physics simulation for a catalog bike, "
        "optionally with venue/conditions and modifications. Returns ET, trap "
        "speed, 60ft/330ft/eighth/1000ft splits, peak g.",
        {"bike_id": {"type": "integer"}, **_ENV_PROPS, **_MOD_PROPS},
        ["bike_id"],
    ),
    _tool(
        "run_top_speed",
        "Simulate terminal top speed for a catalog bike (adaptive solver, "
        "runs past the quarter mile until acceleration plateaus).",
        {"bike_id": {"type": "integer"}, **_ENV_PROPS, **_MOD_PROPS},
        ["bike_id"],
    ),
    _tool(
        "compare_bikes",
        "Head-to-head: run BOTH bikes through the full sim under identical "
        "conditions and report the delta.",
        {
            "bike_a_id": {"type": "integer"},
            "bike_b_id": {"type": "integer"},
            **_ENV_PROPS,
        },
        ["bike_a_id", "bike_b_id"],
    ),
    _tool(
        "search_parts",
        "Compatibility-filtered aftermarket parts for a bike (the fitment "
        "engine guarantees every hit physically fits). Filter by category "
        "substring (exhaust/ecu/air_filter/sprocket/chain/clutch/quickshifter/"
        "battery/suspension/brakes/fuel_system/nitrous/boost/wheelie_bar/"
        "swingarm_ext/lowering/air_shifter) and price.",
        {
            "bike_id": {"type": "integer"},
            "category": {"type": "string"},
            "max_price_inr": {"type": "number"},
            "limit": {"type": "integer", "default": 12},
        },
        ["bike_id"],
    ),
    _tool(
        "list_tires",
        "Tire fitments for a bike: OEM, recommended and drag_prep options "
        "with grip (mu) and price. Use tire ids with run_simulation's "
        "rear_tire_id.",
        {
            "bike_id": {"type": "integer"},
            "fitment_type": {
                "type": "string",
                "enum": ["oem", "recommended", "drag_prep"],
            },
        },
        ["bike_id"],
    ),
    _tool(
        "rank_bikes",
        "Rank catalog bikes by SIMULATED quarter-mile ET within a class. Use "
        "for 'fastest/quickest X' questions (fastest 300cc, quickest cruiser, "
        "best litre bike at altitude...). Filters: category (sport/naked/"
        "cruiser/adventure/touring), displacement window, manufacturer. "
        "Shortlists by power-to-weight then runs REAL sims on the top "
        "candidates (costs up to 8 sims).",
        {
            "category": {"type": "string"},
            "min_cc": {"type": "number"},
            "max_cc": {"type": "number"},
            "manufacturer": {"type": "string"},
            "top_n": {
                "type": "integer",
                "default": 5,
                "description": "How many ranked bikes to return (max 5)",
            },
            **_ENV_PROPS,
        },
        [],
    ),
    _tool(
        "resolve_venue",
        "Resolve a location/track name to a seeded venue id (e.g. 'Aamby "
        "Valley', 'Santa Pod', 'BIC'). Falls back to closest match.",
        {"location": {"type": "string"}},
        ["location"],
    ),
    _tool(
        "list_venues",
        "List all seeded drag venues with altitude and country.",
        {},
        [],
    ),
    _tool(
        "optimize_build",
        "Run the REAL physics build optimizer (surrogate-accelerated knapsack "
        "over compatibility-filtered parts, verified with full sims). "
        "build_tier: stage_1 (bolt-ons ₹60k), stage_2 (+drivetrain ₹200k), "
        "stage_3 (+nitrous/fuel/suspension ₹500k), stage_4 or 'outlaw' "
        "(FULL drag prep: forced induction, wheelie bar, extended swingarm, "
        "drag slicks, gearing + launch autotune — NO budget limit; this is "
        "the outlaw/open-class build and runs the composed pipeline). "
        "Explicit budget_inr overrides the tier default. SLOW (10-120s) — "
        "call at most once per message.",
        {
            "bike_id": {"type": "integer"},
            "build_tier": {
                "type": "string",
                "enum": ["stage_1", "stage_2", "stage_3", "stage_4", "outlaw"],
            },
            "budget_inr": {"type": "number"},
            "goal": {"type": "string", "enum": ["min_et", "max_trap"]},
            "venue_id": {"type": "integer"},
        },
        ["bike_id"],
    ),
    _tool(
        "autotune_setup",
        "Conditions-aware drag setup for a bike: gearing sweep, launch-RPM "
        "sweep, tyre pressures, fuel/timing guidance (full-sim, ~20 sims). "
        "Use for 'how should I set up X at venue Y' questions.",
        {"bike_id": {"type": "integer"}, **_ENV_PROPS},
        ["bike_id"],
    ),
    _tool(
        "simulate_estimated_bike",
        "MODERATE-ACCURACY sim for a bike NOT in the catalog. Supply real "
        "specs (from your knowledge or web_search — never guess numbers). "
        "Required: manufacturer, model_name, displacement_cc, peak_power_hp, "
        "dry_mass_kg. Strongly recommended: peak_power_rpm, peak_torque_nm, "
        "peak_torque_rpm, cylinders, category (sport/naked/cruiser/adventure/"
        "touring), gears, gear_ratios, front/rear_sprocket, cd, "
        "frontal_area_m2, rear_tire_size, year_from. The result is an "
        "ESTIMATE — always present it as such with its confidence score.",
        {
            "spec": {
                "type": "object",
                "description": "Spec dict with the fields above (units: hp, Nm, kg, cc, mm)",
            },
            **_ENV_PROPS,
            "rider_mass_kg": {"type": "number"},
        },
        ["spec"],
    ),
    _tool(
        "web_search",
        "Search the public web. Use when you need facts you don't reliably "
        "know: specs of obscure/new bikes, race results, part prices, rule "
        "definitions. Cite the source URL for any fact you use from it.",
        {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
        },
        ["query"],
    ),
    _tool(
        "web_fetch",
        "Fetch one web page as readable text (use after web_search to read a "
        "promising result).",
        {"url": {"type": "string"}},
        ["url"],
    ),
    _tool(
        "get_catalog_stats",
        "Live catalog counts (bikes, parts, tires, venues) — use instead of "
        "quoting remembered numbers.",
        {},
        [],
    ),
]


# ─── Tool executors ───────────────────────────────────────────────────────


def _exec_search_bikes(ctx: AgentContext, args: dict) -> dict:
    from .resolver import resolve_bike

    query = (args.get("query") or "").strip()
    if not query:
        return {"error": "empty query"}
    limit = max(1, min(int(args.get("limit") or 5), 10))
    match_id, suggestions = resolve_bike(query, ctx.db)
    out: dict[str, Any] = {"query": query}
    if match_id is not None:
        match = next((s for s in suggestions or [] if s.get("id") == match_id), None)
        out["best_match"] = {
            "bike_id": match_id,
            "manufacturer": (match or {}).get("manufacturer_name"),
            "model": (match or {}).get("model_name"),
            "year_from": (match or {}).get("year_from"),
            "year_to": (match or {}).get("year_to"),
        }
    out["candidates"] = [
        {
            "bike_id": s.get("id"),
            "manufacturer": s.get("manufacturer_name"),
            "model": s.get("model_name"),
            "year_from": s.get("year_from"),
            "year_to": s.get("year_to"),
        }
        for s in (suggestions or [])[:limit]
    ]
    if match_id is None and not out["candidates"]:
        out["note"] = (
            "no catalog match — if the user wants this bike, gather real "
            "specs (web_search if needed) and use simulate_estimated_bike"
        )
    return out


def _exec_get_bike_details(ctx: AgentContext, args: dict) -> dict:
    bike_id = int(args.get("bike_id") or 0)
    row = ctx.db.conn.execute(
        """SELECT bm.*, m.name AS manufacturer_name
           FROM bike_models bm JOIN manufacturers m ON bm.manufacturer_id=m.id
           WHERE bm.id=?""",
        (bike_id,),
    ).fetchone()
    if row is None:
        return {"error": f"no bike with id {bike_id}"}
    r = dict(row)
    out = {
        "bike_id": bike_id,
        "manufacturer": r.get("manufacturer_name"),
        "model": r.get("model_name"),
        "year_from": r.get("year_from"),
        "year_to": r.get("year_to"),
        "category": r.get("category"),
        "displacement_cc": r.get("displacement_cc"),
        "peak_power_hp": r.get("peak_power_hp"),
        "peak_torque_nm": r.get("peak_torque_nm"),
        "dry_mass_kg": r.get("dry_mass_kg"),
        "cylinder_config": r.get("cylinder_config"),
    }
    try:
        cfg_row = ctx.db.bikes.get_current_config(bike_id)
        if cfg_row:
            cfg = ctx.db.bikes.to_config(cfg_row["id"])
            if cfg is not None:
                out["config"] = {
                    "power_hp": round(float(cfg.engine.peak_power_hp), 1),
                    "redline_rpm": cfg.engine.redline_rpm,
                    "gears": len(cfg.drivetrain.gear_ratios or []),
                    "final_drive": round(float(cfg.drivetrain.final_ratio), 3),
                    "dry_mass_kg": round(float(cfg.chassis.dry_mass_kg), 1),
                    "cd": round(float(cfg.aero.cd), 3),
                    "tire_mu_peak": round(float(cfg.tires.mu_peak), 2),
                }
    except Exception:  # noqa: BLE001
        pass
    ctx.add_block("bike_details", out)
    return out


def _exec_run_simulation(ctx: AgentContext, args: dict) -> dict:
    err = ctx.spend_sims(1)
    if err:
        return {"error": err}
    from ..engine_select import make_engine

    try:
        config, notes = _build_config_for(ctx, args)
    except ValueError as e:
        return {"error": str(e)}
    bike_name = _bike_display_name(ctx.db, int(args["bike_id"]))
    ctx.tick(0.0, f"Simulating {bike_name}")
    try:
        sim = make_engine(config).run()
    except Exception as e:  # noqa: BLE001
        return {"error": f"simulation failed: {type(e).__name__}: {e}"}
    out = _sim_to_dict(sim, bike_name, notes)
    ctx.add_block("sim_result", out)
    return out


def _exec_run_top_speed(ctx: AgentContext, args: dict) -> dict:
    err = ctx.spend_sims(1)
    if err:
        return {"error": err}
    from ..engine_select import make_engine

    try:
        config, notes = _build_config_for(ctx, args)
    except ValueError as e:
        return {"error": str(e)}
    bike_name = _bike_display_name(ctx.db, int(args["bike_id"]))
    ctx.tick(0.0, f"Top-speed run: {bike_name}")
    try:
        ts = make_engine(config).run_top_speed()
    except Exception as e:  # noqa: BLE001
        return {"error": f"top-speed sim failed: {type(e).__name__}: {e}"}
    out = {
        "bike_name": bike_name,
        "top_speed_kmh": round(float(ts.terminal_velocity_ms) * MS_TO_KMH, 1),
        "top_speed_mph": round(float(ts.terminal_velocity_ms) * MS_TO_MPH, 1),
        "time_to_terminal_s": round(float(ts.time_to_terminal_s), 1),
        "distance_to_terminal_m": round(float(ts.distance_to_terminal_m), 0),
        "terminal_gear": int(ts.terminal_gear),
        "terminal_rpm": round(float(ts.terminal_rpm), 0),
        "reached_plateau": bool(ts.reached_plateau),
    }
    if notes:
        out["modifications"] = notes
    ctx.add_block("top_speed", out)
    return out


def _exec_compare_bikes(ctx: AgentContext, args: dict) -> dict:
    err = ctx.spend_sims(2)
    if err:
        return {"error": err}
    from ..engine_select import make_engine

    results = {}
    for key, id_key in (("a", "bike_a_id"), ("b", "bike_b_id")):
        sub_args = {**args, "bike_id": args.get(id_key)}
        try:
            config, notes = _build_config_for(ctx, sub_args)
        except ValueError as e:
            return {"error": f"bike {key}: {e}"}
        name = _bike_display_name(ctx.db, int(args[id_key]))
        ctx.tick(0.0, f"Simulating {name}")
        try:
            sim = make_engine(config).run()
        except Exception as e:  # noqa: BLE001
            return {"error": f"bike {key} sim failed: {type(e).__name__}: {e}"}
        results[key] = _sim_to_dict(sim, name, notes)
    delta_et = results["a"]["et_quarter_s"] - results["b"]["et_quarter_s"]
    out = {
        "bike_a": results["a"],
        "bike_b": results["b"],
        "delta_et_s": round(delta_et, 4),
        "winner": results["a"]["bike_name"]
        if delta_et < 0
        else results["b"]["bike_name"],
    }
    ctx.add_block("compare_result", out)
    return out


def _exec_search_parts(ctx: AgentContext, args: dict) -> dict:
    from ..database.parts_repo import PartsRepository

    bike_id = int(args.get("bike_id") or 0)
    limit = max(1, min(int(args.get("limit") or 12), 30))
    repo = PartsRepository(ctx.db.conn)
    try:
        rows = repo.search(
            bike_model_id=bike_id,
            category=args.get("category") or None,
            limit=200,
        )
    except TypeError:
        # older search signature — degrade to unfiltered then filter here
        rows = repo.search(bike_model_id=bike_id, limit=200)
    max_price = args.get("max_price_inr")
    out_rows = []
    for r in rows:
        price = r.get("price_inr")
        if max_price and price and float(price) > float(max_price):
            continue
        out_rows.append(
            {
                "part_id": r.get("id"),
                "name": r.get("model_name") or r.get("name"),
                "brand": r.get("brand"),
                "category": r.get("category_name") or r.get("category"),
                "price_inr": price,
            }
        )
        if len(out_rows) >= limit:
            break
    payload = {"bike_id": bike_id, "count": len(out_rows), "parts": out_rows}
    ctx.add_block("parts", payload)
    return payload


def _exec_list_tires(ctx: AgentContext, args: dict) -> dict:
    bike_id = int(args.get("bike_id") or 0)
    try:
        fitments = ctx.db.tires.get_bike_fitments(
            bike_id, fitment_type=args.get("fitment_type") or None
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"fitment lookup failed: {e}"}
    rows = [
        {
            "tire_id": f.get("tire_model_id"),
            "name": f"{f.get('tire_manufacturer', '')} {f.get('model_name', '')}".strip(),
            "size": f.get("size_designation"),
            "position": f.get("position"),
            "fitment_type": f.get("fitment_type"),
            "compound": f.get("compound_type"),
            "mu_peak": f.get("mu_peak"),
            "price_inr": f.get("price_inr"),
        }
        for f in fitments
    ]
    payload = {"bike_id": bike_id, "count": len(rows), "tires": rows}
    ctx.add_block("tires", payload)
    return payload


def _exec_rank_bikes(ctx: AgentContext, args: dict) -> dict:
    """Shortlist by power-to-weight (cheap SQL), then rank by REAL sims."""
    from ..engine_select import make_engine

    top_n = max(1, min(int(args.get("top_n") or 5), 5))
    sql = """
        SELECT bm.id, bm.model_name, m.name AS manufacturer,
               bm.peak_power_hp, bm.dry_mass_kg, bm.displacement_cc,
               bm.category
        FROM bike_models bm JOIN manufacturers m ON bm.manufacturer_id = m.id
        WHERE bm.peak_power_hp IS NOT NULL AND bm.dry_mass_kg IS NOT NULL
    """
    params: list = []
    if args.get("category"):
        sql += " AND LOWER(bm.category) = ?"
        params.append(str(args["category"]).strip().lower())
    if args.get("min_cc") is not None:
        sql += " AND bm.displacement_cc >= ?"
        params.append(float(args["min_cc"]))
    if args.get("max_cc") is not None:
        sql += " AND bm.displacement_cc <= ?"
        params.append(float(args["max_cc"]))
    if args.get("manufacturer"):
        sql += " AND LOWER(m.name) LIKE ?"
        params.append(f"%{str(args['manufacturer']).strip().lower()}%")
    sql += " ORDER BY (bm.peak_power_hp / bm.dry_mass_kg) DESC LIMIT 12"
    rows = [dict(r) for r in ctx.db.conn.execute(sql, params).fetchall()]
    if not rows:
        return {
            "error": "no catalog bikes match those filters",
            "hint": "loosen the displacement window or drop the category",
        }

    n_sim = min(len(rows), max(top_n + 2, 5), 8)
    err = ctx.spend_sims(n_sim)
    if err:
        return {"error": err}
    ranked = []
    for row in rows[:n_sim]:
        try:
            config, _ = _build_config_for(
                ctx, {"bike_id": row["id"], **{k: args.get(k) for k in _ENV_PROPS}}
            )
            ctx.tick(0.0, f"Simulating {row['manufacturer']} {row['model_name']}")
            sim = make_engine(config).run()
            ranked.append(
                {
                    "bike_id": row["id"],
                    "bike_name": f"{row['manufacturer']} {row['model_name']}",
                    "displacement_cc": row["displacement_cc"],
                    "power_hp": row["peak_power_hp"],
                    "et_quarter_s": round(float(sim.time_quarter), 3),
                    "trap_speed_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
                }
            )
        except Exception as e:  # noqa: BLE001 — one bad config must not kill the rank
            logger.warning("rank_bikes sim failed for %s: %s", row["id"], e)
    ranked.sort(key=lambda r: r["et_quarter_s"])
    payload = {
        "method": f"top {n_sim} power-to-weight candidates fully simulated",
        "candidates_considered": len(rows),
        "ranking": ranked[:top_n],
    }
    ctx.add_block("rank_result", payload)
    return payload


def _exec_resolve_venue(ctx: AgentContext, args: dict) -> dict:
    from .resolver import resolve_venue

    location = (args.get("location") or "").strip()
    if not location:
        return {"error": "empty location"}
    venue_id = resolve_venue(location, ctx.db)
    if venue_id is None:
        return {
            "error": f"no seeded venue matches {location!r}",
            "hint": "use list_venues to see what exists, or pass explicit "
            "altitude_m / ambient_temp_c instead",
        }
    row = ctx.db.conn.execute(
        "SELECT id, name, city, country, altitude_m FROM venues WHERE id=?",
        (venue_id,),
    ).fetchone()
    return dict(row) if row else {"venue_id": venue_id}


def _exec_list_venues(ctx: AgentContext, args: dict) -> dict:
    rows = ctx.db.conn.execute(
        "SELECT id, name, city, country, altitude_m FROM venues ORDER BY id"
    ).fetchall()
    payload = {"venues": [dict(r) for r in rows]}
    ctx.add_block("venues", payload)
    return payload


def _exec_optimize_build(ctx: AgentContext, args: dict) -> dict:
    bike_id = int(args.get("bike_id") or 0)
    tier = resolve_build_tier(args.get("build_tier"))
    tier_info = BUILD_TIERS[tier]
    err = ctx.spend_heavy(OUTLAW_SIM_COST if tier == "stage_4" else HEAVY_OP_SIM_COST)
    if err:
        return {"error": err}
    budget = args.get("budget_inr")
    if budget is None:
        budget = tier_info["default_budget_inr"]
    goal = args.get("goal") or "min_et"

    try:
        config, _ = _build_config_for(
            ctx, {"bike_id": bike_id, "venue_id": args.get("venue_id")}
        )
    except ValueError as e:
        return {"error": str(e)}

    from ..database.parts_repo import PartsRepository

    parts_repo = PartsRepository(ctx.db.conn)
    surrogate, surrogate_source = (None, "none")
    if ctx.surrogate_getter is not None:
        try:
            surrogate, surrogate_source = ctx.surrogate_getter()
        except Exception:  # noqa: BLE001
            pass

    bike_name = _bike_display_name(ctx.db, bike_id)

    if tier == "stage_4":
        # Outlaw/open class → the composed max-effort pipeline.
        from ..analysis.outlaw import optimize_outlaw

        ctx.tick(0.0, f"Outlaw build: {bike_name}")
        try:
            payload = optimize_outlaw(
                config,
                parts_repo,
                ctx.db.tires,
                bike_model_id=bike_id,
                budget_inr=budget,
                goal=goal,
                surrogate=surrogate,
                surrogate_source=surrogate_source,
                progress_cb=lambda f, s=None: ctx.tick(f, s),
            )
        except Exception as e:  # noqa: BLE001
            logger.error("outlaw pipeline failed", exc_info=True)
            return {"error": f"outlaw pipeline failed: {type(e).__name__}: {e}"}
        payload["build_tier"] = tier
        payload["tier_label"] = tier_info["label"]
        ctx.add_block("outlaw_result", payload)
        return payload

    from ..analysis.build_optimizer import optimize_build as _optimize

    ctx.tick(0.0, f"Optimizing {tier_info['label']}: {bike_name}")
    try:
        result = _optimize(
            config,
            float(budget),
            parts_repo,
            goal=goal,
            profile=tier_info["profile"],
            bike_model_id=bike_id,
            surrogate=surrogate,
            surrogate_source=surrogate_source,
            progress_cb=lambda f, s=None: ctx.tick(f, s),
        )
    except Exception as e:  # noqa: BLE001
        logger.error("optimize_build failed", exc_info=True)
        return {"error": f"optimizer failed: {type(e).__name__}: {e}"}
    payload = result.to_dict()
    payload["build_tier"] = tier
    payload["tier_label"] = tier_info["label"]
    ctx.add_block("build_result", payload)
    return payload


def _exec_autotune_setup(ctx: AgentContext, args: dict) -> dict:
    err = ctx.spend_heavy()
    if err:
        return {"error": err}
    try:
        config, _ = _build_config_for(ctx, args)
    except ValueError as e:
        return {"error": str(e)}
    from ..analysis.ecu_autotune import autotune

    bike_name = _bike_display_name(ctx.db, int(args["bike_id"]))
    ctx.tick(0.0, f"Autotuning setup: {bike_name}")
    try:
        result = autotune(config, progress_cb=lambda f, s=None: ctx.tick(f, s))
    except Exception as e:  # noqa: BLE001
        return {"error": f"autotune failed: {type(e).__name__}: {e}"}
    payload = result.to_dict()
    ctx.add_block("autotune_result", payload)
    return payload


def _exec_simulate_estimated(ctx: AgentContext, args: dict) -> dict:
    err = ctx.spend_sims(2)  # quarter + top speed
    if err:
        return {"error": err}
    from .estimator import simulate_estimated_bike

    env_overrides = {
        k: args.get(k) for k in ("ambient_temp_c", "humidity_pct", "altitude_m")
    }
    spec = args.get("spec") or {}
    ctx.tick(
        0.0, f"Estimating {spec.get('manufacturer', '')} {spec.get('model_name', '')}"
    )
    payload = simulate_estimated_bike(
        spec,
        db=ctx.db,
        venue_id=args.get("venue_id"),
        env_overrides=env_overrides,
        rider_mass_kg=args.get("rider_mass_kg"),
    )
    if not payload.get("error"):
        ctx.add_block("estimated_sim", payload)
    return payload


def _exec_web_search(ctx: AgentContext, args: dict) -> dict:
    from .webtools import web_search

    ctx.tick(0.0, "Searching the web")
    payload = web_search(
        args.get("query") or "", max_results=int(args.get("max_results") or 5)
    )
    if payload.get("results"):
        ctx.add_block(
            "web_citations",
            {"query": args.get("query"), "results": payload["results"]},
        )
    return payload


def _exec_web_fetch(ctx: AgentContext, args: dict) -> dict:
    from .webtools import web_fetch

    ctx.tick(0.0, "Reading web page")
    return web_fetch(args.get("url") or "")


def _exec_catalog_stats(ctx: AgentContext, args: dict) -> dict:
    counts = {}
    for label, table in (
        ("bikes", "bike_models"),
        ("parts", "parts"),
        ("tires", "tire_models"),
        ("venues", "venues"),
        ("tire_fitments", "bike_tire_fitments"),
    ):
        try:
            counts[label] = ctx.db.conn.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608 — fixed table names
            ).fetchone()[0]
        except Exception:  # noqa: BLE001
            counts[label] = None
    return counts


_EXECUTORS: dict[str, Callable[[AgentContext, dict], dict]] = {
    "search_bikes": _exec_search_bikes,
    "get_bike_details": _exec_get_bike_details,
    "run_simulation": _exec_run_simulation,
    "run_top_speed": _exec_run_top_speed,
    "compare_bikes": _exec_compare_bikes,
    "search_parts": _exec_search_parts,
    "list_tires": _exec_list_tires,
    "rank_bikes": _exec_rank_bikes,
    "resolve_venue": _exec_resolve_venue,
    "list_venues": _exec_list_venues,
    "optimize_build": _exec_optimize_build,
    "autotune_setup": _exec_autotune_setup,
    "simulate_estimated_bike": _exec_simulate_estimated,
    "web_search": _exec_web_search,
    "web_fetch": _exec_web_fetch,
    "get_catalog_stats": _exec_catalog_stats,
}


def execute_tool(ctx: AgentContext, call: ToolCall) -> dict:
    """Execute one tool call. Always returns a dict (errors are data)."""
    fn = _EXECUTORS.get(call.name)
    if fn is None:
        return {"error": f"unknown tool {call.name!r}"}
    if "__malformed_json__" in (call.arguments or {}):
        return {
            "error": "your tool arguments were not valid JSON — retry with correct JSON"
        }
    try:
        return fn(ctx, call.arguments or {})
    except Exception as e:  # noqa: BLE001
        logger.error("tool %s crashed", call.name, exc_info=True)
        return {"error": f"tool crashed: {type(e).__name__}: {e}"}


# ─── System prompt ────────────────────────────────────────────────────────


def _system_prompt(ctx: AgentContext) -> str:
    stats = _exec_catalog_stats(ctx, {})
    tier_lines = []
    for info in BUILD_TIERS.values():
        budget = info["default_budget_inr"]
        budget_txt = "no limit" if budget is None else f"₹{budget:,}"
        tier_lines.append(
            f"  - {info['label']}: {info['description']} (default budget: {budget_txt})"
        )
    tiers = "\n".join(tier_lines)
    return f"""You are the MotoQuant race engineer — the AI assistant of MotoQuant, \
a free, open-source, first-principles motorcycle drag-racing physics \
simulator (15 sub-models, RK4 solver, validated against a weighted corpus of \
published drag-strip benchmarks — motoquant.in/validation). Every tool you \
have is free for every user. Today is {datetime.now():%d %b %Y}.

Catalog right now: {stats.get("bikes")} bikes, {stats.get("parts")} parts, \
{stats.get("tires")} tires, {stats.get("venues")} venues.

CORE DISCIPLINE — these rules are absolute:
1. NEVER invent a physics number. Every ET, trap speed, top speed, or delta \
you state MUST come from a tool result in this conversation. Quote ETs to 3 \
decimals, trap speeds to 1.
2. NEVER invent parts, prices, or specs. Parts come from search_parts / \
optimize_build; specs from get_bike_details or verified web sources.
3. If the user's bike is not in the catalog: gather REAL specs (your own \
knowledge if you are confident, web_search/web_fetch if not), then use \
simulate_estimated_bike. ALWAYS present those results as estimates with \
their confidence score and key assumptions — never as validated numbers.
4. When you use web facts, cite the source URL inline.
5. If a tool returns an error, adapt (fix arguments, try another tool) or \
tell the user honestly what failed. Never fabricate a replacement result.

BUILD-STAGE GLOSSARY (use these definitions consistently):
{tiers}
"Outlaw class" / "open class" build requests = stage_4: run \
optimize_build with build_tier="stage_4" — it composes drag rubber, the \
full-race parts knapsack, gearing + launch autotune and a combined \
verification sim, with no budget limit.

HOW TO WORK:
- Simple factual/conceptual questions (physics, technique, rules, product): \
answer directly; use tools only when they add real numbers.
- Any question about a specific bike's performance: search_bikes → \
run_simulation (with venue/conditions when mentioned). Follow-ups inherit \
context from the conversation — reuse known bike_ids instead of re-searching.
- "Fastest/quickest <class>" questions: use rank_bikes (one call, real sims) \
— do NOT search and simulate bikes one at a time.
- "Best possible / fastest configuration" for a bike = stage_4 outlaw \
optimize_build. Summarize the result: baseline → final ET, the parts list \
with prices, the gearing/launch setup, and total cost.
- Be a race engineer in tone: precise, numbers-first, no hype. Use km/h \
(mention mph for US bikes). Prices in ₹ (INR).
- Budgets: you have {FULL_SIM_BUDGET} full sims and {HEAVY_OP_BUDGET} heavy \
operations (optimizer/autotune) per message — plan tool use accordingly.
- End with the answer, not with what you did. Keep replies tight: lead with \
the number(s), then the how/why in 2-6 sentences, then optional next steps."""


# ─── Main loop ────────────────────────────────────────────────────────────


def _clip_history(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cap client-supplied history: last N messages, total chars bounded."""
    if not messages:
        return []
    clipped = [
        {"role": m.get("role"), "content": (m.get("content") or "")[:4000]}
        for m in messages
        if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
    ][-HISTORY_MAX_MESSAGES:]
    total = 0
    out: list[dict[str, Any]] = []
    for m in reversed(clipped):
        total += len(m["content"])
        if total > HISTORY_MAX_CHARS:
            break
        out.append(m)
    return list(reversed(out))


def run_agent_chat(
    query: str,
    db,
    *,
    client: LLMClient | None = None,
    history: list[dict[str, Any]] | None = None,
    progress_cb: Callable[[float, str | None], None] | None = None,
    surrogate_getter: Callable[[], tuple[Any, str]] | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> AgentChatResult:
    """Run one agent chat turn. Never raises — errors land on the result.

    Cost is bounded per turn by MAX_ITERATIONS / FULL_SIM_BUDGET /
    HEAVY_OP_BUDGET (enforced by the executor) and per client by the API's
    rate limits (see api._chat_daily_cap).
    """
    result = AgentChatResult(raw_query=query)
    if client is None:
        from .client import get_default_client

        client = get_default_client()

    if not client.is_configured:
        result.error = "llm_not_configured"
        result.error_detail = (
            f"LLM provider {client.provider!r} is not configured — set the "
            f"provider API key (e.g. GROQ_API_KEY) on the server"
        )
        return result

    ctx = AgentContext(
        db=db,
        result=result,
        progress_cb=progress_cb,
        surrogate_getter=surrogate_getter,
    )

    system = _system_prompt(ctx)
    messages: list[dict[str, Any]] = _clip_history(history or [])
    messages.append({"role": "user", "content": query})

    for iteration in range(max_iterations):
        result.iterations = iteration + 1
        ctx.tick(
            min(0.9, 0.1 + iteration * (0.8 / max_iterations)),
            "Thinking" if iteration == 0 else None,
        )
        try:
            step: AgentStep = client.call_tools(
                system, messages, AGENT_TOOLS, max_tokens=AGENT_MAX_TOKENS
            )
        except LLMRateLimitError as e:
            result.error = "rate_limited"
            result.error_detail = str(e)
            return result
        except LLMNotConfiguredError as e:
            result.error = "llm_not_configured"
            result.error_detail = str(e)
            return result
        except Exception as e:  # noqa: BLE001
            result.error = "agent_failed"
            result.error_detail = f"{type(e).__name__}: {e}"
            return result

        if not step.tool_calls:
            result.reply = step.text or ""
            ctx.tick(1.0, "Done")
            return result

        # Record the assistant turn, then execute every requested tool.
        messages.append(
            {
                "role": "assistant",
                "content": step.text,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in step.tool_calls
                ],
            }
        )
        for tc in step.tool_calls:
            payload = execute_tool(ctx, tc)
            result.tool_trace.append(
                {
                    "tool": tc.name,
                    "ok": "error" not in payload,
                    "error": payload.get("error"),
                }
            )
            content = json.dumps(payload, default=str)
            if len(content) > TOOL_RESULT_MAX_CHARS:
                content = content[:TOOL_RESULT_MAX_CHARS] + '… (truncated)"}'
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": content,
                }
            )

    # Iteration budget exhausted — ask for a final answer without tools.
    try:
        messages.append(
            {
                "role": "user",
                "content": (
                    "(system: tool budget exhausted — give your final answer "
                    "now using only the results above)"
                ),
            }
        )
        step = client.call_tools(system, messages, [], max_tokens=AGENT_MAX_TOKENS)
        result.reply = step.text or ""
    except Exception as e:  # noqa: BLE001
        result.error = "agent_failed"
        result.error_detail = f"iteration budget exhausted: {type(e).__name__}: {e}"
    ctx.tick(1.0, "Done")
    return result
