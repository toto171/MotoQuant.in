"""2026-10 epoch retune — reports/acc_epoch_2026_10_24.json agrees with the
code that is checked in.

* the report keeps the reports/acc_final_2026_08_08.json headline shape
  (references / n_bikes_swept / clusters / overall) plus trap, top-speed,
  both rule sets, CV record, reference fit and the decomposition;
* every tuned knob set in the report is exactly what
  motoquant/category_profiles.py ships (report and code cannot drift apart);
* the references simulate to the report's pinned ETs;
* (native engine, or MOTOQUANT_SLOW_TESTS=1) a full re-measure reproduces
  the report's ET, trap and top-speed headline exactly.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from motoquant import (
    category_profiles as cp,  # noqa: E402
    engine_select,  # noqa: E402
)
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402

REPORT = ROOT / "reports" / "acc_epoch_2026_10_24.json"
_KNOBS = (
    "over_clutch_factor",
    "max_engine_decel_rads2",
    "launch_floor_factor",
    "mu_peak_override",
    "mu_peak_scale",
    "parasitic_mult",
    "launch_rpm_factor",
    "cd_floor",
)


@pytest.fixture(scope="module")
def report():
    return json.loads(REPORT.read_text())


def test_report_shape(report):
    for key in ("references", "n_bikes_swept", "clusters", "overall"):
        assert key in report  # acc_final_2026_08_08.json headline shape
    for key in (
        "trap_overall",
        "topspeed",
        "by_rules",
        "old_vs_new",
        "decomposition",
        "tuning",
        "reference_fit",
        "lambda_sensitivity",
    ):
        assert key in report, key
    assert set(report["by_rules"]) == {"epoch", "legacy"}
    assert report["rules"] == "epoch"
    assert report["overall"] == report["by_rules"]["epoch"]["overall"]
    # the old-vs-new chain starts at the published 2026-08-08 headline
    head = report["old_vs_new"]["head"]["legacy_rules"]["overall"]
    assert (head["n"], head["w_mean_abs"], head["w_bias"]) == (276, 0.2629, 0.0073)


def test_report_knobs_are_the_shipped_knobs(report):
    clusters = report["tuning"]["clusters"]
    assert clusters, "tuning record empty"
    for tag, rec in clusters.items():
        prof = cp.get_profile(tag)
        assert prof.name == tag
        shipped = {k: getattr(prof, k) for k in _KNOBS}
        assert shipped == rec["theta"], tag


def test_report_reference_fit_is_the_shipped_reference_profile(report):
    best = report["reference_fit"]["best"]
    prof = cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P)
    assert prof.mu_peak_scale == best["mu_peak_scale"]
    assert prof.launch_rpm_factor == best["launch_rpm_factor"]
    assert best["all_within_tol"] and best["order_ok"]


def test_references_simulate_to_the_report(report):
    for label, fn in (
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ):
        et = engine_select.make_engine(fn()).run(max_time=26.0).time_quarter
        assert float(et) == report["references_full"][label]["et_s_full"], label
        assert round(float(et), 4) == report["references"][label]


@pytest.mark.skipif(
    not engine_select.native_active() and os.environ.get("MOTOQUANT_SLOW_TESTS") != "1",
    reason="full re-measure needs the Rust core (seconds) or MOTOQUANT_SLOW_TESTS=1",
)
def test_full_remeasure_reproduces_the_report(report):
    from scripts import tune_epoch_2026_10_24 as te

    te.setup_root(None)
    res = te.measure(["epoch", "legacy"], procs=1, topspeed=True)
    for pol in ("epoch", "legacy"):
        assert res[pol]["overall"] == report["by_rules"][pol]["overall"], pol
        assert res[pol]["trap_overall"] == report["by_rules"][pol]["trap"], pol
    assert res["topspeed"]["summary"] == report["topspeed"]
