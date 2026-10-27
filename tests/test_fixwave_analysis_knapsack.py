"""
Grouped (multiple-choice) knapsack: NumPy rewrite must pick EXACTLY what the
legacy pure-Python DP picked, and the outlaw ₹5M budget must be cheap.

October 2026 audit: at the outlaw "no-limit" ₹5M budget the legacy DP copied a
choice list per ₹100 bucket per group — ~80 s of GIL-held CPU and ~47 MB per
call, up to 4 calls per request. ``roi._grouped_knapsack`` is now a NumPy DP
with back-pointers plus an exact fast path for non-binding budgets. These
tests pin:

* identical picks (same parts, same order) against a verbatim copy of the
  legacy implementation on a seeded random battery (ties, free parts,
  sub-₹100 prices, non-positive gains, budgets from 0 to beyond the total)
  and on real catalog instances (real prices + real slot groups);
* the ₹5M case finishing in a fraction of a second.
"""

import random
import sqlite3
import time
from pathlib import Path

import pytest

from motoquant.analysis.roi import (
    PartROIResult,
    _bucket_weight,
    _grouped_knapsack,
    _knapsack_group_key,
    part_slots,
)

DB_PATH = Path(__file__).resolve().parents[1] / "motoquant.db"


def _legacy_grouped_knapsack(candidates, budget_inr, gain, group_key):
    """Verbatim copy of roi._grouped_knapsack before October 2026."""
    BUCKET = 100
    SCALE = 1_000
    W = int(budget_inr // BUCKET) if budget_inr > 0 else 0

    groups: dict = {}
    for r in candidates:
        groups.setdefault(group_key(r), []).append(r)

    dp = [0] * (W + 1)
    choice: list[list] = [[] for _ in range(W + 1)]
    for items in groups.values():
        new_dp = dp[:]
        new_choice = [c[:] for c in choice]
        for r in items:
            v = int(round(gain(r) * SCALE))
            if v <= 0:
                continue
            w = _bucket_weight(r.price_inr, BUCKET)
            if w > W:
                continue
            for cap in range(W, w - 1, -1):
                cand = dp[cap - w] + v
                if cand > new_dp[cap]:
                    new_dp[cap] = cand
                    new_choice[cap] = choice[cap - w] + [r]
        dp = new_dp
        choice = new_choice
    return choice[W]


def _mk(pid, cat, price, det, dtrap=0.0):
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
        roi_score=0.0,
        cost_per_tenth_inr=float("inf"),
        is_compatible=True,
        availability="in_stock",
    )


def _ids(parts):
    return [r.part_id for r in parts]


def _gain_et(r):
    return r.delta_et_s


def _gain_trap(r):
    return r.delta_trap_ms


_CATS = ("exhaust", "ecu", "air_filter", "sprocket", "bodywork", "brakes", "x")


def _random_instance(rng: random.Random):
    n = rng.randint(1, 26)
    parts = []
    for i in range(n):
        cat = rng.choice(_CATS)
        price = rng.choice(
            [
                0,
                rng.randint(1, 99),
                rng.randint(100, 5_000),
                rng.randint(5_000, 60_000),
                rng.choice([1_000, 2_000, 5_000]),  # repeated weights -> ties
            ]
        )
        det = rng.choice(
            [
                round(rng.uniform(-0.05, 0.4), 4),
                round(rng.uniform(0.0, 0.0006), 5),  # rounds to 0 at SCALE=1000
                rng.choice([0.05, 0.1, 0.2]),  # repeated values -> ties
            ]
        )
        dtrap = round(rng.uniform(-1.0, 4.0), 3)
        parts.append(_mk(i + 1, cat, price, det, dtrap))
    total = sum(p.price_inr for p in parts)
    budget = rng.choice(
        [0, rng.uniform(0, total), total, total * 2 + 1, rng.randint(0, 3_000)]
    )
    # group structure: real category groups, a random slot map, singletons
    slot_of = {
        p.part_id: rng.choice(["slotA", "slotB", "slotC"])
        for p in parts
        if rng.random() < 0.3
    }
    position_of = {
        p.part_id: rng.choice(["front", "rear"])
        for p in parts
        if p.category == "sprocket" and rng.random() < 0.7
    }
    return parts, budget, slot_of, position_of


class TestIdenticalPicksRandomBattery:
    @pytest.mark.parametrize("seed", range(6))
    def test_random_instances_match_legacy(self, seed):
        rng = random.Random(1_000 + seed)
        for _ in range(120):
            parts, budget, slot_of, position_of = _random_instance(rng)

            def key(r, position_of=position_of, slot_of=slot_of):
                return _knapsack_group_key(r, position_of, slot_of)

            for gain in (_gain_et, _gain_trap):
                new = _grouped_knapsack(parts, budget, gain, key)
                old = _legacy_grouped_knapsack(parts, budget, gain, key)
                assert _ids(new) == _ids(old), (
                    f"picks diverged (seed={seed}, budget={budget}): "
                    f"new={_ids(new)} old={_ids(old)}"
                )

    def test_ties_resolve_to_first_item_like_legacy(self):
        # Three equal-value, equal-weight items in one group plus a binding
        # budget: the legacy strict ">" keeps the FIRST in group order.
        parts = [
            _mk(1, "exhaust", 5_000, 0.1),
            _mk(2, "exhaust", 5_000, 0.1),
            _mk(3, "exhaust", 5_000, 0.1),
            _mk(4, "ecu", 5_000, 0.1),
            _mk(5, "ecu", 5_000, 0.1),
        ]
        for budget in (5_000, 9_999, 10_000, 1_000_000):
            new = _grouped_knapsack(parts, budget, _gain_et, _knapsack_group_key)
            old = _legacy_grouped_knapsack(parts, budget, _gain_et, _knapsack_group_key)
            assert _ids(new) == _ids(old)


def _catalog_rows():
    if not DB_PATH.exists():
        pytest.skip("catalog DB not present")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    rows = [
        dict(r)
        for r in conn.execute(
            """SELECT p.*, pc.name AS category_name
                 FROM parts p JOIN parts_categories pc ON pc.id = p.category_id
                ORDER BY p.brand, p.model_name"""
        )
    ]
    conn.close()
    return rows


class TestIdenticalPicksRealCatalog:
    """Real prices and real physical-slot groups (part_slot), gains from a
    deterministic hash so the instance is fixed and has ties."""

    @pytest.mark.parametrize("chunk", range(4))
    def test_catalog_instances_match_legacy(self, chunk):
        rows = _catalog_rows()
        rng = random.Random(77 + chunk)
        sample = rng.sample(rows, 120)
        slot_of = part_slots(sample)
        position_of = {
            pid: s.split(":", 1)[1]
            for pid, s in slot_of.items()
            if s.startswith("sprocket:")
        }
        parts = [
            _mk(
                r["id"],
                r["category_name"],
                r["price_inr"] or 0.0,
                # quantised to 5 ms steps -> plenty of value ties
                round(((r["id"] * 2654435761) % 60) * 0.005 - 0.02, 3),
                ((r["id"] * 40503) % 50) * 0.1 - 1.0,
            )
            for r in sample
        ]

        def key(r):
            return _knapsack_group_key(r, position_of, slot_of)

        for budget in (0, 3_000, 25_000, 90_000, 200_000):
            for gain in (_gain_et, _gain_trap):
                new = _grouped_knapsack(parts, budget, gain, key)
                old = _legacy_grouped_knapsack(parts, budget, gain, key)
                assert _ids(new) == _ids(old), f"budget={budget}"

    def test_fast_path_matches_legacy_when_budget_covers_everything(self):
        rows = _catalog_rows()
        sample = random.Random(5).sample(rows, 60)
        slot_of = part_slots(sample)
        parts = [
            _mk(r["id"], r["category_name"], (r["price_inr"] or 0.0) / 50.0, 0.05)
            for r in sample
        ]
        budget = sum(p.price_inr for p in parts) + 1_000

        def key(r):
            return _knapsack_group_key(r, None, slot_of)

        new = _grouped_knapsack(parts, budget, _gain_et, key)
        old = _legacy_grouped_knapsack(parts, budget, _gain_et, key)
        assert _ids(new) == _ids(old)


class TestOutlawBudgetIsCheap:
    def test_five_million_budget_runs_in_well_under_a_second(self):
        # The audit's repro: 200 singleton candidates at the ₹5M outlaw cap
        # cost ~80 s in the legacy DP. Budget not binding -> exact fast path.
        rng = random.Random(3)
        parts = [
            _mk(i, "x", rng.randint(1_000, 20_000), rng.uniform(0.001, 0.2))
            for i in range(200)
        ]
        t0 = time.perf_counter()
        picks = _grouped_knapsack(parts, 5_000_000, _gain_et, _knapsack_group_key)
        assert time.perf_counter() - t0 < 1.0
        assert len(picks) == 200  # every positive singleton is affordable

    def test_binding_five_million_budget_dp_is_bounded(self):
        # Budget binding at ₹5M (W = 50,000 buckets) -> the real NumPy DP
        # path, not the fast path. Legacy cost here is minutes.
        rng = random.Random(4)
        parts = [
            _mk(i, rng.choice(_CATS), rng.randint(20_000, 400_000), rng.uniform(0, 1))
            for i in range(200)
        ]
        assert sum(p.price_inr for p in parts) > 5_000_000
        t0 = time.perf_counter()
        picks = _grouped_knapsack(parts, 5_000_000, _gain_et, _knapsack_group_key)
        assert time.perf_counter() - t0 < 10.0
        assert sum(p.price_inr for p in picks) <= 5_000_000
        keys = [_knapsack_group_key(p) for p in picks]
        assert len(keys) == len(set(keys))  # one part per group
