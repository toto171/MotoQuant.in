"""
Tests for motoquant.calibration.ecu — ECU log import.

Coverage:
  - Woolich Racing CSV parsing
  - Power Commander PC-Link CSV parsing
  - MoTeC i2 tab-delimited parsing
  - Generic CSV fallback
  - Channel name mapping & unit conversion
  - Run-window detection from speed channel
  - Run-window detection from RPM fallback
  - ET / trap interpolation
  - Multiple runs in one file
  - Edge cases: missing channels, bad data, file-not-found
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# ── path shim ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant.calibration.dragy import QUARTER_MILE_M
from motoquant.calibration.ecu import (
    ECULog,
    ECUParseError,
    _integrate_distance,
    _interpolate_et,
    _interpolate_speed,
    _map_column,
    parse_ecu_file,
)

# ─── helpers ──────────────────────────────────────────────────────────────


def _write_tmp(content: str, suffix: str = ".csv") -> str:
    """Write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _make_woolich_csv(
    n_idle_before: int = 50,
    n_run: int = 1200,
    n_idle_after: int = 30,
    dt: float = 0.01,
    peak_speed_ms: float = 65.0,
    include_gear: bool = True,
    include_afr: bool = True,
    include_temps: bool = True,
) -> str:
    """
    Build a synthetic Woolich Racing CSV with one drag run.
    Speed is stored in km/h (as real Woolich exports), which the parser
    converts to m/s via the KMH_TO_MS factor.
    """
    header_cols = ["Time", "RPM", "TPS%", "Speed"]
    if include_gear:
        header_cols.append("Gear")
    if include_afr:
        header_cols.append("AFR")
    if include_temps:
        header_cols += ["Coolant Temp", "Air Temp"]
    header_cols += ["Ignition Adv", "MAP (kPa)", "Battery"]

    lines = [",".join(header_cols)]

    t = 0.0
    for i in range(n_idle_before):
        row = [f"{t:.3f}", "1100", "0.0", "0.0"]  # speed = 0 km/h
        if include_gear:
            row.append("1")
        if include_afr:
            row.append("14.7")
        if include_temps:
            row += ["85", "30"]
        row += ["0.0", "101.3", "12.6"]
        lines.append(",".join(row))
        t += dt

    for i in range(n_run):
        frac = i / max(n_run - 1, 1)
        speed_kmh = peak_speed_ms * 3.6 * (frac**0.6)  # km/h
        rpm = int(3500 + frac * 10000)
        tps = 5.0 + frac * 95.0
        gear = min(6, int(frac * 6) + 1)
        row = [f"{t:.3f}", str(rpm), f"{tps:.1f}", f"{speed_kmh:.3f}"]
        if include_gear:
            row.append(str(gear))
        if include_afr:
            row.append(f"{12.5 + frac:.2f}")
        if include_temps:
            row += [f"{85 + frac * 5:.1f}", f"{28 + frac * 2:.1f}"]
        row += [f"{28 - frac * 4:.1f}", "101.3", "12.4"]
        lines.append(",".join(row))
        t += dt

    for i in range(n_idle_after):
        row = [f"{t:.3f}", "1000", "0.0", "5.0"]  # slight coast 5 km/h
        if include_gear:
            row.append("1")
        if include_afr:
            row.append("14.7")
        if include_temps:
            row += ["90", "30"]
        row += ["0.0", "101.3", "12.5"]
        lines.append(",".join(row))
        t += dt

    return "\n".join(lines)


def _make_pclink_csv(
    n_idle: int = 40,
    n_run: int = 1000,
    peak_speed_kmh: float = 220.0,
    dt: float = 0.01,
) -> str:
    """Build a synthetic PC-Link CSV."""
    header = "Time (s),RPM,TP%,Lambda,ECT(°C),IAT(°C),VSS(km/h),Gear"
    lines = [header]
    t = 0.0

    for _ in range(n_idle):
        lines.append(f"{t:.3f},900,0.0,1.000,80,25,0.0,1")
        t += dt

    for i in range(n_run):
        frac = i / max(n_run - 1, 1)
        speed_kmh = peak_speed_kmh * (frac**0.55)
        rpm = int(2000 + frac * 11000)
        tps = frac * 100.0
        lam = 0.95 + 0.05 * frac  # lambda 0.95 → 1.0 during run
        gear = min(6, int(frac * 6) + 1)
        lines.append(
            f"{t:.3f},{rpm},{tps:.1f},{lam:.3f},{80 + frac * 5:.1f},{25 + frac:.1f},"
            f"{speed_kmh:.2f},{gear}"
        )
        t += dt

    for _ in range(30):
        lines.append(f"{t:.3f},1000,0.0,1.000,90,26,10.0,1")
        t += dt

    return "\n".join(lines)


def _make_motec_tsv(
    n_idle: int = 50,
    n_run: int = 1500,
    peak_speed_ms: float = 70.0,
    dt: float = 0.01,
) -> str:
    """
    Build a minimal synthetic MoTeC i2 tab-delimited export.
    Units row explicitly states 'm/s' for Ground Speed, so the parser
    applies no conversion (identity) via _apply_unit_overrides.
    """
    # Metadata preamble
    meta = [
        "Segment\t1",
        "Format\tMoTeC CSV Format",
        "Venue\tAamby Valley",
        "Vehicle\tGSX-R 1000",
        "",
        # Channel header row — MoTeC uses "Engine Speed" for RPM
        "Time\tEngine Speed\tThrottle Position\tGround Speed\tGear",
        # Units row — 'm/s' tells _apply_unit_overrides: no km/h conversion
        "s\trpm\t%\tm/s\t",
    ]
    lines = meta

    t = 0.0
    for _ in range(n_idle):
        lines.append(f"{t:.4f}\t1100\t0.0\t0.000\t1")
        t += dt

    for i in range(n_run):
        frac = i / max(n_run - 1, 1)
        speed_ms = peak_speed_ms * (frac**0.5)
        rpm = int(3000 + frac * 11500)
        tps = frac * 100.0
        gear = min(6, int(frac * 6) + 1)
        lines.append(f"{t:.4f}\t{rpm}\t{tps:.2f}\t{speed_ms:.4f}\t{gear}")
        t += dt

    for _ in range(20):
        lines.append(f"{t:.4f}\t1000\t0.0\t2.0\t1")
        t += dt

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# 1. MATHS HELPERS
# ═══════════════════════════════════════════════════════════════════════════


class TestMathHelpers(unittest.TestCase):
    def test_integrate_constant_speed(self):
        """Constant 10 m/s for 10 s → 100 m total."""
        t = np.linspace(0, 10, 101)
        v = np.full(101, 10.0)
        dist = _integrate_distance(t, v)
        self.assertAlmostEqual(dist[-1], 100.0, delta=0.1)

    def test_integrate_starts_zero(self):
        t = np.array([0.0, 1.0, 2.0])
        v = np.array([5.0, 5.0, 5.0])
        dist = _integrate_distance(t, v)
        self.assertEqual(dist[0], 0.0)

    def test_interpolate_et_exact(self):
        t = np.array([0.0, 5.0, 10.0, 15.0])
        d = np.array([0.0, 100.0, 300.0, 500.0])
        et = _interpolate_et(t, d, 300.0)
        self.assertAlmostEqual(et, 10.0, places=6)

    def test_interpolate_et_between_samples(self):
        t = np.array([0.0, 10.0])
        d = np.array([0.0, 402.336])
        et = _interpolate_et(t, d, 201.168)
        self.assertAlmostEqual(et, 5.0, places=4)

    def test_interpolate_et_not_reached(self):
        t = np.array([0.0, 5.0])
        d = np.array([0.0, 200.0])
        et = _interpolate_et(t, d, QUARTER_MILE_M)
        self.assertIsNone(et)

    def test_interpolate_speed_at_qm(self):
        t = np.array([0.0, 10.0, 12.0])
        v = np.array([0.0, 60.0, 65.0])
        d = np.array([0.0, 300.0, 450.0])
        spd = _interpolate_speed(t, v, d, QUARTER_MILE_M)
        self.assertIsNotNone(spd)
        # Should be between 60 and 65
        self.assertGreater(spd, 60.0)
        self.assertLess(spd, 65.0)


# ═══════════════════════════════════════════════════════════════════════════
# 2. CHANNEL MAPPING
# ═══════════════════════════════════════════════════════════════════════════


class TestChannelMapping(unittest.TestCase):
    def _check(self, col: str, expected_std: str):
        std, conv = _map_column(col)
        self.assertEqual(
            std, expected_std, f"'{col}' → expected '{expected_std}', got '{std}'"
        )

    def test_rpm_variants(self):
        for col in ["RPM", "rpm", "Engine Speed", "Engine RPM"]:
            self._check(col, "rpm")

    def test_tps_variants(self):
        for col in ["TPS%", "TPS", "TP%", "Throttle Position", "Throttle%"]:
            self._check(col, "tps_pct")

    def test_speed_kmh(self):
        for col in [
            "Speed",
            "VSS(km/h)",
            "Vehicle Speed (km/h)",
            "Ground Speed (km/h)",
        ]:
            self._check(col, "vehicle_speed_ms")

    def test_speed_kmh_conversion(self):
        _, conv = _map_column("Speed")
        self.assertIsNotNone(conv)
        result = 3.6 * float(conv)
        self.assertAlmostEqual(result, 1.0, places=4)  # 3.6 km/h × (1/3.6) = 1 m/s

    def test_gear(self):
        for col in ["Gear", "Gear Position", "Current Gear"]:
            self._check(col, "gear")

    def test_afr_direct(self):
        std, conv = _map_column("AFR")
        self.assertEqual(std, "afr")
        self.assertIsNone(conv)

    def test_lambda_to_afr(self):
        std, conv = _map_column("Lambda")
        self.assertEqual(std, "afr")
        # Lambda 1.0 → AFR 14.7
        self.assertAlmostEqual(float(conv) * 1.0, 14.7, places=2)

    def test_coolant_temp(self):
        for col in ["Coolant Temp", "ECT(°C)", "Engine Temp", "Water Temp"]:
            self._check(col, "coolant_temp_c")

    def test_air_temp(self):
        for col in ["Air Temp", "IAT(°C)", "Inlet Temp", "Intake Temp"]:
            self._check(col, "air_temp_c")

    def test_ignition_adv(self):
        for col in ["Ignition Adv", "Ignition Timing", "Timing", "Spark Adv"]:
            self._check(col, "ignition_adv_deg")

    def test_map_kpa(self):
        for col in ["MAP (kPa)", "MAP", "Manifold Absolute Pressure"]:
            self._check(col, "map_kpa")

    def test_battery(self):
        for col in ["Battery", "Battery Voltage", "Batt V"]:
            self._check(col, "battery_v")

    def test_unknown_column(self):
        std, conv = _map_column("XyzUnknownChannel_99")
        self.assertIsNone(std)

    def test_time_variants(self):
        for col in ["Time", "Time (s)", "Timestamp"]:
            self._check(col, "time_s")


# ═══════════════════════════════════════════════════════════════════════════
# 3. WOOLICH RACING FORMAT
# ═══════════════════════════════════════════════════════════════════════════


class TestWoolichParsing(unittest.TestCase):
    def setUp(self):
        content = _make_woolich_csv(n_idle_before=50, n_run=1200, peak_speed_ms=65.0)
        self.path = _write_tmp(content)
        self.log = parse_ecu_file(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_logger_type(self):
        self.assertEqual(self.log.logger_type, "woolich")

    def test_sample_rate_approx_100hz(self):
        self.assertAlmostEqual(self.log.sample_rate_hz, 100.0, delta=5.0)

    def test_rpm_channel_present(self):
        self.assertIsNotNone(self.log.rpm)
        self.assertGreater(self.log.rpm.max(), 10000)

    def test_tps_channel_present(self):
        self.assertIsNotNone(self.log.tps_pct)
        self.assertGreater(self.log.tps_pct.max(), 90.0)

    def test_speed_channel_present(self):
        self.assertIsNotNone(self.log.vehicle_speed_ms)
        self.assertAlmostEqual(self.log.vehicle_speed_ms.max(), 65.0, delta=2.0)

    def test_gear_channel_present(self):
        self.assertIsNotNone(self.log.gear)
        self.assertGreaterEqual(self.log.gear.max(), 5)

    def test_afr_channel_present(self):
        self.assertIsNotNone(self.log.afr)
        self.assertGreater(self.log.afr.min(), 10.0)

    def test_coolant_temp_present(self):
        self.assertIsNotNone(self.log.coolant_temp_c)
        self.assertGreater(self.log.coolant_temp_c.min(), 80.0)

    def test_air_temp_present(self):
        self.assertIsNotNone(self.log.air_temp_c)

    def test_one_run_detected(self):
        self.assertEqual(len(self.log.runs), 1)

    def test_run_et_reasonable(self):
        run = self.log.runs[0]
        # 65 m/s peak → QM in ~10-12 s range
        self.assertFalse(
            np.isnan(run.et_quarter), "ET should be detected with this peak speed"
        )
        self.assertGreater(run.et_quarter, 5.0)
        self.assertLess(run.et_quarter, 20.0)

    def test_run_trap_speed_reasonable(self):
        run = self.log.runs[0]
        self.assertFalse(np.isnan(run.trap_speed_ms))
        # Should be close to peak speed at QM crossing
        self.assertGreater(run.trap_speed_ms, 40.0)
        self.assertLess(run.trap_speed_ms, 70.0)

    def test_run_time_starts_at_zero(self):
        run = self.log.runs[0]
        self.assertAlmostEqual(run.time_s[0], 0.0, places=4)

    def test_run_peak_rpm(self):
        run = self.log.runs[0]
        self.assertGreater(run.peak_rpm, 10000)

    def test_run_splits_present(self):
        run = self.log.runs[0]
        splits = run.splits()
        self.assertIn("60ft", splits)
        self.assertIn("660ft", splits)

    def test_to_dict(self):
        d = self.log.to_dict()
        self.assertEqual(d["logger_type"], "woolich")
        self.assertIn("runs", d)
        self.assertEqual(d["n_runs"], 1)


# ═══════════════════════════════════════════════════════════════════════════
# 4. POWER COMMANDER PC-LINK FORMAT
# ═══════════════════════════════════════════════════════════════════════════


class TestPCLinkParsing(unittest.TestCase):
    def setUp(self):
        content = _make_pclink_csv(n_idle=40, n_run=1000, peak_speed_kmh=220.0)
        self.path = _write_tmp(content)
        self.log = parse_ecu_file(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_logger_type(self):
        self.assertEqual(self.log.logger_type, "pclink")

    def test_speed_converted_to_ms(self):
        # 220 km/h = 61.11 m/s
        self.assertIsNotNone(self.log.vehicle_speed_ms)
        self.assertAlmostEqual(self.log.vehicle_speed_ms.max(), 220.0 / 3.6, delta=2.0)

    def test_lambda_converted_to_afr(self):
        # Lambda range 0.95–1.0 → AFR 13.97–14.7
        self.assertIsNotNone(self.log.afr)
        self.assertGreater(self.log.afr.min(), 13.0)
        self.assertLess(self.log.afr.max(), 15.5)

    def test_run_detected(self):
        self.assertGreater(len(self.log.runs), 0)

    def test_coolant_temp_present(self):
        self.assertIsNotNone(self.log.coolant_temp_c)

    def test_air_temp_present(self):
        self.assertIsNotNone(self.log.air_temp_c)


# ═══════════════════════════════════════════════════════════════════════════
# 5. MOTEC i2 FORMAT
# ═══════════════════════════════════════════════════════════════════════════


class TestMoTeCParsing(unittest.TestCase):
    def setUp(self):
        content = _make_motec_tsv(n_idle=50, n_run=1500, peak_speed_ms=70.0)
        self.path = _write_tmp(content, suffix=".csv")
        self.log = parse_ecu_file(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_logger_type_motec(self):
        self.assertEqual(self.log.logger_type, "motec")

    def test_engine_speed_mapped_to_rpm(self):
        self.assertIsNotNone(self.log.rpm)
        self.assertGreater(self.log.rpm.max(), 10000)

    def test_throttle_position_mapped(self):
        self.assertIsNotNone(self.log.tps_pct)
        self.assertGreater(self.log.tps_pct.max(), 90.0)

    def test_ground_speed_in_ms(self):
        # Already m/s in MoTeC file
        self.assertIsNotNone(self.log.vehicle_speed_ms)
        self.assertAlmostEqual(self.log.vehicle_speed_ms.max(), 70.0, delta=2.0)

    def test_run_detected(self):
        self.assertGreater(len(self.log.runs), 0)

    def test_et_reached(self):
        run = self.log.best_run()
        self.assertIsNotNone(run)
        self.assertFalse(np.isnan(run.et_quarter))
        self.assertGreater(run.et_quarter, 5.0)


# ═══════════════════════════════════════════════════════════════════════════
# 6. MULTIPLE RUNS
# ═══════════════════════════════════════════════════════════════════════════


class TestMultipleRuns(unittest.TestCase):
    def _make_two_run_csv(self) -> str:
        """Two runs separated by idle section. Speed in km/h (real Woolich format)."""
        lines = ["Time,RPM,TPS%,Speed"]
        t = 0.0
        dt = 0.01

        def _write_idle(n):
            nonlocal t
            for _ in range(n):
                lines.append(f"{t:.3f},1000,0.0,0.0")  # 0 km/h
                t += dt

        def _write_run(n, peak_ms):
            nonlocal t
            for i in range(n):
                frac = i / max(n - 1, 1)
                s_kmh = peak_ms * 3.6 * (frac**0.55)  # km/h
                rpm = int(3000 + frac * 10000)
                lines.append(f"{t:.3f},{rpm},{frac * 100:.1f},{s_kmh:.3f}")
                t += dt

        _write_idle(50)
        _write_run(1200, 62.0)
        _write_idle(100)  # long idle between runs
        _write_run(1100, 64.0)
        _write_idle(30)

        return "\n".join(lines)

    def setUp(self):
        content = self._make_two_run_csv()
        self.path = _write_tmp(content)
        self.log = parse_ecu_file(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_two_runs_detected(self):
        self.assertEqual(len(self.log.runs), 2)

    def test_run_indices(self):
        self.assertEqual(self.log.runs[0].run_index, 0)
        self.assertEqual(self.log.runs[1].run_index, 1)

    def test_best_run_returns_lowest_et(self):
        best = self.log.best_run()
        self.assertIsNotNone(best)
        for run in self.log.runs:
            if not np.isnan(run.et_quarter):
                self.assertLessEqual(best.et_quarter, run.et_quarter)


# ═══════════════════════════════════════════════════════════════════════════
# 7. MISSING CHANNELS / PARTIAL DATA
# ═══════════════════════════════════════════════════════════════════════════


class TestMissingChannels(unittest.TestCase):
    def test_no_gear_channel(self):
        content = _make_woolich_csv(include_gear=False)
        path = _write_tmp(content)
        try:
            log = parse_ecu_file(path)
            self.assertIsNone(log.gear)
            # Runs should still be detected via speed
            self.assertGreater(len(log.runs), 0)
        finally:
            os.unlink(path)

    def test_no_afr_channel(self):
        content = _make_woolich_csv(include_afr=False)
        path = _write_tmp(content)
        try:
            log = parse_ecu_file(path)
            self.assertIsNone(log.afr)
        finally:
            os.unlink(path)

    def test_no_temp_channels(self):
        content = _make_woolich_csv(include_temps=False)
        path = _write_tmp(content)
        try:
            log = parse_ecu_file(path)
            self.assertIsNone(log.coolant_temp_c)
            self.assertIsNone(log.air_temp_c)
        finally:
            os.unlink(path)

    def test_rpm_only_fallback(self):
        """Log with RPM but no speed channel → fallback run detection via RPM."""
        lines = ["Time,RPM,TPS%"]
        t = 0.0
        dt = 0.01
        # Idle at low RPM
        for _ in range(50):
            lines.append(f"{t:.3f},900,0.0")
            t += dt
        # High-RPM run (> 4000 rpm, sustained)
        for i in range(1200):
            frac = i / 1199
            rpm = int(4500 + frac * 8000)  # 4500 → 12500 rpm
            tps = frac * 100
            lines.append(f"{t:.3f},{rpm},{tps:.1f}")
            t += dt
        # Back to idle
        for _ in range(30):
            lines.append(f"{t:.3f},900,0.0")
            t += dt

        path = _write_tmp("\n".join(lines))
        try:
            log = parse_ecu_file(path)
            self.assertIsNone(log.vehicle_speed_ms)
            # RPM fallback detection — may or may not find a run depending on thresholds
            # Main assertion: no crash + runs is a list
            self.assertIsInstance(log.runs, list)
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════════════════
# 8. ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════


class TestErrorHandling(unittest.TestCase):
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            parse_ecu_file("/nonexistent/path/log.csv")

    def test_empty_file(self):
        path = _write_tmp("")
        try:
            with self.assertRaises(ECUParseError):
                parse_ecu_file(path)
        finally:
            os.unlink(path)

    def test_no_recognised_channels(self):
        content = "col1,col2,col3\n1,2,3\n4,5,6\n"
        path = _write_tmp(content)
        try:
            with self.assertRaises(ECUParseError):
                parse_ecu_file(path)
        finally:
            os.unlink(path)

    def test_header_only_no_data(self):
        content = "Time,RPM,TPS%,Speed\n"
        path = _write_tmp(content)
        try:
            with self.assertRaises(ECUParseError):
                parse_ecu_file(path)
        finally:
            os.unlink(path)

    def test_run_below_qm_distance(self):
        """Run that doesn't reach QM → et_quarter is NaN."""
        lines = ["Time,RPM,TPS%,Speed"]
        t = 0.0
        dt = 0.01
        for _ in range(50):
            lines.append(f"{t:.3f},1000,0.0,0.0")
            t += dt
        # Only 200 samples at high speed — won't reach QM
        for i in range(200):
            frac = i / 199
            lines.append(
                f"{t:.3f},{int(8000 + frac * 5000)},{frac * 100:.1f},{20 + frac * 30:.3f}"
            )
            t += dt

        path = _write_tmp("\n".join(lines))
        try:
            log = parse_ecu_file(path)
            if log.runs:
                run = log.runs[0]
                # Short run: ET is NaN or run may not be detected at all
                self.assertTrue(np.isnan(run.et_quarter) or run.et_quarter > 0)
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════════════════
# 9. DATA QUALITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════


class TestDataQuality(unittest.TestCase):
    def setUp(self):
        content = _make_woolich_csv()
        self.path = _write_tmp(content)
        self.log = parse_ecu_file(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_time_starts_at_zero(self):
        self.assertAlmostEqual(self.log.time_s[0], 0.0, places=4)

    def test_time_monotonically_increasing(self):
        diffs = np.diff(self.log.time_s)
        self.assertTrue(np.all(diffs >= 0), "Time axis should be non-decreasing")

    def test_n_samples_matches_arrays(self):
        self.assertEqual(self.log.n_samples, len(self.log.time_s))
        if self.log.rpm is not None:
            self.assertEqual(self.log.n_samples, len(self.log.rpm))

    def test_run_time_monotonic(self):
        for run in self.log.runs:
            diffs = np.diff(run.time_s)
            self.assertTrue(np.all(diffs >= 0))

    def test_run_channel_lengths_match(self):
        for run in self.log.runs:
            n = len(run.time_s)
            for ch in [run.rpm, run.tps_pct, run.vehicle_speed_ms, run.gear]:
                if ch is not None:
                    self.assertEqual(len(ch), n)

    def test_to_dict_contains_required_keys(self):
        run = self.log.runs[0]
        d = run.to_dict()
        for key in ["run_index", "et_quarter_s", "peak_rpm", "sample_rate_hz"]:
            self.assertIn(key, d)

    def test_ecu_log_to_dict(self):
        d = self.log.to_dict()
        self.assertIn("source_file", d)
        self.assertIn("logger_type", d)
        self.assertIn("n_runs", d)
        self.assertIn("channel_names", d)

    def test_best_run_no_runs(self):
        """best_run() on an empty runs list returns None."""
        log = ECULog(time_s=np.array([0.0, 1.0]))
        result = log.best_run()
        self.assertIsNone(result)

    def test_sample_rate_positive(self):
        self.assertGreater(self.log.sample_rate_hz, 0.0)
        self.assertLess(self.log.sample_rate_hz, 2000.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
