"""Chat-agent tool arguments arrive loosely typed and unbounded.

Ported from the never-merged PRs #117 and #119 (closed in favour of #126):

* #117 — the model sends integers as "5", "5.0", "5 bikes", "top 3"…; a bare
  int() raised ValueError and aborted the whole tool call (Sentry
  MOTOQUANTAPI-2, search_bikes).
* #119 — a repeated part id was applied and priced once per repeat (a
  fabricated ET gain and N x the cost), and an unbounded chat budget sized
  roi's knapsack DP past the instance's memory.

Every test drives the real tool executors against a copy of the shipped
catalog; reverting the fix in motoquant/llm/agent.py turns them red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from motoquant.engine_select import make_engine
from motoquant.llm import agent as agent_mod
from motoquant.llm.agent import (
    AGENT_MAX_BUDGET_INR,
    AgentChatResult,
    AgentContext,
    _as_int,
    _build_config_for,
    _exec_optimize_build,
    _exec_search_bikes,
)
from tests._helpers import live_db_copy

REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"
HAYABUSA_GEN2 = 11  # bike_models.id "Hayabusa (2008-2012)"
AKRAPOVIC_HAYABUSA = 56  # "Racing Full System Hayabusa"


@pytest.fixture(scope="module")
def db():
    d = live_db_copy(REPO_DB)
    if d is None:
        pytest.skip("shipped motoquant.db not available")
    yield d
    d.close()


def _ctx(db):
    return AgentContext(db=db, result=AgentChatResult(raw_query=""))


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        (5, None, 5),
        (5.0, None, 5),
        ("5", None, 5),
        ("5.0", None, 5),
        (" 5 ", None, 5),
        ("5 bikes", None, 5),
        ("top 3", None, 3),
        ("all", 7, 7),
        ("all", None, None),
        ("", 4, 4),
        (None, 9, 9),
        (True, 2, 2),
        (float("nan"), 3, 3),
    ],
)
def test_as_int_contract(value, default, expected):
    assert _as_int(value, default) == expected


@pytest.mark.parametrize("limit", ["5", "5.0", 5.0, " 5 ", "5 bikes", "all", "", None])
def test_search_bikes_tolerates_loosely_typed_limit(db, limit):
    out = _exec_search_bikes(_ctx(db), {"query": "hayabusa", "limit": limit})
    assert "error" not in out
    assert "candidates" in out or "match" in out


def test_string_ids_resolve(db):
    config, _ = _build_config_for(_ctx(db), {"bike_id": str(HAYABUSA_GEN2)})
    assert config is not None


def test_repeated_part_is_applied_and_priced_once(db):
    ctx = _ctx(db)
    once, notes_once = _build_config_for(
        ctx, {"bike_id": HAYABUSA_GEN2, "part_ids": [AKRAPOVIC_HAYABUSA]}
    )
    thrice, notes_thrice = _build_config_for(
        ctx,
        {
            "bike_id": HAYABUSA_GEN2,
            "part_ids": [AKRAPOVIC_HAYABUSA, str(AKRAPOVIC_HAYABUSA), "56.0"],
        },
    )
    assert notes_thrice == notes_once
    assert any(n.startswith("1 parts applied") for n in notes_thrice)
    et_once = make_engine(once).run().time_quarter
    et_thrice = make_engine(thrice).run().time_quarter
    assert et_thrice == et_once


def test_chat_budget_is_clamped_to_the_api_ceiling(db, monkeypatch):
    seen = {}

    class _Result:
        def to_dict(self):
            return {}

    def fake_optimize(config, budget, *a, **kw):
        seen["budget"] = budget
        return _Result()

    monkeypatch.setattr(
        "motoquant.analysis.build_optimizer.optimize_build", fake_optimize
    )
    out = _exec_optimize_build(
        _ctx(db),
        {"bike_id": HAYABUSA_GEN2, "build_tier": "stage_1", "budget_inr": 1e10},
    )
    assert "error" not in out
    assert seen["budget"] == AGENT_MAX_BUDGET_INR == 5_000_000.0


def test_non_numeric_budget_falls_back_to_the_tier_default(db, monkeypatch):
    seen = {}

    class _Result:
        def to_dict(self):
            return {}

    def fake_optimize(config, budget, *a, **kw):
        seen["budget"] = budget
        return _Result()

    monkeypatch.setattr(
        "motoquant.analysis.build_optimizer.optimize_build", fake_optimize
    )
    _exec_optimize_build(
        _ctx(db),
        {"bike_id": HAYABUSA_GEN2, "build_tier": "stage_1", "budget_inr": "lots"},
    )
    assert seen["budget"] == agent_mod.BUILD_TIERS["stage_1"]["default_budget_inr"]
