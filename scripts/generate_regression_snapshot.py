#!/usr/bin/env python3
"""generate_regression_snapshot.py -- regenerate tests/data/sweep_snapshot.json.

This snapshot is the physics-drift tripwire. tests/test_regression_snapshot.py
re-runs the same sims (same bikes, same fixed-dt solver) and fails CI if any
quarter-mile ET or trap speed drifts past a tight tolerance. It would have
caught the R15-primary-ratio copy-paste bug the day it shipped, and the
"power_boost dead-knob" class where a sim output silently stops responding.

Captures: the 3 hand-curated REFERENCE bikes (K5/R1/Hayabusa, from defaults.py,
pinned to ZERO tolerance) plus a deterministic stratified ~35-bike CATALOG
sample loaded via the production DB path (live_db_copy -> bike_configs row ->
db_row_to_config), so it exercises the same code /api/simulate?bike_id=N hits.
Bikes are selected by (model_name, year_from) so the set survives re-seeds.

All sims use run(use_adaptive_dt=False, max_time=26.0) -- fixed 1 ms RK4 is
bit-deterministic. Regenerate ONLY when a physics change is intended:
    python scripts/generate_regression_snapshot.py
An unexpected test diff means the snapshot caught a drift -- investigate first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import motoquant  # noqa: E402
from motoquant.database.bridge import db_row_to_config  # noqa: E402
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402

# Stratified catalog sample: (model_name, year_from, cluster) matched exactly
# against bike_models so the set is stable across re-seeds. cluster is a label.
CATALOG_SAMPLE: list[tuple[str, int, str]] = [
    ("Hayabusa (2008-2012)", 2008, "litre_hyper"),
    ("Ninja ZX-14R (2012-2023)", 2012, "litre_hyper"),
    ("Ninja ZX-10R (2004-2005)", 2004, "litre_sport"),
    ("S 1000 RR (2015-2018)", 2015, "litre_sport"),
    ("Panigale V4 (2018-2024)", 2018, "litre_sport"),
    ("RSV4 1000 (2009-2014)", 2009, "litre_sport"),
    ("Ninja H2 (2015-2023)", 2015, "litre_super"),
    ("GSX-R 600 (2006-2007)", 2006, "sport_600_1000"),
    ("Ninja ZX-6R (2003-2004)", 2003, "sport_600_1000"),
    ("CBR 600RR (2007-2012)", 2007, "sport_600_1000"),
    ("YZF-R6 (2006-2007)", 2006, "sport_600_1000"),
    ("GSX-R 750 (2008-2010)", 2008, "sport_600_1000"),
    ("MT-07 (2018-2024)", 2018, "mid_twin"),
    ("SV650 (2016-2026)", 2016, "mid_twin"),
    ("RS 660 (2021-2026)", 2021, "mid_twin"),
    ("Tuono 660 (2021-2026)", 2021, "mid_twin"),
    ("Ninja 400 (2018-2024)", 2018, "entry_300"),
    ("YZF-R3 (2015-2022)", 2015, "entry_300"),
    ("Apache RR 310 (2018-2024)", 2018, "entry_300"),
    ("Duke 390 (2017-2023)", 2017, "entry_300"),
    ("Dominar 250 (2020-2024)", 2020, "entry_200"),
    ("Apache RTR 200 4V (2016-2024)", 2016, "entry_200"),
    ("Pulsar NS200 (2012-2016)", 2012, "entry_200"),
    ("YZF-R15 V4 (2021-2024)", 2021, "entry_150"),
    ("Classic 350 (2021-2026)", 2021, "cruiser"),
    ("Meteor 350 (2020-2026)", 2020, "cruiser"),
    ("Rocket 3 R (2020-2026)", 2020, "muscle"),
    ("VMAX 1700 (2009-2020)", 2009, "muscle"),
    ("Rebel 1100 (2021-2026)", 2021, "cruiser"),
    ("Diavel V4 (2023-2026)", 2023, "cruiser"),
    ("RD350 (1973-1975)", 1973, "two_stroke"),
    ("RX100 (1985-1996)", 1985, "two_stroke"),
    ("RGV250 Gamma (1991-1996)", 1991, "two_stroke"),
    ("NSR250R SP (1990-1993)", 1990, "two_stroke"),
    ("RG500 Gamma (1985-1987)", 1985, "two_stroke"),
]

REFERENCE_BIKES = [
    ("GSX-R 1000 K5", gsxr1000_k5),
    ("YZF-R1 4C8", yzfr1_4c8),
    ("Hayabusa Gen1", hayabusa_gen1),
]


def _run(config) -> dict:
    """Run one fixed-dt sim and extract the snapshot-relevant scalars."""
    r = motoquant.MotoQuantEngine(config).run(use_adaptive_dt=False, max_time=26.0)
    return {
        "et_s": round(float(r.time_quarter), 6),
        "trap_ms": round(float(r.speed_quarter), 6),
        "trap_kmh": round(float(r.speed_quarter) * 3.6, 4),
        "finished": bool(r.finished_quarter),
        "sixty_ft_s": round(float(r.time_60ft), 6),
        "eighth_s": round(float(r.time_eighth), 6),
    }


def _snapshot_all_current(db) -> dict[str, dict]:
    """Snapshot EVERY catalog bike that has a current config.

    Enumerates all ``bike_models`` joined to their ``is_current=1``
    ``bike_configs`` row, runs the deterministic fixed-dt sim, and keys the
    result by ``model_name|year_from`` (same key scheme as ``catalog``). The
    per-bike ``cluster`` label is the runtime ``category_tag`` for debugging;
    the full-tier test only asserts on ET/trap/finished, so the label is
    informational. This is the full-catalog tier -- ~500 bikes, ~3 min to run.
    """
    full: dict[str, dict] = {}
    rows = db.conn.execute(
        "SELECT bm.model_name AS model_name, bm.year_from AS year_from, bc.* "
        "FROM bike_models bm "
        "JOIN bike_configs bc ON bc.bike_model_id = bm.id AND bc.is_current = 1 "
        "ORDER BY bm.id"
    ).fetchall()
    for row in rows:
        d = dict(row)
        model_name = d["model_name"]
        year_from = d["year_from"]
        cfg = db_row_to_config(d, name=model_name)
        cluster = getattr(cfg, "category_tag", None) or "unknown"
        full[f"{model_name}|{year_from}"] = {"cluster": cluster, **_run(cfg)}
    return full


def build_snapshot(full: bool = True) -> dict:
    from tests._helpers import live_db_copy

    db = live_db_copy()
    if db is None:
        raise SystemExit(
            "FATAL: could not locate motoquant.db (set $MOTOQUANT_DB). "
            "The catalog snapshot cannot be generated without the seeded DB."
        )
    catalog: dict[str, dict] = {}
    catalog_full: dict[str, dict] = {}
    missing: list[str] = []
    try:
        for model_name, year_from, cluster in CATALOG_SAMPLE:
            row = db.conn.execute(
                "SELECT bm.id AS mid FROM bike_models bm "
                "WHERE bm.model_name = ? AND bm.year_from = ? "
                "ORDER BY bm.id LIMIT 1",
                (model_name, year_from),
            ).fetchone()
            if row is None:
                missing.append(f"{model_name} ({year_from})")
                continue
            mid = dict(row)["mid"]
            cfg_row = db.conn.execute(
                "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 "
                "ORDER BY version DESC LIMIT 1",
                (mid,),
            ).fetchone()
            if cfg_row is None:
                missing.append(f"{model_name} ({year_from}) [no current config]")
                continue
            cfg = db_row_to_config(dict(cfg_row), name=model_name)
            catalog[f"{model_name}|{year_from}"] = {"cluster": cluster, **_run(cfg)}
        if full:
            catalog_full = _snapshot_all_current(db)
    finally:
        db.close()
    if missing:
        raise SystemExit(
            "FATAL: curated bikes did not resolve against the DB:\n  "
            + "\n  ".join(missing)
            + "\nFix CATALOG_SAMPLE (name/year drift) before regenerating."
        )
    reference = {name: _run(factory()) for name, factory in REFERENCE_BIKES}
    snapshot = {
        "_comment": (
            "Golden regression snapshot. Regenerate with "
            "`python scripts/generate_regression_snapshot.py` ONLY when a physics "
            "change is intended. See tests/test_regression_snapshot.py. "
            "'catalog' is the always-on stratified sample; 'catalog_full' is every "
            "current-config bike, checked by the MOTOQUANT_SLOW_TESTS=1 tier."
        ),
        "sim_args": {"use_adaptive_dt": False, "max_time": 26.0},
        "reference": reference,
        "catalog": catalog,
    }
    if full:
        snapshot["catalog_full"] = catalog_full
    return snapshot


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate the regression snapshot.")
    ap.add_argument(
        "--out",
        default=str(_REPO_ROOT / "tests" / "data" / "sweep_snapshot.json"),
        help="Output JSON path (default: tests/data/sweep_snapshot.json).",
    )
    ap.add_argument(
        "--no-full",
        action="store_true",
        help=(
            "Skip the ~3-min full-catalog tier (dev convenience). If the output "
            "file already has a 'catalog_full', it is preserved so the guard never "
            "silently shrinks."
        ),
    )
    args = ap.parse_args()
    snapshot = build_snapshot(full=not args.no_full)
    out_path = Path(args.out)
    # Never silently drop the full tier: if --no-full was used but the existing
    # golden carries a catalog_full, carry it forward untouched.
    if args.no_full and out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as fh:
                prev = json.load(fh)
            if "catalog_full" in prev:
                snapshot["catalog_full"] = prev["catalog_full"]
                print("--no-full: preserved existing catalog_full from golden.")
        except (OSError, json.JSONDecodeError):
            pass
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(
        f"Wrote {out_path} -- {len(snapshot['reference'])} reference + "
        f"{len(snapshot['catalog'])} catalog + "
        f"{len(snapshot.get('catalog_full', {}))} full-catalog bikes."
    )
    for name, vals in snapshot["reference"].items():
        print(
            f"  REF {name:18s} ET={vals['et_s']:.4f}s trap={vals['trap_kmh']:.1f}km/h"
        )


if __name__ == "__main__":
    main()
