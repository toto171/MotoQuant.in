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


def _year_overlap(a_from, a_to, b_from, b_to):
    """Overlap width of two [from, to] year ranges (0 if disjoint)."""
    a_to = a_to or a_from
    b_to = b_to or b_from
    if a_from is None or b_from is None:
        return 0
    return max(0, min(a_to, b_to) - max(a_from, b_from) + 1)


def _pick_generation(candidates, row):
    """From specs sharing a (mfr, stripped-model) key, pick the one whose
    year range best matches this DB row's generation. Prevents collapsing
    e.g. GSX-R 1000 K1/K3/K5/K7/K9 to a single spec (the pre-2026-07 bug)."""
    if len(candidates) == 1:
        return candidates[0]
    ryf = row.get("year_from")
    ryt = row.get("year_to")
    # Best year-range overlap wins; ties break toward the closest year_from.
    scored = sorted(
        candidates,
        key=lambda s: (
            _year_overlap(s.year_from, s.year_to, ryf, ryt),
            -abs((s.year_from or 0) - (ryf or 0)),
        ),
        reverse=True,
    )
    return scored[0]


def match_spec_to_row(row, specs_by_key):
    mfr = (row["manufacturer"] or "").strip().lower()
    model = strip_year(row["model_name"]).lower()
    key = (mfr, model)
    if key in specs_by_key:
        return _pick_generation(specs_by_key[key], row)
    mfr_first = mfr.split()[0] if mfr else ""
    for (km, kmod), specs in specs_by_key.items():
        if kmod == model and (km == mfr or km.startswith(mfr_first)):
            return _pick_generation(specs, row)
    return None


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    db = MotoQuantDB(db_path=db_path)
    db.connect()

    # Key on (manufacturer, YEAR-STRIPPED model) -> list of specs. Both the
    # DB row and the spec have their trailing "(YYYY-YYYY)" stripped so the
    # keys align symmetrically (the old code stripped only the row, so a spec
    # whose own name embedded a year suffix bound to the wrong generation).
    # Multi-generation models keep ALL their specs in the list and
    # _pick_generation chooses by year-range overlap.
    specs_by_key = {}
    for s in ALL_KNOWN_BIKES:
        key = (s.manufacturer.strip().lower(), strip_year(s.model_name).lower())
        specs_by_key.setdefault(key, []).append(s)

    rows = db.conn.execute(
        "SELECT bc.id AS config_id, bm.id AS model_id, "
        "m.name AS manufacturer, bm.model_name, bc.config_name, "
        "bm.year_from AS year_from, bm.year_to AS year_to "
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
                "staging_params=?, category_tag=?, "
                "updated_at=CURRENT_TIMESTAMP "
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
                    row_data.get("category_tag"),
                    row["config_id"],
                ),
            )
            # July 13, 2026: also sync the bike_models HEADLINE columns from
            # the spec. Spec-source corrections previously reached only the
            # bike_configs physics blobs — /api/bikes and the web bike pages
            # kept displaying the old figures (a bypass path: the headline
            # columns are otherwise written only at import time).
            db.conn.execute(
                "UPDATE bike_models SET "
                "displacement_cc=COALESCE(?, displacement_cc), "
                "peak_power_hp=COALESCE(?, peak_power_hp), "
                "peak_torque_nm=COALESCE(?, peak_torque_nm), "
                "dry_mass_kg=COALESCE(?, dry_mass_kg), "
                "wet_mass_kg=COALESCE(?, wet_mass_kg), "
                "updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (
                    getattr(spec, "displacement_cc", None),
                    getattr(spec, "peak_power_hp", None),
                    getattr(spec, "peak_torque_nm", None),
                    getattr(spec, "dry_mass_kg", None),
                    getattr(spec, "wet_mass_kg", None),
                    row["model_id"],
                ),
            )
            updated += 1
        except Exception as exc:
            errors += 1
            print(
                "  ERROR on %s %s: %s" % (row["manufacturer"], row["model_name"], exc),
                flush=True,
            )

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
