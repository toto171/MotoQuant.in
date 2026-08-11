#!/usr/bin/env python3
"""Export the shipped numpy surrogate + per-bike features for in-browser quick sims.

Writes two static assets consumed by ``web/lib/surrogate.js``:

  web/public/surrogate/model.json   — the ReLU MLP (weights/norms/envelope) with
                                      every float32 buffer base64-encoded raw
                                      (little-endian), so the browser decodes
                                      bit-exact Float32Arrays instead of parsing
                                      lossy decimal strings.
  web/public/surrogate/bikes.json   — per current bike: the 14 base + 5 extra
                                      surrogate features as FULL float64 (straight
                                      from _extract_nominal_features on the same
                                      db_row_to_config path the API serves), plus
                                      dry_mass_kg so the client can recompose
                                      total mass from its rider/mass sliders.
                                      Also the venue id → altitude_m map.

Why float64 base features instead of the float32 stock vector: the server
inference pipeline is "compute features in float64 → cast the assembled vector
to float32 → run the MLP in float64" (config_to_feature_vector + NumpySurrogate).
Exporting float64 bases lets the JS run the *identical* pipeline — apply slider
transforms in float64, Math.fround each assembled feature, forward in float64 —
so client and server predictions agree to matmul-association noise (~1e-12 s),
proven by tests/test_surrogate_web_export.py and web/scripts/surrogate-parity.mjs.

REGEN CONTRACT: a surrogate is a cache of the physics, and these files are a
cache of the surrogate — regenerate BOTH whenever the surrogate artifact or the
DB configs change, in the same session (see artifacts/surrogate/README.md).

Usage:
    python scripts/gen_surrogate_web.py [--db motoquant.db] [--out web/public/surrogate]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from motoquant.analysis.surrogate_data import (  # noqa: E402
    FEATURE_NAMES,
    _extract_nominal_features,
)
from motoquant.database.bridge import db_row_to_config  # noqa: E402

NPZ_PATH = REPO / "artifacts" / "surrogate" / "surrogate_numpy.npz"

#: The features surrogate.js recomputes client-side from slider state. Everything
#: else in the 26-vector is served verbatim from this export. Keep in sync with
#: web/lib/surrogate.js SLIDER_FEATURES.
CLIENT_RECOMPUTED = ("peak_power_hp", "peak_torque_nm", "total_mass_kg", "altitude_m")


def _b64(arr: np.ndarray) -> str:
    """Base64 of the raw little-endian buffer — bit-exact transport to JS."""
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<f4").tobytes()).decode(
        "ascii"
    )


def export_model(npz_path: Path) -> dict:
    d = np.load(str(npz_path), allow_pickle=False)
    n = int(d["n_layers"][0])
    model = {
        "format": "motoquant-surrogate-web/1",
        "n_layers": n,
        "feature_names": [str(s) for s in d["feature_names"]],
        # All buffers are float32 little-endian, base64 of the raw bytes.
        "feat_mean": _b64(d["feat_mean"]),
        "feat_std": _b64(d["feat_std"]),
        "tgt_mean": _b64(d["tgt_mean"]),
        "tgt_std": _b64(d["tgt_std"]),
        "env_min": _b64(d["env_min"]),
        "env_max": _b64(d["env_max"]),
        "layers": [
            {
                "shape": list(d[f"W{i}"].shape),
                "W": _b64(d[f"W{i}"]),
                "b": _b64(d[f"b{i}"]),
            }
            for i in range(n)
        ],
        "meta_json": str(d["meta_json"][0]) if "meta_json" in d.files else None,
        # Fingerprint ties the web export to the exact npz it came from.
        "npz_sha256": hashlib.sha256(npz_path.read_bytes()).hexdigest(),
    }
    if model["feature_names"] != list(FEATURE_NAMES):
        raise SystemExit(
            "FATAL: npz feature order differs from surrogate_data.FEATURE_NAMES — "
            "the JS slider transforms index by position and would silently misapply."
        )
    return model


def export_bikes(db_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    bikes: dict[str, dict] = {}
    skipped: list[int] = []
    rows = conn.execute(
        """SELECT bc.*, bm.id AS model_id
           FROM bike_configs bc
           JOIN bike_models bm ON bm.id = bc.bike_model_id
           WHERE bc.is_current = 1
           ORDER BY bm.id"""
    ).fetchall()
    for row in rows:
        rd = dict(row)
        mid = int(rd["model_id"])
        try:
            cfg = db_row_to_config(rd)
            feats = _extract_nominal_features(cfg)
        except Exception:
            skipped.append(mid)
            continue
        bikes[str(mid)] = {
            # base + extras as float64; derived features are recomputed
            # client-side exactly like _compute_derived_features does.
            "f": {
                k: float(feats[k])
                for k in FEATURE_NAMES
                if k in feats
                and k
                not in (
                    "power_to_weight_hp_kg",
                    "effective_1st_ratio",
                    "effective_top_ratio",
                    "gear_ratio_2nd",
                    "gear_ratio_3rd",
                    "gear_ratio_4th",
                    "gear_ratio_5th",
                )
            },
            "dry_mass_kg": float(cfg.chassis.dry_mass_kg),
        }
    venues = {
        str(r["id"]): float(r["altitude_m"])
        for r in conn.execute(
            "SELECT id, altitude_m FROM venues WHERE altitude_m IS NOT NULL"
        )
    }
    conn.close()
    if skipped:
        print(f"[gen-surrogate-web] WARNING: skipped unparseable configs: {skipped}")
    return {"bikes": bikes, "venues": venues, "n_bikes": len(bikes)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=str(REPO / "motoquant.db"))
    ap.add_argument("--out", default=str(REPO / "web" / "public" / "surrogate"))
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    model = export_model(NPZ_PATH)
    bikes = export_bikes(Path(args.db))
    # Stamp bikes.json with the model fingerprint so a mismatched pair
    # (regenerated one, forgot the other) is detectable client- and CI-side.
    bikes["npz_sha256"] = model["npz_sha256"]

    (out / "model.json").write_text(json.dumps(model, sort_keys=True), "utf-8")
    (out / "bikes.json").write_text(json.dumps(bikes, sort_keys=True), "utf-8")
    for name in ("model.json", "bikes.json"):
        p = out / name
        print(f"[gen-surrogate-web] wrote {p} ({p.stat().st_size / 1024:.0f} KB)")
    print(
        f"[gen-surrogate-web] {bikes['n_bikes']} bikes, {len(bikes['venues'])} venues"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
