#!/usr/bin/env python3
"""gen_stock_leaderboard.py — simulated stock times for every catalog bike.

Writes ``web/app/leaderboard/stock_times.json``, the data behind the site's
leaderboard. Each bike runs exactly as ``POST /api/simulate/quick`` runs it
with no options: stock, a 75 kg rider, the server's default conditions. The
board therefore shows only what the physics produces; visitors cannot post to
it.

It is a cache of the physics, like the regression snapshot and the instant
estimate model: regenerate it after any change that moves simulated times
(physics, defaults, category profiles, importer or catalog data), in the same
change. ``tests/test_stock_leaderboard.py`` fails when it is stale.

Usage
-----
    python scripts/gen_stock_leaderboard.py            # $MOTOQUANT_DB or motoquant.db
    python scripts/gen_stock_leaderboard.py --check    # exit 1 if the file is stale
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "web" / "app" / "leaderboard" / "stock_times.json"
sys.path.insert(0, str(REPO))


def _bikes(db_path: str) -> list[dict]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT bm.id, m.name AS manufacturer, bm.model_name, bm.year_from,
                      bm.year_to, bm.category, bm.displacement_cc
               FROM bike_models bm
               JOIN manufacturers m ON m.id = bm.manufacturer_id
               WHERE EXISTS (SELECT 1 FROM bike_configs bc
                             WHERE bc.bike_model_id = bm.id AND bc.is_current = 1)
               ORDER BY bm.id"""
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def build(db_path: str) -> dict:
    """Simulate every current bike the way the quick-simulation route does."""
    os.environ["MOTOQUANT_DB"] = db_path
    from motoquant import api, engine_select

    entries = []
    did_not_finish = []
    conditions = None
    for bike in _bikes(db_path):
        cfg = api._build_config(
            bike_id=bike["id"],
            bike_preset=None,
            power_boost_pct=0.0,
            mass_delta_kg=0.0,
            rider_mass_kg=75.0,
        )
        sim = engine_select.make_engine(cfg).run()
        if conditions is None:
            echo = api._environment_echo(cfg)
            conditions = {k: echo[k] for k in echo if k not in ("is_default", "source")}
        if not sim.finished_quarter:
            did_not_finish.append(bike["id"])  # out of time before the line
            continue
        entries.append(
            {
                "id": bike["id"],
                "manufacturer": bike["manufacturer"],
                "model": bike["model_name"],
                "year_from": bike["year_from"],
                "year_to": bike["year_to"],
                "category": bike["category"],
                "displacement_cc": bike["displacement_cc"],
                "et_s": round(float(sim.time_quarter), 3),
                "trap_kmh": round(float(sim.speed_quarter) * 3.6, 1),
            }
        )
    entries.sort(key=lambda e: (e["et_s"], e["id"]))
    return {
        "generated_by": "scripts/gen_stock_leaderboard.py",
        "rider_kg": 75,
        "conditions": conditions,
        "bikes": entries,
        "did_not_finish": did_not_finish,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 2)[1])
    ap.add_argument(
        "--db",
        default=os.environ.get("MOTOQUANT_DB", str(REPO / "motoquant.db")),
        help="catalog database (default: $MOTOQUANT_DB or motoquant.db)",
    )
    ap.add_argument("--check", action="store_true", help="exit 1 if the file is stale")
    args = ap.parse_args(argv)
    data = build(os.path.abspath(args.db))
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(
                f"{OUT.relative_to(REPO)} is stale; run scripts/gen_stock_leaderboard.py"
            )
            return 1
        print(f"{OUT.relative_to(REPO)} is current ({len(data['bikes'])} bikes)")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}: {len(data['bikes'])} bikes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
