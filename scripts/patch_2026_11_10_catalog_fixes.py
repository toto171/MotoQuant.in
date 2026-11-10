#!/usr/bin/env python3
"""patch_2026_11_10_catalog_fixes.py -- ET-neutral catalog data fixes.

Four independent steps, each idempotent (a second run reports 0 changes), none
of which touches a physics blob (bike_configs) -- no quarter-mile ET or trap
speed can move.

Chain position: after ``patch_2026_11_05_reference_rows.py`` and before
``patch_2026_11_10_epoch.py`` (which runs last). Step 1 writes exactly what
the spec-aware ``patch_2026_10_24_config_sync.py`` writes (both go through
``bridge.extract_headline_specs(config, spec=...)`` rules), so on a database
the reseed / config sync has already visited it changes nothing and only
lists the bikes whose bore x stroke contradicts their displacement; it still
repairs a database that was never synced.

1. HEADLINE SPECS.  The bike_models headline columns served by /api/bikes/{id}
   were written from the *defaulted* BikeConfig, so a bike whose spec carried no
   seat height / bore / stroke / compression ratio / wheelbase displayed the
   reference GSX-R1000's figure.  Each current bike is matched to its spec (the
   same matcher scripts/reseed_configs_from_specs.py uses) and the five columns
   are set to the spec's value, or NULL when the spec has none.  Bore and stroke
   are also set NULL when together they contradict the stated displacement by
   more than 3 % (the spec itself carries the wrong figure; no correction is
   invented -- the affected bikes are listed for sourced correction).
2. TIRE FITMENTS.  A fitment whose tire model is a front-position tire sitting
   in a rear slot (or vice versa) is re-linked to the same family's correct-
   position tire when the fitment note names that size and the bike does not
   already carry it; otherwise it is deleted.
3. GENERATED PLACEHOLDER PARTS.  Suspension parts "<brand> <type> V4..V12"
   (K-Tech Damper V4 ... FGRT Cartridge V12) were stamped out by a loop in
   seed.py with synthetic names, round prices and no modifier; the loop is
   removed from the seed and the rows deleted here (with their price history).
   The same applies to the other template-stamped rows listed in
   ``SYNTHETIC_PARTS`` (air filters, brakes, bodywork, fuel systems, five
   quickshifters, three batteries): real brand names on invented products.
4. UNBRANDED WHEELIE BARS.  Three fabricated wheelie bars carried brand names
   ('Precision', 'Schnitzer', 'Voodoo') that match no maker of such a product;
   they are relabelled brand 'Generic' (``GENERIC_RELABEL``), as the seed now
   writes them.  The part itself -- a plain 8/10/12-inch bar -- is kept.

Usage:
    MOTOQUANT_DB=<db> python scripts/patch_2026_11_10_catalog_fixes.py [--dry-run]
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from motoquant.database.bridge import (  # noqa: E402
    SPEC_ONLY_HEADLINE_FIELDS,
    bore_stroke_matches_displacement,
)
from motoquant.database.tire_repo import tire_position_fits_slot  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402

# (brand, part_number) of the loop-generated suspension placeholders.
PLACEHOLDER_PARTS = [
    ("K-Tech", "SUSP-K-T-4"),
    ("Öhlins", "SUSP-ÖHL-5"),
    ("Hyperpro", "SUSP-HYP-6"),
    ("Showa", "SUSP-SHO-7"),
    ("Sachs", "SUSP-SAC-8"),
    ("WP", "SUSP-WP-9"),
    ("Fox", "SUSP-FOX-10"),
    ("Fox", "SUSP-FOX-11"),
    ("FGRT", "SUSP-FGR-12"),
]

# (brand, part_number) of the remaining template-stamped parts: real brand names
# attached to invented products (``f"{brand} ... V{i}"`` / ``AF-PRO-{i}`` series
# with arithmetic prices) from loops in seed.py. Removed from the seed and here.
SYNTHETIC_PARTS = [
    # air filters: "Performance Air Filter V2..V6", "Performance Filter Pro 6..15"
    ("K&N", "AF-PERF-V2"),
    ("BMC", "AF-PERF-V3"),
    ("DNA", "AF-PERF-V4"),
    ("Sprint", "AF-PERF-V5"),
    ("HiFlow", "AF-PERF-V6"),
    ("HiFlow", "AF-PRO-6"),
    ("Pipercross", "AF-PRO-7"),
    ("Green", "AF-PRO-8"),
    ("Simota", "AF-PRO-9"),
    ("AEM", "AF-PRO-10"),
    ("HiFlow", "AF-PRO-11"),
    ("Pipercross", "AF-PRO-12"),
    ("Green", "AF-PRO-13"),
    ("Simota", "AF-PRO-14"),
    ("AEM", "AF-PRO-15"),
    # brakes: "<brand> <component> V4..V10"
    ("Brembo", "BRK-BRE-4"),
    ("Brembo", "BRK-BRE-5"),
    ("Brembo", "BRK-BRE-6"),
    ("EBC", "BRK-EBC-7"),
    ("Galfer", "BRK-GAL-8"),
    ("SBS", "BRK-SBS-9"),
    ("Endless", "BRK-END-10"),
    # bodywork: "<brand> <material> Fairing V3..V6"
    ("Catalyst", "BW-CAT-3"),
    ("Armour", "BW-ARM-4"),
    ("Attack", "BW-ATT-5"),
    ("Hotbodies", "BW-HOT-6"),
    # fuel systems: "Advanced Fuel System 5..8"
    ("Holley", "FS-ADV-5"),
    ("Carburetors", "FS-ADV-6"),
    ("Quantum", "FS-ADV-7"),
    ("Fuel Tech", "FS-ADV-8"),
    # quickshifters: invented SKUs (QS-<brand>-n); QS-HM-4 / QS-BON-10 kept
    ("Translogic", "QS-TRA-5"),
    ("Dynojet", "QS-DYN-6"),  # duplicate of the real DJ-PCQS row
    ("GPR", "QS-GPR-7"),
    ("Helix", "QS-HEL-8"),
    ("Shift Assist", "QS-SHI-9"),
    # batteries: invented motorcycle SKUs; Motobatt MBTX20UHD kept
    ("Enersys", "BATT-ENE-6"),
    ("Yuasa", "BATT-YUA-7"),
    ("Interstate", "BATT-INT-8"),
]

# (old brand, part_number) -> brand 'Generic'. The brand names resolved to no
# maker of these products in reports/scrape_2026_07_10 (found=false).
GENERIC_RELABEL = [
    ("Precision", "WB-8IN"),
    ("Schnitzer", "WB-10IN"),
    ("Voodoo", "WB-12IN"),
]

_SIZE_IN_NOTE = re.compile(r"(\d{2,3})/(\d{2})")


def _spec_index():
    from reseed_configs_from_specs import strip_year

    idx: dict = {}
    for s in ALL_KNOWN_BIKES:
        key = (s.manufacturer.strip().lower(), strip_year(s.model_name).lower())
        idx.setdefault(key, []).append(s)
    return idx


def fix_headline_specs(conn, log) -> dict:
    from reseed_configs_from_specs import match_spec_to_row

    idx = _spec_index()
    rows = conn.execute(
        "SELECT bm.*, m.name AS manufacturer FROM bike_models bm "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id "
        "WHERE EXISTS (SELECT 1 FROM bike_configs bc "
        "              WHERE bc.bike_model_id = bm.id AND bc.is_current = 1)"
    ).fetchall()
    changed = nulled_default = nulled_inconsistent = 0
    inconsistent: list = []
    for row in rows:
        row = dict(row)
        spec = match_spec_to_row(row, idx)
        if spec is None:
            continue
        new = {k: (getattr(spec, k, None) or None) for k in SPEC_ONLY_HEADLINE_FIELDS}
        cyl = row.get("cylinder_count") or getattr(spec, "cylinders", None)
        if not bore_stroke_matches_displacement(
            new["bore_mm"], new["stroke_mm"], cyl, row.get("displacement_cc")
        ):
            new["bore_mm"] = new["stroke_mm"] = None
            inconsistent.append(
                f"{row['id']} {row['manufacturer']} {row['model_name']} "
                f"(spec bore {spec.bore_mm} x stroke {spec.stroke_mm} x {cyl} cyl "
                f"vs {row.get('displacement_cc')} cc)"
            )
        diff = {
            k: v
            for k, v in new.items()
            if (row.get(k) is None) != (v is None)
            or (v is not None and abs(row[k] - v) > 1e-9)
        }
        if not diff:
            continue
        for k, v in diff.items():
            if v is None:
                nulled_default += 1
        changed += 1
        log(f"headline {row['id']} {row['model_name']}: {diff}")
        conn.execute(
            "UPDATE bike_models SET "
            + ", ".join(f"{k} = ?" for k in diff)
            + ", updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*diff.values(), row["id"]),
        )
    nulled_inconsistent = len(inconsistent)
    return {
        "bikes_changed": changed,
        "values_set_null": nulled_default,
        "bore_stroke_inconsistent_with_displacement": nulled_inconsistent,
        "_inconsistent": inconsistent,
    }


def fix_fitment_positions(conn, log) -> dict:
    relinked = deleted = 0
    bad = conn.execute(
        "SELECT f.id, f.bike_model_id, f.position, f.notes, f.tire_model_id, "
        "       t.position AS tpos, t.manufacturer_id, t.model_name "
        "FROM bike_tire_fitments f JOIN tire_models t ON t.id = f.tire_model_id"
    ).fetchall()
    for f in bad:
        if tire_position_fits_slot(f["tpos"], f["position"]):
            continue
        target = None
        m = _SIZE_IN_NOTE.search(f["notes"] or "")
        if m:
            width, aspect = int(m.group(1)), int(m.group(2))
            target = conn.execute(
                "SELECT id FROM tire_models WHERE manufacturer_id = ? AND model_name = ? "
                "AND position = ? AND width_mm = ? AND aspect_ratio = ?",
                (f["manufacturer_id"], f["model_name"], f["position"], width, aspect),
            ).fetchone()
        dup = (
            target is not None
            and conn.execute(
                "SELECT 1 FROM bike_tire_fitments WHERE bike_model_id = ? "
                "AND tire_model_id = ? AND position = ?",
                (f["bike_model_id"], target["id"], f["position"]),
            ).fetchone()
        )
        if target is not None and not dup:
            conn.execute(
                "UPDATE bike_tire_fitments SET tire_model_id = ? WHERE id = ?",
                (target["id"], f["id"]),
            )
            relinked += 1
            log(f"fitment {f['id']}: relinked to tire {target['id']}")
        else:
            conn.execute("DELETE FROM bike_tire_fitments WHERE id = ?", (f["id"],))
            deleted += 1
            why = "intended tire already linked" if dup else "no tire of the noted size"
            log(f"fitment {f['id']}: deleted ({why})")
    return {"relinked": relinked, "deleted": deleted}


def remove_placeholder_parts(conn, log) -> dict:
    removed = 0
    for brand, part_number in PLACEHOLDER_PARTS + SYNTHETIC_PARTS:
        row = conn.execute(
            "SELECT id, model_name FROM parts WHERE brand = ? AND part_number = ?",
            (brand, part_number),
        ).fetchone()
        if row is None:
            continue
        conn.execute("DELETE FROM part_prices WHERE part_id = ?", (row["id"],))
        conn.execute("DELETE FROM parts WHERE id = ?", (row["id"],))
        removed += 1
        log(f"part {row['id']} {brand} {row['model_name']} ({part_number}): removed")
    return {"parts_removed": removed}


def relabel_generic_parts(conn, log) -> dict:
    relabelled = 0
    for brand, part_number in GENERIC_RELABEL:
        row = conn.execute(
            "SELECT id, model_name FROM parts WHERE brand = ? AND part_number = ?",
            (brand, part_number),
        ).fetchone()
        if row is None:
            continue
        already = conn.execute(
            "SELECT id FROM parts WHERE brand = 'Generic' AND part_number = ?",
            (part_number,),
        ).fetchone()
        if already is not None:
            # A seed run after the relabel landed wrote the Generic row beside
            # the old one; drop the old-brand duplicate instead of making two.
            conn.execute("DELETE FROM part_prices WHERE part_id = ?", (row["id"],))
            conn.execute("DELETE FROM parts WHERE id = ?", (row["id"],))
            log(
                f"part {row['id']} {brand} {part_number}: duplicate of Generic row, removed"
            )
        else:
            conn.execute(
                "UPDATE parts SET brand = 'Generic' WHERE id = ?", (row["id"],)
            )
            log(f"part {row['id']} {brand} {row['model_name']}: brand -> Generic")
        relabelled += 1
    return {"parts_relabelled": relabelled}


def apply(db_path: str, dry_run: bool = False, verbose: bool = True) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    def log(msg):
        if verbose:
            print("  " + msg)

    result = {
        "headline": fix_headline_specs(conn, log),
        "fitments": fix_fitment_positions(conn, log),
        "parts": remove_placeholder_parts(conn, log),
        "relabel": relabel_generic_parts(conn, log),
    }
    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    conn.close()
    return result


def total_changes(result: dict) -> int:
    h, f, p = result["headline"], result["fitments"], result["parts"]
    return (
        h["bikes_changed"]
        + f["relinked"]
        + f["deleted"]
        + p["parts_removed"]
        + result["relabel"]["parts_relabelled"]
    )


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    db_path = os.environ.get("MOTOQUANT_DB", str(ROOT / "motoquant.db"))
    print(
        f"patch_2026_11_10_catalog_fixes on {db_path}"
        + (" (dry run)" if dry_run else "")
    )
    result = apply(db_path, dry_run=dry_run)
    for name in ("headline", "fitments", "parts", "relabel"):
        print(name, {k: v for k, v in result[name].items() if not k.startswith("_")})
    for line in result["headline"]["_inconsistent"]:
        print("  bore/stroke inconsistent with displacement -> NULL:", line)
    print(f"total changes: {total_changes(result)}")


if __name__ == "__main__":
    main()
