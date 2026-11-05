#!/usr/bin/env python3
"""patch_2026_11_05_reference_rows.py — refresh the 3 reference bikes' DB rows.

bike_configs rows for bike_model_ids 1/2/3 (GSX-R 1000 K5, YZF-R1 4C8,
Hayabusa Gen1) are hand-curated from ``motoquant/defaults.py`` and excluded
from ``reseed_configs_from_specs.py``. The 2026-10/11 accuracy epoch changed
those factories (shaft efficiency 0.85 -> 0.93, rated-power cap on the
synthetic curves, dead staging/aero fields removed, the frozen
``reference_litre_195p`` tag), so the stored blobs lagged them and every
``db seed`` minted a new config version for each reference bike
(tests/test_fixwave_data_seed.py::test_cli_db_seed_leaves_curated_rows_untouched).

Fix: write ``config_to_db_row(factory())`` — exactly what ``db seed`` stores —
into the 13 parameter blobs and the category tag of each current row, then
re-derive dyno_curves / headline columns via ``patch_2026_10_24_config_sync``.
The environment is not a parameter column, so the rows keep their stored
conditions.

Idempotent: a second run reports 0 changes.

Chain position: after ``patch_2026_10_24_config_sync.py`` (it re-runs it).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.database.bridge import config_to_db_row  # noqa: E402
from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402
from scripts.patch_2026_10_24_config_sync import apply as sync_derived  # noqa: E402

REFERENCE_FACTORIES = {1: gsxr1000_k5, 2: yzfr1_4c8, 3: hayabusa_gen1}
PARAM_COLS = (
    "chassis_params",
    "engine_params",
    "forced_induction_params",
    "drivetrain_params",
    "clutch_params",
    "tire_params",
    "aero_params",
    "suspension_params",
    "braking_params",
    "wheelie_params",
    "rider_params",
    "parasitic_params",
    "staging_params",
)


def apply(db_path: str) -> dict:
    db = MotoQuantDB(db_path)
    conn = db.connect()
    updated = 0
    for model_id, factory in REFERENCE_FACTORIES.items():
        row = conn.execute(
            "SELECT * FROM bike_configs WHERE bike_model_id = ? AND is_current = 1",
            (model_id,),
        ).fetchone()
        if row is None:
            print(f"  bike_model_id={model_id}: no current config row — SKIPPED")
            continue
        cfg = factory()
        target = config_to_db_row(cfg)
        want = {c: target[c] for c in PARAM_COLS}
        want["category_tag"] = cfg.category_tag
        if all(row[k] == v for k, v in want.items()):
            continue
        sets = ", ".join(f"{k} = ?" for k in want)
        conn.execute(
            f"UPDATE bike_configs SET {sets} WHERE id = ?",
            (*want.values(), row["id"]),
        )
        updated += 1
    conn.commit()
    db.close()
    sync = sync_derived(db_path)
    return {"reference_rows_updated": updated, "derived_sync": sync}


if __name__ == "__main__":
    path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"reference rows refresh on {path}:")
    print(f"  {apply(path)}")
