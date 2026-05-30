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
from typing import TYPE_CHECKING, Any, TypedDict

import numpy as np

from ..constants import MS_TO_KMH, MS_TO_MPH
from ..physics import MotoQuantEngine
from .client import LLMClient, LLMNotConfiguredError
from .parse_query import ParsedSimRequest, parse_query
from .summarize import summarize_result

if TYPE_CHECKING:
    from ..database.connection import MotoQuantDB

__all__ = ["ChatResult", "run_chat_pipeline"]


# ───────────────────────────────────────────────────────────────────
# SimDict — typed shape returned by _run_one_sim on success
# ───────────────────────────────────────────────────────────────────


class _SimDictBase(TypedDict):
    """Required fields always present in a successful _run_one_sim result.

    Key names are pinned by the frontend UIs (web ChatPanel + desktop ChatBox);
    do NOT rename without updating both surfaces.
    """

    et_quarter_s: float    # quarter-mile elapsed time in seconds
    trap_speed_kmh: float  # trap speed in km/h
    trap_speed_mph: float  # trap speed in mph
    et_60ft_s: float       # 60-foot split in seconds
    peak_accel_g: float    # peak longitudinal acceleration in g
    bike_name: str         # human-readable bike name (filled in by caller)


class SimDict(_SimDictBase, total=False):
    """Full sim result dict including optional split-time fields.

    The three split fields are added only when the ``SimResult`` object
    carries the corresponding attribute (they are absent for bikes that DNF
    or for simulations shorter than the split distance).
    """

    et_330ft_s: float   # 330-foot split (if available)
    et_eighth_s: float  # 1/8-mile split  (if available)
    et_1000ft_s: float  # 1000-foot split (if available)


# ───────────────────────────────────────────────────────────────────
# CompareDict — typed shape returned by _run_compare on success
# ───────────────────────────────────────────────────────────────────


class _CompareBikeEntry(TypedDict):
    """One side (A or B) of a head-to-head compare result.

    ``bike_id`` and ``bike_name`` are pulled directly from the parsed
    request; ``sim`` is the SimDict produced by `_run_one_sim` for that
    bike.
    """

    bike_id: int | None
    bike_name: str | None
    sim: SimDict


class CompareDict(TypedDict):
    """Full compare-intent result dict.

    Shape pinned by `_summarize_compare` (which reads ``a``, ``b``,
    ``delta_et_s``, ``delta_trap_kmh``, ``faster``) and by the web/desktop
    ChatPanel surfaces — do NOT rename without updating both consumers.
    """

    a: _CompareBikeEntry
    b: _CompareBikeEntry
    delta_et_s: float       # A.et_quarter_s - B.et_quarter_s, rounded to 4dp
    delta_trap_kmh: float   # A.trap_speed_kmh - B.trap_speed_kmh, rounded to 1dp
    faster: str             # "A" | "B" | "tie"


# ───────────────────────────────────────────────────────────────────
# RankResult — typed shape returned by _run_rank on success
# ───────────────────────────────────────────────────────────────────


class _RankEntry(TypedDict):
    """One row in the ``RankResult.top`` list.

    Field names are pinned by `_summarize_rank` (which reads
    ``rank``, ``manufacturer``, ``model``, ``displacement_cc``,
    ``peak_power_hp``, ``et_s``, ``trap_kmh``) and by the validation
    corpus harness — do NOT rename without updating both consumers.
    """

    rank: int
    bike_id: int | None
    manufacturer: str | None
    model: str | None
    year_from: int | None
    displacement_cc: float | None
    peak_power_hp: float | None
    dry_mass_kg: float | None
    et_s: float | None
    trap_kmh: float | None
    et_60ft_s: float | None
    source: str | None


class RankResult(TypedDict):
    """Full rank-intent result dict.

    Shape pinned by `_summarize_rank` (which reads ``top``, ``filter``,
    ``matches``, ``candidates_simulated``) and the validate_chat_corpus
    harness (which reads ``top``) — do NOT rename without updating both.
    """

    filter: dict[str, Any]      # subset of parsed-query kw (limit stripped)
    matches: int                # total catalog rows matching the filter
    candidates_simulated: int   # subset actually run through the engine
    top: list[_RankEntry]       # top-N sorted by sim ET ascending


# ───────────────────────────────────────────────────────────────────
# RecommendResult — typed shape returned by _run_recommend on success
# ───────────────────────────────────────────────────────────────────


class _RecommendPart(TypedDict):
    """One row in the ``RecommendResult.parts`` list.

    Field names are pinned by `_summarize_recommend` (which reads
    ``label``, ``brand``, ``name``, ``price_inr``, ``fitment_reason``,
    ``category``, ``category_display``) — do NOT rename.
    """

    part_id: int | None
    label: str | None
    name: str | None
    brand: str | None
    category: str | None
    category_display: str | None
    price_inr: float | None
    fitment_reason: str | None


class _RecommendTire(TypedDict):
    """One row in the ``RecommendResult.tires`` list.

    Field names are pinned by `_summarize_recommend` tire block (which
    reads ``manufacturer``, ``model``, ``size``, ``mu_peak``,
    ``position``, ``fitment_type``, ``price_inr``).
    """

    tire_model_id: int | None
    manufacturer: str | None
    model: str | None
    size: str | None
    compound: str | None
    mu_peak: float | None
    position: str | None
    fitment_type: str | None
    price_inr: float | None


class RecommendResult(TypedDict):
    """Full recommend-intent result dict.

    Shape pinned by `_summarize_recommend` (which reads ``bike_name``,
    ``budget_inr``, ``parts``, ``tires``, ``total_inr``) and the
    validate_chat_corpus harness (which reads ``build_tier`` and
    ``parts``) — do NOT rename without updating both.
    """

    bike_id: int | None
    bike_name: str | None
    build_tier: str             # "stage_1" | "stage_2" | "all_out"
    budget_inr: float | None    # user-requested budget (None = unspecified)
    effective_budget_inr: float # tier-default fallback when budget_inr is None
    parts: list[_RecommendPart]
    tires: list[_RecommendTire]
    total_inr: float            # sum of parts + tires price_inr


# ───────────────────────────────────────────────────────────────────
# ExplainResult — typed shape returned by _run_explain on success
# ───────────────────────────────────────────────────────────────────


class ExplainResult(TypedDict):
    """Full explain-intent result dict.

    Note: the LLM-generated text answer is stored in ``ChatResult.summary``;
    ``ExplainResult`` only carries the structured metadata about whether the
    answer was grounded in a sim run.
    """

    has_sim_grounding: bool     # True iff a sim was run to anchor the explanation
    bike_id: int | None         # bike resolved from the parsed query (or None)


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
    sim_result: SimDict | None = None  # simulate
    compare_result: CompareDict | None = None  # compare
    rank_result: RankResult | None = None  # rank
    recommend_result: RecommendResult | None = None  # recommend
    explain_result: ExplainResult | None = None  # explain

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
    db: MotoQuantDB,
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
    if intent == "choose_bike":
        return _run_choose_bike(
            parsed, db, client, result, run_summary=run_summary,
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
    db: MotoQuantDB,
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
    db: MotoQuantDB,
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

    compare_payload: CompareDict = {
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
    result.compare_result = compare_payload

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
    db: MotoQuantDB,
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


# Tiered build recipes. Each tier is the ORDERED list of categories to
# include — keys are matched as substrings against parts.category_name (so
# "exhaust" matches both "exhaust" and "exhaust_full_system"). Stage_2
# is the default / safest fallback; stage_1 is light bolt-ons; all_out
# adds suspension + brakes + drag prep.
#
# Tuple shape: (substring_match_key, display_label_for_prompt).

_TIER_STAGE_1 = [
    ("exhaust",      "Exhaust"),
    ("air_filter",   "Air filter"),
    ("ecu",          "ECU flash / piggyback"),
    ("fuel_system",  "Fuel system"),
]

_TIER_STAGE_2 = _TIER_STAGE_1 + [
    ("clutch",       "Clutch / slipper"),
    ("quickshifter", "Quickshifter"),
    ("sprocket",     "Sprocket"),
    ("chain",        "Chain"),
    ("battery",      "Lightweight battery"),
]

_TIER_ALL_OUT = _TIER_STAGE_2 + [
    ("suspension",        "Suspension"),
    ("brakes",            "Brakes"),
    ("weight_reduction",  "Weight reduction"),
    ("nitrous",           "Nitrous"),
    ("boost",             "Boost / forced induction"),
    ("wheelie",           "Wheelie / launch aid"),
]

_TIER_RECIPES = {
    "stage_1":  _TIER_STAGE_1,
    "stage_2":  _TIER_STAGE_2,
    "all_out":  _TIER_ALL_OUT,
}

# Soft budget caps when the user didn't specify one. These are guidance —
# the recommend handler will pick the highest-priced compatible part within
# the tier ceiling so a stage_1 ask doesn't return Öhlins and Brembo Stylema.
_TIER_DEFAULT_BUDGET_INR = {
    "stage_1":  60_000,
    "stage_2": 200_000,
    "all_out": None,  # no cap
}


def _run_recommend(
    parsed: ParsedSimRequest,
    db: MotoQuantDB,
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

        # 3. Group by canonical category, sort each by price.
        #    Tier-aware ordering so stage_1 picks the cheapest viable option
        #    in each category (don't blow the budget on the first pick),
        #    stage_2 picks middle-tier, and all_out goes premium-first.
        tier_for_sort = (parsed.build_tier or "stage_2").lower()
        by_cat: dict[str, list[dict[str, Any]]] = {}
        for p in parts:
            cat = (p.get("category_name") or "uncategorized").lower()
            by_cat.setdefault(cat, []).append(p)
        for lst in by_cat.values():
            if tier_for_sort == "stage_1":
                # Cheapest first: a budget user wants the entry-tier upgrade,
                # not the Akrapovic. Skip zero-price entries — those are
                # placeholder rows without real pricing.
                lst.sort(key=lambda p: float(p.get("price_inr") or 9_999_999))
            elif tier_for_sort == "all_out":
                # Premium first: no-budget user wants the Öhlins / Brembo /
                # Akrapovic pick. Sort by price descending.
                lst.sort(key=lambda p: -float(p.get("price_inr") or 0))
            else:
                # stage_2 (default): pick the median-price part in each
                # category. Sort ascending then access middle index later.
                lst.sort(key=lambda p: float(p.get("price_inr") or 0))

        # 4. Walk the priority list for the user's chosen build tier and pick
        #    one part per category until budget is roughly spent (allow 20 %
        #    headroom — better to over-build than leave the user with a half-
        #    finished plan). Stage_1 implicitly excludes high-cost categories
        #    (suspension/brakes/weight). All_out skips the budget cap entirely.
        tier = (parsed.build_tier or "stage_2").lower()
        recipe = _TIER_RECIPES.get(tier, _TIER_STAGE_2)
        # Effective budget: explicit > tier default > infinite
        effective_budget = (
            budget
            if budget is not None
            else _TIER_DEFAULT_BUDGET_INR.get(tier)
        )
        budget_cap = (
            effective_budget * 1.2 if effective_budget else float("inf")
        )
        selected: list[dict[str, Any]] = []
        used_budget = 0.0
        for cat_key, cat_label in recipe:
            # Find any cat_name in by_cat that contains the priority key
            candidates: list[dict[str, Any]] = []
            for cat_name, lst in by_cat.items():
                if cat_key in cat_name:
                    candidates.extend(lst)
            if not candidates:
                continue
            # For stage_2 prefer the median candidate so we don't always
            # pick the cheapest (would feel like a stage_1 recommend) or the
            # most expensive (would leave nothing for other categories).
            if tier_for_sort == "stage_2" and len(candidates) > 1:
                mid = len(candidates) // 2
                ordered = candidates[mid:] + candidates[:mid]
            else:
                ordered = candidates
            for p in ordered:
                price = float(p.get("price_inr") or 0)
                if used_budget + price > budget_cap:
                    continue
                selected.append({"_label": cat_label, **p})
                used_budget += price
                break
            if effective_budget and used_budget >= effective_budget * 0.95:
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
            "build_tier": tier,
            "budget_inr": budget,
            "effective_budget_inr": effective_budget,
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
    db: MotoQuantDB,
    client: LLMClient | None,
    result: ChatResult,
    *,
    run_summary: bool,
) -> ChatResult:
    """Answer a tuning/physics question with optional sim grounding.

    If a specific bike was identified, run a quick sim and use its numbers as
    grounding for the explanation. Otherwise rely purely on the LLM.
    """
    sim_for_context: SimDict | None = None
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
    bike_id: int, parsed: ParsedSimRequest, db: MotoQuantDB
) -> SimDict | str:
    """Run a single sim for `bike_id` with `parsed`'s overrides applied.

    Returns a :class:`SimDict` on success or an error string on failure.
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

    out: SimDict = {
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
    db: MotoQuantDB, bike_name: str, *, limit: int = 5
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
    parsed: ParsedSimRequest, comp: CompareDict, client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant, a drag-racing tuner. Compare these two bikes "
        "definitively. Format: "
        "(1) one-line winner with explicit ΔET in seconds and Δtrap in km/h. "
        "(2) 1-2 sentences on WHY the winner wins — cite the actual P/W "
        "ratio difference, gearing advantage, or aero (use the data given). "
        "(3) One trade-off line — the loser is better at X (price, "
        "Indian-market availability, parts ecosystem, top speed past 1/4). "
        "STRICT: cite actual sim ETs to 3 decimals and trap to 1 decimal. "
        "Do not invent specs. No 'in conclusion' / 'overall' filler. "
        "No bullet points unless required. Aim 50-80 words total."
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
    parsed: ParsedSimRequest, rk: RankResult, client: LLMClient | None
) -> str:
    sys_p = (
        "You are MotoQuant. Summarize a ranked top-N drag list. Format: "
        "(1) one-line podium (1st-3rd by sim ET with explicit times). "
        "(2) For #1 only, 1-2 sentences on what gives it the edge "
        "(P/W ratio, gearing, weight, aero — use whatever the data shows). "
        "(3) Two-line aside on a notable runner-up if interesting (e.g. "
        "newer / cheaper / Indian-market / more affordable parts). "
        "STRICT: cite actual sim ETs to 3 decimals; do not invent specs. "
        "No filler verbs. 60-100 words total."
    )
    top = rk.get("top", [])[:5]
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
        f"Filter applied: {rk.get('filter')}\n"
        f"Total catalog matches: {rk.get('matches')}\n"
        f"Bikes simulated: {rk.get('candidates_simulated', '?')}\n\n"
        f"Top results (sorted by physics-engine ET):\n" + "\n".join(lines)
    )
    return _llm_text(client, sys_p, user)


def _summarize_recommend(
    parsed: ParsedSimRequest, rec: RecommendResult, client: LLMClient | None
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
        f"Budget: ₹{budget:,}\n" if budget else "Budget: (unspecified)\n"
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
    sim_context: SimDict | None,
    client: LLMClient | None,
) -> str:
    sys_p = (
        "You are MotoQuant, a drag-racing tuner with first-principles physics "
        "background. Answer concretely in 3-5 sentences. STRICT RULES: "
        "(1) If a sim result is in the data, cite exact ET / trap / 60ft. "
        "(2) If you state a physical effect (rho, DA, traction), give a "
        "specific number / ratio / direction (\'+0.05s slower\', "
        "\'8 % less power\') — never \'significantly\' / \'noticeable\' / "
        "\'a bit\'. (3) Indian context: prefer Aamby Valley / MMRT / BIC / "
        "Kari examples; use INR. (4) End with a one-line actionable "
        "takeaway the user can apply at the strip. No preamble."
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


def _apply_archetype(config: Any, parsed: ParsedSimRequest, db: MotoQuantDB) -> None:
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


# ───────────────────────────────────────────────────────────────────
# Intent: CHOOSE_BIKE  (pick best bike for class+venue+budget)
# ───────────────────────────────────────────────────────────────────

# Class -> displacement window + category filter. Used by _run_choose_bike
# to narrow the catalog before running candidate sims.
_CLASS_FILTERS = {
    "litre": {
        "disp_min": 950, "disp_max": 1200,
        "categories": {"sport", "naked"},
        "label": "Litre / open-class superbike",
    },
    "600": {
        "disp_min": 580, "disp_max": 700,
        "categories": {"sport", "naked"},
        "label": "Supersport 600",
    },
    "300": {
        "disp_min": 250, "disp_max": 410,
        "categories": {"sport", "naked"},
        "label": "Entry-level sport 300",
    },
    "twin": {
        "disp_min": 470, "disp_max": 800,
        "categories": {"sport", "naked", "cruiser", "modern_classic"},
        "cylinder_count": 2,
        "label": "Mid-displacement twin",
    },
    "cruiser": {
        "disp_min": 800, "disp_max": 2500,
        "categories": {"cruiser", "muscle"},
        "label": "Cruiser / muscle",
    },
    "2t": {
        "disp_min": 95, "disp_max": 800,
        "stroke_type": 2,
        "label": "Two-stroke (vintage / dirt)",
    },
    "two-stroke": {
        "disp_min": 95, "disp_max": 800,
        "stroke_type": 2,
        "label": "Two-stroke (vintage / dirt)",
    },
    "modified-hayabusa": {
        "model_keywords": ["Hayabusa"],
        "disp_min": 1290, "disp_max": 1350,
        "label": "Pro Street modified Hayabusa",
    },
    "naked": {
        "categories": {"naked", "muscle"},
        "disp_min": 600,
        "label": "Streetfighter / naked",
    },
    "small-cc": {
        "disp_min": 145, "disp_max": 250,
        "categories": {"sport", "naked", "underbone"},
        "label": "Small-cc Indian / SE Asia drag",
    },
}


def _choose_bike_candidate_query(parsed, db):
    """Build SQL + params to fetch candidate bikes for the target_class."""
    cls = (parsed.target_class or "").lower().strip()
    spec = _CLASS_FILTERS.get(cls) or _CLASS_FILTERS["litre"]

    where = ["1=1"]
    params = []

    if spec.get("disp_min"):
        where.append("bm.displacement_cc >= ?")
        params.append(spec["disp_min"])
    if spec.get("disp_max"):
        where.append("bm.displacement_cc <= ?")
        params.append(spec["disp_max"])
    if spec.get("categories"):
        cats = list(spec["categories"])
        ph = ",".join(["?"] * len(cats))
        where.append("LOWER(bm.category) IN (" + ph + ")")
        params.extend(c.lower() for c in cats)
    if spec.get("cylinder_count"):
        where.append("bm.cylinder_count = ?")
        params.append(spec["cylinder_count"])
    if spec.get("model_keywords"):
        for kw in spec["model_keywords"]:
            where.append("bm.model_name LIKE ?")
            params.append("%" + kw + "%")

    if parsed.prefer_indian:
        indian_mfrs = (
            "Bajaj", "TVS", "Hero", "Royal Enfield", "Mahindra", "Yezdi",
            "Jawa", "Indian Motorcycle",
            "Yamaha", "Honda", "Suzuki", "Kawasaki", "KTM", "Triumph",
            "BMW", "Aprilia", "Husqvarna", "CFMoto", "Benelli",
            "Harley-Davidson",
        )
        ph = ",".join(["?"] * len(indian_mfrs))
        where.append("m.name IN (" + ph + ")")
        params.extend(indian_mfrs)

    sql = (
        "SELECT bm.id, bm.model_name, bm.year_from, bm.year_to, "
        "       bm.displacement_cc, bm.peak_power_hp, bm.peak_torque_nm, "
        "       bm.dry_mass_kg, bm.wet_mass_kg, bm.category, "
        "       bm.cylinder_count, m.name AS manufacturer "
        "FROM bike_models bm "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id "
        "WHERE " + " AND ".join(where) + " "
        "ORDER BY (bm.peak_power_hp / "
        "          NULLIF(COALESCE(bm.dry_mass_kg, bm.wet_mass_kg), 0)) DESC "
        "LIMIT 30"
    )
    return sql, params


def _run_choose_bike(parsed, db, client, result, *, run_summary):
    """Pick best bike for target_class + venue + budget."""
    sql, params = _choose_bike_candidate_query(parsed, db)
    try:
        rows = [dict(r) for r in db._conn.execute(sql, params).fetchall()]
    except Exception as e:
        result.error = "choose_bike_failed"
        result.error_detail = "DB query failed: " + type(e).__name__ + ": " + str(e)
        return result

    if not rows:
        result.error = "no_candidates"
        result.error_detail = (
            "No bikes match target_class='" + str(parsed.target_class)
            + "' with prefer_indian=" + str(parsed.prefer_indian)
        )
        return result

    sim_rows = []
    for r in rows[:25]:
        try:
            cfg_row = db.bikes.get_current_config(r["id"])
            if cfg_row is None:
                continue
            env = None
            if parsed.venue_id is not None:
                try:
                    env = db.venues.to_environment(
                        parsed.venue_id, month=datetime.now().month
                    )
                except Exception:
                    env = None
            cfg = db.bikes.to_config(cfg_row["id"], environment=env)
            if cfg is None:
                continue
            _apply_env_overrides(cfg, parsed)
            _apply_archetype(cfg, parsed, db)
            _apply_power_boost(cfg, parsed)
            engine = MotoQuantEngine(cfg)
            sim = engine.run()
            sim_rows.append({
                **r,
                "sim_et_s": round(float(sim.time_quarter), 3),
                "sim_trap_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
                "sim_60ft_s": round(float(getattr(sim, "time_60ft", 0.0) or 0.0), 3),
            })
        except Exception:
            continue

    if not sim_rows:
        result.error = "all_sims_failed"
        result.error_detail = (
            "Found " + str(len(rows)) + " candidate bikes but all sims failed."
        )
        return result

    sim_rows.sort(key=lambda r: r.get("sim_et_s") or 999.0)
    hero = sim_rows[0]
    runners_up = sim_rows[1:5]

    result.choose_bike_result = {
        "target_class": parsed.target_class,
        "class_label": _CLASS_FILTERS.get(
            (parsed.target_class or "").lower(), {}
        ).get("label"),
        "venue_name": parsed.venue_name,
        "venue_id": parsed.venue_id,
        "budget_inr": parsed.budget_inr,
        "prefer_indian": parsed.prefer_indian,
        "candidate_count": len(sim_rows),
        "hero": _slim_choose_row(hero),
        "runners_up": [_slim_choose_row(r) for r in runners_up],
    }

    if run_summary:
        try:
            result.summary = _summarize_choose_bike(
                parsed, result.choose_bike_result, client
            )
        except Exception as e:
            result.summary = (
                "(choose_bike summary failed: " + type(e).__name__ + ": " + str(e) + ")"
            )

    return result


def _slim_choose_row(r):
    return {
        "bike_id": r.get("id"),
        "manufacturer": r.get("manufacturer"),
        "model_name": r.get("model_name"),
        "year_from": r.get("year_from"),
        "year_to": r.get("year_to"),
        "displacement_cc": r.get("displacement_cc"),
        "peak_power_hp": r.get("peak_power_hp"),
        "peak_torque_nm": r.get("peak_torque_nm"),
        "dry_mass_kg": r.get("dry_mass_kg"),
        "category": r.get("category"),
        "sim_et_s": r.get("sim_et_s"),
        "sim_trap_kmh": r.get("sim_trap_kmh"),
        "sim_60ft_s": r.get("sim_60ft_s"),
    }


def _summarize_choose_bike(parsed, cb, client):
    sys_p = (
        "You are MotoQuant, a drag-racing tuner. Build a definitive "
        "bike-pick recommendation from the data below. Format: "
        "(1) one-line hero pick with sim ET + trap, "
        "(2) 2-3 sentences explaining why it wins (P/W ratio, gearing, "
        "available mods in the catalog, Indian-market availability if "
        "prefer_indian=true), (3) bullet list of runners-up with their "
        "sim ETs and the single trade-off. "
        "STRICT: use ONLY the bikes in the data — do not invent specs "
        "or models. Cite the actual sim ET to 3 decimals. No preamble."
    )

    hero = cb.get("hero") or {}
    runners = cb.get("runners_up") or []
    venue = cb.get("venue_name") or "ISA standard conditions"
    cls_label = cb.get("class_label") or cb.get("target_class") or "(unspecified)"

    lines = []
    lines.append("User asked: " + parsed.raw_query)
    lines.append("Class: " + str(cls_label))
    lines.append("Venue: " + str(venue))
    if cb.get("budget_inr"):
        lines.append("Budget hint: ₹" + format(int(cb["budget_inr"]), ","))
    if cb.get("prefer_indian"):
        lines.append("User prefers Indian-market bikes.")
    lines.append("Total candidates evaluated: " + str(cb.get("candidate_count")))
    lines.append("")
    lines.append("HERO PICK:")
    lines.append(
        "  " + str(hero.get("manufacturer")) + " " + str(hero.get("model_name"))
        + " (" + str(hero.get("year_from")) + "-" + str(hero.get("year_to")) + ") — "
        + str(hero.get("displacement_cc")) + "cc, "
        + str(hero.get("peak_power_hp")) + " hp, "
        + str(hero.get("dry_mass_kg")) + " kg dry"
    )
    lines.append(
        "  Sim ET " + str(hero.get("sim_et_s")) + " s @ trap "
        + str(hero.get("sim_trap_kmh")) + " km/h (60ft "
        + str(hero.get("sim_60ft_s")) + " s)"
    )
    lines.append("")
    lines.append("RUNNERS-UP:")
    for r in runners:
        lines.append(
            "  " + str(r.get("manufacturer")) + " " + str(r.get("model_name")) + " — "
            + str(r.get("peak_power_hp")) + " hp / "
            + str(r.get("dry_mass_kg")) + " kg dry, "
            + "sim ET " + str(r.get("sim_et_s")) + " s @ "
            + str(r.get("sim_trap_kmh")) + " km/h"
        )

    return _llm_text(client, sys_p, "\n".join(lines))
