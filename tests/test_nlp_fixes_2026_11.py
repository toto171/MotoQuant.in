"""
Regression tests for the November 2026 natural-language (``motoquant.nlp``)
audit fixes. Queries run end to end against a COPY of the shipped catalog and
assert the CONFIG changed as intended and ET moved the right way.

  F2  named parts are chosen by fitment + ROI and actually applied
  F3  altitude needs altitude context; wind in m/s, km/h and mph; word-
      boundary part keywords
  F4  track prep reaches the field the physics reads (tires.track_prep_type)
  plus: an ambiguous short bike name resolves to the commonly-benchmarked bike.
"""

from __future__ import annotations

import os
import shutil

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.models import TRACK_RUBBER
from motoquant.nlp import NLQueryParser, NLSimRunner

REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("nlp_fixes") / "t.db"
    shutil.copyfile(REPO_DB, path)
    d = MotoQuantDB(str(path))
    d.connect()
    yield d
    d.close()


@pytest.fixture(scope="module")
def runner(db):
    return NLSimRunner(db)


@pytest.fixture(scope="module")
def base(runner):
    return runner.run_query("simulate my Hayabusa")


@pytest.fixture(scope="module")
def parser():
    return NLQueryParser()


def _compatible_ids(db, bike_id):
    from motoquant.analysis.roi import _ALL_PARTS_LIMIT

    return {
        p["id"] for p in db.parts.search(bike_model_id=bike_id, limit=_ALL_PARTS_LIMIT)
    }


# ───────────────────────────── F2 parts really applied ─────────────────────────────
class TestPartsApplied:
    def test_exhaust_is_compatible_applied_and_quicker(self, runner, db, base):
        out = runner.run_query("simulate my Hayabusa with exhaust")
        assert "error" not in out
        assert len(out["applied_part_details"]) == 1
        detail = out["applied_part_details"][0]
        bike_id = runner._resolve_bike("hayabusa")["id"]
        assert detail["part_id"] in _compatible_ids(db, bike_id)
        assert detail["category"] == "exhaust"
        assert out["delta_et_s"] < -0.01  # with parts - without: negative = quicker
        assert out["et_s"] < base["et_s"]

    def test_nitrous_and_turbo_apply_and_pick_the_right_kit(self, runner, base):
        nit = runner.run_query("my Hayabusa with nitrous")
        assert nit["applied_part_details"] and nit["et_s"] < base["et_s"]
        turbo = runner.run_query("my Hayabusa with a turbo")
        assert turbo["applied_part_details"]
        assert "turbo" in turbo["applied_part_details"][0]["name"].lower()
        assert turbo["et_s"] < base["et_s"] - 0.1

    def test_part_is_checked_for_fit_on_non_hayabusa_bikes(self, runner, db):
        out = runner.run_query("my k5 with exhaust")
        bike_id = runner._resolve_bike("k5")["id"]
        assert out["applied_part_details"]
        assert out["applied_part_details"][0]["part_id"] in _compatible_ids(db, bike_id)

    def test_unfittable_category_is_reported_not_faked(self, runner):
        # The reference Hayabusa launches on a prepped strip and is not
        # traction-limited: the best drag tyre in its fitment table does not
        # make it quicker, so nothing is applied and the result says so.
        out = runner.run_query("my Hayabusa with slick tire")
        assert out["applied_parts"] == []
        assert [m["category"] for m in out["parts_not_applied"]] == ["tire"]
        assert out["unavailable_parts"] == ["tire"]
        assert out["delta_et_s"] == 0.0
        # A bike with no drag tyre in its fitment table: reported, not faked.
        none = runner.run_query("my Duke 390 with drag tyre")
        assert none["applied_parts"] == []
        assert "no drag tyre" in none["parts_not_applied"][0]["reason"]

    def test_drag_tyre_is_applied_when_it_makes_the_bike_quicker(self, runner):
        # Tyres are not catalog parts: a "slick" request is met from the
        # bike's drag-prep fitment table, and only when the sim gains from it.
        stock = runner.run_query("my Hayabusa Gen2")
        out = runner.run_query("my Hayabusa Gen2 with slick")
        assert [d["category"] for d in out["applied_part_details"]] == ["tire"]
        assert out["applied_part_details"][0]["part_id"] is None
        assert out["applied_part_ids"] == []
        assert out["applied_cost_inr"] == out["applied_part_details"][0]["price_inr"]
        assert out["delta_et_s"] < -0.01
        assert out["et_s"] < stock["et_s"] - 0.01
        # ...and never over a stated budget.
        poor = runner.run_query("my Hayabusa Gen2 with slick budget 1000")
        assert poor["applied_parts"] == []
        assert "budget" in poor["parts_not_applied"][0]["reason"]

    def test_one_forced_induction_system_and_parts_in_build_order(self, runner):
        # Turbo and nitrous both write forced_induction.boost_type: fitting
        # the second would silently erase the first.
        both = runner.run_query("my Hayabusa with turbo and nitrous and exhaust")
        cats = [d["category"] for d in both["applied_part_details"]]
        assert cats == ["exhaust", "turbo"]  # NA part first, then the boost kit
        assert [m["category"] for m in both["parts_not_applied"]] == ["nitrous"]
        assert "one forced-induction system" in both["parts_not_applied"][0]["reason"]
        turbo = runner.run_query("my Hayabusa with turbo")
        assert both["et_s"] < turbo["et_s"]  # the exhaust still counts
        assert both["applied_part_ids"] == [
            d["part_id"] for d in both["applied_part_details"]
        ]

    def test_the_part_with_the_largest_gain_in_budget_is_chosen(self, runner, db):
        from motoquant.analysis.roi import compute_parts_roi

        bike_id = runner._resolve_bike("hayabusa")["id"]
        out = runner.run_query("my Hayabusa with exhaust budget 1 lakh")
        chosen = out["applied_part_details"][0]
        rows = db.parts.search(category="exhaust", bike_model_id=bike_id, limit=10_000)
        from motoquant.database.bridge import db_row_to_config

        cfg = db_row_to_config(dict(db.bikes.get_current_config(bike_id)), name="x")
        rois = compute_parts_roi(cfg, [r["id"] for r in rows], db.parts)
        affordable = [r for r in rois if r.price_inr <= 100_000 and r.delta_et_s > 0]
        best = max(affordable, key=lambda r: (r.delta_et_s, -r.price_inr))
        assert chosen["part_id"] == best.part_id
        assert chosen["price_inr"] <= 100_000


# ───────────────────────── F3 altitude / wind / keywords ─────────────────────────
class TestEnvironmentParsing:
    def test_wind_in_m_per_s_does_not_set_altitude(self, runner, base):
        out = runner.run_query("simulate my Hayabusa with 5 m/s headwind")
        env = out["environment"]
        assert env["altitude_m"] == base["environment"]["altitude_m"]
        assert env["wind_speed_ms"] == pytest.approx(5.0)
        assert env["wind_direction_deg"] == 0.0
        assert out["et_s"] > base["et_s"]  # headwind is slower

    def test_wind_in_kmh_and_mph(self, runner, base, parser):
        kmh = runner.run_query("my Hayabusa with a 36 km/h headwind")
        assert kmh["environment"]["wind_speed_ms"] == pytest.approx(10.0)
        assert kmh["et_s"] > base["et_s"]
        mph = runner.run_query("my Hayabusa with a 15 mph tailwind")
        assert mph["environment"]["wind_speed_ms"] == pytest.approx(6.7056, abs=1e-3)
        assert mph["environment"]["wind_direction_deg"] == 180.0
        assert mph["et_s"] < base["et_s"]  # tailwind helps
        # a wind speed in mph is not a request to maximise trap speed
        assert parser.parse("my busa with 15 mph tailwind").optimization_goal == (
            "minimize_et"
        )

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("at altitude 1500 m", 1500.0),
            ("1200 m altitude", 1200.0),
            ("at 2000 ft elevation", 609.6),
            ("5 m/s headwind", None),
            ("a 10 m run-up", None),
            ("1000m", None),
        ],
    )
    def test_altitude_requires_context(self, parser, text, expected):
        got = parser.parse(f"my busa {text}").altitude_m
        assert got == (pytest.approx(expected) if expected is not None else None)

    def test_high_altitude_query_is_slower(self, runner, base):
        out = runner.run_query("my Hayabusa at altitude 2500 m")
        assert out["environment"]["altitude_m"] == 2500.0
        assert out["et_s"] > base["et_s"]

    def test_substring_keywords_no_longer_misfire(self, parser):
        assert parser.parse("wet track, my busa").parts_mentioned == []
        assert parser.parse(
            "my busa on a scrub of a map of the pod"
        ).parts_mentioned == [
            "air_filter",
            "ecu",
        ]
        assert parser.parse("get a set of numbers").optimization_goal == "minimize_et"
        assert parser.parse("my busa wet clutch").parts_mentioned == ["clutch"]

    def test_wet_track_applies_no_clutch_part(self, runner):
        out = runner.run_query("my Hayabusa on a wet track")
        assert out["applied_parts"] == []
        assert out["parsed_query"]["parts_mentioned"] == []


# ───────────────────────────────── F4 track prep ─────────────────────────────────
class TestTrackPrep:
    def test_track_prep_reaches_the_tyre_field_the_physics_reads(self, runner):
        # The stock Gen2 Hayabusa row has no prep and its launch is
        # traction-limited, so prep must make it measurably quicker. (A small
        # single such as the 390 Duke is not traction-limited under the 1-ft
        # rollout timing: its ET moves by ~0.1 ms, which proves nothing.)
        plain = runner.run_query("my Hayabusa Gen2")
        prepped = runner.run_query("my Hayabusa Gen2 with rubber buildup")
        assert "Gen2" in plain["bike_name"]
        assert plain["environment"]["track_prep"] != TRACK_RUBBER
        assert prepped["environment"]["track_prep"] == TRACK_RUBBER
        assert prepped["et_s"] < plain["et_s"] - 0.02
        small = runner.run_query("my 390 duke with rubber buildup")
        assert small["environment"]["track_prep"] == TRACK_RUBBER


# ─────────────────────────────── bike resolution ───────────────────────────────
class TestBikeResolution:
    def test_duke_resolves_to_the_390_not_the_125(self, runner):
        out = runner.run_query("my duke")
        assert "390" in out["bike_name"]
        assert "125" not in out["bike_name"]
        assert out["bike_alternatives"]  # ambiguity is surfaced, not hidden

    def test_k5_and_busa_still_resolve(self, runner):
        assert "K5" in runner.run_query("my k5")["bike_name"]
        assert "Hayabusa" in runner.run_query("my busa")["bike_name"]
