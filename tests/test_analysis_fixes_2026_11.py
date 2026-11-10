"""
Regression tests for the November 2026 analysis-layer audit fixes.

Every test drives the production path (public functions, the CLI ``main``,
HTTP via TestClient) against a COPY of the shipped catalog. Findings covered:

  F1/F12  autotune launch-RPM liveness + honest guideline wording
  F6      sim memo (identical results, fewer sims)
  F7      joint-sim swap repair
  F8/F11  Bayesian / Sobol parameters are live
  F9      build-profile categories match the catalog
  F10     candidate pool is never truncated
  F5      one sign convention for public ET deltas (+ compare delta)
  zero-effect parts are flagged, never ranked
  physics-core F5: surrogate features read the live rider-mass field
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from motoquant.analysis import build_optimizer as bo, roi as roi_mod
from motoquant.analysis.ecu_autotune import autotune
from motoquant.database.connection import MotoQuantDB

REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")

HAYABUSA = 3  # GSX1300R Gen1 reference bike (two_step False)
DUKE_390 = 66
INTERCEPTOR = 79


# ──────────────────────────────── fixtures ────────────────────────────────
@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("analysis_fixes") / "t.db"
    shutil.copyfile(REPO_DB, path)
    d = MotoQuantDB(str(path))
    d.connect()
    d.test_path = str(path)
    yield d
    d.close()


def _cfg(db, bike_id):
    row = db.bikes.get_current_config(bike_id)
    return db.bikes.to_config(row["id"])


class _Subset:
    """Parts repo restricted to a fixed id set (keeps optimizer tests small)."""

    def __init__(self, repo, ids):
        self._repo = repo
        self._conn = repo._conn
        self.ids = set(ids)

    def search(self, **kw):
        return [p for p in self._repo.search(**kw) if p["id"] in self.ids]

    def get(self, pid):
        return self._repo.get(pid)

    def apply_to_config(self, pid, cfg):
        return self._repo.apply_to_config(pid, cfg)

    def apply_multiple(self, ids, cfg):
        return self._repo.apply_multiple(ids, cfg)


@pytest.fixture
def engine_runs(monkeypatch):
    """Record the config of every full physics sim."""
    import motoquant.physics as phys

    seen = []
    orig = phys.MotoQuantEngine.run

    def run(self, *a, **k):
        seen.append(copy.deepcopy(self.cfg))
        return orig(self, *a, **k)

    monkeypatch.setattr(phys.MotoQuantEngine, "run", run)
    return seen


# ───────────────────────────── F1 / F12 autotune ─────────────────────────────
class TestAutotuneLaunchLiveness:
    def test_no_two_step_means_no_launch_recommendation(self, db, engine_runs):
        cfg = _cfg(db, HAYABUSA)
        assert cfg.staging.two_step is False
        stock_launch = cfg.staging.launch_rpm
        res = autotune(cfg, gear_span=1, launch_steps=4)
        lr = res.launch_rpm
        assert lr["adjustable"] is False
        assert lr["recommended_rpm"] is None
        assert lr["delta_et_s"] == 0.0
        assert "not modelled" in lr["reason"]
        # No sim ever varied the launch RPM, and the combined verification
        # did not feed one in.
        assert {c.staging.launch_rpm for c in engine_runs} == {stock_launch}
        # gearing sweep (<=5 teeth) + stock + combined; no 6-7 launch sims
        assert len(engine_runs) <= 1 + 5 + 1
        assert "not modelled" in res.summary()

    def test_two_step_bike_keeps_a_live_recommendation(self, db):
        cfg = _cfg(db, HAYABUSA)
        cfg.staging.two_step = True
        res = autotune(cfg, gear_span=1, launch_steps=4)
        lr = res.launch_rpm
        assert lr["adjustable"] is True
        assert lr["recommended_rpm"] is not None
        assert len({c["et_s"] for c in lr["candidates"]}) > 1
        assert lr["delta_et_s"] <= 1e-9
        # the recommendation is genuinely the quickest candidate
        assert lr["et_s"] == min(c["et_s"] for c in lr["candidates"])

    def test_route_reports_not_adjustable(self, db):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        os.environ["MOTOQUANT_DB"] = db.test_path
        from motoquant import api

        client = TestClient(api.app)
        r = client.post(
            "/api/autotune/ecu",
            json={"bike_id": HAYABUSA, "gear_span": 1, "launch_steps": 3},
        )
        assert r.status_code == 200, r.text
        lr = r.json()["launch_rpm"]
        assert lr["adjustable"] is False
        assert lr["recommended_rpm"] is None

    def test_guidance_is_labelled_not_simulated(self, db):
        res = autotune(_cfg(db, HAYABUSA), gear_span=1, launch_steps=3)
        assert "not simulated" in res.tyre_pressure["rationale"].lower()
        assert "not simulated" in res.fuel_timing["rationale"].lower()
        assert res.tyre_pressure["is_guideline"] is True
        assert res.fuel_timing["is_guideline"] is True
        assert "enlarge" not in res.tyre_pressure["rationale"].lower()

    def test_power_figures_come_from_the_environment_model(self, db, monkeypatch):
        import motoquant.analysis.ecu_autotune as at

        class FakeEnv:
            rho = 1.0  # would imply 18.4 % loss if re-derived from rho / 1.225
            density_alt_ft = 5000.0
            power_correction = 0.80

            def __init__(self, cfg):
                pass

        monkeypatch.setattr(at, "EnvironmentalModel", FakeEnv)
        block, _ = at._environment_block(_cfg(db, HAYABUSA))
        assert block["power_correction_pct"] == 80.0
        assert block["power_loss_pct"] == 20.0


# ─────────────────────────────── F6 sim memo ───────────────────────────────
class TestSimMemo:
    def test_memo_is_keyed_by_config_content(self, db):
        calls = []

        def runner(cfg):
            calls.append(1)
            return 10.0 + cfg.chassis.dry_mass_kg / 1000.0, 50.0

        memo = roi_mod.SimMemo(runner)
        a = _cfg(db, HAYABUSA)
        memo(a)
        memo(copy.deepcopy(a))
        assert len(calls) == 1 and memo.hits == 1
        b = copy.deepcopy(a)
        b.chassis.dry_mass_kg += 1.0
        memo(b)
        assert len(calls) == 2

    def test_optimizer_results_identical_with_fewer_sims(
        self, db, monkeypatch, engine_runs
    ):
        cfg = _cfg(db, HAYABUSA)
        monkeypatch.setattr(bo, "SWAP_REPAIR_MAX_SIMS", 0, raising=False)

        def run(memo_on):
            monkeypatch.setattr(roi_mod, "MEMO_ENABLED", memo_on, raising=False)
            engine_runs.clear()
            out = bo.optimize_build(
                cfg,
                100_000,
                db.parts,
                bike_model_id=HAYABUSA,
                profile="drag_prep",
                max_candidates=70,
            ).to_dict()
            out["scoring_stats"] = {
                k: v
                for k, v in out["scoring_stats"].items()
                if k not in ("sims_run", "sims_memoized")
            }
            return json.dumps(out, sort_keys=True), len(engine_runs)

        off_payload, off_sims = run(False)
        on_payload, on_sims = run(True)
        assert on_payload == off_payload
        assert on_sims < off_sims - 3

    def test_progress_ticks_still_fire_for_memoized_scores(self, db):
        cfg = _cfg(db, HAYABUSA)
        ticks = []
        bo.optimize_build(
            cfg,
            60_000,
            db.parts,
            bike_model_id=HAYABUSA,
            profile="drag_prep",
            max_candidates=12,
            progress_cb=lambda f, s=None: ticks.append((f, s)),
        )
        scoring = [t for t in ticks if t[1] == "Scoring candidate parts"]
        assert len(scoring) >= 12  # one tick per scorer call, memo hit or not


# ─────────────────────────────── F7 swap repair ───────────────────────────────
class _Part:
    def __init__(self, pid, cat, price, gain):
        self.part_id, self.category, self.price_inr = pid, cat, float(price)
        self.delta_et_s, self.delta_trap_ms = float(gain), 0.0
        self.is_compatible = True


class _StubRepo:
    _conn = None

    def apply_multiple(self, ids, cfg):
        return tuple(sorted(ids))


class _StubPredictor:
    """Non-additive joint ET table: ids -> ET."""

    def __init__(self, table):
        self.table = table
        self.calls = 0

    def full_sim(self, key):
        self.calls += 1
        return self.table.get(key, 10.0), 50.0


class TestSwapRepairUnit:
    def _setup(self, table):
        # A and B are both worth 0.30 alone but overlap; C is worth 0.25 alone
        # and stacks cleanly with A, so the joint optimum is {A, C}.
        a = _Part(1, "x_a", 100, 0.30)
        b = _Part(2, "x_b", 100, 0.30)
        c = _Part(3, "x_c", 100, 0.25)
        return [a, b, c]

    def test_swap_found_by_joint_sim(self):
        parts = self._setup(None)
        a, b, c = parts
        table = {
            (1,): 9.70,
            (2,): 9.70,
            (3,): 9.75,
            (1, 2): 9.68,
            (1, 3): 9.50,
            (2, 3): 9.60,
        }
        pred = _StubPredictor(table)
        out, sims = bo._swap_repair(
            None,
            [a, b],
            parts,
            200.0,
            "min_et",
            parts_repo=_StubRepo(),
            predictor=pred,
            position_of={},
            slot_of={},
        )
        assert {r.part_id for r in out} == {1, 3}
        assert 0 < sims <= bo.SWAP_REPAIR_MAX_SIMS

    def test_budget_and_cap_respected(self):
        parts = self._setup(None)
        a, b, c = parts
        pred = _StubPredictor({(1, 3): 9.0, (2, 3): 9.0})
        out, _ = bo._swap_repair(
            None,
            [a, b],
            parts,
            150.0,
            "min_et",
            parts_repo=_StubRepo(),
            predictor=pred,
            position_of={},
            slot_of={},
        )  # swapping needs 200 of budget; only 150 -> no feasible move
        assert {r.part_id for r in out} == {1, 2}
        pool = [_Part(10 + i, f"c{i}", 10, 0.1) for i in range(30)]
        pred2 = _StubPredictor({})
        _, sims = bo._swap_repair(
            None,
            pool[:2],
            pool,
            1000.0,
            "min_et",
            parts_repo=_StubRepo(),
            predictor=pred2,
            position_of={},
            slot_of={},
        )
        assert sims <= bo.SWAP_REPAIR_MAX_SIMS

    def test_cancellation_propagates(self):
        class Cancelled(BaseException):
            pass

        parts = self._setup(None)

        def cb(f, s=None):
            raise Cancelled

        with pytest.raises(Cancelled):
            bo._swap_repair(
                None,
                [parts[0], parts[1]],
                parts,
                200.0,
                "min_et",
                parts_repo=_StubRepo(),
                predictor=_StubPredictor({(1, 3): 9.0}),
                position_of={},
                slot_of={},
                progress_cb=cb,
            )


# Known losing cases from the audit, reproduced on the real catalog. The
# expected sets are the exhaustive (brute-force) optima over the same ten
# candidate parts.
_CASES = [
    (
        INTERCEPTOR,
        90_360,
        [468, 248, 283, 485, 50, 120, 81, 201, 11, 105],
        {50, 468, 11},
    ),
    (
        HAYABUSA,
        310_736,
        [56, 172, 354, 352, 50, 48, 359, 357, 104, 348],
        {172, 50, 359, 354, 104},
    ),
]


class TestSwapRepairRealCatalog:
    @pytest.mark.parametrize("bike,budget,cands,expected", _CASES)
    def test_matches_brute_force_optimum(self, db, bike, budget, cands, expected):
        repo = _Subset(db.parts, cands)
        res = bo.optimize_build(
            _cfg(db, bike),
            budget,
            repo,
            bike_model_id=bike,
            profile="all",
            include_next_upgrade=False,
        )
        assert {p.part_id for p in res.parts} == expected
        assert res.total_cost_inr <= budget
        assert res.scoring_stats["swap_repair_sims"] <= bo.SWAP_REPAIR_MAX_SIMS

    def test_reported_gain_is_the_joint_sim(self, db):
        from motoquant.analysis.roi import _run_et

        cfg = _cfg(db, INTERCEPTOR)
        repo = _Subset(db.parts, _CASES[0][2])
        res = bo.optimize_build(
            cfg, 90_360, repo, bike_model_id=INTERCEPTOR, include_next_upgrade=False
        )
        joint_cfg = db.parts.apply_multiple([p.part_id for p in res.parts], cfg)
        et, _ = _run_et(joint_cfg)
        assert res.optimized_et_s == pytest.approx(et, abs=1e-4)
        additive = sum(p.delta_et_s for p in res.parts)
        assert res.delta_et_s != pytest.approx(additive, abs=1e-4)  # not a sum


# ───────────────────────────── F8 / F11 liveness ─────────────────────────────
class TestBayesianSobolLiveness:
    def _et(self, cfg):
        return roi_mod._run_et(cfg)[0]

    def test_every_bayesian_parameter_changes_et(self, db):
        from motoquant.analysis.bayesian_opt import BayesianBuildOptimizer

        base = _cfg(db, HAYABUSA)
        opt = BayesianBuildOptimizer(base)
        et0 = self._et(opt._apply_params_to_config({}))
        assert "rear_pressure_delta" not in opt.PARAM_BOUNDS
        dead = []
        for key, (lo, hi) in opt.PARAM_BOUNDS.items():
            moved = max(
                abs(self._et(opt._apply_params_to_config({key: v})) - et0)
                for v in (lo, hi)
            )
            if moved < 1e-4:
                dead.append(key)
        assert dead == []

    def test_every_sobol_default_parameter_changes_et(self, db):
        from motoquant.analysis import sobol

        base = _cfg(db, HAYABUSA)
        specs = list(sobol.DEFAULT_PARAM_BOUNDS.values())
        assert "reaction_time" not in sobol.DEFAULT_PARAM_BOUNDS
        prepared = sobol.prepare_config_for_specs(base, specs)
        nominal = [float(sobol._get_nested(prepared, s.path)) for s in specs]
        dead = []
        for i, (key, spec) in enumerate(sobol.DEFAULT_PARAM_BOUNDS.items()):
            ets = []
            for v in (spec.low, spec.high):
                row = np.array(nominal)
                row = np.where(
                    [s.kind == "relative" for s in specs], 1.0, np.array(nominal)
                ).astype(float)
                row[i] = v
                cfg = sobol._apply_sample_row(prepared, specs, nominal, row)
                ets.append(self._et(cfg))
            if abs(ets[0] - ets[1]) < 1e-4:
                dead.append(key)
        assert dead == []


# ─────────────────────────── F9 / F10 candidate pools ───────────────────────────
class TestProfilesAndPools:
    def test_profile_categories_match_catalog(self, db):
        from motoquant.analysis.recommendations import _PROFILE_CATEGORIES, BuildProfile

        catalog = {r["name"] for r in db.parts.list_categories()}
        for profile, cats in _PROFILE_CATEGORIES.items():
            assert cats <= catalog, (profile, cats - catalog)
        assert catalog <= _PROFILE_CATEGORIES[BuildProfile.FULL_RACE]
        for cat in ("lowering_kit", "air_shifter", "lockup_clutch"):
            assert cat in _PROFILE_CATEGORIES[BuildProfile.DRAG_PREP]

    def test_every_owned_call_site_asks_for_the_whole_pool(self, db):
        from motoquant.analysis.recommendations import (
            generate_upgrade_path,
            get_category_upgrade_order,
            recommend_build,
        )

        limits = []

        class Spy:
            _conn = db.parts._conn

            def search(self, **kw):
                limits.append(kw.get("limit"))
                return []

            def get(self, pid):
                return None

        cfg = _cfg(db, HAYABUSA)
        bo.optimize_build(cfg, 50_000, Spy(), bike_model_id=HAYABUSA)
        recommend_build(cfg, 50_000, Spy(), bike_model_id=HAYABUSA)
        generate_upgrade_path(cfg, Spy(), bike_model_id=HAYABUSA)
        get_category_upgrade_order(cfg, Spy(), bike_model_id=HAYABUSA)
        roi_mod.find_best_build(cfg, 50_000, Spy(), bike_model_id=HAYABUSA)
        assert limits and all(lim >= 1000 for lim in limits), limits

    def test_agent_part_search_is_not_truncated(self, db, monkeypatch):
        from motoquant.database import parts_repo as pr
        from motoquant.llm import agent

        seen = []
        orig = pr.PartsRepository.search

        def spy(self, *a, **kw):
            seen.append(kw.get("limit"))
            return orig(self, *a, **kw)

        monkeypatch.setattr(pr.PartsRepository, "search", spy)
        ctx = SimpleNamespace(db=db, add_block=lambda *a, **k: None)
        out = agent._exec_search_parts(ctx, {"bike_id": HAYABUSA, "limit": 30})
        assert out["count"] == 30
        assert seen and all(lim >= 1000 for lim in seen)

    def test_large_pools_are_returned_whole(self, db):
        sizes = {
            bid: len(db.parts.search(bike_model_id=bid, limit=roi_mod._ALL_PARTS_LIMIT))
            for bid in (1, 2, 3, 17)
        }
        over = {b: n for b, n in sizes.items() if n > 200}
        if not over:
            pytest.skip(f"no catalog bike currently has a >200-part pool: {sizes}")
        for bid, n in over.items():
            capped = db.parts.search(bike_model_id=bid, limit=200)
            assert len(capped) == 200 < n


# ─────────────────────────── zero-effect parts ───────────────────────────
class TestZeroEffectParts:
    NO_MODIFIER_PART = 102  # catalog row with no modifiers at all

    def test_flagged_not_ranked(self, db):
        cfg = _cfg(db, HAYABUSA)
        rows = roi_mod.compute_parts_roi(
            cfg, [self.NO_MODIFIER_PART, 56], db.parts, bike_model_id=HAYABUSA
        )
        by_id = {r.part_id: r for r in rows}
        dead = by_id[self.NO_MODIFIER_PART]
        assert dead.no_straight_line_effect is True
        assert dead.roi_score == 0.0
        assert by_id[56].no_straight_line_effect is False
        assert rows[0].part_id == 56  # real upgrade ranks first

    def test_never_selected_or_recommended(self, db):
        repo = _Subset(db.parts, [self.NO_MODIFIER_PART, 56])
        res = bo.optimize_build(
            _cfg(db, HAYABUSA), 10_000_000, repo, bike_model_id=HAYABUSA
        )
        assert self.NO_MODIFIER_PART not in {p.part_id for p in res.parts}
        flagged = {
            p["part_id"]: p["no_straight_line_effect"] for p in res.to_dict()["parts"]
        }
        assert flagged.get(56) is False


# ─────────────────────── F5 sign convention & compare ───────────────────────
def _cli(db, argv):
    from unittest.mock import patch

    from motoquant.run import main

    buf = io.StringIO()
    with patch("motoquant.run.ensure_db", return_value=db):
        with contextlib.redirect_stdout(buf):
            main(argv)
    return json.loads(buf.getvalue())


class TestDeltaSign:
    PART = 240  # Akrapovic slip-on, a real quarter-mile gain on the Duke 390

    def test_one_sign_everywhere(self, db):
        roi_out = _cli(
            db,
            [
                "analysis",
                "roi",
                "--bike-id",
                str(DUKE_390),
                "--part-ids",
                str(self.PART),
                "--json",
            ],
        )
        row = roi_out["parts"][0]
        impact = _cli(
            db,
            ["parts", "--bike-id", str(DUKE_390), "--impact", str(self.PART), "--json"],
        )
        res = bo.optimize_build(
            _cfg(db, DUKE_390),
            1_000_000,
            _Subset(db.parts, [self.PART]),
            bike_model_id=DUKE_390,
            include_next_upgrade=False,
        )
        opt = res.to_dict()["parts"][0]
        rec_out = _cli(
            db,
            [
                "analysis",
                "recommend",
                "--bike-id",
                str(DUKE_390),
                "--budget",
                "1000000",
                "--json",
            ],
        )
        assert row["delta_et_s"] < -0.05  # negative = quicker
        assert row["et_gain_s"] == pytest.approx(-row["delta_et_s"], abs=1e-4)
        assert impact["delta_et_s"] == pytest.approx(row["delta_et_s"], abs=2e-3)
        assert opt["delta_et_s"] == pytest.approx(row["delta_et_s"], abs=2e-3)
        assert impact["delta_trap_mps"] == pytest.approx(
            row["delta_trap_mps"], abs=5e-3
        )
        assert opt["delta_trap_mps"] == pytest.approx(row["delta_trap_mps"], abs=5e-3)
        # recommend payload: quicker build => negative delta, plus a positive gain
        assert rec_out["delta_et_s"] < 0 < rec_out["et_gain_s"]
        assert all(p["delta_et_s"] <= 0 for p in rec_out["parts_selected"])

    def test_compare_delta_is_b_minus_a_in_agent_and_runner(self, db, monkeypatch):
        from motoquant.llm import runner
        from motoquant.llm.agent import run_agent_chat
        from motoquant.llm.client import LLMClient

        script = iter(
            [
                {
                    "tool_calls": [
                        {
                            "id": "c0",
                            "name": "compare_bikes",
                            "arguments": {"bike_a_id": 11, "bike_b_id": 1},
                        }
                    ]
                },
                "done",
            ]
        )
        client = LLMClient(_call_override=lambda kind, kwargs: next(script))
        res = run_agent_chat("busa vs k5", db, client=client)
        blk = res.last_block("compare_result")
        a, b = blk["bike_a"]["et_quarter_s"], blk["bike_b"]["et_quarter_s"]
        assert blk["delta_et_s"] == pytest.approx(b - a, abs=1e-4)
        assert blk["winner"] == (blk["bike_a"] if b > a else blk["bike_b"])["bike_name"]

        sims = {
            1: {"et_quarter_s": 10.0, "trap_speed_kmh": 200.0},
            2: {"et_quarter_s": 10.3, "trap_speed_kmh": 190.0},
        }
        monkeypatch.setattr(runner, "_run_one_sim", lambda bid, p, d: sims[bid])
        parsed = SimpleNamespace(
            bike_id=1, bike_name="A", bike_b_id=2, bike_b_name="B", raw_query="q"
        )
        out = runner._run_compare(
            parsed,
            db,
            None,
            runner.ChatResult(raw_query="q"),
            run_summary=False,
            suggestion_limit=3,
        )
        cmp = out.compare_result
        assert cmp["delta_et_s"] == pytest.approx(0.3, abs=1e-6)  # B - A
        assert cmp["delta_trap_kmh"] == pytest.approx(-10.0, abs=1e-6)
        assert cmp["faster"] == "A"


# ───────────────────── physics-core F5: surrogate rider mass ─────────────────────
class TestSurrogateRiderMass:
    def test_features_read_the_live_rider_mass_field(self, db):
        from motoquant.analysis.surrogate_data import (
            FEATURE_NAMES,
            config_to_feature_vector,
        )

        i = FEATURE_NAMES.index("total_mass_kg")
        cfg = _cfg(db, HAYABUSA)
        base = config_to_feature_vector(cfg)[i]
        heavy = copy.deepcopy(cfg)
        heavy.chassis.rider_mass_kg += 15.0
        assert config_to_feature_vector(heavy)[i] == pytest.approx(base + 15.0)
        # the duplicate, unread copy must not leak into the features
        phantom = copy.deepcopy(cfg)
        phantom.rider.mass_kg = 120.0
        assert config_to_feature_vector(phantom)[i] == pytest.approx(base)
