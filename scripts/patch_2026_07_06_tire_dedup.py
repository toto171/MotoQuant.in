#!/usr/bin/env python3
"""patch_2026_07_06_tire_dedup.py — merge duplicate tire rows.

Five tire_models rows are notation-duplicates of an existing row: the same
manufacturer + model_name + position + physical size, differing only in the
size string's construction marker ('100/90-17' bias notation vs '100/90R17').
They were minted by seeders that compared size_designation as an exact
string; tire_repo.create now normalizes notation before matching (July 6,
2026), so fresh seeds can no longer recreate them — this patch cleans the
shipped DB.

Merge direction: keep the row with more fitments (the '-' bias-notation row
in every case, matching how the OEM specs write these sizes), re-point
bike_tire_fitments from the duplicate, drop fitment rows that would collide
with an existing (bike, tire, position, fitment_type) link, then delete the
duplicate tire row.

Idempotent: re-running after the duplicates are gone is a no-op.
"""

import os
import sqlite3

# (keep_id, drop_id) — verified same mfr+model+position+physical size
MERGES = [
    (101, 104),  # MRF Zapper front 100/90-17  <- 100/90R17
    (103, 105),  # MRF Zapper front 100/90-19  <- 100/90R19
    (132, 133),  # IRC GP-110 rear 120/70-17   <- 120/70R17
    (142, 143),  # Bridgestone Battlax rear 140/60-17 <- 140/60R17
    (145, 147),  # Bridgestone Battlax rear 140/70-18 <- 140/70R18
    # Keep 154 (complete width/aspect/rim columns) over 153 (NULL aspect/rim)
    (154, 153),  # MRF Zapper rear 150/80R16 <- 150/80B16
]


def apply(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    merged = 0
    skipped = 0
    for keep_id, drop_id in MERGES:
        drop = conn.execute(
            "SELECT id FROM tire_models WHERE id=?", (drop_id,)
        ).fetchone()
        if drop is None:
            skipped += 1
            continue
        keep = conn.execute(
            "SELECT id FROM tire_models WHERE id=?", (keep_id,)
        ).fetchone()
        if keep is None:
            print(f"  keep row {keep_id} missing — leaving {drop_id} untouched")
            skipped += 1
            continue
        # Re-point fitments; drop any that would duplicate an existing link.
        fit_cols = [r[1] for r in conn.execute("PRAGMA table_info(bike_tire_fitments)")]
        for fit in conn.execute(
            "SELECT * FROM bike_tire_fitments WHERE tire_model_id=?", (drop_id,)
        ).fetchall():
            probe_cols = [
                c
                for c in ("bike_model_id", "position", "fitment_type")
                if c in fit_cols
            ]
            where = " AND ".join(f"{c}=?" for c in probe_cols)
            exists = conn.execute(
                f"SELECT 1 FROM bike_tire_fitments WHERE tire_model_id=? AND {where}",
                (keep_id, *[fit[c] for c in probe_cols]),
            ).fetchone()
            if exists:
                conn.execute("DELETE FROM bike_tire_fitments WHERE id=?", (fit["id"],))
            else:
                conn.execute(
                    "UPDATE bike_tire_fitments SET tire_model_id=? WHERE id=?",
                    (keep_id, fit["id"]),
                )
        conn.execute("DELETE FROM tire_models WHERE id=?", (drop_id,))
        merged += 1
    conn.commit()
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    return {"merged": merged, "already_clean": skipped, "fk_violations": len(fk)}


if __name__ == "__main__":
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"tire dedup patch: {apply(db_path)}")
