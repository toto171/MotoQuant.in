"""Part-effectiveness guards — a priced part must actually move the sim.

Background (2026-07-25 weekly audit, §3.3c)
-------------------------------------------
``DrivetrainParams.quickshifter`` has **no reader in the physics engine** — the
sim reads only ``drivetrain.total_shift_time_ms``. Eight shipped catalog parts
priced Rs12,640-Rs42,000 carried ``drivetrain.quickshifter`` as their ONLY
parameter modification, so selecting one moved ET by exactly 0.000000 s while
twelve functionally identical siblings that also set ``total_shift_time_ms``
delivered -0.084 to -0.094 s. Those eight parts still appeared in ROI tables
and the build-optimizer's candidate pool as if they did something.

This module is the regression guard, in two layers:

1. ``TestDeadQuickshifterSKUs`` — the eight named SKUs, each applied through
   the REAL production path (``bridge.apply_part_to_config`` -> ``BikeConfig``
   -> ``MotoQuantEngine.run``) against a compatible catalog bike, must cut ET
   by a measurable margin. Reverting the data fix fails these.
2. ``TestShiftPartClassGuard`` — the class-level invariant: *every* part in
   the ``quickshifter`` / ``air_shifter`` categories must move ET on at least
   one compatible bike. This catches the next dead shift-part SKU, not just
   the eight we know about.
3. ``TestSeedSourceCarriesFix`` — the seed-source fold (July-4 A3-15): a fresh
   ``seed_parts_catalog()`` must produce the armed overrides on its own, so the
   patch script is never the sole carrier of the fix.

The DB tests run against a **temporary copy** of the shipped ``motoquant.db``
with ``scripts/patch_2026_08_08_quickshifter_overrides.py`` applied (the patch
is idempotent, so it is a no-op once the tracked DB has been re-patched by the
reseed chain). The production ``motoquant.db`` is never opened for writing.

Runtime is bounded by caching one baseline sim per bike and preferring bikes
whose baseline is already cached, so the whole module runs a few dozen sims.
"""

import importlib.util
import json
import shutil
import sqlite3
import sys
import warnings
from pathlib import Path

import pytest

from motoquant.database import bridge
from motoquant.database.parts_repo import enrich_bike_row_for_fitment
from motoquant.parts.compatibility import is_compatible
from motoquant.physics import MotoQuantEngine

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REPO_DB = _REPO_ROOT / "motoquant.db"
_PATCH = _REPO_ROOT / "scripts" / "patch_2026_08_08_quickshifter_overrides.py"

# The eight SKUs the audit found dead, keyed by their stable part_number,
# with the shift time the data fix gives them. Kept here (rather than imported
# from the patch) so a silent edit to the patch's table fails this test.
DEAD_EIGHT: dict[str, float] = {
    "HT-QS-MOD": 60.0,  # HealTech QuickShifter Controller Module
    "QS-HM-4": 70.0,  # HM QS Mid-Range
    "QS-TRA-5": 60.0,  # Translogic QS Pro V2
    "QS-DYN-6": 55.0,  # Dynojet Power Commander QS
    "QS-GPR-7": 60.0,  # GPR Gear Box QS
    "QS-HEL-8": 60.0,  # Helix QS Universal
    "QS-SHI-9": 60.0,  # Shift Assist Pro
    "QS-BON-10": 60.0,  # Bonamici Racing Quick Shifter
}

SHIFT_CATEGORIES = ("quickshifter", "air_shifter")

# A part that claims to speed up shifting must beat this. The functional
# siblings deliver 0.084-0.094 s; 0.01 s is ~10x the RK4 solver's own noise
# floor on a fixed 1 ms step (which is bit-reproducible, so really zero).
MIN_ET_GAIN_S = 0.01


def _load_patch_module():
    spec = importlib.util.spec_from_file_location("_qs_patch_2026_08_08", _PATCH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def patched_db(tmp_path_factory):
    """A writable temp copy of the shipped catalog with the patch applied."""
    if not _REPO_DB.exists():
        pytest.skip(f"{_REPO_DB} not present")
    if not _PATCH.exists():
        pytest.skip(f"{_PATCH} not present")
    dst = tmp_path_factory.mktemp("qs_effectiveness") / "motoquant.db"
    shutil.copy(_REPO_DB, dst)
    patch = _load_patch_module()
    first = patch.apply(str(dst))
    assert first["missing"] == 0, f"patch could not find all SKUs: {first}"
    # Idempotency is part of the contract — a second run must change nothing.
    second = patch.apply(str(dst))
    assert second["updated"] == 0 and second["already_armed"] == second["expected"], (
        f"patch is not idempotent: {second}"
    )
    return dst


@pytest.fixture(scope="module")
def conn(patched_db):
    c = sqlite3.connect(f"file:{patched_db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


@pytest.fixture(scope="module")
def bike_pool(conn):
    """Every catalog bike that has a current config, with fitment fields filled.

    Compatibility checking is pure Python and cheap; only the sims are
    expensive, so the pool is the full catalog and the sims are cached.
    """
    rows = conn.execute(
        """SELECT bm.id AS bike_model_id, bm.model_name, bm.displacement_cc,
                  bc.*
           FROM bike_models bm
           JOIN bike_configs bc
             ON bc.bike_model_id = bm.id AND bc.is_current = 1
           ORDER BY bm.displacement_cc"""
    ).fetchall()
    pool = []
    for r in rows:
        cfg_row = dict(r)
        bike_row = dict(
            conn.execute(
                "SELECT * FROM bike_models WHERE id = ?", (cfg_row["bike_model_id"],)
            ).fetchone()
        )
        enrich_bike_row_for_fitment(conn, bike_row)
        pool.append((bike_row, cfg_row))
    assert pool, "no bikes with a current config in the catalog"
    return pool


@pytest.fixture(scope="module")
def baselines():
    """bike_model_id -> stock ET, filled lazily so we sim each bike at most once."""
    return {}


def _config_for(cfg_row):
    return bridge.db_row_to_config(cfg_row, name=cfg_row.get("model_name", "DB Bike"))


def _run_et(config) -> float:
    result = MotoQuantEngine(config).run()
    et = result.time_quarter
    assert et is not None and et > 0, "bike did not finish the quarter mile"
    return et


def _baseline_et(cfg_row, baselines) -> float:
    key = cfg_row["bike_model_id"]
    if key not in baselines:
        baselines[key] = _run_et(_config_for(cfg_row))
    return baselines[key]


def _fetch_part(conn, *, part_number=None, part_id=None) -> dict:
    if part_number is not None:
        row = conn.execute(
            """SELECT p.*, pc.name AS category_name
               FROM parts p JOIN parts_categories pc ON pc.id = p.category_id
               WHERE p.part_number = ?""",
            (part_number,),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT p.*, pc.name AS category_name
               FROM parts p JOIN parts_categories pc ON pc.id = p.category_id
               WHERE p.id = ?""",
            (part_id,),
        ).fetchone()
    assert row is not None, f"part not found: {part_number or part_id}"
    return dict(row)


def _compatible_bikes(part: dict, bike_pool):
    for bike_row, cfg_row in bike_pool:
        ok, _reason = is_compatible(part, bike_row)
        if ok:
            yield bike_row, cfg_row


def _best_gain(part, bike_pool, baselines, *, max_bikes=1, prefer_cached=True):
    """Apply `part` to up to `max_bikes` compatible bikes; return the best gain.

    Returns (gain_s, bike_name) with gain_s = stock_et - modified_et (positive
    means the part made the bike faster), or (None, None) if the part fits
    nothing in the catalog.
    """
    candidates = list(_compatible_bikes(part, bike_pool))
    if not candidates:
        return None, None
    if prefer_cached:
        # Re-use an already-simulated bike where possible: saves the baseline sim.
        candidates.sort(key=lambda bc: bc[1]["bike_model_id"] not in baselines)

    best_gain = None
    best_name = None
    for bike_row, cfg_row in candidates[:max_bikes]:
        stock_et = _baseline_et(cfg_row, baselines)
        with warnings.catch_warnings():
            # apply_part_to_config warns on unknown paths; test_parts_integrity
            # already guards that, and a warning must not abort this sim.
            warnings.simplefilter("ignore")
            modified = bridge.apply_part_to_config(_config_for(cfg_row), part)
        gain = stock_et - _run_et(modified)
        if best_gain is None or gain > best_gain:
            best_gain = gain
            best_name = bike_row["model_name"]
    return best_gain, best_name


class TestDeadQuickshifterSKUs:
    """The eight audit-flagged SKUs, through the real bridge + engine."""

    @pytest.mark.parametrize("part_number", sorted(DEAD_EIGHT))
    def test_part_measurably_reduces_et(self, part_number, conn, bike_pool, baselines):
        part = _fetch_part(conn, part_number=part_number)
        gain, bike_name = _best_gain(part, bike_pool, baselines)
        assert gain is not None, (
            f"{part_number} ({part['brand']} {part['model_name']}) fits no bike "
            "in the catalog — it can never be sold or simulated"
        )
        assert gain > MIN_ET_GAIN_S, (
            f"{part_number} ({part['brand']} {part['model_name']}, "
            f"Rs{part['price_inr']:,.0f}) moved ET by only {gain:+.6f} s on "
            f"{bike_name}. A priced quickshifter that does nothing is the "
            "2026-07-25 audit's §3.3c dead-knob bug — check that its "
            "param_overrides still carry drivetrain.total_shift_time_ms."
        )

    @pytest.mark.parametrize("part_number", sorted(DEAD_EIGHT))
    def test_shift_time_override_is_the_expected_value(self, part_number, conn):
        """Pins the chosen value, and that it is absolute (not a delta)."""
        part = _fetch_part(conn, part_number=part_number)
        overrides = json.loads(part["param_overrides"] or "{}")
        assert overrides.get("drivetrain.total_shift_time_ms") == pytest.approx(
            DEAD_EIGHT[part_number]
        ), f"{part_number} shift-time override drifted: {overrides}"
        # The (inert but honest) product-metadata flag stays.
        assert overrides.get("drivetrain.quickshifter") is True


class TestShiftPartClassGuard:
    """Every shift-assist part must be live — guards the class, not the eight."""

    def test_all_shift_parts_move_et(self, conn, bike_pool, baselines):
        rows = conn.execute(
            f"""SELECT p.id
                FROM parts p JOIN parts_categories pc ON pc.id = p.category_id
                WHERE pc.name IN ({",".join("?" * len(SHIFT_CATEGORIES))})
                ORDER BY p.id""",
            SHIFT_CATEGORIES,
        ).fetchall()
        assert len(rows) >= 20, f"only {len(rows)} shift parts — catalog shrank?"

        dead = []
        unfitted = []
        for r in rows:
            part = _fetch_part(conn, part_id=r["id"])
            gain, bike_name = _best_gain(part, bike_pool, baselines)
            label = (
                f"#{part['id']} {part['brand']} {part['model_name']} "
                f"[{part['category_name']}]"
            )
            if gain is None:
                unfitted.append(label)
            elif gain <= MIN_ET_GAIN_S:
                dead.append(f"{label} -> {gain:+.6f} s on {bike_name}")

        assert not dead, (
            "shift-assist parts that do not measurably improve ET (the sim "
            "reads drivetrain.total_shift_time_ms; drivetrain.quickshifter and "
            "drivetrain.air_shifter have no reader in physics.py):\n  "
            + "\n  ".join(dead)
        )
        assert not unfitted, (
            "shift-assist parts that fit no bike in the catalog:\n  "
            + "\n  ".join(unfitted)
        )


class TestSeedSourceCarriesFix:
    """A fresh seed must produce the fix on its own (seed-source fold rule)."""

    def test_fresh_seed_arms_every_dead_sku(self):
        from motoquant.database.connection import MotoQuantDB
        from motoquant.database.seed import seed_parts_catalog

        db = MotoQuantDB(":memory:")
        db.initialize()
        seed_parts_catalog(db)

        missing = []
        for part_number, want_ms in DEAD_EIGHT.items():
            row = db.conn.execute(
                "SELECT model_name, param_overrides FROM parts WHERE part_number = ?",
                (part_number,),
            ).fetchone()
            if row is None:
                missing.append(f"{part_number}: not seeded")
                continue
            overrides = json.loads(row["param_overrides"] or "{}")
            got = overrides.get("drivetrain.total_shift_time_ms")
            if got != want_ms:
                missing.append(
                    f"{part_number} ({row['model_name']}): "
                    f"expected {want_ms} ms, seed produced {got!r}"
                )
        db.close()
        assert not missing, (
            "seed source lost the 2026-08-08 quickshifter fix — a fresh "
            "seed_all() would resurrect the dead-knob bug (July-4 A3-15 "
            "seed-source fold rule):\n  " + "\n  ".join(missing)
        )
