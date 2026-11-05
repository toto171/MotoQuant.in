"""2026-10 epoch, ROUND 2 — reports/acc_epoch2_2026_10_29.json is internally
consistent and REPRODUCIBLE on the current code.

Round 2 was superseded by round 3 (reports/acc_epoch3_2026_11_03.json,
tests/test_epoch3_tune_report.py pins THAT report against the shipped
profiles). Round 3 only ADDED a knob (``CategoryProfile.wheelie_margin``,
1.0 = bit-identical no-op), so applying the round-2 knob sets with
wheelie_margin 1.0 must still reproduce this report exactly — which is what
the checks below now do (``_round2_profiles``).

* the report keeps the reports/acc_final_2026_08_08.json headline shape
  (references / n_bikes_swept / clusters / overall) plus trap, 60 ft, top
  speed, the three headline metrics (a) / (b) / (c), the HEAD-membership
  cluster table, the mass gate, the CV record, the reference fit and the
  decomposition;
* the old-vs-new chain starts at the EXACT published 2026-08-08 metric
  (HEAD labels, legacy binding + weights: 276 / 0.2629 / +0.0073);
* every tuned knob set in the report is a complete round-2 knob set and the
  reference fit is the report's reference theta;
* the references simulate to the report's pinned ETs and the gate recorded
  zero inversions;
* (native engine, or MOTOQUANT_SLOW_TESTS=1) a full re-measure reproduces the
  report's ET / trap / top-speed headline and the gate exactly.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib.util
import json
import os
from pathlib import Path

import pytest

from motoquant import category_profiles as cp, engine_select
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "acc_epoch2_2026_10_29.json"
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


@contextlib.contextmanager
def _round2_profiles(report):
    """Every profile at the report's round-2 knobs, wheelie_margin 1.0."""
    saved = dict(cp._PROFILES)
    thetas = {t: r["theta"] for t, r in report["tuning"]["clusters"].items()}
    best = report["reference_fit"]["best"]
    try:
        for tag, prof in saved.items():
            th = thetas.get(tag, {})
            kw = {k: th[k] for k in _KNOBS if k in th}
            if tag == cp.CATEGORY_REFERENCE_LITRE_195P:
                kw.update(
                    mu_peak_scale=best["mu_peak_scale"],
                    launch_rpm_factor=best["launch_rpm_factor"],
                )
            cp._PROFILES[tag] = dataclasses.replace(prof, **kw, wheelie_margin=1.0)
        yield
    finally:
        cp._PROFILES.clear()
        cp._PROFILES.update(saved)


def _tuner():
    spec = importlib.util.spec_from_file_location(
        "_t_epoch2_tuner", ROOT / "scripts" / "tune_epoch2_2026_10_29.py"
    )
    mod = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_report_shape(report):
    for key in ("references", "n_bikes_swept", "clusters", "overall"):
        assert key in report  # acc_final_2026_08_08.json headline shape
    for key in (
        "trap_overall",
        "trap66_overall",
        "t60_overall",
        "topspeed",
        "by_rules",
        "headline",
        "clusters_head_membership_published_metric",
        "mass_gate",
        "old_vs_new",
        "decomposition",
        "tuning",
        "lambda_sensitivity",
        "reference_fit",
        "conservative_alternatives",
        "acceptance",
        "notes",
    ):
        assert key in report, key
    assert report["rules"] == "epoch" and report["timing"] == "row"
    assert set(report["by_rules"]) == {"epoch", "legacy"}
    assert report["overall"] == report["headline"]["a_epoch_current_row"]["overall"]
    assert set(report["headline"]) == {
        "a_epoch_current_row",
        "a_epoch_current_1ft",
        "b_legacy_current_row",
        "c_legacy_head_row",
        "c_legacy_head_1ft",
    }


def test_chain_starts_at_the_published_metric(report):
    head = report["old_vs_new"]["head"]["headline"]["c_legacy_head_row"]["overall"]
    assert (head["n"], head["w_mean_abs"], head["w_bias"]) == (276, 0.2629, 0.0073)
    c = report["headline"]["c_legacy_head_row"]["overall"]
    assert c["n"] == 276  # the same 276 bindings on the round-2 catalog
    acc = report["acceptance"]["et_published_metric_c"]
    assert acc["published_head"] == 0.2629
    assert acc["value"] == c["w_mean_abs"]


def test_report_knobs_are_complete_round2_knob_sets(report):
    clusters = report["tuning"]["clusters"]
    assert clusters
    for tag, rec in clusters.items():
        assert tag in cp._PROFILES, tag
        assert set(rec["theta"]) == set(_KNOBS), tag


def test_report_reference_fit_is_inside_round2_bounds(report):
    best = report["reference_fit"]["best"]
    assert 0.95 <= best["mu_peak_scale"] <= 1.15
    assert best["launch_rpm_factor"] is None or (
        0.45 <= best["launch_rpm_factor"] <= 0.75
    )
    assert best["order_ok"]
    assert all(v["monotone"] for v in best["mass_gate"].values())


def test_references_simulate_to_the_report(report):
    """Round-2 reference knobs + wheelie_margin 1.0 = the round-2 ETs, bit
    for bit (round 3's knob is a no-op at 1.0)."""
    with _round2_profiles(report):
        for label, fn in (
            ("K5", gsxr1000_k5),
            ("R1", yzfr1_4c8),
            ("Hayabusa", hayabusa_gen1),
        ):
            et = engine_select.make_engine(fn()).run(max_time=26.0).time_quarter
            assert float(et) == report["references_full"][label]["et_s_full"], label
            assert round(float(et), 4) == report["references"][label]


def test_report_gate_is_clean(report):
    g = report["mass_gate"]
    assert g["catalog"]["inversions"] == 0
    assert all(v["monotone"] for v in g["references"].values())
    assert g["litre_traction_above_2nd"]["max"] <= 0.05
    assert report["acceptance"]["mass_inversions"]["pass_zero"] is True


def test_constrained_selection_is_recorded(report):
    """litre_sport_195p was selected over the gate-feasible points only; the
    record keeps the unconstrained choice and its inversion."""
    rec = report["tuning"]["clusters"]["litre_sport_195p"]
    assert rec["feasible"]["n_feasible"] >= 1
    assert "constrained_cv" in rec
    assert any(t["inversions"] for t in rec["gate_tried"])
    key = f"{rec['point'][0]:.2f}|{rec['point'][1]}"
    assert key in rec["feasible"]["points"]
    assert rec["feasible"]["points"][key]["min_margin_s"] >= 0.0


@pytest.mark.skipif(
    not engine_select.native_active() and os.environ.get("MOTOQUANT_SLOW_TESTS") != "1",
    reason="full re-measure needs the Rust core (seconds) or MOTOQUANT_SLOW_TESTS=1",
)
def test_full_remeasure_reproduces_the_report(report):
    te2 = _tuner()
    te2.TE.setup_root(None)
    head_dump = None  # (c) needs the HEAD corpus dump — compare (a) and (b)
    with _round2_profiles(report):
        res = te2.measure(
            {k: v for k, v in te2.SCORINGS.items() if v[0] == "current"},
            procs=1,
            head=head_dump,
            topspeed=True,
            gate=True,
        )
    for name in ("a_epoch_current_row", "a_epoch_current_1ft", "b_legacy_current_row"):
        h = report["headline"][name]
        assert res["scorings"][name]["overall"] == h["overall"], name
        assert res["scorings"][name]["trap_overall"] == h["trap"], name
    assert res["topspeed"]["summary"] == report["topspeed"]
    assert res["mass_gate"]["catalog"]["inversions"] == 0
