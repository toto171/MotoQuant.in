"""
tests/test_regression_snapshot.py
=================================
Golden-file physics-drift tripwire.

This is the single most load-bearing regression guard in the suite. It pins the
quarter-mile ET and trap speed of:

  * the 3 hand-curated REFERENCE bikes (GSX-R 1000 K5 / YZF-R1 4C8 / Hayabusa
    Gen1) built from ``motoquant.defaults`` -- pinned to **zero** tolerance, so
    the canonical baselines 9.9331 / 10.1436 / 10.3633 s can never silently
    move; and
  * a deterministic, stratified ~35-bike CATALOG sample loaded through the
    **production DB path** (``live_db_copy`` -> ``bike_configs`` row ->
    ``db_row_to_config`` -> ``MotoQuantEngine.run``) -- i.e. the same code that
    ``/api/simulate?bike_id=N`` exercises. Pinned to a tight tolerance.

Why this matters
----------------
Past sessions shipped bugs that the existing baseline-only checks missed:
  * the R15 primary-ratio copy-paste (Ninja 300 ratio left on the Ninja 400) --
    a single catalog bike's ET drifted by seconds while K5/R1/Hayabusa stayed
    perfect; and
  * the ``power_boost_pct`` "dead knob", where a sim output stopped responding
    to a physics input entirely.
A per-bike golden snapshot catches both classes the day they ship.

Determinism
-----------
Every sim runs ``use_adaptive_dt=False, max_time=26.0`` -- fixed 1 ms RK4 is
bit-deterministic, so the comparison tolerances are *tight* (2 ms ET / ~0.1
km/h trap), not loose error bands.

Regenerating the golden
-----------------------
The golden lives at ``tests/data/sweep_snapshot.json``. Regenerate it ONLY when
a physics change is *intended*::

    python scripts/generate_regression_snapshot.py

An unexpected failure here means the snapshot caught a drift -- investigate the
diff *before* regenerating, or the guard is worthless.

Opt-in wider sweep
------------------
The always-on test re-sims the ~35-bike stratified ``catalog`` sample (well
under the sandbox's per-call budget). Setting ``MOTOQUANT_SLOW_TESTS=1`` turns
on ``test_catalog_snapshot_no_drift_full``, which re-sims the golden's
``catalog_full`` block -- EVERY current bike_config in the catalog (500+ bikes)
through the same production DB path -- at the same tight tolerance. This is the
true full-catalog drift guard; it is far too slow for every-PR CI, hence opt-in.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import motoquant
from motoquant.database.bridge import db_row_to_config
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from tests._helpers import live_db_copy

# ── Tolerances ───────────────────────────────────────────────────────────────
# Reference bikes: "exact" to 6 decimals (the golden stores 6-decimal values),
# so 1e-6 absorbs only JSON-storage rounding -- 100x tighter than the 4-decimal
# baseline contract (9.9331 / 10.1436 / 10.3633); a real 0.001s move trips it.
REF_ET_TOL_S = 1e-6
REF_TRAP_TOL_MS = 1e-6
# Catalog bikes: tight, because fixed-dt is deterministic. 2 ms ET, ~0.1 km/h
# trap. These are NOT physical error bars -- they only absorb cross-platform
# float rounding in the last ULP, not real physics movement.
CAT_ET_TOL_S = 0.002
CAT_TRAP_TOL_MS = 0.03  # 0.03 m/s ~= 0.108 km/h

_SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "sweep_snapshot.json"

_REFERENCE_FACTORIES = {
    "GSX-R 1000 K5": gsxr1000_k5,
    "YZF-R1 4C8": yzfr1_4c8,
    "Hayabusa Gen1": hayabusa_gen1,
}


def _load_golden() -> dict:
    if not _SNAPSHOT_PATH.exists():
        pytest.fail(
            f"Golden snapshot missing at {_SNAPSHOT_PATH}. "
            "Generate it with `python scripts/generate_regression_snapshot.py`."
        )
    with open(_SNAPSHOT_PATH, encoding="utf-8") as fh:
        return json.load(fh)


_GOLDEN = _load_golden()
_SIM_ARGS = _GOLDEN.get("sim_args", {"use_adaptive_dt": False, "max_time": 26.0})


def _sim_scalars(config) -> tuple[float, float, bool]:
    """Re-run a sim and return (et_s, trap_ms, finished)."""
    r = motoquant.MotoQuantEngine(config).run(**_SIM_ARGS)
    return float(r.time_quarter), float(r.speed_quarter), bool(r.finished_quarter)


def _config_from_catalog_key(db, key: str):
    """Resolve a 'model_name|year_from' golden key back to a live BikeConfig.

    Returns None if the bike is no longer in the catalog (the test treats that
    as a hard failure -- a shrinking guard is a broken guard).
    """
    model_name, year_str = key.rsplit("|", 1)
    year_from = int(year_str)
    row = db.conn.execute(
        "SELECT bm.id AS mid FROM bike_models bm "
        "WHERE bm.model_name = ? AND bm.year_from = ? ORDER BY bm.id LIMIT 1",
        (model_name, year_from),
    ).fetchone()
    if row is None:
        return None
    mid = dict(row)["mid"]
    cfg_row = db.conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 "
        "ORDER BY version DESC LIMIT 1",
        (mid,),
    ).fetchone()
    if cfg_row is None:
        return None
    return db_row_to_config(dict(cfg_row), name=model_name)


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", sorted(_GOLDEN["reference"].keys()))
def test_reference_baselines_exact(name):
    """The 3 canonical bikes must reproduce their golden ET/trap to the digit.

    Zero tolerance. If this fails, a physics change moved a load-bearing
    baseline -- that is never allowed to happen silently.
    """
    factory = _REFERENCE_FACTORIES[name]
    et, trap, finished = _sim_scalars(factory())
    g = _GOLDEN["reference"][name]
    assert finished, f"{name}: reference bike no longer finishes the quarter mile"
    assert et == pytest.approx(g["et_s"], abs=REF_ET_TOL_S), (
        f"{name}: ET drift -- golden {g['et_s']:.6f}s, now {et:.6f}s "
        f"(delta {et - g['et_s']:+.6f}s). Reference baselines are pinned exactly; "
        f"if intentional, regenerate the snapshot AND update the baseline contract."
    )
    assert trap == pytest.approx(g["trap_ms"], abs=REF_TRAP_TOL_MS), (
        f"{name}: trap drift -- golden {g['trap_ms']:.6f} m/s, now {trap:.6f} m/s "
        f"(delta {trap - g['trap_ms']:+.6f})."
    )


def test_catalog_snapshot_no_drift():
    """Re-sim every catalog bike via the production DB path; fail on any drift.

    This is the bug-catcher: a single bike whose ET moves past 2 ms (e.g. a
    wrong gear ratio, a dead physics knob, a clutch-model change) trips the
    assert, with a per-bike report of exactly which bikes drifted and by how
    much.
    """
    # Pin the SHIPPED catalog explicitly. live_db_copy() otherwise prefers
    # $MOTOQUANT_DB, which sibling modules (test_api / test_llm_runner /
    # test_spec_corrections) transiently repoint at freshly-seeded tmp DBs
    # during the same pytest session — making this drift tripwire flake by
    # snapshotting the wrong DB rather than the real motoquant.db.
    _repo_db = Path(__file__).resolve().parent.parent / "motoquant.db"
    db = live_db_copy(_repo_db if _repo_db.exists() else None)
    if db is None:
        pytest.skip("live motoquant.db not found (set $MOTOQUANT_DB)")

    catalog = _GOLDEN["catalog"]
    drifts: list[str] = []
    missing: list[str] = []
    try:
        for key in sorted(catalog):
            g = catalog[key]
            cfg = _config_from_catalog_key(db, key)
            if cfg is None:
                missing.append(key)
                continue
            et, trap, finished = _sim_scalars(cfg)
            if finished != g["finished"]:
                drifts.append(f"  {key}: finished {g['finished']} -> {finished}")
            if abs(et - g["et_s"]) > CAT_ET_TOL_S:
                drifts.append(
                    f"  {key}: ET {g['et_s']:.4f}s -> {et:.4f}s "
                    f"(delta {et - g['et_s']:+.4f}s, tol {CAT_ET_TOL_S}s)"
                )
            if abs(trap - g["trap_ms"]) > CAT_TRAP_TOL_MS:
                drifts.append(
                    f"  {key}: trap {g['trap_ms']:.3f} -> {trap:.3f} m/s "
                    f"(delta {trap - g['trap_ms']:+.3f}, tol {CAT_TRAP_TOL_MS})"
                )
    finally:
        db.close()

    assert not missing, (
        "Golden bikes no longer resolve against the catalog (the guard is "
        "shrinking -- fix CATALOG_SAMPLE or the DB):\n" + "\n".join(missing)
    )
    assert not drifts, (
        f"Physics drift detected in {len(drifts)} check(s) vs the golden "
        f"snapshot. If intentional, regenerate with "
        f"`python scripts/generate_regression_snapshot.py`:\n" + "\n".join(drifts)
    )


def test_snapshot_covers_all_clusters():
    """Sanity: the golden must span the full cluster taxonomy, not collapse to
    one engine class (which would make the guard blind to whole segments)."""
    clusters = {v["cluster"] for v in _GOLDEN["catalog"].values()}
    expected = {
        "litre_hyper",
        "litre_super",
        "litre_sport",
        "sport_600_1000",
        "mid_twin",
        "entry_300",
        "entry_200",
        "entry_150",
        "cruiser",
        "muscle",
        "two_stroke",
    }
    assert expected.issubset(clusters), (
        f"Golden snapshot lost cluster coverage. Missing: {expected - clusters}"
    )
    assert len(_GOLDEN["catalog"]) >= 30, (
        f"Catalog sample shrank to {len(_GOLDEN['catalog'])} bikes (<30); "
        "the guard is weakening."
    )


@pytest.mark.skipif(
    os.environ.get("MOTOQUANT_SLOW_TESTS") != "1",
    reason="opt-in full-catalog sweep; set MOTOQUANT_SLOW_TESTS=1",
)
def test_catalog_snapshot_no_drift_full():
    """Re-sim EVERY current bike_config in the golden's catalog_full block.

    This is the true full-catalog drift guard (500+ bikes), not an alias of the
    ~35-bike always-on sample. It loads each bike through the same production DB
    path (``db_row_to_config``), runs the same fixed-dt sim, and asserts each ET
    and trap speed stays within the same tight tolerance the always-on catalog
    test uses (2 ms ET / 0.03 m/s trap). A bike that no longer resolves, or one
    that cannot be loaded/simmed, is a hard failure -- never a silent skip.
    """
    full = _GOLDEN.get("catalog_full")
    assert full, (
        "Golden snapshot has no 'catalog_full' block. Regenerate it with "
        "`python scripts/generate_regression_snapshot.py` (full is on by default)."
    )

    # Pin the SHIPPED catalog explicitly (same rationale as the always-on test:
    # sibling modules transiently repoint $MOTOQUANT_DB at fresh tmp DBs).
    _repo_db = Path(__file__).resolve().parent.parent / "motoquant.db"
    db = live_db_copy(_repo_db if _repo_db.exists() else None)
    if db is None:
        pytest.skip("live motoquant.db not found (set $MOTOQUANT_DB)")

    drifts: list[str] = []
    missing: list[str] = []
    failed: list[str] = []
    checked = 0
    try:
        for key in sorted(full):
            g = full[key]
            cfg = _config_from_catalog_key(db, key)
            if cfg is None:
                missing.append(key)
                continue
            try:
                et, trap, finished = _sim_scalars(cfg)
            except Exception as exc:  # noqa: BLE001 -- report, don't swallow
                failed.append(f"  {key}: {type(exc).__name__}: {exc}")
                continue
            checked += 1
            if finished != g["finished"]:
                drifts.append(f"  {key}: finished {g['finished']} -> {finished}")
            if abs(et - g["et_s"]) > CAT_ET_TOL_S:
                drifts.append(
                    f"  {key}: ET {g['et_s']:.4f}s -> {et:.4f}s "
                    f"(delta {et - g['et_s']:+.4f}s, tol {CAT_ET_TOL_S}s)"
                )
            if abs(trap - g["trap_ms"]) > CAT_TRAP_TOL_MS:
                drifts.append(
                    f"  {key}: trap {g['trap_ms']:.3f} -> {trap:.3f} m/s "
                    f"(delta {trap - g['trap_ms']:+.3f}, tol {CAT_TRAP_TOL_MS})"
                )
    finally:
        db.close()

    assert not missing, (
        "Golden bikes in catalog_full no longer resolve against the catalog "
        "(the full guard is shrinking -- regenerate the golden against the live "
        "DB):\n" + "\n".join(missing)
    )
    assert not failed, (
        f"{len(failed)} bike(s) in catalog_full could not be loaded/simmed via "
        "the production DB path (never silently skipped):\n" + "\n".join(failed)
    )
    assert not drifts, (
        f"Physics drift detected in {len(drifts)} check(s) vs the golden's "
        f"catalog_full. If intentional, regenerate with "
        f"`python scripts/generate_regression_snapshot.py`:\n" + "\n".join(drifts)
    )

    # Prove this tier actually exercised the WHOLE catalog, not a 35-bike subset.
    assert checked == len(full), (
        f"Full tier checked {checked} bikes but catalog_full has {len(full)}; "
        "the sweep did not cover the whole golden."
    )
    assert checked >= 500, (
        f"Full tier only exercised {checked} bikes (<500); this is not a true "
        "full-catalog sweep. Regenerate the golden against the live DB."
    )
    print(
        f"\n[full tier] re-simmed {checked} catalog bikes via the production DB "
        "path with zero drift vs the golden."
    )
