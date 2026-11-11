"""Live weather comes from the visitor's browser (2026-11-11).

Open-Meteo limits its free tier per IP address, and the API on a free Render
service shares its outbound address with many other apps, so the API's own
lookups failed with HTTP 429 and the site could not show live weather for any
place that is not a known track. The website now fetches the reading in the
browser (``web/lib/openMeteo.js``) and the API only does the atmosphere maths:

* ``/api/venues/resolve`` takes the reading as ``observed`` and makes no
  outbound call; ``seeded_only`` matches a known track or answers 404, also
  without a call.
* A simulation that carries altitude, temperature, humidity and pressure is
  not looked up again (the site now sends all four for a searched place).

The tests run through HTTP on a copy of the catalog. ``requests.get`` is
replaced so that any outbound call is recorded and fails, with the Open-Meteo
fallback switched ON: if one of these paths starts calling out again, the
test sees it without touching the network.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")

PUNE = {"lat": 18.52, "lon": 73.86, "altitude_m": 554.0}
PUNE_READING = {
    "temperature_c": 25.9,
    "humidity_pct": 48.0,
    "pressure_msl_hpa": 1013.8,
    "wind_speed_ms": 2.1,
    "wind_direction_deg": 270.0,
    "country": "IN",
}
# The four values the site sends with a searched place.
PUNE_CONDITIONS = {
    "altitude_m": 554.0,
    "ambient_temp_c": 26.0,
    "humidity_pct": 48.0,
    "pressure_hpa": 1013.8,
}


@pytest.fixture(scope="module")
def api_client():
    tmp = tempfile.NamedTemporaryFile(prefix="mq_weather_", suffix=".db", delete=False)
    tmp.close()
    shutil.copyfile(_REPO_DB, tmp.name)
    prior = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = tmp.name
    import motoquant.api as api_mod

    api_mod._db_conn = None
    api_mod._db_facade = None
    try:
        yield TestClient(api_mod.app), api_mod
    finally:
        # Close what the app opened on the copy (Windows cannot delete an
        # open file), then forget it so the next module starts fresh.
        for handle in (api_mod._db_facade, api_mod._db_conn):
            close = getattr(handle, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        api_mod._db_conn = None
        api_mod._db_facade = None
        if prior is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = prior
        try:
            os.unlink(tmp.name)
        except PermissionError:
            pass  # still held on Windows; the temp folder is cleaned later


@pytest.fixture()
def outbound(monkeypatch):
    """Record (and fail) every outbound HTTP GET; the Open-Meteo fallback is on."""
    import requests

    calls = []

    def refuse(url, *args, **kwargs):
        calls.append(url)
        raise AssertionError(f"unexpected outbound call to {url}")

    monkeypatch.setattr(requests, "get", refuse)
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    monkeypatch.setenv("MOTOQUANT_OPEN_METEO", "1")
    return calls


# ─── /api/venues/resolve ─────────────────────────────────────────────────


def test_a_browser_reading_is_resolved_without_calling_out(api_client, outbound):
    client, api = api_client
    r = client.post(
        "/api/venues/resolve",
        json={"location": "Pune, IN", **PUNE, "observed": PUNE_READING},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert outbound == []
    assert body["source"] == "open-meteo"
    assert body["matched_venue_id"] is None
    assert body["country"] == "IN"
    assert body["latitude"] == 18.52 and body["longitude"] == 73.86
    assert body["altitude_m"] == 554.0
    assert body["temperature_c"] == 25.9 and body["pressure_hpa"] == 1013.8
    assert body["fetched_at"]
    # The air is computed exactly as for the server's own lookup of the same
    # reading: one formula, whoever fetched the numbers.
    same = api._live_conditions(
        location_name="Pune, IN",
        country="IN",
        lat=18.52,
        lon=73.86,
        altitude_m=554.0,
        temp_c=25.9,
        humidity=48.0,
        pressure_hpa=1013.8,
        wind_ms=2.1,
        wind_deg=270.0,
        provider="open-meteo",
    )
    for key in ("air_density_kgm3", "density_altitude_m", "power_correction_factor"):
        assert body[key] == same[key], key


def test_a_reading_needs_coordinates(api_client, outbound):
    client, _ = api_client
    r = client.post(
        "/api/venues/resolve", json={"location": "Pune, IN", "observed": PUNE_READING}
    )
    assert r.status_code == 422, r.text
    assert outbound == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("humidity_pct", 150.0),
        ("pressure_msl_hpa", 500.0),
        ("temperature_c", 95.0),
        ("wind_direction_deg", 400.0),
        ("country", "india"),
    ],
)
def test_a_reading_is_bounded(api_client, outbound, field, value):
    client, _ = api_client
    reading = {**PUNE_READING, field: value}
    r = client.post("/api/venues/resolve", json={**PUNE, "observed": reading})
    assert r.status_code == 422, (field, r.text)
    assert outbound == []


def test_seeded_only_matches_a_known_track_without_calling_out(api_client, outbound):
    client, _ = api_client
    r = client.post(
        "/api/venues/resolve", json={"location": "mmrt", "seeded_only": True}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "seeded_venue"
    assert body["matched_venue_id"] is not None
    assert "MMRT" in body["venue_name"]
    assert outbound == []


def test_seeded_only_is_a_404_for_any_other_place(api_client, outbound):
    client, _ = api_client
    r = client.post(
        "/api/venues/resolve", json={"location": "Pune, IN", "seeded_only": True}
    )
    assert r.status_code == 404, r.text
    assert outbound == []


def test_a_known_track_still_wins_over_a_reading(api_client, outbound):
    client, _ = api_client
    r = client.post(
        "/api/venues/resolve",
        json={"location": "mmrt", **PUNE, "observed": PUNE_READING},
    )
    assert r.status_code == 200, r.text
    assert r.json()["source"] == "seeded_venue"
    assert outbound == []


# ─── simulations that already carry the conditions ───────────────────────


def _quick(client, **extra):
    r = client.post("/api/simulate/quick", json={"bike_id": 81, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_a_run_with_all_four_values_is_not_looked_up(api_client, outbound):
    client, _ = api_client
    named = _quick(client, location="Pune, IN", lat=18.52, lon=73.86, **PUNE_CONDITIONS)
    assert outbound == []
    # The place's name only labels the run: the physics is the same as for
    # the bare values.
    bare = _quick(client, **PUNE_CONDITIONS)
    assert named["et_quarter_s"] == bare["et_quarter_s"]
    env = named["environment"]
    assert env["altitude_m"] == 554.0
    assert env["ambient_temp_c"] == 26.0
    assert env["humidity_pct"] == 48.0
    assert env["pressure_hpa"] == 1013.8


def test_a_known_track_named_in_a_run_keeps_its_surface(api_client, outbound):
    """The local seeded match still names the run and sets the surface (salt
    here), exactly as the full lookup did before."""
    client, _ = api_client
    env = _quick(client, location="bonneville", **PUNE_CONDITIONS)["environment"]
    assert outbound == []
    assert "Bonneville" in env["name"]
    assert env["track_surface"] == "salt"
    assert env["altitude_m"] == 554.0  # the explicit value still wins


def test_a_run_missing_a_value_still_looks_the_place_up(api_client, monkeypatch):
    """Clients that send only part of the conditions keep the old behaviour."""
    import requests

    client, _ = api_client
    calls = []

    class _Resp:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        if "geocoding" in url:
            return _Resp(
                {
                    "results": [
                        {
                            "name": "Pune",
                            "latitude": 18.52,
                            "longitude": 73.86,
                            "elevation": 554.0,
                            "country_code": "IN",
                        }
                    ]
                }
            )
        return _Resp(
            {
                "elevation": 562.0,
                "current": {
                    "temperature_2m": 25.9,
                    "relative_humidity_2m": 48,
                    "pressure_msl": 1013.8,
                    "wind_speed_10m": 2.1,
                    "wind_direction_10m": 270,
                },
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    monkeypatch.setenv("MOTOQUANT_OPEN_METEO", "1")
    partial = {k: v for k, v in PUNE_CONDITIONS.items() if k != "pressure_hpa"}
    _quick(client, location="Pune, IN", **partial)
    assert calls, "a run without the pressure must still resolve the place"
