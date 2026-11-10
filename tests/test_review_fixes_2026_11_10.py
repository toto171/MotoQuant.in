"""Regression tests for the 10 November 2026 review of the release branch.

* The public chat writes nothing to the catalog database: an estimate for
  a bike missing from the catalog is not logged as a suggestion.
* A cached live-weather reading keeps the time it was fetched, so the site
  never labels a ten-minute-old reading as fresh.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from motoquant.database import MotoQuantDB

_REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"

SPEC = {
    "manufacturer": "Testmoto",
    "model_name": "Review 600",
    "displacement_cc": 599,
    "peak_power_hp": 118,
    "peak_power_rpm": 13000,
    "peak_torque_nm": 66,
    "peak_torque_rpm": 11000,
    "dry_mass_kg": 167,
    "cylinders": 4,
    "category": "sport",
}


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "mq.db"
    shutil.copy(_REPO_DB, path)
    d = MotoQuantDB(str(path))
    yield d
    d.close()


def test_chat_estimate_does_not_log_a_suggestion(db):
    from motoquant.llm.agent import (
        AgentChatResult,
        AgentContext,
        _exec_simulate_estimated,
    )

    before = db.conn.execute("SELECT COUNT(*) FROM bike_suggestions").fetchone()[0]
    ctx = AgentContext(db=db, result=AgentChatResult(raw_query="Review 600?"))
    out = _exec_simulate_estimated(ctx, {"spec": dict(SPEC)})
    assert "error" not in out, out
    assert out["estimated"] is True
    after = db.conn.execute("SELECT COUNT(*) FROM bike_suggestions").fetchone()[0]
    assert after == before


def test_cached_weather_keeps_its_fetch_time(monkeypatch):
    import time

    import motoquant.api as api

    calls = []

    def fake(*, location, lat, lon, altitude_m):
        calls.append(location)
        return {"temperature_c": 25.0, "humidity_pct": 50.0}

    monkeypatch.setattr(api, "_fetch_owm_uncached", fake)
    with api._owm_cache_lock:
        api._owm_cache.clear()
    kw = {"location": "Lonavala", "lat": 18.75, "lon": 73.4, "altitude_m": None}
    first = api._fetch_owm_for_location(**kw)
    time.sleep(0.01)
    second = api._fetch_owm_for_location(**kw)
    assert len(calls) == 1  # served from the cache
    assert first["fetched_at"] == second["fetched_at"]
    with api._owm_cache_lock:
        api._owm_cache.clear()
