#!/usr/bin/env python3
"""patch_2026_10_24_parts_data.py — arm the dead forced-induction kits and
ship the Trask 1950 cc fitment cap.

October 2026 core audit (reports/audit_core_2026_10_23_partial.md), three
findings fixed in the seed sources AND carried into the shipped DB here
(seed-source fold rule: the patch is never the only carrier of a fix):

1. **10 of 20 forced-induction parts delivered zero forced-induction power.**

   * Nitrous kits ZEX-35-UNI / ZEX-50-MOTO / NX-MICRO-15 set
     ``n2o_hp_per_stage`` but not ``n2o_stages`` (dataclass default 0), so
     ``hp_add = shot * 0``: 15/35/50 hp kits all simmed an identical
     -0.161 s at Aamby and exactly 0.000 s at sea level (the only "gain" was
     the boosted density-altitude floor). Now ``n2o_stages = 1``.
   * Turbo kits VT-STAGE1-GSXR / ORP-TT-GSXR-DRAG / HKS-R1-TURBO /
     GARRETT-G25-PANI-V4 / TRASK-VT-TURBO / TRASK-ASSAULT-M8 /
     TRASK-TORNADO-M8 set ``boost_type = 'turbo'`` with no
     ``target_boost_bar`` (0 bar) and encoded their gain as
     ``engine.peak_power_hp`` / ``peak_torque_nm`` deltas, which the bridge
     discards for boosted parts. A '+180 hp' twin-turbo simmed SLOWER than
     stock at sea level (+0.031 s, all mass). Now ``target_boost_bar`` comes
     from each kit's own ``specifications.boost_psi`` (psi x 0.0689476), with
     a spool time and the intercooler its specs declare, and the dead hp
     deltas are dropped (mass deltas kept).
   * TTS-SC-S1000RR already had its 5 psi boost; its +60 hp / +50 Nm deltas
     were dead data and are dropped.

2. **Trask turbo 1950 cc cap never reached the shipped DB.** The seed source
   widened TRASK-VT-TURBO's ``displacement_max_cc`` 1750 -> 1950 so Harley M8
   114/117 and Indian Thunderstroke/PowerPlus big twins match, but the DB row
   still carried 1750: 12 bikes could not see the kit. Only the cap and the
   description move; the row's manufacturer list ('Indian' is canonical in
   the DB) is left as is.

Rows are matched by (brand, part_number) — the parts table's UNIQUE key — so
ids never matter. Every value below is asserted equal to the fresh seed by
tests/test_fixwave_data_parts.py, so the patch and the seed cannot drift.

Idempotent: a second run reports 0 changes. Touches only ``parts``.
"""

from __future__ import annotations

import json
import os
import sqlite3

# (brand, part_number) -> {"param_overrides": {...}, "param_deltas": {...}}
FI_PARTS: dict[tuple[str, str], dict[str, dict]] = {
    ("ZEX", "ZEX-35-UNI"): {
        "param_overrides": {
            "forced_induction.boost_type": "n2o",
            "forced_induction.n2o_hp_per_stage": 35.0,
            "forced_induction.n2o_stages": 1,
        },
    },
    ("ZEX", "ZEX-50-MOTO"): {
        "param_overrides": {
            "forced_induction.boost_type": "n2o",
            "forced_induction.n2o_hp_per_stage": 50.0,
            "forced_induction.n2o_stages": 1,
        },
    },
    ("Nitrous Express", "NX-MICRO-15"): {
        "param_overrides": {
            "forced_induction.boost_type": "n2o",
            "forced_induction.n2o_hp_per_stage": 15.0,
            "forced_induction.n2o_stages": 1,
        },
    },
    ("Velocity Turbo", "VT-STAGE1-GSXR"): {  # 6.5 psi
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.448,
            "forced_induction.turbo_spool_time_s": 0.55,
            "forced_induction.intercooler_type": "a2a",
        },
        "param_deltas": {"chassis.dry_mass_kg": 8.5},
    },
    ("ORP", "ORP-TT-GSXR-DRAG"): {  # 12 psi, twin small turbos
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.827,
            "forced_induction.turbo_spool_time_s": 0.5,
            "forced_induction.intercooler_type": "a2a",
        },
        "param_deltas": {"chassis.dry_mass_kg": 15.0},
    },
    ("HKS", "HKS-R1-TURBO"): {  # 7 psi
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.483,
            "forced_induction.turbo_spool_time_s": 0.55,
            "forced_induction.intercooler_type": "a2a",
        },
        "param_deltas": {"chassis.dry_mass_kg": 9.0},
    },
    ("Garrett", "GARRETT-G25-PANI-V4"): {  # 6 psi, liquid-cooled IC
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.414,
            "forced_induction.turbo_spool_time_s": 0.55,
            "forced_induction.intercooler_type": "a2w",
        },
        "param_deltas": {"chassis.dry_mass_kg": 9.5},
    },
    ("TTS Supercharger", "TTS-SC-S1000RR"): {  # 5 psi (unchanged), dead hp dropped
        "param_overrides": {
            "forced_induction.boost_type": "sc_roots",
            "forced_induction.target_boost_bar": 0.345,
        },
        "param_deltas": {"chassis.dry_mass_kg": 7.5},
    },
    ("Trask Performance", "TRASK-VT-TURBO"): {  # 7.5 psi, liquid IC
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.517,
            "forced_induction.turbo_spool_time_s": 0.55,
            "forced_induction.intercooler_type": "a2w",
        },
        "param_deltas": {"chassis.dry_mass_kg": 10.0},
    },
    ("Trask Performance", "TRASK-ASSAULT-M8"): {  # 8 psi
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.552,
            "forced_induction.turbo_spool_time_s": 0.55,
        },
        "param_deltas": {"chassis.dry_mass_kg": 12.0},
    },
    ("Trask Performance", "TRASK-TORNADO-M8"): {  # 6 psi
        "param_overrides": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 0.414,
            "forced_induction.turbo_spool_time_s": 0.55,
        },
        "param_deltas": {"chassis.dry_mass_kg": 11.0},
    },
}

TRASK_KEY = ("Trask Performance", "TRASK-VT-TURBO")
TRASK_MAX_CC = 1950
TRASK_DESCRIPTION = (
    "Trask turbo for Harley/Indian V-twins incl. M8 114/117 (belt-drive OK); "
    "+85 hp, drag-prepped"
)


def _loads(s: str | None):
    return json.loads(s) if s else None


def apply(db_path: str, verbose: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    fi_updated = 0
    missing: list[str] = []

    for (brand, part_number), target in FI_PARTS.items():
        row = conn.execute(
            "SELECT id, param_overrides, param_deltas FROM parts"
            " WHERE brand = ? AND part_number = ?",
            (brand, part_number),
        ).fetchone()
        if row is None:
            missing.append(part_number)
            if verbose:
                print(f"  MISSING  {brand} {part_number}")
            continue
        new_ov = target["param_overrides"]
        new_dl = target.get("param_deltas")
        if _loads(row["param_overrides"]) == new_ov and _loads(row["param_deltas"]) == (
            new_dl or None
        ):
            continue
        conn.execute(
            "UPDATE parts SET param_overrides = ?, param_deltas = ?,"
            " updated_at = datetime('now','utc') WHERE id = ?",
            (json.dumps(new_ov), json.dumps(new_dl) if new_dl else None, row["id"]),
        )
        fi_updated += 1
        if verbose:
            print(f"  ARMED    {brand} {part_number} (id {row['id']})")

    trask_updated = 0
    row = conn.execute(
        "SELECT id, fitment_rules FROM parts WHERE brand = ? AND part_number = ?",
        TRASK_KEY,
    ).fetchone()
    if row is None:
        missing.append(TRASK_KEY[1] + " (fitment)")
    else:
        rules = _loads(row["fitment_rules"]) or {}
        match = rules.setdefault("match", {})
        if (
            match.get("displacement_max_cc") != TRASK_MAX_CC
            or rules.get("description") != TRASK_DESCRIPTION
        ):
            match["displacement_max_cc"] = TRASK_MAX_CC
            rules["description"] = TRASK_DESCRIPTION
            conn.execute(
                "UPDATE parts SET fitment_rules = ?,"
                " updated_at = datetime('now','utc') WHERE id = ?",
                (json.dumps(rules), row["id"]),
            )
            trask_updated = 1
            if verbose:
                print(f"  WIDENED  Trask turbo (id {row['id']}) -> {TRASK_MAX_CC} cc")

    conn.commit()
    conn.close()
    return {
        "fi_parts_updated": fi_updated,
        "trask_rule_updated": trask_updated,
        "missing": missing,
    }


if __name__ == "__main__":
    db = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"parts data patch on {db}:")
    print(f"  {apply(db, verbose=True)}")
