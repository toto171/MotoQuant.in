"""
Fix-wave regressions — Dragy GPS import (motoquant/calibration/dragy.py).

Each test drives the production parser (parse_dragy_file, the function the
CLI `calibrate import-dragy` and POST /api/calibrate/dragy both call) and
fails on the pre-fix code:

* run detection was O(windows x N): every staged window re-integrated the
  whole rest of the file and re-took the median sample rate;
* one blank / null speed cell desynced the t and v arrays (numpy broadcast
  ValueError) instead of skipping the row; a top-level JSON list raised
  AttributeError;
* CSV units were read from the JOINED header (an 'Accel (m/s2)' column made
  mph speeds be read as m/s) and single-letter candidates matched as
  substrings ('t' picked the Distance column as time);
* multi-run JSON numbered its runs 0, 2, 4;
* a launch that stopped short of 402 m was integrated straight through the
  stop and the relaunch into a bogus extra run.
"""

import argparse
import io
import json
import math
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest

from motoquant.calibration import dragy
from motoquant.calibration.dragy import (
    QUARTER_MILE_M,
    DragParseError,
    _col_index,
    _integrate_distance,
    _interpolate_et,
    parse_dragy_file,
)

# ─── Synthetic data ───────────────────────────────────────────────────────


def _run_arrays(rate=10.0, idle_s=3.0, accel=10.0, vmax=60.0, dur=15.0, t0=0.0):
    """Idle, then a ramp to vmax: reaches 402 m in ~9.6 s at the defaults."""
    n_idle = int(idle_s * rate)
    ts = [t0 + i / rate for i in range(n_idle)]
    vs = [0.0] * n_idle
    tl = t0 + n_idle / rate
    for i in range(int(dur * rate)):
        tt = i / rate
        ts.append(tl + tt)
        vs.append(min(vmax, accel * tt))
    return np.array(ts), np.array(vs)


def _write_csv(path: Path, header: str, rows) -> Path:
    path.write_text(header + "\n" + "\n".join(rows) + "\n")
    return path


def _kmh_rows(t, v):
    return [f"{a:.2f},{b * 3.6:.3f}" for a, b in zip(t, v)]


@pytest.fixture()
def ref_et(tmp_path):
    """ET of the clean km/h reference file."""
    t, v = _run_arrays()
    p = _write_csv(tmp_path / "ref.csv", "Time (s),Speed (km/h)", _kmh_rows(t, v))
    runs = parse_dragy_file(p)
    assert len(runs) == 1
    return runs[0].et_quarter


# ─── 1. Run detection is linear (DoS) ─────────────────────────────────────


def _write_dos(path: Path, n_rows: int) -> Path:
    """5 zero-speed rows + 1 row at 40 m/s, repeated: one staged window per 6 rows."""
    rows = []
    t = 0.0
    for i in range(n_rows):
        rows.append(f"{t:.2f},{40.0 if i % 6 == 5 else 0.0}")
        t += 0.1
    return _write_csv(path, "Time (s),Speed (m/s)", rows)


def test_detection_work_is_linear_in_file_length(tmp_path, monkeypatch):
    """Total samples integrated must stay O(N), not O(windows x N).

    The pre-fix detector integrated the whole remainder of the file for each
    of the ~N/6 staged windows (~N^2/12 samples: 300M for this 60k-row file)
    and re-took the full-file median sample rate per window.
    """
    n_rows = 60_000
    p = _write_dos(tmp_path / "dos.csv", n_rows)

    integrated = {"samples": 0}
    rate_calls = {"n": 0}
    real_integrate = dragy._integrate_distance
    real_rate = dragy._detect_sample_rate

    def counting_integrate(t, v):
        integrated["samples"] += len(t)
        return real_integrate(t, v)

    def counting_rate(t):
        rate_calls["n"] += 1
        return real_rate(t)

    monkeypatch.setattr(dragy, "_integrate_distance", counting_integrate)
    monkeypatch.setattr(dragy, "_detect_sample_rate", counting_rate)

    runs = parse_dragy_file(p)

    assert runs == []  # every "run" is a 4 m spike — none is a quarter mile
    assert integrated["samples"] <= 3 * n_rows, integrated
    assert rate_calls["n"] == 1, rate_calls


def test_crafted_upload_parses_fast(tmp_path):
    """Wall-clock guard on the same attack shape (old code: ~40 s at 120k rows)."""
    import time

    p = _write_dos(tmp_path / "dos120k.csv", 120_000)
    t0 = time.perf_counter()
    assert parse_dragy_file(p) == []
    assert time.perf_counter() - t0 < 10.0


def test_file_over_sample_cap_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(dragy, "MAX_SAMPLES", 1000)
    t, v = _run_arrays(rate=100.0, dur=15.0)  # 1800 rows
    p = _write_csv(tmp_path / "long.csv", "Time (s),Speed (km/h)", _kmh_rows(t, v))
    with pytest.raises(DragParseError, match="more than"):
        parse_dragy_file(p)


def test_real_sample_cap_is_far_above_real_sessions():
    # 25 Hz for 1 h is 90k samples; the cap must never bite a real export.
    assert dragy.MAX_SAMPLES >= 100_000


# ─── 2. Malformed rows skip the row, never crash ──────────────────────────


def test_blank_speed_cell_skips_row(tmp_path, ref_et):
    t, v = _run_arrays()
    rows = _kmh_rows(t, v)
    rows[50] = f"{t[50]:.2f},"  # blank speed cell mid-run
    p = _write_csv(tmp_path / "blank.csv", "Time (s),Speed (km/h)", rows)
    runs = parse_dragy_file(p)
    assert len(runs) == 1
    assert runs[0].et_quarter == pytest.approx(ref_et, abs=0.05)
    r = runs[0]
    assert len(r.timestamps) == len(r.velocity_ms) == len(r.distance_m)


def test_null_json_speed_skips_sample(tmp_path, ref_et):
    t, v = _run_arrays()
    samples = [{"t": float(a), "speed_kmh": float(b * 3.6)} for a, b in zip(t, v)]
    samples[50]["speed_kmh"] = None
    p = tmp_path / "null.json"
    p.write_text(json.dumps({"runs": [{"samples": samples}]}))
    runs = parse_dragy_file(p)
    assert len(runs) == 1
    assert runs[0].et_quarter == pytest.approx(ref_et, abs=0.05)


@pytest.mark.parametrize(
    "payload",
    [
        [{"t": 0.0, "speed_kmh": 0.0}],  # top-level list
        {"runs": "nope"},
        {"runs": [5]},
        {"runs": [{"samples": [1, 2, 3]}]},
    ],
)
def test_bad_json_shape_raises_parse_error(tmp_path, payload):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(DragParseError):
        parse_dragy_file(p)


def test_cli_import_dragy_reports_bad_json_cleanly(tmp_path):
    """The CLI path used to surface a raw AttributeError traceback."""
    from motoquant.run import cmd_calibrate

    p = tmp_path / "list.json"
    p.write_text(json.dumps([{"t": 0.0, "speed_kmh": 0.0}]))
    args = argparse.Namespace(
        cal_command="import-dragy", file=str(p), best=False, output_json=False
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_calibrate(args)
    assert rc == 1
    assert "Parse error" in buf.getvalue()


def test_api_upload_with_blank_cell_parses(ref_et):
    """POST /api/calibrate/dragy: was a 422 with the numpy broadcast message."""
    from fastapi.testclient import TestClient

    from motoquant.api import app

    t, v = _run_arrays()
    rows = _kmh_rows(t, v)
    rows[40] = f"{t[40]:.2f},"
    body = ("Time (s),Speed (km/h)\n" + "\n".join(rows) + "\n").encode()
    r = TestClient(app).post(
        "/api/calibrate/dragy",
        files={"file": ("blank.csv", io.BytesIO(body), "text/csv")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["best_run"]["et_quarter_s"] == pytest.approx(ref_et, abs=0.05)


# ─── 3. Column / unit detection ───────────────────────────────────────────


def test_accel_ms2_column_does_not_flip_mph_speed(tmp_path, ref_et):
    """'m/s' in ANOTHER column's label read every mph value as m/s (ET 5.9 s)."""
    t, v = _run_arrays()
    rows = [f"{a:.2f},{b / 0.44704:.4f},0.0" for a, b in zip(t, v)]
    p = _write_csv(tmp_path / "acc.csv", "Time (s),Speed (mph),Accel (m/s2)", rows)
    runs = parse_dragy_file(p)
    assert len(runs) == 1
    assert runs[0].et_quarter == pytest.approx(ref_et, abs=0.01)


def test_elapsed_time_column_is_not_shadowed_by_distance(tmp_path, ref_et):
    """'t' substring-matched 'Distance' before 'elapsed' was tried (ET 26.3 s)."""
    t, v = _run_arrays()
    d = _integrate_distance(t, v)
    rows = [f"{a:.2f},{b * 3.6:.3f},{c:.3f}" for a, b, c in zip(t, v, d)]
    p = _write_csv(tmp_path / "el.csv", "Elapsed,Speed (km/h),Distance (m)", rows)
    runs = parse_dragy_file(p)
    assert len(runs) == 1
    assert runs[0].et_quarter == pytest.approx(ref_et, abs=0.01)


def test_single_letter_candidates_match_exactly():
    header = ["Time (s)", "Speed (km/h)", "Distance (m)"]
    assert _col_index(header, ["d"]) == -1  # used to match 'Speed'
    assert _col_index(["t", "v", "d"], ["d"]) == 2
    assert _col_index(["t (s)", "v (m/s)"], ["t"]) == 0
    assert _col_index(header, ["distance"]) == 2


# ─── 4. Multi-run JSON indices ────────────────────────────────────────────


def test_multi_run_json_indices_are_sequential(tmp_path):
    runs_json = []
    for k in range(3):
        t, v = _run_arrays(accel=10.0 - k)
        runs_json.append(
            {
                "samples": [
                    {"t": float(a), "speed_kmh": float(b * 3.6)} for a, b in zip(t, v)
                ]
            }
        )
    p = tmp_path / "multi.json"
    p.write_text(json.dumps({"meta": {}, "runs": runs_json}))
    runs = parse_dragy_file(p)
    assert [r.run_index for r in runs] == [0, 1, 2]
    assert [r.to_dict()["run_index"] for r in runs] == [0, 1, 2]


# ─── 5. Aborted runs are not integrated through the stop ─────────────────


def test_aborted_launch_is_not_reported_as_a_run(tmp_path):
    """Launch, stop at ~300 m, re-stage, relaunch: exactly one run — the relaunch."""
    rate = 10.0
    # aborted: idle 3 s, ramp to 30 m/s, cruise, brake to 0 well before 402 m
    t1, v1 = _run_arrays(rate=rate, idle_s=3.0, accel=6.0, vmax=30.0, dur=12.0)
    v1[-20:] = 0.0  # stopped for 2 s at the end
    d1 = _integrate_distance(t1, v1)[-1]
    assert d1 < QUARTER_MILE_M
    t2, v2 = _run_arrays(rate=rate, idle_s=2.0, t0=t1[-1] + 1 / rate)
    t = np.concatenate([t1, t2])
    v = np.concatenate([v1, v2])
    p = _write_csv(tmp_path / "abort.csv", "Time (s),Speed (km/h)", _kmh_rows(t, v))

    runs = parse_dragy_file(p)
    assert len(runs) == 1

    # ...and it is the relaunch, with the ET it has on its own.
    p2 = _write_csv(tmp_path / "second.csv", "Time (s),Speed (km/h)", _kmh_rows(t2, v2))
    alone = parse_dragy_file(p2)
    assert len(alone) == 1
    assert runs[0].et_quarter == pytest.approx(alone[0].et_quarter, abs=1e-9)


# ─── 6. Accepted runs keep exactly the per-launch integration ────────────


def test_et_equals_integration_from_the_launch_frame(tmp_path):
    """The prefix-sum detector must report the same ET (to the bit) as
    integrating v(t) from the launch frame, which is what the old detector
    did for every accepted run."""
    t, v = _run_arrays(rate=25.0)
    v = v + np.where(v > 0, 0.03 * np.sin(np.arange(len(v))), 0.0)
    runs = dragy._detect_runs(t, v, _integrate_distance(t, v))
    assert len(runs) == 1
    launch, _end, et, _trap = runs[0]
    t_run = t[launch:] - t[launch]
    d_run = _integrate_distance(t_run, v[launch:])
    assert et == _interpolate_et(t_run, d_run, QUARTER_MILE_M)
    assert math.isfinite(et) and 5.0 < et < 30.0
