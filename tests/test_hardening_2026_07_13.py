"""
Regression tests for the July-13-2026 hardening batch.

1. boost_type validation: an unrecognized boost_type string previously
   slipped through silently — ``torque_mult`` fell through to 1.0 (zero
   boost) while ``is_boosted`` still granted the ×0.97 density-altitude
   floor, so the config simmed almost-but-not-quite like NA with no
   warning (measured −0.025 s on the Hayabusa reference at its venue).
   The engine now rejects it at construction.

2. ``max_time_s`` request floor: the API accepted any ``gt=0`` value, but
   a max_time below the solver dt raised an unhandled ValueError deep in
   the engine (July-11 review finding). The Field floor (``ge=0.1``) turns
   that into a clean 422 at validation.

Both tests drive production paths per docs/INVARIANTS.md I8.
"""

import os
import sys
import tempfile
import unittest

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1

# ---------------------------------------------------------------------------
# Isolated DB -- TestMaxTimeRequestFloor POSTs to /api/simulate/top-speed and
# /api/simulate/distance through the real app. connect() falls back to the
# repo's tracked motoquant.db when MOTOQUANT_DB is unset, so any route-level
# writer (the retired sim-quota meter once wrote three ``sim_usage`` rows into
# the SHIPPED catalog this way) would leak residue into it. Redirecting keeps
# this module hermetic regardless of what the routes write. Same pattern as
# test_jobs_api.py / test_api.py.
# ---------------------------------------------------------------------------
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_hardening_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run.

    Module-level overrides execute at COLLECTION time, so a sibling module
    imported later (test_api, test_jobs_api) leaves MOTOQUANT_DB pointing at
    ITS tmp DB by the time these tests actually run. Re-asserting here makes
    collection order irrelevant. The restore value is captured HERE (run time),
    not at import, so we never restore a sibling's since-deleted tmp path.
    """
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def tearDownModule():
    """Drop the tmp DB and restore MOTOQUANT_DB after all tests finish."""
    _api_mod = sys.modules.get("motoquant.api")
    if _api_mod is not None and getattr(_api_mod, "_db_conn", None) is not None:
        try:
            _api_mod._db_conn.close()
        except Exception:  # noqa: BLE001
            pass
        _api_mod._db_conn = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


class TestBoostTypeValidation(unittest.TestCase):
    def test_unknown_boost_type_raises_at_engine_construction(self):
        cfg = hayabusa_gen1()
        cfg.forced_induction.boost_type = "supercharger"  # plausible typo
        with self.assertRaises(ValueError) as ctx:
            MotoQuantEngine(cfg)
        self.assertIn("boost_type", str(ctx.exception))

    def test_all_valid_boost_types_construct(self):
        for bt in ("na", "turbo", "sc_roots", "sc_centrifugal", "n2o"):
            cfg = gsxr1000_k5()
            cfg.forced_induction.boost_type = bt
            MotoQuantEngine(cfg)  # must not raise


class TestMaxTimeRequestFloor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            from motoquant.api import app

            cls.client = TestClient(app)
        except Exception:  # noqa: BLE001
            cls.client = None

    def _post(self, url, body):
        if self.client is None:
            self.skipTest("fastapi not installed")
        return self.client.post(url, json=body)

    def test_topspeed_sub_dt_max_time_is_422(self):
        r = self._post(
            "/api/simulate/top-speed",
            {"bike_preset": "gsxr1000_k5", "max_time_s": 0.0005},
        )
        self.assertEqual(r.status_code, 422)

    def test_distance_sub_dt_max_time_is_422(self):
        r = self._post(
            "/api/simulate/distance",
            {
                "bike_preset": "gsxr1000_k5",
                "distance_m": 1000.0,
                "max_time_s": 0.0005,
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_normal_max_time_still_accepted(self):
        r = self._post(
            "/api/simulate/top-speed",
            {"bike_preset": "gsxr1000_k5", "max_time_s": 60.0},
        )
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
