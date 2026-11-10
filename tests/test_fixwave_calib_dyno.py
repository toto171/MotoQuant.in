"""
Fix-wave regressions — dyno import + SAE J1349 (motoquant/calibration/dyno.py).

Production paths exercised: parse_dyno_file (shared by the CLI and the API),
`calibrate import-dyno` via cmd_calibrate, and POST /api/calibrate/dyno.
Every test fails on the pre-fix code:

* DynoJet's documented 'RPM,WHP,TQ' export (TQ in lb-ft) was read as Nm, so
  the injected torque curve — the thing the sim consumes — was 26% low;
* pressure entered in inHg (DynoJet sheets print 29.92) or bar was taken as
  kPa (CF 3.3 / 97.7), and RH 150 % or a lone temperature were accepted;
* the 'SAE J1349' factor omitted the standard's 1.18 / −0.18 terms.
"""

import argparse
import io
import math
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest

from motoquant.calibration import dyno
from motoquant.calibration.dyno import (
    DynoParseError,
    parse_dyno_file,
    sae_j1349_correction_factor,
)

LBFT_TO_NM = 1.35582
HP_TO_KW = 0.745699872


def _consistent_curve():
    """A physically consistent run: true peak ≈ 95 Nm / ≈ 122 hp."""
    rpm = np.arange(3000, 12001, 250).astype(float)
    tq_nm = 60.0 + 35.0 * np.exp(-(((rpm - 8500.0) / 3000.0) ** 2))
    kw = tq_nm * rpm * 2 * math.pi / 60 / 1000
    return rpm, tq_nm, kw


def _write(path: Path, header: str, rows) -> Path:
    path.write_text(header + "\n" + "\n".join(rows) + "\n")
    return path


@pytest.fixture()
def dynojet_csv(tmp_path):
    rpm, tq_nm, kw = _consistent_curve()
    rows = [
        f"{r:.0f},{k / HP_TO_KW:.2f},{t / LBFT_TO_NM:.2f}"
        for r, t, k in zip(rpm, tq_nm, kw)
    ]
    return _write(tmp_path / "dynojet.csv", "RPM,WHP,TQ", rows)


def _curve_implied_kw(result):
    return float(np.max(result.curve.torque_nm * result.rpm * 2 * math.pi / 60 / 1000))


# ─── 1. Torque unit of an unlabelled 'TQ' column ──────────────────────────


def test_dynojet_tq_column_is_read_as_lbft(dynojet_csv):
    _, tq_nm, kw = _consistent_curve()
    r = parse_dyno_file(dynojet_csv)
    assert r.peak_torque_nm == pytest.approx(tq_nm.max(), rel=0.02)
    # The injected curve must carry the file's power (was 26% low).
    assert _curve_implied_kw(r) == pytest.approx(kw.max(), rel=0.02)
    assert r.raw_metadata.get("torque_unit_inferred") == "lbft"


def test_unlabelled_torque_that_is_nm_stays_nm(tmp_path):
    rpm, tq_nm, kw = _consistent_curve()
    rows = [f"{r:.0f},{k:.3f},{t:.3f}" for r, t, k in zip(rpm, tq_nm, kw)]
    p = _write(tmp_path / "nm.csv", "RPM,Power (kW),TQ", rows)
    r = parse_dyno_file(p)
    assert r.peak_torque_nm == pytest.approx(tq_nm.max(), rel=0.02)
    assert r.raw_metadata.get("torque_unit_inferred") == "nm"


def test_labelled_unit_wins_but_mismatch_is_recorded(tmp_path):
    """An explicit '(Nm)' label is trusted, but a 26% power/torque disagreement
    is surfaced instead of silently feeding a wrong curve."""
    rpm, tq_nm, kw = _consistent_curve()
    rows = [
        f"{r:.0f},{k / HP_TO_KW:.2f},{t / LBFT_TO_NM:.2f}"
        for r, t, k in zip(rpm, tq_nm, kw)
    ]
    p = _write(tmp_path / "mislabelled.csv", "RPM,WHP,Torque (Nm)", rows)
    r = parse_dyno_file(p)
    assert r.peak_torque_nm == pytest.approx(tq_nm.max() / LBFT_TO_NM, rel=0.02)
    assert r.raw_metadata["power_torque_mismatch_pct"] > 20


def test_api_dyno_upload_reports_lbft_torque_in_nm(dynojet_csv):
    from fastapi.testclient import TestClient

    from motoquant.api import app

    _, tq_nm, _ = _consistent_curve()
    r = TestClient(app).post(
        "/api/calibrate/dyno",
        files={
            "file": ("dynojet.csv", io.BytesIO(dynojet_csv.read_bytes()), "text/csv")
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["peak_torque_nm"] == pytest.approx(tq_nm.max(), rel=0.02)


# ─── 2. Ambient-input validation and unit auto-detection ──────────────────


@pytest.mark.parametrize("pressure", [29.92, 1.0132, 1013.2, 14.696])
def test_inhg_bar_hpa_psi_pressures_are_converted(dynojet_csv, pressure):
    ref = parse_dyno_file(dynojet_csv, temp_c=25.0, pressure_kpa=101.32)
    r = parse_dyno_file(dynojet_csv, temp_c=25.0, pressure_kpa=pressure)
    assert r.correction_factor == pytest.approx(ref.correction_factor, abs=2e-3)
    assert 0.9 < r.correction_factor < 1.1  # inHg used to give CF 3.31
    assert "pressure_input_note" in r.raw_metadata


@pytest.mark.parametrize(
    "kw",
    [
        {"temp_c": 25.0, "pressure_kpa": 50.0},  # no unit makes this plausible
        {"temp_c": 25.0, "pressure_kpa": 101.3, "rh_pct": 150.0},
        {"temp_c": 77.0, "pressure_kpa": 101.3},  # °F typed as °C
        {"temp_c": 25.0, "pressure_kpa": float("nan")},
        {"temp_c": 25.0},  # pressure missing: was silently uncorrected
        {"pressure_kpa": 101.3},
    ],
)
def test_implausible_or_partial_ambient_is_rejected(dynojet_csv, kw):
    with pytest.raises(dyno.DynoInputError):
        parse_dyno_file(dynojet_csv, **kw)
    assert issubclass(dyno.DynoInputError, DynoParseError)
    assert issubclass(dyno.DynoInputError, ValueError)


def test_correction_factor_function_validates_its_inputs():
    with pytest.raises(ValueError):
        sae_j1349_correction_factor(25.0, 29.92, 0.0)  # inHg passed as kPa
    with pytest.raises(ValueError):
        sae_j1349_correction_factor(25.0, 101.3, 120.0)


def test_cli_import_dyno_rejects_bad_pressure(dynojet_csv):
    from motoquant.run import cmd_calibrate

    args = argparse.Namespace(
        cal_command="import-dyno",
        file=str(dynojet_csv),
        temp=25.0,
        pressure=5.0,
        rh=0.0,
        crank=False,
        output_json=False,
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_calibrate(args)
    assert rc == 1
    assert "Invalid ambient conditions" in buf.getvalue()


def test_cli_import_dyno_converts_inhg_and_says_so(dynojet_csv):
    from motoquant.run import cmd_calibrate

    args = argparse.Namespace(
        cal_command="import-dyno",
        file=str(dynojet_csv),
        temp=25.0,
        pressure=29.92,
        rh=0.0,
        crank=False,
        output_json=False,
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_calibrate(args)
    out = buf.getvalue()
    assert rc == 0
    assert "inHg" in out
    peak_hp = float(out.split("kW  (")[1].split(" hp")[0])
    assert peak_hp < 140  # 3.3x inflation printed ~405 hp


def test_api_dyno_rejects_implausible_pressure(dynojet_csv):
    from fastapi.testclient import TestClient

    from motoquant.api import app

    r = TestClient(app).post(
        "/api/calibrate/dyno",
        files={"file": ("d.csv", io.BytesIO(dynojet_csv.read_bytes()), "text/csv")},
        data={"temp_c": "25", "pressure_kpa": "5", "rh_pct": "0"},
    )
    assert r.status_code == 422


# ─── 3. SAE J1349 per the standard ────────────────────────────────────────


def test_j1349_includes_mechanical_efficiency_terms():
    """35 °C / 95 kPa / 60 % RH: J1349 = 1.116; the friction-free form gave 1.098."""
    assert sae_j1349_correction_factor(35.0, 95.0, 60.0) == pytest.approx(
        1.1160, abs=5e-4
    )
    assert sae_j1349_correction_factor(25.0, 99.0, 0.0) == pytest.approx(1.0, abs=1e-12)


def test_corrected_import_applies_the_standard_factor(dynojet_csv):
    raw = parse_dyno_file(dynojet_csv)
    corr = parse_dyno_file(dynojet_csv, temp_c=35.0, pressure_kpa=95.0, rh_pct=60.0)
    assert corr.peak_power_kw / raw.peak_power_kw == pytest.approx(1.1160, abs=5e-4)
