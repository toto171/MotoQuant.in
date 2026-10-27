"""
Natural-language runner fixes (October 2026 audit), through
``NLSimRunner.run_query`` / ``NLQueryParser.parse`` and the ``nl`` CLI.

* run_query DISCARDED apply_part_to_config's return value, so "with nitrous
  and exhaust" simulated the stock bike — and the parts it reported were the
  first alphabetical rows of the whole category (a Harley nitrous kit and a
  Rocket 3 exhaust on a Hayabusa).
* Budgets stopped at the first comma ("50,000" -> ₹50) and ignored k / lakh.
* "3 m/s headwind" also set altitude_m=3; "brake discs" mentioned a
  supercharger ("sc"), "wet track" a clutch ("wet").
* Track prep was written to environment.track_prep, which physics never reads.
* "k5" resolved to BMW R 1250 RT (model code K52), "r1" to R 12 nineT.
"""

import argparse
import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.nlp import NLQueryParser, NLSimRunner
from motoquant.parts.compatibility import is_compatible

DB_PATH = Path(__file__).resolve().parents[1] / "motoquant.db"


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    if not DB_PATH.exists():
        pytest.skip("catalog DB not present")
    path = tmp_path_factory.mktemp("nl") / "motoquant.db"
    shutil.copy(DB_PATH, path)
    d = MotoQuantDB(str(path))
    d.connect()
    yield d
    d.close()


@pytest.fixture(scope="module")
def runner(db):
    return NLSimRunner(db)


class TestPartsAreReallyApplied:
    def test_mentioned_parts_change_the_et_and_fit_the_bike(self, runner, db):
        stock = runner.run_query("my hayabusa at aamby valley")
        modded = runner.run_query(
            "my hayabusa with nitrous and exhaust at aamby valley"
        )
        assert modded["applied_part_ids"], modded
        assert modded["et_s"] < stock["et_s"] - 0.05, (stock["et_s"], modded["et_s"])
        from motoquant.database.parts_repo import enrich_bike_row_for_fitment

        bike = runner._resolve_bike("hayabusa")
        bike_row = dict(
            db.conn.execute(
                "SELECT * FROM bike_models WHERE id = ?", (bike["id"],)
            ).fetchone()
        )
        enrich_bike_row_for_fitment(db.conn, bike_row)
        for pid in modded["applied_part_ids"]:
            assert is_compatible(db.parts.get(pid), bike_row)[0], pid

    def test_turbo_mention_fits_a_turbo_kit(self, runner, db):
        out = runner.run_query("my hayabusa with turbo at aamby valley")
        assert out["applied_part_ids"], out
        import json

        part = db.parts.get(out["applied_part_ids"][0])
        assert (
            json.loads(part["param_overrides"])["forced_induction.boost_type"]
            == "turbo"
        )

    def test_track_prep_reaches_the_physics(self, runner):
        # Hayabusa Gen2's stock row has no prep; on VHT it hooks up harder.
        bare = runner.run_query("my hayabusa gen2 at aamby valley")
        prepped = runner.run_query("my hayabusa gen2 at aamby valley on vht prep")
        assert "Gen2" in bare["bike_name"]
        assert prepped["et_s"] < bare["et_s"] - 0.1


class TestParser:
    @pytest.mark.parametrize(
        "query,budget",
        [
            ("budget of 50,000 inr", 50_000),
            ("budget 1.5 lakh", 150_000),
            ("budget 50k", 50_000),
            ("spend ₹75,000 on my k5", 75_000),
            ("budget 100000", 100_000),
        ],
    )
    def test_budget_amounts(self, query, budget):
        assert NLQueryParser().parse(query).budget_inr == budget

    def test_wind_speed_is_not_an_altitude(self):
        p = NLQueryParser().parse("k5 at aamby with 3 m/s headwind")
        assert p.altitude_m is None
        assert p.headwind_ms == pytest.approx(3.0)
        assert NLQueryParser().parse("my k5 at 1200m altitude").altitude_m == 1200

    def test_keywords_match_whole_words(self):
        assert NLQueryParser().parse("new brake discs").parts_mentioned == ["brakes"]
        assert NLQueryParser().parse("my k5 on a wet track").parts_mentioned == []
        assert "supercharger" in NLQueryParser().parse("with an sc kit").parts_mentioned


class TestBikeResolution:
    @pytest.mark.parametrize(
        "query,model,code",
        [
            ("k5", "GSX-R 1000", "K5"),
            ("r1", "YZF-R1", "4C8"),
            ("busa", "Hayabusa", None),
        ],
    )
    def test_short_codes_resolve_to_the_right_bike(self, runner, query, model, code):
        bike = runner._resolve_bike(query)
        assert bike is not None
        assert model in bike["model_name"]
        if code:
            assert bike["model_code"] == code


class TestCli:
    def _run(self, db, query):
        import re

        from motoquant import run

        args = argparse.Namespace(
            query=query, db=str(db.path), output_json=False, verbose=False
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run.cmd_nl(args)
        assert rc == 0
        out = buf.getvalue()
        return out, float(re.search(r"ET:\s+([\d.]+)s", out).group(1))

    def test_nl_cli_simulates_the_modified_bike(self, db):
        stock_out, stock_et = self._run(db, "my hayabusa at aamby valley")
        out, et = self._run(db, "my hayabusa with exhaust at aamby valley")
        assert "Parts:" in out
        assert et < stock_et, (stock_et, et)


class TestSamePhysicsAsTheApi:
    def test_nl_et_matches_the_api_config_path(self, runner, db):
        # BikeRepository.to_config preferred a stale dyno_curves row: the NL
        # answer for an R15 V3 was 16.51 s while /api/simulate said 18.79 s.
        from motoquant.database.bridge import db_row_to_config
        from motoquant.engine_select import make_engine

        out = runner.run_query("my r15 v3 at aamby valley")
        assert "R15 V3" in out["bike_name"]
        bike = runner._resolve_bike("r15 v3")
        row = db.conn.execute(
            "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 "
            "AND config_name='stock'",
            (bike["id"],),
        ).fetchone()
        cfg = db_row_to_config(dict(row), name="api path")
        venue = next(
            v for v in db.venues.list_all() if v["name"].lower().startswith("aamby")
        )
        assert "Aamby" in (out["environment"]["venue"] or "")
        assert out["environment"]["altitude_m"] == pytest.approx(venue["altitude_m"])
        cfg.environment.venue_name = venue["name"]
        cfg.environment.altitude_m = float(venue["altitude_m"])
        cfg.environment.track_surface = (venue["surface_type"] or "asphalt").lower()
        assert out["et_s"] == pytest.approx(
            round(float(make_engine(cfg).run().time_quarter), 4), abs=1e-4
        )


class TestVenueResolution:
    @pytest.mark.parametrize(
        "query,needle",
        [
            ("my k5 at santa pod", "Santa Pod"),
            ("my k5 at hyderabad", "Hyderabad"),
            ("my k5 at al-ain", "Al-Ain"),
        ],
    )
    def test_named_venue_is_applied(self, runner, db, query, needle):
        # The alias table yields "santa pod" but the catalog row is "Santa
        # Pod Raceway (UK)" (short name santa_pod): the old exact-name lookup
        # missed, so the run silently used the default Aamby environment.
        out = runner.run_query(query)
        venue = next(v for v in db.venues.list_all() if needle in v["name"])
        assert out["environment"]["venue"] == venue["name"]
        assert out["environment"]["altitude_m"] == pytest.approx(venue["altitude_m"])
