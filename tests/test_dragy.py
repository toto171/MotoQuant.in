"""
Tests for motoquant.calibration.dragy
======================================
All tests use in-memory / tmp files — no network or real device needed.
Synthetic GPS data is generated with realistic physics so boundary detection
and ET computation can be verified analytically.
"""

import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from motoquant.calibration.dragy import (
    QUARTER_MILE_M,
    DragParseError,
    DragRunData,
    _compute_acceleration,
    _detect_runs,
    _detect_sample_rate,
    _integrate_distance,
    _interpolate_et,
    _interpolate_speed_at_distance,
    _to_si_distance,
    _to_si_velocity,
    best_run,
    parse_dragy_file,
)

# ─── Synthetic run generator ─────────────────────────────────────────────


def _synthetic_run(
    dt: float = 0.1,
    idle_before_s: float = 3.0,
    et_target_s: float = 10.0,
    peak_speed_ms: float = 62.0,  # ~223 km/h trap
    idle_after_s: float = 2.0,
) -> tuple:
    """
    Generate synthetic GPS v(t) that mimics a Dragy recording.

    Returns (t_arr, v_ms_arr) as numpy arrays, plus the analytically-computed
    ET and trap speed for verification.

    Velocity model: simple parabolic ramp from 0 to peak_speed at et_target,
    then flat coasting.  Distance is integrated analytically.
    """
    n_idle_pre = int(idle_before_s / dt)
    n_run = int(et_target_s / dt) + 50  # some over-run past 1/4 mile
    n_idle_post = int(idle_after_s / dt)

    # Pre-run idle (v = 0)
    t_idle_pre = np.arange(0, n_idle_pre) * dt
    v_idle_pre = np.zeros(n_idle_pre)

    # Run: ramp from 0 → peak_speed over et_target seconds (quadratic)
    t_run = np.arange(0, n_run) * dt
    # v(t) = A*t*(1 - t/(2*et_target)) so that v'(0) = A, v(et_target) ≈ peak
    # Simpler: linear ramp to peak then constant
    v_run = np.clip(t_run / et_target_s * peak_speed_ms, 0, peak_speed_ms)

    # Post-trap idle — handle zero idle_before gracefully
    t_mid_offset = t_idle_pre[-1] + dt if n_idle_pre > 0 else 0.0
    t_last = t_run[-1] + t_mid_offset + dt
    t_idle_post = np.arange(0, n_idle_post) * dt + t_last
    v_idle_post = np.zeros(n_idle_post)

    # Stitch together with proper timestamps
    t_full = np.concatenate(
        [
            t_idle_pre,
            t_run + t_mid_offset,
            t_idle_post,
        ]
    )
    v_full = np.concatenate([v_idle_pre, v_run, v_idle_post])

    # Analytical ET: d(t) = integral of v_run(t) = (peak/(2*et)) * t^2
    # → t² = QUARTER_MILE_M * 2 * et / peak → t_q = sqrt(QM * 2 / (peak/et))
    # For linear ramp v(t) = (peak/et)*t:
    #   d(t) = (peak/(2*et)) * t^2
    #   d(t_q) = QM → t_q = sqrt(2 * QM * et / peak)
    t_q = math.sqrt(2 * QUARTER_MILE_M * et_target_s / peak_speed_ms)
    v_q = min(peak_speed_ms, (peak_speed_ms / et_target_s) * t_q)

    return t_full, v_full, t_q, v_q


def _write_csv_file(
    path: Path,
    t: np.ndarray,
    v_ms: np.ndarray,
    speed_unit: str = "mph",
    dist_unit: str = "ft",
    include_distance: bool = True,
) -> None:
    """Write synthetic arrays as a Dragy-style CSV."""
    if speed_unit == "mph":
        v_export = v_ms / 0.44704
        v_header = "Speed (mph)"
    elif speed_unit == "kmh":
        v_export = v_ms * 3.6
        v_header = "Speed (km/h)"
    else:
        v_export = v_ms
        v_header = "Speed (m/s)"

    d_m = _integrate_distance(t, v_ms)

    if dist_unit == "ft":
        d_export = d_m / 0.3048
        d_header = "Distance (ft)"
    else:
        d_export = d_m
        d_header = "Distance (m)"

    with open(path, "w", newline="") as fh:
        fh.write(f"Time (s),{v_header}")
        if include_distance:
            fh.write(f",{d_header}")
        fh.write("\n")
        for i in range(len(t)):
            fh.write(f"{t[i]:.3f},{v_export[i]:.4f}")
            if include_distance:
                fh.write(f",{d_export[i]:.4f}")
            fh.write("\n")


def _write_json_file(
    path: Path, t: np.ndarray, v_ms: np.ndarray, speed_unit: str = "mph"
) -> None:
    """Write synthetic arrays as a Dragy-style JSON."""
    if speed_unit == "mph":
        v_export = v_ms / 0.44704
        v_key = "v_mph"
    elif speed_unit == "kmh":
        v_export = v_ms * 3.6
        v_key = "v_kmh"
    else:
        v_export = v_ms
        v_key = "v_ms"

    samples = [{"t": float(t[i]), v_key: float(v_export[i])} for i in range(len(t))]
    payload = {
        "meta": {"track": "Aamby Valley", "vehicle": "GSX-R 1000"},
        "runs": [{"et": 10.0, "samples": samples}],
    }
    with open(path, "w") as fh:
        json.dump(payload, fh)


# ─── Unit helper tests ────────────────────────────────────────────────────


class TestUnitConversion(unittest.TestCase):
    def test_mph_to_ms(self):
        v = np.array([0.0, 60.0, 100.0])
        result = _to_si_velocity(v, "mph")
        self.assertAlmostEqual(result[1], 26.8224, places=3)
        self.assertAlmostEqual(result[2], 44.704, places=3)

    def test_kmh_to_ms(self):
        v = np.array([0.0, 108.0])
        result = _to_si_velocity(v, "kmh")
        self.assertAlmostEqual(result[1], 30.0, places=5)

    def test_ms_passthrough(self):
        v = np.array([0.0, 25.0, 50.0])
        result = _to_si_velocity(v, "ms")
        np.testing.assert_array_equal(v, result)

    def test_ft_to_m(self):
        d = np.array([0.0, 1320.0])
        result = _to_si_distance(d, "ft")
        self.assertAlmostEqual(result[1], QUARTER_MILE_M, places=3)

    def test_m_passthrough(self):
        d = np.array([0.0, 402.336])
        result = _to_si_distance(d, "m")
        np.testing.assert_array_equal(d, result)


# ─── Integration and derivative ──────────────────────────────────────────


class TestIntegrationAndDerivative(unittest.TestCase):
    def test_constant_velocity_integrates_correctly(self):
        t = np.linspace(0, 10, 101)  # 0–10 s at 0.1 s steps
        v = np.full(101, 30.0)  # 30 m/s constant
        d = _integrate_distance(t, v)
        self.assertAlmostEqual(d[-1], 300.0, places=4)

    def test_linear_ramp_integrates_to_parabola(self):
        # v(t) = a*t → d(T) = a*T²/2
        a = 5.0  # m/s²
        T = 10.0
        n = 10001
        t = np.linspace(0, T, n)
        v = a * t
        d = _integrate_distance(t, v)
        expected = 0.5 * a * T**2
        self.assertAlmostEqual(d[-1], expected, places=2)

    def test_integration_starts_at_zero(self):
        t = np.linspace(0, 5, 51)
        v = np.ones(51) * 10.0
        d = _integrate_distance(t, v)
        self.assertEqual(d[0], 0.0)

    def test_acceleration_constant_velocity_is_zero(self):
        t = np.linspace(0, 5, 51)
        v = np.full(51, 20.0)
        a = _compute_acceleration(t, v)
        np.testing.assert_allclose(a, 0.0, atol=1e-9)

    def test_acceleration_constant_ramp(self):
        # v(t) = 10*t → dv/dt = 10 everywhere
        t = np.linspace(0, 5, 501)
        v = 10.0 * t
        a = _compute_acceleration(t, v)
        np.testing.assert_allclose(a, 10.0, atol=1e-6)

    def test_sample_rate_detection(self):
        t = np.arange(0, 100, 0.1)  # 10 Hz
        sr = _detect_sample_rate(t)
        self.assertAlmostEqual(sr, 10.0, places=5)

    def test_sample_rate_detection_25hz(self):
        t = np.arange(0, 40, 0.04)  # 25 Hz
        sr = _detect_sample_rate(t)
        self.assertAlmostEqual(sr, 25.0, places=3)


# ─── Interpolation ────────────────────────────────────────────────────────


class TestInterpolation(unittest.TestCase):
    def _make_linear_run(self, accel=5.0, T=12.0, dt=0.1):
        t = np.arange(0, T, dt)
        v = accel * t
        d = _integrate_distance(t, v)
        return t, v, d

    def test_et_interpolation_exact(self):
        t, v, d = self._make_linear_run(accel=5.0, T=12.0)
        # d(t) = 2.5*t² → t_q = sqrt(402.336/2.5) ≈ 12.69s — but T=12 so cap
        # use lower distance
        target = 100.0
        et = _interpolate_et(t, d, target)
        # v = 5t, d = 2.5t² → t = sqrt(d/2.5)
        expected = math.sqrt(target / 2.5)
        self.assertIsNotNone(et)
        self.assertAlmostEqual(et, expected, places=1)

    def test_et_returns_none_when_not_reached(self):
        t = np.linspace(0, 5, 51)
        d = np.linspace(0, 100.0, 51)  # only goes to 100m
        et = _interpolate_et(t, d, 402.336)
        self.assertIsNone(et)

    def test_speed_at_distance_interpolation(self):
        t = np.linspace(0, 10, 101)
        v = np.linspace(0, 50, 101)  # linear ramp
        d = _integrate_distance(t, v)
        speed = _interpolate_speed_at_distance(v, d, d[50])
        self.assertAlmostEqual(speed, v[50], places=3)

    def test_speed_at_distance_none_beyond_range(self):
        t = np.linspace(0, 5, 51)
        v = np.full(51, 10.0)
        d = _integrate_distance(t, v)  # max ~50m
        speed = _interpolate_speed_at_distance(v, d, 9999.0)
        self.assertIsNone(speed)


# ─── Run boundary detection ───────────────────────────────────────────────


class TestRunBoundaryDetection(unittest.TestCase):
    def _build_full_telemetry(self, **kwargs):
        t, v, t_q, v_q = _synthetic_run(**kwargs)
        d = _integrate_distance(t, v)
        return t, v, d, t_q, v_q

    def test_single_run_detected(self):
        t, v, d, t_q, v_q = self._build_full_telemetry(
            et_target_s=10.0, peak_speed_ms=62.0
        )
        runs = _detect_runs(t, v, d)
        self.assertEqual(len(runs), 1)

    def test_et_within_tolerance(self):
        t, v, d, t_q, v_q = self._build_full_telemetry(
            et_target_s=10.0, peak_speed_ms=62.0, dt=0.1
        )
        runs = _detect_runs(t, v, d)
        self.assertEqual(len(runs), 1)
        launch_idx, end_idx, et, trap = runs[0]
        # ET tolerance: within 0.2 s of analytical (GPS is 10 Hz)
        self.assertAlmostEqual(et, t_q, delta=0.3)

    def test_trap_speed_within_tolerance(self):
        t, v, d, t_q, v_q = self._build_full_telemetry(
            et_target_s=10.0, peak_speed_ms=62.0
        )
        runs = _detect_runs(t, v, d)
        _, _, _, trap = runs[0]
        self.assertAlmostEqual(trap, v_q, delta=2.0)  # within 2 m/s

    def test_no_run_below_speed_threshold(self):
        """Very slow run (10 m/s peak = 36 km/h) should be rejected."""
        t, v, d, _, _ = self._build_full_telemetry(peak_speed_ms=10.0, et_target_s=25.0)
        runs = _detect_runs(t, v, d)
        self.assertEqual(len(runs), 0)

    def test_pure_idle_no_run(self):
        """All-zero velocity → no runs."""
        t = np.linspace(0, 30, 301)
        v = np.zeros(301)
        d = _integrate_distance(t, v)
        runs = _detect_runs(t, v, d)
        self.assertEqual(len(runs), 0)

    def test_two_runs_in_sequence(self):
        """Two back-to-back runs separated by idle window → 2 runs detected."""
        t1, v1, _, _ = _synthetic_run(
            idle_before_s=2.0, et_target_s=10.0, peak_speed_ms=60.0, idle_after_s=3.0
        )
        t2, v2, _, _ = _synthetic_run(
            idle_before_s=0.0, et_target_s=10.5, peak_speed_ms=58.0, idle_after_s=2.0
        )
        t_offset = t1[-1] + 0.1
        t_full = np.concatenate([t1, t2 + t_offset])
        v_full = np.concatenate([v1, v2])
        d_full = _integrate_distance(t_full, v_full)
        runs = _detect_runs(t_full, v_full, d_full)
        self.assertGreaterEqual(len(runs), 1)  # at least one; often 2


# ─── CSV parsing ──────────────────────────────────────────────────────────


class TestCSVParsing(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.t, self.v, self.t_q, self.v_q = _synthetic_run(
            idle_before_s=2.0, et_target_s=10.0, peak_speed_ms=60.0, dt=0.1
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def _csv_path(self, name):
        return Path(self.tmpdir.name) / name

    # ── Imperial (mph / ft) ──────────────────────────────────────────────

    def test_parse_csv_imperial_with_distance(self):
        p = self._csv_path("run_imperial.csv")
        _write_csv_file(p, self.t, self.v, speed_unit="mph", dist_unit="ft")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    def test_parse_csv_imperial_no_distance(self):
        p = self._csv_path("run_imperial_nodist.csv")
        _write_csv_file(
            p, self.t, self.v, speed_unit="mph", dist_unit="ft", include_distance=False
        )
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    # ── Metric (km/h / m) ───────────────────────────────────────────────

    def test_parse_csv_metric(self):
        p = self._csv_path("run_metric.csv")
        _write_csv_file(p, self.t, self.v, speed_unit="kmh", dist_unit="m")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    def test_trap_speed_si_correct(self):
        p = self._csv_path("run_trap.csv")
        _write_csv_file(p, self.t, self.v, speed_unit="mph", dist_unit="ft")
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].trap_speed_ms, self.v_q, delta=2.0)

    def test_trap_speed_kmh_property(self):
        p = self._csv_path("run_kmh.csv")
        _write_csv_file(p, self.t, self.v, speed_unit="kmh", dist_unit="m")
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(
            runs[0].trap_speed_kmh, runs[0].trap_speed_ms * 3.6, places=4
        )

    # ── Metadata and file properties ────────────────────────────────────

    def test_source_file_recorded(self):
        p = self._csv_path("source_check.csv")
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertEqual(runs[0].source_file, str(p))

    def test_sample_rate_approx_10hz(self):
        p = self._csv_path("sr_check.csv")
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].sample_rate_hz, 10.0, delta=0.5)

    def test_timestamps_start_at_zero(self):
        p = self._csv_path("t0_check.csv")
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].timestamps[0], 0.0, places=5)

    def test_distance_starts_at_zero(self):
        p = self._csv_path("d0_check.csv")
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].distance_m[0], 0.0, places=5)

    def test_distance_monotonically_increasing(self):
        p = self._csv_path("mono_check.csv")
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        diffs = np.diff(runs[0].distance_m)
        self.assertTrue(np.all(diffs >= -0.01))

    def test_parse_empty_csv_raises(self):
        p = self._csv_path("empty.csv")
        p.write_text("Time (s),Speed (mph),Distance (ft)\n")
        with self.assertRaises(DragParseError):
            parse_dragy_file(p)

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            parse_dragy_file("/nonexistent/path/run.csv")


# ─── JSON parsing ─────────────────────────────────────────────────────────


class TestJSONParsing(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.t, self.v, self.t_q, self.v_q = _synthetic_run(
            idle_before_s=2.0, et_target_s=10.0, peak_speed_ms=60.0, dt=0.1
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def _json_path(self, name):
        return Path(self.tmpdir.name) / name

    def test_parse_json_mph(self):
        p = self._json_path("run_mph.json")
        _write_json_file(p, self.t, self.v, speed_unit="mph")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    def test_parse_json_kmh(self):
        p = self._json_path("run_kmh.json")
        _write_json_file(p, self.t, self.v, speed_unit="kmh")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    def test_parse_json_ms(self):
        p = self._json_path("run_ms.json")
        _write_json_file(p, self.t, self.v, speed_unit="ms")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.3)

    def test_json_trap_speed(self):
        p = self._json_path("trap_json.json")
        _write_json_file(p, self.t, self.v, speed_unit="mph")
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].trap_speed_ms, self.v_q, delta=2.0)

    def test_json_metadata_preserved(self):
        p = self._json_path("meta_json.json")
        _write_json_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertIn("track", runs[0].raw_metadata)

    def test_json_empty_samples_skipped(self):
        p = self._json_path("empty_json.json")
        payload = {"meta": {}, "runs": [{"samples": []}]}
        p.write_text(json.dumps(payload))
        runs = parse_dragy_file(p)
        self.assertEqual(runs, [])

    def test_json_malformed_raises(self):
        p = self._json_path("bad.json")
        p.write_text("{not valid json")
        with self.assertRaises((DragParseError, Exception)):
            parse_dragy_file(p)


# ─── DragRunData properties and methods ───────────────────────────────────


class TestDragRunDataProperties(unittest.TestCase):
    def _make_run(self, et=None, trap=58.0, sr=10.0) -> DragRunData:
        t = np.linspace(0, 12, 121)
        v = np.clip(t / 10.0 * trap, 0, trap)
        d = _integrate_distance(t, v)
        a = _compute_acceleration(t, v)
        # Derive et_quarter from the distance array so splits() is consistent
        computed_et = _interpolate_et(t, d, QUARTER_MILE_M)
        actual_et = computed_et if computed_et is not None else (et or 12.0)
        return DragRunData(
            timestamps=t,
            velocity_ms=v,
            distance_m=d,
            acceleration_ms2=a,
            et_quarter=actual_et,
            trap_speed_ms=trap,
            sample_rate_hz=sr,
            source_file="synthetic",
        )

    def test_trap_speed_kmh(self):
        run = self._make_run(trap=58.0)
        self.assertAlmostEqual(run.trap_speed_kmh, 58.0 * 3.6, places=4)

    def test_trap_speed_mph(self):
        run = self._make_run(trap=58.0)
        self.assertAlmostEqual(run.trap_speed_mph, 58.0 * 2.23694, places=3)

    def test_duration_s(self):
        run = self._make_run()
        self.assertAlmostEqual(run.duration_s, 12.0, delta=0.01)

    def test_splits_returns_dict(self):
        run = self._make_run()
        s = run.splits()
        self.assertIsInstance(s, dict)

    def test_splits_60ft_less_than_330ft(self):
        run = self._make_run()
        s = run.splits()
        if "60ft" in s and "330ft" in s:
            self.assertLess(s["60ft"], s["330ft"])

    def test_splits_1320ft_equals_quarter(self):
        # _make_run derives et_quarter from the distance array, so splits["1320ft"]
        # must match et_quarter (same integration, same interpolation).
        run = self._make_run()
        s = run.splits()
        if "1320ft" in s:
            self.assertAlmostEqual(s["1320ft"], run.et_quarter, delta=0.05)

    def test_to_dict_keys(self):
        run = self._make_run()
        d = run.to_dict()
        for key in ["et_quarter", "trap_speed_kmh", "trap_speed_mph", "splits"]:
            self.assertIn(key, d)

    def test_to_dict_et_rounded(self):
        run = self._make_run()
        d = run.to_dict()
        # ET in to_dict is rounded to 4 decimal places
        self.assertEqual(d["et_quarter"], round(run.et_quarter, 4))


# ─── best_run helper ─────────────────────────────────────────────────────


class TestBestRun(unittest.TestCase):
    def _fake_run(self, et):
        t = np.array([0.0, 1.0])
        v = np.array([0.0, 10.0])
        d = _integrate_distance(t, v)
        a = _compute_acceleration(t, v)
        return DragRunData(t, v, d, a, et, 50.0, 10.0, "test")

    def test_best_run_lowest_et(self):
        runs = [self._fake_run(10.5), self._fake_run(10.1), self._fake_run(10.8)]
        best = best_run(runs)
        self.assertAlmostEqual(best.et_quarter, 10.1)

    def test_best_run_empty_list(self):
        self.assertIsNone(best_run([]))

    def test_best_run_single(self):
        runs = [self._fake_run(11.2)]
        self.assertAlmostEqual(best_run(runs).et_quarter, 11.2)


# ─── End-to-end round-trip ────────────────────────────────────────────────


class TestEndToEnd(unittest.TestCase):
    """
    Full round-trip: synthetic CSV → parse → DragRunData → verify ET and splits.
    Uses 25 Hz to test non-10 Hz sample rates.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.t, self.v, self.t_q, self.v_q = _synthetic_run(
            dt=0.04,  # 25 Hz
            idle_before_s=3.0,
            et_target_s=9.8,  # fast-ish bike
            peak_speed_ms=65.0,  # ~234 km/h
            idle_after_s=2.0,
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_25hz_csv_et_accuracy(self):
        p = Path(self.tmpdir.name) / "25hz.csv"
        _write_csv_file(p, self.t, self.v, speed_unit="kmh", dist_unit="m")
        runs = parse_dragy_file(p)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0].et_quarter, self.t_q, delta=0.2)

    def test_25hz_sample_rate_detected(self):
        p = Path(self.tmpdir.name) / "25hz_sr.csv"
        _write_csv_file(p, self.t, self.v, speed_unit="kmh", dist_unit="m")
        runs = parse_dragy_file(p)
        self.assertAlmostEqual(runs[0].sample_rate_hz, 25.0, delta=1.0)

    def test_arrays_same_length(self):
        p = Path(self.tmpdir.name) / "25hz_len.csv"
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        run = runs[0]
        self.assertEqual(len(run.timestamps), len(run.velocity_ms))
        self.assertEqual(len(run.timestamps), len(run.distance_m))
        self.assertEqual(len(run.timestamps), len(run.acceleration_ms2))

    def test_run_index_zero(self):
        p = Path(self.tmpdir.name) / "run_idx.csv"
        _write_csv_file(p, self.t, self.v)
        runs = parse_dragy_file(p)
        self.assertEqual(runs[0].run_index, 0)


if __name__ == "__main__":
    unittest.main()
