"""The site's leaderboard data must match the current physics and catalog.

``web/app/leaderboard/stock_times.json`` is a cache of the simulator (see
``scripts/gen_stock_leaderboard.py``). These checks fail when it goes stale:
a bike added or removed, or a physics change that moves stock times.
"""

from __future__ import annotations

import json
import random
import shutil
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

REPO = Path(__file__).resolve().parent.parent
DATA = json.loads(
    (REPO / "web" / "app" / "leaderboard" / "stock_times.json").read_text("utf-8")
)
REGEN = "regenerate with: python scripts/gen_stock_leaderboard.py"


def _current_bike_ids() -> set[int]:
    conn = sqlite3.connect(f"file:{REPO / 'motoquant.db'}?mode=ro", uri=True)
    try:
        return {
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT bike_model_id FROM bike_configs WHERE is_current = 1"
            )
        }
    finally:
        conn.close()


def test_every_current_bike_is_on_the_board():
    listed = {b["id"] for b in DATA["bikes"]} | set(DATA["did_not_finish"])
    assert listed == _current_bike_ids(), REGEN


def test_board_is_sorted_by_time():
    times = [b["et_s"] for b in DATA["bikes"]]
    assert times == sorted(times)


@pytest.fixture(scope="module")
def api_on_copy(tmp_path_factory):
    import os

    path = tmp_path_factory.mktemp("lb") / "motoquant.db"
    shutil.copyfile(REPO / "motoquant.db", path)
    prior = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = str(path)
    from motoquant import api, engine_select

    api._db_conn = None
    yield api, engine_select
    api._db_conn = None
    if prior is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = prior


def test_sampled_times_match_the_simulator(api_on_copy):
    api, engine_select = api_on_copy
    bikes = DATA["bikes"]
    sample = [bikes[0], bikes[len(bikes) // 2], bikes[-1]]
    sample += random.Random(7).sample(bikes, 5)
    for b in sample:
        cfg = api._build_config(
            bike_id=b["id"],
            bike_preset=None,
            power_boost_pct=0.0,
            mass_delta_kg=0.0,
            rider_mass_kg=float(DATA["rider_kg"]),
        )
        sim = engine_select.make_engine(cfg).run()
        assert round(float(sim.time_quarter), 3) == b["et_s"], (b["model"], REGEN)


def test_conditions_are_the_server_defaults(api_on_copy):
    api, _ = api_on_copy
    cfg = api._build_config(
        bike_id=DATA["bikes"][0]["id"],
        bike_preset=None,
        power_boost_pct=0.0,
        mass_delta_kg=0.0,
        rider_mass_kg=75.0,
    )
    echo = api._environment_echo(cfg)
    for key, value in DATA["conditions"].items():
        assert echo[key] == value, (key, REGEN)
