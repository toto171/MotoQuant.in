"""2026-10 epoch, round 2 — scripts/gen_accuracy_viz_data.py delegates binding
AND source weights to the published sweep's rule set.

Before round 2 the /validation dataset bound catalog bikes with its own copy
of the LEGACY rule (first in-range entry, else the group's first entry of any
year) and then weighted them with the EPOCH classifier — a rule mix the
headline never used (on the round-1 tree: 276 rows / w|d| 0.2473 in the
explorer vs 266 / 0.2480 in the headline). Pins:

* ``bind_record`` == ``phys_weighted_sweep.bind`` for every catalog bike under
  both rule sets;
* ``main()`` on a sweep's chunk files reproduces
  ``phys_weighted_sweep.score_rows`` exactly (n, w|d|, bias) and keeps its
  output schema;
* a bike bound only by the legacy rule is not in the epoch dataset;
* first-motion rows are scored on the matching run when the sweep stored it.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts import (
    gen_accuracy_viz_data as gav,  # noqa: E402
    phys_weighted_sweep as pws,  # noqa: E402
)
from scripts.sweep_lib import build_bench_map  # noqa: E402
from scripts.validation_sweep import BENCHMARKS  # noqa: E402

BIKE_KEYS = {
    "make",
    "model",
    "year",
    "disp_cc",
    "real_et",
    "sim_et",
    "delta",
    "abs_delta",
    "real_trap",
    "sim_trap",
    "cluster",
    "cluster_label",
    "source",
    "weight",
    "quality",
}


def _rec(spec, sim_et=12.0, **extra):
    return {
        "manufacturer": spec.manufacturer,
        "model": spec.model_name,
        "year_from": spec.year_from,
        "year_to": spec.year_to,
        "disp_cc": spec.displacement_cc,
        "power_hp": spec.peak_power_hp,
        "stroke_type": getattr(spec, "stroke_type", 4) or 4,
        "category": getattr(spec, "category", None),
        "cylinders": getattr(spec, "cylinders", None),
        "finished": True,
        "sim_et": sim_et,
        "sim_trap_kmh": 180.0,
        **extra,
    }


@pytest.mark.parametrize("rules", ["epoch", "legacy"])
def test_bind_record_is_the_sweep_binding(rules):
    bm = build_bench_map(BENCHMARKS)
    n = 0
    for spec in ALL_KNOWN_BIKES:
        rec = _rec(spec)
        got = gav.bind_record(rec, bm, rules)
        assert got == pws.bind(rec, bm, rules), spec.model_name
        n += got is not None
    assert n > 250


def test_headline_rules_are_the_default():
    assert gav.HEADLINE_RULES == pws.HEADLINE_RULES == "epoch"


def test_legacy_only_binding_is_not_in_the_epoch_dataset():
    bm = build_bench_map(BENCHMARKS)
    spec = next(s for s in ALL_KNOWN_BIKES if s.model_name == "R 12 nineT")
    assert gav.bind_record(_rec(spec), bm, "epoch") is None
    assert gav.bind_record(_rec(spec), bm, "legacy") is not None


def test_scored_sim_et_matches_the_row_convention():
    fm_src = "Otomotif Racelogic instrumented 402m comparo (Indonesia)"
    assert gav.scored_sim_et({"sim_et": 15.0}, "Sport Rider 2009") == (15.0, False)
    # first-motion row, sweep without the rollout-0 run: explicit fallback
    assert gav.scored_sim_et({"sim_et": 15.0}, fm_src) == (15.0, True)
    rec = {"sim_et": 15.0, "sim_et_first_motion": 15.4}
    assert gav.scored_sim_et(rec, fm_src) == (15.4, False)


def test_main_reproduces_the_sweep_score(tmp_path, monkeypatch):
    """Run main() on synthetic chunk files: the dataset's aggregates equal
    phys_weighted_sweep.score_rows on the same records (the published
    headline), and every bike row keeps the documented schema."""
    rows = []
    for i, spec in enumerate(ALL_KNOWN_BIKES):
        # deterministic synthetic sim ETs spread around 12 s
        rows.append(_rec(spec, sim_et=11.0 + (i % 17) * 0.13))
    (tmp_path / "chunk_0000.json").write_text(json.dumps(rows))
    out = tmp_path / "viz.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["gen_accuracy_viz_data.py", "--state-dir", str(tmp_path), "--out", str(out)],
    )
    assert gav.main() == 0
    data = json.loads(out.read_text())
    want = pws.score_rows(rows, "epoch")["overall"]
    assert data["n_matched"] == want["n"]
    assert data["overall"]["w_mean_abs"] == pytest.approx(want["w_mean_abs"], abs=1e-4)
    assert data["overall"]["w_bias"] == pytest.approx(want["w_bias"], abs=1e-4)
    assert set(data) == {
        "generated",
        "references",
        "n_matched",
        "overall",
        "distribution",
        "clusters",
        "bikes",
    }
    assert all(set(b) == BIKE_KEYS for b in data["bikes"])
    assert set(data["references"]) == {"K5", "R1", "Hayabusa"}


def test_legacy_delegate_kept_for_the_pre_epoch_comparison():
    """``_match_benchmark`` has no binding logic of its own any more — it is
    sweep_lib's legacy policy (kept for tests/test_epoch_tune_scripts.py)."""
    from scripts.sweep_lib import bind_benchmark_for_record

    bm = build_bench_map(BENCHMARKS)
    for spec in ALL_KNOWN_BIKES[::11]:
        rec = _rec(spec)
        assert gav._match_benchmark(rec, bm) == bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bm,
            policy="legacy",
        )
