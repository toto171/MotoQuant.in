"""
Outlaw pipeline fixes (October 2026 audit), through ``optimize_outlaw``.

* The fitted drag tyre was neither deducted from the budget nor reported:
  a ₹60k budget bought ₹58.7k of parts PLUS a ₹41.4k slick (67% over) while
  total_cost_inr said ₹58,700.
* The pipeline re-applied the parts in DISPLAY order while optimize_build had
  verified them in price order, so with a boost part in the build the
  autotune stage tuned a different bike (different final boost_type) from the
  one that was priced.
"""

import sqlite3
from pathlib import Path

import pytest

from motoquant.analysis.outlaw import optimize_outlaw
from motoquant.database.bridge import db_row_to_config
from motoquant.database.parts_repo import PartsRepository
from motoquant.database.tire_repo import TireRepository

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


def _cfg(conn, bike_id):
    row = conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id=? AND config_name='stock' "
        "AND is_current=1",
        (bike_id,),
    ).fetchone()
    return db_row_to_config(dict(row), name=f"bike {bike_id}")


class _PoolRepo:
    def __init__(self, repo, ids):
        self._repo = repo
        self._ids = set(ids)
        self._conn = repo._conn

    def search(self, **kw):
        return [r for r in self._repo.search(**kw) if r["id"] in self._ids]

    def __getattr__(self, name):
        return getattr(self._repo, name)


_POOL = [354, 31, 50, 143, 56, 359, 25]


class TestTyreCostCountsAgainstTheBudget:
    def test_user_budget_covers_tyre_plus_parts(self, conn):
        out = optimize_outlaw(
            _cfg(conn, 11),
            _PoolRepo(PartsRepository(conn), _POOL),
            TireRepository(conn),
            bike_model_id=11,
            budget_inr=60_000,
            gear_span=1,
            launch_steps=3,
        )
        assert out["tire_stage"]["applied"] is True
        tyre = float(out["tire_stage"]["price_inr"])
        assert tyre > 0
        assert out["tire_cost_inr"] == pytest.approx(tyre)
        assert out["parts_budget_inr"] == pytest.approx(60_000 - tyre)
        assert out["total_cost_inr"] == pytest.approx(out["parts_cost_inr"] + tyre)
        assert out["total_cost_inr"] <= 60_000 + 1e-6

    def test_tyre_dearer_than_the_budget_is_skipped(self, conn):
        out = optimize_outlaw(
            _cfg(conn, 11),
            _PoolRepo(PartsRepository(conn), _POOL),
            TireRepository(conn),
            bike_model_id=11,
            budget_inr=20_000,
            gear_span=1,
            launch_steps=3,
        )
        assert out["tire_stage"]["applied"] is False
        assert "budget" in out["tire_stage"]["note"]
        assert out["total_cost_inr"] <= 20_000 + 1e-6


class TestPricedBikeIsTheTunedBike:
    def test_setup_stock_et_equals_the_verified_build(self, conn):
        # The build contains NA parts AND a boost part; autotune's stock run
        # (the bike rebuilt by the pipeline) must be the bike optimize_build
        # verified — same parts, same order.
        out = optimize_outlaw(
            _cfg(conn, 11),
            _PoolRepo(PartsRepository(conn), [143, 56, 50]),
            TireRepository(conn),
            bike_model_id=11,
            budget_inr=None,
            gear_span=1,
            launch_steps=3,
        )
        build = out["build"]
        assert {p["part_id"] for p in build["parts"]} >= {143}
        assert out["setup"]["stock"]["et_s"] == pytest.approx(
            build["optimized_et_s"], abs=1e-4
        )
        assert build["applied_part_ids"][-1] == 143  # boost applied last
