#!/usr/bin/env python3
"""
Add bike_tire_fitments rows for under-served drag/recommended tires
across 5 bike segments where the chat's recommend intent currently
returns 'no drag tires' or 'no recommended tires':

  - Hayabusa (id=11) — NO drag, NO recommended
  - Pulsar NS200 (id=140) — NO drag, NO recommended (Indian 200cc class)
  - Continental GT 650 (id=78) — has rec, no drag
  - Low Rider ST (id=133) — has rec, no drag
  - Classic 350 (id=166) — likely missing both

Idempotent — uses INSERT OR IGNORE on (bike_model_id, tire_model_id, position).

Tire model IDs verified against /tmp/mq_git.db on 2026-04-30. If a tire
model is renumbered by a future re-seed, this script may insert into
the wrong row — re-validate IDs before re-running on a fresh DB.

Usage:
    MOTOQUANT_DB=motoquant.db python scripts/patch_2026_04_30_drag_fitments.py
"""

import os
import sqlite3
import sys

# (bike_model_id, tire_model_id, position, fitment_type, notes)
ROWS = [
    # ── Hayabusa (id=11) — drag class champion, deserves the full kit ──
    (11, 187, "front", "recommended",
     "Pirelli Night Dragon 120/70 (street DOT, μ=1.85) — popular Hayabusa front upgrade"),
    (11, 172, "rear",  "recommended",
     "Pirelli Night Dragon 180/55 (street DOT) — pairs with front for drag-tuned street build"),
    (11, 165, "rear",  "drag_prep",
     "M&H Racemaster 5.5/18 (full slick μ=1.85) — track-only Pro Street class"),
    (11, 166, "rear",  "drag_prep",
     "Mickey Thompson ET Drag 180/55 (full slick) — Pro Street alternative to M&H"),
    (11, 215, "rear",  "drag_prep",
     "M&H Racemaster 6.0/18 — wider than 5.5 for high-power turbo Hayabusa builds"),
    (11, 163, "front", "drag_prep",
     "Avon AM23A Drag Radial 120/70 — DOT-legal drag front"),

    # ── Pulsar NS200 (id=140) — Indian 200cc drag staple ──
    (140, 185, "rear",  "recommended",
     "MRF Revz EF1 Drag 120/70 — Indian-made street drag tire (high mu, available)"),
    (140, 21,  "rear",  "drag_prep",
     "MRF Revz EF1 Drag 190/50 — needs aftermarket wider rear hoop / spacer kit"),
    (140, 14,  "rear",  "drag_prep",
     "Dunlop D212 GP Pro 190/55 — track-only DOT-R, fitting needs wider rim"),

    # ── Continental GT 650 (id=78) — drag prep gap ──
    (78, 187, "front", "drag_prep",
     "Pirelli Night Dragon 120/70 (DOT, μ=1.85) — drag launch front"),
    (78, 172, "rear",  "drag_prep",
     "Pirelli Night Dragon 180/55 (DOT, μ=1.85) — drag launch rear (street legal)"),

    # ── Low Rider ST (id=133) — Harley big-twin needs cruiser-friendly drag rubber ──
    (133, 172, "rear",  "drag_prep",
     "Pirelli Night Dragon 180/55 — DOT-legal drag rear, Harley-friendly carcass"),
    (133, 215, "rear",  "drag_prep",
     "M&H Racemaster 6.0/18 — wide drag slick for Pro Street muscle bike use"),

    # ── Classic 350 (id=166) — RE Classic 350 drag rubber options ──
    (166, 185, "rear",  "recommended",
     "MRF Revz EF1 Drag 120/70 — Indian-made for RE Classic 350 drag builds"),
    (166, 187, "rear",  "drag_prep",
     "Pirelli Night Dragon 180/55 — needs wider aftermarket rear hoop"),
]


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"Patching {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")

    n_added = 0
    n_skipped = 0
    n_failed = 0

    for bike_id, tire_id, position, ftype, notes in ROWS:
        # Verify both bike and tire exist
        b = conn.execute(
            "SELECT model_name FROM bike_models WHERE id = ?", (bike_id,)
        ).fetchone()
        t = conn.execute(
            "SELECT model_name FROM tire_models WHERE id = ?", (tire_id,)
        ).fetchone()
        if not b or not t:
            print(f"  SKIP bike={bike_id} tire={tire_id}: bike or tire not found")
            n_failed += 1
            continue
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO bike_tire_fitments (
                    bike_model_id, tire_model_id, position, fitment_type, notes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (bike_id, tire_id, position, ftype, notes),
            )
            if cur.rowcount > 0:
                n_added += 1
            else:
                n_skipped += 1
        except Exception as e:  # noqa: BLE001
            n_failed += 1
            print(f"  FAIL bike={bike_id} tire={tire_id}: {type(e).__name__}: {e}")

    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print(f"Total rows attempted: {len(ROWS)}")
    print(f"Inserted:             {n_added}")
    print(f"Skipped (already in): {n_skipped}")
    print(f"Failed:               {n_failed}")
    print("=" * 60)

    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
