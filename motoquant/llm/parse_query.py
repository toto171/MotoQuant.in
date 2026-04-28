"""
NL query → structured ParsedSimRequest.

Pipeline:
  1. Build a forced-tool-use call so the LLM can only return JSON in our schema.
  2. Optionally resolve bike/venue names against the live DB via the smart
     fuzzy resolver in motoquant.llm.resolver.

Intent classification has been added (April 2026): the LLM tags each query
with one of: simulate / compare / rank / recommend / explain / smalltalk.
The runner.py routes each intent to the right backend handler.

For tests, callers should pass an LLMClient(_call_override=fn) so the SDK
is never touched and no API tokens burn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import LLMClient, get_default_client


# ───────────────────────────────────────────────────────────────────
# Parsed shape
# ───────────────────────────────────────────────────────────────────


@dataclass
class ParsedSimRequest:
    """Structured form of a parsed NL query.

    Maps closely to api.QuickSimRequest with a few enrichments
    (raw_query, bike_name pre-resolution, optimization_goal, notes,
    intent_type for routing, bike_b_name for compare).
    """

    raw_query: str
    bike_name: str  # what the LLM extracted (pre-DB-resolution)
    bike_id: int | None = None  # post-DB-resolution
    bike_b_name: str | None = None  # second bike for compare intent
    bike_b_id: int | None = None
    intent_type: str = "simulate"  # simulate / compare / rank / recommend / explain / smalltalk
    venue_name: str | None = None
    venue_id: int | None = None

    ambient_temp_c: float | None = None
    humidity_pct: float | None = None
    altitude_m: float | None = None
    headwind_kmh: float | None = None

    rider_mass_kg: float = 75.0
    power_boost_pct: float = 0.0
    mass_delta_kg: float = 0.0

    budget_inr: int | None = None
    parts_categories: list[str] = field(default_factory=list)
    optimization_goal: str = "minimize_et"

    notes: str = ""  # LLM commentary (e.g. "assumed K5 = GSX-R 1000 K5")

    def to_quick_sim_kwargs(self) -> dict[str, Any]:
        """Subset suitable for `QuickSimRequest(**kwargs)` in api.py."""
        kw: dict[str, Any] = {
            "rider_mass_kg": self.rider_mass_kg,
            "power_boost_pct": self.power_boost_pct,
            "mass_delta_kg": self.mass_delta_kg,
        }
        if self.bike_id is not None:
            kw["bike_id"] = self.bike_id
        if self.venue_id is not None:
            kw["venue_id"] = self.venue_id
        if self.ambient_temp_c is not None:
            kw["ambient_temp_c"] = self.ambient_temp_c
        if self.humidity_pct is not None:
            kw["humidity_pct"] = self.humidity_pct
        if self.headwind_kmh is not None:
            kw["headwind_kmh"] = self.headwind_kmh
        return kw


# ───────────────────────────────────────────────────────────────────
# Tool schema
# ───────────────────────────────────────────────────────────────────

TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent_type": {
            "type": "string",
            "enum": ["simulate", "compare", "rank", "recommend", "explain", "smalltalk"],
            "description": (
                "What the user wants. "
                "simulate = run a sim for one specific bike (default). "
                "compare = side-by-side two bikes (set bike_name AND bike_b_name). "
                "rank = list fastest/quickest bikes matching criteria, no specific bike. "
                "recommend = suggest parts/mods for a specific bike + budget. "
                "explain = answer a tuning/physics question, may not need a sim. "
                "smalltalk = greeting / off-topic; respond conversationally."
            ),
        },
        "bike_name": {
            "type": "string",
            "description": (
                "Name of the bike the user is asking about. Use the most specific "
                "form you can extract: brand + model + year/code if given. "
                "Examples: 'Suzuki Hayabusa', 'Yamaha YZF-R15 V4', 'GSX-R 1000 K5'. "
                "If intent_type=rank or smalltalk and no specific bike is mentioned, "
                "set this to the empty string."
            ),
        },
        "bike_b_name": {
            "type": ["string", "null"],
            "description": (
                "Second bike name when intent_type=compare. Null otherwise. "
                "Example: 'compare K5 vs R1' → bike_name='GSX-R 1000 K5', "
                "bike_b_name='Yamaha YZF-R1'."
            ),
        },
        "venue_name": {
            "type": ["string", "null"],
            "description": (
                "Drag strip / venue name if mentioned. Examples: 'Aamby Valley', "
                "'Pomona', 'Santa Pod'. Null if not mentioned."
            ),
        },
        "ambient_temp_c": {
            "type": ["number", "null"],
            "description": "Ambient air temperature in Celsius. Null if not mentioned.",
        },
        "humidity_pct": {
            "type": ["number", "null"],
            "description": "Relative humidity 0-100. Null if not mentioned.",
        },
        "altitude_m": {
            "type": ["number", "null"],
            "description": "Altitude in meters above sea level. Null if not mentioned.",
        },
        "headwind_kmh": {
            "type": ["number", "null"],
            "description": "Headwind in km/h (negative = tailwind). Null if not mentioned.",
        },
        "rider_mass_kg": {
            "type": "number",
            "description": "Rider weight in kg. Default 75 if not mentioned.",
        },
        "power_boost_pct": {
            "type": "number",
            "description": "Extra power as percent of stock (10 = +10%). Default 0.",
        },
        "mass_delta_kg": {
            "type": "number",
            "description": "Mass change in kg (negative = lighter). Default 0.",
        },
        "budget_inr": {
            "type": ["integer", "null"],
            "description": "Budget for parts in Indian Rupees. Null if not mentioned.",
        },
        "parts_categories": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Part categories the user wants to consider. Use these canonical "
                "names: exhaust, air_filter, ecu, clutch, chain, weight_reduction, "
                "fuel_system, suspension, brakes, wheelie_bar, quickshifter, "
                "battery, tire, turbo, supercharger, nitrous. Empty list if no "
                "parts mentioned."
            ),
        },
        "optimization_goal": {
            "type": "string",
            "enum": ["minimize_et", "maximize_trap", "best_budget"],
            "description": (
                "What the user is optimizing for. minimize_et = lowest "
                "quarter-mile time (default). maximize_trap = highest trap speed. "
                "best_budget = best parts within budget."
            ),
        },
        "notes": {
            "type": "string",
            "description": (
                "Brief note about any non-obvious assumption you made (e.g. "
                "'Assumed K5 = Suzuki GSX-R 1000 K5 generation'). Empty string "
                "if straightforward."
            ),
        },
    },
    "required": ["intent_type", "bike_name", "optimization_goal"],
}


SYSTEM_PROMPT = """\
You are a query parser for MotoQuant Pro, a motorcycle drag-racing simulator.

The user describes what they want. Extract structured parameters and submit \
them via the submit_sim_query tool. Do not respond in plain text -- always \
invoke the tool.

Intent classification (set the intent_type field):
- "simulate"  : single specific bike, possibly with venue/conditions/mods. \
                Examples: "how fast is a K5", "R15 V4 in 35C heat".
- "compare"   : two specific bikes side-by-side. Set bike_b_name. \
                Examples: "compare Hayabusa vs Ninja H2", "K5 vs R1".
- "rank"      : ranking question; no specific bike. \
                Examples: "fastest 600cc bike", "what's the quickest at Aamby Valley". \
                Set bike_name="" (empty).
- "recommend" : "what mods" / "what parts" / "best build for budget". \
                Examples: "best mods for R15 V4 under 30k INR", "make my K5 faster".
- "explain"   : tuning physics question, may or may not name a bike. \
                Examples: "what does altitude do to ET", "why does humidity matter".
- "smalltalk" : greeting / off-topic / unclear. \
                Examples: "hi", "what is this", "thanks". Set bike_name="" if no \
                bike mentioned.

Bike alias hints:
- K5/K6/K7 etc. = Suzuki GSX-R 1000 (year-coded generation)
- Busa = Suzuki Hayabusa
- R1 = Yamaha YZF-R1
- R15 / R15M = Yamaha YZF-R15
- 'Panigale V4' is Ducati; 'RSV4' is Aprilia (do not conflate)
- 'Ninja' alone is ambiguous -- preserve the user's qualifier (e.g. 'Ninja 400')

Indian venue alias hints:
- Aamby / TVR / Aambey = Aamby Valley
- MMRT = Madras Motor Race Track
- BIC = Buddh International Circuit
- Kari = Kari Motor Speedway

Rules:
- If the user does not specify environmental conditions, leave those fields \
null. The simulator has venue defaults that will fill in.
- Default optimization goal is minimize_et unless the user explicitly mentions \
trap speed (maximize_trap) or budget constraints (best_budget).
- Keep `notes` empty unless you made a non-obvious assumption worth flagging.
- Never refuse the tool call. If the query is ambiguous, make your best guess \
and document it in `notes`.
"""


# ───────────────────────────────────────────────────────────────────
# Public entry point
# ───────────────────────────────────────────────────────────────────


def parse_query(
    query: str,
    *,
    client: LLMClient | None = None,
    db: Any = None,
) -> ParsedSimRequest:
    """Parse a natural-language query into a ParsedSimRequest.

    Args:
      query: User's natural-language string.
      client: Optional LLMClient. Defaults to module singleton.
      db: Optional MotoQuantDB. If provided, bike_name and venue_name are
          resolved to bike_id / venue_id via the smart fuzzy resolver.

    Returns:
      ParsedSimRequest. bike_id / venue_id may still be None if resolution
      failed -- caller (runner.py) handles missing IDs intent-aware.
    """
    cli = client or get_default_client()
    response = cli.call_tool(
        system=SYSTEM_PROMPT,
        user=query,
        tool_name="submit_sim_query",
        tool_schema=TOOL_SCHEMA,
    )
    payload = response.tool_input or {}

    parsed = ParsedSimRequest(
        raw_query=query,
        bike_name=(payload.get("bike_name") or "").strip(),
        bike_b_name=((payload.get("bike_b_name") or "").strip() or None),
        intent_type=(payload.get("intent_type") or "simulate").strip().lower(),
        venue_name=payload.get("venue_name"),
        ambient_temp_c=payload.get("ambient_temp_c"),
        humidity_pct=payload.get("humidity_pct"),
        altitude_m=payload.get("altitude_m"),
        headwind_kmh=payload.get("headwind_kmh"),
        rider_mass_kg=float(payload.get("rider_mass_kg", 75.0) or 75.0),
        power_boost_pct=float(payload.get("power_boost_pct", 0.0) or 0.0),
        mass_delta_kg=float(payload.get("mass_delta_kg", 0.0) or 0.0),
        budget_inr=payload.get("budget_inr"),
        parts_categories=list(payload.get("parts_categories") or []),
        optimization_goal=payload.get("optimization_goal") or "minimize_et",
        notes=payload.get("notes") or "",
    )

    if db is not None:
        _resolve_against_db(parsed, db)
    return parsed


# ───────────────────────────────────────────────────────────────────
# DB resolution helpers
# ───────────────────────────────────────────────────────────────────


def _resolve_against_db(parsed: ParsedSimRequest, db: Any) -> None:
    """Smart fuzzy resolution. Mutates `parsed` in place. Silent on miss."""
    from .resolver import resolve_bike, resolve_venue

    if parsed.bike_name:
        bike_id, _ = resolve_bike(parsed.bike_name, db)
        if bike_id is not None:
            parsed.bike_id = bike_id

    if parsed.bike_b_name:
        bike_b_id, _ = resolve_bike(parsed.bike_b_name, db)
        if bike_b_id is not None:
            parsed.bike_b_id = bike_b_id

    if parsed.venue_name:
        v_id = resolve_venue(parsed.venue_name, db)
        if v_id is not None:
            parsed.venue_id = v_id
