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
    parts_excluded: list[str] = field(default_factory=list)  # named but negated
    budget_unlimited: bool = False  # "no budget", "unlimited", "money no object"
    notes: list[str] = field(default_factory=list)  # input that was read but not used


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
            "what ET does my Hayabusa run with turbo at Pomona in summer?"
        """
        query_lower = query.lower()

        notes: list[str] = []

        # Extract bike reference
        bike_query = self._extract_bike(query_lower)

        # Extract venue reference
        venue_query = self._extract_venue(query_lower)

        # Extract environmental conditions
        temp = self._extract_temperature(query_lower, notes)
        humidity = self._extract_humidity(query_lower)
        altitude = self._extract_altitude(query_lower)
        headwind, wind_dir = self._extract_wind(query_lower)

        # Extract budget
        budget = self._extract_budget(query_lower, notes)
        unlimited = budget is None and self._budget_is_unlimited(query_lower)

        # Extract parts mentioned (and the ones the user ruled out)
        parts, excluded = self._split_parts(self._without_venues(query_lower))

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
            parts_excluded=excluded,
            budget_unlimited=unlimited,
            notes=notes,
        )

    # ── typed numbers ────────────────────────────────────────────────────────
    # Every number in a query is found once, with the unit or marker attached to
    # it, and given exactly one type. The budget, the bike hint and the bike
    # lookup all read these types, so a year, a temperature, a sprocket size or
    # a model number can never be mistaken for money (or the other way round).
    _NUM_TOK_RE = re.compile(
        r"(?<![a-z0-9,])(?<![a-z]-)(?<!\d\.)"
        r"(?P<num>\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    )
    _UNIT_TYPES = tuple(
        (name, re.compile(rx))
        for name, rx in (
            ("speed", r"\s*(?:m/s|mps|km/h|kmph|kmh|kph|mph)(?![a-z0-9])"),
            (
                "temp",
                r"\s*(?:[°º˚]\s*[cf]?|degrees?(?:\s+(?:celsius|fahrenheit|c|f))?"
                r"|celsius|centigrade|fahrenheit|[cf])(?![a-z0-9])",
            ),
            ("percent", r"\s*%"),
            ("rpm", r"\s*(?:k\s*)?rpm(?![a-z0-9])"),
            ("mass", r"\s*(?:kgs?|kilograms?|lbs?|pounds?)(?![a-z0-9])"),
            ("disp", r"\s*cc(?![a-z0-9])"),
            ("pressure", r"\s*(?:psi|bar|kpa)(?![a-z0-9])"),
            ("power", r"\s*(?:hp|bhp|ps|kw|nm)(?![a-z0-9])"),
            (
                "length",
                r"\s*(?:kms?|miles?|mm|cm|m|meters?|metres?|ft|feet)(?![a-z0-9/])",
            ),
            (
                "time",
                r"\s*(?:secs?|seconds?|s|minutes?|mins?|hours?|hrs?|days?|years?|yrs?)"
                r"(?![a-z0-9])",
            ),
            ("teeth", r"(?:\s*(?:teeth|tooth)|t)(?![a-z0-9])"),
        )
    )
    _MONEY_SUFFIX_RE = re.compile(
        r"\s*(?P<s>thousand|lakhs?|lacs?|crores?|million|mn|cr|k|l)(?![a-z0-9])"
    )
    _NONMONEY_AFTER_RE = re.compile(
        r"^\s*(?:rpm|km|kg|cc|m\b|ft|psi|hp|bhp|miles?|mph|bar)"
    )
    _TEETH_BEFORE_RE = re.compile(
        r"(?:front|rear|sprocket|gearing|countershaft|cog)\s+(?:sprocket\s+)?"
        r"(?:of\s+|to\s+|=\s*|:\s*)?[+\-]?\s*$"
    )
    _TEETH_AFTER_RE = re.compile(r"^\s*(?:/\s*\d|sprockets?\b|gearing\b|cogs?\b)")
    _TEETH_PAIR_BEFORE_RE = re.compile(r"\d\s*/\s*$")

    @staticmethod
    def _is_year(raw: str) -> bool:
        return re.fullmatch(r"(?:19[5-9]|20[0-2])\d|203[0-5]", raw) is not None

    @classmethod
    def _number_tokens(cls, text: str) -> list[dict]:
        """Every number in lowercase ``text`` with its type and extent.

        Types: money (value in rupees), speed, temp, percent, rpm, mass, disp,
        pressure, power, length, time, teeth, glued (a model number fused to
        letters: "10r", "4c8"), year (bare 1950-2035), bare (none of these).
        ``start``/``end`` cover the number and everything attached to it
        (currency marker, unit, magnitude suffix).
        """
        out: list[dict] = []
        claimed = 0  # end of the last currency marker an earlier number took
        for m in cls._NUM_TOK_RE.finditer(text):
            value = float(m.group("num").replace(",", ""))
            s, e = m.start(), m.end()
            before, after = text[:s], text[e:]
            tok = {"type": "bare", "start": s, "end": e, "value": value, "weak": False}
            sm = cls._MONEY_SUFFIX_RE.match(after)
            if sm and cls._NONMONEY_AFTER_RE.match(after[sm.end() :]):
                sm = None
            pos = e + (sm.end() if sm else 0)
            cb = cls._CUR_BEFORE_RE.search(before)
            ca = cls._CUR_AFTER_RE.match(text[pos:])
            if ca:
                nxt = cls._NEXT_NUMBER_RE.match(text[pos + ca.end() :])
                rest = text[pos + ca.end() + nxt.end() :] if nxt else ""
                if (
                    nxt
                    and not cls._is_year(nxt.group(1))
                    and not any(rx.match(rest) for _, rx in cls._UNIT_TYPES)
                ):
                    ca = None  # "duke 250 INR 55000": the marker is the next amount's
            if ca and cls._is_year(m.group("num")) and not sm:
                ca = None  # "2021 Rs. 1,50,000": the marker belongs to what follows
            if cb and cb.start() < claimed:
                cb = None  # that marker already closes the previous amount
            if cb and re.search(r"rs\s*$", before) and value < 1000 and not sm:
                cb = None  # "RS 660" is a model, "Rs 5000" is money
            mult = cls._SUFFIX_MULT[sm.group("s")] if sm else 1.0
            if cb or ca:
                if ca:
                    claimed = pos + ca.end()
                tok.update(
                    type="money",
                    start=cb.start() if cb else s,
                    end=pos + (ca.end() if ca else 0),
                    value=value * mult,
                )
                out.append(tok)
                continue
            for name, rx in cls._UNIT_TYPES:
                um = rx.match(after)
                if um:
                    tok.update(type=name, end=e + um.end())
                    break
            else:
                if sm:
                    tok.update(
                        type="money",
                        end=pos,
                        value=value * mult,
                        weak=sm.group("s") == "l",
                    )
                elif (
                    cls._TEETH_AFTER_RE.match(after)
                    or cls._TEETH_BEFORE_RE.search(before)
                    or cls._TEETH_PAIR_BEFORE_RE.search(before)
                ):
                    tok["type"] = "teeth"
                elif after[:1].isalpha():
                    tok["type"] = "glued"
                elif re.fullmatch(r"\d{4}", m.group("num")) and (1950 <= value <= 2035):
                    tok["type"] = "year"
            out.append(tok)
        return out

    @classmethod
    def _mask_typed_numbers(
        cls, text: str, keep: tuple[str, ...], fill: str = " "
    ) -> str:
        """``text`` with every number whose type is not in ``keep`` blanked out."""
        pieces, last = [], 0
        for t in cls._number_tokens(text):
            if t["type"] in keep:
                continue
            pieces.append(text[last : t["start"]])
            pieces.append(fill)
            last = t["end"]
        pieces.append(text[last:])
        return "".join(pieces)

    # ── bike phrase (from the text alone) ───────────────────────────────────
    # Words that end a bike name when reading "my <bike> ...".
    _BIKE_STOP = frozenset(
        "for at with in on to and from of run does do is are will would "
        "can could get gets give gives make makes under below within over "
        "using use plus without no not but then also only have has had "
        "budget stock bike motorcycle motorbike when while what which how "
        "optimize optimise simulate sim setup set tune upgrade upgraded "
        "modified mod mods by or if as it its i we you me us please pls "
        "show tell compare vs versus".split()
    )
    # Weather, track, money and gearing words: never part of a bike's name.
    _NON_BIKE_WORDS = frozenset(
        "wet dry track rubber buildup vht pj1 prep humidity headwind tailwind "
        "wind altitude elevation asl temp temperature lakh lakhs lac lacs inr "
        "rupees rs unlimited limit summer winter monsoon hot cold warm weather "
        "gearing gear gears tooth teeth front rear ratio celsius fahrenheit "
        "degrees degree sea level above around about approx approximately "
        "roughly upto up max maximum min cap afford spend spending price "
        "ceiling thousand million crore cr per day today et quarter mile trap "
        "time result results".split()
    )
    # Model names that stand alone ("Hayabusa", "Bullet"); the catalog resolves them.
    _BIKE_WORDS = frozenset(
        "busa hayabusa bullet fireblade panigale monster scout meteor "
        "interceptor himalayan".split()
    )

    def _extract_bike(self, query_lower: str) -> str:
        """Best-effort bike phrase from the text alone (no catalog needed).

        Numbers that are money, weather, a year or a sprocket size are blanked
        first, so what is left is words plus model numbers; the longest run of
        those (or the run after "my"/"a"/"the") that looks like a bike is the
        hint. ``NLSimRunner`` resolves bikes against the catalog; this is the
        fallback it uses and what ``ParsedQuery.bike_query`` carries for
        parser-only callers.
        """
        text = self._mask_typed_numbers(query_lower, ("bare", "glued"), " | ")
        toks = re.findall(r"[a-z0-9][a-z0-9\-]*|[|,;:.!?()]", text)
        part_words = {
            w for kws in self.PART_KEYWORDS.values() for k in kws for w in k.split()
        }
        venue_words = {w for a in self.VENUE_ALIASES for w in re.split(r"[\s-]+", a)}
        stop = self._BIKE_STOP | self._NON_BIKE_WORDS | part_words | venue_words
        markers = {"my", "a", "an", "the", "our"}
        runs: list[tuple[list[str], bool]] = []
        cur: list[str] = []
        cur_marker = marker = False

        def flush():
            nonlocal cur
            if cur:
                runs.append((cur, cur_marker))
            cur = []

        for t in toks:
            if t in markers:
                flush()
                marker = True
            elif t == "|":
                flush()
            elif t in ",;:.!?()" or t in stop:
                flush()
                marker = False
            elif t.isdigit() and len(t) >= 5:
                flush()
            else:
                if not cur:
                    cur_marker = marker
                cur.append(t)
        flush()

        def mixed(t: str) -> bool:
            return bool(re.search(r"[a-z]", t) and re.search(r"\d", t))

        def qualifies(run: list[str], marked: bool) -> bool:
            for i, t in enumerate(run):
                if mixed(t) or t in self.BIKE_ALIASES or t in self._BIKE_WORDS:
                    return True
                nxt = run[i + 1] if i + 1 < len(run) else ""
                if t.replace("-", "").isalpha() and nxt.isdigit() and len(nxt) <= 4:
                    return True
            return marked and any(t.replace("-", "").isalpha() for t in run)

        good = [(r, m) for r, m in runs if qualifies(r, m)]
        for run, marked in good:
            if marked:
                return " ".join(run)
        if good:
            return " ".join(max((r for r, _ in good), key=len))
        return ""

    def _without_venues(self, query_lower: str) -> str:
        """Query text with venue names blanked ("Santa Pod" is not an intake pod)."""
        for alias in self.VENUE_ALIASES:
            query_lower = query_lower.replace(alias, " ")
        return query_lower

    def _extract_venue(self, query_lower: str) -> str | None:
        """Extract venue reference from query."""
        for alias, standard in self.VENUE_ALIASES.items():
            if alias in query_lower:
                return standard
        return None

    # ── temperature ──────────────────────────────────────────────────────────
    _TEMP_NUM = r"(?P<sign>-|−|minus\s+|negative\s+)?(?P<num>\d+(?:\.\d+)?)"
    _TEMP_DEG = r"\s*(?P<deg>°|º|˚|degrees?\b|deg\b\.?)?\s*"
    _TEMP_UNIT = r"(?P<unit>celsius|centigrade|fahrenheit|c|f)(?![a-z0-9])"
    _TEMP_RE = re.compile(rf"(?<![\w.]){_TEMP_NUM}{_TEMP_DEG}{_TEMP_UNIT}")
    _TEMP_RANGE_RE = re.compile(
        r"(?<![\w.])(?P<a>\d+(?:\.\d+)?)\s*(?:°|º|˚|degrees?|deg)?\s*"
        r"(?:-|–|—|to)\s*"
        r"(?P<b>\d+(?:\.\d+)?)\s*(?P<deg>°|º|˚|degrees?\b|deg\b\.?)?\s*"
        r"(?P<unit>celsius|centigrade|fahrenheit|c|f)(?![a-z0-9])"
    )
    _TEMP_BELOW_ZERO_RE = re.compile(
        r"(?<![\w.])(?P<num>\d+(?:\.\d+)?)\s*(?:°|º|˚|degrees?)?\s*"
        r"(?P<unit>celsius|centigrade|fahrenheit|c|f)?\s*below\s+(?:zero|freezing|0)\b"
    )
    _TEMP_WORD_RE = re.compile(
        r"\btemp(?:erature)?\s*(?:of|is|at|=|:)?\s*"
        r"(?P<sign>-|−|minus\s+|negative\s+)?(?P<num>\d+(?:\.\d+)?)(?![\d.]*\s*"
        r"(?:%|°|c\b|f\b|k\b|km|mph|kg|m/s|rpm|hp|cc|ft))"
    )
    # Ambient air the simulator accepts as plausible, in Celsius.
    _TEMP_MIN_C, _TEMP_MAX_C = -60.0, 60.0

    @staticmethod
    def _to_celsius(value: float, unit: str) -> float:
        if unit.startswith("f"):
            return (value - 32.0) * 5.0 / 9.0
        return value

    def _temp_candidate(
        self, value: float, unit: str, explicit: bool, notes: list[str]
    ) -> float | None:
        """Celsius value if plausible; else None (with a note when explicit)."""
        t_c = round(self._to_celsius(value, unit), 2)
        if self._TEMP_MIN_C <= t_c <= self._TEMP_MAX_C:
            return t_c
        if explicit or unit.startswith("c"):
            shown = f"{value:g}°{unit[0].upper()}"
            conv = f" ({t_c:g}°C)" if unit.startswith("f") else ""
            notes.append(
                f"temperature {shown}{conv} is outside "
                f"{self._TEMP_MIN_C:g}..{self._TEMP_MAX_C:g}°C, so it was not applied"
            )
        return None

    def _extract_temperature(
        self, query_lower: str, notes: list[str] | None = None
    ) -> float | None:
        """Ambient temperature in Celsius, or None.

        Reads signed values ("-5C", "minus 5 C", "5 below zero"), Celsius
        ("35C", "35 degrees celsius") and Fahrenheit ("95F", "95 degrees
        fahrenheit"; converted). A range ("35-40C") gives its midpoint. A hyphen
        glued to a preceding word or number is a dash, never a minus. Values
        outside -60..60 C are not applied and a note says so. A bare
        "temperature 35" with no unit is read as Celsius.
        """
        notes = notes if notes is not None else []
        text = query_lower
        for m in self._TEMP_RANGE_RE.finditer(text):
            unit = m.group("unit")
            if unit == "f" and not m.group("deg"):
                continue  # "600-700 f": a model range, not a temperature
            lo, hi = float(m.group("a")), float(m.group("b"))
            got = self._temp_candidate(
                (lo + hi) / 2.0, unit, bool(m.group("deg")), notes
            )
            if got is not None:
                return got
        for m in self._TEMP_BELOW_ZERO_RE.finditer(text):
            got = self._temp_candidate(
                -float(m.group("num")), m.group("unit") or "c", True, notes
            )
            if got is not None:
                return got
        for m in self._TEMP_RE.finditer(text):
            unit = m.group("unit")
            explicit = bool(m.group("deg")) or len(unit) > 1
            if unit == "f" and not explicit:
                # A bare "95f" is plausible only as a real Fahrenheit reading.
                if not 0 <= float(m.group("num")) <= 140:
                    continue
            value = float(m.group("num"))
            if m.group("sign"):
                value = -value
            got = self._temp_candidate(value, unit, explicit, notes)
            if got is not None:
                return got
        m = self._TEMP_WORD_RE.search(text)
        if m:
            value = float(m.group("num"))
            if m.group("sign"):
                value = -value
            return self._temp_candidate(value, "c", True, notes)
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
        "kmph": 1.0 / 3.6,
        "mph": 0.44704,
    }

    def _extract_wind(self, query_lower: str) -> tuple[float | None, float | None]:
        """Extract wind as (speed in m/s, direction deg: 0 head / 180 tail).

        Understands m/s, km/h (kmh, kph) and mph, in "5 m/s headwind",
        "headwind of 20 km/h", "12 mph tailwind" and "wind of 4 m/s" forms.
        Unqualified "wind" means headwind.
        """
        num = r"(\d+(?:\.\d+)?)"
        unit = r"(m/s|mps|km/h|kmph|kmh|kph|mph)"
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

    # ── budget ───────────────────────────────────────────────────────────────
    _SUFFIX_MULT = {
        "k": 1e3,
        "thousand": 1e3,
        "l": 1e5,
        "lakh": 1e5,
        "lakhs": 1e5,
        "lac": 1e5,
        "lacs": 1e5,
        "cr": 1e7,
        "crore": 1e7,
        "crores": 1e7,
        "mn": 1e6,
        "million": 1e6,
    }
    _CUR_BEFORE_RE = re.compile(r"(?:₹|\brs\.?|\binr|\brupees?)\s*$")
    _CUR_AFTER_RE = re.compile(r"^\s*(?:/-|(?:inr|rupees?|rs)\b\.?|₹)")
    _NEXT_NUMBER_RE = re.compile(r"\s*(\d[\d,]*(?:\.\d+)?)")
    _BUDGET_BEFORE_RE = re.compile(
        r"\b(?:budget|spend|spending|afford|cap|capped|limit|maximum|max|ceiling|"
        r"price)\b(?:\s+(?:of|is|at|around|about|approx|approximately|upto|up\s+to|"
        r"under|within|to|a|an|the|total|nearly|roughly)\b)*[\s:=~]*"
        r"(?:₹|rs\.?|inr)?\s*$"
    )
    _WEAK_BEFORE_RE = re.compile(
        r"\b(?:under|below|within|upto|up\s+to|less\s+than|at\s+most|around|about|"
        r"roughly|approx(?:imately)?)\s*(?:₹|rs\.?|inr)?\s*$"
    )
    _BUDGET_AFTER_RE = re.compile(
        r"^\s*(?:inr|rupees?|rs\.?)?\s*(?:budget|spend|max(?:imum)?|limit|cap)\b"
    )
    # What may stand right before a bare "<number> budget": a joining word or a
    # clause break, never a bike name ("Duke 390 budget").
    _CONNECTOR_BEFORE_RE = re.compile(
        r"(?:^|[,;]\s*|\b(?:with|a|an|the|for|of|my|have|has)\s+)$"
    )
    _UNLIMITED_RE = re.compile(
        r"\b(?:no\s+budget|without\s+(?:a\s+)?budget|unlimited(?:\s+budget)?|"
        r"no[\s-]+limit|"
        r"no\s+spending\s+limit|any\s+budget|money\s+(?:is\s+)?no\s+object|"
        r"budget\s+(?:is\s+)?no\s+(?:issue|object|concern|problem|limit|bar)|"
        r"sky'?s\s+the\s+limit|cost\s+(?:is\s+)?no\s+(?:issue|object)|"
        r"no\s+cap\s+on\s+(?:the\s+)?(?:budget|spend\w*))\b"
    )
    BUDGET_AMBIGUOUS_NOTE = (
        "I couldn't tell which number is your budget — say e.g. 'budget ₹50,000'"
    )

    def _extract_budget(
        self, query_lower: str, notes: list[str] | None = None
    ) -> int | None:
        """Budget in rupees, or None when the text states no amount.

        Numbers are typed first (``_number_tokens``): only a money token (a
        currency marker or a magnitude suffix: k, thousand, lakh, lac, L, crore,
        cr, million) or a bare number that follows a budget word can be a
        budget. Years, model numbers, temperatures, speeds, sizes, percentages
        and sprocket sizes never are.

        Several money tokens: the one next to a budget/limit word wins (a
        "budget"/"spend" word beats "under"/"within"). With no way to choose,
        the budget stays None and ``notes`` says so; a wrong budget is worse
        than none.
        """
        text = query_lower
        toks = self._number_tokens(text)

        def anchor(t: dict) -> int:
            """2 strong keyword beside it, 1 weak keyword, 0 none."""
            win = text[max(0, t["start"] - 48) : t["start"]]
            after = text[t["end"] :]
            if self._BUDGET_BEFORE_RE.search(win) or self._BUDGET_AFTER_RE.match(after):
                return 2
            return 1 if self._WEAK_BEFORE_RE.search(win) else 0

        def refuse() -> None:
            if notes is not None and self.BUDGET_AMBIGUOUS_NOTE not in notes:
                notes.append(self.BUDGET_AMBIGUOUS_NOTE)

        money = [
            t for t in toks if t["type"] == "money" and (not t["weak"] or anchor(t))
        ]
        if len(money) == 1:
            return int(round(money[0]["value"]))
        if money:
            top = max(anchor(t) for t in money)
            best = [t for t in money if anchor(t) == top] if top else []
            if len(best) == 1:
                return int(round(best[0]["value"]))
            refuse()
            return None

        found: tuple[int, int, int] | None = None  # (priority, position, rupees)
        unclear = False
        for t in toks:
            if t["type"] != "bare":
                continue
            rupees = int(round(t["value"]))
            before = text[: t["start"]]
            win = before[-48:]
            after = text[t["end"] :]
            if self._BUDGET_BEFORE_RE.search(win):
                prio = 0
            elif self._WEAK_BEFORE_RE.search(win) and rupees >= 1000:
                prio = 1
            elif self._BUDGET_AFTER_RE.match(after):
                if rupees >= 1000 and self._CONNECTOR_BEFORE_RE.search(before):
                    prio = 2
                else:
                    unclear = unclear or rupees >= 10000
                    continue
            else:
                continue
            if rupees > 0 and (found is None or (prio, t["start"]) < found[:2]):
                found = (prio, t["start"], rupees)
        if found:
            return found[2]
        if unclear:
            refuse()
        return None

    def _budget_is_unlimited(self, query_lower: str) -> bool:
        """True for "no budget", "unlimited", "money no object", ..."""
        return self._UNLIMITED_RE.search(query_lower) is not None

    # ── parts, with negation ─────────────────────────────────────────────────
    _NEGATORS = frozenset(
        "without w/o no not none never nor minus excluding exclude excluded "
        "except besides remove removing delete skip avoid omit forget ignore "
        "sans don't dont doesn't doesnt didn't didnt can't cant won't wont "
        "shouldn't".split()
    )
    # Ends a negation scope: a positive marker or a conjunction that flips it.
    _SCOPE_STOP = frozenset("with plus but then also only using however yet".split())
    # Words a negation reaches through ("don't add nitrous", "no need for ECU").
    _SCOPE_PASS = frozenset(
        "add use install fit include want need put get run any a an the my of "
        "for extra additional new fancy aftermarket some more and or nor to be "
        "i we you really kind sort mess any".split()
    )
    _BUDGETISH = frozenset(
        "budget budgets limit limits cap restriction restrictions".split()
    )
    _TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'’\-/]*|[,;:.!?()]")

    def _negated_spans(self, text: str) -> list[tuple[int, int]]:
        """Character spans of ``text`` that sit inside a negation scope."""
        spans: list[tuple[int, int]] = []
        active = False
        left = 0
        for m in self._TOKEN_RE.finditer(text):
            tok = m.group(0).replace("’", "'")
            if tok in self._NEGATORS:
                active, left = True, 6
                continue
            if not active:
                continue
            if tok in self._SCOPE_STOP or tok in ",;:.!?()" or tok in self._BUDGETISH:
                active = False
                continue
            left -= 1
            if left < 0:
                active = False
                continue
            if tok not in self._SCOPE_PASS:
                spans.append((m.start(), m.end()))
        return spans

    def _split_parts(self, query_lower: str) -> tuple[list[str], list[str]]:
        """Parts to apply and parts the user ruled out, as parser categories.

        "without exhaust", "no turbo", "don't add nitrous", "except ECU" and
        "stock exhaust" exclude the category named after them. A category named
        both ways counts as wanted.
        """
        neg = self._negated_spans(query_lower)
        stock_starts = {m.end() for m in re.finditer(r"\bstock\s+", query_lower)}
        wanted: list[str] = []
        excluded: list[str] = []
        for category, pattern in self._part_patterns.items():
            hits = list(pattern.finditer(query_lower))
            if not hits:
                continue
            negated = [
                h
                for h in hits
                if h.start() in stock_starts or any(a <= h.start() < b for a, b in neg)
            ]
            if len(negated) < len(hits):
                wanted.append(category)
            else:
                excluded.append(category)
        return wanted, excluded

    def _extract_parts(self, query_lower: str) -> list[str]:
        """Parts mentioned and not negated (see ``_split_parts``)."""
        return self._split_parts(query_lower)[0]

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
        # "no budget" / "unlimited" lifts the limit; it is not a budget request.
        query_lower = self._UNLIMITED_RE.sub(" ", query_lower)

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
        self._bike_idx: list[dict] | None = None

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

        # Resolve bike: the catalog's own names first, then the parser's phrase.
        self.last_bike_alternatives = []
        bike_model, phrase, runners = self._match_bike(query)
        if bike_model:
            parsed.bike_query = phrase
            self.last_bike_alternatives = [
                f"{r['manufacturer_name']} {r['model_name']}" for r in runners
            ]
        else:
            bike_model = self._resolve_bike(parsed.bike_query)
        if not bike_model:
            what = (
                f"matching '{parsed.bike_query}'"
                if parsed.bike_query
                else "named in the query"
            )
            return {
                "error": f"Could not find a bike {what}. Try 'bikes' command to see available models."
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
        suggestions.extend(parsed.notes)

        return {
            "parsed_query": {
                "raw_query": parsed.raw_query,
                "bike_query": parsed.bike_query,
                "venue_query": parsed.venue_query,
                "temperature_c": parsed.temperature_c,
                "humidity_pct": parsed.humidity_pct,
                "parts_mentioned": parsed.parts_mentioned,
                "parts_excluded": parsed.parts_excluded,
                "budget_inr": parsed.budget_inr,
                "budget_unlimited": parsed.budget_unlimited,
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
            "parts_excluded": list(parsed.parts_excluded),
            "parse_notes": list(parsed.notes),
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

    # ── bike vocabulary (the catalog's own names) ─────────────────────────────
    # Single query words that name no bike on their own.
    _GENERIC_WORDS = frozenset(
        "my the bike bikes motorcycle motorbike with for and from at in on to of "
        "stock sport street super pro special edition road race racing track "
        "speed time budget best max test quick sim simulate setup optimize "
        "optimise what does run how fast add get try compare inr rupees rs "
        "humidity temp temperature wind headwind tailwind altitude summer winter "
        "monsoon exhaust intake filter ecu clutch chain sprocket battery brake "
        "brakes tire tyre tires tyres slick nitrous turbo supercharger".split()
    )
    # Short spoken forms -> the words the catalog uses.
    _QUERY_ALIASES = {
        "busa": ("hayabusa",),
        "gixxer": ("gsxr",),
        "gsxr": ("gsx", "r"),
        "fireblade": ("fireblade",),
    }
    _MFR_ALIASES = {
        "re": "royalenfield",
        "hd": "harleydavidson",
        "harley": "harleydavidson",
        "mv": "mvagusta",
        "kawa": "kawasaki",
        "beemer": "bmw",
    }
    _YEAR_TOKEN = re.compile(r"(?:19|20)\d\d")

    def _bike_index(self) -> list[dict]:
        """Per-bike matching view of the catalog, built once per runner."""
        if self._bike_idx is not None:
            return self._bike_idx
        idx: list[dict] = []
        for order, row in enumerate(self.db.bikes.search(limit=20000)):
            toks = self._norm_tokens(row["model_name"])
            view: dict[str, int] = {}
            for i in range(len(toks)):
                acc = ""
                for j in range(i, min(i + 4, len(toks))):
                    acc += toks[j]
                    span = j - i + 1
                    if acc not in view or view[acc] > span:
                        view[acc] = span
            for code in self._norm_tokens(str(row.get("model_code") or "")):
                if re.search(r"[a-z]", code) and re.search(r"\d", code):
                    view.setdefault(code, 0)
            idx.append(
                {
                    "row": row,
                    "order": order,
                    "toks": toks,
                    "view": view,
                    "mfr": re.sub(r"[^a-z0-9]", "", row["manufacturer_name"].lower()),
                }
            )
        self._bike_idx = idx
        return idx

    def _scrub_for_bike(self, text: str) -> str:
        """Blank venue names and every typed number (money, weather, sizes) so
        none of them can read as a bike; years stay for the model-year tie-break.
        """
        text = text.lower()
        for alias in NLQueryParser.VENUE_ALIASES:
            text = text.replace(alias, " ")
        return NLQueryParser._mask_typed_numbers(text, ("bare", "glued", "year"))

    def _match_bike(self, query: str) -> tuple[dict | None, str, list[dict]]:
        """Find the catalog bike a free-text query names.

        Query words (and any 1-4 word run, in any order, with the spaces and
        hyphens removed: "gsxr 1000" = "GSX-R 1000", "zx10r" = "ZX-10R") are
        looked up in each bike's name and code. The bike covering the most of
        the query wins; ties go to the named manufacturer, a model year the
        query gives, the commonly-benchmarked family, the closest name, then
        the newest generation. Returns (row, matched phrase, runners-up).
        """
        from itertools import permutations

        text = self._scrub_for_bike(query)
        raw = [t for t in re.split(r"[^a-z0-9]+", text) if t]
        year = next((int(t) for t in raw if self._YEAR_TOKEN.fullmatch(t)), None)
        toks: list[str] = []
        for t in raw:
            if self._YEAR_TOKEN.fullmatch(t):
                continue
            toks.extend(self._QUERY_ALIASES.get(t, (t,)))
        if not toks:
            return None, "", []

        def distinctive(c: str) -> bool:
            return (
                bool(re.search(r"[a-z]", c))
                and c not in self._GENERIC_WORDS
                and (len(c) >= 3 or (len(c) >= 2 and re.search(r"\d", c) is not None))
            )

        grams: list[tuple[int, int, str, tuple[int, ...]]] = []
        for start in range(len(toks)):
            for n in range(1, 5):
                if start + n > len(toks):
                    break
                span = tuple(range(start, start + n))
                orders = permutations(span) if n <= 3 else [span]
                for order in orders:
                    c = "".join(toks[i] for i in order)
                    if n == 1 and not distinctive(c):
                        continue
                    if n > 1 and not re.search(r"[a-z]", c):
                        continue
                    grams.append((n, len(c), c, span))
        grams.sort(key=lambda g: (-g[0], -g[1]))
        compacts = {
            "".join(toks[i:j])
            for i in range(len(toks))
            for j in range(i + 1, min(i + 3, len(toks)) + 1)
        }
        q_mfrs = compacts | {self._MFR_ALIASES.get(t, t) for t in toks}

        scored: list[tuple[tuple, dict, set[int]]] = []
        for ent in self._bike_index():
            view = ent["view"]
            covered: set[int] = set()
            score = spans = 0
            for n, length, c, span in grams:
                if c in view and covered.isdisjoint(span):
                    covered.update(span)
                    score += length
                    spans += view[c]
            if not score:
                continue
            name_toks = set(ent["toks"])
            for i, t in enumerate(toks):
                if i not in covered and t.isdigit() and t in name_toks:
                    score += len(t)
                    spans += 1
            row = ent["row"]
            mfr_hit = any(
                m == ent["mfr"] or (len(m) >= 4 and ent["mfr"].startswith(m))
                for m in q_mfrs
            )
            y0, y1 = row.get("year_from"), row.get("year_to")
            year_miss = (
                0
                if year is None
                else (0 if (y0 or 0) <= year and (y1 is None or year <= y1) else 1)
            )
            ts = set(ent["toks"])
            popular = 0 if any(h <= ts for h in self._POPULAR_BIKE_TOKENS) else 1
            extra = max(len(ent["toks"]) - spans, 0)
            key = (
                -score,
                0 if mfr_hit else 1,
                year_miss,
                popular,
                extra,
                -(y0 or 0),
                ent["order"],
            )
            scored.append((key, row, covered))
        if not scored:
            return None, "", []
        scored.sort(key=lambda s: s[0])
        key, row, covered = scored[0]
        phrase = " ".join(toks[i] for i in sorted(covered))
        runners = [r for k, r, _ in scored[1:] if k[0] == key[0]][:5]
        return row, phrase, runners

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
            if not {"turbo", "supercharger"} & (
                set(parsed.parts_mentioned) | set(parsed.parts_excluded)
            ):
                suggestions.append(
                    "Consider turbocharger or supercharger for ET improvement (0.3-0.5s typical)"
                )
        if result.time_quarter > 10.0:
            if not {"weight_reduction"} & (
                set(parsed.parts_mentioned) | set(parsed.parts_excluded)
            ):
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
