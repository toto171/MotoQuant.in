"""
Fix-wave regressions — CLI (motoquant/run.py).

Drives main() / the subcommand handlers against a temp copy of the shipped
motoquant.db (plus one real subprocess for the exit status). Each test fails
on the pre-fix code:

* a successful `sim` returned its SimResult from main(); sys.exit() printed
  the ~4 KB repr to stderr and exited 1;
* `bikes --fitments ID` crashed (BikeRepository has no .get());
* `calibrate overlay --bike-id N` swallowed an ImportError and always
  simulated the K5 reference without saying so;
* `analysis surrogate ... --bike-id` queried a nonexistent 'bikes' table;
* `run_bike` capped the sim at 20 s, so bikes slower than that (RX100,
  20.85 s) reported a 0.0 s quarter mile;
* CLI sims bypassed motoquant.engine_select.
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest

from motoquant import engine_select
from motoquant.run import main

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    dst = tmp_path_factory.mktemp("cli_db") / "motoquant.db"
    shutil.copy(REPO / "motoquant.db", dst)
    return str(dst)


def _model_id(db_path: str, name_like: str) -> int:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT bm.id FROM bike_models bm JOIN bike_configs bc "
            "ON bc.bike_model_id = bm.id AND bc.is_current = 1 "
            "AND bc.config_name = 'stock' WHERE bm.model_name LIKE ? "
            "ORDER BY bm.id LIMIT 1",
            (name_like,),
        ).fetchone()
    assert row, f"no catalog bike like {name_like!r}"
    return int(row[0])


def _cli(db_path, *argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["--db", db_path, *argv])
    return rc, buf.getvalue()


@pytest.fixture()
def gps_run(tmp_path):
    """A Dragy CSV of a ~9.6 s quarter mile."""
    rate = 10.0
    t = np.arange(int(18 * rate)) / rate
    v = np.where(t < 3.0, 0.0, np.minimum(60.0, 10.0 * (t - 3.0)))
    p = tmp_path / "run.csv"
    p.write_text(
        "Time (s),Speed (km/h)\n"
        + "\n".join(f"{a:.2f},{b * 3.6:.3f}" for a, b in zip(t, v))
        + "\n"
    )
    return str(p)


# ─── 1. sim exit status ───────────────────────────────────────────────────


def test_main_returns_int_status_for_successful_sim(db_path):
    rc, out = _cli(db_path, "sim", "--bike-id", "1", "--quiet", "--json")
    assert rc == 0  # was the SimResult object
    assert json.loads(out)["splits"]["quarter_mile_s"] > 0


def test_sim_subprocess_exits_zero_with_clean_stderr(db_path):
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "motoquant.run",
            "--db",
            db_path,
            "sim",
            "--bike-id",
            "1",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
        timeout=300,
        env={**os.environ, "PYTHONPATH": str(REPO)},
    )
    assert proc.returncode == 0, proc.stderr[:500]
    assert "SimResult(" not in proc.stderr


# ─── 2. bikes --fitments ──────────────────────────────────────────────────


def test_bikes_fitments_lists_tires(db_path):
    rc, out = _cli(db_path, "bikes", "--fitments", "1")
    assert rc in (0, None)
    assert "Tire Fitments for" in out


def test_bikes_fitments_unknown_bike_is_an_error(db_path):
    rc, out = _cli(db_path, "bikes", "--fitments", "99999999")
    assert rc == 1
    assert "no bike found" in out


# ─── 3. calibrate overlay --bike-id ───────────────────────────────────────


def test_overlay_simulates_the_requested_bike(db_path, gps_run):
    rx100 = _model_id(db_path, "RX100%")
    busa = 3  # reference Hayabusa row
    rc_a, out_a = _cli(
        db_path, "calibrate", "overlay", gps_run, "--bike-id", str(rx100), "--json"
    )
    rc_b, out_b = _cli(
        db_path, "calibrate", "overlay", gps_run, "--bike-id", str(busa), "--json"
    )
    assert rc_a == rc_b == 0
    a, b = json.loads(out_a), json.loads(out_b)
    assert "RX100" in a["bike"] and "Hayabusa" in b["bike"]
    # RX100 ~20.9 s vs Hayabusa ~10.5 s (both printed the K5's 9.9331 s)
    assert a["et_sim_s"] - b["et_sim_s"] > 5.0


def test_overlay_text_report_names_the_bike(db_path, gps_run):
    rc, out = _cli(db_path, "calibrate", "overlay", gps_run, "--bike-id", "3")
    assert rc == 0
    assert "Simulated bike:" in out and "Hayabusa" in out


def test_overlay_unknown_bike_is_an_error_not_a_k5_fallback(db_path, gps_run):
    rc, out = _cli(db_path, "calibrate", "overlay", gps_run, "--bike-id", "99999999")
    assert rc == 1
    assert "no config found" in out


# ─── 4. analysis surrogate --bike-id ──────────────────────────────────────


def test_surrogate_generate_with_bike_id(db_path, tmp_path):
    out_npz = tmp_path / "s.npz"
    rc, out = _cli(
        db_path,
        "analysis",
        "surrogate",
        "generate",
        "--bike-id",
        "3",
        "--n-samples",
        "2",
        "--output",
        str(out_npz),
    )
    assert rc == 0, out
    assert out_npz.exists()


# ─── 5. slow bikes get their real ET ──────────────────────────────────────


def test_slow_bike_quarter_mile_is_reported(db_path):
    rx100 = _model_id(db_path, "RX100%")
    rc, out = _cli(db_path, "sim", "--bike-id", str(rx100), "--quiet", "--json")
    assert rc == 0
    d = json.loads(out)
    assert d["splits"]["quarter_mile_s"] > 20.0  # was 0.0 (20 s cap)
    assert d["simulation"]["finished_quarter"] is True


# ─── 6. engine selection ──────────────────────────────────────────────────


def test_cli_sims_go_through_engine_select(db_path, gps_run, monkeypatch):
    calls = {"n": 0}
    real_make = engine_select.make_engine

    def counting(cfg, dt=0.001):
        calls["n"] += 1
        return real_make(cfg, dt=dt)

    monkeypatch.setattr(engine_select, "make_engine", counting)
    _cli(db_path, "sim", "--bike-id", "1", "--quiet", "--json")
    assert calls["n"] >= 1
    before = calls["n"]
    _cli(db_path, "calibrate", "overlay", gps_run, "--bike-id", "3", "--json")
    assert calls["n"] == before + 1


def test_engine_subcommand_reports_selection(db_path):
    rc, out = _cli(db_path, "engine", "--json")
    assert rc == 0
    info = json.loads(out)
    assert info["engine"] in ("native", "python")
    assert info["mode"] in ("auto", "python", "native", "invalid")
