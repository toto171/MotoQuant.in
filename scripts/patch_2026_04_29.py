#!/usr/bin/env python3
"""
One-shot patch (April 29, 2026) — applies five changes to motoquant.db:

0. Forward-migrate schema (idempotent ALTER TABLE for older DBs).
1. Correct Ninja H2 hp 310 -> 228 (street-legal H2 ram-air number).
2. Insert Ninja H2R (310 hp, track-only) as a new bike.
3. Insert 6 missing OEM flagships (Norton V4SV, BMW HP4 Race, Aprilia
   RSV4 1100 Factory FW1A, MV F4 RC, Honda RC213V-S, Z H2 SX SE+).
4. Create bike_archetypes table (if missing) + seed 5 modded archetypes
   (TTS Stage 2, Velocity 5-sec, Bonneville H2 Carbon, Schnitz Nitrous,
   Ron Ayers RAW).

Run idempotently — every step detects already-patched state and skips.

Usage:
    MOTOQUANT_DB=motoquant.db python scripts/patch_2026_04_29.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.database.connection import MotoQuantDB
from motoquant.database.seed_archetypes import seed_archetypes
from motoquant.scraper.importer import import_batch, spec_to_bike_config
from motoquant.scraper.known_bikes import KAWASAKI_H2_2015, KAWASAKI_H2R_2015
from motoquant.scraper.known_bikes_extended import EXTENDED_BIKES


ARCHETYPES_DDL = """
CREATE TABLE IF NOT EXISTS bike_archetypes (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    name                     TEXT    NOT NULL,
    base_bike_model_id       INTEGER NOT NULL REFERENCES bike_models(id) ON DELETE CASCADE,
    description              TEXT,
    power_multiplier         REAL    NOT NULL DEFAULT 1.0,
    peak_power_hp_override   REAL,
    peak_torque_nm_override  REAL,
    mass_delta_kg            REAL    NOT NULL DEFAULT 0.0,
    cd_delta                 REAL    NOT NULL DEFAULT 0.0,
    frontal_area_delta_m2    REAL    NOT NULL DEFAULT 0.0,
    sprocket_front_override  INTEGER,
    sprocket_rear_override   INTEGER,
    chain_pitch_override     TEXT,
    tire_mu_override         REAL,
    notes                    TEXT,
    source_url               TEXT,
    estimated_build_inr      REAL,
    is_homologation          INTEGER NOT NULL DEFAULT 0,
    created_at               TEXT    DEFAULT (datetime('now','utc')),
    UNIQUE(name, base_bike_model_id)
);
CREATE INDEX IF NOT EXISTS idx_archetype_base ON bike_archetypes(base_bike_model_id);
CREATE INDEX IF NOT EXISTS idx_archetype_name ON bike_archetypes(name);
"""


def _ensure_column(conn, table, col, col_def):
    """ALTER TABLE ADD COLUMN if not present. Idempotent."""
    rows = conn.execute("PRAGMA table_info(" + table + ")").fetchall()
    existing = {r[1] for r in rows}
    if col in existing:
        return
    print("  + adding " + table + "." + col)
    conn.execute("ALTER TABLE " + table + " ADD COLUMN " + col + " " + col_def)


def _migrate_schema(conn):
    """Forward-migrate older DB schemas to match motoquant.database.schema."""
    print("\n[0/4] Forward-migrating schema (idempotent)...")
    _ensure_column(conn, "bike_models", "data_source", "TEXT DEFAULT 'estimated'")
    _ensure_column(
        conn, "bike_models", "updated_at",
        "TEXT DEFAULT (datetime('now','utc'))",
    )
    conn.commit()
    print("  schema migration complete")


def _refresh_config_blob(conn, bike_id, spec):
    try:
        from motoquant.database.bridge import config_to_db_row
        cfg = spec_to_bike_config(spec)
        row = config_to_db_row(cfg)
        sections = [
            "engine_params", "drivetrain_params", "clutch_params",
            "chain_params", "tires_params", "aero_params", "chassis_params",
            "rider_params", "staging_params", "environment_params",
            "wheelie_params", "parasitic_params",
        ]
        update_kw = {k: row[k] for k in sections if k in row}
        if update_kw:
            sets = ", ".join(k + "=?" for k in update_kw)
            conn.execute(
                "UPDATE bike_configs SET " + sets + " WHERE bike_model_id=?",
                list(update_kw.values()) + [bike_id],
            )
            conn.commit()
            print("    bike_configs blob refreshed (%d sections)" % len(update_kw))
    except Exception as e:
        print("    WARN: bike_configs refresh failed: %s: %s" % (type(e).__name__, e))


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print("Patching " + db_path)

    db = MotoQuantDB(db_path)
    db.connect()
    conn = db._conn

    # 0. Forward schema migrations
    _migrate_schema(conn)

    # 1. Correct existing H2 row
    print("\n[1/4] Correcting Ninja H2 power figure...")
    h2_row = conn.execute(
        "SELECT bm.id, bm.peak_power_hp FROM bike_models bm "
        "JOIN manufacturers m ON m.id=bm.manufacturer_id "
        "WHERE m.name='Kawasaki' AND bm.model_name LIKE '%Ninja H2%' "
        "AND bm.model_name NOT LIKE '%Mach%' "
        "AND bm.model_name NOT LIKE '%SX%' "
        "AND bm.model_name NOT LIKE '%Z H2%' "
        "AND bm.model_name NOT LIKE '%H2R%' "
        "ORDER BY bm.id LIMIT 1"
    ).fetchone()
    if h2_row is None:
        print("  H2 row not found - skipping H2 correction")
    elif h2_row["peak_power_hp"] == 228.0:
        print("  H2 (id=%d) already at 228 hp - skipping" % h2_row["id"])
    else:
        print("  H2 (id=%d): %s -> 228.0 hp" % (h2_row["id"], h2_row["peak_power_hp"]))
        conn.execute(
            "UPDATE bike_models "
            "SET peak_power_hp=228.0, peak_power_rpm=11000, "
            "    peak_torque_nm=141.7, peak_torque_rpm=10500 "
            "WHERE id=?",
            (h2_row["id"],),
        )
        conn.commit()
        _refresh_config_blob(conn, h2_row["id"], KAWASAKI_H2_2015)

    # 2. Insert H2R if absent
    print("\n[2/4] Inserting Ninja H2R...")
    existing_h2r = conn.execute(
        "SELECT bm.id FROM bike_models bm "
        "JOIN manufacturers m ON m.id=bm.manufacturer_id "
        "WHERE m.name='Kawasaki' AND bm.model_name LIKE '%H2R%'"
    ).fetchone()
    if existing_h2r is not None:
        print("  H2R already present (id=%d) - skipping" % existing_h2r["id"])
    else:
        result = import_batch(db, [KAWASAKI_H2R_2015])
        print("  H2R inserted: result=%s" % result)

    # 3. Insert 6 extended OEM bikes
    print("\n[3/4] Inserting %d extended-flagship OEM bikes..." % len(EXTENDED_BIKES))
    before = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    result = import_batch(db, EXTENDED_BIKES)
    after = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    print("  before=%d after=%d delta=%d (%s)" % (before, after, after - before, result))

    # 4. Create + seed bike_archetypes table
    print("\n[4/4] Creating bike_archetypes table + seeding 5 modded builds...")
    for stmt in ARCHETYPES_DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            conn.execute(s)
    conn.commit()
    print("  bike_archetypes table ensured")

    n_inserted = seed_archetypes(db)
    total_arc = conn.execute("SELECT COUNT(*) FROM bike_archetypes").fetchone()[0]
    print("  archetypes inserted=%d (total now %d)" % (n_inserted, total_arc))

    # Final summary
    final_count = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    arc_count = conn.execute("SELECT COUNT(*) FROM bike_archetypes").fetchone()[0]
    print("\n" + "=" * 60)
    print("FINAL STATE: bike_models=%d  bike_archetypes=%d" % (final_count, arc_count))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
