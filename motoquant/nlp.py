"""
MotoQuant Pro — Natural Language Tuning Interface
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
from .models import BikeConfig
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

    # Part keywords by category
    PART_KEYWORDS = {
        "turbo": ["turbo", "turbocharged", "turbocharger"],
        "supercharger": ["supercharger", "sc", "roots", "centrifugal"],
        "nitrous": ["nitrous", "n2o", "nos"],
        "exhaust": ["exhaust", "pipes", "headers"],
        "air_filter": ["air filter", "intake", "pod"],
        "ecu": ["ecu", "flash", "tune", "map"],
        "clutch": ["clutch", "slipper", "wet"],
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
        """Extract altitude (meters) from query."""
        patterns = [
            r"(\d+)\s*m\b(?:\s+altitude)?",  # 1000m or 1000m altitude
            r"altitude\s+(?:of\s+)?(\d+)\s*m",  # altitude of 1000m
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return float(match.group(1))
        return None

    def _extract_headwind(self, query_lower: str) -> float | None:
        """Extract headwind speed (m/s) from query."""
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:m/s|m\/s)\s+(?:wind|headwind)",
            r"headwind\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:m/s|m\/s)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return float(match.group(1))
        return None

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
        for category, keywords in self.PART_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    mentioned.append(category)
                    break  # Only add category once
        return mentioned

    def _extract_track_prep(self, query_lower: str) -> str | None:
        """Extract track prep type from query."""
        prep_map = {
            "vht": ["vht", "victor"],
            "pj1": ["pj1", "paint"],
            "rubber": ["rubber", "buildup"],
        }
        for prep_type, keywords in prep_map.items():
            for keyword in keywords:
                if keyword in query_lower:
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

        config = self.db.bikes.to_config(config_row["id"])
        bike_name = f"{bike_model['manufacturer_name']} {bike_model['model_name']}"
        if bike_model.get("model_code"):
            bike_name += f" {bike_model['model_code']}"

        # Resolve venue and apply environment
        if parsed.venue_query:
            venue = self.db.venues.get_by_name(parsed.venue_query)
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
            config.environment.wind_direction_deg = 0  # Headwind
        if parsed.track_prep_type:
            config.environment.track_prep = parsed.track_prep_type

        # Apply parts if mentioned
        applied_parts = []
        if parsed.parts_mentioned:
            # Find parts by category
            for category in parsed.parts_mentioned:
                parts = self.db.parts.search(category=category)
                if parts:
                    # Take the first part in that category
                    best_part = parts[0]
                    part_display = (
                        best_part.get("model_name")
                        or best_part.get("name")
                        or "Unknown Part"
                    )
                    applied_parts.append(part_display)
                    # Apply the part's overrides to config
                    self._apply_part_overrides(config, best_part)

        # Run simulation
        engine = MotoQuantEngine(config)
        result = engine.run()

        # Generate suggestions
        suggestions = self._generate_suggestions(parsed, config, result, applied_parts)

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
            "config_name": config.name,
            "environment": {
                "venue": config.environment.venue_name,
                "altitude_m": config.environment.altitude_m,
                "ambient_temp_c": config.environment.ambient_temp_c,
                "humidity_pct": config.environment.relative_humidity_pct,
                "density_altitude_ft": config.environment.density_altitude_ft(),
            },
            "applied_parts": applied_parts,
            "et_s": round(result.time_quarter, 4),
            "trap_speed_kmh": round(result.speed_quarter * 3.6, 1),  # m/s to km/h
            "trap_speed_mph": round(result.speed_quarter * 2.237, 1),  # m/s to mph
            "sixty_foot_s": round(result.time_60ft, 4),
            "peak_accel_g": round(float(__import__("numpy").max(result.a)), 2),
            "suggestions": suggestions,
        }

    def _resolve_bike(self, bike_query: str) -> dict | None:
        """
        Resolve a bike query string to a bike model in the database.
        Returns the bike model row or None if not found.
        """
        if not bike_query:
            return None

        # Try name_contains match (searches model_name and model_code)
        rows = self.db.bikes.search(name_contains=bike_query)
        if rows:
            return rows[0]

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

    def _apply_part_overrides(self, config: BikeConfig, part: dict):
        """Apply a part's parameter overrides to a config."""
        from .database.bridge import apply_part_to_config

        try:
            apply_part_to_config(config, part)
        except Exception as e:
            print(f"Warning: could not apply part {part['name']}: {e}")

    def _generate_suggestions(
        self,
        parsed: ParsedQuery,
        config: BikeConfig,
        result: SimResult,
        applied_parts: list[str],
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
            try:
                applied_cost = 0
                for part_name in applied_parts:
                    # Search for the part by name_contains
                    parts_list = self.db.parts.search(name_contains=part_name)
                    if parts_list:
                        price = parts_list[0].get("price_inr", 0)
                        applied_cost += price

                remaining = parsed.budget_inr - applied_cost
                if remaining > 0:
                    suggestions.append(
                        f"₹{remaining:,} remaining in budget. Explore additional parts."
                    )
                elif remaining < 0:
                    suggestions.append(
                        f"Budget exceeded by ₹{abs(remaining):,}. Consider lower-cost alternatives."
                    )
            except Exception:
                # Silently fail on budget calculation
                pass

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
