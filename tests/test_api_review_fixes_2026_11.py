"""Regression tests for the November 2026 review of the combined API.

Each test drives the production route (FastAPI TestClient against a copy of
the shipped catalog) and fails if its fix is reverted.

* The quick-sim stock baseline runs in the conditions the request resolved;
  a named place (live weather) is never answered from the baseline cache.
* Weather lookups are cached for ten minutes; failures are not.
* Parts apply in one canonical order, so click order cannot change a time.
* A seeded venue named by ``location`` races on its own surface.
* An air temperature without a track temperature puts the track 7 °C above it.
* A front tyre cannot be fitted at the rear (and the reverse).
* A job whose result alone exceeds the byte budget is still pollable.
* CLI: unknown venue ids and unknown Sobol parameters are errors.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

_REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"

_TMP_DIR = None
_PRIOR_DB_ENV = None
_PRIOR_OWM_KEY = None
api = None
client = None


def setUpModule():
    global _TMP_DIR, _PRIOR_DB_ENV, _PRIOR_OWM_KEY, api, client
    _PRIOR_OWM_KEY = os.environ.pop("OPENWEATHERMAP_API_KEY", None)
    _TMP_DIR = tempfile.mkdtemp(prefix="mq_api_review_")
    shutil.copyfile(_REPO_DB, os.path.join(_TMP_DIR, "motoquant.db"))
    _PRIOR_DB_ENV = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = os.path.join(_TMP_DIR, "motoquant.db")
    import motoquant.api as _api

    api = _api
    _close_api_db()
    client = TestClient(api.app)


def tearDownModule():
    _close_api_db()
    if _PRIOR_DB_ENV is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_DB_ENV
    if _PRIOR_OWM_KEY is not None:
        os.environ["OPENWEATHERMAP_API_KEY"] = _PRIOR_OWM_KEY
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


def _close_api_db():
    if getattr(api, "_db_conn", None) is not None:
        try:
            api._db_conn.close()
        except Exception:
            pass
        api._db_conn = None


def _post(path, body):
    from motoquant import ratelimit

    ratelimit.reset()
    return client.post(path, json=body)


# Part 48 adds +10 hp; part 354 multiplies power by 1.032. They do not commute.
_ECU, _FILTER = 48, 354
_PLACE = {"bike_id": 3, "location": "Lonavala", "lat": 18.75, "lon": 73.4}


class _FakeWeather:
    def __init__(self):
        self.calls = 0
        self.t, self.p, self.h = 15.0, 1030.0, 30.0
        self.fail = False

    def __call__(self, *, location, lat, lon, altitude_m):
        self.calls += 1
        if self.fail:
            return {"_error": "owm_error: HTTP 503"}
        return {
            "location_name": location or "X",
            "country": "IN",
            "latitude": lat,
            "longitude": lon,
            "altitude_m": altitude_m or 0.0,
            "temperature_c": self.t,
            "humidity_pct": self.h,
            "pressure_hpa": self.p,
            "pressure_kpa": self.p / 10,
            "wind_speed_ms": 0.0,
            "wind_direction_deg": 0.0,
            "air_density_kgm3": 1.2,
            "density_altitude_ft": 0.0,
            "density_altitude_m": 0.0,
            "power_correction_factor": 1.0,
        }


@pytest.fixture
def weather(monkeypatch):
    fake = _FakeWeather()
    monkeypatch.setattr(api, "_fetch_owm_uncached", fake)
    # resolve_venue only reaches the provider when a key is configured.
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test-key-not-real")
    # Open the catalog connection first: its freshness token is part of the
    # baseline-cache key, and a cold first request would key differently.
    _post("/api/simulate/quick", {"bike_id": 3})
    with api._owm_cache_lock:
        api._owm_cache.clear()
    api._stock_cache.clear()
    return fake


def test_place_baseline_follows_todays_weather(weather):
    first = _post("/api/simulate/quick", {**_PLACE, "part_ids": [_ECU]}).json()
    assert first["stock_et_s"] is not None
    # The weather changes (expire the lookup cache as ten minutes would).
    weather.t, weather.p, weather.h = 42.0, 985.0, 80.0
    with api._owm_cache_lock:
        api._owm_cache.clear()
    second = _post("/api/simulate/quick", {**_PLACE, "part_ids": [_ECU]}).json()
    stock_now = _post("/api/simulate/quick", dict(_PLACE)).json()
    assert second["environment"]["ambient_temp_c"] == 42.0
    assert second["stock_et_s"] == stock_now["et_quarter_s"]
    assert second["stock_et_s"] != first["stock_et_s"]


def test_quick_sim_with_parts_resolves_weather_once(weather, monkeypatch):
    # With the lookup cache off, the stock baseline must still reuse the
    # request's own resolved conditions rather than resolving them again.
    monkeypatch.setattr(api, "_OWM_CACHE_TTL_S", 0.0)
    r = _post("/api/simulate/quick", {**_PLACE, "part_ids": [_ECU]}).json()
    assert r["stock_et_s"] is not None
    assert weather.calls == 1


def test_weather_lookups_are_cached_but_failures_are_not(weather):
    _post("/api/simulate/quick", dict(_PLACE))
    _post("/api/simulate/quick", dict(_PLACE))
    assert weather.calls == 1
    with api._owm_cache_lock:
        api._owm_cache.clear()
    weather.fail = True
    _post("/api/simulate/quick", dict(_PLACE))
    _post("/api/simulate/quick", dict(_PLACE))
    assert weather.calls == 3


def test_weather_cache_entries_expire(weather, monkeypatch):
    _post("/api/simulate/quick", dict(_PLACE))
    real = time.monotonic
    monkeypatch.setattr(
        api._time, "monotonic", lambda: real() + api._OWM_CACHE_TTL_S + 1
    )
    _post("/api/simulate/quick", dict(_PLACE))
    assert weather.calls == 2


def test_part_order_does_not_change_the_time():
    a = _post("/api/simulate/quick", {"bike_id": 3, "part_ids": [_ECU, _FILTER]})
    b = _post("/api/simulate/quick", {"bike_id": 3, "part_ids": [_FILTER, _ECU]})
    assert a.status_code == b.status_code == 200
    assert {p["id"] for p in a.json()["parts_applied"]} == {_ECU, _FILTER}
    assert a.json()["et_quarter_s"] == b.json()["et_quarter_s"]


def test_venue_named_by_location_uses_its_surface():
    by_id = _post(
        "/api/simulate/quick",
        {"bike_id": 3, "venue_id": 6, "ambient_temp_c": 20, "humidity_pct": 50},
    ).json()
    by_name = _post(
        "/api/simulate/quick",
        {
            "bike_id": 3,
            "location": "Santa Pod Raceway (UK)",
            "ambient_temp_c": 20,
            "humidity_pct": 50,
        },
    ).json()
    assert by_id["environment"]["track_surface"] == "concrete"
    assert by_name["environment"]["track_surface"] == "concrete"


def test_air_temperature_alone_sets_the_track_seven_degrees_warmer():
    r = _post("/api/simulate/quick", {"bike_id": 3, "ambient_temp_c": 40}).json()
    assert r["environment"]["track_temp_c"] == pytest.approx(47.0)
    r = _post(
        "/api/simulate/quick",
        {"bike_id": 3, "ambient_temp_c": 40, "track_temp_c": 35},
    ).json()
    assert r["environment"]["track_temp_c"] == pytest.approx(35.0)


def test_apply_conditions_sets_the_track_seven_degrees_warmer():
    # The autotune / optimizer routes call _apply_conditions directly.
    from motoquant.defaults import gsxr1000_k5

    cfg = gsxr1000_k5()
    api._apply_conditions(cfg, api.ConditionsRequest(ambient_temp_c=40))
    assert cfg.environment.track_temp_c == pytest.approx(47.0)


def _tyre_ids():
    c = sqlite3.connect(f"file:{os.environ['MOTOQUANT_DB']}?mode=ro", uri=True)
    try:
        front = c.execute(
            "SELECT id FROM tire_models WHERE position='front' LIMIT 1"
        ).fetchone()[0]
        rear = c.execute(
            "SELECT id FROM tire_models WHERE position='rear' LIMIT 1"
        ).fetchone()[0]
    finally:
        c.close()
    return front, rear


def test_tyre_must_match_its_wheel():
    front, rear = _tyre_ids()
    ok = _post(
        "/api/simulate/quick",
        {"bike_id": 3, "front_tire_id": front, "rear_tire_id": rear},
    )
    assert ok.status_code == 200
    bad_rear = _post("/api/simulate/quick", {"bike_id": 3, "rear_tire_id": front})
    assert bad_rear.status_code == 422
    assert "front tyre" in bad_rear.json()["detail"]
    bad_front = _post("/api/simulate/quick", {"bike_id": 3, "front_tire_id": rear})
    assert bad_front.status_code == 422
    # Job routes answer at submit time.
    job = _post("/api/jobs/simulate", {"bike_id": 3, "rear_tire_id": front})
    assert job.status_code == 422


def test_oversized_result_is_still_pollable(monkeypatch):
    from motoquant import jobs

    monkeypatch.setattr(jobs, "MAX_RESULT_BYTES_TOTAL", 1)
    job = jobs.create_job("test", lambda progress: {"payload": "x" * 5000})
    for _ in range(200):
        j = jobs.get_job(job.id)
        if j is not None and j.status in ("done", "error"):
            break
        time.sleep(0.01)
    j = jobs.get_job(job.id)
    assert j is not None and j.status == "done"


def test_cli_unknown_venue_is_an_error(tmp_path):
    from motoquant import run

    db = tmp_path / "cli.db"
    shutil.copyfile(_REPO_DB, db)
    with pytest.raises(SystemExit) as exc:
        run.main(["--db", str(db), "sim", "--bike-id", "3", "--venue-id", "99999"])
    assert exc.value.code == 1


def test_cli_unknown_sobol_parameter_is_an_error(tmp_path, capsys):
    from motoquant import run

    db = tmp_path / "cli.db"
    shutil.copyfile(_REPO_DB, db)
    code = run.main(["--db", str(db), "analysis", "sobol", "--params", "nonsense"])
    assert code == 2
    assert "unknown parameter" in capsys.readouterr().out
