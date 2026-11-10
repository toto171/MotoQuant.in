#!/usr/bin/env python3
"""patch_2026_10_24_config_sync.py — re-derive the two copies of physics data
that reseeds never refreshed.

``bike_configs`` JSON blobs are the source of truth for the physics (they are
what /api/simulate, the golden snapshot and every reseed/patch read and
write). Two DERIVED copies of them had gone stale (October 2026 core audit):

1. **dyno_curves rows.** ``create_config`` writes one dyno_curves row per
   config at insert time; ``reseed_configs_from_specs.py`` and every patch
   rewrite only the blobs. In the shipped DB 508 of 553 rows no longer match
   their config's engine_params curve (506 still carry the pre-Aug-8
   at-wheel semantics). ``BikeRepository.to_config`` preferred those rows, so
   CLI/chat/NL sims ran a different curve than the API (up to 2.28 s). The
   repository now reads the blob; this patch rewrites each row to the blob so
   the table (used for cross-bike curve comparison) is honest too.

2. **bike_models headline columns.** The reseed syncs only displacement/hp/
   torque/mass, so 9 bikes listed bore/stroke/compression/rpm points/
   wheelbase the sim does not use (e.g. V-Strom SX 250 wheelbase 1355 vs 1440
   in physics; Continental GT 650 bore x stroke 84 x 58 vs 78 x 67.8). This
   patch re-derives every headline column from the current stock blob via
   ``BikeRepository.sync_headline_specs`` (the same ``extract_headline_specs``
   the importer uses). None of these columns feed the physics or the
   parts-compatibility engine (which reads displacement, cylinder config,
   category, year, chain pitch and stroke type — all already in sync).

Neither change moves a simulated ET: the physics reads only the blobs.
Idempotent: a second run reports 0 changes.

Chain position: append after ``patch_2026_08_08_quickshifter_overrides.py``,
and re-run after any reseed (until the reseed itself refreshes both copies).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.database.bridge import db_row_to_config  # noqa: E402
from motoquant.database.connection import MotoQuantDB  # noqa: E402


def _curve_cols(engine_blob: str) -> tuple | None:
    dc = json.loads(engine_blob).get("dyno_curve") if engine_blob else None
    if dc is None:
        return None
    rpm = [float(x) for x in dc["rpm"]]
    torque = [float(x) for x in dc["torque_nm"]]
    return (
        1 if dc.get("is_at_wheel") else 0,
        json.dumps(rpm),
        json.dumps(torque),
        len(rpm),
    )


def apply(db_path: str, verbose: bool = False) -> dict:
    db = MotoQuantDB(db_path)
    conn = db.connect()
    curves_updated = 0
    curves_inserted = 0
    headline_rows = 0
    headline_cells = 0

    for cfg in conn.execute(
        "SELECT id, engine_params, source, confidence FROM bike_configs"
    ).fetchall():
        target = _curve_cols(cfg["engine_params"])
        if target is None:
            continue
        rows = conn.execute(
            "SELECT id, is_at_wheel, rpm_points, torque_values, num_points"
            " FROM dyno_curves WHERE bike_config_id = ?",
            (cfg["id"],),
        ).fetchall()
        if not rows:
            conn.execute(
                """INSERT INTO dyno_curves
                   (bike_config_id, curve_type, is_at_wheel, rpm_points,
                    torque_values, num_points, source, confidence)
                   VALUES (?, 'torque', ?, ?, ?, ?, ?, ?)""",
                (cfg["id"], *target, cfg["source"], cfg["confidence"]),
            )
            curves_inserted += 1
            continue
        for r in rows:
            current = (
                r["is_at_wheel"],
                r["rpm_points"],
                r["torque_values"],
                r["num_points"],
            )
            if current == target:
                continue
            conn.execute(
                """UPDATE dyno_curves SET is_at_wheel = ?, rpm_points = ?,
                       torque_values = ?, num_points = ?
                   WHERE id = ?""",
                (*target, r["id"]),
            )
            curves_updated += 1

    for row in conn.execute(
        """SELECT bc.*, bm.model_name FROM bike_configs bc
           JOIN bike_models bm ON bm.id = bc.bike_model_id
           WHERE bc.is_current = 1 AND bc.config_name = 'stock'"""
    ).fetchall():
        cfg = db_row_to_config(dict(row))
        changed = db.bikes.sync_headline_specs(row["bike_model_id"], cfg)
        if changed:
            headline_rows += 1
            headline_cells += len(changed)
            if verbose:
                print(
                    f"  HEADLINE {row['bike_model_id']} {row['model_name']}: {changed}"
                )

    conn.commit()
    db.close()
    return {
        "dyno_curves_updated": curves_updated,
        "dyno_curves_inserted": curves_inserted,
        "headline_models_updated": headline_rows,
        "headline_cells_updated": headline_cells,
    }


if __name__ == "__main__":
    path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"config sync patch on {path}:")
    print(f"  {apply(path, verbose=True)}")
