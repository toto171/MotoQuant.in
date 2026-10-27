"""
Native (Rust) physics core — parity gate.

``motoquant/physics.py`` is the reference; ``motoquant_core`` (built from
rust/motoquant-core by ``make native``) is a float-op-for-float-op port that
must reproduce it bit-for-bit. Native-dependent tests skip when the extension
is not built, so a pure-Python checkout stays green — UNLESS
``MOTOQUANT_REQUIRE_NATIVE=1`` (``make native-test``, the CI native job):
then a missing, schema-incompatible or STALE build (compiled from different
Rust sources than this checkout) fails instead of skipping.

The full-catalog / stress / top-speed sweep lives in
``scripts/check_native_parity.py`` (``make native-parity``); this module is
the fast always-on slice: the three pinned references (fixed + adaptive +
top speed), a deterministic catalog sample through the production DB path,
unit-level parity of the NumPy/libm primitives the loop depends on, and the
resolved-config schema contract.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import shutil
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

import motoquant as mq
from motoquant import native
from motoquant.database.bridge import db_row_to_config
from motoquant.physics import MotoQuantEngine

ROOT = Path(__file__).resolve().parent.parent
REQUIRE_NATIVE = os.environ.get("MOTOQUANT_REQUIRE_NATIVE") == "1"

# Native-dependent tests are skipped when the extension is not built (and
# REQUIRE_NATIVE is off); the fixture/manifest freshness guards at the bottom
# always run (pure Python).
needs_native = pytest.mark.skipif(
    not native.available() and not REQUIRE_NATIVE,
    reason="motoquant_core not built (make native)",
)
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


def test_native_build_is_present_and_fresh_when_required():
    """``make native-test`` / CI must not go green on a missing or stale build."""
    if not REQUIRE_NATIVE:
        pytest.skip("MOTOQUANT_REQUIRE_NATIVE != 1")
    info = native.native_info()
    assert native.available(), (
        f"MOTOQUANT_REQUIRE_NATIVE=1 but the Rust core is unavailable or built "
        f"for another schema ({info}) — run `make native`"
    )
    assert not native.is_stale(), (
        f"motoquant_core was built from different Rust sources "
        f"(built {native.built_fingerprint()} != checkout "
        f"{native.fingerprint_sources()}) — run `make native`"
    )
    assert native.host_math()["exact"], info


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
    # Nothing to integrate (finish line at the rest position): both engines
    # raise the same ValueError. With the default 1-ft rollout distance=0 is
    # a valid run that ends at the start beam (ET 0).
    for eng in (MotoQuantEngine(cfg).run, lambda **kw: native.run_native(cfg, **kw)):
        with pytest.raises(ValueError, match="the loop never ran"):
            eng(distance=0.0, rollout_m=0.0)
        assert float(eng(distance=0.0).time_quarter) == 0.0
    # Output sizing `np.zeros(int(max_time / dt) + 1)`: same class as Python.
    for kw, exc in (
        ({"max_time": -1.0}, ValueError),
        ({"max_time": float("nan")}, ValueError),
        ({"max_time": float("inf")}, OverflowError),
    ):
        with pytest.raises(exc):
            MotoQuantEngine(mq.gsxr1000_k5()).run(**kw)
        with pytest.raises(exc):
            native.run_native(mq.gsxr1000_k5(), **kw)
    with pytest.raises(ZeroDivisionError):
        MotoQuantEngine(mq.gsxr1000_k5(), dt=0.0).run()
    with pytest.raises(ZeroDivisionError):
        native.run_native(mq.gsxr1000_k5(), dt=0.0)


@needs_native
def test_oversized_run_raises_memoryerror_instead_of_aborting():
    """A run that would store more than MAX_SAMPLES samples must raise a
    Python MemoryError (Python's own np.zeros raises MemoryError for it) —
    before the cap this aborted the whole interpreter in the allocator."""
    cfg = mq.gsxr1000_k5()
    with pytest.raises(MemoryError):
        native.run_native(cfg, distance=1e12, max_time=1e9)
    # A huge horizon that the bike never needs is fine: buffers grow lazily.
    r = native.run_native(cfg, max_time=1e6)
    assert abs(float(r.time_quarter) - REFS["gsxr1000_k5"]) <= TOL


@needs_native
@pytest.mark.parametrize(
    "path,value",
    [("rider_mass_kg", 95.0), ("dry_mass_kg", 160.0), ("fluid_mass_kg", 30.0)],
)
def test_config_mass_edited_after_construction_matches_python(path, value):
    """Python's step 0 uses the construction-time ``self.m_total``; every later
    step re-reads ``cfg.chassis.total_mass_kg`` (schema 2). Engine reuse: both
    restore ``self.m_total`` from the config after a run."""
    py = MotoQuantEngine(mq.gsxr1000_k5())
    na = native.NativeEngine(mq.gsxr1000_k5())
    setattr(py.cfg.chassis, path, value)
    setattr(na.cfg.chassis, path, value)
    r1p, r1n = py.run(), na.run()
    _assert_same(r1p, r1n, f"{path} first run")
    assert na.m_total == py.m_total == py.cfg.chassis.total_mass_kg
    _assert_same(py.run(), na.run(), f"{path} reused engine")
    # And the edit is real physics, not a no-op on either side.
    assert r1n.time_quarter != native.run_native(mq.gsxr1000_k5()).time_quarter


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


def _gen_engine_web():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import gen_engine_web  # noqa: PLC0415
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    return gen_engine_web


def test_wasm_manifest_matches_binary():
    """The committed browser engine must be the current one — checked against
    the wasm's OWN exports (schema_version, source fingerprint), never against
    the Python constants that also wrote the manifest."""
    eng = ROOT / "web" / "public" / "engine"
    wasm = eng / "motoquant_core.wasm"
    if not wasm.exists():
        pytest.skip("browser engine not built")
    manifest = json.loads((eng / "engine.json").read_text())
    assert manifest["sha256"] == hashlib.sha256(wasm.read_bytes()).hexdigest()
    meta = _gen_engine_web().wasm_metadata(wasm)
    assert meta["schema"] == native.SCHEMA_VERSION == manifest["schema"], (
        f"committed wasm exports schema {meta['schema']}, native.py is "
        f"{native.SCHEMA_VERSION} — run `make wasm`"
    )
    js = (ROOT / "web" / "lib" / "engine.js").read_text()
    m = re.search(r"export const ENGINE_SCHEMA = (\d+);", js)
    assert m and int(m.group(1)) == native.SCHEMA_VERSION, "engine.js ENGINE_SCHEMA"
    fx = json.loads(FIXTURES.read_text())
    assert fx["schema"] == native.SCHEMA_VERSION, "fixture schema"
    assert manifest["source_fingerprint"] == meta["source_fingerprint"]
    here = native.fingerprint_sources()
    if here is not None:
        assert meta["source_fingerprint"] == here, (
            "web/public/engine/motoquant_core.wasm was built from different Rust "
            "sources than this checkout — run `make wasm`"
        )


def test_wasm_reader_rejects_non_constant_exports():
    gen = _gen_engine_web()
    data = (ROOT / "web" / "public" / "engine" / "motoquant_core.wasm").read_bytes()
    with pytest.raises(ValueError, match="i32.const"):
        gen.wasm_const_exports(data, ("simulate",))
    with pytest.raises(ValueError, match="no exported function"):
        gen.wasm_const_exports(data, ("nope",))


def test_source_fingerprint_tracks_rust_sources(tmp_path):
    """fingerprint_sources() must change when any engine source changes (the
    staleness signal) and be stable otherwise."""
    crate = tmp_path / "rust" / "motoquant-core"
    shutil.copytree(native.CRATE_DIR / "src", crate / "src")
    shutil.copy(native.CRATE_DIR / "Cargo.toml", crate / "Cargo.toml")
    shutil.copy(native.CRATE_DIR.parent / "Cargo.lock", crate.parent / "Cargo.lock")
    a = native.fingerprint_sources(crate)
    assert a == native.fingerprint_sources()  # same bytes -> same hash
    eng = crate / "src" / "engine.rs"
    eng.write_text(eng.read_text() + "\n// edit\n")
    assert native.fingerprint_sources(crate) != a
    assert native.fingerprint_sources(tmp_path / "missing") is None


def test_is_stale_compares_build_with_checkout(monkeypatch):
    monkeypatch.setattr(native, "built_fingerprint", lambda: "aaaaaaaaaaaaaaaa")
    monkeypatch.setattr(native, "_checkout_fingerprint", lambda: "bbbbbbbbbbbbbbbb")
    assert native.is_stale()
    monkeypatch.setattr(native, "_checkout_fingerprint", lambda: None)
    assert not native.is_stale()  # sources absent (wheel install): unknown


@needs_native
def test_built_extension_matches_checkout_sources():
    assert native.built_fingerprint() == native.fingerprint_sources(), (
        "stale build — run `make native`"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_next_config_serves_the_engine_with_cache_and_wasm_type():
    """web/next.config.js headers() — the function `next build` calls — must
    give /engine/* the stale-safe short cache and the wasm its MIME type
    (instantiateStreaming needs `application/wasm`)."""
    import subprocess

    out = subprocess.run(
        [
            "node",
            "-e",
            "require('./next.config.js').headers()"
            ".then((h) => console.log(JSON.stringify(h)))",
        ],
        cwd=ROOT / "web",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert out.returncode == 0, out.stderr
    rules = {r["source"]: r["headers"] for r in json.loads(out.stdout)}
    cache = {h["key"]: h["value"] for h in rules["/engine/:path*"]}
    assert "max-age=3600" in cache["Cache-Control"]
    assert "immutable" not in cache["Cache-Control"]  # file name is not hashed
    wasm = {h["key"]: h["value"] for h in rules["/engine/motoquant_core.wasm"]}
    assert wasm["Content-Type"] == "application/wasm"
