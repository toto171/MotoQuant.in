#!/usr/bin/env python3
"""patch_2026_08_08_quickshifter_overrides.py — arm eight dead quickshifter SKUs.

The 2026-07-25 weekly audit (reports/session_2026_07_25_weekly_audit.md §3.3c)
found eight shipped, priced catalog parts that move ET by exactly 0.000000 s:

    ``DrivetrainParams.quickshifter`` has NO reader in the physics engine — the
    sim reads only ``drivetrain.total_shift_time_ms`` (physics.py, the shift
    dead-time term). These eight parts carried ``drivetrain.quickshifter`` as
    their ONLY parameter modification, so selecting one changed nothing, while
    twelve functionally identical sibling quickshifters that also set
    ``total_shift_time_ms`` deliver −0.084 to −0.094 s.

This patch adds the honest ``drivetrain.total_shift_time_ms`` override to each
of the eight, matching the corrected seed source in
``motoquant/database/seed.py`` (seed-source fold rule, July-4 A3-15 — the
patch must never be the only carrier of the fix).

``drivetrain.quickshifter: True`` is deliberately KEPT on every row: it is
honest product metadata (the part really is a quickshifter) even though the
current physics engine does not read it. If a future epoch wires that flag up,
the metadata is already correct.

Values and their evidence (stock baseline is 100 ms on 538 of 541 configs;
the twelve functional siblings sit in a 48–70 ms band):

  HT-QS-MOD   HealTech QuickShifter Controller Module  -> 60 ms
              HealTech's own siblings bracket it: iQSE-1 Universal I4 at an
              absolute 50 ms, iQSE Indian 200-400 at −40 ms off stock (= 60).
              Take the conservative end for this generic controller SKU.
  QS-HM-4     HM QS Mid-Range                          -> 70 ms
              HM's Super Lite (HM-QS-SLT) is the 60 ms top-tier unit in the
              same line; Mid-Range sits one rung below it.
  QS-TRA-5    Translogic QS Pro V2                     -> 60 ms
              Predecessor generation to the QS Pro III Bidirectional
              (TL-QS3-BD, 50 ms) and IntelliShift Sport I4 (55 ms).
  QS-DYN-6    Dynojet Power Commander QS               -> 55 ms
              Same product line and same street price (Rs12,640) as DJ-PCQS,
              already seeded at 55 ms — mirror it exactly.
  QS-GPR-7    GPR Gear Box QS                          -> 60 ms
  QS-HEL-8    Helix QS Universal                       -> 60 ms
  QS-SHI-9    Shift Assist Pro                         -> 60 ms
  QS-BON-10   Bonamici Racing Quick Shifter            -> 60 ms
              No functional sibling for these four brands, so they take the
              60 ms band midpoint rather than any vendor's fastest claim.

Absolute overrides (not deltas) are used throughout, matching the majority
sibling convention (9 of 12) and keeping re-application idempotent.

Idempotent: re-running after the overrides are present is a no-op.
"""

import json
import os
import sqlite3

# part_number -> (model_name for the log, total_shift_time_ms)
SHIFT_TIMES_MS: dict[str, tuple[str, float]] = {
    "HT-QS-MOD": ("HealTech QuickShifter Controller Module", 60.0),
    "QS-HM-4": ("HM QS Mid-Range", 70.0),
    "QS-TRA-5": ("Translogic QS Pro V2", 60.0),
    "QS-DYN-6": ("Dynojet Power Commander QS", 55.0),
    "QS-GPR-7": ("GPR Gear Box QS", 60.0),
    "QS-HEL-8": ("Helix QS Universal", 60.0),
    "QS-SHI-9": ("Shift Assist Pro", 60.0),
    "QS-BON-10": ("Bonamici Racing Quick Shifter", 60.0),
}

_PATH = "drivetrain.total_shift_time_ms"


def apply(db_path: str, verbose: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    updated = 0
    already = 0
    missing = 0

    for part_number, (label, shift_ms) in SHIFT_TIMES_MS.items():
        row = conn.execute(
            "SELECT id, param_overrides, param_deltas FROM parts WHERE part_number=?",
            (part_number,),
        ).fetchone()
        if row is None:
            missing += 1
            if verbose:
                print(f"  MISSING  {part_number} ({label}) — not in this DB")
            continue

        overrides = json.loads(row["param_overrides"]) if row["param_overrides"] else {}
        deltas = json.loads(row["param_deltas"]) if row["param_deltas"] else {}

        # Already armed — either by a previous run of this patch, or by a
        # delta-carrying variant of the same SKU. Leave it alone.
        if overrides.get(_PATH) == shift_ms:
            already += 1
            if verbose:
                print(f"  OK       {part_number} ({label}) already {shift_ms:g} ms")
            continue
        if _PATH in deltas:
            already += 1
            if verbose:
                print(f"  SKIP     {part_number} ({label}) carries a delta already")
            continue

        overrides[_PATH] = shift_ms
        # Keep the (inert but honest) quickshifter flag if it was there, and
        # add it if a previous edit dropped it.
        overrides.setdefault("drivetrain.quickshifter", True)
        conn.execute(
            "UPDATE parts SET param_overrides=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(overrides), row["id"]),
        )
        updated += 1
        if verbose:
            print(f"  ARMED    {part_number} ({label}) -> {shift_ms:g} ms")

    conn.commit()
    conn.close()
    return {
        "updated": updated,
        "already_armed": already,
        "missing": missing,
        "expected": len(SHIFT_TIMES_MS),
    }


if __name__ == "__main__":
    db = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"quickshifter override patch on {db}:")
    print(f"  {apply(db, verbose=True)}")
