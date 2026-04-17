"""
Tests for motoquant.api -- FastAPI endpoints.

Uses FastAPI's TestClient (starlette) for synchronous endpoint testing.
Does NOT require a running server or database; presets handle all sim calls.
"""

import io
import json
import math
import unittest

import numpy as np

# FastAPI TestClient
from fastapi.testclient import TestClient

from motoquant.api import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dragy_csv_bytes(n_run_points=400, peak_mph=160.0, duration_s=12.0):
    """Generate a minimal Dragy-style CSV in memory (imperial, with distance).

    Includes a staged period (20 frames at v=0) before the launch ramp,
    which the Dragy parser's run-boundary detector requires (MIN_STAGE_FRAMES=5).
    """
    dt = duration_s / n_run_points
    lines = ["Time (s),Speed (mph),Distance (ft)"]
    n_stage = 20
    for i in range(n_stage):
        t = i * dt
        lines.append(f"{t:.3f},0.0000,0.0000")
    dist_ft = 0.0
    for i in range(n_run_points):
        t = (n_stage + i) * dt
        frac = i / n_run_points
        v_mph = peak_mph * (frac ** 0.7)
        v_ms = v_mph * 0.44704
        dist_ft += v_ms * dt / 0.3048
        lines.append(f"{t:.3f},{v_mph:.4f},{dist_ft:.4f}")
    return "\n".join(lines).encode("utf-8")


def _dyno_csv_bytes(n_points=50):
    """Generate a minimal DynoJet-style CSV (WHP/lb-ft vs RPM)."""
    lines = ["RPM,WHP,TQ (lb-ft)"]
    for i in range(n_points):
        rpm = 3000 + i * (11000 - 3000) / n_points
        frac = (rpm - 3000) / 8000
        whp = 150 * math.exp(-0.5 * ((frac - 0.85) / 0.25) ** 2)
        tq = whp * 5252 / rpm if rpm > 0 else 0
        lines.append(f"{rpm:.0f},{whp:.2f},{tq:.2f}")
    return "\n".join(lines).encode("utf-8")


# ===========================================================================
# Existing endpoint smoke tests
# ===========================================================================

class TestHealthEndpoints(unittest.TestCase):
    def test_root(self):
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["service"], "MotoQuant Pro API")
        self.assertEqual(body["status"], "ok")

    def test_health(self):
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("status", body)
        self.assertIn("database", body)

    def test_docs_accessible(self):
        r = client.get("/docs")
        self.assertEqual(r.status_code, 200)


class TestQuickSim(unittest.TestCase):
    def test_preset_gsxr(self):
        r = client.post("/api/simulate/quick", json={
            "bike_preset": "gsxr1000_k5",
            "rider_mass_kg": 75,
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("et_quarter_s", body)
        self.assertGreater(body["et_quarter_s"], 9.0)
        self.assertLess(body["et_quarter_s"], 12.0)

    def test_preset_hayabusa(self):
        r = client.post("/api/simulate/quick", json={
            "bike_preset": "hayabusa_gen1",
            "rider_mass_kg": 80,
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["trap_speed_kmh"], 180)

    def test_power_boost_makes_faster(self):
        stock = client.post("/api/simulate/quick", json={
            "bike_preset": "gsxr1000_k5",
        }).json()
        boosted = client.post("/api/simulate/quick", json={
            "bike_preset": "gsxr1000_k5",
            "power_boost_pct": 20,
        }).json()
        self.assertLess(boosted["et_quarter_s"], stock["et_quarter_s"])

    def test_heavier_rider_slower(self):
        light = client.post("/api/simulate/quick", json={
            "bike_preset": "gsxr1000_k5",
            "rider_mass_kg": 60,
        }).json()
        heavy = client.post("/api/simulate/quick", json={
            "bike_preset": "gsxr1000_k5",
            "rider_mass_kg": 120,
        }).json()
        self.assertLess(light["et_quarter_s"], heavy["et_quarter_s"])


class TestFullSim(unittest.TestCase):
    def test_returns_timeseries(self):
        r = client.post("/api/simulate", json={
            "bike_preset": "yzfr1_4c8",
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("timeseries", body)
        ts = body["timeseries"]
        self.assertIn("t_s", ts)
        self.assertIn("v_kmh", ts)
        self.assertIn("rpm", ts)
        self.assertGreater(len(ts["t_s"]), 10)

    def test_splits_present(self):
        r = client.post("/api/simulate", json={
            "bike_preset": "gsxr1000_k5",
        })
        body = r.json()
        self.assertIn("splits", body)
        splits = body["splits"]
        self.assertLess(splits["60ft_s"], splits["330ft_s"])
        self.assertLess(splits["660ft_s"], splits["1320ft_s"])


# ===========================================================================
# A vs B Comparison
# ===========================================================================

class TestCompareEndpoint(unittest.TestCase):
    def test_basic_compare_same_bike(self):
        r = client.post("/api/simulate/compare", json={
            "a_bike_preset": "gsxr1000_k5",
            "a_power_boost_pct": 0,
            "b_bike_preset": "gsxr1000_k5",
            "b_power_boost_pct": 15,
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("a", body)
        self.assertIn("b", body)
        self.assertIn("delta", body)
        self.assertLess(body["delta"]["et_s"], 0)
        self.assertEqual(body["delta"]["faster"], "B")

    def test_compare_returns_timeseries(self):
        r = client.post("/api/simulate/compare", json={
            "a_bike_preset": "gsxr1000_k5",
            "b_bike_preset": "hayabusa_gen1",
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("timeseries", body["a"])
        self.assertIn("timeseries", body["b"])
        self.assertGreater(len(body["a"]["timeseries"]["t_s"]), 10)

    def test_compare_different_bikes(self):
        r = client.post("/api/simulate/compare", json={
            "a_bike_preset": "gsxr1000_k5",
            "b_bike_preset": "hayabusa_gen1",
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["a"]["et_quarter_s"], 8)
        self.assertGreater(body["b"]["et_quarter_s"], 8)
        expected_delta = round(body["b"]["et_quarter_s"] - body["a"]["et_quarter_s"], 4)
        self.assertAlmostEqual(body["delta"]["et_s"], expected_delta, places=3)

    def test_compare_cost_diff(self):
        r = client.post("/api/simulate/compare", json={
            "a_bike_preset": "gsxr1000_k5",
            "b_bike_preset": "gsxr1000_k5",
            "b_power_boost_pct": 10,
        })
        body = r.json()
        self.assertEqual(body["delta"]["cost_diff_inr"], 0)

    def test_compare_labels(self):
        r = client.post("/api/simulate/compare", json={
            "a_bike_preset": "gsxr1000_k5",
            "b_bike_preset": "gsxr1000_k5",
        })
        body = r.json()
        self.assertEqual(body["a"]["label"], "A")
        self.assertEqual(body["b"]["label"], "B")


# ===========================================================================
# Dragy Upload
# ===========================================================================

class TestDragyUpload(unittest.TestCase):
    def test_upload_csv_parses_run(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("test_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("runs_detected", body)
        self.assertGreaterEqual(body["runs_detected"], 1)
        self.assertIn("best_run", body)
        best = body["best_run"]
        self.assertIn("et_quarter_s", best)
        self.assertIn("trap_speed_kmh", best)
        self.assertIn("timeseries", best)

    def test_upload_with_overlay(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", io.BytesIO(csv_bytes), "text/csv")},
            data={"bike_preset": "gsxr1000_k5"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("overlay", body)
        ov = body["overlay"]
        self.assertIn("sim_et_s", ov)
        self.assertIn("et_error_s", ov)
        self.assertIn("v_rmse_kmh", ov)
        self.assertIn("sim_timeseries", ov)

    def test_upload_without_overlay(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertNotIn("overlay", body)

    def test_upload_invalid_csv_returns_422(self):
        bad_csv = b"this,is,not,a,dragy,file\n1,2,3,4,5,6\n"
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")},
        )
        self.assertIn(r.status_code, [422, 400])

    def test_filename_returned(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("my_dragy_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        self.assertEqual(body.get("filename"), "my_dragy_run.csv")


# ===========================================================================
# Dyno Upload
# ===========================================================================

class TestDynoUpload(unittest.TestCase):
    def test_upload_dyno_csv(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("peak_power_hp", body)
        self.assertIn("peak_torque_nm", body)
        self.assertIn("curve", body)
        self.assertGreater(body["peak_power_hp"], 50)
        self.assertLess(body["peak_power_hp"], 300)

    def test_dyno_curve_arrays(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        curve = body["curve"]
        self.assertIn("rpm", curve)
        self.assertIn("power_hp", curve)
        self.assertIn("torque_nm", curve)
        self.assertEqual(len(curve["rpm"]), len(curve["power_hp"]))
        self.assertEqual(len(curve["rpm"]), len(curve["torque_nm"]))

    def test_dyno_with_atmospheric_correction(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
            data={"temp_c": "35", "pressure_kpa": "95", "rh_pct": "60"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["correction_factor"], 0.9)
        self.assertIn("is_at_wheel", body)

    def test_dyno_filename_returned(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("hayabusa_dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        self.assertEqual(body.get("filename"), "hayabusa_dyno.csv")

    def test_dyno_invalid_csv_returns_422(self):
        bad = b"nothing useful here\njust junk\n"
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("bad.csv", io.BytesIO(bad), "text/csv")},
        )
        self.assertIn(r.status_code, [422, 400])


if __name__ == "__main__":
    unittest.main()
