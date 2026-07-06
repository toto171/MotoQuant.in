"""
Tests for motoquant.analysis.build_optimizer (Track B — Build Optimizer).

Three layers:
  * unit  — _select_build (multiple-choice knapsack) on synthetic ROI rows; no sims.
  * unit  — SurrogatePredictor full-sim fallback contract; reference baselines.
  * integ — optimize_build end-to-end against the seeded catalog (small candidate
            caps to stay fast).  Skipped if the catalog DB can't be opened.
  * route — /api/optimize/build via FastAPI TestClient; gated on fastapi.

Integration uses a read-only, immutable connection so it is safe on FUSE /
full-disk sandboxes and needs no DB copy.  Set MOTOQUANT_TEST_DB to point at a
specific catalog (defaults to ./motoquant.db).
"""

import os
import sqlite3

import pytest

from motoquant.analysis.build_optimizer import (
    _EXCLUSIVE_CATEGORIES,
    VALID_GOALS,
    OptimizedBuild,
    _select_build,
    make_predictor,
    optimize_build,
)
from motoquant.analysis.roi import PartROIResult
from motoquant.defaults import gsxr1000_k5

DB_PATH = os.environ.get("MOTOQUANT_TEST_DB", "motoquant.db")


def _mk(pid, cat, price, det, dtrap=0.0):
    """Build a synthetic PartROIResult."""
    return PartROIResult(
        part_id=pid,
        part_name=f"P{pid}",
        brand="B",
        category=cat,
        category_display=cat,
        price_inr=float(price),
        price_usd=None,
        base_et_s=10.0,
        modified_et_s=10.0 - det,
        delta_et_s=float(det),
        delta_trap_ms=float(dtrap),
        roi_score=(det / max(price, 1) * 1e5),
        cost_per_tenth_inr=(price / (det * 10) if det > 0 else float("inf")),
        is_compatible=True,
        availability="in_stock",
        is_free=(price == 0),
    )


# ─────────────────────────────── _select_build ───────────────────────────────
class TestSelectBuild:
    def _pool(self):
        return [
            _mk(1, "air_filter", 5000, 0.05, 1.0),
            _mk(2, "air_filter", 9000, 0.08, 1.6),
            _mk(3, "air_filter", 7000, 0.03, 0.6),
            _mk(4, "exhaust", 40000, 0.10, 2.5),
            _mk(5, "exhaust", 55000, 0.12, 3.0),
            _mk(6, "ecu", 20000, 0.06, 1.5),
            _mk(7, "sprocket", 3000, 0.04, 0.4),
            _mk(8, "fuel_system", 18000, 0.05, 1.2),
        ]

    def test_exclusive_categories_never_stack(self):
        sel = _select_build(self._pool(), 100_000, "min_et")
        from collections import Counter

        counts = Counter(r.category for r in sel)
        for cat in _EXCLUSIVE_CATEGORIES:
            assert counts.get(cat, 0) <= 1, f"{cat} stacked: {counts[cat]}"

    def test_budget_respected(self):
        sel = _select_build(self._pool(), 30_000, "min_et")
        assert sum(r.price_inr for r in sel) <= 30_000

    def test_picks_best_in_exclusive_group(self):
        # within air_filter, only the best ET filter (#2, 0.08s) should survive
        # when budget is ample; #1 and #3 are dominated.
        sel = _select_build(self._pool(), 500_000, "min_et")
        filters = [r.part_id for r in sel if r.category == "air_filter"]
        assert filters == [2]

    def test_free_parts_selected_at_zero_budget(self):
        pool = self._pool() + [_mk(9, "air_filter", 0, 0.02)]
        sel = _select_build(pool, 0, "min_et")
        assert sel and all(r.price_inr == 0 for r in sel)

    def test_objective_changes_value_basis(self):
        # A part with tiny ET gain but big trap gain should be preferred under
        # max_trap but not under min_et.
        pool = [
            _mk(1, "exhaust", 30000, 0.10, 0.5),  # great ET, weak trap
            _mk(2, "exhaust", 30000, 0.02, 4.0),  # weak ET, great trap
        ]
        et_pick = _select_build(pool, 30000, "min_et")
        trap_pick = _select_build(pool, 30000, "max_trap")
        assert et_pick[0].part_id == 1
        assert trap_pick[0].part_id == 2

    def test_empty_when_nothing_affordable(self):
        assert _select_build(self._pool(), 100, "min_et") == []


# ─────────────────────────────── predictor ───────────────────────────────
class TestPredictor:
    def test_fullsim_fallback_matches_run_et(self):
        from motoquant.analysis.roi import _run_et

        cfg = gsxr1000_k5()
        pred = make_predictor(None)
        et, trap = pred(cfg)
        ref_et, ref_trap = _run_et(cfg)
        assert et == pytest.approx(ref_et, abs=1e-6)
        assert trap == pytest.approx(ref_trap, abs=1e-6)
        assert pred.method == "full_sim"
        assert pred.stats()["fallback_calls"] == 1
        assert pred.stats()["surrogate_calls"] == 0

    def test_k5_baseline_preserved(self):
        # roi.py was extended for the optimizer — the reference baseline must not move.
        et, _ = make_predictor(None)(gsxr1000_k5())
        assert et == pytest.approx(10.0334, abs=2e-3)

    def test_valid_goals(self):
        assert VALID_GOALS == ("min_et", "max_trap")


# ─────────────────────────────── integration ───────────────────────────────
def _db_ok():
    try:
        c = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True)
        c.execute("SELECT 1 FROM bike_models LIMIT 1")
        c.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_ok(), reason="catalog DB unavailable")
class TestOptimizeBuildIntegration:
    @pytest.fixture(scope="class")
    def conn(self):
        c = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True)
        c.row_factory = sqlite3.Row
        yield c
        c.close()

    @pytest.fixture(scope="class")
    def repo(self, conn):
        from motoquant.database.parts_repo import PartsRepository

        return PartsRepository(conn)

    def _bike(self, conn, min_cc=900):
        row = conn.execute(
            """SELECT bm.id, m.name mfr, bm.model_name
               FROM bike_models bm JOIN manufacturers m ON bm.manufacturer_id=m.id
               WHERE bm.displacement_cc >= ? ORDER BY bm.id LIMIT 1""",
            (min_cc,),
        ).fetchone()
        return dict(row)

    def _config(self, conn, bid, name):
        from motoquant.database.bridge import db_row_to_config

        row = conn.execute(
            "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 ORDER BY version DESC LIMIT 1",
            (bid,),
        ).fetchone()
        return db_row_to_config(dict(row), name=name)

    def test_optimize_litre_min_et(self, conn, repo):
        b = self._bike(conn)
        cfg = self._config(conn, b["id"], f"{b['mfr']} {b['model_name']}")
        res = optimize_build(
            cfg, 80_000, repo, goal="min_et", bike_model_id=b["id"], max_candidates=10
        )
        assert isinstance(res, OptimizedBuild)
        assert res.total_cost_inr <= 80_000 + 1e-6
        assert res.parts_skipped_incompatible == 0
        # an improving on-budget build should be found for a litre bike
        # (delta_et_s = optimized - base since July 6, 2026: negative = faster)
        assert res.delta_et_s <= 0.0
        # exclusivity holds in the realised build
        from collections import Counter

        counts = Counter(p.category.lower() for p in res.parts)
        for cat in _EXCLUSIVE_CATEGORIES:
            assert counts.get(cat, 0) <= 1
        # JSON-serializable
        import json

        json.dumps(res.to_dict())

    def test_goal_max_trap_returns_valid_build(self, conn, repo):
        b = self._bike(conn)
        cfg = self._config(conn, b["id"], f"{b['mfr']} {b['model_name']}")
        res = optimize_build(
            cfg, 80_000, repo, goal="max_trap", bike_model_id=b["id"], max_candidates=10
        )
        assert res.goal == "max_trap"
        assert res.total_cost_inr <= 80_000 + 1e-6
        assert res.delta_trap_kmh >= 0.0

    def test_zero_budget_only_free_or_empty(self, conn, repo):
        b = self._bike(conn)
        cfg = self._config(conn, b["id"], f"{b['mfr']} {b['model_name']}")
        res = optimize_build(
            cfg, 0, repo, goal="min_et", bike_model_id=b["id"], max_candidates=10
        )
        assert res.total_cost_inr == 0.0
        assert all(p.price_inr == 0 for p in res.parts)

    def test_bad_goal_defaults_to_min_et(self, conn, repo):
        b = self._bike(conn)
        cfg = self._config(conn, b["id"], f"{b['mfr']} {b['model_name']}")
        res = optimize_build(
            cfg, 50_000, repo, goal="nonsense", bike_model_id=b["id"], max_candidates=6
        )
        assert res.goal == "min_et"


# ─────────────────────────────── route (fastapi-gated) ───────────────────────────────
class TestOptimizeRoute:
    @pytest.fixture(scope="class")
    def client(self):
        pytest.importorskip("fastapi")
        if not _db_ok():
            pytest.skip("catalog DB unavailable")
        from fastapi.testclient import TestClient

        os.environ.setdefault("MOTOQUANT_DB", DB_PATH)
        from motoquant.api import app

        return TestClient(app)

    def test_optimize_endpoint(self, client):
        # use a real catalog bike_id; pick the first litre bike id via the API
        bikes = client.get("/api/bikes", params={"search": "", "limit": 1}).json()
        bike_id = (bikes.get("bikes") or bikes.get("results") or bikes)[0]["id"]
        r = client.post(
            "/api/optimize/build",
            json={
                "bike_id": bike_id,
                "budget_inr": 60000,
                "goal": "min_et",
                "max_candidates": 6,
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "optimized_et_s" in body and "parts" in body
        assert body["total_cost_inr"] <= 60000 + 1e-6


class TestKnapsackBudgetAndGrouping:
    """June 2026 regressions: ceil bucket weights (sub-100-rupee parts used to
    weigh ZERO buckets so budgets could be exceeded), position-aware sprocket
    exclusivity, and the widened exclusive-category taxonomy."""

    def test_sub_bucket_parts_cannot_exceed_budget(self):
        # Three Rs99 parts at a Rs100 budget: floor-division weights made all
        # three free (weight 0) so all were selected at Rs297 total spend.
        pool = [
            _mk(1, "bodywork", 99, 0.05),
            _mk(2, "suspension", 99, 0.05),
            _mk(3, "fuel_system", 99, 0.05),
        ]
        sel = _select_build(pool, 100, "min_et")
        assert sum(r.price_inr for r in sel) <= 100, (
            f"budget exceeded: {sum(r.price_inr for r in sel)}"
        )

    def test_rear_sprockets_never_stack_with_position_map(self):
        pool = [
            _mk(11, "sprocket", 3000, 0.05),
            _mk(12, "sprocket", 3100, 0.06),
            _mk(13, "sprocket", 2900, 0.04),
        ]
        position_of = {11: "rear", 12: "rear", 13: "front"}
        sel = _select_build(pool, 100_000, "min_et", position_of=position_of)
        rears = [r.part_id for r in sel if position_of.get(r.part_id) == "rear"]
        fronts = [r.part_id for r in sel if position_of.get(r.part_id) == "front"]
        assert len(rears) <= 1, f"two rear sprockets selected: {rears}"
        # front + best rear should coexist (separate positions)
        assert fronts == [13]
        assert rears == [12]

    def test_chain_and_boost_now_exclusive(self):
        assert "chain" in _EXCLUSIVE_CATEGORIES
        assert "boost_kit" in _EXCLUSIVE_CATEGORIES
        assert "nitrous" in _EXCLUSIVE_CATEGORIES
        assert "wheelie_bar" in _EXCLUSIVE_CATEGORIES
        assert "swingarm_ext" in _EXCLUSIVE_CATEGORIES
        pool = [
            _mk(21, "chain", 8000, 0.03),
            _mk(22, "chain", 9000, 0.04),
            _mk(23, "boost_kit", 90_000, 0.50),
            _mk(24, "boost_kit", 95_000, 0.55),
        ]
        sel = _select_build(pool, 500_000, "min_et")
        from collections import Counter

        counts = Counter(r.category for r in sel)
        assert counts.get("chain", 0) <= 1
        assert counts.get("boost_kit", 0) <= 1


class TestComputePartsRoiRealFitment:
    """June 2026: compute_parts_roi consulted only the legacy compatible_bikes
    JSON, so every fitment_rules part was flagged incompatible (and
    find_best_build's parts_skipped_incompatible was fiction). With a DB-backed
    repo the production is_compatible() engine must drive the flag."""

    def _db_repo(self):
        import os
        import sqlite3

        import pytest

        db_path = os.environ.get("MOTOQUANT_TEST_DB", DB_PATH)
        if not os.path.exists(db_path):
            pytest.skip("no production DB in working tree")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        from motoquant.database.parts_repo import PartsRepository

        return conn, PartsRepository(conn)

    def test_compat_flag_uses_fitment_engine(self):
        conn, repo = self._db_repo()
        from motoquant.analysis.roi import compute_parts_roi
        from motoquant.defaults import hayabusa_gen1

        cfg = hayabusa_gen1()

        def fast(c):
            return (10.0 - (215.0 - c.chassis.dry_mass_kg) * 0.001, 60.0)

        # 48 = Hayabusa Gen1 Stage 1 flash (fits bike 3); 123 = Duke 390 tune (must not)
        rois = compute_parts_roi(cfg, [48, 123], repo, bike_model_id=3, et_fn=fast)
        by_id = {r.part_id: r for r in rois}
        assert by_id[48].is_compatible, (
            "Hayabusa flash flagged incompatible with the Hayabusa — legacy "
            "compatible_bikes fallback is back in the production path"
        )
        assert not by_id[123].is_compatible, "Duke 390 tune passed on a Hayabusa"
        conn.close()

    def test_incompatible_parts_never_selected(self):
        conn, repo = self._db_repo()
        from motoquant.analysis.roi import find_best_build
        from motoquant.defaults import hayabusa_gen1

        cfg = hayabusa_gen1()

        def fast(c):
            return (10.0 - (215.0 - c.chassis.dry_mass_kg) * 0.001, 60.0)

        build = find_best_build(
            cfg,
            budget_inr=500_000,
            parts_repo=repo,
            part_ids=[48, 123],
            bike_model_id=3,
            et_fn=fast,
        )
        chosen = {p.part_id for p in build.selected_parts}
        assert 123 not in chosen, "incompatible part entered the optimized build"
        assert build.parts_skipped_incompatible == 1
        conn.close()
