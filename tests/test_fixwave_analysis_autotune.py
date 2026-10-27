"""
ecu_autotune fixes (October 2026 audit), through ``autotune()`` itself.

* Launch-RPM sweep: staging.launch_rpm is only honoured with a two-step, and
  520 of 541 catalog configs have none — the old sweep ran N identical sims
  and then "recommended" the lowest grid point (min() tie-break) with a made-up
  "reduces wheelspin" rationale, reporting the unused 8000 rpm dataclass
  default as the stock launch RPM (above a Street Bob's redline).
* Gearing sweep: clamped to 28-56 teeth, so belt bikes (66T pulleys) were
  "swept" over a single never-stock 56T candidate and told to fit it.
"""

import copy
import sqlite3
from pathlib import Path

import pytest

from motoquant import engine_select
from motoquant.analysis.ecu_autotune import autotune
from motoquant.database.bridge import db_row_to_config
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


def _cfg(conn, bike_id):
    row = conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id=? AND config_name='stock' "
        "AND is_current=1",
        (bike_id,),
    ).fetchone()
    return db_row_to_config(dict(row), name=f"bike {bike_id}")


def _et(cfg):
    return float(engine_select.make_engine(cfg).run().time_quarter)


class TestLaunchSweep:
    def test_street_bob_reports_the_real_launch_and_no_fake_advice(self, conn):
        cfg = _cfg(conn, 4600)  # Harley-Davidson Street Bob 114, no two-step
        assert cfg.staging.two_step is False
        res = autotune(cfg, gear_span=1, launch_steps=6)
        lr = res.launch_rpm
        # It launches at peak-torque RPM, not the unused 8000 rpm default.
        assert lr["stock_rpm"] == pytest.approx(cfg.engine.peak_torque_rpm, abs=1)
        assert lr["stock_rpm"] < cfg.engine.redline_rpm
        if lr["delta_et_s"] >= 0:
            assert lr["changed"] is False
            assert lr["recommended_rpm"] == lr["stock_rpm"]
            assert "no change" in lr["rationale"]
        else:
            assert lr["requires_two_step"] is True

    def test_sweep_candidates_actually_differ(self):
        # The K5 reference has no two-step either: every candidate used to
        # simulate the exact same 9.9331 s.
        cfg = gsxr1000_k5()
        assert cfg.staging.two_step is False
        res = autotune(cfg, gear_span=1, launch_steps=6)
        ets = {c["et_s"] for c in res.launch_rpm["candidates"]}
        assert len(ets) > 1, "launch sweep is dead (all candidates identical)"
        stock = [c for c in res.launch_rpm["candidates"] if c["is_stock"]]
        assert len(stock) == 1
        assert stock[0]["et_s"] == pytest.approx(round(_et(cfg), 4), abs=1e-4)

    def test_recommended_launch_is_what_the_combined_run_uses(self, conn):
        cfg = _cfg(conn, 11)
        res = autotune(cfg, gear_span=1, launch_steps=6)
        lr, g = res.launch_rpm, res.gearing
        check = copy.deepcopy(cfg)
        if g.get("adjustable"):
            check.drivetrain.rear_sprocket = int(g["recommended_rear"])
        if lr["changed"]:
            check.staging.two_step = True
            check.staging.launch_rpm = float(lr["recommended_rpm"])
        assert res.combined["et_s"] == pytest.approx(round(_et(check), 4), abs=1e-4)


class TestGearingSweep:
    def test_belt_bike_is_not_given_sprocket_advice(self, conn):
        cfg = _cfg(conn, 4600)  # 32/66 belt pulleys, no chain pitch on record
        res = autotune(cfg, gear_span=2, launch_steps=3)
        assert res.gearing["adjustable"] is False
        assert "fixed" in res.gearing["recommendation"]
        assert res.gearing["delta_et_s"] == 0.0

    def test_sweep_window_follows_the_stock_sprocket(self):
        # A chain bike with a big rear sprocket: the old absolute 56T cap
        # collapsed every candidate to 56 and never simulated stock.
        cfg = gsxr1000_k5()
        cfg.drivetrain.front_sprocket = 28
        cfg.drivetrain.rear_sprocket = 66
        res = autotune(cfg, gear_span=2, launch_steps=3)
        teeth = [c["rear_sprocket"] for c in res.gearing["candidates"]]
        assert 66 in teeth
        assert max(teeth) > 56
        assert len(set(teeth)) > 1
        stock = [c for c in res.gearing["candidates"] if c["is_stock"]]
        assert stock and stock[0]["rear_sprocket"] == 66

    def test_engine_is_reported(self):
        res = autotune(gsxr1000_k5(), gear_span=1, launch_steps=3)
        assert res.engine == ("native" if engine_select.native_active() else "python")
