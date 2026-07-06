#!/usr/bin/env python3
"""patch_2026_07_06_reference_configs.py — stamp category_tag on the 3
hand-curated reference bikes' DB rows.

Root cause (July 6, 2026 stress-test session): bike_configs rows for
bike_model_ids 1/2/3 (GSX-R 1000 K5, YZF-R1 4C8, Hayabusa Gen1) are
excluded from reseed_configs_from_specs.py by design, so the schema-v6
category_tag column was never stamped for them and stayed NULL. At
runtime physics.py then auto-derives a tag from displacement/power —
which lands the Hayabusa (1299cc, 173hp, sub-195hp so not litre_sport)
in the "other" catch-all cluster, whose over-clutch launch profile makes
/api/simulate?bike_id=3 ~0.36 s FASTER than the hand-curated
defaults.py reference model. K5/R1 derive into litre_sport_600_1000
whose launch knobs match litre_sport_195p, so their ETs were unaffected
(their documented DB-vs-defaults delta is the by-design Aamby-vs-sea-
level environment, see bridge.config_to_db_row docstring).

Fix: stamp category_tag='litre_sport_195p' — the tag the defaults.py
configs carry explicitly — on the is_current=1 rows of bikes 1/2/3.

Idempotent: re-running is a no-op once the tags are set.

Usage:
    MOTOQUANT_DB=motoquant.db python scripts/patch_2026_07_06_reference_configs.py
"""

import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

REFERENCE_TAG = "litre_sport_195p"
REFERENCE_BIKE_IDS = (1, 2, 3)


def apply(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    updated = 0
    already = 0
    for bid in REFERENCE_BIKE_IDS:
        row = conn.execute(
            "SELECT id, category_tag FROM bike_configs "
            "WHERE bike_model_id=? AND is_current=1",
            (bid,),
        ).fetchone()
        if row is None:
            print(f"  bike_model_id={bid}: no current config row — SKIPPED")
            continue
        if row["category_tag"] == REFERENCE_TAG:
            already += 1
            continue
        conn.execute(
            "UPDATE bike_configs SET category_tag=? WHERE id=?",
            (REFERENCE_TAG, row["id"]),
        )
        updated += 1
    conn.commit()
    conn.close()
    return {"updated": updated, "already_correct": already}


if __name__ == "__main__":
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    summary = apply(db_path)
    print(f"reference category_tag patch: {summary}")
