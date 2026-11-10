"""2026-10 epoch, ROUND 3 — reports/acc_epoch3_2026_11_03.json agrees with the
code that is checked in.

* the report keeps the round-2 report shape (acc_final_2026_08_08.json
  headline keys + trap / 60 ft / top speed / (a) (b) (c) / HEAD-membership
  cluster table / mass gate / CV record / reference fit / decomposition) and
  adds the per-cluster residual SD vs HEAD and the within-band counts;
* the old-vs-new chain starts at the EXACT published 2026-08-08 metric
  (HEAD labels, legacy binding + weights: 276 / 0.2629 / +0.0073);
* every tuned knob set in the report is exactly what
  motoquant/category_profiles.py ships (wheelie_margin included), inside the
  round-3 bounds, and launch_rpm_factor is set only by the families that may
  set it ('margin+lr' under the 1-SE rule, 'grip+margin+lr' = gate escape);
* the reference fit is the shipped reference profile and the references
  simulate to the report's pinned ETs;
* the shipped set is the owner's choice for litre_sport_195p
  ('alt_litre195_margin', 2026-11-05): the gate records exactly the two
  accepted dry-mass inversions (HP4 Race, Panigale V4R) and no litre bike
  traction-limited above 2nd gear; the tuner's own gate-escape selection
  is preserved as a record;
* (native engine, or MOTOQUANT_SLOW_TESTS=1) a full re-measure of the
  shipped code reproduces the newest published reports/acc_final_*.json
  (ET headline under all three scorings, trap, top speed) and the accepted
  dry-mass inversions. This report's own headline predates later catalog
  changes and is history.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from motoquant import category_profiles as cp, engine_select
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "acc_epoch3_2026_11_03.json"
KNOBS = (
    "over_clutch_factor",
    "max_engine_decel_rads2",
    "launch_floor_factor",
    "mu_peak_override",
    "mu_peak_scale",
    "parasitic_mult",
    "launch_rpm_factor",
    "cd_floor",
    "wheelie_margin",
)
LR_FAMILIES = {"margin+lr", "grip+margin+lr"}
#: Dry-mass inversions accepted with the owner's litre_sport_195p choice.
ACCEPTED_INVERSIONS = {"Ducati Panigale V4R", "BMW HP4 Race"}


@pytest.fixture(scope="module")
def report():
    return json.loads(REPORT.read_text())


def _tuner():
    name = "_t_epoch3_tuner"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / "tune_epoch3_2026_11_03.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_report_shape(report):
    for key in ("references", "n_bikes_swept", "clusters", "overall"):
        assert key in report
    for key in (
        "trap_overall",
        "t60_overall",
        "topspeed",
        "by_rules",
        "headline",
        "clusters_head_membership_published_metric",
        "mass_gate",
        "old_vs_new",
        "decomposition",
        "tuning",
        "reference_fit",
        "acceptance",
        "bands_vs_head",
        "residual_sd_vs_head",
    ):
        assert key in report, key
    assert set(report["headline"]) == {
        "a_epoch_current_row",
        "a_epoch_current_1ft",
        "b_legacy_current_row",
        "c_legacy_head_row",
        "c_legacy_head_1ft",
    }
    assert report["overall"] == report["headline"]["a_epoch_current_row"]["overall"]


def test_chain_starts_at_the_published_metric(report):
    head = report["old_vs_new"]["head"]["headline"]["c_legacy_head_row"]["overall"]
    assert (head["n"], head["w_mean_abs"], head["w_bias"]) == (276, 0.2629, 0.0073)
    acc = report["acceptance"]["et_published_metric_c"]
    assert acc["published_head"] == 0.2629
    assert (
        acc["value"] == report["headline"]["c_legacy_head_row"]["overall"]["w_mean_abs"]
    )


def test_report_knobs_are_the_shipped_knobs(report):
    clusters = report["tuning"]["clusters"]
    assert clusters
    for tag, rec in clusters.items():
        prof = cp.get_profile(tag)
        assert prof.name == tag
        assert {k: getattr(prof, k) for k in KNOBS} == rec["theta"], tag


def test_knobs_inside_the_round3_bounds(report):
    for tag, rec in report["tuning"]["clusters"].items():
        th = rec["theta"]
        assert 0.97 <= th["mu_peak_scale"] <= 1.10, tag
        assert 0.65 <= th["wheelie_margin"] <= 1.0, tag
        assert th["mu_peak_override"] is None
        assert th["over_clutch_factor"] == 0.0 and th["launch_floor_factor"] == 0.0
        assert th["parasitic_mult"] == 1.0
        if th["launch_rpm_factor"] is not None:
            assert rec["selected"] in LR_FAMILIES, tag
            assert 0.45 <= th["launch_rpm_factor"] <= 0.75, tag


def test_reference_fit_is_the_shipped_reference_profile(report):
    best = report["reference_fit"]["best"]
    prof = cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P)
    assert prof.mu_peak_scale == best["mu_peak_scale"]
    assert prof.wheelie_margin == best["wheelie_margin"]
    assert prof.launch_rpm_factor is None
    assert best["all_within_tol"] and best["order_ok"]
    assert all(v["monotone"] for v in best["mass_gate"].values())


def test_references_simulate_to_the_report(report):
    for label, fn in (
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ):
        r = engine_select.make_engine(fn()).run(max_time=26.0)
        assert float(r.time_quarter) == report["references_full"][label]["et_s_full"]
        assert round(float(r.time_quarter), 4) == report["references"][label]


def test_report_gate(report):
    g = report["mass_gate"]
    assert g["catalog"]["inversions"] == len(ACCEPTED_INVERSIONS)
    assert {x["name"] for x in g["catalog"]["inverted"]} == ACCEPTED_INVERSIONS
    assert all(x["cluster"] == "litre_sport_195p" for x in g["catalog"]["inverted"])
    assert all(v["monotone"] for v in g["references"].values())
    assert g["litre_traction_above_2nd"]["n_any"] == 0
    for probe in ("rider", "sea_dry", "sea_rider"):
        assert probe in g["probes"]  # reported (target zero, listed if not)


def test_gate_constrained_clusters_are_recorded(report):
    """Every cluster whose unconstrained choice failed the gate carries the
    constrained record and its point is gate-feasible."""
    for tag, rec in report["tuning"]["clusters"].items():
        if rec.get("selected") in ("thin", "unbound"):
            continue
        if rec.get("owner_decision"):
            continue  # shipped by owner decision; see test_owner_decision_recorded
        if not rec.get("gate_tried") or rec["gate_tried"][-1]["inversions"] == 0:
            continue
        assert "feasible" in rec, tag
        pt = rec["point"]
        key = f"{pt[0]:.2f}|{pt[1]:.2f}|{pt[2]}"
        assert key in rec["feasible"]["points"], (tag, key)


@pytest.mark.skipif(
    not engine_select.native_active() and os.environ.get("MOTOQUANT_SLOW_TESTS") != "1",
    reason="full re-measure needs the Rust core (seconds) or MOTOQUANT_SLOW_TESTS=1",
)
def test_full_remeasure_reproduces_the_published_report():
    """A full re-measure of the shipped code reproduces the newest
    reports/acc_final_*.json, the report every public accuracy figure is
    taken from. (This report, acc_epoch3, is a record of its day: the
    catalog changed after it, so its own headline is no longer reproducible
    and is not compared.)"""
    final = json.loads(
        sorted((ROOT / "reports").glob("acc_final_*.json"))[-1].read_text()
    )
    t3 = _tuner()
    t3.TE.setup_root(None)
    res = t3.T2.measure(
        {k: v for k, v in t3.T2.SCORINGS.items() if v[0] == "current"},
        procs=1,
        head=None,
        topspeed=True,
        gate=True,
    )
    published = {
        "a_epoch_current_row": final,
        "a_epoch_current_1ft": final["timing_uniform_1ft"],
        "b_legacy_current_row": final["by_rules"]["legacy"],
    }
    for name, rec in published.items():
        got = res["scorings"][name]
        assert got["overall"] == rec["overall"], name
        trap = rec["trap_overall"]
        for key in ("n", "w_mean_abs_kmh", "w_bias_kmh"):
            assert got["trap_overall"][key] == trap[key], (name, key)
        # the sweep and the tuner round the unweighted trap mean separately
        assert (
            abs(got["trap_overall"]["raw_mean_abs_kmh"] - trap["raw_mean_abs_kmh"])
            <= 0.011
        )
    # plateau_count counts different populations in the two tools
    ts = {k: v for k, v in res["topspeed"]["summary"].items() if k != "plateau_count"}
    assert ts == {k: v for k, v in final["topspeed"].items() if k != "plateau_count"}
    assert {x["name"] for x in res["mass_gate"]["catalog"]["inverted"]} == (
        ACCEPTED_INVERSIONS
    )


def test_owner_decision_recorded(report):
    """litre_sport_195p ships the CV 'margin' choice by owner decision; the
    tuner's gate-escape selection is kept verbatim as a record, and the
    shipped headline equals the tune-time alt_litre195_margin measurement."""
    rec = report["tuning"]["clusters"]["litre_sport_195p"]
    od = rec["owner_decision"]
    assert od["shipped"] == "alt_litre195_margin" and od["date"] == "2026-11-05"
    assert set(od["accepted_residuals"]) == ACCEPTED_INVERSIONS
    assert rec["point"] == [1.0, 0.69, None]
    tuner = rec["tuner_selected"]
    assert tuner["selected"] == "grip+margin+lr"
    assert tuner["point"] == [1.05, 0.97, 0.475]
    alts = report["conservative_alternatives"]
    assert "alt_gate_escape_tuner_choice" in alts
    assert (
        alts["alt_litre195_margin"]["thetas_applied"]["litre_sport_195p"]
        == rec["theta"]
    )
    for name, h in alts["alt_litre195_margin"]["headline"].items():
        assert report["headline"][name]["overall"] == h["overall"], name
    assert "shipped_2026_11_05" in report["notes"]
