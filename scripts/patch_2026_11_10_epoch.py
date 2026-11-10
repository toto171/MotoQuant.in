#!/usr/bin/env python3
"""patch_2026_11_10_epoch.py -- duplicate-bike removal (epoch 2026-11-10).

Runs LAST in the re-seed chain (after scripts/reseed_configs_from_specs.py and
every earlier patch). Idempotent: a second run reports 0 changes.

Seven motorcycles were entered twice with overlapping year ranges and
conflicting data, and the two CBR1000RR-R Fireblade SP generations overlapped on
2024. The spec sources now carry one row per bike (see
reports/session_2026_11_10_epoch.md for which row survived and why); this script
brings the database in line:

  * the removed row's dependents are re-pointed or deleted -- saved runs
    (sim_runs) and archetypes move to the surviving bike; its configs, dyno
    curves, provenance, tire fitments and spec corrections go with it (fitments
    are NOT merged: the two rows carried different tyre sizes);
  * the surviving row's year range, display name and mass headline columns are
    set from its spec.

Rows are identified by their natural key (manufacturer, model, model_code,
year_from), never by database id, so the script also works on a fresh seed
(where it simply finds nothing to remove).

Usage:
    MOTOQUANT_DB=<db> python scripts/patch_2026_11_10_epoch.py [--dry-run]
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402

# (manufacturer, model, removed (model_code, year_from), surviving (model_code, year_from))
DUPLICATES = [
    ("Royal Enfield", "Continental GT 650", ("GT650", 2020), ("2018", 2018)),
    ("Royal Enfield", "Interceptor 650", ("INT650", 2020), ("2018", 2018)),
    (
        "Royal Enfield",
        "Super Meteor 650",
        ("SM650", 2023),
        ("SUPER_METEOR_650_2023", 2023),
    ),
    ("Honda", "Hornet 2.0", (None, 2024), ("2020", 2020)),
    ("Aprilia", "Tuono 457", ("T457", 2024), ("Tuono_457_2025", 2025)),
    ("TVS", "Raider 125", (None, 2022), ("TVS-R125", 2021)),
    ("Suzuki", "V-Strom SX 250", (None, 2022), ("DR-Z250SX", 2022)),
]

# Bikes that stay but whose year range changed: (manufacturer, model, model_code, year_from)
YEAR_RANGE_CHANGES = [
    ("Honda", "CBR1000RR-R Fireblade SP", "SC82", 2020),
    ("Honda", "Hornet 2.0", "2020", 2020),
]


def _strip_year(name: str) -> str:
    from reseed_configs_from_specs import strip_year

    return strip_year(name)


def _find_model(conn, manufacturer, model, model_code, year_from):
    rows = conn.execute(
        "SELECT bm.* FROM bike_models bm JOIN manufacturers m "
        "ON m.id = bm.manufacturer_id WHERE m.name = ? AND bm.year_from = ? "
        "AND bm.model_code IS ?",
        (manufacturer, year_from, model_code),
    ).fetchall()
    rows = [r for r in rows if _strip_year(r["model_name"]) == model]
    if len(rows) > 1:
        raise RuntimeError(f"ambiguous bike row: {manufacturer} {model} {model_code}")
    return rows[0] if rows else None


def _spec_for(manufacturer, model, model_code, year_from):
    for s in ALL_KNOWN_BIKES:
        if (
            s.manufacturer == manufacturer
            and _strip_year(s.model_name) == model
            and s.model_code == model_code
            and s.year_from == year_from
        ):
            return s
    raise RuntimeError(f"no spec for {manufacturer} {model} {model_code} {year_from}")


def _table_exists(conn, name) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def _current_config_id(conn, model_id):
    row = conn.execute(
        "SELECT id FROM bike_configs WHERE bike_model_id = ? "
        "ORDER BY is_current DESC, version DESC, id DESC LIMIT 1",
        (model_id,),
    ).fetchone()
    return row["id"] if row else None


def _sync_survivor(conn, row, spec, log) -> int:
    """Set year range, display name and mass headline columns from the spec."""
    name = _strip_year(row["model_name"])
    year_to = spec.year_to or spec.year_from
    new_name = f"{name} ({spec.year_from}-{year_to})"
    dry = spec.dry_mass_kg
    if dry is None and spec.wet_mass_kg:
        dry = spec.wet_mass_kg - 25.0  # the importer's wet -> dry convention
    wanted = {
        "model_name": new_name,
        "year_from": spec.year_from,
        "year_to": year_to,
        "dry_mass_kg": dry,
        "wet_mass_kg": spec.wet_mass_kg,
    }
    changed = {k: v for k, v in wanted.items() if row[k] != v}
    if not changed:
        return 0
    sets = ", ".join(f"{k} = ?" for k in changed)
    conn.execute(
        f"UPDATE bike_models SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (*changed.values(), row["id"]),
    )
    log(f"updated bike {row['id']} {row['model_name']!r}: {changed}")
    return 1


def remove_duplicates(conn, log) -> dict:
    removed = repointed_runs = updated = 0
    counts = {"configs": 0, "fitments": 0, "provenance": 0, "dyno_curves": 0}
    for mfr, model, (lose_code, lose_year), (keep_code, keep_year) in DUPLICATES:
        keep = _find_model(conn, mfr, model, keep_code, keep_year)
        lose = _find_model(conn, mfr, model, lose_code, lose_year)
        if keep is None:
            if lose is not None:
                raise RuntimeError(
                    f"{mfr} {model}: the surviving row is missing but the "
                    "duplicate exists - refusing to delete"
                )
            continue
        if lose is not None:
            keep_cfg = _current_config_id(conn, keep["id"])
            lose_cfgs = [
                r["id"]
                for r in conn.execute(
                    "SELECT id FROM bike_configs WHERE bike_model_id = ?",
                    (lose["id"],),
                )
            ]
            for cid in lose_cfgs:
                if keep_cfg is not None:
                    repointed_runs += conn.execute(
                        "UPDATE sim_runs SET bike_config_id = ? WHERE bike_config_id = ?",
                        (keep_cfg, cid),
                    ).rowcount
                counts["dyno_curves"] += conn.execute(
                    "DELETE FROM dyno_curves WHERE bike_config_id = ?", (cid,)
                ).rowcount
                counts["provenance"] += conn.execute(
                    "DELETE FROM data_provenance WHERE entity_type = 'bike_config' "
                    "AND entity_id = ?",
                    (cid,),
                ).rowcount
            counts["configs"] += conn.execute(
                "DELETE FROM bike_configs WHERE bike_model_id = ?", (lose["id"],)
            ).rowcount
            counts["fitments"] += conn.execute(
                "DELETE FROM bike_tire_fitments WHERE bike_model_id = ?", (lose["id"],)
            ).rowcount
            if _table_exists(conn, "bike_archetypes"):
                conn.execute(
                    "UPDATE bike_archetypes SET base_bike_model_id = ? "
                    "WHERE base_bike_model_id = ?",
                    (keep["id"], lose["id"]),
                )
            if _table_exists(conn, "spec_corrections"):
                conn.execute(
                    "DELETE FROM spec_corrections WHERE bike_model_id = ?",
                    (lose["id"],),
                )
            conn.execute(
                "DELETE FROM data_provenance WHERE entity_type = 'bike_model' "
                "AND entity_id = ?",
                (lose["id"],),
            )
            conn.execute("DELETE FROM bike_models WHERE id = ?", (lose["id"],))
            removed += 1
            log(
                f"removed duplicate bike {lose['id']} {lose['model_name']!r} "
                f"(kept {keep['id']} {keep['model_name']!r})"
            )
        updated += _sync_survivor(
            conn, keep, _spec_for(mfr, model, keep_code, keep_year), log
        )
    for mfr, model, code, year in YEAR_RANGE_CHANGES:
        row = _find_model(conn, mfr, model, code, year)
        if row is not None:
            updated += _sync_survivor(conn, row, _spec_for(mfr, model, code, year), log)
    # Kerb-as-dry corrections on bikes that are not part of a duplicate pair.
    for mfr, model, code, year in [("Honda", "CBR1000RR-R Fireblade SP", "8BL", 2024)]:
        row = _find_model(conn, mfr, model, code, year)
        if row is not None:
            updated += _sync_survivor(conn, row, _spec_for(mfr, model, code, year), log)
    return {
        "bikes_removed": removed,
        "bikes_updated": updated,
        "runs_repointed": repointed_runs,
        **{f"{k}_deleted": v for k, v in counts.items()},
    }


def apply(db_path: str, dry_run: bool = False, verbose: bool = True) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    def log(msg):
        if verbose:
            print("  " + msg)

    result = {"duplicates": remove_duplicates(conn, log)}
    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    conn.close()
    return result


def total_changes(result: dict) -> int:
    d = result["duplicates"]
    return d["bikes_removed"] + d["bikes_updated"]


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    db_path = os.environ.get("MOTOQUANT_DB", str(ROOT / "motoquant.db"))
    print(f"patch_2026_11_10_epoch on {db_path}" + (" (dry run)" if dry_run else ""))
    result = apply(db_path, dry_run=dry_run)
    print("duplicates", result["duplicates"])
    print(f"total changes: {total_changes(result)}")


if __name__ == "__main__":
    main()
