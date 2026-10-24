"""
build_optimizer.optimize_build fixes (October 2026 audit), on the real catalog.

Every test drives ``optimize_build`` itself (the function behind
/api/optimize/build and the outlaw pipeline). A pool-restricting wrapper
around the real PartsRepository keeps the candidate list small and
deterministic; everything downstream (ROI pass, surrogate predictor, knapsack,
verification, refinement) is production code.
"""

import os
import sqlite3
from pathlib import Path

import pytest

from motoquant import engine_select
from motoquant.analysis import build_optimizer
from motoquant.analysis.build_optimizer import make_predictor, optimize_build
from motoquant.database.bridge import db_row_to_config
from motoquant.database.parts_repo import PartsRepository

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "motoquant.db"
ARTIFACT = ROOT / "artifacts" / "surrogate" / "surrogate_numpy.npz"


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


@pytest.fixture(scope="module")
def surrogate():
    if not ARTIFACT.exists():
        pytest.skip("numpy surrogate artifact missing")
    from motoquant.analysis.surrogate_numpy import NumpySurrogate

    return NumpySurrogate.load(ARTIFACT)


def _cfg(conn, bike_id):
    row = conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id=? AND config_name='stock' "
        "AND is_current=1",
        (bike_id,),
    ).fetchone()
    return db_row_to_config(dict(row), name=f"bike {bike_id}")


class _PoolRepo:
    """Real PartsRepository restricted to a fixed candidate pool."""

    def __init__(self, repo, ids):
        self._repo = repo
        self._ids = set(ids)
        self._conn = repo._conn
        self.discovered: list[int] = []

    def search(self, **kw):
        rows = self._repo.search(**kw)
        self.discovered = [r["id"] for r in rows]
        return [r for r in rows if r["id"] in self._ids]

    def __getattr__(self, name):
        return getattr(self._repo, name)


def _full_et(repo, cfg, ids):
    r = engine_select.make_engine(repo.apply_multiple(ids, cfg)).run()
    return float(r.time_quarter)


def _applied(res):
    return getattr(res, "applied_part_ids", None) or [
        p.part_id for p in sorted(res.parts, key=lambda p: p.price_inr)
    ]


# ─────────────────────── combined build is a full sim ───────────────────────
class TestCombinedBuildIsFullSim:
    def test_reported_build_matches_independent_full_sim(self, conn, repo, surrogate):
        # Audit repro (bike 5, ₹60k, street_legal, numpy surrogate): reported
        # 10.2376 s / -0.180 s while a full sim of the same list gave
        # 10.0933 s / -0.324 s.
        cfg = _cfg(conn, 5)
        res = optimize_build(
            cfg,
            60_000,
            _PoolRepo(repo, [13, 50, 359, 289, 88, 11, 354]),
            profile="street_legal",
            bike_model_id=5,
            surrogate=surrogate,
            surrogate_source="numpy",
            full_physics=False,
        )
        assert res.parts, "expected an improving build"
        truth = _full_et(repo, cfg, _applied(res))
        assert res.optimized_et_s == pytest.approx(round(truth, 4), abs=1e-4)
        base = _full_et(repo, cfg, [])
        assert res.delta_et_s == pytest.approx(round(truth - base, 4), abs=2e-4)
        if res.cost_per_tenth_inr is not None:
            assert res.cost_per_tenth_inr == pytest.approx(
                res.total_cost_inr / (-(truth - base) * 10.0), rel=1e-3
            )


# ─────────────────────── feature-blind fallback ───────────────────────
class TestFeatureBlindFallback:
    @pytest.mark.parametrize("part_id,bike_id", [(548, 1), (546, 2), (550, 49)])
    def test_blind_plus_visible_part_is_full_simmed(
        self, conn, repo, surrogate, part_id, bike_id
    ):
        # Model-specific quickshifters change the shift time (invisible to
        # the 26 features) AND add ~0.15 kg (visible): the old bit-identical
        # gate surrogate-scored them at ~+0.001 s instead of ~-0.05 s.
        cfg = _cfg(conn, bike_id)
        pred = make_predictor(surrogate, "numpy")
        base_et, _ = pred(cfg)
        mod = repo.apply_to_config(part_id, cfg)
        pred_et, _ = pred(mod)
        true_et = _full_et(repo, cfg, [part_id])
        assert pred_et == pytest.approx(true_et, abs=1e-6)
        assert pred_et - base_et < -0.02
        assert pred.stats()["feature_blind"] >= 1

    def test_uniform_power_scale_still_uses_the_surrogate(self, conn, repo, surrogate):
        # A plain ECU power part only rescales the dyno curve, which the
        # peak-power/torque features see — it must stay surrogate-scored, or
        # the surrogate would never be used for power parts.
        cfg = _cfg(conn, 5)
        pred = make_predictor(surrogate, "numpy")
        pred(cfg)
        pred(repo.apply_to_config(50, cfg))
        assert pred.stats()["surrogate_calls"] >= 2
        assert pred.stats()["feature_blind"] == 0


# ─────────────────────── forced-induction slot ───────────────────────
class TestForcedInductionSlot:
    def test_nitrous_and_supercharger_never_both_selected(self, conn, repo):
        # Audit repro: bike 11 at ₹4.5L picked BOTH a 60 HP nitrous kit and a
        # supercharger; the nitrous was erased by the SC's boost_type.
        res = optimize_build(
            _cfg(conn, 11),
            450_000,
            _PoolRepo(repo, [143, 140, 137, 50, 354]),
            bike_model_id=11,
        )
        boost = [p for p in res.parts if p.category in ("boost_kit", "nitrous")]
        assert len(boost) <= 1, [p.part_id for p in boost]

    def test_na_power_parts_are_applied_before_boost(self, conn, repo):
        # Price order put the ₹95k nitrous before the ₹238k exhaust, so the
        # exhaust's dyno-curve scaling was skipped (engine already boosted).
        cfg = _cfg(conn, 11)
        res = optimize_build(cfg, 400_000, _PoolRepo(repo, [143, 56]), bike_model_id=11)
        assert sorted(p.part_id for p in res.parts) == [56, 143]
        assert res.applied_part_ids == [56, 143]
        good = _full_et(repo, cfg, [56, 143])
        bad = _full_et(repo, cfg, [143, 56])
        assert good < bad
        assert res.optimized_et_s == pytest.approx(round(good, 4), abs=1e-4)


# ─────────────────────── slot stacking ───────────────────────
class TestSlotStacking:
    def test_quickshifter_module_in_ecu_category_does_not_stack(self, conn, repo):
        # HealTech QS module (117, filed under 'ecu') stacked with a real QS
        # (359): its absolute 60 ms override replaced 48 ms -> ₹33,951 spent
        # on a regression.
        res = optimize_build(
            _cfg(conn, 5), 150_000, _PoolRepo(repo, [359, 117]), bike_model_id=5
        )
        ids = {p.part_id for p in res.parts}
        assert not {359, 117} <= ids

    def test_fuel_and_bodywork_parts_one_per_slot(self, conn, repo):
        from motoquant.analysis.roi import part_slot

        pool = [
            p["id"]
            for p in repo.search(bike_model_id=11, limit=10**6)
            if p["category_name"] in ("fuel_system", "bodywork")
        ]
        res = optimize_build(
            _cfg(conn, 11),
            5_000_000,
            _PoolRepo(repo, pool),
            profile="full_race",
            bike_model_id=11,
        )
        slots = [part_slot(repo.get(p.part_id)) for p in res.parts]
        claimed = [s for s in slots if s]
        assert len(claimed) == len(set(claimed)), claimed
        assert slots.count("bodywork:fairing") <= 1
        assert slots.count("fuel_system:controller") <= 1


# ─────────────────────── gearing pairs / drop-one ───────────────────────
class TestBuildNeverWorseThanItsParts:
    def test_sprocket_pair_cannot_undo_the_turbo(self, conn, repo):
        # Audit repro: on drag slicks the knapsack added front 15T (274) and
        # rear 50T (31), each ~-0.11 s alone; together (+39% final drive) the
        # turbo build verified 0.83 s slower than the turbo alone.
        cfg = _cfg(conn, 11)
        cfg.tires.mu_peak = 1.92
        res = optimize_build(
            cfg,
            400_000,
            _PoolRepo(repo, [137, 31, 274]),
            profile="full_race",
            bike_model_id=11,
        )
        turbo_alone = _full_et(repo, cfg, [137])
        assert res.optimized_et_s <= round(turbo_alone, 4) + 1e-4
        for p in res.parts:
            assert (
                res.optimized_et_s <= round(_full_et(repo, cfg, [p.part_id]), 4) + 1e-4
            )


# ─────────────────────── verified ROI metrics ───────────────────────
class TestVerifiedRoiMetrics:
    def test_cost_per_tenth_follows_the_verified_delta(self, conn, repo, surrogate):
        # Audit repro: PCVI Stage 2 on bike 11 showed delta -0.0845 s but
        # cost-per-tenth ₹40,780 (the delta implied ₹21,065).
        res = optimize_build(
            _cfg(conn, 11),
            450_000,
            _PoolRepo(repo, [50, 354, 56, 25]),
            profile="street_legal",
            bike_model_id=11,
            surrogate=surrogate,
            surrogate_source="numpy",
            full_physics=False,
        )
        assert res.parts
        for p in res.parts:
            if p.delta_et_s < -0.005:
                implied = p.price_inr / (-p.delta_et_s * 10.0)
                assert p.cost_per_tenth_inr == pytest.approx(implied, rel=2e-3), p
                assert p.roi_score == pytest.approx(
                    -p.delta_et_s / p.price_inr * 100_000, rel=2e-3
                )


# ─────────────────────── next upgrade ───────────────────────
class TestNextUpgrade:
    def test_next_upgrade_is_a_real_gain_in_a_free_slot(self, conn, repo):
        # Audit repro: bike 77 build had front sprocket 210 and next_upgrade
        # offered front sprocket 211 (+0.108 s claimed, 0.127 s SLOWER real).
        cfg = _cfg(conn, 77)
        res = optimize_build(
            cfg,
            8_000,
            _PoolRepo(repo, [210, 211, 231, 233, 227]),
            profile="street_legal",
            bike_model_id=77,
        )
        chosen = {p.part_id for p in res.parts}
        nu = res.next_upgrade
        if nu is None:
            return
        pid = nu["part"]["part_id"]
        assert not ({210, 211} <= chosen | {pid})
        assert not ({231, 233} <= chosen | {pid})
        real = _full_et(repo, cfg, _applied(res)) - _full_et(
            repo, cfg, _applied(res) + [pid]
        )
        assert nu["marginal_et_gain_s"] == pytest.approx(real, abs=2e-3)
        assert nu["marginal_et_gain_s"] > 0


# ─────────────────────── candidate discovery ───────────────────────
class TestCandidateDiscovery:
    def test_optimizer_discovers_every_compatible_part(self, conn, repo):
        compatible = repo.search(bike_model_id=3, limit=10**6)
        assert len(compatible) > 200
        pool = _PoolRepo(repo, [354])
        optimize_build(_cfg(conn, 3), 10_000, pool, bike_model_id=3)
        assert len(pool.discovered) == len(compatible)
        for pid in (141, 100, 383, 149, 104):  # the parts the 200-cap dropped
            assert pid in pool.discovered


# ─────────────────────── native engine / honest scorer ───────────────────────
_NATIVE = engine_select.native_active()


class TestNativeScoring:
    @pytest.mark.skipif(not _NATIVE, reason="Rust core not active")
    def test_native_scores_every_candidate_with_full_physics(
        self, conn, repo, surrogate
    ):
        res = optimize_build(
            _cfg(conn, 5),
            60_000,
            _PoolRepo(repo, [13, 50, 359, 88]),
            bike_model_id=5,
            surrogate=surrogate,
            surrogate_source="numpy",
        )
        stats = res.scoring_stats
        assert stats["engine"] == "native"
        assert stats["surrogate_calls"] == 0
        assert "surrogate_skipped" in stats
        assert res.scoring_method == "full_sim"

    def test_python_engine_keeps_the_surrogate_path(
        self, conn, repo, surrogate, monkeypatch
    ):
        monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
        res = optimize_build(
            _cfg(conn, 5),
            60_000,
            _PoolRepo(repo, [13, 50]),
            bike_model_id=5,
            surrogate=surrogate,
            surrogate_source="numpy",
        )
        assert res.scoring_stats["engine"] == "python"
        assert res.scoring_stats["surrogate_calls"] > 0
        assert res.scoring_stats["final_build"] == "full_sim"

    def test_cpu_yield_only_on_the_python_engine(
        self, conn, repo, surrogate, monkeypatch
    ):
        sleeps = []
        monkeypatch.setattr(build_optimizer.time, "sleep", sleeps.append)

        def run():
            optimize_build(
                _cfg(conn, 5),
                60_000,
                _PoolRepo(repo, [13, 50]),
                bike_model_id=5,
                surrogate=surrogate,
                surrogate_source="numpy",
                full_physics=False,
            )

        if _NATIVE:
            run()
            assert sleeps == [], "Rust core releases the GIL — no yield needed"
        monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
        run()
        assert sleeps, "Python engine verification sims must still yield"


@pytest.mark.skipif(
    not (_NATIVE or os.environ.get("MOTOQUANT_SLOW_TESTS") == "1"),
    reason="whole-catalog build: needs the Rust core or MOTOQUANT_SLOW_TESTS=1",
)
class TestWholeCatalogOutlawBuild:
    def test_no_limit_full_race_build_is_buildable(self, conn, repo):
        from motoquant.analysis.roi import part_slot

        cfg = _cfg(conn, 11)
        cfg.tires.mu_peak = 1.92
        res = optimize_build(
            cfg, 5_000_000, repo, profile="full_race", bike_model_id=11
        )
        slots = [part_slot(repo.get(p.part_id)) for p in res.parts]
        claimed = [s for s in slots if s]
        assert len(claimed) == len(set(claimed)), claimed
        cats = [p.category for p in res.parts]
        assert cats.count("boost_kit") + cats.count("nitrous") <= 1
        assert res.optimized_et_s == pytest.approx(
            round(_full_et(repo, cfg, res.applied_part_ids), 4), abs=1e-4
        )
        # never worse than the best single part on its own
        best_single = min(_full_et(repo, cfg, [p.part_id]) for p in res.parts)
        assert res.optimized_et_s <= round(best_single, 4) + 1e-4
