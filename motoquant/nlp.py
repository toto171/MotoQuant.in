"""
MotoQuant — Natural Language Tuning Interface
=============================================
Pure Python NLP parser for translating natural language queries like
"optimize my Hayabusa for 35°C at Aamby Valley with a 50000 INR budget"
into structured parameter overrides.

Phase 4C feature: v1 uses regex/keyword extraction (no Ollama required).
Future: --use-ollama flag will enable LLM-powered parsing (Phase 5).
"""

import re
from dataclasses import dataclass, field

from .database.connection import MotoQuantDB
from .engine_select import make_engine
from .models import TRACK_PJ1, TRACK_RUBBER, TRACK_VHT, BikeConfig
from .physics import SimResult

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
    headwind_ms: float | None = None
    track_prep_type: str | None = None


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

    # Part keywords by mention key. Matched on WORD boundaries (an optional
    # plural "s"/"es" allowed): substring matching made "brake discs" mention
    # a supercharger ("sc") and "wet track" a clutch ("wet"), and "tune my
    # bike" an ECU ("tune" is the verb, not a part).
    PART_KEYWORDS = {
        "turbo": ["turbo", "turbocharged", "turbocharger"],
        "supercharger": ["supercharger", "supercharged", "sc", "roots", "centrifugal"],
        "nitrous": ["nitrous", "n2o", "nos"],
        "exhaust": ["exhaust", "pipe", "header", "slip-on", "full system"],
        "air_filter": ["air filter", "intake", "pod filter"],
        "ecu": ["ecu", "flash", "remap", "piggyback", "power commander", "fuel map"],
        "clutch": ["clutch", "slipper"],
        "chain": ["chain"],
        "sprocket": ["sprocket", "gearing"],
        "weight_reduction": [
            "weight reduction",
            "carbon",
            "lightweight",
            "ti-6al",
            "aluminum",
            "fairing",
        ],
        "fuel_system": ["fuel pump", "injector", "fuel rail"],
        "suspension": ["suspension", "coilover", "shock", "fork", "spring"],
        "brakes": ["brake", "pad", "disc", "rotor", "caliper"],
        "wheelie_bar": ["wheelie bar"],
        "quickshifter": ["quickshifter", "quick shift", "quick shifter"],
        "battery": ["battery", "lithium"],
        "tire": ["slick", "drag tire", "drag tyre", "r-compound"],
    }

    # Mention key -> real parts_categories.name in the catalog. "tire" is not
    # a parts category: drag rubber comes from the tyre fitment table.
    CATEGORY_FOR_MENTION = {
        "turbo": "boost_kit",
        "supercharger": "boost_kit",
        "nitrous": "nitrous",
        "exhaust": "exhaust",
        "air_filter": "air_filter",
        "ecu": "ecu",
        "clutch": "clutch_kit",
        "chain": "chain",
        "sprocket": "sprocket",
        "weight_reduction": "bodywork",
        "fuel_system": "fuel_system",
        "suspension": "suspension",
        "brakes": "brakes",
        "wheelie_bar": "wheelie_bar",
        "quickshifter": "quickshifter",
        "battery": "battery",
    }

    # Model-code / nickname aliases that a substring search resolves wrongly
    # ("k5" matched BMW's model code K52, "r1" matched "R 12 nineT"): each maps
    # to (model_name substring, preferred model_code).
    CANONICAL_BIKES = {
        "k5": ("GSX-R 1000", "K5"),
        "k6": ("GSX-R 1000", "K5"),
        "gsxr": ("GSX-R 1000", "K5"),
        "gsxr1000": ("GSX-R 1000", "K5"),
        "r1": ("YZF-R1", "4C8"),
        "yzfr1": ("YZF-R1", "4C8"),
        "4c8": ("YZF-R1", "4C8"),
        "crossplane": ("YZF-R1", "4C8"),
        "busa": ("Hayabusa", None),
        "gsx1300": ("Hayabusa", None),
        "gsx1300r": ("Hayabusa", None),
        "hayabusa": ("Hayabusa", None),
    }

    def __init__(self):
        """Initialize the parser."""

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
        headwind = self._extract_headwind(query_lower)

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

    def _extract_altitude(self, query_lower: str) -> float | None:
        """Extract altitude (meters) from query.

        A speed in m/s is NOT an altitude ("3 m/s headwind" used to set
        altitude_m=3)."""
        patterns = [
            r"altitude\s+(?:of\s+)?(\d+)\s*m(?:eters?|etres?)?\b(?!\s*/\s*s)",
            r"(\d+)\s*m(?:eters?|etres?)?\b(?!\s*/\s*s)(?:\s+altitude)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return float(match.group(1))
        return None

    def _extract_headwind(self, query_lower: str) -> float | None:
        """Extract the wind along the strip (m/s): positive = headwind,
        negative = tailwind."""
        num = r"(\d+(?:\.\d+)?)\s*m\s*/\s*s"
        patterns = [
            (num + r"\s+(?:head\s*wind|wind)", 1.0),
            (r"head\s*wind\s+(?:of\s+)?" + num, 1.0),
            (num + r"\s+tail\s*wind", -1.0),
            (r"tail\s*wind\s+(?:of\s+)?" + num, -1.0),
        ]
        for pattern, sign in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return sign * float(match.group(1))
        return None

    # Indian money words: "50k", "1.5 lakh", "2 crore".
    _MONEY_UNITS = {
        "k": 1_000,
        "lakh": 100_000,
        "lakhs": 100_000,
        "lac": 100_000,
        "lacs": 100_000,
        "crore": 10_000_000,
        "crores": 10_000_000,
        "cr": 10_000_000,
    }
    _AMOUNT = r"(\d[\d,]*(?:\.\d+)?)\s*(k|lakhs?|lacs?|crores?|cr)?\b"

    def _extract_budget(self, query_lower: str) -> int | None:
        """Extract budget in INR from query.

        Accepts thousands separators ("50,000"), k / lakh / crore units
        ("50k", "1.5 lakh") and ₹ / rs / inr markers. The old pattern stopped
        at the first comma ("budget of 50,000 inr" -> ₹50) and read
        "1.5 lakh" as ₹1."""
        amount = self._AMOUNT
        patterns = [
            r"(?:budget|spend(?:ing)?)\s+(?:of\s+|is\s+|:\s*)?(?:₹|\brs\.?|\binr)?\s*"
            + amount,
            r"(?:₹|\brs\.?\s|\binr\s)\s*" + amount,
            r"(\d[\d,]*(?:\.\d+)?)\s*(k|lakhs?|lacs?|crores?|cr)?\s*(?:inr|rupees?)\b",
            r"(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if not match:
                continue
            try:
                value = float(match.group(1).replace(",", ""))
            except ValueError:
                continue
            unit = (match.group(2) or "").strip()
            value *= self._MONEY_UNITS.get(unit, 1)
            return int(round(value))
        return None

    @staticmethod
    def _keyword_in(keyword: str, text: str) -> bool:
        """Whole-word match (optional plural) — never a substring."""
        pat = rf"(?<![a-z0-9]){re.escape(keyword)}(?:e?s)?(?![a-z0-9])"
        return re.search(pat, text) is not None

    def _extract_parts(self, query_lower: str) -> list[str]:
        """Extract parts mentioned in query."""
        mentioned = []
        for category, keywords in self.PART_KEYWORDS.items():
            for keyword in keywords:
                if self._keyword_in(keyword, query_lower):
                    mentioned.append(category)
                    break  # Only add category once
        return mentioned

    def _extract_track_prep(self, query_lower: str) -> str | None:
        """Extract track prep type (a models.TRACK_* constant) from query."""
        prep_map = {
            TRACK_VHT: ["vht", "victor"],
            TRACK_PJ1: ["pj1", "paint"],
            TRACK_RUBBER: ["rubber", "buildup", "rubbered"],
        }
        for prep_type, keywords in prep_map.items():
            for keyword in keywords:
                if self._keyword_in(keyword, query_lower):
                    return prep_type
        return None

    def _infer_optimization_goal(self, query_lower: str, parts: list[str]) -> str:
        """Infer the optimization goal from query content."""
        if "budget" in query_lower or "afford" in query_lower or "cheap" in query_lower:
            return "best_budget"
        if "speed" in query_lower or "trap" in query_lower or "mph" in query_lower:
            return "maximize_trap"
        if "time" in query_lower or "et" in query_lower or "quick" in query_lower:
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

        bike_name = f"{bike_model['manufacturer_name']} {bike_model['model_name']}"
        if bike_model.get("model_code"):
            bike_name += f" {bike_model['model_code']}"
        # Build the config exactly like /api/simulate does (the config row's
        # JSON physics blob). BikeRepository.to_config prefers a stale
        # dyno_curves row over that blob, so NL answers diverged from the API
        # by up to 2.28 s for the same bike (October 2026 audit).
        from .database.bridge import db_row_to_config

        config = db_row_to_config(dict(config_row), name=bike_name)

        # Resolve venue and apply environment (the same fields /api/simulate
        # applies for a venue_id: altitude + track surface). The alias table
        # yields "aamby valley" but the catalog row is "Aamby Valley Airstrip
        # (TVR)" — the old exact-name lookup never matched, so every NL venue
        # was silently ignored.
        if parsed.venue_query:
            venue = self._resolve_venue(parsed.venue_query)
            if venue:
                config.environment.venue_name = venue["name"]
                if venue.get("altitude_m") is not None:
                    config.environment.altitude_m = float(venue["altitude_m"])
                config.environment.track_surface = (
                    venue.get("surface_type") or "asphalt"
                ).lower()

        # Apply parsed environmental conditions
        if parsed.temperature_c is not None:
            config.environment.ambient_temp_c = parsed.temperature_c
        if parsed.humidity_pct is not None:
            config.environment.relative_humidity_pct = parsed.humidity_pct
        if parsed.altitude_m is not None:
            config.environment.altitude_m = parsed.altitude_m
        if parsed.headwind_ms is not None:
            # Wind direction is measured against the strip heading
            # (EnvironmentParams.headwind_component): heading = pure headwind,
            # heading + 180 = pure tailwind.
            heading = float(getattr(config.environment, "track_heading_deg", 0.0))
            config.environment.wind_speed_ms = abs(parsed.headwind_ms)
            config.environment.wind_direction_deg = (
                heading if parsed.headwind_ms >= 0 else (heading + 180.0) % 360.0
            )
        if parsed.track_prep_type:
            # Physics reads the prep compound from the tyre model
            # (TireParams.track_prep_multiplier); environment.track_prep is
            # never read.
            config.tires.track_prep_type = parsed.track_prep_type

        # Apply parts if mentioned: the best COMPATIBLE part in each category
        # (by simulated ET gain on this bike, within the remaining budget).
        # The old runner took the first alphabetical row of the whole
        # category (a Harley nitrous kit and a Rocket 3 exhaust on a
        # Hayabusa) and then DISCARDED apply_part_to_config's return value,
        # so the "modified" ET was the stock ET.
        applied_parts: list[str] = []
        applied_part_ids: list[int] = []
        unavailable_parts: list[str] = []
        applied_cost = 0.0
        if parsed.parts_mentioned:
            config, applied_cost = self._apply_mentioned_parts(
                config,
                bike_model["id"],
                parsed,
                applied_parts,
                applied_part_ids,
                unavailable_parts,
            )

        # Run simulation (Rust core when active).
        result = make_engine(config).run()

        # Generate suggestions
        suggestions = self._generate_suggestions(
            parsed, config, result, applied_parts, applied_cost
        )

        return {
            "parsed_query": {
                "raw_query": parsed.raw_query,
                "bike_query": parsed.bike_query,
                "venue_query": parsed.venue_query,
                "temperature_c": parsed.temperature_c,
                "humidity_pct": parsed.humidity_pct,
                "budget_inr": parsed.budget_inr,
                "parts_mentioned": parsed.parts_mentioned,
                "optimization_goal": parsed.optimization_goal,
            },
            "bike_name": bike_name,
            "config_name": config.name,
            "environment": {
                "venue": config.environment.venue_name,
                "altitude_m": config.environment.altitude_m,
                "ambient_temp_c": config.environment.ambient_temp_c,
                "humidity_pct": config.environment.relative_humidity_pct,
                "density_altitude_ft": config.environment.density_altitude_ft(),
            },
            "applied_parts": applied_parts,
            "applied_part_ids": applied_part_ids,
            "unavailable_parts": unavailable_parts,
            "applied_cost_inr": round(applied_cost, 2),
            "et_s": round(result.time_quarter, 4),
            "trap_speed_kmh": round(result.speed_quarter * 3.6, 1),  # m/s to km/h
            "trap_speed_mph": round(result.speed_quarter * 2.237, 1),  # m/s to mph
            "sixty_foot_s": round(result.time_60ft, 4),
            "peak_accel_g": round(float(__import__("numpy").max(result.a)), 2),
            "suggestions": suggestions,
        }

    def _apply_mentioned_parts(
        self,
        config: BikeConfig,
        bike_model_id: int,
        parsed: ParsedQuery,
        applied_parts: list[str],
        applied_part_ids: list[int],
        unavailable_parts: list[str],
    ) -> tuple[BikeConfig, float]:
        """Apply the best compatible part per mentioned category.

        Naturally-aspirated categories go first and forced induction last —
        bridge.apply_part_to_config only scales the dyno curve while the
        engine is still NA. Returns (modified config, total part cost).
        """
        from .analysis.outlaw import _best_drag_tire
        from .analysis.roi import CANDIDATE_LIMIT, compute_parts_roi

        boost = {"boost_kit", "nitrous"}
        mentions = sorted(
            parsed.parts_mentioned,
            key=lambda m: self.parser.CATEGORY_FOR_MENTION.get(m) in boost,
        )
        budget_left = float(parsed.budget_inr) if parsed.budget_inr else None
        spent = 0.0
        used_categories: set[str] = set()
        for mention in mentions:
            if mention == "tire":
                best = _best_drag_tire(self.db.tires, bike_model_id)
                if best and float(best.get("mu_peak") or 0) > config.tires.mu_peak:
                    config.tires.mu_peak = float(best["mu_peak"])
                    applied_parts.append(
                        f"{best.get('tire_manufacturer', '')} "
                        f"{best.get('model_name', '')}".strip()
                    )
                    spent += float(best.get("price_inr") or 0.0)
                else:
                    unavailable_parts.append("drag tyre (none better than stock)")
                continue
            category = self.parser.CATEGORY_FOR_MENTION.get(mention)
            if category is None:
                continue
            # turbo + supercharger both map to boost_kit: one forced-induction
            # system per bike.
            if category in used_categories or (
                category in boost and used_categories & boost
            ):
                continue
            rows = self.db.parts.search(
                category=category,
                bike_model_id=bike_model_id,
                limit=CANDIDATE_LIMIT,
            )
            if mention in self._BOOST_FLAVOUR:
                # "turbo" must not silently fit a supercharger (both are
                # boost_kit rows) — filter on the kit's boost_type override.
                rows = [r for r in rows if self._boost_flavour(r) == mention]
            if budget_left is not None:
                rows = [
                    r for r in rows if float(r.get("price_inr") or 0.0) <= budget_left
                ]
            if not rows:
                unavailable_parts.append(mention)
                continue
            rois = compute_parts_roi(
                config, [r["id"] for r in rows], self.db.parts, min_delta_et_ms=0.0
            )
            if not rois:
                unavailable_parts.append(mention)
                continue
            best_roi = max(rois, key=lambda r: r.delta_et_s)
            part = next(r for r in rows if r["id"] == best_roi.part_id)
            config = self._apply_part_overrides(config, part)
            used_categories.add(category)
            applied_parts.append(
                f"{part.get('brand', '')} {part.get('model_name', '')}".strip()
            )
            applied_part_ids.append(part["id"])
            price = float(part.get("price_inr") or 0.0)
            spent += price
            if budget_left is not None:
                budget_left -= price
        return config, spent

    def _resolve_venue(self, venue_query: str) -> dict | None:
        """Venue row for a parsed venue name (exact, then fuzzy)."""
        venue = self.db.venues.get_by_name(venue_query)
        if venue:
            return venue
        try:
            from .llm.resolver import resolve_venue

            venue_id = resolve_venue(venue_query, self.db)
        except Exception:  # noqa: BLE001 — no venue is better than a crash
            venue_id = None
        return self.db.venues.get(venue_id) if venue_id is not None else None

    _BOOST_FLAVOUR = ("turbo", "supercharger")

    @staticmethod
    def _boost_flavour(part: dict) -> str | None:
        """'turbo' / 'supercharger' from a boost kit's boost_type override."""
        import json as _json

        raw = part.get("param_overrides") or {}
        if isinstance(raw, str):
            try:
                raw = _json.loads(raw)
            except (ValueError, TypeError):
                raw = {}
        bt = str((raw or {}).get("forced_induction.boost_type") or "")
        if bt.startswith("turbo"):
            return "turbo"
        if bt.startswith("sc"):
            return "supercharger"
        return None

    def _resolve_bike(self, bike_query: str) -> dict | None:
        """
        Resolve a bike query string to a bike model in the database.
        Returns the bike model row or None if not found.

        Order: canonical nicknames/model codes ("k5", "r1", "busa") ->
        whole-word catalog match on model name / exact model code -> the
        scored fuzzy resolver (llm.resolver) -> manufacturer alias ->
        category. A bare substring search is never trusted for short codes:
        "k5" used to resolve to BMW "R 1250 RT" (model code K52) and "r1" to
        "R 12 nineT".
        """
        if not bike_query:
            return None
        q = bike_query.lower().strip()
        key = re.sub(r"[\s\-_]+", "", q)

        canon = self.parser.CANONICAL_BIKES.get(key)
        if canon is not None:
            name_part, code = canon
            rows = self.db.bikes.search(name_contains=name_part, limit=200)
            if code:
                coded = [
                    r
                    for r in rows
                    if str(r.get("model_code") or "").lower() == code.lower()
                ]
                rows = coded or rows
            if rows:
                return sorted(rows, key=lambda r: r["id"])[0]

        # "<model> <model code>" ("hayabusa gen2", "gsx-r 1000 k7", "r1 rn32").
        tokens = q.split()
        if len(tokens) > 1:
            for i, tok in enumerate(tokens):
                rest = " ".join(t for j, t in enumerate(tokens) if j != i)
                rows = self.db.bikes.search(name_contains=rest, limit=200)
                coded = [
                    r for r in rows if str(r.get("model_code") or "").lower() == tok
                ]
                if coded:
                    return coded[0]

        word = rf"(?<![a-z0-9]){re.escape(q)}(?![a-z0-9])"
        rows = self.db.bikes.search(name_contains=q, limit=200)
        exact = [
            r
            for r in rows
            if re.search(word, str(r.get("model_name") or "").lower())
            or str(r.get("model_code") or "").lower() == q
        ]
        if exact:
            return exact[0]

        try:
            from .llm.resolver import resolve_bike

            bike_id, _suggestions = resolve_bike(bike_query, self.db)
        except Exception:  # noqa: BLE001 — fall through to the simple paths
            bike_id = None
        if bike_id is not None:
            model = self.db.bikes.get_model(bike_id)
            if model:
                return model

        mfg = self.parser.BIKE_ALIASES.get(key, q)
        rows = self.db.bikes.search(manufacturer=mfg)
        if rows:
            return rows[0]

        # Try category match (e.g., "sport")
        rows = self.db.bikes.search(category=q)
        if rows:
            return rows[0]

        return None

    def _apply_part_overrides(self, config: BikeConfig, part: dict) -> BikeConfig:
        """Apply a part to ``config`` and RETURN the modified config.

        apply_part_to_config never mutates its input; callers must use the
        returned config (the old version discarded it, so NL "with exhaust"
        queries simulated the stock bike)."""
        from .database.bridge import apply_part_to_config

        try:
            return apply_part_to_config(config, part)
        except Exception as e:
            print(
                f"Warning: could not apply part {part.get('model_name', part.get('id'))}: {e}"
            )
            return config

    def _generate_suggestions(
        self,
        parsed: ParsedQuery,
        config: BikeConfig,
        result: SimResult,
        applied_parts: list[str],
        applied_cost: float = 0.0,
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

        # Budget suggestions (priced from the parts actually applied)
        if parsed.budget_inr and applied_parts:
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
