"""
Every full-physics scorer in the analysis layer must run through
``engine_select.make_engine`` (Rust core when active, Python reference
otherwise) — October 2026. Before, roi._run_et, the optimizer's fallback /
verify sims, the autotune sweeps, the outlaw baseline, Sobol, the Bayesian
optimizer, surrogate data generation and the NL runner all constructed
``MotoQuantEngine`` directly, so none of them could use the Rust core.

A spy engine class (subclassing whatever engine is selected, so results are
unchanged) counts constructions through the selector.
"""

import shutil
from pathlib import Path

import pytest

from motoquant import engine_select
from motoquant.defaults import gsxr1000_k5

DB_PATH = Path(__file__).resolve().parents[1] / "motoquant.db"


@pytest.fixture
def spy(monkeypatch):
    base = engine_select.engine_class()
    made = []

    class Spy(base):
        def __init__(self, *a, **k):
            made.append(1)
            super().__init__(*a, **k)

    monkeypatch.setattr(engine_select, "engine_class", lambda: Spy)
    return made


class _EmptyRepo:
    """A parts repo with no candidates (the optimizer stops after baseline)."""

    _conn = None

    def search(self, **kw):
        return []


def test_roi_run_et_uses_the_selector(spy):
    from motoquant.analysis.roi import _run_et

    _run_et(gsxr1000_k5())
    assert spy


def test_optimizer_full_sim_scoring_uses_the_selector(spy):
    from motoquant.analysis.build_optimizer import optimize_build

    optimize_build(gsxr1000_k5(), 10_000, _EmptyRepo())
    assert spy


def test_autotune_sweeps_use_the_selector(spy):
    from motoquant.analysis.ecu_autotune import autotune

    autotune(gsxr1000_k5(), gear_span=1, launch_steps=3)
    assert len(spy) >= 4


def test_outlaw_baseline_uses_the_selector(spy):
    from motoquant.analysis.outlaw import optimize_outlaw

    optimize_outlaw(gsxr1000_k5(), _EmptyRepo(), None, gear_span=1, launch_steps=3)
    assert spy


def test_sobol_and_bayesian_use_the_selector(spy):
    from motoquant.analysis import sobol
    from motoquant.analysis.bayesian_opt import BayesianBuildOptimizer

    sobol._run_et(gsxr1000_k5())
    n_sobol = len(spy)
    BayesianBuildOptimizer(gsxr1000_k5(), budget_inr=10_000)
    assert n_sobol >= 1 and len(spy) > n_sobol


def test_surrogate_training_data_uses_the_selector(spy):
    from motoquant.analysis.surrogate_data import generate_training_data

    generate_training_data(gsxr1000_k5(), n_samples=2, seed=1)
    assert spy


def test_nl_runner_uses_the_selector(spy, tmp_path):
    if not DB_PATH.exists():
        pytest.skip("catalog DB not present")
    from motoquant.database.connection import MotoQuantDB
    from motoquant.nlp import NLSimRunner

    path = tmp_path / "motoquant.db"
    shutil.copy(DB_PATH, path)
    db = MotoQuantDB(str(path))
    db.connect()
    try:
        out = NLSimRunner(db).run_query("my k5 at aamby valley")
    finally:
        db.close()
    assert "et_s" in out
    assert spy
