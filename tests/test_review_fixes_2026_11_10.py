"""Regression tests for the 10 November 2026 review of the release branch.

* The public chat writes nothing to the catalog database: an estimate for
  a bike missing from the catalog is not logged as a suggestion.
* A cached live-weather reading keeps the time it was fetched, so the site
  never labels a ten-minute-old reading as fresh.
* No tracked file carries a path from a contributor's machine.
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


_OWM_FIELDS = {
    "location_name": "Lonavala",
    "country": "IN",
    "latitude": 18.75,
    "longitude": 73.4,
    "altitude_m": 622.0,
    "temperature_c": 25.0,
    "humidity_pct": 50.0,
    "pressure_hpa": 1010.0,
    "pressure_kpa": 101.0,
    "wind_speed_ms": 0.0,
    "wind_direction_deg": 0.0,
    "air_density_kgm3": 1.1,
    "density_altitude_ft": 3000.0,
    "density_altitude_m": 914.0,
    "power_correction_factor": 0.95,
}


def test_cached_weather_keeps_its_fetch_time(monkeypatch, tmp_path):
    """Through the route: the second resolve is served from the cache and
    reports the time of the real fetch, not the time it was served."""
    import sqlite3
    import time

    import motoquant.api as api

    copy = tmp_path / "mq.db"
    shutil.copy(_REPO_DB, copy)
    conn = sqlite3.connect(str(copy), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    monkeypatch.setattr(api, "_get_db", lambda: conn)
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test-key-not-real")
    calls = []

    def fake(*, location, lat, lon, altitude_m):
        calls.append(location)
        return dict(_OWM_FIELDS)

    monkeypatch.setattr(api, "_fetch_owm_uncached", fake)
    with api._owm_cache_lock:
        api._owm_cache.clear()
    req = api.VenueResolveRequest(location="Lonavala", lat=18.75, lon=73.4)
    first = api.resolve_venue(req)
    time.sleep(0.01)
    second = api.resolve_venue(req)
    with api._owm_cache_lock:
        api._owm_cache.clear()
    conn.close()
    assert first["source"] == second["source"] == "openweathermap"
    assert len(calls) == 1  # served from the cache
    assert first["fetched_at"] == second["fetched_at"]


def test_no_local_paths_in_tracked_files():
    """The public tree must not carry paths from a contributor's machine."""
    import subprocess

    root = _REPO_DB.parent
    files = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.split()
    needles = ("/tmp/" + "claude", "/home/" + "user/")
    hits = []
    for name in files:
        if name.endswith((".db", ".npz", ".png", ".ico", ".wasm", ".woff2", ".lock")):
            continue
        try:
            text = (root / name).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        hits += [name for n in needles if n in text]
    assert not hits, sorted(set(hits))
