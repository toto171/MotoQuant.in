"""
Tests for motoquant.analysis.ecu_autotune (Track B — ECU / Setup Autotune).

Unit tests build a reference config from defaults (no DB needed) and assert the
advisor is genuinely conditions-aware: at high density altitude the engine makes
less power, so the fuel trim leans out and gearing shortens.  A fastapi-gated
route test covers /api/autotune/ecu with explicit conditions (no OWM key needed).
"""

import copy

import pytest

from motoquant.analysis.ecu_autotune import EcuAutotune, autotune
from motoquant.defaults import gsxr1000_k5


def _cfg(alt, temp, rh, press, ttemp, name):
    c = copy.deepcopy(gsxr1000_k5())
    c.name = name
    c.environment.altitude_m = alt
    c.environment.ambient_temp_c = temp
    c.environment.relative_humidity_pct = rh
    c.environment.barometric_pressure_hpa = press
    c.environment.track_temp_c = ttemp
    return c


@pytest.fixture(scope="module")
def sea():
    return autotune(
        _cfg(0, 18, 45, 1013.0, 25, "K5 @ sea"), gear_span=2, launch_steps=4
    )


@pytest.fixture(scope="module")
def high_da():
    return autotune(
        _cfg(1500, 40, 75, 845.0, 48, "K5 @ high DA"), gear_span=2, launch_steps=4
    )


class TestStructure:
    def test_returns_full_recommendation(self, sea):
        assert isinstance(sea, EcuAutotune)
        for block in (
            "environment",
            "stock",
            "gearing",
            "launch_rpm",
            "tyre_pressure",
            "fuel_timing",
            "combined",
        ):
            assert getattr(sea, block), f"missing {block}"

    def test_environment_block_has_atmospherics(self, sea):
        e = sea.environment
        for k in (
            "density_altitude_ft",
            "air_density_kgm3",
            "power_correction_pct",
            "temperature_c",
        ):
            assert k in e
        assert 0.5 < e["air_density_kgm3"] < 1.4

    def test_gearing_recommendation_present(self, sea):
        g = sea.gearing
        assert "recommendation" in g and "delta_et_s" in g
        # K5 is chain-driven, so gearing is adjustable and produces candidates
        assert g["adjustable"] is True
        assert len(g["candidates"]) >= 2
        # recommended gearing is never slower than stock
        # (delta_et_s = recommended - stock since July 6, 2026: <= 0 = not slower)
        assert g["delta_et_s"] <= 1e-6

    def test_launch_recommendation_present(self, sea):
        lr = sea.launch_rpm
        assert lr["recommended_rpm"] > 0
        assert lr["delta_et_s"] <= 1e-6
        assert len(lr["candidates"]) >= 2

    def test_tyre_and_fuel_guidelines(self, sea):
        assert sea.tyre_pressure["rear_psi"] <= sea.tyre_pressure["stock_rear_psi"]
        assert sea.fuel_timing["is_guideline"] is True
        assert "timing_advance_deg" in sea.fuel_timing

    def test_json_serializable(self, sea):
        import json

        json.dumps(sea.to_dict())

    def test_summary_string(self, sea):
        s = sea.summary()
        assert "setup for" in s and "gearing" in s


class TestConditionsAware:
    def test_high_da_has_higher_density_altitude(self, sea, high_da):
        assert (
            high_da.environment["density_altitude_ft"]
            > sea.environment["density_altitude_ft"] + 1500
        )

    def test_high_da_makes_less_power(self, sea, high_da):
        assert (
            high_da.environment["power_correction_pct"]
            < sea.environment["power_correction_pct"]
        )

    def test_high_da_leans_fuel_more(self, sea, high_da):
        # thinner air -> lean out; high-DA trim must be more negative than sea-level
        assert high_da.fuel_timing["fuel_trim_pct"] < sea.fuel_timing["fuel_trim_pct"]
        assert high_da.fuel_timing["fuel_trim_pct"] < 0.0

    def test_high_da_slower_stock_et(self, sea, high_da):
        # less power at altitude -> a slower stock quarter mile (physics sanity)
        assert high_da.stock["et_s"] > sea.stock["et_s"]

    def test_density_ratio_below_one_at_altitude(self, high_da):
        assert high_da.fuel_timing["density_ratio"] < 1.0


class TestShaftDriveGuard:
    def test_non_chain_bike_marks_gearing_fixed(self):
        cfg = copy.deepcopy(gsxr1000_k5())
        cfg.drivetrain.front_sprocket = 0  # emulate shaft/belt drive
        cfg.drivetrain.rear_sprocket = 0
        res = autotune(cfg, gear_span=2, launch_steps=3)
        assert res.gearing["adjustable"] is False
        assert "fixed" in res.gearing["recommendation"].lower()


class TestAutotuneRoute:
    @pytest.fixture(scope="class")
    def client(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from motoquant.api import app

        return TestClient(app)

    def test_autotune_endpoint_with_explicit_conditions(self, client):
        r = client.post(
            "/api/autotune/ecu",
            json={
                "bike_preset": "gsxr1000_k5",
                "ambient_temp_c": 38,
                "humidity_pct": 70,
                "pressure_hpa": 900,
                "altitude_m": 1200,
                "gear_span": 2,
                "launch_steps": 3,
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "gearing" in body and "fuel_timing" in body and "environment" in body
        assert "environment_source" in body
        assert (
            body["environment"]["density_altitude_ft"] > 2000
        )  # hot + high + low pressure
