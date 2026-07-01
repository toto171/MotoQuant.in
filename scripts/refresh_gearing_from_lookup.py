"""
refresh_gearing_from_lookup.py
==============================
Idempotent utility: for every current bike_config row in motoquant.db, refresh
gear_ratios / front_sprocket / rear_sprocket / primary_ratio from the authoritative
Tier-1 lookup in motoquant.scraper.gear_ratios, *except* for the three reference
bikes (K5, YZF-R1 4C8, Hayabusa Gen1) which are kept locked to their defaults.py
ship configs so the K5=10.033 / R1=10.286 / Busa=10.471 baselines are preserved.

TIER-1 ONLY: lookup_gear_ratios() never returns None -- bikes without a named-model
(Tier-1) entry fall through to GENERIC Tier-2 category/displacement defaults. We
DELIBERATELY skip those (see the SAFETY note in refresh()), because many carry
engine-family-correct or hand-tuned DB gearing that a generic default would regress.
Only ~160 bikes (the Tier-1 mismatches) are rewritten; the ~310 Tier-2 bikes are
left exactly as they are.

Why this exists
---------------
On April 22 2026 we discovered that motoquant.db had leaked K5-like gear ratios
into ~270 bike rows (notably RE Continental GT 650 showed 178 km/h terminal
velocity in 4th gear — physically impossible). The root cause was that the DB
had been seeded *before* the April-22 gear-ratio audit (`066fc0e`) landed in
gear_ratios.py and no subsequent refresh pass had written the corrected ratios
back into the DB. The importer logic itself is correct; it's the already-seeded
rows that are stale.

Run on demand whenever gear_ratios.py changes:

    python -m scripts.refresh_gearing_from_lookup
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Allow running as a loose script from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motoquant import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402
from motoquant.scraper.gear_ratios import lookup_gear_ratios  # noqa: E402

# lookup_gear_ratios() returns this confidence on a Tier-1 (named-model) hit;
# anything lower is a GENERIC Tier-2 category/displacement default. See the
# Tier-1-only safety note in refresh() for why we never reseed from Tier-2.
TIER1_CONFIDENCE = 0.75

REFERENCE_NAME_PATTERNS: dict[str, callable] = {
    "GSX-R 1000 K5": gsxr1000_k5,
    "YZF-R1 4C8": yzfr1_4c8,
    "Hayabusa GSX1300R Gen1": hayabusa_gen1,
}


def _reference_ship_config_for(model_name: str):
    for needle, fn in REFERENCE_NAME_PATTERNS.items():
        if needle in model_name:
            return fn()
    return None


def refresh(db_path: str = "motoquant.db") -> dict:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT bc.id, bc.bike_model_id, m.name, bm.model_name, bm.year_from, bm.year_to,
               bc.drivetrain_params
        FROM bike_configs bc
        JOIN bike_models bm ON bm.id = bc.bike_model_id
        JOIN manufacturers m ON m.id = bm.manufacturer_id
        WHERE bc.is_current = 1
        """
    )
    rows = cur.fetchall()
    stats = {
        "total": len(rows),
        "updated": 0,
        "unchanged": 0,
        "reference_locked": 0,
        "no_tier1": 0,
        "tier2_skipped": 0,
        "malformed_skipped": 0,
    }

    for cid, bmid, mfr, mdl, yf, yt, dp in rows:
        drv = json.loads(dp)

        ship = _reference_ship_config_for(mdl)
        if ship is not None:
            ratios = list(ship.drivetrain.gear_ratios)
            front = ship.drivetrain.front_sprocket
            rear = ship.drivetrain.rear_sprocket
            primary = ship.drivetrain.primary_ratio
            stats["reference_locked"] += 1
        else:
            clean = mdl.split("(")[0].strip()
            year = yf or 2024
            if yt and yf:
                year = (yf + yt) // 2
            lookup = lookup_gear_ratios(mfr, clean, year)
            if lookup is None:
                stats["no_tier1"] += 1
                continue
            ratios, front, rear, primary, conf = lookup
            # SAFETY (Tier-1 only): lookup_gear_ratios() NEVER returns None -- a
            # non-Tier-1 bike falls through to GENERIC Tier-2 category/displacement
            # defaults (confidence < TIER1_CONFIDENCE). Applying those would
            # overwrite engine-family-correct / hand-tuned DB gearing with a
            # generic curve (e.g. clobbering the Versys 650's real ER650 cassette
            # with a generic parallel-twin default). Only reseed from authoritative
            # Tier-1 (named-model) matches; leave everything else untouched.
            if conf < TIER1_CONFIDENCE:
                stats["tier2_skipped"] += 1
                continue
            ratios = list(ratios)
            # Guard against malformed Tier-1 entries (e.g. a 5-speed padded to 6
            # with a trailing None). The physics multiplies by every gear, so a
            # None gear crashes the sim; skip and preserve the DB value.
            if any(r is None for r in ratios):
                stats["malformed_skipped"] += 1
                continue

        already = (
            drv.get("gear_ratios") == ratios
            and drv.get("front_sprocket") == front
            and drv.get("rear_sprocket") == rear
            and abs((drv.get("primary_ratio") or 0) - primary) < 1e-3
        )
        if already:
            stats["unchanged"] += 1
            continue

        drv["gear_ratios"] = ratios
        drv["front_sprocket"] = int(front)
        drv["rear_sprocket"] = int(rear)
        drv["primary_ratio"] = float(primary)
        # Chain drive: recompute final_drive from the new sprockets.
        # Shaft-/belt-drive bikes have front=0 in the Tier-1 lookup -- but the
        # physics still needs a NUMERIC final reduction (models.py final_ratio
        # falls back to final_drive_ratio when there are no chain sprockets), so
        # PRESERVE the existing value rather than nulling it (nulling broke the
        # R 1250 GS sim: primary * gear * None -> TypeError).
        if float(front) > 0:
            drv["final_drive_ratio"] = float(rear) / float(front)
        cur.execute(
            "UPDATE bike_configs SET drivetrain_params = ?, "
            "updated_at = datetime('now','utc') WHERE id = ?",
            (json.dumps(drv), cid),
        )
        stats["updated"] += 1

    conn.commit()
    conn.close()
    return stats


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "motoquant.db"
    result = refresh(db)
    print(f"DB: {db}")
    for k, v in result.items():
        print(f"  {k}: {v}")
