#!/usr/bin/env python3
"""
MotoQuant — OEM tire-fitment integrity patch (2026-08-08).

Cleans the shipped-DB damage left by the two `bike_tire_fitments` defects the
2026-07-25 weekly audit found (§3.3b). Both root causes are fixed in the seed
sources, so a fresh `seed_all()` can no longer recreate the damage:

  * `motoquant/database/seed.py` — the ±20 mm OEM fallback filtered compounds
    with a DENYLIST ('race', 'drag_dot', 'drag_slick') that never named the
    catalog's later-added 'drag' compound (10 rows, mu_peak 1.85 — the
    highest-grip rows in the table). Fallback candidates are ordered mu_peak
    DESC, so those drag slicks WON, and the shipped DB asserts M&H Racemaster
    / Avon AM23A drag rubber as the factory fitment for 24 bikes — the three
    pinned reference bikes among them. Now an ALLOWLIST (`OEM_COMPOUNDS`),
    applied by the shared picker `seed.pick_oem_tire`.

  * `motoquant/database/tire_repo.py` — `link_bike_fitment` used
    INSERT OR REPLACE against UNIQUE(bike_model_id, tire_model_id, position,
    fitment_type). That key INCLUDES the tire, so seeding a *different* tire
    into the same slot appended a SECOND is_default=1 row instead of
    superseding the first: 77 (bike, position) groups across 65 bikes carry
    two mutually exclusive "default OEM" tires, growing ~7 per seed run.
    Linking a default now supersedes the previous one.

What this script repairs (a group = one (bike_model_id, position) slot, over
fitment_type='oem' AND is_default=1 rows only — 'recommended' and 'drag_prep'
rows are never touched):

  A. Groups holding a tire whose compound is not in `seed.OEM_COMPOUNDS`.
  B. Groups holding more than one default row.

Repair rule — the group is re-decided by the FIXED production picker
(`seed.pick_oem_tire`) against the bike's own declared size in
`bike_configs.tire_params`, and re-linked through the FIXED production linker
(`TireRepository.link_bike_fitment`). Every decision therefore agrees with what
a re-seed would choose: re-running `seed_bike_tire_fitments` over a patched DB
touches none of the repaired slots. (It does still fill 6 slots that carry no
OEM row at all — pre-existing staleness against tires seeded after fitments
were last run, unrelated to this defect and deliberately out of scope here:
this patch repairs wrong rows, it does not backfill missing ones.)

  * picker returns a tire  -> that tire is kept/created as the single default;
    every other default row in the group is deleted (a superseded pick is not
    a second OEM fitment — the API bike-detail route and `bikes --fitments`
    list every 'oem' row, so leaving it behind keeps asserting a tire the
    factory never fitted);
  * picker returns None    -> every default row in the group is deleted.
    Honest absence beats wrong data; nothing invents a replacement.

Idempotent: a second run finds no damaged groups and reports 0 changes.

Chain position (docs/KNOWN_TRAPS.md T17) — append LAST in the re-seed chain,
after `patch_2026_07_13_scrape_data.py`. Order-independent: it touches only
`bike_tire_fitments`. Note it is a *cleaner*, not a re-required step: because
both root causes are fixed in the seed sources, re-running
`seed_bike_tire_fitments` over the damaged DB already converges on the same
clean row set (verified: seeding the patched and the unpatched catalog yields
byte-identical fitment rows). It is in the chain so a catalog rebuilt without
a fitment re-seed still lands clean.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.database.seed import OEM_COMPOUNDS, pick_oem_tire  # noqa: E402

_PLACEHOLDERS = ", ".join("?" * len(OEM_COMPOUNDS))


def _damaged_groups(conn) -> list[tuple[int, str]]:
    """(bike_model_id, position) slots with a non-OEM compound or >1 default."""
    rows = conn.execute(
        f"""SELECT btf.bike_model_id, btf.position
            FROM bike_tire_fitments btf
            JOIN tire_models tm ON tm.id = btf.tire_model_id
            WHERE btf.fitment_type = 'oem' AND btf.is_default = 1
            GROUP BY btf.bike_model_id, btf.position
            HAVING COUNT(*) > 1
                OR SUM(tm.compound_type NOT IN ({_PLACEHOLDERS})) > 0
            ORDER BY btf.bike_model_id, btf.position""",
        sorted(OEM_COMPOUNDS),
    ).fetchall()
    return [(r["bike_model_id"], r["position"]) for r in rows]


def _declared_size(conn, bike_model_id: int, position: str) -> str | None:
    """The bike's own OEM tire size for `position`, from its current stock config."""
    row = conn.execute(
        """SELECT tire_params FROM bike_configs
           WHERE bike_model_id = ? AND is_current = 1 AND config_name = 'stock'
           ORDER BY id DESC LIMIT 1""",
        (bike_model_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["tire_params"]).get(f"{position}_size")
    except (TypeError, ValueError):
        return None


def apply(db_path: str, verbose: bool = True) -> dict:
    db = MotoQuantDB(db_path)
    conn = db.connect()
    conn.execute("PRAGMA foreign_keys=ON")

    groups = _damaged_groups(conn)
    repaired = dropped_rows = 0
    slots_repicked = slots_emptied = 0

    for bike_model_id, position in groups:
        current = conn.execute(
            """SELECT btf.id, btf.tire_model_id, tm.compound_type,
                      tm.model_name, tm.size_designation
               FROM bike_tire_fitments btf
               JOIN tire_models tm ON tm.id = btf.tire_model_id
               WHERE btf.bike_model_id = ? AND btf.position = ?
                 AND btf.fitment_type = 'oem' AND btf.is_default = 1
               ORDER BY btf.id""",
            (bike_model_id, position),
        ).fetchall()

        size_str = _declared_size(conn, bike_model_id, position)
        desired = pick_oem_tire(db, position, size_str) if size_str else None
        keep_id = desired["id"] if desired else None

        for row in current:
            if row["tire_model_id"] == keep_id:
                continue
            conn.execute("DELETE FROM bike_tire_fitments WHERE id = ?", (row["id"],))
            dropped_rows += 1

        if keep_id is not None:
            # Re-link through the fixed production path (upsert + supersede).
            db.tires.link_bike_fitment(
                bike_model_id=bike_model_id,
                tire_model_id=keep_id,
                position=position,
                fitment_type="oem",
                is_default=True,
            )
            slots_repicked += 1
        else:
            slots_emptied += 1

        repaired += 1
        if verbose:
            was = ", ".join(
                f"{r['model_name']} {r['size_designation']} [{r['compound_type']}]"
                for r in current
            )
            now = (
                f"{desired['model_name']} {desired['size_designation']} "
                f"[{desired['compound_type']}]"
                if desired
                else "(none — no acceptable OEM candidate)"
            )
            print(f"  bike {bike_model_id} {position}: {was}  ->  {now}")

    conn.commit()
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    remaining_bad = len(_damaged_groups(conn))
    db.close()

    return {
        "groups_repaired": repaired,
        "slots_repicked": slots_repicked,
        "slots_emptied": slots_emptied,
        "rows_deleted": dropped_rows,
        "groups_still_damaged": remaining_bad,
        "fk_violations": len(fk),
    }


if __name__ == "__main__":
    path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"fitment-integrity patch on {path}")
    print(f"  patch result: {apply(path)}")
