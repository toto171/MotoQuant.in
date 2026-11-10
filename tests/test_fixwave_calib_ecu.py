"""
Fix-wave regressions — ECU log import (motoquant/calibration/ecu.py).

Production paths exercised: parse_ecu_file and `calibrate import-ecu`
(cmd_calibrate). Every test fails on the pre-fix code:

* header units were thrown away before matching, so 'Speed (mph)' and
  'Vehicle Speed (m/s)' were read as km/h, 'Coolant Temp (F)' as °C and
  'MAP (psi)' as kPa;
* a comma CSV whose header starts 'Vehicle…' was taken for a MoTeC
  preamble, and one text column ('Lap Name') rejected every row;
* with no time column a 1-second axis was invented (16 s log → "1900 Hz");
* run extraction re-scanned trailing idle windows from every index (O(n²));
* the MoTeC path dropped its first real sample.
"""

import argparse
import io
import json
import time
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest

from motoquant.calibration.ecu import ECUParseError, parse_ecu_file

RATE = 100.0


def _run(idle_s=3.0, dur=16.0, tail_idle_s=0.0):
    n_idle, n_run, n_tail = int(idle_s * RATE), int(dur * RATE), int(tail_idle_s * RATE)
    t = np.arange(n_idle + n_run + n_tail) / RATE
    v = np.zeros_like(t)
    v[n_idle : n_idle + n_run] = np.minimum(58.0, 9.0 * np.arange(n_run) / RATE)
    rpm = np.where(v > 0, 6000 + v * 100, 1500.0)
    return t, v, rpm


def _write(path: Path, header, rows) -> Path:
    path.write_text(",".join(header) + "\n" + "\n".join(",".join(r) for r in rows))
    return path


@pytest.fixture()
def kmh_log(tmp_path):
    t, v, rpm = _run()
    rows = [
        [f"{a:.2f}", f"{b:.0f}", "100", f"{c * 3.6:.3f}", "90", "100"]
        for a, b, c in zip(t, rpm, v)
    ]
    return _write(
        tmp_path / "kmh.csv",
        ["Time", "RPM", "TPS%", "Speed (km/h)", "Coolant Temp (C)", "MAP (kPa)"],
        rows,
    )


@pytest.fixture()
def ref_et(kmh_log):
    run = parse_ecu_file(kmh_log).best_run()
    assert run is not None and np.isfinite(run.et_quarter)
    return run.et_quarter


# ─── 1. Units written in the header are honoured ──────────────────────────


def test_mph_speed_fahrenheit_and_psi_columns(tmp_path, ref_et):
    t, v, rpm = _run()
    rows = [
        [f"{a:.2f}", f"{b:.0f}", "100", f"{c / 0.44704:.4f}", "194", "14.5"]
        for a, b, c in zip(t, rpm, v)
    ]
    p = _write(
        tmp_path / "mph.csv",
        ["Time", "RPM", "TPS%", "Speed (mph)", "Coolant Temp (F)", "MAP (psi)"],
        rows,
    )
    log = parse_ecu_file(p)
    assert log.best_run().et_quarter == pytest.approx(ref_et, abs=0.01)
    assert log.coolant_temp_c[0] == pytest.approx(90.0, abs=0.01)  # 194 °F
    assert log.map_kpa[0] == pytest.approx(14.5 * 6.89476, abs=0.01)


def test_metres_per_second_speed_column(tmp_path, ref_et):
    t, v, rpm = _run()
    rows = [[f"{a:.2f}", f"{b:.0f}", "100", f"{c:.4f}"] for a, b, c in zip(t, rpm, v)]
    p = _write(
        tmp_path / "ms.csv", ["Time", "RPM", "TPS%", "Vehicle Speed (m/s)"], rows
    )
    run = parse_ecu_file(p).best_run()
    assert run.et_quarter == pytest.approx(ref_et, abs=0.01)  # was nan


def test_cli_import_ecu_json_uses_header_units(tmp_path, ref_et):
    from motoquant.run import cmd_calibrate

    t, v, rpm = _run()
    rows = [
        [f"{a:.2f}", f"{b:.0f}", "100", f"{c / 0.44704:.4f}"]
        for a, b, c in zip(t, rpm, v)
    ]
    p = _write(tmp_path / "vss.csv", ["Time", "RPM", "TPS%", "VSS (mph)"], rows)
    args = argparse.Namespace(
        cal_command="import-ecu",
        file=str(p),
        best=False,
        channels=False,
        output_json=True,
        sample_rate=None,
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cmd_calibrate(args) == 0
    out = json.loads(buf.getvalue())
    assert out["runs"][0]["et_quarter_s"] == pytest.approx(ref_et, abs=0.01)


# ─── 2. Realistic headers / text columns ──────────────────────────────────


def test_csv_header_starting_with_vehicle_is_not_motec(tmp_path, ref_et):
    t, v, rpm = _run()
    rows = [
        [f"{c * 3.6:.3f}", f"{a:.2f}", f"{b:.0f}", "100"] for a, b, c in zip(t, rpm, v)
    ]
    p = _write(
        tmp_path / "veh.csv", ["Vehicle Speed (km/h)", "Time", "RPM", "TPS%"], rows
    )
    log = parse_ecu_file(p)
    assert log.logger_type != "motec"
    assert log.best_run().et_quarter == pytest.approx(ref_et, abs=1e-9)


def test_text_column_does_not_reject_every_row(tmp_path, ref_et):
    t, v, rpm = _run()
    rows = [
        [f"{a:.2f}", f"{b:.0f}", "100", f"{c * 3.6:.3f}", "Q1", "N" if c == 0 else "3"]
        for a, b, c in zip(t, rpm, v)
    ]
    p = _write(
        tmp_path / "text.csv",
        ["Time", "RPM", "TPS%", "Speed (km/h)", "Lap Name", "Gear"],
        rows,
    )
    log = parse_ecu_file(p)
    assert log.n_samples == len(t)
    assert log.best_run().et_quarter == pytest.approx(ref_et, abs=1e-9)
    assert "lap_name" not in log.extra_channels  # an all-text channel is dropped
    assert np.isnan(log.gear[0]) and log.gear[-1] == 3.0  # 'N' → NaN, not row loss


def test_no_time_column_requires_a_sample_rate(tmp_path, ref_et):
    t, v, rpm = _run()
    rows = [[f"{b:.0f}", "100", f"{c * 3.6:.3f}"] for b, c in zip(rpm, v)]
    p = _write(tmp_path / "notime.csv", ["RPM", "TPS%", "Speed (km/h)"], rows)
    with pytest.raises(ECUParseError, match="no time column"):
        parse_ecu_file(p)
    log = parse_ecu_file(p, sample_rate_hz=RATE)
    assert log.sample_rate_hz == pytest.approx(RATE)
    assert log.best_run().et_quarter == pytest.approx(ref_et, abs=0.02)


def test_cli_import_ecu_sample_rate_flag(tmp_path):
    from motoquant.run import build_parser, cmd_calibrate

    t, v, rpm = _run()
    rows = [[f"{b:.0f}", "100", f"{c * 3.6:.3f}"] for b, c in zip(rpm, v)]
    p = _write(tmp_path / "notime.csv", ["RPM", "TPS%", "Speed (km/h)"], rows)
    args = build_parser().parse_args(
        ["calibrate", "import-ecu", str(p), "--sample-rate", "100", "--json"]
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cmd_calibrate(args) == 0
    assert json.loads(buf.getvalue())["sample_rate_hz"] == pytest.approx(100.0)


# ─── 3. Linear run extraction ─────────────────────────────────────────────


@pytest.mark.parametrize("with_speed", [True, False])
def test_idle_log_parses_in_linear_time(tmp_path, with_speed):
    """12k idle rows: ~15 s on the old O(n²) scan (speed and RPM paths)."""
    n = 12_000
    if with_speed:
        header = ["Time", "RPM", "TPS%", "Speed (km/h)"]
        rows = [[f"{i / RATE:.2f}", "1500", "0", "0.0"] for i in range(n)]
    else:
        header = ["Time", "RPM", "TPS%"]
        rows = [[f"{i / RATE:.2f}", "1500", "0"] for i in range(n)]
    p = _write(tmp_path / "idle.csv", header, rows)
    t0 = time.perf_counter()
    log = parse_ecu_file(p)
    assert log.runs == []
    assert time.perf_counter() - t0 < 3.0


def test_run_followed_by_idle_tail_still_found(tmp_path, ref_et):
    t, v, rpm = _run(tail_idle_s=60.0)
    rows = [
        [f"{a:.2f}", f"{b:.0f}", "100", f"{c * 3.6:.3f}"] for a, b, c in zip(t, rpm, v)
    ]
    p = _write(tmp_path / "tail.csv", ["Time", "RPM", "TPS%", "Speed (km/h)"], rows)
    t0 = time.perf_counter()
    log = parse_ecu_file(p)
    assert len(log.runs) == 1
    assert log.runs[0].et_quarter == pytest.approx(ref_et, abs=1e-9)
    assert time.perf_counter() - t0 < 2.0


# ─── 4. MoTeC keeps every data row ────────────────────────────────────────


def test_motec_first_data_row_is_kept():
    import os

    from tests.test_ecu import _make_motec_tsv, _write_tmp

    path = _write_tmp(_make_motec_tsv(n_idle=50, n_run=1500))
    try:
        log = parse_ecu_file(path)
    finally:
        os.unlink(path)
    assert log.logger_type == "motec"
    assert log.n_samples == 50 + 1500 + 20  # was one short
    assert log.time_s[0] == 0.0
