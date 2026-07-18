"""
Factory speed-limiter model — regression tests (July 17, 2026).

Scoped July 13 (docs/ROADMAP.md): the sim ran litre bikes to their
aero-limited 320-340 km/h against 299-limited published figures (topspeed
sweep bias +28.5 km/h, A/B-proven NOT to be the decel clamp). The model:

  BikeSpec.speed_limiter_kmh  →  spec_to_bike_config  →
  DrivetrainParams.speed_limiter_kmh  →  physics.run() clamps net
  acceleration to <= 0 at/above the limiter speed (deceleration above it
  stays possible), so run_top_speed() plateaus at ≈ the limiter.

Load-bearing property pinned here: the None (unlimited) path is
BIT-IDENTICAL — the hot loop pays only an `is not None` check, so the
pinned K5/R1/Hayabusa baselines and every unannotated bike are untouched
by construction. All tests exercise the production paths (importer,
physics loop, DB bridge, config_io) per docs/INVARIANTS.md I8.
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from motoquant import MotoQuantEngine
from motoquant.config_io import load_config, save_config
from motoquant.database.bridge import config_to_db_row, db_row_to_config
from motoquant.defaults import gsxr1000_k5
from motoquant.models import DrivetrainParams
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import (
    KAWASAKI_Z1000_2014,
    SUZUKI_GSXR1000_L7,
)
from motoquant.scraper.spec import BikeSpec
from motoquant.scraper.validator import score_spec, validate_spec

# Mirrors scripts/check_baselines.py (the CI drift gate) — the limiter's
# None path must leave the pinned reference bit-identical.
K5_PINNED_ET_S = 9.9330563825
BASELINE_TOL_S = 1e-9


def _limited_config():
    """Production path: annotated 299-limited spec → BikeConfig."""
    return spec_to_bike_config(SUZUKI_GSXR1000_L7)


def _unannotated_config():
    """Production path: spec with NO limiter annotation → BikeConfig."""
    return spec_to_bike_config(KAWASAKI_Z1000_2014)


class TestNonePathBitIdentity(unittest.TestCase):
    """Unlimited bikes must be bit-identical with the limiter code in place."""

    def test_default_is_none(self):
        self.assertIsNone(DrivetrainParams().speed_limiter_kmh)
        self.assertIsNone(gsxr1000_k5().drivetrain.speed_limiter_kmh)

    def test_k5_baseline_pinned(self):
        et = MotoQuantEngine(gsxr1000_k5()).run().time_quarter
        self.assertLessEqual(abs(et - K5_PINNED_ET_S), BASELINE_TOL_S)

    def test_unreached_limiter_is_bit_identical_to_none(self):
        # An ARMED limiter the bike never reaches (340 km/h vs a ~235 km/h
        # quarter-mile trap) must not perturb the float stream: the clamp
        # sites only compare, never compute, below the limiter. Combined
        # with test_k5_baseline_pinned this proves the None checks inert.
        for cfg_none in (gsxr1000_k5(), _unannotated_config()):
            cfg_hi = copy.deepcopy(cfg_none)
            cfg_hi.drivetrain.speed_limiter_kmh = 340.0
            r_none = MotoQuantEngine(cfg_none).run()
            r_hi = MotoQuantEngine(cfg_hi).run()
            self.assertEqual(
                repr(r_none.time_quarter), repr(r_hi.time_quarter), cfg_none.name
            )
            self.assertTrue(np.array_equal(r_none.v, r_hi.v), cfg_none.name)
            self.assertTrue(np.array_equal(r_none.x, r_hi.x), cfg_none.name)

    def test_explicit_none_equals_field_absent(self):
        # Legacy DB rows serialized before the field existed deserialize
        # through the same production bridge — simulate one by deleting the
        # key from the JSON blob and prove the sim is identical.
        cfg = _unannotated_config()
        row = config_to_db_row(cfg)
        blob = json.loads(row["drivetrain_params"])
        self.assertIn("speed_limiter_kmh", blob)
        del blob["speed_limiter_kmh"]
        legacy_row = dict(row, drivetrain_params=json.dumps(blob))
        cfg_legacy = db_row_to_config(legacy_row, environment=cfg.environment)
        self.assertIsNone(cfg_legacy.drivetrain.speed_limiter_kmh)
        et_new = MotoQuantEngine(cfg).run().time_quarter
        et_legacy = MotoQuantEngine(cfg_legacy).run().time_quarter
        self.assertEqual(repr(et_new), repr(et_legacy))


class TestValidatorBounds(unittest.TestCase):
    """speed_limiter_kmh bounded ~120-340; presence carries no penalty."""

    @staticmethod
    def _spec(limiter):
        return BikeSpec(
            manufacturer="Testco",
            model_name="Limited 1000",
            displacement_cc=999.0,
            peak_power_hp=180.0,
            peak_power_rpm=12000,
            peak_torque_nm=110.0,
            peak_torque_rpm=10000,
            dry_mass_kg=180.0,
            speed_limiter_kmh=limiter,
        )

    def test_accepts_299(self):
        result = validate_spec(self._spec(299.0))
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertFalse(
            [w for w in result.warnings if "speed_limiter" in w],
            "limiter annotation must not add warnings",
        )

    def test_rejects_50(self):
        result = validate_spec(self._spec(50.0))
        self.assertFalse(result.is_valid)
        self.assertTrue(any("speed_limiter_kmh" in e for e in result.errors))

    def test_rejects_500(self):
        result = validate_spec(self._spec(500.0))
        self.assertFalse(result.is_valid)
        self.assertTrue(any("speed_limiter_kmh" in e for e in result.errors))

    def test_no_confidence_penalty(self):
        bare = self._spec(None)
        annotated = self._spec(299.0)
        score_bare = score_spec(bare, validate_spec(bare))
        score_annotated = score_spec(annotated, validate_spec(annotated))
        self.assertEqual(score_bare, score_annotated)


class TestImporterThreading(unittest.TestCase):
    """spec.speed_limiter_kmh must reach DrivetrainParams via the importer."""

    def test_annotated_spec_threads_through(self):
        self.assertEqual(SUZUKI_GSXR1000_L7.speed_limiter_kmh, 299.0)
        cfg = _limited_config()
        self.assertEqual(cfg.drivetrain.speed_limiter_kmh, 299.0)

    def test_unannotated_spec_stays_none(self):
        self.assertIsNone(KAWASAKI_Z1000_2014.speed_limiter_kmh)
        self.assertIsNone(_unannotated_config().drivetrain.speed_limiter_kmh)


class TestPhysicsClamp(unittest.TestCase):
    """The sim must plateau at ≈ the limiter, and only above it."""

    def test_topspeed_caps_at_limiter(self):
        # GSX-R 1000 L7 (299-limited fleet): unlimited it runs to its
        # aero-limited ~338 km/h — the exact July-13 finding. Reverting the
        # physics clamp, the importer threading, or the annotation all make
        # the limited run blow past 301 and fail here.
        cfg = _limited_config()
        ts = MotoQuantEngine(cfg).run_top_speed()
        self.assertLessEqual(abs(ts.terminal_velocity_kmh - 299.0), 2.0)
        self.assertTrue(ts.reached_plateau)

        stripped = copy.deepcopy(cfg)
        stripped.drivetrain.speed_limiter_kmh = None
        ts_unl = MotoQuantEngine(stripped).run_top_speed()
        self.assertGreater(
            ts_unl.terminal_velocity_kmh,
            320.0,
            "unlimited run should overshoot — otherwise this bike no longer "
            "exercises the limiter and the test needs a faster subject",
        )

    def test_et_unchanged_by_annotation(self):
        # Quarter-mile trap (~250 km/h) sits below 299, so the annotation
        # must not move the ET by a single bit.
        cfg = _limited_config()
        stripped = copy.deepcopy(cfg)
        stripped.drivetrain.speed_limiter_kmh = None
        r_lim = MotoQuantEngine(cfg).run()
        r_unl = MotoQuantEngine(stripped).run()
        self.assertLess(r_lim.speed_quarter * 3.6, 299.0)
        self.assertEqual(repr(r_lim.time_quarter), repr(r_unl.time_quarter))
        self.assertTrue(np.array_equal(r_lim.v, r_unl.v))


class TestRoundTrips(unittest.TestCase):
    """The field must survive BOTH persistence paths (the category_tag trap)."""

    def test_db_bridge_round_trip(self):
        cfg = _limited_config()
        restored = db_row_to_config(config_to_db_row(cfg), environment=cfg.environment)
        self.assertEqual(restored.drivetrain.speed_limiter_kmh, 299.0)

    def test_db_bridge_round_trip_none(self):
        cfg = _unannotated_config()
        restored = db_row_to_config(config_to_db_row(cfg), environment=cfg.environment)
        self.assertIsNone(restored.drivetrain.speed_limiter_kmh)

    def test_config_io_round_trip(self):
        cfg = _limited_config()
        cfg_none = _unannotated_config()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "limited.json"
            save_config(cfg, path)
            self.assertEqual(load_config(path).drivetrain.speed_limiter_kmh, 299.0)
            path_none = Path(td) / "unlimited.json"
            save_config(cfg_none, path_none)
            self.assertIsNone(load_config(path_none).drivetrain.speed_limiter_kmh)


if __name__ == "__main__":
    unittest.main()
