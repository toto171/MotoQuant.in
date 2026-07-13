"""Regression tests for the SHIPPED numpy surrogate artifact (v2, June 2026).

The artifact at artifacts/surrogate/surrogate_numpy.npz is what production
(Render free tier, numpy-only) actually serves for /api/surrogate/* and what
the Build Optimizer scores candidates through. These tests pin the contract
that made the optimizer fast catalog-wide:

  * the artifact loads via NumpySurrogate and declares the 26-feature schema
    with an embedded training envelope;
  * the envelope covers the FULL bike catalog at stock (the v1 model covered
    240/501 — Hayabusa bike_id=11 was the original out-of-envelope repro);
  * spot predictions stay within 0.5 s of the full physics sim on the
    production DB path;
  * v1 (21-feature) models keep working on a [:21] slice of v2 vectors;
  * forced-induction configs are NEVER scored by the surrogate (boost lives
    outside the feature vector — SurrogatePredictor must full-sim them).
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from motoquant.analysis.build_optimizer import _check_envelope, make_predictor
from motoquant.analysis.surrogate_data import FEATURE_NAMES, config_to_feature_vector
from motoquant.analysis.surrogate_numpy import NumpySurrogate
from motoquant.defaults import gsxr1000_k5

REPO = Path(__file__).resolve().parent.parent
ARTIFACT = REPO / "artifacts" / "surrogate" / "surrogate_numpy.npz"
DB = REPO / "motoquant.db"

#: production spot bikes: (bike_models.id, name) — Hayabusa 11 is the bike the
#: v1 envelope rejected at stock (the original Build-Optimizer slowness repro).
SPOT_BIKES = [(11, "Hayabusa 2008-2012"), (81, "YZF-R15 V4"), (66, "Duke 390")]


def _load_spot_configs():
    """Load spot-bike configs via the production path (bike_configs row)."""
    from motoquant.database.bridge import db_row_to_config

    tmp = Path(tempfile.mkdtemp()) / "mq.db"
    shutil.copy(DB, tmp)  # journal-safe on FUSE-mounted checkouts
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    out = {}
    for bid, name in SPOT_BIKES:
        row = conn.execute(
            "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 "
            "ORDER BY version DESC LIMIT 1",
            (bid,),
        ).fetchone()
        out[bid] = db_row_to_config(dict(row), name=name)
    conn.close()
    return out


@unittest.skipUnless(ARTIFACT.exists(), "shipped artifact missing")
class TestShippedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = NumpySurrogate.load(ARTIFACT)

    def test_schema_is_v2(self):
        self.assertEqual(self.model.n_features, len(FEATURE_NAMES))
        self.assertEqual(self.model.feature_names, FEATURE_NAMES)

    def test_envelope_embedded(self):
        env = self.model.envelope
        self.assertIsNotNone(env, "v2 artifact must embed its training envelope")
        env_min, env_max = env
        self.assertEqual(len(env_min), len(FEATURE_NAMES))
        self.assertTrue(np.all(env_min < env_max))

    @unittest.skipUnless(DB.exists(), "production DB missing")
    def test_envelope_covers_spot_bikes_stock(self):
        env_min, env_max = self.model.envelope
        for bid, cfg in _load_spot_configs().items():
            fvec = config_to_feature_vector(cfg).astype(np.float64)
            inside = bool(np.all((fvec >= env_min) & (fvec <= env_max)))
            self.assertTrue(inside, f"bike_id={bid} stock fell out of envelope")
            ok, violations = _check_envelope(fvec, self.model)
            self.assertTrue(ok, f"bike_id={bid}: {violations}")

    @unittest.skipUnless(DB.exists(), "production DB missing")
    def test_spot_predictions_within_half_second_of_sim(self):
        from motoquant.physics import MotoQuantEngine

        for bid, cfg in _load_spot_configs().items():
            et_pred, _ = self.model.predict_config(cfg)
            et_sim = MotoQuantEngine(cfg).run().time_quarter
            self.assertLess(
                abs(et_pred - et_sim),
                0.5,
                f"bike_id={bid}: surrogate {et_pred:.3f}s vs sim {et_sim:.3f}s",
            )

    def test_out_of_envelope_detected(self):
        cfg = gsxr1000_k5()
        cfg.engine.peak_power_hp *= 4.0  # 640 hp — beyond any training row
        ok, violations = _check_envelope(config_to_feature_vector(cfg), self.model)
        self.assertFalse(ok)
        self.assertIn("peak_power_hp", violations)


class TestV1PrefixCompat(unittest.TestCase):
    def test_wider_vector_is_truncated_for_narrow_models(self):
        """A 21-input (v1-era) model must accept a 26-wide v2 vector."""
        rng = np.random.default_rng(0)
        w = [rng.normal(size=(21, 8)), rng.normal(size=(8, 2))]
        b = [np.zeros(8), np.zeros(2)]
        legacy = NumpySurrogate(
            w,
            b,
            np.zeros(21),
            np.ones(21),
            np.zeros(2),
            np.ones(2),
            FEATURE_NAMES[:21],
        )
        self.assertEqual(legacy.n_features, 21)
        self.assertIsNone(legacy.envelope)  # pre-envelope artifact
        et, trap = legacy.predict(np.zeros(26))  # must not raise
        self.assertEqual(et.shape, (1,))
        self.assertEqual(trap.shape, (1,))

    def test_feature_names_v1_prefix_frozen(self):
        # the append-only contract the truncation relies on
        from motoquant.analysis.surrogate_data import (
            BASE_FEATURE_NAMES,
            DERIVED_FEATURE_NAMES,
        )

        self.assertEqual(FEATURE_NAMES[:21], BASE_FEATURE_NAMES + DERIVED_FEATURE_NAMES)


@unittest.skipUnless(ARTIFACT.exists(), "shipped artifact missing")
class TestBoostedConfigsNeverSurrogateScored(unittest.TestCase):
    def test_nitrous_config_falls_back_to_full_sim(self):
        """forced_induction is invisible to the feature vector; the predictor
        must full-sim boosted configs instead of returning the NA prediction."""
        import copy

        from motoquant.analysis.roi import _run_et

        model = NumpySurrogate.load(ARTIFACT)
        pred = make_predictor(model, "numpy")
        base = gsxr1000_k5()
        pred(base)  # baseline call captures the reference feature vector

        boosted = copy.deepcopy(base)
        # "n2o" is the real boost-type constant — the invalid "nitrous"
        # string this test previously used now raises at engine
        # construction (July-13 hardening), which is the desired behaviour.
        boosted.forced_induction.boost_type = "n2o"
        boosted.forced_induction.n2o_hp_per_stage = 40.0
        self.assertTrue(boosted.forced_induction.is_boosted)
        # features unchanged — without the blind-signature gate the surrogate
        # would claim the nitrous kit is worth exactly nothing
        self.assertTrue(
            np.array_equal(
                config_to_feature_vector(base), config_to_feature_vector(boosted)
            )
        )
        et_pred, _ = pred(boosted)
        et_true, _ = _run_et(boosted)
        self.assertEqual(pred.stats()["feature_blind"], 1)
        self.assertAlmostEqual(et_pred, et_true, places=6)


if __name__ == "__main__":
    unittest.main()
