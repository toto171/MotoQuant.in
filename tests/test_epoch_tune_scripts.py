"""2026-10 epoch retune — the sweep/tune scripts share ONE binding
implementation and run on the selected engine.

Pins (scripts/phys_weighted_sweep.py, scripts/tune_cluster_knobs.py,
scripts/topspeed_sweep.py, scripts/tune_epoch_2026_10_24.py):

* every catalog bike binds to exactly the benchmark (target ET, trap, source,
  weight) that ``sweep_lib.bind_benchmark_for_record`` gives it, under BOTH
  rule sets (``epoch`` = epoch binding + epoch weights; ``legacy`` = the
  pre-epoch binding + ``source_quality_legacy``) — the inline LEGACY binding
  copies that used to live in phys_weighted_sweep.report() and
  tune_cluster_knobs.build_matches() are gone, so a binding fix can never
  again reach one script and not the other;
* scripts/gen_accuracy_viz_data.py (which reuses phys_weighted_sweep's
  ``_bench_map``) still imports and binds like the legacy rule;
* the sweep runners construct engines through
  ``motoquant.engine_select.make_engine`` (the Rust core when built and
  current, the Python reference otherwise).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
)
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)  # topspeed_sweep imports sweep_lib top-level

from motoquant import engine_select  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts import (
    phys_weighted_sweep as pws,  # noqa: E402
    tune_cluster_knobs as tck,  # noqa: E402
)
from scripts.sweep_lib import (  # noqa: E402
    bind_benchmark_for_record,
    build_bench_map,
    source_quality_legacy,
    source_weight,
)
from scripts.validation_sweep import BENCHMARKS  # noqa: E402


def _rec(spec):
    return {
        "manufacturer": spec.manufacturer,
        "model": spec.model_name,
        "year_from": spec.year_from,
        "year_to": spec.year_to,
    }


@pytest.fixture(scope="module")
def bench_map():
    return build_bench_map(BENCHMARKS)


@pytest.mark.parametrize("rules", ["epoch", "legacy"])
def test_phys_weighted_sweep_binds_like_sweep_lib(rules, bench_map):
    policy = rules
    wfn = source_weight if rules == "epoch" else (lambda s: source_quality_legacy(s)[0])
    n = 0
    for spec in ALL_KNOWN_BIKES:
        want = bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bench_map,
            policy=policy,
            weight_fn=wfn,
        )
        got = pws.bind(_rec(spec), bench_map, rules)
        if want is None:
            assert got is None, spec.model_name
            continue
        n += 1
        assert got == (*want, wfn(want[2])), spec.model_name
    assert n > 250  # the corpus binds hundreds of catalog bikes


def test_rule_sets_are_the_canonical_classifiers():
    assert pws.RULES["epoch"] == ("epoch", source_weight)
    policy, wfn = pws.RULES["legacy"]
    assert policy == "legacy"
    for src in {row[5] for row in BENCHMARKS}:
        assert wfn(src) == source_quality_legacy(src)[0]
    assert pws.HEADLINE_RULES == "epoch"
    # still the very same canonical object (tests/test_sweep_source_weight.py)
    assert pws.source_weight is source_weight


def test_bench_map_shape_kept_for_gen_accuracy_viz_data():
    bm = pws._bench_map()
    assert bm == build_bench_map(BENCHMARKS)
    for key, entries in bm.items():
        assert isinstance(key, tuple) and len(key) == 2
        assert all(len(e) == 4 for e in entries)


def test_gen_accuracy_viz_data_still_binds(bench_map):
    from scripts import gen_accuracy_viz_data as gav

    # its own (legacy-rule) matcher must keep agreeing with sweep_lib's
    # legacy policy on the live corpus
    for spec in ALL_KNOWN_BIKES[::7]:
        want = bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bench_map,
            policy="legacy",
        )
        assert gav._match_benchmark(_rec(spec), gav._bench_map()) == want


@pytest.mark.parametrize("rules", ["epoch", "legacy"])
def test_tune_cluster_knobs_matches_like_sweep_lib(rules, bench_map):
    policy, wfn = pws.RULES[rules]
    got = {m["i"]: m for m in tck.build_matches(rules)}
    want = {}
    for i, spec in enumerate(ALL_KNOWN_BIKES):
        hit = bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bench_map,
            policy=policy,
            weight_fn=wfn,
        )
        if hit is not None:
            want[i] = hit
    assert set(got) == set(want)
    for i, (te, tt, src) in want.items():
        m = got[i]
        assert (m["target_et"], m["target_trap"], m["source"]) == (te, tt, src)
        assert m["weight"] == wfn(src)


def test_tune_cluster_knobs_rejects_unknown_rules(monkeypatch):
    monkeypatch.setenv("MQ_RULES", "bogus")
    with pytest.raises(SystemExit):
        tck._rules()
    monkeypatch.setenv("MQ_RULES", "legacy")
    assert tck._rules() == "legacy"


def test_runners_use_engine_select():
    import topspeed_sweep as tss

    assert pws.make_engine is engine_select.make_engine
    assert tck.make_engine is engine_select.make_engine
    assert tss.make_engine is engine_select.make_engine
    for mod in (pws, tck, tss):
        assert not hasattr(mod, "MotoQuantEngine"), mod.__name__


def test_tune_epoch_cluster_labels_mirror_sweep_with_clusters():
    from scripts import sweep_with_clusters as swc, tune_epoch_2026_10_24 as te

    assert te.TAG_TO_CLUSTER == swc.TAG_TO_CLUSTER
