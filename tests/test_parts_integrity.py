"""Parts-catalog data-integrity guards (2026-07-02 audit).

These run against the live motoquant.db and pin invariants that silent
data bugs violate:

1. Sprockets REPLACE the stock part, so front/rear_sprocket must be set via
   param_overrides (absolute), never param_deltas (additive). Five parts in
   indian_retailer_depth.py used deltas, so applying a "16T front" to a
   stock-17 bike produced 33 teeth — corrupting every ROI/optimizer gearing
   number for those parts.
2. No part may reference a param path that does not exist on BikeConfig
   (the bridge canary): a typo'd path silently no-ops.
"""

import json
import sqlite3
from pathlib import Path

import pytest

# Resolve the REAL production catalog explicitly (not $MOTOQUANT_DB): these
# tests validate the shipped motoquant.db, and other test modules
# (test_api.py) transiently repoint MOTOQUANT_DB at a tmp DB during the same
# pytest session.
_REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"


@pytest.fixture(scope="module")
def conn():
    if not _REPO_DB.exists():
        pytest.skip(f"{_REPO_DB} not present")
    c = sqlite3.connect(f"file:{_REPO_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def _all_parts(conn):
    return conn.execute(
        "SELECT id, brand, model_name, param_overrides, param_deltas FROM parts"
    ).fetchall()


class TestSprocketsUseOverrides:
    def test_no_sprocket_teeth_in_param_deltas(self, conn):
        offenders = []
        for r in _all_parts(conn):
            pd = json.loads(r["param_deltas"]) if r["param_deltas"] else {}
            for k in pd:
                if "front_sprocket" in k or "rear_sprocket" in k:
                    offenders.append(f"{r['id']} {r['brand']} {r['model_name']}")
        assert not offenders, (
            "sprocket teeth must be absolute (param_overrides), never additive "
            "(param_deltas) — offenders: " + ", ".join(offenders)
        )

    def test_sprocket_override_applies_absolutely(self, conn):
        # applying a 16T front sprocket to the K5 (stock 17) must yield 16
        import warnings

        warnings.filterwarnings("ignore")
        from motoquant.database import bridge
        from motoquant.defaults import gsxr1000_k5

        row = conn.execute(
            "SELECT * FROM parts WHERE param_overrides LIKE '%front_sprocket%' LIMIT 1"
        ).fetchone()
        if not row:
            pytest.skip("no front-sprocket part in catalog")
        part = dict(row)
        want = json.loads(part["param_overrides"])["drivetrain.front_sprocket"]
        cfg = bridge.apply_part_to_config(gsxr1000_k5(), part)
        assert cfg.drivetrain.front_sprocket == want


class TestNoDeadParamPaths:
    def test_every_param_path_exists_on_config(self, conn):
        """apply_part_to_config warns on unknown paths; assert none warn."""
        import warnings

        from motoquant.database import bridge
        from motoquant.defaults import gsxr1000_k5

        base = gsxr1000_k5()
        dead = []
        for r in _all_parts(conn):
            part = dict(r)
            if not (part.get("param_overrides") or part.get("param_deltas")):
                continue
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                try:
                    bridge.apply_part_to_config(base, part)
                except Exception:
                    continue
                for warning in w:
                    msg = str(warning.message).lower()
                    if "path" in msg or "invalid" in msg or "unknown" in msg:
                        dead.append(f"{r['id']} {r['brand']}: {warning.message}")
        assert not dead, (
            "parts with invalid param paths (silent no-ops):\n" + "\n".join(dead[:20])
        )


class TestIdPreservingUpsert:
    """tire_repo.create() / parts_repo.create() must upsert in place, not
    DELETE+re-INSERT (INSERT OR REPLACE), which trips the un-cascaded FK from
    bike_tire_fitments and wipes part_prices/renumbers ids."""

    def _fresh_db(self):
        from motoquant.database.connection import MotoQuantDB

        db = MotoQuantDB(":memory:")
        db.initialize()
        return db

    def test_reseed_with_fitment_does_not_crash(self):
        from motoquant.database.seed import seed_all

        db = self._fresh_db()
        try:
            seed_all(db)
            t = db._conn.execute("SELECT id FROM tire_models LIMIT 1").fetchone()[0]
            b = db._conn.execute("SELECT id FROM bike_models LIMIT 1").fetchone()[0]
            db.tires.link_bike_fitment(b, t, "front", "oem")
            # Second seed_all used to raise FOREIGN KEY constraint failed.
            seed_all(db)
            t2 = db._conn.execute("SELECT id FROM tire_models LIMIT 1").fetchone()[0]
            assert t == t2, "tire id must be preserved across re-seed"
        finally:
            db.close()

    def test_tire_create_preserves_id(self):
        db = self._fresh_db()
        try:
            id1 = db.tires.create("MRF", "Zapper Q", "100/80-17", "sport")
            id2 = db.tires.create("MRF", "Zapper Q", "100/80-17", "sport")
            assert id1 == id2
        finally:
            db.close()

    def test_part_create_preserves_id(self):
        db = self._fresh_db()
        try:
            id1 = db.parts.create(
                "exhaust",
                "Akrapovic",
                "Test Slip-On",
                {"x": 1},
                part_number="AKX-TEST-1",
            )
            id2 = db.parts.create(
                "exhaust",
                "Akrapovic",
                "Test Slip-On v2",
                {"x": 2},
                part_number="AKX-TEST-1",
            )
            assert id1 == id2
        finally:
            db.close()


class TestSprocketPositionExclusivity:
    """July 3, 2026 audit: 14 sprocket parts shipped without
    specifications.position, so the knapsack's front/rear exclusivity
    degraded them to singleton groups — two FRONT sprockets could co-select
    in one optimizer build. Pins both the DB patch
    (scripts/patch_2026_07_03_sprocket_position.py) and the name-regex
    fallback in roi._sprocket_positions."""

    def test_every_db_sprocket_has_position(self, conn):
        rows = conn.execute(
            """
            SELECT p.id, p.model_name, p.specifications
              FROM parts p JOIN parts_categories c ON p.category_id = c.id
             WHERE c.name = 'sprocket'
            """
        ).fetchall()
        assert rows, "no sprocket parts in catalog?"
        missing = []
        for r in rows:
            try:
                specs = json.loads(r["specifications"]) if r["specifications"] else {}
            except (ValueError, TypeError):
                specs = {}
            if not isinstance(specs, dict) or specs.get("position") not in (
                "front",
                "rear",
            ):
                missing.append((r["id"], r["model_name"]))
        assert not missing, (
            f"sprockets missing specifications.position (re-run "
            f"scripts/patch_2026_07_03_sprocket_position.py): {missing}"
        )

    def test_positionless_front_sprockets_cannot_co_select(self):
        """Two front sprockets WITHOUT specifications.position (name-only)
        must land in the same knapsack group via the model-name fallback —
        the optimizer may pick at most one. A rear sprocket may still join."""
        import copy as _copy

        from motoquant.analysis.roi import find_best_build
        from motoquant.defaults import gsxr1000_k5

        parts = {
            1: {
                "id": 1,
                "brand": "JT",
                "model_name": "520 Front Sprocket 15T Test",
                "category_name": "sprocket",
                "specifications": "{}",  # NO position key — fallback must fire
                "price_inr": 1000.0,
            },
            2: {
                "id": 2,
                "brand": "JT",
                "model_name": "520 Front Sprocket 16T Test",
                "category_name": "sprocket",
                "specifications": "{}",
                "price_inr": 1000.0,
            },
            3: {
                "id": 3,
                "brand": "JT",
                "model_name": "520 Rear Sprocket 45T Test",
                "category_name": "sprocket",
                "specifications": "{}",
                "price_inr": 1000.0,
            },
        }

        class FakeRepo:
            def get(self, pid):
                return parts.get(pid)

            def apply_to_config(self, pid, cfg):
                mod = _copy.deepcopy(cfg)
                mod._test_gain = getattr(cfg, "_test_gain", 0) + 1
                return mod

            def apply_multiple(self, pids, cfg):
                mod = _copy.deepcopy(cfg)
                mod._test_gain = getattr(cfg, "_test_gain", 0) + len(pids)
                return mod

        def et_fn(cfg):
            # Each applied part is "worth" 0.1 s — no physics involved.
            return 10.0 - 0.1 * getattr(cfg, "_test_gain", 0), 200.0

        result = find_best_build(
            base_config=gsxr1000_k5(),
            budget_inr=10_000.0,
            parts_repo=FakeRepo(),
            part_ids=[1, 2, 3],
            et_fn=et_fn,
        )
        picked = {r.part_id for r in result.selected_parts}
        n_front = len(picked & {1, 2})
        assert n_front <= 1, (
            f"knapsack stacked two positionless FRONT sprockets: {picked} "
            f"(roi._sprocket_positions name fallback is dead)"
        )
        # Positive control: one front + the rear should both be selectable.
        assert 3 in picked and n_front == 1, (
            f"expected one front + one rear sprocket selected, got {picked}"
        )
