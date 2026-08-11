"""Web-surrogate export + JS parity pins.

The in-browser quick sim (web/lib/surrogate.js) is only trustworthy if it is
*provably* the same computation as the server surrogate pipeline. These tests
pin that chain end-to-end:

  1. scripts/gen_surrogate_web.py exports per-bike features that are exactly
     _extract_nominal_features(db_row_to_config(row)) — the same path the API
     serves — and a model.json that reproduces NumpySurrogate bit-for-bit.
  2. The JS module (run via node against the real exported assets, through its
     real loader) matches the Python reference pipeline to <1e-9 s across the
     full catalog plus randomized slider perturbations.

If node is unavailable the JS-parity test skips; the Python-side export pins
still run everywhere (CI runners have node).

Run with:
    python -m pytest tests/test_surrogate_web_export.py -v
"""

from __future__ import annotations

import base64
import json
import random
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
DB_PATH = REPO / "motoquant.db"
NPZ_PATH = REPO / "artifacts" / "surrogate" / "surrogate_numpy.npz"

from motoquant.analysis.surrogate_data import (  # noqa: E402
    FEATURE_NAMES,
    _extract_nominal_features,
    config_to_feature_vector,
)
from motoquant.analysis.surrogate_numpy import NumpySurrogate  # noqa: E402
from motoquant.database.bridge import db_row_to_config  # noqa: E402

_gen_mod = None


def _gen():
    """Import scripts/gen_surrogate_web.py as a module (scripts/ isn't a package)."""
    global _gen_mod
    if _gen_mod is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "gen_surrogate_web", REPO / "scripts" / "gen_surrogate_web.py"
        )
        _gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_gen_mod)
    return _gen_mod


def _decode_f32(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype="<f4")


def _load_current_rows(limit: int | None = None):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    q = (
        "SELECT bc.*, bm.id AS model_id FROM bike_configs bc "
        "JOIN bike_models bm ON bm.id = bc.bike_model_id "
        "WHERE bc.is_current = 1 ORDER BY bm.id"
    )
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    conn.close()
    return rows


class TestModelExport(unittest.TestCase):
    """model.json must reproduce the shipped npz bit-for-bit."""

    @classmethod
    def setUpClass(cls):
        cls.model = _gen().export_model(NPZ_PATH)
        cls.npz = np.load(str(NPZ_PATH), allow_pickle=False)

    def test_feature_order_matches_canon(self):
        self.assertEqual(self.model["feature_names"], list(FEATURE_NAMES))

    def test_weight_buffers_bit_exact(self):
        for i in range(int(self.npz["n_layers"][0])):
            np.testing.assert_array_equal(
                _decode_f32(self.model["layers"][i]["W"]),
                self.npz[f"W{i}"].ravel(),
            )
            np.testing.assert_array_equal(
                _decode_f32(self.model["layers"][i]["b"]), self.npz[f"b{i}"]
            )

    def test_norms_and_envelope_bit_exact(self):
        for key in (
            "feat_mean",
            "feat_std",
            "tgt_mean",
            "tgt_std",
            "env_min",
            "env_max",
        ):
            np.testing.assert_array_equal(_decode_f32(self.model[key]), self.npz[key])

    def test_json_forward_pass_matches_numpy_surrogate(self):
        """A forward pass built ONLY from model.json must equal NumpySurrogate.

        This is the guarantee that the JSON is a complete, sufficient
        description of the model — nothing implicit is left in the npz.
        """
        surr = NumpySurrogate.load(NPZ_PATH)
        W = [
            _decode_f32(layer["W"]).astype(np.float64).reshape(layer["shape"])
            for layer in self.model["layers"]
        ]
        b = [
            _decode_f32(layer["b"]).astype(np.float64) for layer in self.model["layers"]
        ]
        fm = _decode_f32(self.model["feat_mean"]).astype(np.float64)
        fs = _decode_f32(self.model["feat_std"]).astype(np.float64)
        tm = _decode_f32(self.model["tgt_mean"]).astype(np.float64)
        ts = _decode_f32(self.model["tgt_std"]).astype(np.float64)

        rows = _load_current_rows(limit=50)
        X = np.stack(
            [config_to_feature_vector(db_row_to_config(r)) for r in rows]
        ).astype(np.float64)
        a = (X - fm) / fs
        for Wi, bi in zip(W[:-1], b[:-1]):
            a = np.maximum(0.0, a @ Wi + bi)
        out = (a @ W[-1] + b[-1]) * ts + tm
        et_ref, trap_ref = surr.predict(X)
        np.testing.assert_allclose(out[:, 0], et_ref, rtol=0, atol=1e-12)
        np.testing.assert_allclose(out[:, 1], trap_ref, rtol=0, atol=1e-12)


class TestBikesExport(unittest.TestCase):
    """bikes.json features must equal the API's own config path exactly."""

    @classmethod
    def setUpClass(cls):
        cls.data = _gen().export_bikes(DB_PATH)

    def test_full_catalog_exported(self):
        rows = _load_current_rows()
        self.assertEqual(self.data["n_bikes"], len(rows))
        self.assertGreaterEqual(self.data["n_bikes"], 500)

    def test_features_match_extraction_exactly(self):
        rows = _load_current_rows()
        sampled = rows[::37] + rows[-1:]  # every 37th + last — ~16 spread bikes
        for row in sampled:
            cfg = db_row_to_config(row)
            ref = _extract_nominal_features(cfg)
            got = self.data["bikes"][str(row["model_id"])]
            for name, val in got["f"].items():
                self.assertEqual(
                    val, float(ref[name]), f"bike {row['model_id']} feature {name}"
                )
            self.assertEqual(got["dry_mass_kg"], float(cfg.chassis.dry_mass_kg))

    def test_venue_altitudes_exported(self):
        self.assertGreaterEqual(len(self.data["venues"]), 15)
        for alt in self.data["venues"].values():
            self.assertIsInstance(alt, float)

    def test_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            _gen().main(["--out", f"{td}/a"])
            _gen().main(["--out", f"{td}/b"])
            for name in ("model.json", "bikes.json"):
                self.assertEqual(
                    Path(td, "a", name).read_bytes(),
                    Path(td, "b", name).read_bytes(),
                    f"{name} not byte-deterministic",
                )


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestJsParity(unittest.TestCase):
    """The REAL web/lib/surrogate.js must match the server surrogate pipeline.

    The reference values are computed through the genuine server path —
    db_row_to_config + the _build_config override semantics + fround +
    NumpySurrogate — so a pass here means client and server surrogate answers
    are numerically interchangeable.
    """

    TOL_S = 1e-9

    def _server_reference(self, cfg, rider, boost, mass_delta, altitude):
        """Mirror api._build_config's override arithmetic on a config's features."""
        feats = _extract_nominal_features(cfg)
        scale = 1.0 + boost / 100.0
        base = dict(feats)
        base["peak_power_hp"] = feats["peak_power_hp"] * scale
        base["peak_torque_nm"] = feats["peak_torque_nm"] * scale
        base["total_mass_kg"] = float(cfg.chassis.dry_mass_kg) + mass_delta + rider
        if altitude is not None:
            base["altitude_m"] = altitude
        from motoquant.analysis.surrogate_data import _compute_derived_features

        base.update(_compute_derived_features(base))
        vec = np.array([base[k] for k in FEATURE_NAMES], dtype=np.float32)
        et, trap = self._surr.predict(vec.reshape(1, -1))
        env_min, env_max = self._surr.envelope
        in_env = bool(np.all(vec >= env_min) and np.all(vec <= env_max))
        return float(et[0]), float(trap[0]) * 3.6, in_env

    def test_full_catalog_and_sliders_parity(self):
        with tempfile.TemporaryDirectory() as td:
            assets = Path(td) / "surrogate"
            _gen().main(["--out", str(assets)])
            self._surr = NumpySurrogate.load(NPZ_PATH)

            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            venues = dict(
                conn.execute(
                    "SELECT id, altitude_m FROM venues WHERE altitude_m IS NOT NULL"
                ).fetchall()
            )
            conn.close()

            rng = random.Random(20260811)
            rows = _load_current_rows()
            cases = []
            for i, row in enumerate(rows):
                cfg = db_row_to_config(row)
                if i % 4 == 0:  # every 4th bike also gets a randomized slider case
                    rider = rng.uniform(50, 130)
                    boost = rng.uniform(-20, 60)
                    mdelta = rng.uniform(-30, 30)
                    vid = rng.choice(list(venues)) if rng.random() < 0.5 else None
                    combos = [(75.0, 0.0, 0.0, None), (rider, boost, mdelta, vid)]
                else:
                    combos = [(75.0, 0.0, 0.0, None)]
                for rider, boost, mdelta, vid in combos:
                    alt = float(venues[vid]) if vid is not None else None
                    et, trap, in_env = self._server_reference(
                        cfg, rider, boost, mdelta, alt
                    )
                    case = {
                        "bike_id": row["model_id"],
                        "rider_mass_kg": rider,
                        "power_boost_pct": boost,
                        "mass_delta_kg": mdelta,
                        "venue_id": vid,
                    }
                    if in_env:
                        case["expected_et_s"] = et
                        case["expected_trap_kmh"] = trap
                    else:
                        case["expect_refusal"] = "envelope"
                    cases.append(case)

            fixture = Path(td) / "fixture.json"
            fixture.write_text(
                json.dumps({"tolerance_s": self.TOL_S, "cases": cases}), "utf-8"
            )

            proc = subprocess.run(
                [
                    "node",
                    str(REPO / "web" / "scripts" / "surrogate-parity.mjs"),
                    str(fixture),
                    "--assets",
                    str(assets),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"JS parity failed:\n{proc.stdout}\n{proc.stderr}",
            )
            # The harness prints its pass line — keep it visible in -v runs.
            print(proc.stdout.strip())


if __name__ == "__main__":
    unittest.main()
