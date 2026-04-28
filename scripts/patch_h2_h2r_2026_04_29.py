#!/usr/bin/env python3
"""
One-shot patch: correct Ninja H2 hp + add Ninja H2R to motoquant.db.

The Apr 27 mega-session catalog (now in production) had Kawasaki Ninja H2
listed at 310 hp — that's the H2R's number. The street-legal H2 produces
228 hp with ram air. This script:

1. UPDATE bike_models SET peak_power_hp=228 WHERE name='Ninja H2 (...)'
2. UPDATE the H2's bike_configs JSON blob to match (so /api/simulate uses
   the correct power figure).
3. INSERT a new bike_models row for Ninja H2R (310 hp, track-only).
4. INSERT corresponding bike_configs for H2R via spec_to_bike_config.

Run idempotently: detects already-patched rows and skips.
Usage: MOTOQUANT_DB=motoquant.db python scripts/patch_h2_h2r_2026_04_29.py
"""

import os
import sys

# Project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.database.connection import MotoQuantDB
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import KAWASAKI_H2_2015, KAWASAKI_H2R_2015


def main() -> int:
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"Patching {db_path}")

    db = MotoQuantDB(db_path)
    db.connect()
    conn = db._conn

    # ── 1. Correct existing H2 row ────────────────────────────────────
    h2_row = conn.execute(
        """SELECT bm.id, bm.peak_power_hp FROM bike_models bm
           JOIN manufacturers m ON m.id=bm.manufacturer_id
           WHERE m.name='Kawasaki' AND bm.model_name LIKE '%Ninja H2%'
           AND bm.model_name NOT LIKE '%Mach%'
           AND bm.model_name NOT LIKE '%SX%'
           AND bm.model_name NOT LIKE '%Z H2%'
           AND bm.model_name NOT LIKE '%H2R%'
           ORDER BY bm.id LIMIT 1""",
    ).fetchone()
    if h2_row is None:
        print("  H2 row not found — skipping H2 correction")
    elif h2_row["peak_power_hp"] == 228.0:
        print(f"  H2 (id={h2_row['id']}) already at 228 hp — skipping")
    else:
        print(f"  H2 (id={h2_row['id']}): {h2_row['peak_power_hp']} -> 228.0 hp")
        conn.execute(
            """UPDATE bike_models
               SET peak_power_hp=228.0,
                   peak_power_rpm=11000,
                   peak_torque_nm=141.7,
                   peak_torque_rpm=10500,
                   updated_at=datetime('now','utc')
               WHERE id=?""",
            (h2_row["id"],),
        )
        # Commit the headline UPDATE eagerly so it survives even if the
        # config-blob refresh below errors.
        conn.commit()

        # Refresh the bike_configs JSON blobs so /api/simulate?bike_id=N picks
        # up the corrected power figure (otherwise headline says 228 but the
        # sim engine reads 310 from the JSON blob).
        try:
            from motoquant.database.bridge import config_to_db_row
            cfg = spec_to_bike_config(KAWASAKI_H2_2015)
            row = config_to_db_row(cfg)
            # config_to_db_row returns a dict where every JSON-section column
            # is already serialised. Filter to the cols that exist on bike_configs.
            sections = [
                "engine_params", "drivetrain_params", "clutch_params",
                "chain_params", "tires_params", "aero_params", "chassis_params",
                "rider_params", "staging_params", "environment_params",
                "wheelie_params", "parasitic_params",
            ]
            update_kw = {k: row[k] for k in sections if k in row}
            if update_kw:
                sets = ", ".join(f"{k}=?" for k in update_kw)
                conn.execute(
                    f"UPDATE bike_configs SET {sets} WHERE bike_model_id=?",
                    list(update_kw.values()) + [h2_row["id"]],
                )
                conn.commit()
                print(f"    H2 bike_configs blob refreshed ({len(update_kw)} sections)")
        except Exception as e:
            print(f"    WARN: bike_configs refresh failed: {type(e).__name__}: {e}")
            # Headline columns still got corrected, which is the visible win.

    # ── 2. Insert H2R if absent ───────────────────────────────────────
    existing_h2r = conn.execute(
        """SELECT bm.id FROM bike_models bm
           JOIN manufacturers m ON m.id=bm.manufacturer_id
           WHERE m.name='Kawasaki' AND bm.model_name LIKE '%H2R%'""",
    ).fetchone()
    if existing_h2r is not None:
        print(f"  H2R already present (id={existing_h2r['id']}) — skipping")
    else:
        # Use the standard import_batch single-row path
        from motoquant.scraper.importer import import_batch
        result = import_batch(db, [KAWASAKI_H2R_2015])
        n_added = result.get("added", 0)
        print(f"  H2R inserted: added={n_added}, errors={result.get('errors', 0)}")
        # Re-fetch to confirm
        h2r_id = conn.execute(
            """SELECT bm.id FROM bike_models bm
               JOIN manufacturers m ON m.id=bm.manufacturer_id
               WHERE m.name='Kawasaki' AND bm.model_name LIKE '%H2R%'""",
        ).fetchone()
        if h2r_id:
            print(f"    H2R now has bike_id={h2r_id['id']}")

    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    print(f"\nFinal bike_models count: {final_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
