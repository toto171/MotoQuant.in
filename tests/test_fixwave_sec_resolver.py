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
