"""Regression tests: the chat agent's bike resolver missed common catalog
queries (audit 2026-10-23, motoquant/llm/resolver.py).

* "RE Classic 350" -> None: "RE" was stripped for the SQL search, but scoring
  compared the raw query against the "royal enfield" tokens (Jaccard 40 < 60).
* "Kawasaki ZX10R" / "BMW S1000RR" -> None with zero candidates: nothing
  matched a separator-free spelling against "Ninja ZX-10R" / "S 1000 RR".
* "GSX-R1000 K5" -> None although the catalog holds "GSX-R 1000 K5/K6" (the
  K5 reference bike).

When the resolver misses, the agent reports "bike not found" or runs an
LLM-recalled estimate instead of the curated config, so these go through the
real ``resolve_bike`` against a copy of the shipped catalog.

Review follow-up (2026-10-24): the whole-catalog fallback added for those
fixes made a BRAND-ONLY query resolve confidently. Every model of the brand
token-contains "honda", so the oldest, shortest-named one won ("honda" ->
NS400R, "ktm" -> 1190 RC8 R, "bmw" -> K1300S), and the chat simulated that
bike without saying so instead of asking which one was meant. "re" (Royal
Enfield) even matched a Honda "Fireblade" through the "re" inside it.
"""

from __future__ import annotations

import os

import pytest

from motoquant.llm import resolver
from motoquant.llm.resolver import (
    _score_candidate,
    _strip_manufacturer_prefix,
    resolve_bike,
)
from tests._helpers import live_db_copy

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")


@pytest.fixture(scope="module")
def db():
    if not os.path.exists(_DB_PATH):
        pytest.skip("motoquant.db not found")
    return live_db_copy(_DB_PATH)


def _resolved_name(db, query):
    bike_id, _ = resolve_bike(query, db)
    assert bike_id is not None, f"{query!r} did not resolve"
    row = db._conn.execute(
        "SELECT m.name AS mfr, bm.model_name FROM bike_models bm "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id WHERE bm.id = ?",
        (bike_id,),
    ).fetchone()
    return f"{row['mfr']} {row['model_name']}".lower()


@pytest.mark.parametrize(
    "query, expected",
    [
        ("RE Classic 350", "royal enfield classic 350"),
        ("Kawasaki ZX10R", "kawasaki ninja zx-10r"),
        ("BMW S1000RR", "bmw s 1000 rr"),
        ("GSX-R1000 K5", "suzuki gsx-r 1000 k5/k6"),
        ("zx10r", "ninja zx-10r"),
        ("s1000rr", "s 1000 rr"),
        ("gsxr1000", "suzuki gsx-r 1000"),
        # Dropped 1-char token: the RR-R must beat the plain CBR1000RR.
        ("Honda CBR1000RR-R", "cbr1000rr-r"),
    ],
)
def test_audit_queries_resolve(db, query, expected):
    assert expected in _resolved_name(db, query)


@pytest.mark.parametrize(
    "query, expected",
    [
        ("Suzuki Hayabusa", "hayabusa"),
        ("KTM RC 390", "rc 390"),
        ("Yamaha YZF-R15 V4", "r15 v4"),
        ("R1", "yzf-r1 "),
        ("R15", "yzf-r15"),
        ("Royal Enfield Classic 350", "classic 350"),
        ("Ninja ZX-10R", "ninja zx-10r"),
        ("GSX-R 1000 K5", "gsx-r 1000 k5"),
    ],
)
def test_existing_queries_unchanged(db, query, expected):
    assert expected in _resolved_name(db, query)


def test_garbage_still_returns_none(db):
    bike_id, _ = resolve_bike("zzzzzzzzz garbage 999", db)
    assert bike_id is None


def test_compact_match_respects_token_boundaries():
    # "R1" must not ride inside "R15": windows are whole-token runs only.
    assert "r1" not in resolver._compact_windows(["yzf", "r15", "v4"])
    assert resolver._compact_score("R1", "Yamaha YZF-R15 V4") == 0
    assert _score_candidate("ZX10R", "Kawasaki", "Ninja ZX-10R (2004-2005)") >= 85


def test_alias_scoring_uses_the_real_manufacturer():
    assert _score_candidate("RE Classic 350", "Royal Enfield", "Classic 350") >= 85
    # The alias only helps when it IS the candidate's manufacturer.
    assert _score_candidate("RE Classic 350", "Jawa", "Classic 350") < 85


def test_hyphenated_brand_prefix_is_stripped():
    assert _strip_manufacturer_prefix("Harley-Davidson Fat Bob") == (
        "fat bob",
        "harley davidson",
    )


# ── Brand-only queries must not pick a model ───────────────────────────────

_BRAND_ONLY = [
    ("honda", "honda"),
    ("ktm", "ktm"),
    ("harley", "harley-davidson"),
    ("Harley Davidson", "harley-davidson"),
    ("bmw", "bmw"),
    ("suzuki", "suzuki"),
    ("royal enfield", "royal enfield"),
    ("re", None),  # matched a Honda "Fireblade" before
    ("jawa", "jawa"),  # three Jawa models in the catalog
    ("yamaha r", "yamaha"),  # a lone 1-char token names no model
    ("Royal", "royal enfield"),  # brand words that are not a known prefix
    ("Davidson", "harley-davidson"),
]


@pytest.mark.parametrize("query, brand", _BRAND_ONLY)
def test_brand_only_query_does_not_resolve(db, query, brand):
    bike_id, suggestions = resolve_bike(query, db)
    assert bike_id is None, f"{query!r} guessed bike {bike_id}"
    # The chips / the agent's candidate list still get the brand's models,
    # so the caller can ask which one was meant.
    assert suggestions, query
    if brand is not None:
        mfrs = {str(s.get("manufacturer_name") or "").lower() for s in suggestions}
        assert mfrs == {brand}, (query, mfrs)


@pytest.mark.parametrize(
    "query, expected",
    [
        # A remainder of 2+ characters with the separators removed is a model.
        ("Yamaha R 1", "yzf-r1 "),
        ("R 1", "yzf-r1 "),
        ("Jawa 42", "jawa 42"),
        ("Jawa Perak", "perak"),
        ("Kawasaki H2", "h2"),
        ("BMW R 18", "r 18"),
        ("HD Fat Bob", "fat bob"),
        ("Indian Scout", "scout"),
    ],
)
def test_brand_plus_model_still_resolves(db, query, expected):
    assert expected in _resolved_name(db, query)


def test_guard_changes_no_model_bearing_catalog_query(db, monkeypatch):
    """Over every '<brand> <model>' and '<model>' spelling in the catalog,
    the brand-only guard never changes which bike resolves."""
    rows = db._conn.execute(
        "SELECT m.name AS mfr, bm.model_name FROM bike_models bm "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id"
    ).fetchall()
    queries = set()
    for r in rows:
        model = resolver._YEAR_RANGE_RE.sub(" ", r["model_name"]).strip()
        queries.update({f"{r['mfr']} {model}", model})
    guarded = {q: resolve_bike(q, db)[0] for q in sorted(queries)}
    monkeypatch.setattr(resolver, "_names_only_a_manufacturer", lambda *a: False)
    changed = [q for q in sorted(queries) if resolve_bike(q, db)[0] != guarded[q]]
    assert not changed, changed[:10]


def test_chat_parse_path_leaves_bike_unset_for_a_brand(db):
    """The production chat path: the LLM extracted only a brand, so
    parsed.bike_id must stay None (the runner then answers bike_not_found
    with suggestions) rather than silently pinning an arbitrary model."""
    from motoquant.llm.parse_query import ParsedSimRequest, _resolve_against_db

    for brand in ("Honda", "KTM", "Harley", "BMW"):
        parsed = ParsedSimRequest(raw_query=f"simulate my {brand}", bike_name=brand)
        _resolve_against_db(parsed, db)
        assert parsed.bike_id is None, (brand, parsed.bike_id)

    parsed = ParsedSimRequest(raw_query="simulate my RC 390", bike_name="KTM RC 390")
    _resolve_against_db(parsed, db)
    assert parsed.bike_id is not None


def test_agent_search_bikes_reports_no_best_match_for_a_brand(db):
    from motoquant.llm.agent import AgentChatResult, AgentContext, _exec_search_bikes

    ctx = AgentContext(db=db, result=AgentChatResult(raw_query=""))
    out = _exec_search_bikes(ctx, {"query": "Honda"})
    assert "best_match" not in out, out.get("best_match")
    assert out["candidates"]
    assert all(c["manufacturer"] == "Honda" for c in out["candidates"])

    out = _exec_search_bikes(ctx, {"query": "Honda CBR1000RR-R"})
    assert "cbr1000rr-r" in out["best_match"]["model"].lower()
