"""2026-10 epoch, ROUND 2 — the tuner and sweep scripts.

Pins scripts/tune_epoch2_2026_10_29.py's selection mechanics (bounds, the
neutral tie-break, constrained CV, the zero-tolerance gate, the donor guard
helpers, the 66-ft trap, per-row timing binding) and the per-row timing
convention in scripts/phys_weighted_sweep.py and scripts/tune_cluster_knobs.py.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from motoquant.defaults import gsxr1000_k5  # noqa: E402
from motoquant.engine_select import make_engine  # noqa: E402
from scripts import (  # noqa: E402
    phys_weighted_sweep as pws,
    sweep_lib,
    tune_cluster_knobs as tck,
)
from scripts.validation_sweep import BENCHMARKS  # noqa: E402


@pytest.fixture(scope="module")
def t2():
    spec = importlib.util.spec_from_file_location(
        "_t_epoch2_scripts", ROOT / "scripts" / "tune_epoch2_2026_10_29.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.TE.setup_root(None)
    return mod


# ── search space ────────────────────────────────────────────────────────────


def test_grids_are_the_physical_bounds(t2):
    assert t2.MU_GRID[0] == 0.95 and t2.MU_GRID[-1] == 1.15
    assert all(abs(b - a - 0.01) < 1e-9 for a, b in zip(t2.MU_GRID, t2.MU_GRID[1:]))
    lr = [x for x in t2.LR_GRID_4T if x is not None]
    assert t2.LR_GRID_4T[0] is None
    assert lr[0] == 0.45 and lr[-1] == 0.75
    assert t2.LR_GRID_2T == [None]  # a two-stroke launches on its pipe
    assert t2.lr_grid("two_stroke") == [None]
    assert set(t2.family_points("grip+lr", "litre_sport_195p")) >= {
        (1.0, None),
        (0.95, 0.45),
        (1.15, 0.75),
    }


def test_neutral_wins_inside_the_flat_band(t2):
    J = {(1.0, None): 0.5000, (0.97, None): 0.4995, (0.95, 0.5): 0.30}
    # within EPS of the best the most neutral point wins
    assert t2.pick([(1.0, None), (0.97, None)], J.get) == (1.0, None)
    # a real improvement is taken
    assert t2.pick(list(J), J.get) == (0.95, 0.5)
    assert t2.ndist((1.0, None)) == 0.0
    assert t2.ndist((1.0, 0.55)) > t2.ndist((0.9, None))  # launch rpm costs more
    assert t2.complexity_pt((1.0, None)) == 0
    assert t2.complexity_pt((0.95, 0.5)) == 2


def test_cv_select_respects_the_allowed_set(t2):
    rows = [
        {
            "target_et": 10.0,
            "target_trap": None,
            "weight": 1.0,
            "bench_key": f"k{i}",
        }
        for i in range(10)
    ]
    grid = {pt: [(10.4, None, None)] * 10 for pt in t2.family_points("grip+lr", "x")}
    grid[(0.95, 0.5)] = [(10.0, None, None)] * 10  # perfect, but not allowed
    grid[(1.05, 0.475)] = [(10.1, None, None)] * 10
    free = t2.cv_select("x", rows, grid, 0.01, 5)
    assert free["families"]["grip+lr"]["point"] == [0.95, 0.5]
    con = t2.cv_select("x", rows, grid, 0.01, 5, allowed={(1.05, 0.475)})
    assert set(con["families"]) == {"grip+lr"}  # no other family has a point
    assert con["families"]["grip+lr"]["point"] == [1.05, 0.475]
    assert con["candidate_order"][0] == "grip+lr"


def test_gate_ok_has_zero_tolerance(t2):
    assert t2._gate_ok({"inversions": 0, "min_margin_s": 0.0})
    assert t2._gate_ok({"inversions": 0, "min_margin_s": None})
    # the probe's own 1e-4 s tolerance would pass this; selection does not
    assert not t2._gate_ok({"inversions": 0, "min_margin_s": -3e-05})
    assert not t2._gate_ok({"inversions": 1, "min_margin_s": 0.01})


def _inv(name, kind, et, plus, minus):
    return {
        "name": name,
        "kind": kind,
        "et": et,
        "et_plus10": plus,
        "et_minus10": minus,
    }


def test_no_worse_than_neutral(t2):
    neu = {
        "point": [1.0, None],
        "family": "neutral",
        "inverted": [_inv("HP4", ["-10kg slower"], 9.187, 9.193, 9.192)],
    }
    smaller = {
        "point": [1.0, 0.5],
        "family": "launch",
        "inverted": [_inv("HP4", ["-10kg slower"], 9.240, 9.249, 9.243)],
    }
    worse = {
        "point": [0.95, 0.525],
        "family": "grip+lr",
        "inverted": [_inv("HP4", ["+10kg faster", "-10kg slower"], 9.36, 9.35, 9.37)],
    }
    assert t2.no_worse_than_neutral([worse, smaller, neu])["point"] == [1.0, 0.5]
    assert t2.no_worse_than_neutral([worse]) is None


def test_traction_above_second_gear(t2):
    lim = {
        "1": {"steps": 100, "traction_frac": 0.5, "wheelie_frac": 0.4},
        "2": {"steps": 100, "traction_frac": 0.2, "wheelie_frac": 0.0},
        "3": {"steps": 300, "traction_frac": 0.1, "wheelie_frac": 0.0},
        "4": {"steps": 100, "traction_frac": 0.0, "wheelie_frac": 0.0},
        "all": {"steps": 600, "traction_frac": 0.15, "wheelie_frac": 0.07},
    }
    assert t2.traction_above_2nd(lim) == pytest.approx(0.075)
    assert t2.traction_above_2nd(None) is None


def test_trap_66ft_is_the_strip_average(t2):
    r = make_engine(gsxr1000_k5()).run(max_time=26.0)
    t66 = t2._trap_66ft(r, 402.336)
    v_end = r.speed_quarter * 3.6
    # an accelerating bike averages less than its finish-line speed
    assert v_end - 4.0 < t66 < v_end
    et, trap, t60, trap66 = t2.sim_quarter(gsxr1000_k5(), sweep_lib.ROLLOUT_1FT_M)
    assert et == r.time_quarter and trap66 == t66
    et0, *_ = t2.sim_quarter(gsxr1000_k5(), 0.0)
    assert et0 > et  # first-motion timing includes the first foot


def test_bind_rows_carry_the_row_timing_convention(t2):
    rows = t2.bind_rows("epoch", t2.CTX["benchmarks"])
    assert len(rows) > 250
    for r in rows:
        conv, basis = sweep_lib.timing_convention_meta(r["source"])
        assert (r["timing"], r["timing_basis"]) == (conv, basis)
        assert r["rollout_m"] == sweep_lib.rollout_m_for_source(r["source"])
    assert {r["timing"] for r in rows} == {"rollout_1ft", "first_motion"}


def test_head_key_and_load_thetas(t2, tmp_path):
    assert t2._head_key("BMW", "HP4 Race", 2017) == "bmw|hp4 race|2017"
    p = tmp_path / "th.json"
    p.write_text('{"thetas": {"other": {"mu_peak_scale": 0.97}}}')
    assert t2.load_thetas(str(p)) == {"other": {"mu_peak_scale": 0.97}}


# ── per-row timing in the sweep scripts ─────────────────────────────────────

_FM_SRC = "Otomotif Racelogic instrumented 402m comparo (Indonesia)"


def test_phys_weighted_sweep_scores_each_row_under_its_convention():
    rec = {"sim_et": 15.0, "sim_et_first_motion": 15.4}
    assert pws.scored_sim_et(rec, "Sport Rider 2009") == (15.0, False)
    assert pws.scored_sim_et(rec, _FM_SRC) == (15.4, False)
    assert pws.scored_sim_et(rec, _FM_SRC, timing="1ft") == (15.0, False)
    # a pre-round-2 chunk without the rollout-0 run: counted fallback
    assert pws.scored_sim_et({"sim_et": 15.0}, _FM_SRC) == (15.0, True)


def test_phys_weighted_sweep_counts_timing_fallbacks():
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    rows = []
    for s in ALL_KNOWN_BIKES:
        rows.append(
            {
                "manufacturer": s.manufacturer,
                "model": s.model_name,
                "year_from": s.year_from,
                "year_to": s.year_to,
                "disp_cc": s.displacement_cc,
                "power_hp": s.peak_power_hp,
                "stroke_type": s.stroke_type or 4,
                "category": s.category,
                "cylinders": s.cylinders,
                "sim_et": 12.0,
                "sim_trap_kmh": 200.0,
            }
        )
    old = pws.score_rows(rows, "epoch")
    assert old["timing"] == "row" and old["n_timing_fallback"] > 0
    for r in rows:
        r["sim_et_first_motion"] = 12.3
    new = pws.score_rows(rows, "epoch")
    assert new["n_timing_fallback"] == 0
    # the first-motion rows now score 0.3 s slower; nothing else moves
    assert new["overall"]["w_bias"] > old["overall"]["w_bias"]
    uni = pws.score_rows(rows, "epoch", timing="1ft")
    assert uni["overall"] == old["overall"]


def test_tune_cluster_knobs_matches_carry_the_row_rollout():
    for m in tck.build_matches("epoch"):
        assert m["rollout_m"] == sweep_lib.rollout_m_for_source(m["source"])


@pytest.mark.skipif(
    os.environ.get("MOTOQUANT_ENGINE", "auto") == "python",
    reason="spot-check on the selected engine",
)
def test_tune_cluster_knobs_sims_the_row_rollout():
    ms = [m for m in tck.build_matches("epoch") if m["rollout_m"] == 0.0][:1]
    assert ms, "the corpus has first-motion rows"
    i = ms[0]["i"]
    fm = tck._sim_one((i, 0.0, {}))[1][0]
    ro = tck._sim_one((i, sweep_lib.ROLLOUT_1FT_M, {}))[1][0]
    assert fm > ro


def test_corpus_still_has_first_motion_rows():
    srcs = {row[5] for row in BENCHMARKS}
    assert any(sweep_lib.timing_convention(s) == "first_motion" for s in srcs)
