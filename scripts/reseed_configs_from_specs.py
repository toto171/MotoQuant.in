#!/usr/bin/env python3
"""
Refresh the bike_configs JSON blobs from current spec_to_bike_config output.

The DB was seeded before the April-20 Cluster 4 small-cc kaizen work
(displacement-scaled engine inertia, parasitic right-sizing, aero Cd per
category, tuned chain efficiency, per-category crr). The persisted
bike_configs JSON still holds those pre-kaizen values, so every call that
loads a config from DB (e.g. /api/simulate?bike_id=N) simulates 2-5 s
slower than the same bike built fresh via spec_to_bike_config.

Walks every is_current=1 bike_configs row, matches to ALL_KNOWN_BIKES by
(manufacturer, model_name-stripped-of-year-suffix), regenerates the
BikeConfig, UPDATEs the JSON blobs in place. Model IDs are preserved.

Usage:
    MOTOQUANT_DB=/path/to/motoquant.db python3 scripts/reseed_configs_from_specs.py
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant.database import MotoQuantDB
from motoquant.database.bridge import config_to_db_row
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


_YEAR_SUFFIX = re.compile(r"\s*\(\d{4}(?:-\d{4})?\)\s*$")


def strip_year(s):
    return _YEAR_SUFFIX.sub("", s or "").strip()


def match_spec_to_row(row, specs_by_key):
    mfr = (row["manufacturer"] or "").strip().lower()
    model = strip_year(row["model_name"]).lower()
    key = (mfr, model)
    if key in specs_by_key:
        return specs_by_key[key]
    mfr_first = mfr.split()[0] if mfr else ""
    for (km, kmod), spec in specs_by_key.items():
        if kmod == model and (km == mfr or km.startswith(mfr_first)):
            return spec
    return None


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    db = MotoQuantDB(db_path=db_path)
    db.connect()

    specs_by_key = {}
    for s in ALL_KNOWN_BIKES:
        key = (s.manufacturer.strip().lower(), s.model_name.strip().lower())
        specs_by_key[key] = s

    rows = db.conn.execute(
        "SELECT bc.id AS config_id, bm.id AS model_id, "
        "m.name AS manufacturer, bm.model_name, bc.config_name "
        "FROM bike_configs bc "
        "JOIN bike_models bm ON bc.bike_model_id = bm.id "
        "JOIN manufacturers m ON bm.manufacturer_id = m.id "
        "WHERE bc.is_current = 1"
    ).fetchall()
    rows = [dict(r) for r in rows]

    print("Scanning %d current bike_configs rows..." % len(rows), flush=True)

    updated = 0
    skipped_no_spec = 0
    errors = 0
    unmatched = []

    for row in rows:
        spec = match_spec_to_row(row, specs_by_key)
        if spec is None:
            skipped_no_spec += 1
            unmatched.append("%s %s" % (row["manufacturer"], row["model_name"]))
            continue

        try:
            cfg = spec_to_bike_config(spec)
            row_data = config_to_db_row(cfg)
            db.conn.execute(
                "UPDATE bike_configs SET "
                "chassis_params=?, engine_params=?, forced_induction_params=?, "
                "drivetrain_params=?, clutch_params=?, tire_params=?, "
                "aero_params=?, suspension_params=?, braking_params=?, "
                "wheelie_params=?, rider_params=?, parasitic_params=?, "
                "staging_params=?, updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (
                    row_data["chassis_params"],
                    row_data["engine_params"],
                    row_data["forced_induction_params"],
                    row_data["drivetrain_params"],
                    row_data["clutch_params"],
                    row_data["tire_params"],
                    row_data["aero_params"],
                    row_data["suspension_params"],
                    row_data["braking_params"],
                    row_data["wheelie_params"],
                    row_data["rider_params"],
                    row_data["parasitic_params"],
                    row_data["staging_params"],
                    row["config_id"],
                ),
            )
            updated += 1
        except Exception as exc:
            errors += 1
            print("  ERROR on %s %s: %s" % (row["manufacturer"], row["model_name"], exc), flush=True)

    db.conn.commit()

    print("", flush=True)
    print("Summary:", flush=True)
    print("  Updated:        %d" % updated, flush=True)
    print("  No spec match:  %d" % skipped_no_spec, flush=True)
    print("  Errors:         %d" % errors, flush=True)

    if unmatched:
        print("", flush=True)
        print("Unmatched models (kept stale):", flush=True)
        for u in unmatched[:30]:
            print("  " + u, flush=True)
        if len(unmatched) > 30:
            print("  ... and %d more" % (len(unmatched) - 30), flush=True)

    db.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
