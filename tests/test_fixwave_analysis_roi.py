"""
roi.py fixes (October 2026 audit), driven through the production entry points
(find_best_build / recommend_build / part_slot on real catalog rows).

* noise floor: ``min_delta_et_ms`` used to zero only ``roi_score``; the
  knapsack still bought every part below it.
* candidate discovery: ``limit=200`` (after the brand-ordered compatibility
  filter) silently dropped the alphabetically-last parts of bikes with 201-205
  compatible parts (Hayabusa Gen1 lost both ZEX nitrous kits and three Öhlins
  suspension parts from every optimizer and recommender run).
* physical slots: fuel-system / bodywork / unpositioned brake parts were
  freely stackable, and a quickshifter filed under 'ecu' stacked with a real
  quickshifter.
* nitrous shares the forced-induction slot with turbo/SC kits.
* refine_build: a combined build can never be worse than a subset of itself.
"""

import copy
import sqlite3
from pathlib import Path

import pytest

from motoquant.analysis.recommendations import (
    EXCLUSIVE_GROUPS,
    BuildProfile,
    _detect_warnings,
    recommend_build,
)
from motoquant.analysis.roi import (
    PartROIResult,
    _knapsack_group_key,
    apply_order_ids,
    find_best_build,
    part_slot,
    refine_build,
)
from motoquant.database.bridge import db_row_to_config
from motoquant.database.parts_repo import PartsRepository
from motoquant.defaults import gsxr1000_k5

DB_PATH = Path(__file__).resolve().parents[1] / "motoquant.db"


@pytest.fixture(scope="module")
def conn():
    if not DB_PATH.exists():
        pytest.skip("catalog DB not present")
    c = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro&immutable=1", uri=True, check_same_thread=False
    )
    c.row_factory = sqlite3.Row
    yield c
    c.close()


@pytest.fixture(scope="module")
def repo(conn):
    return PartsRepository(conn)


def _cfg(conn, bike_id):
    row = conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id=? AND config_name='stock' "
        "AND is_current=1",
        (bike_id,),
    ).fetchone()
    return db_row_to_config(dict(row), name=f"bike {bike_id}")


class _PoolRepo:
    """The real PartsRepository restricted to a fixed candidate pool, so the
    production optimizer path runs on a small, deterministic part list."""

    def __init__(self, repo, ids):
        self._repo = repo
        self._ids = set(ids)
        self._conn = repo._conn

    def search(self, **kw):
        return [r for r in self._repo.search(**kw) if r["id"] in self._ids]

    def __getattr__(self, name):
        return getattr(self._repo, name)


def _const_et(cfg):
    """Cheap stand-in scorer: every part looks like a 10 ms gain."""
    return 10.0 - 0.01 * getattr(cfg, "_n", 0), 60.0


# ─────────────────────────── noise floor ───────────────────────────
class TestNoiseFloorSelects:
    def test_floor_excludes_parts_below_it(self, conn, repo):
        # Audit repro: with a 100 ms floor the knapsack still bought 359
        # (67 ms), 289 (32 ms) and 88 (24 ms).
        cfg = _cfg(conn, 5)
        build = find_best_build(
            cfg,
            100_000,
            repo,
            part_ids=[289, 88, 359, 375, 376],
            bike_model_id=5,
            min_delta_et_ms=100.0,
        )
        assert build.selected_parts == []
        assert build.total_cost_inr == 0.0

    def test_floor_keeps_parts_above_it(self, conn, repo):
        cfg = _cfg(conn, 5)
        build = find_best_build(
            cfg,
            100_000,
            repo,
            part_ids=[289, 88, 359, 375, 376],
            bike_model_id=5,
            min_delta_et_ms=50.0,
        )
        assert [p.part_id for p in build.selected_parts] == [359]


# ─────────────────────────── candidate pool ───────────────────────────
class TestCandidatePoolNotCut:
    def test_hayabusa_gen1_sees_every_compatible_part(self, repo):
        cfg = gsxr1000_k5()
        compatible = repo.search(bike_model_id=3, limit=10**6)
        assert len(compatible) > 200  # the case the old cap broke
        build = find_best_build(
            cfg, 10_000, repo, bike_model_id=3, et_fn=lambda c: (10.0, 60.0)
        )
        assert build.parts_evaluated == len(compatible)


# ─────────────────────────── physical slots ───────────────────────────
class TestPartSlots:
    def test_quickshifter_filed_under_ecu_is_a_quickshifter(self, repo):
        assert part_slot(repo.get(117)) == "quickshifter"
        assert part_slot(repo.get(359)) == "quickshifter"
        # a real ECU flash stays in the ECU group
        assert part_slot(repo.get(50)) is None

    def test_fuel_system_slots(self, repo):
        assert part_slot(repo.get(93)) == "fuel_system:injector"
        assert part_slot(repo.get(347)) == "fuel_system:injector"
        assert part_slot(repo.get(348)) == "fuel_system:injector"
        assert part_slot(repo.get(92)) == "fuel_system:pump"
        assert part_slot(repo.get(144)) == "fuel_system:pump"
        for pid in (94, 146, 285, 286, 287, 288, 351):
            assert part_slot(repo.get(pid)) == "fuel_system:controller", pid

    def test_bodywork_fairings_share_one_slot(self, repo):
        for pid in (107, 108, 164, 165, 166, 167, 265):
            assert part_slot(repo.get(pid)) == "bodywork:fairing", pid
        assert part_slot(repo.get(423)) == "bodywork:winglets"
        assert part_slot(repo.get(264)) == "bodywork:windscreen"

    def test_unpositioned_brake_parts_are_front_axle(self, repo):
        for pid in (101, 157, 158):  # calipers without a stated axle
            assert part_slot(repo.get(pid)) == "brakes:caliper:front", pid
        for pid in (102, 159, 160, 162, 163, 261, 370):  # pad sets
            assert part_slot(repo.get(pid)) == "brakes:pad:front", pid
        for pid in (363, 364, 366):
            assert part_slot(repo.get(pid)) == "brakes:master_cylinder:front", pid
        assert part_slot(repo.get(296)) is None  # brake fluid: no slot

    def test_suspension_fallbacks(self, repo):
        assert part_slot(repo.get(105)) == "suspension:shock"  # coilover kit
        assert part_slot(repo.get(396)) == "lowering_kit"
        assert part_slot(repo.get(398)) == "lowering_kit"

    def test_nitrous_shares_the_forced_induction_group(self):
        def mk(pid, cat):
            return PartROIResult(
                pid, "p", "b", cat, cat, 1.0, None, 10, 9.9, 0.1, 1.0, 1, 1, True, "x"
            )

        assert _knapsack_group_key(mk(1, "nitrous")) == _knapsack_group_key(
            mk(2, "boost_kit")
        )
        assert any({"boost_kit", "nitrous"} <= g for g in EXCLUSIVE_GROUPS)
        warns = _detect_warnings([mk(1, "nitrous"), mk(2, "boost_kit")])
        assert any(w.severity == "critical" for w in warns)

    def test_full_catalog_stacking_is_impossible(self, conn, repo):
        # find_best_build over every fuel-system / bodywork / brake /
        # suspension part compatible with the Hayabusa Gen2, at a budget that
        # buys them all: every selected part must own a distinct slot.
        pool = [
            p["id"]
            for p in repo.search(bike_model_id=11, limit=10**6)
            if p["category_name"] in ("fuel_system", "bodywork", "brakes", "suspension")
        ]

        def et_fn(cfg):  # every part "helps" a little: worst case for stacking
            return 10.0 - 0.01 * getattr(cfg, "_n", 0), 60.0

        class CountingRepo(_PoolRepo):
            def apply_to_config(self, pid, cfg):
                out = self._repo.apply_to_config(pid, cfg)
                out._n = getattr(cfg, "_n", 0) + 1
                return out

            def apply_multiple(self, pids, cfg):
                for pid in pids:
                    cfg = self.apply_to_config(pid, cfg)
                return cfg

        build = find_best_build(
            gsxr1000_k5(),
            5_000_000,
            CountingRepo(repo, pool),
            part_ids=pool,
            bike_model_id=11,
            et_fn=et_fn,
        )
        slots = [part_slot(repo.get(p.part_id)) for p in build.selected_parts]
        claimed = [s for s in slots if s]
        assert len(claimed) == len(set(claimed)), claimed
        fuel = [p for p in build.selected_parts if p.category == "fuel_system"]
        assert len(fuel) <= 8  # one per fuel slot (was 13 parts)
        fairings = [s for s in slots if s == "bodywork:fairing"]
        assert len(fairings) <= 1  # was 6 complete fairing kits


# ─────────────────────────── application order ───────────────────────────
class TestApplyOrder:
    def test_boost_parts_applied_last(self):
        def mk(pid, cat, price):
            return PartROIResult(
                pid, "p", "b", cat, cat, price, None, 10, 9.9, 0.1, 1.0, 1, 1, True, "x"
            )

        parts = [mk(1, "nitrous", 95_000), mk(2, "exhaust", 238_000), mk(3, "ecu", 1)]
        assert apply_order_ids(parts) == [3, 2, 1]


# ─────────────────────────── refine_build ───────────────────────────
class TestRefineBuild:
    def _mk(self, pid, cat, price, det):
        return PartROIResult(
            pid,
            f"p{pid}",
            "b",
            cat,
            cat,
            price,
            None,
            10,
            10 - det,
            det,
            0.0,
            1,
            1,
            True,
            "x",
        )

    def test_sprocket_pair_rechosen_jointly(self):
        # Front and rear sprockets each help alone but over-gear together;
        # the knapsack picks both, refine_build must keep only the better one.
        front, rear = (
            self._mk(1, "sprocket", 100, 0.10),
            self._mk(2, "sprocket", 100, 0.11),
        )
        other = self._mk(3, "exhaust", 100, 0.05)
        table = {
            (): 10.0,
            (1,): 9.90,
            (2,): 9.89,
            (1, 2): 10.15,
            (3,): 9.95,
            (1, 3): 9.85,
            (2, 3): 9.84,
            (1, 2, 3): 10.10,
        }

        class Repo:
            def apply_multiple(self, pids, cfg):
                cfg = copy.deepcopy(cfg)
                cfg._ids = tuple(sorted(pids))
                return cfg

        def et_fn(cfg):
            return table[getattr(cfg, "_ids", ())], 60.0

        slot_of = {1: "sprocket:front", 2: "sprocket:rear"}
        out = refine_build(
            gsxr1000_k5(),
            [front, rear, other],
            [front, rear, other],
            10_000,
            Repo(),
            et_fn,
            group_key=lambda r: _knapsack_group_key(r, None, slot_of),
        )
        assert sorted(r.part_id for r in out.selected) == [2, 3]
        assert out.et_s == pytest.approx(9.84)
        assert out.gearing_changed is True

    def test_drop_one_removes_a_part_that_hurts_the_build(self):
        a, b = self._mk(1, "exhaust", 100, 0.1), self._mk(2, "ecu", 100, 0.1)
        table = {(): 10.0, (1,): 9.9, (2,): 9.9, (1, 2): 9.95}

        class Repo:
            def apply_multiple(self, pids, cfg):
                cfg = copy.deepcopy(cfg)
                cfg._ids = tuple(sorted(pids))
                return cfg

        out = refine_build(
            gsxr1000_k5(),
            [a, b],
            [a, b],
            10_000,
            Repo(),
            lambda cfg: (table[getattr(cfg, "_ids", ())], 60.0),
        )
        assert len(out.selected) == 1
        assert out.et_s == pytest.approx(9.9)
        assert len(out.dropped) == 1


# ─────────────────────────── recommend_build ───────────────────────────
class TestRecommendNextUpgrade:
    def test_next_upgrade_never_refills_an_occupied_slot(self, conn, repo):
        # Audit repro: bike 77 build held front sprocket 210 and the next
        # upgrade offered front sprocket 211 (which made it 0.13 s SLOWER).
        cfg = _cfg(conn, 77)
        pool = _PoolRepo(repo, [210, 211, 231, 233])
        rec = recommend_build(
            cfg,
            8_000,
            pool,
            profile=BuildProfile.STREET_LEGAL,
            bike_model_id=77,
        )
        chosen = {p.part_id for p in rec.build.selected_parts}
        nu = rec.next_upgrade
        if nu is not None:
            # 210/211 are both front sprockets, 231/233 both air filters.
            assert not ({210, 211} <= chosen | {nu.part.part_id})
            assert not ({231, 233} <= chosen | {nu.part.part_id})
            assert nu.marginal_et_gain_s > 0
