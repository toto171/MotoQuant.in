"""
Smart fuzzy resolver for bike + venue names.

Replaces the old `_resolve_against_db` simple substring lookup which failed
on common shapes like:
  - "Suzuki Hayabusa"     → DB has "Hayabusa GSX1300R Gen1" / "Hayabusa (2008-2012)"
  - "KTM RC 390"          → DB has "RC 390"; manufacturer prefix in query confused matcher
  - "Yamaha YZF-R15 V4"   → DB has "YZF-R15 V4 (2021-2026)"; year-range parens broke match
  - "fastest bike"        → no specific bike; intent classifier handles separately

Strategy:
  1. Normalise query: lowercase, replace -/_ with space, split into tokens.
  2. Strip known manufacturer prefixes if they're not in DB model_name.
  3. Strip "(YYYY-YYYY)" parenthetical year ranges from candidate model_names.
  4. Token-set Jaccard similarity scoring + substring containment bonus.
  5. Return best match if score >= MATCH_THRESHOLD, else None + suggestions.

No external dependencies. Pure stdlib.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..database.connection import MotoQuantDB

# Manufacturers known to appear at the start of user queries.
# When the LLM returns "Suzuki Hayabusa" but the DB row has model_name="Hayabusa
# GSX1300R Gen1" + manufacturer="Suzuki" (joined separately), we strip the
# manufacturer prefix from the query before matching against model_name.
_KNOWN_MANUFACTURERS = {
    "suzuki",
    "yamaha",
    "honda",
    "kawasaki",
    "ducati",
    "bmw",
    "ktm",
    "aprilia",
    "triumph",
    "harley-davidson",
    "harley",
    "indian",
    "royal enfield",
    "re",
    "bajaj",
    "tvs",
    "hero",
    "yezdi",
    "jawa",
    "benelli",
    "cfmoto",
    "qj motor",
    "qj",
    "mahindra",
    "hyosung",
    "mv agusta",
    "moto guzzi",
    "buell",
    "husqvarna",
    "bimota",
    "bsa",
    "benda",
    "ebr",
    "kove",
    "norton",
    "zontes",
    "hd",
    "indian motorcycle",
    "cf moto",
}

# Short or informal manufacturer names -> the catalog's name (normalised).
# Scoring compares against the candidate's real manufacturer, so "RE Classic
# 350" must know that "re" means Royal Enfield.
_MANUFACTURER_ALIASES = {
    "re": "royal enfield",
    "harley": "harley davidson",
    "hd": "harley davidson",
    "indian motorcycle": "indian",
    "qj": "qj motor",
    "cf moto": "cfmoto",
}

# Strip "(2024-2026)", "(2024)", etc. from candidate names before scoring.
_YEAR_RANGE_RE = re.compile(r"\s*\(\s*\d{4}(?:\s*[-–]\s*\d{4})?\s*\)\s*")

# Common single-letter token noise we want to keep (V4, V2, K5, R1 etc) — these
# are MEANINGFUL as bike identifiers, so don't drop them.
# Anything below 2 chars otherwise is filtered out.
_MIN_TOKEN_LEN = 2

MATCH_THRESHOLD = 60  # 0-100 scale; below this → bike_not_found
SUGGESTIONS_LIMIT = 5


# ───────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────


@lru_cache(maxsize=8192)  # pure; a catalog-wide scan re-normalises ~550 names
def _normalize(s: str) -> str:
    """Lowercase, drop punctuation that confounds matching, collapse spaces."""
    if not s:
        return ""
    s = s.lower()
    s = _YEAR_RANGE_RE.sub(" ", s)
    # Replace separators with space so "yzf-r15" tokens match "yzf r15"
    s = re.sub(r"[-/_,.]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _tokenize(s: str) -> set[str]:
    """Set of tokens with length >= _MIN_TOKEN_LEN."""
    n = _normalize(s)
    return {t for t in n.split() if len(t) >= _MIN_TOKEN_LEN}


def _strip_manufacturer_prefix(query: str) -> tuple[str, str | None]:
    """Strip a known manufacturer prefix from the query. Return (stripped, mfr).

    Examples:
      "Suzuki Hayabusa"    -> ("hayabusa", "suzuki")
      "KTM RC 390"         -> ("rc 390", "ktm")
      "Royal Enfield 650"  -> ("650", "royal enfield")
      "RC 390"             -> ("rc 390", None)
    """
    q = _normalize(query)
    if not q:
        return q, None
    # Try multi-word manufacturers first (so "royal enfield" matches before "re").
    # Keys are normalised like the query ("harley-davidson" -> "harley
    # davidson"), else a hyphenated brand could never match its own prefix.
    for mfr in sorted(_KNOWN_MANUFACTURERS, key=len, reverse=True):
        key = _normalize(mfr)
        if q.startswith(key + " ") or q == key:
            stripped = q[len(key) :].strip()
            return stripped, key
    return q, None


def _canonical_manufacturer(name: str | None) -> str:
    """Normalised catalog manufacturer name for a brand or its alias."""
    n = _normalize(name or "")
    return _MANUFACTURER_ALIASES.get(n, n)


def _compact_windows(seq: list[str]) -> dict[str, int]:
    """Every contiguous run of tokens joined with no separator, mapped to the
    fewest tokens left outside that run.

    "Ninja ZX-10R" -> tokens [ninja, zx, 10r] -> {"ninja": 2, "ninjazx": 1,
    "ninjazx10r": 0, "zx": 2, "zx10r": 1, "10r": 2}. A query typed without
    separators ("ZX10R", "S1000RR", "GSX-R1000 K5") then matches the catalog
    spelling ("ZX-10R", "S 1000 RR", "GSX-R 1000 K5/K6") exactly on a token
    boundary, so "R1" still does NOT match "R15".
    """
    out: dict[str, int] = {}
    n = len(seq)
    for i in range(n):
        joined = ""
        for j in range(i, n):
            joined += seq[j]
            extra = n - (j - i + 1)
            if joined not in out or extra < out[joined]:
                out[joined] = extra
    return out


def _compact_score(query: str, candidate: str) -> int:
    """0-100: how well the separator-free query matches a token run of the
    candidate (see _compact_windows). 0 when it does not match."""
    q_seq = _normalize(query).split()
    q_compact = "".join(q_seq)
    if len(q_compact) < 2:
        return 0
    extra = _compact_windows(_normalize(candidate).split()).get(q_compact)
    if extra is None:
        return 0
    return max(85, 100 - 3 * extra)


def _compact_match(query: str, candidate: str) -> bool:
    return _compact_score(query, candidate) > 0


def _score_candidate(query: str, manufacturer: str, model_name: str) -> int:
    """0-100 similarity score between query and a candidate (manufacturer, model_name).

    Higher = better. The best of:
      - token-set containment / Jaccard of the full query against
        "manufacturer model" (_token_score);
      - the same with the manufacturer prefix stripped, scored against the
        model name alone, when the query's brand (or its alias, "RE" ->
        Royal Enfield) IS the candidate's manufacturer;
      - a separator-free match ("ZX10R" vs "ZX-10R", "S1000RR" vs
        "S 1000 RR") on a token boundary (_compact_score).
    """
    if not _normalize(query):
        return 0
    cand_full = f"{manufacturer} {model_name}".strip()
    best = max(
        _token_score(query, manufacturer, model_name),
        _compact_score(query, cand_full),
        _compact_score(query, model_name),
    )
    stripped, q_mfr = _strip_manufacturer_prefix(query)
    if (
        q_mfr
        and stripped
        and manufacturer
        and _canonical_manufacturer(q_mfr) == _canonical_manufacturer(manufacturer)
    ):
        best = max(
            best,
            _token_score(stripped, "", model_name),
            _compact_score(stripped, model_name),
        )
    return best


def _token_score(query: str, manufacturer: str, model_name: str) -> int:
    """Token-set containment / Jaccard score (see _score_candidate)."""
    q_norm = _normalize(query)
    if not q_norm:
        return 0

    # Strip parenthetical year range from model_name before scoring.
    cand_model = _normalize(model_name)
    cand_full = f"{_normalize(manufacturer)} {cand_model}".strip()

    q_tokens = _tokenize(query)
    cand_tokens = _tokenize(cand_full)
    if not q_tokens or not cand_tokens:
        return 0

    # Containment: if every query token appears in the candidate, near-perfect.
    if q_tokens.issubset(cand_tokens):
        # Tight containment is best; reward shorter candidates more (closer match).
        # If candidate has many extra tokens, slightly penalise.
        extra = len(cand_tokens - q_tokens)
        score = max(85, 100 - 3 * extra)
        # _tokenize drops 1-char tokens, so "CBR1000RR-R" contains-matched the
        # plain CBR1000RR as strongly as the RR-R. Charge each dropped query
        # token the candidate does not have.
        short = {t for t in q_norm.split() if len(t) < _MIN_TOKEN_LEN}
        missing = short - set(cand_full.split())
        return score - 10 * len(missing)

    # Otherwise Jaccard.
    intersect = q_tokens & cand_tokens
    union = q_tokens | cand_tokens
    if not union:
        return 0
    base = int(100 * len(intersect) / len(union))

    # Boost: every query token also appears as substring of any cand token
    # (catches "RC390" matching candidate "RC 390" via substring).
    cand_join = " ".join(sorted(cand_tokens))
    substr_hits = sum(1 for t in q_tokens if t in cand_join)
    if q_tokens and substr_hits / len(q_tokens) >= 0.8:
        base = max(base, 70)

    return base


# ───────────────────────────────────────────────────────────────────
# Public resolution API
# ───────────────────────────────────────────────────────────────────


def resolve_bike(
    name: str | None, db: MotoQuantDB
) -> tuple[int | None, list[dict[str, Any]]]:
    """Resolve a free-form bike name to a (bike_id, suggestions) pair.

    bike_id is None if no match scored >= MATCH_THRESHOLD.
    suggestions is the top-5 best candidates regardless (for chips UI).
    """
    if not name or db is None:
        return None, []

    raw = name.strip()
    stripped, mfr = _strip_manufacturer_prefix(raw)

    # Build a candidate pool. Try multiple search strategies and merge.
    candidates: dict[int, dict[str, Any]] = {}

    # Strategy 1: raw query as substring (covers exact catalog matches).
    try:
        rows = db.bikes.search(name_contains=raw, limit=30) or []
    except Exception:
        rows = []
    for r in rows:
        candidates[r["id"]] = r

    # Strategy 2: stripped query (handles "Suzuki Hayabusa" → search "Hayabusa")
    if stripped and stripped != raw.lower():
        try:
            rows = db.bikes.search(name_contains=stripped, limit=30) or []
        except Exception:
            rows = []
        for r in rows:
            candidates[r["id"]] = r

    # Strategy 3: manufacturer-filtered search (if we identified one). Search
    # by the catalog name ("re" -> "royal%enfield"; a bare LIKE '%re%' hit
    # every brand containing "re"), with '%' for the separators the
    # normaliser removed ("harley%davidson" matches "Harley-Davidson").
    if mfr:
        mfr_like = _canonical_manufacturer(mfr).replace(" ", "%")
        try:
            rows = db.bikes.search(manufacturer=mfr_like, limit=500) or []
        except Exception:
            rows = []
        # Only keep rows whose model_name contains at least one significant
        # query token, or matches it with the separators removed ("ZX10R" vs
        # "Ninja ZX-10R"); otherwise this floods with the entire
        # manufacturer's catalogue.
        sig_tokens = {t for t in _tokenize(stripped or raw) if len(t) >= 2}
        for r in rows:
            model = r.get("model_name", "") or ""
            if sig_tokens & _tokenize(model) or _compact_match(stripped or raw, model):
                candidates[r["id"]] = r

    # Strategy 4: token-by-token fallback if pool is still empty.
    if not candidates:
        for tok in sorted(_tokenize(raw), key=len, reverse=True):
            if len(tok) < 3:
                continue
            try:
                rows = db.bikes.search(name_contains=tok, limit=30) or []
            except Exception:
                rows = []
            for r in rows:
                candidates[r["id"]] = r
            if len(candidates) >= 30:
                break

    def _score_all(rows: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
        out = [
            (
                _score_candidate(
                    raw, r.get("manufacturer_name") or "", r.get("model_name") or ""
                ),
                r,
            )
            for r in rows
        ]
        out.sort(key=lambda x: (-x[0], x[1].get("year_from") or 0))
        return out

    scored = _score_all(list(candidates.values()))

    # Strategy 5: the SQL LIKE strategies cannot see a separator-free spelling
    # ("ZX10R", "GSX-R1000 K5") or a brand typed by its alias. When nothing in
    # the pool clears the bar, score the whole catalog (~550 rows, a few ms).
    if not scored or scored[0][0] < MATCH_THRESHOLD:
        try:
            everything = db.bikes.search(limit=100_000) or []
        except Exception:
            everything = []
        if everything:
            for r in everything:
                candidates.setdefault(r["id"], r)
            full = _score_all(list(candidates.values()))
            if full and full[0][0] >= MATCH_THRESHOLD:
                scored = full

    if not scored:
        return None, []

    suggestions = [r for _, r in scored[:SUGGESTIONS_LIMIT]]
    best_score, best_row = scored[0]

    if best_score >= MATCH_THRESHOLD:
        return best_row["id"], suggestions
    return None, suggestions


def resolve_venue(name: str | None, db: MotoQuantDB) -> int | None:
    """Resolve a venue name to a venue_id. Falls back to None on miss."""
    if not name or db is None:
        return None
    try:
        v = db.venues.get_by_name(name)
        if v:
            return v["id"]
    except Exception:
        # Fall through to the substring search below; resolver returns
        # None on total miss per the docstring contract.
        pass
    # Try a substring-based search in the venues table.
    try:
        rows = db.venues.list_all() or []
    except Exception:
        return None
    n_norm = _normalize(name)
    n_tokens = _tokenize(name)
    best = None
    best_score = 0
    for r in rows:
        # Compare against the venue's display fields.
        for field_name in ("name", "short_name", "city"):
            v_norm = _normalize(r.get(field_name) or "")
            if not v_norm:
                continue
            if n_norm in v_norm or v_norm in n_norm:
                # Containment → strong match.
                return r["id"]
            v_tokens = _tokenize(r.get(field_name) or "")
            if not v_tokens or not n_tokens:
                continue
            common = n_tokens & v_tokens
            if common:
                s = int(100 * len(common) / len(n_tokens | v_tokens))
                if s > best_score:
                    best_score = s
                    best = r["id"]
    if best_score >= 60:
        return best
    return None


# ───────────────────────────────────────────────────────────────────
# Archetype resolution (modded builds layered onto an OEM base bike)
# ───────────────────────────────────────────────────────────────────

# Normalised aliases → canonical archetype name in bike_archetypes.name.
# Keys are lower-cased token strings; values are exact DB names.
_ARCHETYPE_ALIASES: dict[str, str] = {
    "tts hayabusa": "TTS Stage 2 Turbo Hayabusa",
    "tts stage 2 hayabusa": "TTS Stage 2 Turbo Hayabusa",
    "tts turbo hayabusa": "TTS Stage 2 Turbo Hayabusa",
    "stage 2 hayabusa": "TTS Stage 2 Turbo Hayabusa",
    "velocity hayabusa": "Velocity Racing 5-sec Turbo Hayabusa",
    "velocity 5 sec hayabusa": "Velocity Racing 5-sec Turbo Hayabusa",
    "velocity 5sec hayabusa": "Velocity Racing 5-sec Turbo Hayabusa",
    "5 second hayabusa": "Velocity Racing 5-sec Turbo Hayabusa",
    "5sec hayabusa": "Velocity Racing 5-sec Turbo Hayabusa",
    "bonneville h2": "Bonneville H2 Carbon Track Edition",
    "bonneville h2 carbon": "Bonneville H2 Carbon Track Edition",
    "salt flat h2": "Bonneville H2 Carbon Track Edition",
    "carbon h2": "Bonneville H2 Carbon Track Edition",
    "schnitz hayabusa": "Schnitz Nitrous Hayabusa",
    "schnitz nitrous hayabusa": "Schnitz Nitrous Hayabusa",
    "nitrous hayabusa": "Schnitz Nitrous Hayabusa",
    "nos hayabusa": "Schnitz Nitrous Hayabusa",
    "ron ayers hayabusa": "Ron Ayers RAW Turbo Hayabusa",
    "ron ayers raw hayabusa": "Ron Ayers RAW Turbo Hayabusa",
    "raw racing hayabusa": "Ron Ayers RAW Turbo Hayabusa",
    "raw hayabusa": "Ron Ayers RAW Turbo Hayabusa",
}


def resolve_archetype(name: str, db: MotoQuantDB) -> tuple[int | None, int | None]:
    """Resolve a free-text archetype name → (archetype_id, base_bike_model_id).

    Returns (None, None) if no match. Tries:
      1. Exact (case-insensitive) match against bike_archetypes.name.
      2. Alias map for common short forms ("TTS Hayabusa", "Velocity 5-sec").
      3. Token-set Jaccard fuzzy match (>= 50% overlap).
    """
    if not name:
        return None, None

    try:
        rows = db._conn.execute(
            "SELECT id, name, base_bike_model_id FROM bike_archetypes ORDER BY id"
        ).fetchall()
    except Exception:
        return None, None
    if not rows:
        return None, None

    # 1. Exact (case-insensitive) name match.
    n_lower = name.strip().lower()
    for r in rows:
        if (r["name"] or "").strip().lower() == n_lower:
            return r["id"], r["base_bike_model_id"]

    # 2. Alias map.
    n_norm = _normalize(name)
    if n_norm in _ARCHETYPE_ALIASES:
        canon = _ARCHETYPE_ALIASES[n_norm]
        for r in rows:
            if (r["name"] or "").strip().lower() == canon.lower():
                return r["id"], r["base_bike_model_id"]

    # 3. Token-set Jaccard fuzzy match.
    n_tokens = _tokenize(name)
    if not n_tokens:
        return None, None

    best = None
    best_score = 0
    for r in rows:
        cand_tokens = _tokenize(r["name"] or "")
        if not cand_tokens:
            continue
        common = n_tokens & cand_tokens
        if not common:
            continue
        score = int(100 * len(common) / len(n_tokens | cand_tokens))
        if score > best_score:
            best_score = score
            best = r

    if best is not None and best_score >= 50:
        return best["id"], best["base_bike_model_id"]
    return None, None
