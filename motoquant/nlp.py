"""
MotoQuant — Natural Language Tuning Interface
==================================================
Pure Python NLP parser for translating natural language queries like
"optimize my Hayabusa for 35°C at Aamby Valley with a 50000 INR budget"
into structured parameter overrides.

Phase 4C feature: v1 uses regex/keyword extraction (no Ollama required).
Future: --use-ollama flag will enable LLM-powered parsing (Phase 5).
"""

import re
from dataclasses import dataclass, field

from .database.connection import MotoQuantDB
from .models import (
    TRACK_PJ1,
    TRACK_RUBBER,
    TRACK_VHT,
    BikeConfig,
)
from .physics import MotoQuantEngine, SimResult

__all__ = ["ParsedQuery", "NLQueryParser", "NLSimRunner", "format_nl_result"]

# ═══════════════════════════════════════════
# DESIGN NOTES (Phase 4C)
# ═══════════════════════════════════════════
# v1.0 — Pure Python parser (current)
#   Uses regex patterns to extract:
#   - Bike references ("my Hayabusa", "K5", "R1")
#   - Venue names ("Aamby Valley", "Pomona", "Sydney")
#   - Environmental conditions (temperature, humidity, altitude, wind)
#   - Budget constraints (INR amounts)
#   - Part mentions (turbo, exhaust, weight reduction, etc.)
#   - Optimization goals (minimize ET, maximize trap, best budget)
#
# v2.0 — Ollama LLM parser (Phase 5, planned)
#   If --use-ollama flag provided:
#   1. Send query + BikeConfig JSON schema to local Ollama instance
#   2. Use structured output (JSON mode) to enforce parsing constraints
#   3. Fall back to v1.0 parser if Ollama unavailable
#   4. Base models: Mistral 7B or Phi-3 (efficient, math-aware)
#   5. Example system prompt:
#      "You are a motorcycle drag racing tuner. Parse the user's natural
#       language request and extract: bike name, venue, temperature (°C),
#       humidity (%), budget (INR), parts mentioned, optimization goal.
#       Output valid JSON."
#
# Both versions return the same ParsedQuery dataclass for consistency.


# Parser track-prep words -> the model's prep constants.
_TRACK_PREP_CONSTANTS = {
    "vht": TRACK_VHT,
    "pj1": TRACK_PJ1,
    "rubber": TRACK_RUBBER,
}

# ═══════════════════════════════════════════
# DATACLASS: ParsedQuery
# ═══════════════════════════════════════════


@dataclass
class ParsedQuery:
    """
    Result of parsing a natural language query.
    """

    raw_query: str
    bike_query: str
    venue_query: str | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    altitude_m: float | None = None
    budget_inr: int | None = None
    parts_mentioned: list[str] = field(default_factory=list)
    optimization_goal: str = "minimize_et"  # minimize_et | maximize_trap | best_budget
    headwind_ms: float | None = None  # wind speed (m/s); direction below
    track_prep_type: str | None = None
    wind_direction_deg: float | None = None  # 0 = headwind, 180 = tailwind


# ═══════════════════════════════════════════
# NLQueryParser — Pure Python Pattern Matching
# ═══════════════════════════════════════════


class NLQueryParser:
    """
    Parses natural language queries into structured ParsedQuery objects.
    Uses regex + keyword extraction; does not require Ollama.
    """

    # Common bike name variations
    BIKE_ALIASES = {
        "busa": "hayabusa",
        "gsx1300": "hayabusa",
        "gsx1300r": "hayabusa",
        "gsxr": "gsxr1000",
        "gsxr1000": "gsxr1000",
        "k5": "gsxr1000",
        "k6": "gsxr1000",
        "r1": "yzfr1",
        "yzfr1": "yzfr1",
        "4c8": "yzfr1",
        "crossplane": "yzfr1",
        "ninja": "kawasaki",
        "duke": "ktm",
        "rc": "ktm",
        "dominar": "bajaj",
        "pulsar": "bajaj",
        "apache": "tvs",
        "continental": "enfield",
        "interceptor": "enfield",
        "himalayan": "enfield",
    }

    # Venue aliases
    VENUE_ALIASES = {
        "aamby": "aamby valley",
        "tvr": "aamby valley",
        "mmrt": "mmrt",
        "bic": "bic",
        "kari": "kari",
        "hyderabad": "hyderabad",
        "santa pod": "santa pod",
        "pomona": "pomona",
        "gainesville": "gainesville",
        "sydney": "sydney",
        "dubai": "dubai",
        "al-ain": "al-ain",
        "jerez": "jerez",
    }

    # Part keywords by category. Matched as whole words / phrases (an optional
    # plural "s"), never as substrings: "sc" must not fire inside "scrub",
    # "wet" inside "wet track", "map" inside "mapped".
    PART_KEYWORDS = {
        "turbo": ["turbo", "turbocharged", "turbocharger"],
        "supercharger": ["supercharger", "sc", "roots", "centrifugal"],
        "nitrous": ["nitrous", "n2o", "nos"],
        "exhaust": ["exhaust", "pipes", "headers"],
        "air_filter": ["air filter", "intake", "pod"],
        "ecu": ["ecu", "flash", "tune", "map"],
        "clutch": ["clutch", "slipper", "wet clutch"],
        "chain": ["chain", "sprocket"],
        "weight_reduction": [
            "weight reduction",
            "carbon",
            "lightweight",
            "ti-6al",
            "aluminum",
        ],
        "fuel_system": ["fuel pump", "injector", "rail"],
        "suspension": ["suspension", "coilover", "spring"],
        "brakes": ["brake", "pad", "disc", "rotor"],
        "wheelie_bar": ["wheelie bar"],
        "quickshifter": ["quickshifter", "quick shift"],
        "battery": ["battery", "lithium"],
        "tire": ["slick", "drag tire", "r-compound"],
    }

    # Parser category -> catalog parts categories searched for it. Categories
    # that map to nothing (tyres are not parts) are reported, not guessed.
    PART_DB_CATEGORIES = {
        "turbo": ["boost_kit"],
        "supercharger": ["boost_kit"],
        "nitrous": ["nitrous"],
        "exhaust": ["exhaust"],
        "air_filter": ["air_filter"],
        "ecu": ["ecu"],
        "clutch": ["clutch_kit"],
        "chain": ["chain", "sprocket"],
        "weight_reduction": ["bodywork"],
        "fuel_system": ["fuel_system"],
        "suspension": ["suspension"],
        "brakes": ["brakes"],
        "wheelie_bar": ["wheelie_bar"],
        "quickshifter": ["quickshifter"],
        "battery": ["battery"],
        "tire": [],
    }

    # Within boost_kit the parser category also names the kind of kit.
    _BOOST_NAME_HINTS = {
        "turbo": re.compile(r"turbo", re.IGNORECASE),
        "supercharger": re.compile(
            r"supercharg|blower|roots|centrifugal|procharger", re.IGNORECASE
        ),
    }

    @staticmethod
    def _kw_pattern(keywords: list[str]) -> re.Pattern:
        alts = "|".join(re.escape(k) for k in keywords)
        return re.compile(rf"(?<![a-z0-9])(?:{alts})s?(?![a-z0-9])")

    def __init__(self):
        """Initialize the parser."""
        self._part_patterns = {
            cat: self._kw_pattern(kws) for cat, kws in self.PART_KEYWORDS.items()
        }

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into a ParsedQuery.

        Examples:
            "optimize my Hayabusa for 35°C at Aamby Valley"
            "setup K5 for 28C, 50% humidity, budget 100000 INR"
            "what ET with turbo at Pomona in summer?"
        """
        query_lower = query.lower()

        # Extract bike reference
        bike_query = self._extract_bike(query_lower)

        # Extract venue reference
        venue_query = self._extract_venue(query_lower)

        # Extract environmental conditions
        temp = self._extract_temperature(query_lower)
        humidity = self._extract_humidity(query_lower)
        altitude = self._extract_altitude(query_lower)
        headwind, wind_dir = self._extract_wind(query_lower)

        # Extract budget
        budget = self._extract_budget(query_lower)

        # Extract parts mentioned
        parts = self._extract_parts(query_lower)

        # Infer optimization goal
        goal = self._infer_optimization_goal(query_lower, parts)

        # Extract track prep type
        track_prep = self._extract_track_prep(query_lower)

        return ParsedQuery(
            raw_query=query,
            bike_query=bike_query,
            venue_query=venue_query,
            temperature_c=temp,
            humidity_pct=humidity,
            altitude_m=altitude,
            budget_inr=budget,
            parts_mentioned=parts,
            optimization_goal=goal,
            headwind_ms=headwind,
            track_prep_type=track_prep,
            wind_direction_deg=wind_dir,
        )

    def _extract_bike(self, query_lower: str) -> str:
        """Extract bike reference from query."""
        # Look for explicit mentions: "my X", "a X", "the X"
        # This captures bike names that come after possessive/article modifiers
        # Stop at common delimiter keywords
        patterns = [
            r"my\s+(\w+(?:\s+\w+)?)\s+(?:for|at|with|in|to|and)",  # "my Hayabusa for/at/with/and..."
            r"my\s+([a-z0-9\-]+)(?:\s|$)",  # "my K5 " or "my K5$"
            r"(?:a|the)\s+(\w+(?:\s+\w+)?)\s+(?:bike|motorcycle)",  # "a Hayabusa bike"
            r"with\s+my\s+(\w+(?:\s+\w+)?)",  # "with my Hayabusa"
            r"(\w+)\s+(?:bike|motorcycle|motorbike)",  # "Hayabusa bike"
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                candidate = match.group(1).strip()
                # Return single or double-word candidates (bike names are usually 1-2 words)
                if candidate and len(candidate.split()) <= 2:
                    return candidate
        return ""

    def _extract_venue(self, query_lower: str) -> str | None:
        """Extract venue reference from query."""
        for alias, standard in self.VENUE_ALIASES.items():
            if alias in query_lower:
                return standard
        return None

    def _extract_temperature(self, query_lower: str) -> float | None:
        """Extract temperature (°C or C) from query."""
        # Patterns: "35°C", "35C", "35 C", "temp 35C", "temperature 35°C", "35 degrees celsius"
        patterns = [
            r"(\d+)\s*°?c\b",  # 35°C or 35C
            r"(\d+)\s+degrees?\s+celsius",  # 35 degrees celsius
            r"temp[erature]*\s+(?:of\s+)?(\d+)\s*°?c",  # temp 35C
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return float(match.group(1))
        return None

    def _extract_humidity(self, query_lower: str) -> float | None:
        """Extract relative humidity (%) from query."""
        patterns = [
            r"(\d+)\s*%\s*(?:humidity|rh)",  # 50% humidity or 50% RH
            r"humidity\s+(?:of\s+)?(\d+)\s*%",  # humidity of 50%
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return float(match.group(1))
        return None

    _LEN_UNIT = r"(m|meters?|metres?|ft|feet)"

    def _extract_altitude(self, query_lower: str) -> float | None:
        """Extract altitude (metres) from query.

        Requires altitude context ("altitude", "elevation", "asl", "above sea
        level") so a bare "5 m/s" or "10 m" is never read as an altitude.
        """
        num = r"(\d+(?:\.\d+)?)"
        unit = self._LEN_UNIT
        patterns = [
            rf"(?:altitude|elevation|elev)\s*(?:of|is|at|=|:)?\s*{num}\s*{unit}(?![/\w])",
            rf"{num}\s*{unit}(?![/\w])\s*(?:altitude|elevation|elev|asl|above\s+sea\s+level)\b",
            rf"(?:at|@)\s*{num}\s*{unit}(?![/\w])\s*(?:asl|above\s+sea\s+level)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = float(match.group(1))
                if match.group(2).startswith(("ft", "feet")):
                    value *= 0.3048
                return value
        return None

    _WIND_UNITS = {
        "m/s": 1.0,
        "mps": 1.0,
        "km/h": 1.0 / 3.6,
        "kmh": 1.0 / 3.6,
        "kph": 1.0 / 3.6,
        "mph": 0.44704,
    }

    def _extract_wind(self, query_lower: str) -> tuple[float | None, float | None]:
        """Extract wind as (speed in m/s, direction deg: 0 head / 180 tail).

        Understands m/s, km/h (kmh, kph) and mph, in "5 m/s headwind",
        "headwind of 20 km/h", "12 mph tailwind" and "wind of 4 m/s" forms.
        Unqualified "wind" means headwind.
        """
        num = r"(\d+(?:\.\d+)?)"
        unit = r"(m/s|mps|km/h|kmh|kph|mph)"
        kind = r"(head|tail)?\s*wind"
        patterns = [
            rf"{num}\s*{unit}\s+{kind}\b",
            rf"(head|tail)?wind\s+(?:of\s+|at\s+|speed\s+)?{num}\s*{unit}",
        ]
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, query_lower)
            if not match:
                continue
            if i == 0:
                value, u, which = match.group(1), match.group(2), match.group(3)
            else:
                which, value, u = match.group(1), match.group(2), match.group(3)
            speed = float(value) * self._WIND_UNITS[u]
            return round(speed, 4), (180.0 if which == "tail" else 0.0)
        return None, None

    def _extract_headwind(self, query_lower: str) -> float | None:
        """Wind speed in m/s (see ``_extract_wind``)."""
        return self._extract_wind(query_lower)[0]

    def _extract_budget(self, query_lower: str) -> int | None:
        """Extract budget in INR from query."""
        patterns = [
            r"(?:budget|spend)\s+(?:of\s+)?₹?(\d+)(?:\s*(?:inr|rupees?))?",
            r"₹(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return int(match.group(1))
        return None

    def _extract_parts(self, query_lower: str) -> list[str]:
        """Extract parts mentioned in query."""
        mentioned = []
        for category, pattern in self._part_patterns.items():
            if pattern.search(query_lower):
                mentioned.append(category)
        return mentioned

    def _extract_track_prep(self, query_lower: str) -> str | None:
        """Extract track prep type from query."""
        prep_map = {
            "vht": ["vht", "victor"],
            "pj1": ["pj1", "paint"],
            "rubber": ["rubber", "buildup"],
        }
        for prep_type, keywords in prep_map.items():
            if self._kw_pattern(keywords).search(query_lower):
                return prep_type
        return None

    def _infer_optimization_goal(self, query_lower: str, parts: list[str]) -> str:
        """Infer the optimization goal from query content."""
        # A wind speed in mph ("12 mph tailwind") is not a request for trap speed.
        query_lower = re.sub(r"\d+(?:\.\d+)?\s*mph\b", " ", query_lower)

        def has(*words: str) -> bool:
            return self._kw_pattern(list(words)).search(query_lower) is not None

        if has("budget", "afford", "cheap"):
            return "best_budget"
        if has("speed", "trap", "mph"):
            return "maximize_trap"
        if has("time", "et", "quick"):
            return "minimize_et"
        # If no explicit goal but budget is mentioned, assume best_budget
        if parts and "best_budget" in query_lower:
            return "best_budget"
        return "minimize_et"  # Default: minimize ET


# ═══════════════════════════════════════════
# NLSimRunner — Execute Parsed Query
# ═══════════════════════════════════════════


class NLSimRunner:
    """
    Takes a ParsedQuery and resolves it against the database,
    builds a BikeConfig, runs the simulation, and returns results.
    """

    def __init__(self, db: MotoQuantDB):
        """
        Initialize with a database connection.

        Args:
            db: MotoQuantDB instance (opened connection)
        """
        self.db = db
        self.parser = NLQueryParser()
        self.last_bike_alternatives: list[str] = []

    def run_query(self, query: str) -> dict:
        """
        Parse and execute a natural language query.

        Args:
            query: Natural language string (e.g., "optimize my Hayabusa for 35C at Aamby Valley")

        Returns:
            Dictionary with keys:
                - parsed_query: ParsedQuery object (as dict)
                - bike_name: Resolved bike name
                - config: BikeConfig used
                - result: SimResult
                - et_s: Quarter-mile ET in seconds
                - trap_speed_kmh: Trap speed in km/h
                - suggestions: List of optimization suggestions
                - error: Error message if failed (optional)
        """
        # Parse the query
        parsed = self.parser.parse(query)

        # Resolve bike
        bike_model = self._resolve_bike(parsed.bike_query)
        if not bike_model:
            return {
                "error": f"Could not find bike matching '{parsed.bike_query}'. Try 'bikes' command to see available models."
            }

        # Get current config
        config_row = self.db.bikes.get_current_config(bike_model["id"])
        if not config_row:
            return {
                "error": f"No configuration found for {bike_model['manufacturer_name']} {bike_model['model_name']}"
            }

        config = self.db.bikes.to_config(config_row["id"])
        bike_name = f"{bike_model['manufacturer_name']} {bike_model['model_name']}"
        if bike_model.get("model_code"):
            bike_name += f" {bike_model['model_code']}"

        # Resolve venue and apply environment
        if parsed.venue_query:
            venue = self.db.venues.get_by_name(parsed.venue_query)
            if not venue:
                from .llm.resolver import resolve_venue

                venue_id = resolve_venue(parsed.venue_query, self.db)
                venue = self.db.venues.get(venue_id) if venue_id else None
            if venue:
                config.environment.venue_name = venue["name"]
                config.environment.altitude_m = venue["altitude_m"]

        # Apply parsed environmental conditions
        if parsed.temperature_c is not None:
            config.environment.ambient_temp_c = parsed.temperature_c
        if parsed.humidity_pct is not None:
            config.environment.relative_humidity_pct = parsed.humidity_pct
        if parsed.altitude_m is not None:
            config.environment.altitude_m = parsed.altitude_m
        if parsed.headwind_ms is not None:
            config.environment.wind_speed_ms = parsed.headwind_ms
            config.environment.wind_direction_deg = (
                parsed.wind_direction_deg
                if parsed.wind_direction_deg is not None
                else 0.0
            )  # 0 = headwind, 180 = tailwind
        if parsed.track_prep_type:
            # The tyre-level prep field is the one the physics reads.
            config.tires.track_prep_type = _TRACK_PREP_CONSTANTS[parsed.track_prep_type]

        # Apply parts if mentioned: for each category, the compatible part with
        # the best ROI on this bike (and venue conditions) is applied to the
        # config; categories with no fitting part are reported, never faked.
        applied_parts: list[str] = []
        applied_details: list[dict] = []
        parts_not_applied: list[dict] = []
        base_et_s = None
        if parsed.parts_mentioned:
            from .analysis.roi import SimMemo

            memo = SimMemo()
            base_et_s = memo(config)[0]
            remaining = float(parsed.budget_inr) if parsed.budget_inr else None
            for category in parsed.parts_mentioned:
                part, reason = self._pick_part(
                    category, config, bike_model["id"], memo, remaining
                )
                if part is None:
                    parts_not_applied.append({"category": category, "reason": reason})
                    continue
                config = self._apply_part_overrides(config, part)
                if remaining is not None:
                    remaining -= part["price_inr"] or 0.0
                part_display = (
                    f"{part.get('brand') or ''} {part.get('model_name') or part.get('name') or 'Unknown Part'}"
                ).strip()
                applied_parts.append(part_display)
                applied_details.append(
                    {
                        "category": category,
                        "part_id": part["id"],
                        "name": part_display,
                        "price_inr": part.get("price_inr"),
                    }
                )

        # Run simulation
        engine = MotoQuantEngine(config)
        result = engine.run()

        # Generate suggestions
        suggestions = self._generate_suggestions(
            parsed, config, result, applied_details
        )
        for miss in parts_not_applied:
            suggestions.append(f"{miss['category']}: {miss['reason']}")

        return {
            "parsed_query": {
                "raw_query": parsed.raw_query,
                "bike_query": parsed.bike_query,
                "venue_query": parsed.venue_query,
                "temperature_c": parsed.temperature_c,
                "humidity_pct": parsed.humidity_pct,
                "parts_mentioned": parsed.parts_mentioned,
                "optimization_goal": parsed.optimization_goal,
            },
            "bike_name": bike_name,
            "bike_alternatives": list(self.last_bike_alternatives),
            "config_name": config.name,
            "environment": {
                "venue": config.environment.venue_name,
                "wind_speed_ms": config.environment.wind_speed_ms,
                "wind_direction_deg": config.environment.wind_direction_deg,
                "track_prep": config.tires.track_prep_type,
                "altitude_m": config.environment.altitude_m,
                "ambient_temp_c": config.environment.ambient_temp_c,
                "humidity_pct": config.environment.relative_humidity_pct,
                "density_altitude_ft": config.environment.density_altitude_ft(),
            },
            "applied_parts": applied_parts,
            "applied_part_details": applied_details,
            "parts_not_applied": parts_not_applied,
            "base_et_s": round(base_et_s, 4) if base_et_s is not None else None,
            "delta_et_s": (  # with parts - without: negative = quicker
                round(result.time_quarter - base_et_s, 4) + 0.0
                if base_et_s is not None
                else None
            ),
            "et_s": round(result.time_quarter, 4),
            "trap_speed_kmh": round(result.speed_quarter * 3.6, 1),  # m/s to km/h
            "trap_speed_mph": round(result.speed_quarter * 2.237, 1),  # m/s to mph
            "sixty_foot_s": round(result.time_60ft, 4),
            "peak_accel_g": round(float(__import__("numpy").max(result.a)), 2),
            "suggestions": suggestions,
        }

    # Bike families users name most often (the simulator's quick-pick chips):
    # when a short name matches several catalog rows, these win.
    _POPULAR_BIKE_TOKENS = (
        {"hayabusa", "gen1"},
        {"duke", "390"},
        {"r15", "v4"},
        {"classic", "350"},
        {"zx", "10r"},
        {"gsx", "r", "1000"},
    )

    @staticmethod
    def _norm_tokens(name: str) -> list[str]:
        name = re.sub(r"\(\s*\d{4}(?:\s*[-–]\s*\d{4})?\s*\)", " ", name.lower())
        return [t for t in re.split(r"[^a-z0-9]+", name) if t]

    def _resolve_bike(self, bike_query: str) -> dict | None:
        """
        Resolve a bike query string to a bike model in the database.
        Returns the bike model row or None if not found.

        A short name that matches several rows ("duke") resolves to the
        closest name, preferring the commonly-benchmarked family, then the
        newest generation; the other matches are listed on
        ``self.last_bike_alternatives``.
        """
        self.last_bike_alternatives = []
        if not bike_query:
            return None

        # Try name_contains match (searches model_name and model_code)
        rows = self.db.bikes.search(name_contains=bike_query, limit=500)
        if rows:
            q_tokens = set(self._norm_tokens(bike_query))
            whole = [
                r
                for r in rows
                if q_tokens and q_tokens <= set(self._norm_tokens(r["model_name"]))
            ]
            pool = whole or rows

            def rank(item):
                idx, r = item
                toks = set(self._norm_tokens(r["model_name"]))
                extra = len(toks - q_tokens)
                popular = 0 if any(h <= toks for h in self._POPULAR_BIKE_TOKENS) else 1
                return (popular, extra, -(r.get("year_from") or 0), idx)

            ordered = [r for _, r in sorted(enumerate(pool), key=rank)]
            self.last_bike_alternatives = [
                f"{r['manufacturer_name']} {r['model_name']}" for r in ordered[1:6]
            ]
            return ordered[0]

        # Try code match (for things like "K5", "K6", "K7", etc.)
        # Map common codes to their manufacturer
        code_manufacturer_map = {
            "k5": "suzuki",
            "k6": "suzuki",
            "k7": "suzuki",
            "k9": "suzuki",
            "l7": "suzuki",
            "gen1": "suzuki",
            "gen2": "suzuki",
            "gen3": "suzuki",
        }
        if bike_query.lower() in code_manufacturer_map:
            mfg = code_manufacturer_map[bike_query.lower()]
            rows = self.db.bikes.search(manufacturer=mfg)
            if rows:
                return rows[0]

        # Try manufacturer only
        rows = self.db.bikes.search(manufacturer=bike_query)
        if rows:
            return rows[0]

        # Try category match (e.g., "sport")
        rows = self.db.bikes.search(category=bike_query)
        if rows:
            return rows[0]

        return None

    def _pick_part(
        self,
        category: str,
        config: BikeConfig,
        bike_id: int,
        memo,
        budget_left: float | None,
    ) -> tuple[dict | None, str]:
        """Best-ROI compatible part for a parser category, or (None, reason)."""
        from .analysis.roi import _ALL_PARTS_LIMIT, compute_parts_roi

        db_cats = self.parser.PART_DB_CATEGORIES.get(category, [])
        if not db_cats:
            return (
                None,
                "this kind of change is not a catalog part, so it was not applied",
            )
        pool: list[dict] = []
        for db_cat in db_cats:
            pool.extend(
                self.db.parts.search(
                    category=db_cat, bike_model_id=bike_id, limit=_ALL_PARTS_LIMIT
                )
            )
        hint = self.parser._BOOST_NAME_HINTS.get(category)
        if hint is not None:
            pool = [
                p
                for p in pool
                if hint.search(f"{p.get('brand')} {p.get('model_name')}")
            ]
        if not pool:
            return None, "no compatible part in the catalog fits this bike"
        by_id = {p["id"]: p for p in pool}
        rois = compute_parts_roi(
            config,
            list(by_id),
            self.db.parts,
            bike_model_id=bike_id,
            et_fn=memo,
        )
        useful = [
            r
            for r in rois
            if r.delta_et_s > 0
            and not r.no_straight_line_effect
            and (budget_left is None or r.price_inr <= budget_left)
        ]
        if not useful:
            return (
                None,
                "no compatible part gives a measurable improvement within budget",
            )
        return by_id[useful[0].part_id], ""

    def _apply_part_overrides(self, config: BikeConfig, part: dict) -> BikeConfig:
        """Return ``config`` with a part's parameter overrides applied.

        ``apply_part_to_config`` returns a new config; the caller must keep it.
        """
        from .database.bridge import apply_part_to_config

        try:
            return apply_part_to_config(config, part)
        except Exception as e:
            print(f"Warning: could not apply part {part.get('model_name')}: {e}")
            return config

    def _generate_suggestions(
        self,
        parsed: ParsedQuery,
        config: BikeConfig,
        result: SimResult,
        applied_parts: list[dict],
    ) -> list[str]:
        """Generate optimization suggestions based on the result."""
        suggestions = []

        # ET-based suggestions
        if result.time_quarter > 10.5:
            if (
                "turbo" not in parsed.parts_mentioned
                and "supercharger" not in parsed.parts_mentioned
            ):
                suggestions.append(
                    "Consider turbocharger or supercharger for ET improvement (0.3-0.5s typical)"
                )
        if result.time_quarter > 10.0:
            if "weight_reduction" not in parsed.parts_mentioned:
                suggestions.append(
                    "Weight reduction parts could improve acceleration by 0.1-0.2s"
                )

        # Traction suggestions
        if parsed.temperature_c and parsed.temperature_c > 30:
            suggestions.append(
                "High ambient temperature reduces tire grip. Consider slick tires or track prep."
            )

        # Budget suggestions
        if parsed.budget_inr and applied_parts:
            applied_cost = sum(float(p.get("price_inr") or 0.0) for p in applied_parts)
            remaining = parsed.budget_inr - applied_cost
            if remaining > 0:
                suggestions.append(
                    f"₹{remaining:,.0f} remaining in budget. Explore additional parts."
                )
            elif remaining < 0:
                suggestions.append(
                    f"Budget exceeded by ₹{abs(remaining):,.0f}. Consider lower-cost alternatives."
                )

        return suggestions


# ═══════════════════════════════════════════
# Helper: Format output for CLI display
# ═══════════════════════════════════════════


def format_nl_result(result: dict) -> str:
    """
    Format a NL simulation result for pretty CLI output.
    """
    if "error" in result:
        return f"  Error: {result['error']}"

    lines = []
    lines.append("\n  ╔══ NL QUERY RESULT ══╗")
    lines.append(f"\n  Bike: {result['bike_name']}")
    lines.append(f"  Venue: {result['environment']['venue']}")
    lines.append(
        f"  Conditions: {result['environment']['ambient_temp_c']}°C, "
        f"{result['environment']['humidity_pct']}% RH, "
        f"DA={result['environment']['density_altitude_ft']:.0f} ft"
    )

    if result["applied_parts"]:
        lines.append(f"  Parts: {', '.join(result['applied_parts'])}")

    lines.append("\n  Results:")
    lines.append(f"    ET:           {result['et_s']:.3f}s")
    lines.append(
        f"    Trap Speed:   {result['trap_speed_kmh']:.1f} km/h ({result['trap_speed_mph']:.1f} mph)"
    )
    lines.append(f"    60-ft:        {result['sixty_foot_s']:.3f}s")
    lines.append(f"    Peak Accel:   {result['peak_accel_g']:.2f}g")

    if result["suggestions"]:
        lines.append("\n  Suggestions:")
        for sugg in result["suggestions"]:
            lines.append(f"    • {sugg}")

    lines.append("")
    return "\n".join(lines)
