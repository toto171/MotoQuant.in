"""
Native (Rust) physics core — parity gate.

``motoquant/physics.py`` is the reference; ``motoquant_core`` (built from
rust/motoquant-core by ``make native``) is a float-op-for-float-op port that
must reproduce it bit-for-bit. Skipped entirely when the extension is not
built, so a pure-Python checkout stays green.

The full-catalog / stress / top-speed sweep lives in
``scripts/check_native_parity.py`` (``make native-parity``); this module is
the fast always-on slice: the three pinned references (fixed + adaptive +
top speed), a deterministic catalog sample through the production DB path,
unit-level parity of the NumPy/libm primitives the loop depends on, and the
resolved-config schema contract.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
from pathlib import Path

import numpy as np
import pytest

import motoquant as mq
from motoquant import native
from motoquant.database.bridge import db_row_to_config
from motoquant.physics import MotoQuantEngine

# Native-dependent tests are skipped when the extension is not built; the
# fixture/manifest freshness guards at the bottom always run (pure Python).
needs_native = pytest.mark.skipif(
    not native.available(), reason="motoquant_core not built (make native)"
)

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-9
CHANNELS = (
    "t", "x", "v", "a", "rpm", "gear", "slip", "traction_pct", "N_front",
    "N_rear", "F_drive", "F_drag", "F_rr", "T_tire", "T_clutch", "P_boost",
    "power_kw", "r_eff",
)  # fmt: skip
REFS = {
    "gsxr1000_k5": 9.933056382451884,
    "yzfr1_4c8": 10.143589715692835,
    "hayabusa_gen1": 10.363345081274984,
}


def _assert_same(rp, rn, label):
    assert len(rp.t) == len(rn.t), f"{label}: sample count {len(rp.t)} != {len(rn.t)}"
    for ch in CHANNELS:
        a = np.asarray(getattr(rp, ch))
        b = np.asarray(getattr(rn, ch))
        assert np.array_equal(a, b), (
            f"{label}: channel {ch} first differs at step "
            f"{int(np.flatnonzero(a != b)[0])}"
        )
    for k in ("time_60ft", "time_eighth", "time_quarter", "speed_quarter"):
        assert getattr(rp, k) == getattr(rn, k), f"{label}: {k}"
    assert rp.finished_quarter == rn.finished_quarter


# ── references ───────────────────────────────────────────────────────────────


@needs_native
@pytest.mark.parametrize("factory", sorted(REFS))
def test_reference_fixed_bit_identical(factory):
    cfg = getattr(mq, factory)()
    rp = MotoQuantEngine(cfg).run()
    rn = native.run_native(cfg)
    assert abs(float(rn.time_quarter) - REFS[factory]) <= TOL
    _assert_same(rp, rn, factory)


@needs_native
@pytest.mark.parametrize("factory", sorted(REFS))
def test_reference_adaptive_bit_identical(factory):
    cfg = getattr(mq, factory)()
    rp = MotoQuantEngine(cfg).run(use_adaptive_dt=True)
    rn = native.run_native(cfg, use_adaptive_dt=True)
    _assert_same(rp, rn, factory + " adaptive")


@needs_native
def test_reference_top_speed_identical():
    cfg = mq.hayabusa_gen1()
    tp = MotoQuantEngine(cfg).run_top_speed()
    tn = native.run_top_speed_native(cfg)
    assert tp.terminal_velocity_ms == tn.terminal_velocity_ms
    assert tp.time_to_terminal_s == tn.time_to_terminal_s
    assert tp.reached_plateau == tn.reached_plateau
    assert tp.lsr_splits == tn.lsr_splits
    _assert_same(tp.full_sim, tn.full_sim, "hayabusa top speed")


@needs_native
def test_native_engine_is_a_drop_in_subclass():
    eng = native.NativeEngine(mq.gsxr1000_k5())
    assert isinstance(eng, MotoQuantEngine)
    calls = []
    r = eng.run(progress_cb=calls.append)
    assert calls[0] == 0.0 and calls[-1] == 1.0
    assert abs(float(r.time_quarter) - REFS["gsxr1000_k5"]) <= TOL
    # engine reuse: a second run is identical (m_total is per-run state)
    assert eng.run().time_quarter == r.time_quarter


# ── catalog sample through the production DB path ────────────────────────────


def _catalog_sample(n=12):
    con = sqlite3.connect(f"file:{ROOT / 'motoquant.db'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT bc.*, bm.model_name AS _name FROM bike_configs bc "
        "JOIN bike_models bm ON bm.id = bc.bike_model_id "
        "WHERE bc.is_current = 1 ORDER BY bc.bike_model_id"
    ).fetchall()
    con.close()
    rows = [dict(r) for r in rows]
    step = max(1, len(rows) // n)
    return rows[::step][:n]


@needs_native
@pytest.mark.skipif(
    not (ROOT / "motoquant.db").exists(), reason="motoquant.db not present"
)
@pytest.mark.parametrize(
    "row", _catalog_sample() if (ROOT / "motoquant.db").exists() else []
)
def test_catalog_sample_bit_identical(row):
    name = row.pop("_name")
    cfg = db_row_to_config(row, name=name)
    _assert_same(MotoQuantEngine(cfg).run(), native.run_native(cfg), name)


@needs_native
def test_boosted_and_two_stroke_paths():
    busa = mq.hayabusa_gen1()
    busa.forced_induction.boost_type = "turbo"
    busa.forced_induction.target_boost_bar = 1.0
    busa.forced_induction.prespool_boost_bar = 0.3
    busa.forced_induction.intercooler_type = "a2a"
    _assert_same(MotoQuantEngine(busa).run(), native.run_native(busa), "turbo busa")

    k5 = mq.gsxr1000_k5()
    k5.engine.dyno_curve = None
    k5.engine.stroke_type = 2
    k5.engine.powervalve = True
    _assert_same(MotoQuantEngine(k5).run(), native.run_native(k5), "curve-less 2T")


@needs_native
def test_degenerate_inputs_raise_like_python():
    cfg = mq.gsxr1000_k5()
    with pytest.raises(UnboundLocalError):
        MotoQuantEngine(cfg).run(distance=0.0)
    # The native path rejects distance=0 up front with a clear ValueError
    # instead of reproducing Python's accidental UnboundLocalError.
    with pytest.raises(ValueError):
        native.run_native(cfg, distance=0.0)
    with pytest.raises(ValueError):
        native.run_native(cfg, max_time=-1.0)


# ── unit-level primitives ────────────────────────────────────────────────────


@needs_native
def test_np_interp_parity_random():
    mc = native._core()
    rng = random.Random(1234)
    for _ in range(300):
        n = rng.choice([1, 2, 3, 4, 5, 9, 25, 100])
        xp = sorted(rng.uniform(500, 16000) for _ in range(n))
        if rng.random() < 0.3 and n > 2:  # exercise duplicate knots
            xp[n // 2] = xp[n // 2 - 1]
        fp = [rng.uniform(-5, 200) for _ in range(n)]
        queries = (
            [rng.uniform(0, 18000) for _ in range(20)] + xp + [xp[0] - 1, xp[-1] + 1]
        )
        for x in queries:
            assert mc.np_interp(x, xp, fp) == float(np.interp(x, xp, fp)), (x, xp, fp)
    assert math.isnan(mc.np_interp(float("nan"), [1.0, 2.0], [3.0, 4.0]))


@needs_native
def test_searchsorted_parity():
    mc = native._core()
    rng = random.Random(7)
    arr = sorted(rng.uniform(0, 400) for _ in range(500))
    for key in [rng.uniform(-10, 410) for _ in range(200)] + arr[:20]:
        assert mc.searchsorted_left(arr, key) == int(np.searchsorted(arr, key))


@needs_native
def test_host_math_is_reproduced():
    info = native.host_math()
    assert info["pow_matches"] and info["sin_matches"], info
    assert info["np_exp_matches_svml_ha"] or info["np_exp_matches_libm"], info
    mc = native._core()
    xs = [-((i * 0.0731) % 30.0) for i in range(2000)]
    got = mc.exp_impl(xs, info["exp_impl"])
    assert got == [float(np.exp(np.float64(x))) for x in xs]


# ── schema contract ──────────────────────────────────────────────────────────


@needs_native
def test_schema_versions_agree():
    mc = native._core()
    assert mc.SCHEMA_VERSION == native.SCHEMA_VERSION == mc.schema_version()
    resolved = native.resolve_config(mq.gsxr1000_k5())
    assert resolved["schema"] == native.SCHEMA_VERSION


@needs_native
def test_resolved_config_round_trips_exactly():
    # Every double must survive Python json -> Rust serde_json -> back exactly.
    resolved = native.resolve_config(mq.hayabusa_gen1())
    echoed = json.loads(native._core().echo_config(native.resolved_json(resolved)))
    assert echoed == resolved


@needs_native
def test_schema_mismatch_and_unknown_fields_are_rejected():
    resolved = native.resolve_config(mq.gsxr1000_k5())
    bad = dict(resolved, schema=native.SCHEMA_VERSION + 1)
    with pytest.raises(ValueError, match="schema"):
        native.run_resolved(bad)
    extra = json.loads(native.resolved_json(resolved))
    extra["tire"]["mystery_knob"] = 1.0
    with pytest.raises(ValueError):
        native.run_resolved(extra)


@needs_native
def test_summary_path_matches_full_run():
    cfg = mq.hayabusa_gen1()
    full = MotoQuantEngine(cfg).run()
    summ = native.summary_native(cfg)
    for k in ("time_60ft", "time_eighth", "time_quarter", "speed_quarter"):
        assert summ[k] == getattr(full, k)


# ── freshness guards (pure Python — run even without the extension) ─────────

FIXTURES = ROOT / "rust" / "fixtures" / "engine_parity.json"


@pytest.mark.skipif(not FIXTURES.exists(), reason="engine fixtures not generated")
@pytest.mark.parametrize("factory", sorted(REFS))
def test_engine_fixtures_are_fresh(factory):
    """The committed Rust/wasm parity fixtures must match TODAY's Python.

    If this fails, the physics (or resolve schema) changed: port the change to
    rust/motoquant-core, then `make wasm` (regenerates the fixtures + the
    committed wasm) — see docs/RUST_CORE.md, regen contract.
    """
    fx = json.loads(FIXTURES.read_text())
    case = next(c for c in fx["cases"] if c["label"] == factory)
    r = MotoQuantEngine(getattr(mq, factory)()).run()
    assert case["expected"]["time_quarter"] == float(r.time_quarter)
    assert case["expected"]["n"] == len(r.t)
    resolved = native.resolve_config(
        getattr(mq, factory)(), exp_impl=case["config"]["exp_impl"]
    )
    assert json.loads(native.resolved_json(resolved)) == case["config"], (
        "resolve_config output drifted from the committed fixture — "
        "schema change? bump SCHEMA_VERSION + `make wasm`"
    )


def test_wasm_manifest_matches_binary():
    import hashlib

    eng = ROOT / "web" / "public" / "engine"
    if not (eng / "motoquant_core.wasm").exists():
        pytest.skip("browser engine not built")
    manifest = json.loads((eng / "engine.json").read_text())
    data = (eng / "motoquant_core.wasm").read_bytes()
    assert manifest["sha256"] == hashlib.sha256(data).hexdigest()
    assert manifest["schema"] == native.SCHEMA_VERSION
