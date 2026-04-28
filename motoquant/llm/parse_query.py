"""
parse_query -- turn a natural-language query into a structured ParsedSimRequest.

Pipeline
--------
  1. LLM extracts: bike_name, venue_name, env params, parts list, goal
     (forced via tool-use, never plain text)
  2. Local code resolves bike_name -> bike_id via DB fuzzy match (optional)
  3. Local code resolves venue_name -> venue_id via DB lookup (optional)
  4. Returns ParsedSimRequest -- maps cleanly to api.QuickSimRequest

Why two-stage (LLM + local resolution):
  - Keeps the LLM prompt tiny (don't dump 327 bike rows into context every call)
  - Reuses the existing fuzzy-matching logic in BikesRepository.search()
  - Cheap: ~$0.01/query at Claude Sonnet 4.6 rates with ~1k token output

Usage
-----
    from motoquant.llm import parse_query
    from motoquant.database.connection import MotoQuantDB

    db = MotoQuantDB("motoquant.db")
    parsed = parse_query("optimize my K5 for 35C at Aamby Valley", db=db)
    print(parsed.bike_id, parsed.ambient_temp_c)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import LLMClient, get_default_client

__all__ = ["ParsedSimRequest", "parse_query", "TOOL_SCHEMA", "SYSTEM_PROMPT"]


# ───────────────────────────────────────────────────────────────────
# ParsedSimRequest -- output dataclass
# ───────────────────────────────────────────────────────────────────


@dataclass
class ParsedSimRequest:
    """Structured form of a parsed NL query.

    Maps closely to api.QuickSimRequest with a few enrichments
    (raw_query, bike_name pre-resolution, optimization_goal, notes).
    """

    raw_query: str
    bike_name: str  # what the LLM extracted (pre-DB-resolution)
    bike_id: int | None = None  # post-DB-resolution
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
        """Subset suitable for `QuickSimRequest(**kwargs)` in api.py.

        Skips None values so QuickSimRequest's own defaults kick in.
        """
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
# Tool schema -- Anthropic forces the model to produce this shape
# ───────────────────────────────────────────────────────────────────

TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "bike_name": {
            "type": "string",
            "description": (
                "Name of the bike the user is asking about. "
                "Use the most specific form you can extract: brand + model + "
                "year/code if given. Examples: 'Suzuki Hayabusa', "
                "'Yamaha YZF-R15 V4', 'GSX-R 1000 K5'."
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
                "Part categories the user wants to consider. "
                "Use these canonical names: exhaust, air_filter, ecu, clutch, "
                "chain, weight_reduction, fuel_system, suspension, brakes, "
                "wheelie_bar, quickshifter, battery, tire, turbo, supercharger, "
                "nitrous. Empty list if no parts mentioned."
            ),
        },
        "optimization_goal": {
            "type": "string",
            "enum": ["minimize_et", "maximize_trap", "best_budget"],
            "description": (
                "What the user is optimizing for. "
                "minimize_et = lowest quarter-mile time (default). "
                "maximize_trap = highest trap speed. "
                "best_budget = best parts within budget."
            ),
        },
        "notes": {
            "type": "string",
            "description": (
                "Brief note about any non-obvious assumption you made (e.g. "
                "'Assumed K5 = Suzuki GSX-R 1000 K5 generation'). "
                "Empty string if straightforward."
            ),
        },
    },
    "required": ["bike_name", "optimization_goal"],
}


SYSTEM_PROMPT = """\
You are a query parser for MotoQuant Pro, a motorcycle drag-racing simulator.

The user describes what they want to simulate or optimize. Extract structured \
parameters and submit them via the submit_sim_query tool. Do not respond in \
plain text -- always invoke the tool.

Bike alias hints:
- K5/K6/K7 etc. = Suzuki GSX-R 1000 (year-coded generation)
- Busa = Suzuki Hayabusa
- R1 = Yamaha YZF-R1
- R15 / R15M = Yamaha YZF-R15
- 'Panigale V4' is Ducati; 'RSV4' is Aprilia (do not conflate)
- 'Ninja' alone is ambiguous -- preserve the user's qualifier (e.g. 'Ninja 400')

Indian venue alias hints:
- Aamby / TVR = Aamby Valley
- MMRT = Madras Motor Race Track
- BIC = Buddh International Circuit

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
          resolved to bike_id / venue_id via DB lookup.

    Returns:
      ParsedSimRequest. bike_id / venue_id may still be None if resolution
      failed -- caller should check and fall back gracefully.

    Raises:
      LLMNotConfiguredError: no API key and no _call_override.
      RuntimeError: model refused to invoke the tool.
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
    """Best-effort fuzzy resolution. Mutates `parsed` in place. Silent on miss."""
    if parsed.bike_name:
        try:
            rows = db.bikes.search(name_contains=parsed.bike_name)
            if rows:
                parsed.bike_id = rows[0]["id"]
        except Exception:
            # Don't fail parse on DB error; caller handles missing bike_id.
            pass

    if parsed.venue_name:
        try:
            venue = db.venues.get_by_name(parsed.venue_name)
            if venue:
                parsed.venue_id = venue["id"]
        except Exception:
            pass
