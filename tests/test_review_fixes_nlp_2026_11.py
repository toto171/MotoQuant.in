"""
Regression tests for the review of ``motoquant.nlp``:

  F1  budgets keep their magnitude (50k, 1.5 lakh, 50,000, 1,50,000, Rs., ...)
  F2  parts the user ruled out ("without exhaust", "no turbo") are not applied
  F3  temperature keeps its sign; Fahrenheit converts; absurd values are noted
  F4  bikes are found in natural phrasings, using the catalog's own names

plus a 50-query end-to-end corpus through ``NLSimRunner.run_query`` (the call
the ``nl`` CLI command makes) against a COPY of the shipped catalog.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import shutil

import pytest

import motoquant.nlp as nlp_module
from motoquant.database.connection import MotoQuantDB
from motoquant.models import TRACK_RUBBER, TRACK_VHT
from motoquant.nlp import NLQueryParser, NLSimRunner

REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("nlp_review") / "t.db"
    shutil.copyfile(REPO_DB, path)
    d = MotoQuantDB(str(path))
    d.connect()
    yield d
    d.close()


@pytest.fixture(scope="module")
def runner(db):
    return NLSimRunner(db)


@pytest.fixture(scope="module")
def parser():
    return NLQueryParser()


# ═════════════════════════════════ F1 budget ═════════════════════════════════
BUDGET_CASES = [
    ("budget 50k", 50_000),
    ("budget 50K", 50_000),
    ("under 50k", 50_000),
    ("a 50k budget", 50_000),
    ("budget of 50 thousand", 50_000),
    ("budget of ₹1.5 lakh", 150_000),
    ("budget ₹1.5 lakhs", 150_000),
    ("within 2 lakh", 200_000),
    ("2 lac budget", 200_000),
    ("around 3L", 300_000),
    ("budget 3 L", 300_000),
    ("1 crore budget", 10_000_000),
    ("budget 0.5 cr", 5_000_000),
    ("budget 50,000", 50_000),
    ("budget 1,50,000", 150_000),
    ("budget of 2,00,000 rupees", 200_000),
    ("budget 100000", 100_000),
    ("budget: 100000 INR", 100_000),
    ("spend 25000", 25_000),
    ("₹50000", 50_000),
    ("₹ 50,000", 50_000),
    ("Rs. 75,000", 75_000),
    ("Rs.75000", 75_000),
    ("rs 75000", 75_000),
    ("rs.2,00,000", 200_000),
    ("INR 40000", 40_000),
    ("40000 INR", 40_000),
    ("40000 rupees", 40_000),
    ("50000/-", 50_000),
    ("50k rupees", 50_000),
    ("under 50000", 50_000),
    ("at most 80k", 80_000),
    ("budget is around 1 lakh", 100_000),
    ("1.5 lakh", 150_000),
    ("Aprilia RS 457 under 5 lakh", 500_000),
    ("a 15 mph tailwind and 12 lakh", 1_200_000),
]
NOT_A_BUDGET = [
    "my 650 twin",
    "a 2019 model",
    "75 kg rider",
    "35C weather",
    "14k rpm limiter",
    "5 m/s headwind",
    "Aprilia RS 660",
    "RS 457",
    "1000cc",
    "at 2000 ft altitude",
    "under 2000 ft",
    "budget 35C",
    "budget 50% humidity",
    "300 hp",
    "rider weighs 80 kg",
    "10 m run-up",
]


class TestBudget:
    @pytest.mark.parametrize("text,rupees", BUDGET_CASES)
    def test_amount_keeps_its_magnitude(self, parser, text, rupees):
        assert parser._extract_budget(text.lower()) == rupees
        assert parser.parse(f"my busa {text}").budget_inr == rupees

    @pytest.mark.parametrize("text", NOT_A_BUDGET)
    def test_measurements_are_not_budgets(self, parser, text):
        assert parser.parse(f"my busa {text}").budget_inr is None

    @pytest.mark.parametrize(
        "text",
        [
            "no budget",
            "unlimited budget",
            "money no object",
            "budget is no object",
            "no limit",
            "without a budget",
        ],
    )
    def test_unlimited(self, parser, text):
        q = parser.parse(f"my busa with turbo, {text}")
        assert q.budget_unlimited and q.budget_inr is None
        assert q.optimization_goal != "best_budget"

    def test_explicit_amount_beats_unlimited_wording(self, parser):
        q = parser.parse("my busa, no limit, budget 2 lakh")
        assert q.budget_inr == 200_000 and not q.budget_unlimited

    def test_budget_reaches_part_selection(self, runner):
        """A real budget must neither be ignored nor read 1000x too small."""
        rich = runner.run_query("my Hayabusa with exhaust budget 2 lakh")
        assert rich["applied_part_details"]
        spent = sum(p["price_inr"] or 0 for p in rich["applied_part_details"])
        assert spent <= 200_000
        poor = runner.run_query("my Hayabusa with exhaust budget 100")
        assert poor["applied_parts"] == []
        assert [m["category"] for m in poor["parts_not_applied"]] == ["exhaust"]
        assert poor["parsed_query"]["budget_inr"] == 100

    def test_k_suffix_budget_buys_a_part(self, runner):
        out = runner.run_query("my Hayabusa with exhaust under 1.5 lakh")
        assert out["parsed_query"]["budget_inr"] == 150_000
        assert out["applied_part_details"]


# ═════════════════════════════════ F2 negation ═════════════════════════════════
NEGATION_CASES = [
    # (phrase, wanted, excluded)
    ("with exhaust", ["exhaust"], []),
    ("without exhaust", [], ["exhaust"]),
    ("no turbo", [], ["turbo"]),
    ("with a turbo", ["turbo"], []),
    ("with no turbo", [], ["turbo"]),
    ("stock exhaust", [], ["exhaust"]),
    ("keep the stock air filter", [], ["air_filter"]),
    ("don't add nitrous", [], ["nitrous"]),
    ("do not add nitrous", [], ["nitrous"]),
    ("add nitrous", ["nitrous"], []),
    ("except ECU", [], ["ecu"]),
    ("w/o exhaust", [], ["exhaust"]),
    ("with exhaust but no turbo", ["exhaust"], ["turbo"]),
    ("no turbo, with nitrous", ["nitrous"], ["turbo"]),
    ("no turbo and no nitrous", [], ["turbo", "nitrous"]),
    ("without turbo or nitrous", [], ["turbo", "nitrous"]),
    ("exhaust and ecu, no quickshifter", ["exhaust", "ecu"], ["quickshifter"]),
    ("excluding the clutch", [], ["clutch"]),
    ("minus the exhaust", [], ["exhaust"]),
    ("stock Hayabusa with exhaust", ["exhaust"], []),
    ("no budget, with exhaust", ["exhaust"], []),
]


class TestNegatedParts:
    @pytest.mark.parametrize("phrase,wanted,excluded", NEGATION_CASES)
    def test_scope(self, parser, phrase, wanted, excluded):
        q = parser.parse(f"my Hayabusa {phrase}")
        assert sorted(q.parts_mentioned) == sorted(wanted)
        assert sorted(q.parts_excluded) == sorted(excluded)

    def test_positive_and_negated_forms_of_one_sentence(self, runner):
        base = runner.run_query("my Hayabusa")
        pos = runner.run_query("my Hayabusa with turbo")
        neg = runner.run_query("my Hayabusa with no turbo")
        assert pos["applied_parts"] and pos["et_s"] < base["et_s"] - 0.1
        assert neg["applied_parts"] == []
        assert neg["parts_excluded"] == ["turbo"]
        assert neg["et_s"] == pytest.approx(base["et_s"])

    def test_negated_part_is_never_applied_next_to_wanted_ones(self, runner, db):
        out = runner.run_query("my Hayabusa with exhaust but no turbo, no nitrous")
        cats = {d["category"] for d in out["applied_part_details"]}
        assert cats == {"exhaust"}
        assert sorted(out["parts_excluded"]) == ["nitrous", "turbo"]

    def test_excluding_one_part_applies_the_rest(self, runner):
        out = runner.run_query("my Hayabusa with ecu except exhaust")
        cats = {d["category"] for d in out["applied_part_details"]}
        assert "exhaust" not in cats
        assert out["parts_excluded"] == ["exhaust"]


# ═════════════════════════════════ F3 temperature ═════════════════════════════════
TEMP_CASES = [
    ("35C", 35.0),
    ("35°C", 35.0),
    ("35 °C", 35.0),
    ("35 degrees celsius", 35.0),
    ("22.5C", 22.5),
    ("-5C", -5.0),
    ("-5°C", -5.0),
    ("minus 5 C", -5.0),
    ("minus 5 degrees celsius", -5.0),
    ("negative 3C", -3.0),
    ("5 below zero", -5.0),
    ("5C below zero", -5.0),
    ("95F", 35.0),
    ("95°F", 35.0),
    ("95 degrees fahrenheit", 35.0),
    ("32F", 0.0),
    ("-4F", -20.0),
    ("35-40C", 37.5),
    ("35 to 40 C", 37.5),
    ("Hayabusa - 35C", 35.0),
    ("temperature 30", 30.0),
    ("temp of -2", -2.0),
]


class TestTemperature:
    @pytest.mark.parametrize("text,celsius", TEMP_CASES)
    def test_value(self, parser, text, celsius):
        got = parser.parse(f"my busa at {text}").temperature_c
        assert got == pytest.approx(celsius, abs=0.01)

    @pytest.mark.parametrize("text", ["300C", "-120C", "500°F", "900 degrees celsius"])
    def test_absurd_values_are_noted_not_applied(self, parser, text):
        q = parser.parse(f"my busa at {text}")
        assert q.temperature_c is None
        assert q.notes and "not applied" in q.notes[0]

    @pytest.mark.parametrize("text", ["600 f exhaust", "1000cc", "400 cc", "R1 4C8"])
    def test_model_numbers_are_not_temperatures(self, parser, text):
        assert parser.parse(f"my busa {text}").temperature_c is None

    def test_sign_and_unit_reach_the_simulation(self, runner):
        base = runner.run_query("my Hayabusa")
        cold = runner.run_query("my Hayabusa at -5C")
        fahr = runner.run_query("my Hayabusa at 95F")
        hot = runner.run_query("my Hayabusa at 35C")
        assert cold["environment"]["ambient_temp_c"] == -5.0
        assert fahr["environment"]["ambient_temp_c"] == pytest.approx(35.0)
        assert cold["et_s"] < base["et_s"] < hot["et_s"]
        assert fahr["et_s"] == pytest.approx(hot["et_s"])

    def test_absurd_temperature_is_reported_in_the_result(self, runner, db):
        base = runner.run_query("my Hayabusa")
        out = runner.run_query("my Hayabusa at 300C")
        assert (
            out["environment"]["ambient_temp_c"]
            == base["environment"]["ambient_temp_c"]
        )
        assert out["parse_notes"]
        assert any("not applied" in s for s in out["suggestions"])


# ═════════════════════════════════ F4 bike extraction ═════════════════════════════════
BIKE_CASES = [
    ("my Hayabusa", "Hayabusa"),
    ("Hayabusa with turbo", "Hayabusa"),
    ("my busa", "Hayabusa"),
    ("what ET does my Hayabusa run with a turbo at Pomona", "Hayabusa"),
    ("a 2019 Duke 390", "Duke 390"),
    ("my 390 duke", "390 Duke"),
    ("Yamaha R15 V4", "R15 V4"),
    ("yamaha yzf-r15 v4 at 30c", "R15 V4"),
    ("R15", "R15"),
    ("gsxr 1000", "GSX-R 1000"),
    ("gsxr1000", "GSX-R 1000"),
    ("GSX-R1000 K5", "K5"),
    ("suzuki gsx-r 1000 2005", "K5"),
    ("K5", "K5"),
    ("zx10r", "ZX-10R"),
    ("zx-10r", "ZX-10R"),
    ("my Kawasaki ZX 10R", "ZX-10R"),
    ("ninja 400", "Ninja 400"),
    ("kawasaki ninja 400 for 28C", "Ninja 400"),
    ("RE classic 350", "Classic 350"),
    ("royal enfield classic 350", "Classic 350"),
    ("continental gt 650", "Continental GT 650"),
    ("my continental gt650", "Continental GT 650"),
    ("bullet", "Bullet"),
    ("pulsar ns200", "NS 200"),
    ("bajaj pulsar ns 200", "NS 200"),
    ("apache rr 310", "Apache RR 310"),
    ("tvs apache rr310", "Apache RR 310"),
    ("KTM RC390", "RC 390"),
    ("ktm rc 390", "RC 390"),
    ("my Apache 160 with exhaust", "160"),
    ("a 2012 Hayabusa", "Hayabusa (2008-2012)"),
    ("the Hayabusa 25th Anniversary", "25th Anniversary"),
    ("setup K5 for 28C, 50% humidity, budget 100000 INR", "K5"),
    (
        "optimize my Hayabusa for 35°C at Aamby Valley with a 50000 INR budget",
        "Hayabusa",
    ),
]


class TestBikeExtraction:
    @pytest.mark.parametrize("query,expect", BIKE_CASES)
    def test_resolves(self, runner, query, expect):
        row, phrase, _ = runner._match_bike(query)
        assert row is not None, query
        full = f"{row['manufacturer_name']} {row['model_name']} {row.get('model_code') or ''}"
        assert expect.lower() in full.lower(), (query, full)
        assert phrase

    @pytest.mark.parametrize(
        "query",
        [
            "what ET with turbo at Pomona in summer?",
            "simulate with exhaust under 50k at 30C",
            "budget 1 lakh, nitrous, 5 m/s headwind",
            "",
        ],
    )
    def test_no_bike_named_is_not_guessed(self, runner, query):
        out = runner.run_query(query)
        assert "error" in out

    def test_part_and_weather_words_never_name_a_bike(self, runner):
        words = {
            w
            for kws in NLQueryParser.PART_KEYWORDS.values()
            for k in kws
            for w in k.split()
        }
        words |= set(NLQueryParser.VENUE_ALIASES) | {"humidity", "headwind", "summer"}
        for w in sorted(words):
            row, _, _ = runner._match_bike(f"with {w} at 30c")
            assert row is None, (w, row and row["model_name"])

    def test_docstring_examples_all_name_a_bike(self, runner):
        sources = [
            inspect.getdoc(nlp_module),
            inspect.getdoc(NLQueryParser.parse),
            inspect.getdoc(NLSimRunner.run_query),
        ]
        examples = [
            m for src in sources for m in re.findall(r'"([^"\n]{12,})"', src or "")
        ]
        assert len(examples) >= 4
        for q in examples:
            row, _, _ = runner._match_bike(q)
            assert row is not None, f"docstring example names no bike: {q!r}"
            out = runner.run_query(q)
            assert "error" not in out, (q, out)

    def test_parser_alone_gives_a_bike_hint(self, parser):
        assert parser.parse("what ET does my Hayabusa run").bike_query == "hayabusa"
        assert parser.parse("my busa with 15 mph tailwind").bike_query == "busa"
        assert parser.parse("my 390 duke").bike_query == "390 duke"
        assert parser.parse("a 2019 Duke 390 at 30c").bike_query == "duke 390"


# ══════════════ model numbers beside budget words (either side) ══════════════
# (sentence, rupees or None, bike fragments that must all appear in the resolved
# bike's compact name)
NUMBER_NEXT_TO_BUDGET = [
    ("Duke 390 budget ₹1.5 lakh with exhaust and ecu, 95F", 150_000, ["duke", "390"]),
    ("RC 390 budget 80k", 80_000, ["rc", "390"]),
    ("R15 budget 40000", 40_000, ["r15"]),
    ("Ninja 400 under 2 lakh", 200_000, ["ninja", "400"]),
    ("2019 Duke 390 budget of 60,000", 60_000, ["duke", "390"]),
    ("GSX-R 1000 budget 3L", 300_000, ["gsx", "1000"]),
    ("Classic 350 budget 25k", 25_000, ["classic", "350"]),
    ("MT-15 with 50000 budget", 50_000, ["mt", "15"]),
    ("budget 75k Duke 250", 75_000, ["duke", "250"]),
    ("Hayabusa 1340 budget", None, ["hayabusa"]),
    ("ZX-10R budget Rs. 1,50,000/-", 150_000, ["zx", "10r"]),
    ("Continental GT 650 budget: 90k", 90_000, ["continental", "650"]),
    ("budget ₹2 lakh Continental GT 650", 200_000, ["continental", "650"]),
    ("Pulsar NS200 budget 1.2 lakh", 120_000, ["ns", "200"]),
    ("Apache RR 310 budget 1 lakh", 100_000, ["rr", "310"]),
    ("Hayabusa 1300 budget 2 crore", 20_000_000, ["hayabusa"]),
    ("2019 Duke 390 under 50k", 50_000, ["duke", "390"]),
    ("Duke 390 2019 budget", None, ["duke", "390"]),
    ("R15 V4 ₹40000 budget", 40_000, ["r15", "v4"]),
    ("my busa with a 50000 budget", 50_000, ["hayabusa"]),
    ("KTM RC390 budget 1,00,000", 100_000, ["rc", "390"]),
    ("Ninja 400 budget 400", 400, ["ninja", "400"]),
]


class TestModelNumberNextToBudget:
    @pytest.mark.parametrize("text,rupees,frag", NUMBER_NEXT_TO_BUDGET)
    def test_budget_and_bike(self, runner, parser, text, rupees, frag):
        assert parser.parse(text).budget_inr == rupees, text
        row, _, _ = runner._match_bike(text)
        assert row is not None, text
        compact = re.sub(
            r"[^a-z0-9]",
            "",
            f"{row['model_name']} {row.get('model_code') or ''}".lower(),
        )
        assert all(f in compact for f in frag), (text, row["model_name"])

    @pytest.mark.parametrize(
        "text,hint",
        [
            ("R15 V4 with 5 m/s headwind, no budget", "r15 v4"),
            ("MT-15 at 30c", "mt-15"),
            ("ZX-10R with exhaust", "zx-10r"),
            ("RC 390 budget 80k", "rc 390"),
            ("Pulsar NS200 at 35C", "pulsar ns200"),
            ("Apache RR 310 with ecu", "apache rr 310"),
            ("GSX-R 1000 budget 3L", "gsx-r 1000"),
        ],
    )
    def test_parser_only_bike_hint(self, parser, text, hint):
        assert parser.parse(text).bike_query == hint

    def test_r15_headwind_no_budget_end_to_end(self, runner):
        base = runner.run_query("simulate my R15 V4")
        out = runner.run_query("R15 V4 with 5 m/s headwind, no budget")
        assert "error" not in out
        assert "R15 V4" in out["bike_name"] and "Yamaha" in out["bike_name"]
        assert out["environment"]["altitude_m"] == base["environment"]["altitude_m"]
        assert out["environment"]["wind_speed_ms"] == pytest.approx(5.0)
        assert out["environment"]["wind_direction_deg"] == 0.0
        assert out["parsed_query"]["budget_unlimited"] is True
        assert out["parsed_query"]["budget_inr"] is None
        assert out["et_s"] > base["et_s"]


# ══════════════ generated adversarial sentences (ground truth known) ══════════════
# Sentences are composed from typed fragments (bike, year, money, parts,
# weather, wind, altitude, gearing, track) in random clause order with random
# joiners, so a year, a model number or a sprocket size lands next to money in
# every order. Ground truth comes from the fragments, not from the parser.
SWEEP_BIKES = [  # (text, phrase the parser hint must contain, fragments of the bike)
    ("ninja 400", "ninja 400", ["ninja", "400"]),
    ("zx-10r", "zx-10r", ["zx", "10r"]),
    ("duke 390", "duke 390", ["duke", "390"]),
    ("gsxr 1000 k5", "gsxr 1000 k5", ["k5"]),
    ("classic 350", "classic 350", ["classic", "350"]),
    ("rc 390", "rc 390", ["rc", "390"]),
    ("mt-15", "mt-15", ["mt", "15"]),
    ("ns200", "ns200", ["ns", "200"]),
    ("pulsar ns200", "pulsar ns200", ["ns", "200"]),
    ("r15 v4", "r15 v4", ["r15", "v4"]),
    ("rr 310", "rr 310", ["rr", "310"]),
    ("apache rr 310", "apache rr 310", ["rr", "310"]),
    ("hayabusa", "hayabusa", ["hayabusa"]),
    ("hayabusa 1340", "hayabusa 1340", ["hayabusa"]),
    ("my busa", "busa", ["hayabusa"]),
    ("my ninja 400", "ninja 400", ["ninja", "400"]),
    ("yamaha r15 v4", "yamaha r15 v4", ["r15", "v4"]),
    ("kawasaki ninja 400", "kawasaki ninja 400", ["ninja", "400"]),
    ("royal enfield classic 350", "classic 350", ["classic", "350"]),
    ("continental gt 650", "continental gt 650", ["continental", "650"]),
    ("gsx-r 1000", "gsx-r 1000", ["gsx", "1000"]),
    ("zx10r", "zx10r", ["zx", "10r"]),
    ("ktm rc390", "rc390", ["rc", "390"]),
    ("duke 250", "duke 250", ["duke", "250"]),
    ("bullet", "bullet", ["bullet"]),
    ("s1000rr", "s1000rr", ["s1000rr"]),
    ("mt-15 v2", "mt-15 v2", ["mt", "15", "v2"]),
    ("gsxr 1000", "gsxr 1000", ["gsx", "1000"]),
]
SWEEP_YEARS = [2005, 2012, 2019, 2021, 2024]
SWEEP_MONEY = [  # (clause, rupees, unlimited)
    ("under 80k", 80_000, False),
    ("₹1.5 lakh", 150_000, False),
    ("Rs. 1,50,000/-", 150_000, False),
    ("budget 60000", 60_000, False),
    ("2 lakh budget", 200_000, False),
    ("for 40k", 40_000, False),
    ("within 75,000 rupees", 75_000, False),
    ("budget of ₹90,000", 90_000, False),
    ("budget Rs 1.2 lakh", 120_000, False),
    ("3L budget", 300_000, False),
    ("up to 2.5 lakh", 250_000, False),
    ("INR 55000", 55_000, False),
    ("40000 INR", 40_000, False),
    ("a budget of 50 thousand", 50_000, False),
    ("budget: 45k", 45_000, False),
    ("spend 25000", 25_000, False),
    ("around ₹65,000", 65_000, False),
    ("max 1 crore", 10_000_000, False),
    ("with a 50000 budget", 50_000, False),
    ("no budget", None, True),
    ("unlimited budget", None, True),
    ("", None, False),
]
SWEEP_PARTS = [  # (clause, wanted, excluded)
    ("with exhaust and ecu", ["exhaust", "ecu"], []),
    ("without turbo", [], ["turbo"]),
    ("no exhaust", [], ["exhaust"]),
    ("with exhaust but no nitrous", ["exhaust"], ["nitrous"]),
    ("stock air filter", [], ["air_filter"]),
    ("with nitrous, no turbo", ["nitrous"], ["turbo"]),
    ("plus quickshifter", ["quickshifter"], []),
    ("without nitrous", [], ["nitrous"]),
    ("", [], []),
]
# (clause, field values). Fields: temp, humidity, wind (m/s), wind_dir, altitude,
# wanted (extra parts the clause names), prep (track prep)
SWEEP_EXTRAS = [
    ("at 38C", {"temp": 38.0}),
    ("at -5C", {"temp": -5.0}),
    ("at 104F", {"temp": 40.0}),
    ("at 95 degrees fahrenheit", {"temp": 35.0}),
    ("temperature 30", {"temp": 30.0}),
    ("at minus 3 C", {"temp": -3.0}),
    ("at 45°C", {"temp": 45.0}),
    ("50% humidity", {"humidity": 50.0}),
    ("with 5 m/s headwind", {"wind": 5.0, "wind_dir": 0.0}),
    ("with an 18 km/h tailwind", {"wind": 5.0, "wind_dir": 180.0}),
    ("with 10 mph headwind", {"wind": 4.4704, "wind_dir": 0.0}),
    ("with a 20 kmph headwind", {"wind": 5.5556, "wind_dir": 0.0}),
    ("at altitude 1500 m", {"altitude": 1500.0}),
    ("at 3000 ft elevation", {"altitude": 914.4}),
    ("1200 m altitude", {"altitude": 1200.0}),
    ("with a 14 tooth sprocket", {"wanted": ["chain"]}),
    ("with 15/45 gearing", {}),
    ("with +2 teeth rear", {}),
    ("with front sprocket 15", {"wanted": ["chain"]}),
    ("with a 16T front", {}),
    ("wet track", {}),
    ("with rubber buildup", {"prep": "rubber"}),
    ("with vht", {"prep": "vht"}),
    ("on pj1", {"prep": "pj1"}),
]
_PREP_WORDS = {
    "at", "with", "on", "under", "for", "within", "up", "around", "budget",
    "spend", "max", "without", "stock", "plus", "no", "unlimited", "a", "an",
}  # fmt: skip
_JOINERS = [", ", " ", " and ", " at ", " with "]
_SWEEP_FIELDS = ("temp", "humidity", "wind", "wind_dir", "altitude", "prep")


def _extra_group(clause: str) -> str:
    if "humidity" in clause:
        return "humidity"
    for key, name in (("wind", "wind"), ("altitude", "alt"), ("elevation", "alt")):
        if key in clause:
            return name
    if any(w in clause for w in ("track", "rubber", "vht", "pj1")):
        return "track"
    if any(w in clause for w in ("sprocket", "gearing", "teeth", "16T")):
        return "gear"
    return "temp"


def sweep_sentences(n=600, seed=20261110):
    import random

    rng = random.Random(seed)
    out = []
    while len(out) < n:
        text, phrase, frags = rng.choice(SWEEP_BIKES)
        year = rng.choice(SWEEP_YEARS) if rng.random() < 0.5 else None
        if year:
            bike_clause = f"{year} {text}" if rng.random() < 0.5 else f"{text} {year}"
        else:
            bike_clause = text
        money = rng.choice(SWEEP_MONEY)
        parts = rng.choice(SWEEP_PARTS)
        groups: dict[str, tuple[str, dict]] = {}
        for clause, vals in rng.sample(SWEEP_EXTRAS, rng.randint(1, 4)):
            groups.setdefault(_extra_group(clause), (clause, vals))
        clauses = [bike_clause, money[0], parts[0]] + [c for c, _ in groups.values()]
        clauses = [c for c in clauses if c]
        rng.shuffle(clauses)
        sentence = clauses[0]
        for c in clauses[1:]:
            joiner = rng.choice(_JOINERS)
            if c.split()[0] in _PREP_WORDS and joiner in (" at ", " with "):
                joiner = ", "
            sentence += joiner + c
        truth = dict.fromkeys(_SWEEP_FIELDS)
        wanted = list(parts[1])
        for _, vals in groups.values():
            for k, v in vals.items():
                if k == "wanted":
                    wanted += v
                else:
                    truth[k] = v
        out.append(
            {
                "q": sentence,
                "phrase": phrase,
                "bike": frags,
                "budget": money[1],
                "unlimited": money[2],
                "wanted": sorted(wanted),
                "excluded": sorted(parts[2]),
                **truth,
            }
        )
    return out


def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def check_sentence(parser, runner, case):
    """Mismatch labels for one sentence (empty = every value right)."""
    bad = []
    q = parser.parse(case["q"])
    if q.budget_inr != case["budget"]:
        bad.append(f"budget {q.budget_inr} != {case['budget']}")
    if q.budget_unlimited != case["unlimited"]:
        bad.append("unlimited")
    if sorted(q.parts_mentioned) != sorted(case["wanted"]):
        bad.append(f"wanted {q.parts_mentioned}")
    if sorted(q.parts_excluded) != sorted(case["excluded"]):
        bad.append(f"excluded {q.parts_excluded}")
    for got, want, name in (
        (q.temperature_c, case["temp"], "temp"),
        (q.humidity_pct, case["humidity"], "humidity"),
        (q.headwind_ms, case["wind"], "wind"),
        (q.wind_direction_deg, case["wind_dir"], "wind_dir"),
        (q.altitude_m, case["altitude"], "altitude"),
    ):
        if (got is None) != (want is None) or (
            want is not None and abs(got - want) > 0.01
        ):
            bad.append(f"{name} {got} != {want}")
    if q.track_prep_type != case["prep"]:
        bad.append(f"prep {q.track_prep_type}")
    if _compact(case["phrase"]) not in _compact(q.bike_query):
        bad.append(f"hint {q.bike_query!r}")
    row, _, _ = runner._match_bike(case["q"])
    if row is None:
        bad.append("no bike")
    else:
        name = _compact(f"{row['model_name']} {row.get('model_code') or ''}")
        if not all(f in name for f in case["bike"]):
            bad.append(f"bike {row['model_name']}")
    return bad


# Sampled from the generator with the seed above: every sentence shape that the
# earlier ranking-by-neighbouring-words code got wrong (budget, bike hint, wind).
FROZEN_SENTENCES = [
    {
        "q": "at 3000 ft elevation and a budget of 50 thousand no exhaust with zx10r",
        "phrase": "zx10r",
        "bike": ["zx", "10r"],
        "budget": 50000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["exhaust"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 914.4,
        "prep": None,
    },
    {
        "q": "zx-10r, a budget of 50 thousand no exhaust and with 15/45 gearing",
        "phrase": "zx-10r",
        "bike": ["zx", "10r"],
        "budget": 50000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["exhaust"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "at 45°C, with vht, up to 2.5 lakh no exhaust with ktm rc390 2021",
        "phrase": "rc390",
        "bike": ["rc", "390"],
        "budget": 250000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["exhaust"],
        "temp": 45.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "vht",
    },
    {
        "q": "unlimited budget at 2005 duke 390, with vht, plus quickshifter, with 5 m/s headwind, at 38C 1200 m altitude",
        "phrase": "duke 390",
        "bike": ["duke", "390"],
        "budget": None,
        "unlimited": True,
        "wanted": ["quickshifter"],
        "excluded": [],
        "temp": 38.0,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 0.0,
        "altitude": 1200.0,
        "prep": "vht",
    },
    {
        "q": "classic 350 2024 with front sprocket 15, a budget of 50 thousand no exhaust",
        "phrase": "classic 350",
        "bike": ["classic", "350"],
        "budget": 50000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": ["exhaust"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "no exhaust, with vht, ns200, with a 14 tooth sprocket, around ₹65,000, at -5C",
        "phrase": "ns200",
        "bike": ["ns", "200"],
        "budget": 65000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": ["exhaust"],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "vht",
    },
    {
        "q": "at 3000 ft elevation and ₹1.5 lakh stock air filter and at minus 3 C at apache rr 310 2019",
        "phrase": "apache rr 310",
        "bike": ["rr", "310"],
        "budget": 150000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["air_filter"],
        "temp": -3.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 914.4,
        "prep": None,
    },
    {
        "q": "without nitrous, with a 14 tooth sprocket and with an 18 km/h tailwind, gsx-r 1000 2019, 40000 INR",
        "phrase": "gsx-r 1000",
        "bike": ["gsx", "1000"],
        "budget": 40000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": ["nitrous"],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "2019 gsxr 1000 k5 and at minus 3 C no exhaust, on pj1, at altitude 1500 m",
        "phrase": "gsxr 1000 k5",
        "bike": ["k5"],
        "budget": None,
        "unlimited": False,
        "wanted": [],
        "excluded": ["exhaust"],
        "temp": -3.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1500.0,
        "prep": "pj1",
    },
    {
        "q": "with a 16T front, stock air filter and my busa at wet track budget: 45k",
        "phrase": "busa",
        "bike": ["hayabusa"],
        "budget": 45000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["air_filter"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "with +2 teeth rear, budget 60000 without nitrous, at 95 degrees fahrenheit and continental gt 650 and at 3000 ft elevation",
        "phrase": "continental gt 650",
        "bike": ["continental", "650"],
        "budget": 60000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["nitrous"],
        "temp": 35.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 914.4,
        "prep": None,
    },
    {
        "q": "up to 2.5 lakh, with a 20 kmph headwind zx-10r with exhaust and ecu and at 104F",
        "phrase": "zx-10r",
        "bike": ["zx", "10r"],
        "budget": 250000,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": 40.0,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "Rs. 1,50,000/- with 50% humidity with a 16T front, plus quickshifter with zx10r 2012 and at 45°C",
        "phrase": "zx10r",
        "bike": ["zx", "10r"],
        "budget": 150000,
        "unlimited": False,
        "wanted": ["quickshifter"],
        "excluded": [],
        "temp": 45.0,
        "humidity": 50.0,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "1200 m altitude, with an 18 km/h tailwind and with exhaust and ecu, under 80k gsx-r 1000",
        "phrase": "gsx-r 1000",
        "bike": ["gsx", "1000"],
        "budget": 80000,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": 1200.0,
        "prep": None,
    },
    {
        "q": "without turbo, with rubber buildup, 50% humidity and budget of ₹90,000, duke 250, at 95 degrees fahrenheit",
        "phrase": "duke 250",
        "bike": ["duke", "250"],
        "budget": 90000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["turbo"],
        "temp": 35.0,
        "humidity": 50.0,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "rubber",
    },
    {
        "q": "with an 18 km/h tailwind at 2019 duke 390, with exhaust and ecu at 1200 m altitude",
        "phrase": "duke 390",
        "bike": ["duke", "390"],
        "budget": None,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": 1200.0,
        "prep": None,
    },
    {
        "q": "at 3000 ft elevation, with a 20 kmph headwind, max 1 crore and 2012 my ninja 400 with nitrous, no turbo",
        "phrase": "ninja 400",
        "bike": ["ninja", "400"],
        "budget": 10000000,
        "unlimited": False,
        "wanted": ["nitrous"],
        "excluded": ["turbo"],
        "temp": None,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": 914.4,
        "prep": None,
    },
    {
        "q": "without nitrous and 2 lakh budget wet track at kawasaki ninja 400 2005",
        "phrase": "kawasaki ninja 400",
        "bike": ["ninja", "400"],
        "budget": 200000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["nitrous"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "2019 ninja 400, max 1 crore, with a 14 tooth sprocket, with a 20 kmph headwind plus quickshifter",
        "phrase": "ninja 400",
        "bike": ["ninja", "400"],
        "budget": 10000000,
        "unlimited": False,
        "wanted": ["chain", "quickshifter"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "at 3000 ft elevation with +2 teeth rear, spend 25000 and 2021 r15 v4 and with exhaust and ecu, with a 20 kmph headwind with vht",
        "phrase": "r15 v4",
        "bike": ["r15", "v4"],
        "budget": 25000,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": 914.4,
        "prep": "vht",
    },
    {
        "q": "at -5C, with a 16T front, with rubber buildup, at altitude 1500 m hayabusa, with exhaust and ecu with 40000 INR",
        "phrase": "hayabusa",
        "bike": ["hayabusa"],
        "budget": 40000,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1500.0,
        "prep": "rubber",
    },
    {
        "q": "with a 20 kmph headwind budget Rs 1.2 lakh with r15 v4 and temperature 30, with exhaust but no nitrous",
        "phrase": "r15 v4",
        "bike": ["r15", "v4"],
        "budget": 120000,
        "unlimited": False,
        "wanted": ["exhaust"],
        "excluded": ["nitrous"],
        "temp": 30.0,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "with a 20 kmph headwind, 2024 rr 310, budget 60000, stock air filter",
        "phrase": "rr 310",
        "bike": ["rr", "310"],
        "budget": 60000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["air_filter"],
        "temp": None,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "with exhaust and ecu, around ₹65,000 with ninja 400 and wet track and at -5C",
        "phrase": "ninja 400",
        "bike": ["ninja", "400"],
        "budget": 65000,
        "unlimited": False,
        "wanted": ["ecu", "exhaust"],
        "excluded": [],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "at -5C, with a 14 tooth sprocket 40000 INR 2012 gsx-r 1000",
        "phrase": "gsx-r 1000",
        "bike": ["gsx", "1000"],
        "budget": 40000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": [],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "2 lakh budget with rubber buildup, hayabusa 1340 2005 and with an 18 km/h tailwind, without nitrous",
        "phrase": "hayabusa 1340",
        "bike": ["hayabusa"],
        "budget": 200000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["nitrous"],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": None,
        "prep": "rubber",
    },
    {
        "q": "with vht, at altitude 1500 m with nitrous, no turbo gsxr 1000 k5 2005, budget Rs 1.2 lakh",
        "phrase": "gsxr 1000 k5",
        "bike": ["k5"],
        "budget": 120000,
        "unlimited": False,
        "wanted": ["nitrous"],
        "excluded": ["turbo"],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1500.0,
        "prep": "vht",
    },
    {
        "q": "2021 gsxr 1000 k5 INR 55000 at minus 3 C with 1200 m altitude, with a 14 tooth sprocket, with exhaust and ecu",
        "phrase": "gsxr 1000 k5",
        "bike": ["k5"],
        "budget": 55000,
        "unlimited": False,
        "wanted": ["chain", "ecu", "exhaust"],
        "excluded": [],
        "temp": -3.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1200.0,
        "prep": None,
    },
    {
        "q": "at 38C, for 40k and without turbo, with an 18 km/h tailwind with continental gt 650 2021",
        "phrase": "continental gt 650",
        "bike": ["continental", "650"],
        "budget": 40000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["turbo"],
        "temp": 38.0,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "1200 m altitude, rc 390 2021, without turbo budget 60000 and with a 14 tooth sprocket, at minus 3 C",
        "phrase": "rc 390",
        "bike": ["rc", "390"],
        "budget": 60000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": ["turbo"],
        "temp": -3.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1200.0,
        "prep": None,
    },
    {
        "q": "plus quickshifter, with front sprocket 15 and at altitude 1500 m with an 18 km/h tailwind, budget Rs 1.2 lakh with pulsar ns200",
        "phrase": "pulsar ns200",
        "bike": ["ns", "200"],
        "budget": 120000,
        "unlimited": False,
        "wanted": ["chain", "quickshifter"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": 1500.0,
        "prep": None,
    },
    {
        "q": "with a 14 tooth sprocket and with nitrous, no turbo and duke 250, spend 25000, at 38C",
        "phrase": "duke 250",
        "bike": ["duke", "250"],
        "budget": 25000,
        "unlimited": False,
        "wanted": ["chain", "nitrous"],
        "excluded": ["turbo"],
        "temp": 38.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "continental gt 650, with nitrous, no turbo, at minus 3 C, budget 60000, with rubber buildup",
        "phrase": "continental gt 650",
        "bike": ["continental", "650"],
        "budget": 60000,
        "unlimited": False,
        "wanted": ["nitrous"],
        "excluded": ["turbo"],
        "temp": -3.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "rubber",
    },
    {
        "q": "1200 m altitude and with an 18 km/h tailwind, with a 50000 budget with r15 v4, stock air filter",
        "phrase": "r15 v4",
        "bike": ["r15", "v4"],
        "budget": 50000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["air_filter"],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": 1200.0,
        "prep": None,
    },
    {
        "q": "2019 gsxr 1000 k5 and with an 18 km/h tailwind and with front sprocket 15 and with exhaust and ecu, with vht",
        "phrase": "gsxr 1000 k5",
        "bike": ["k5"],
        "budget": None,
        "unlimited": False,
        "wanted": ["chain", "ecu", "exhaust"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": None,
        "prep": "vht",
    },
    {
        "q": "at 95 degrees fahrenheit and INR 55000, at 3000 ft elevation with pulsar ns200, with exhaust but no nitrous with an 18 km/h tailwind",
        "phrase": "pulsar ns200",
        "bike": ["ns", "200"],
        "budget": 55000,
        "unlimited": False,
        "wanted": ["exhaust"],
        "excluded": ["nitrous"],
        "temp": 35.0,
        "humidity": None,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": 914.4,
        "prep": None,
    },
    {
        "q": "for 40k, with rubber buildup, at 104F at ktm rc390 with an 18 km/h tailwind 50% humidity",
        "phrase": "rc390",
        "bike": ["rc", "390"],
        "budget": 40000,
        "unlimited": False,
        "wanted": [],
        "excluded": [],
        "temp": 40.0,
        "humidity": 50.0,
        "wind": 5.0,
        "wind_dir": 180.0,
        "altitude": None,
        "prep": "rubber",
    },
    {
        "q": "50% humidity on pj1 with 3L budget, stock air filter, 2005 gsx-r 1000",
        "phrase": "gsx-r 1000",
        "bike": ["gsx", "1000"],
        "budget": 300000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["air_filter"],
        "temp": None,
        "humidity": 50.0,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "pj1",
    },
    {
        "q": "50% humidity, at 38C, without nitrous, mt-15, under 80k, with a 20 kmph headwind",
        "phrase": "mt-15",
        "bike": ["mt", "15"],
        "budget": 80000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["nitrous"],
        "temp": 38.0,
        "humidity": 50.0,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
    {
        "q": "budget: 45k with +2 teeth rear, plus quickshifter, on pj1 at gsxr 1000 k5",
        "phrase": "gsxr 1000 k5",
        "bike": ["k5"],
        "budget": 45000,
        "unlimited": False,
        "wanted": ["quickshifter"],
        "excluded": [],
        "temp": None,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": None,
        "prep": "pj1",
    },
    {
        "q": "on pj1 at bullet, at -5C and with a 50000 budget and with exhaust but no nitrous, with a 14 tooth sprocket, at 3000 ft elevation",
        "phrase": "bullet",
        "bike": ["bullet"],
        "budget": 50000,
        "unlimited": False,
        "wanted": ["chain", "exhaust"],
        "excluded": ["nitrous"],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 914.4,
        "prep": "pj1",
    },
    {
        "q": "around ₹65,000, with vht and with 10 mph headwind, at altitude 1500 m, classic 350, no exhaust",
        "phrase": "classic 350",
        "bike": ["classic", "350"],
        "budget": 65000,
        "unlimited": False,
        "wanted": [],
        "excluded": ["exhaust"],
        "temp": None,
        "humidity": None,
        "wind": 4.4704,
        "wind_dir": 0.0,
        "altitude": 1500.0,
        "prep": "vht",
    },
    {
        "q": "with a 14 tooth sprocket and no exhaust, up to 2.5 lakh with continental gt 650 at altitude 1500 m, at -5C",
        "phrase": "continental gt 650",
        "bike": ["continental", "650"],
        "budget": 250000,
        "unlimited": False,
        "wanted": ["chain"],
        "excluded": ["exhaust"],
        "temp": -5.0,
        "humidity": None,
        "wind": None,
        "wind_dir": None,
        "altitude": 1500.0,
        "prep": None,
    },
    {
        "q": "r15 v4, under 80k and at minus 3 C, with a 20 kmph headwind, with exhaust but no nitrous",
        "phrase": "r15 v4",
        "bike": ["r15", "v4"],
        "budget": 80000,
        "unlimited": False,
        "wanted": ["exhaust"],
        "excluded": ["nitrous"],
        "temp": -3.0,
        "humidity": None,
        "wind": 5.5556,
        "wind_dir": 0.0,
        "altitude": None,
        "prep": None,
    },
]


@pytest.mark.parametrize(
    "case", FROZEN_SENTENCES, ids=[c["q"][:70] for c in FROZEN_SENTENCES]
)
def test_frozen_generated_sentences(runner, parser, case):
    assert check_sentence(parser, runner, case) == []


REPORTED_FAILURES = [
    # (sentence, budget, bike hint, resolved-bike fragments)
    (
        "my ninja 400 under 80k no exhaust at aamby valley 38C",
        80_000,
        "ninja 400",
        ["ninja", "400"],
    ),
    ("ZX-10R 2021 Rs. 1,50,000/- without nitrous", 150_000, "zx-10r", ["zx", "10r"]),
    ("what does a 14 tooth sprocket do on my rc 390", None, "rc 390", ["rc", "390"]),
    ("gsxr 1000 k5 at 104F with wet track", None, "gsxr 1000 k5", ["k5"]),
]


class TestTypedNumbers:
    @pytest.mark.parametrize("text,rupees,hint,frags", REPORTED_FAILURES)
    def test_reported_sentences(self, runner, parser, text, rupees, hint, frags):
        q = parser.parse(text)
        assert q.budget_inr == rupees
        assert _compact(hint) in _compact(q.bike_query)
        row, _, _ = runner._match_bike(text)
        assert all(
            f in _compact(f"{row['model_name']} {row.get('model_code') or ''}")
            for f in frags
        )

    @pytest.mark.parametrize(
        "text,kind",
        [
            ("2021", "year"),
            ("38C", "temp"),
            ("104F", "temp"),
            ("5 m/s", "speed"),
            ("18 km/h", "speed"),
            ("20 kmph", "speed"),
            ("50%", "percent"),
            ("14k rpm", "rpm"),
            ("75 kg", "mass"),
            ("1000cc", "disp"),
            ("32 psi", "pressure"),
            ("120 hp", "power"),
            ("1500 m", "length"),
            ("3000 ft", "length"),
            ("14 tooth", "teeth"),
            ("+2 teeth", "teeth"),
            ("16T", "teeth"),
            ("15/45", "teeth"),
            ("front sprocket 15", "teeth"),
            ("10r", "glued"),
            ("80k", "money"),
            ("₹500", "money"),
            ("Rs. 1,50,000/-", "money"),
            ("1.5 lakh", "money"),
            ("390", "bare"),
        ],
    )
    def test_each_number_gets_one_type(self, text, kind):
        toks = NLQueryParser._number_tokens(text.lower())
        assert toks and toks[-1]["type"] == kind, (text, toks)

    @pytest.mark.parametrize(
        "text,rupees",
        [
            ("40000 INR 1200 m altitude", 40_000),
            ("75,000 rupees 50% humidity", 75_000),
            ("duke 250 INR 55000", 55_000),
            ("gsx-r 1000 \u20b91.5 lakh", 150_000),
            ("with +2 teeth rear 2 lakh budget", 200_000),
            ("zx-10r with 15/45 gearing 3L budget", 300_000),
            ("apache rr 310 Rs. 1,50,000/-", 150_000),
            ("40000 INR 2012 gsx-r 1000", 40_000),
            ("2021 INR 55000 duke 390", 55_000),
        ],
    )
    def test_currency_marker_belongs_to_the_right_number(self, parser, text, rupees):
        assert parser.parse(text).budget_inr == rupees

    @pytest.mark.parametrize(
        "text",
        [
            "Rs. 50,000 and Rs. 80,000",
            "40k or 60k",
            "Duke 390 50000 budget",
            "Duke 390, \u20b980000 or \u20b955000",
        ],
    )
    def test_unclear_budget_is_refused_with_a_note(self, parser, text):
        q = parser.parse(text)
        assert q.budget_inr is None
        assert any("couldn't tell which number is your budget" in n for n in q.notes)

    def test_keyword_picks_between_two_amounts(self, parser):
        assert (
            parser.parse("Duke 390 budget 80k, parts worth ₹2 lakh").budget_inr
            == 80_000
        )
        assert parser.parse("Duke 390 ₹2 lakh, under 50k").budget_inr == 50_000

    def test_the_unclear_note_reaches_run_query(self, runner):
        out = runner.run_query("Duke 390 with Rs. 50,000 and Rs. 80,000")
        assert out["parsed_query"]["budget_inr"] is None
        assert any("which number is your budget" in s for s in out["suggestions"])

    @pytest.mark.parametrize(
        "text,hint",
        [
            ("what does a 14 tooth sprocket do on my rc 390", "rc 390"),
            ("hayabusa with 15/45 gearing, 5 m/s headwind", "hayabusa"),
            ("2019 ninja 400 under 80k", "ninja 400"),
            ("ninja 400 2019 under 80k", "ninja 400"),
            ("my ninja 400 at 38C", "ninja 400"),
            ("zx-10r at 104F", "zx-10r"),
        ],
    )
    def test_hint_never_takes_a_typed_number(self, parser, text, hint):
        assert parser.parse(text).bike_query == hint


class TestGeneratedSentences:
    def test_generated_sentences_are_all_read_correctly(self, runner, parser):
        failures = {}
        for c in sweep_sentences(160):
            bad = check_sentence(parser, runner, c)
            if bad:
                failures[c["q"]] = bad
        assert not failures, json.dumps(failures, ensure_ascii=False, indent=1)

    def test_run_query_on_generated_sentences(self, runner):
        """The same sentences through the CLI's entry point (sampled for speed)."""
        for c in sweep_sentences(160)[::32]:
            out = runner.run_query(c["q"])
            assert "error" not in out, c["q"]
            assert all(f in _compact(out["bike_name"]) for f in c["bike"]), c["q"]
            applied = {d["category"] for d in out["applied_part_details"]}
            assert not applied & set(c["excluded"]), c["q"]
            assert sorted(out["parts_excluded"]) == sorted(c["excluded"]), c["q"]
            env = out["environment"]
            for key, field in (
                ("ambient_temp_c", "temp"),
                ("humidity_pct", "humidity"),
                ("wind_speed_ms", "wind"),
                ("altitude_m", "altitude"),
            ):
                if c[field] is not None:
                    assert env[key] == pytest.approx(c[field], abs=0.01), (c["q"], key)
            assert out["parsed_query"]["budget_inr"] == c["budget"], c["q"]
            assert out["parsed_query"]["budget_unlimited"] == c["unlimited"], c["q"]
            if c["budget"] is not None:
                spent = sum(d["price_inr"] or 0 for d in out["applied_part_details"])
                assert spent <= c["budget"], c["q"]


# ═════════════════════════════════ 50-query end-to-end corpus ═════════════════════════════════
BASE = {
    "hayabusa": "Hayabusa",
    "gsxr": "GSX-R 1000 K5",
    "zx10r": "ZX-10R",
    "r15": "R15 V4",
    "duke": "Duke 390",
    "ninja": "Ninja 400",
    "classic": "Classic 350",
    "gt650": "Continental GT 650",
    "ns200": "Pulsar NS200",
    "rr310": "Apache RR 310",
    "rc390": "RC 390",
    "bullet": "Bullet",
}


def C(
    q,
    bike,
    name,
    *,
    env=None,
    parts=(),
    excluded=(),
    move=None,
    venue=None,
    budget=None,
    other=False,
):
    return {
        "q": q,
        "bike": bike,
        "name": name,
        "env": env or {},
        "parts": list(parts),
        "excluded": list(excluded),
        "move": move,
        "venue": venue,
        "budget": budget,
        "other": other,
    }


CORPUS = [
    # environment, one factor at a time
    C(
        "my Hayabusa at 35C",
        "hayabusa",
        "Hayabusa",
        env={"ambient_temp_c": 35.0},
        move="slower",
    ),
    C(
        "my Hayabusa at -5C",
        "hayabusa",
        "Hayabusa",
        env={"ambient_temp_c": -5.0},
        move="faster",
    ),
    C(
        "a 2019 Duke 390 at 95F",
        "duke",
        "390 Duke",
        env={"ambient_temp_c": 35.0},
        move="slower",
    ),
    C(
        "R15 V4 at 10 degrees celsius",
        "r15",
        "R15 V4",
        env={"ambient_temp_c": 10.0},
        move="faster",
    ),
    C(
        "my Hayabusa with 80% humidity",
        "hayabusa",
        "Hayabusa",
        env={"humidity_pct": 80.0},
        move="slower",
    ),
    C(
        "gsxr 1000 K5 with 10 m/s headwind",
        "gsxr",
        "K5",
        env={"wind_speed_ms": 10.0, "wind_direction_deg": 0.0},
        move="slower",
    ),
    C(
        "GSX-R1000 K5 with 18 km/h tailwind",
        "gsxr",
        "K5",
        env={"wind_speed_ms": 5.0, "wind_direction_deg": 180.0},
        move="faster",
    ),
    C(
        "zx10r with 10 mph headwind",
        "zx10r",
        "ZX-10R",
        env={"wind_speed_ms": 4.4704, "wind_direction_deg": 0.0},
        move="slower",
    ),
    C(
        "ninja 400 at altitude 1500 m",
        "ninja",
        "Ninja 400",
        env={"altitude_m": 1500.0},
        move="slower",
    ),
    C(
        "RE classic 350 at 3000 ft elevation",
        "classic",
        "Classic 350",
        env={"altitude_m": 914.4},
        move="slower",
    ),
    C(
        "continental gt 650 at 28C, 50% humidity",
        "gt650",
        "Continental GT 650",
        env={"ambient_temp_c": 28.0, "humidity_pct": 50.0},
        move="slower",
    ),
    C("bullet at 15C", "bullet", "Bullet", env={"ambient_temp_c": 15.0}, move="faster"),
    C(
        "pulsar ns200 with rubber buildup",
        "ns200",
        "NS 200",
        env={"track_prep": TRACK_RUBBER},
        move="changed",
    ),
    C(
        "apache rr 310 with vht",
        "rr310",
        "Apache RR 310",
        env={"track_prep": TRACK_VHT},
        move="changed",
    ),
    C(
        "KTM RC390 at 40C",
        "rc390",
        "RC 390",
        env={"ambient_temp_c": 40.0},
        move="slower",
    ),
    # venues
    C("my Hayabusa at Pomona", "hayabusa", "Hayabusa", venue="Pomona", move="faster"),
    C("my Duke 390 at Santa Pod", "duke", "390 Duke", venue="Santa Pod"),
    C("Yamaha R15 V4 at Dubai", "r15", "R15 V4", venue="Dubai"),
    # parts wanted
    C(
        "my Hayabusa with exhaust",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        move="faster",
    ),
    C(
        "my Hayabusa with a turbo",
        "hayabusa",
        "Hayabusa",
        parts=["turbo"],
        move="faster",
    ),
    C(
        "my Hayabusa with nitrous",
        "hayabusa",
        "Hayabusa",
        parts=["nitrous"],
        move="faster",
    ),
    C("gsxr 1000 K5 with ecu flash", "gsxr", "K5", parts=["ecu"], move="faster"),
    C("zx10r with air filter", "zx10r", "ZX-10R", parts=["air_filter"]),
    C("duke 390 with exhaust", "duke", "390 Duke", parts=["exhaust"]),
    C("R15 V4 with quickshifter", "r15", "R15 V4", parts=["quickshifter"]),
    C(
        "ninja 400 with exhaust and air filter",
        "ninja",
        "Ninja 400",
        parts=["exhaust", "air_filter"],
    ),
    C(
        "my Hayabusa with exhaust and ecu",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust", "ecu"],
        move="faster",
    ),
    C("my Hayabusa with clutch", "hayabusa", "Hayabusa", parts=["clutch"]),
    # parts ruled out
    C(
        "my Hayabusa without exhaust",
        "hayabusa",
        "Hayabusa",
        excluded=["exhaust"],
        move="same",
    ),
    C(
        "my Hayabusa with no turbo",
        "hayabusa",
        "Hayabusa",
        excluded=["turbo"],
        move="same",
    ),
    C(
        "my Hayabusa with stock exhaust",
        "hayabusa",
        "Hayabusa",
        excluded=["exhaust"],
        move="same",
    ),
    C(
        "my Hayabusa, don't add nitrous",
        "hayabusa",
        "Hayabusa",
        excluded=["nitrous"],
        move="same",
    ),
    C(
        "my Hayabusa with exhaust but no turbo",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        excluded=["turbo"],
        move="faster",
    ),
    C(
        "my Hayabusa with ecu except exhaust",
        "hayabusa",
        "Hayabusa",
        parts=["ecu"],
        excluded=["exhaust"],
        move="faster",
    ),
    C(
        "my Hayabusa with exhaust, no nitrous",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        excluded=["nitrous"],
        move="faster",
    ),
    C(
        "gsxr 1000 K5 without turbo or nitrous",
        "gsxr",
        "K5",
        excluded=["turbo", "nitrous"],
        move="same",
    ),
    # budgets
    C(
        "my Hayabusa with exhaust budget 50k",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        budget=50_000,
    ),
    C(
        "my Hayabusa with exhaust under ₹1.5 lakh",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        budget=150_000,
        move="faster",
    ),
    C(
        "my Hayabusa with exhaust budget 100",
        "hayabusa",
        "Hayabusa",
        budget=100,
        move="same",
    ),
    C(
        "my Hayabusa with exhaust and ecu budget 2,00,000",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust", "ecu"],
        budget=200_000,
        move="faster",
    ),
    C(
        "my Hayabusa with turbo, no budget",
        "hayabusa",
        "Hayabusa",
        parts=["turbo"],
        move="faster",
    ),
    # docstring-style and combined
    C(
        "optimize my Hayabusa for 35°C at Aamby Valley with a 50000 INR budget",
        "hayabusa",
        "Hayabusa",
        env={"ambient_temp_c": 35.0},
        venue="Aamby",
        budget=50_000,
        move="slower",
    ),
    C(
        "setup K5 for 28C, 50% humidity, budget 100000 INR",
        "gsxr",
        "K5",
        env={"ambient_temp_c": 28.0, "humidity_pct": 50.0},
        budget=100_000,
        move="slower",
    ),
    C(
        "what ET does my Hayabusa run with turbo at Pomona in summer?",
        "hayabusa",
        "Hayabusa",
        parts=["turbo"],
        venue="Pomona",
        move="faster",
    ),
    C(
        "my Hayabusa with exhaust at 30C",
        "hayabusa",
        "Hayabusa",
        parts=["exhaust"],
        env={"ambient_temp_c": 30.0},
        move="changed",
    ),
    C(
        "Hayabusa with turbo and 5 m/s tailwind",
        "hayabusa",
        "Hayabusa",
        parts=["turbo"],
        env={"wind_speed_ms": 5.0, "wind_direction_deg": 180.0},
        move="faster",
    ),
    C(
        "my busa with nitrous at altitude 1000 m",
        "hayabusa",
        "Hayabusa",
        parts=["nitrous"],
        env={"altitude_m": 1000.0},
        move="changed",
    ),
    C(
        "my 390 duke with exhaust at 30C budget 40k",
        "duke",
        "390 Duke",
        parts=["exhaust"],
        env={"ambient_temp_c": 30.0},
        budget=40_000,
    ),
    C("a 2012 Hayabusa", "hayabusa", "Hayabusa (2008-2012)", move=None, other=True),
    C(
        "the Hayabusa 25th Anniversary",
        "hayabusa",
        "25th Anniversary",
        move=None,
        other=True,
    ),
    C("suzuki gsx-r 1000 2005", "gsxr", "K5", move="same"),
]
assert len(CORPUS) >= 50

_RESULTS: dict[str, dict] = {}


@pytest.fixture(scope="module")
def bases(runner):
    return {k: runner.run_query(f"simulate my {v}") for k, v in BASE.items()}


@pytest.mark.parametrize("case", CORPUS, ids=[c["q"][:60] for c in CORPUS])
def test_end_to_end_corpus(runner, bases, case):
    out = runner.run_query(case["q"])
    assert "error" not in out, out
    _RESULTS[case["q"]] = {
        k: out[k]
        for k in (
            "bike_name",
            "et_s",
            "delta_et_s",
            "environment",
            "applied_parts",
            "parts_excluded",
            "parts_not_applied",
            "parse_notes",
        )
    }
    got_name = out["bike_name"].lower()
    assert all(w in got_name for w in case["name"].lower().split()), out["bike_name"]
    base = bases[case["bike"]]
    assert "error" not in base

    # the config changed only in the intended fields
    env, benv = out["environment"], base["environment"]
    changing = set(case["env"])
    if case["venue"]:
        assert case["venue"].lower() in env["venue"].lower()
        changing |= {"venue", "altitude_m"}
    for key in (
        ()
        if case["other"]
        else (
            "ambient_temp_c",
            "humidity_pct",
            "wind_speed_ms",
            "wind_direction_deg",
            "altitude_m",
            "track_prep",
            "venue",
        )
    ):
        if key in changing:
            if key in case["env"]:
                want = case["env"][key]
                if isinstance(want, float):
                    assert env[key] == pytest.approx(want, abs=0.01), key
                else:
                    assert env[key] == want, key
        else:
            assert env[key] == benv[key], f"{key} changed unexpectedly"

    # parts: exactly the wanted categories (or reported unfittable), never the excluded
    applied = {d["category"] for d in out["applied_part_details"]}
    unfit = {m["category"] for m in out["parts_not_applied"]}
    assert applied | unfit == set(case["parts"]) or (
        case["budget"] is not None
        and applied | unfit <= set(case["parts"]) | {"exhaust"}
    ), (applied, unfit)
    assert not applied & set(case["excluded"])
    assert sorted(out["parts_excluded"]) == sorted(case["excluded"])
    if case["budget"] is not None:
        spent = sum(d["price_inr"] or 0 for d in out["applied_part_details"])
        assert spent <= case["budget"]
    if applied:
        assert out["delta_et_s"] < 0  # with parts - without: negative = quicker

    # ET moves the right way relative to the same bike unmodified
    dt = out["et_s"] - base["et_s"]
    move = case["move"]
    if move == "faster":
        assert dt < -1e-4, dt
    elif move == "slower":
        assert dt > 1e-4, dt
    elif move == "same":
        assert dt == pytest.approx(0.0, abs=1e-6), dt
    elif move == "changed":
        assert abs(dt) > 1e-4, dt


def teardown_module(module):
    dump = os.environ.get("NLP_CORPUS_DUMP")
    if dump and _RESULTS:
        with open(dump, "w") as fh:
            json.dump(_RESULTS, fh, indent=2, default=str)
