#!/usr/bin/env python3
"""
Diagnose the dead-power / 22.034s R15 V3 bug (April 2026).
Usage:  MOTOQUANT_DB=/path/to/motoquant.db python3 scripts/diagnose_r15_db_path.py
"""
import copy
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import motoquant
from motoquant.database import MotoQuantDB
from motoquant.database.bridge import db_row_to_config
from motoquant.models import DynoCurve
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def find_r15_bike_id(db):
    rows = db.conn.execute(
        "SELECT bm.id, m.name as manuf, bm.model_name, bm.year_from "
        "FROM bike_models bm JOIN manufacturers m ON bm.manufacturer_id = m.id "
        "WHERE bm.model_name LIKE '%R15 V3%' OR bm.model_name LIKE '%YZF-R15%V3%' "
        "ORDER BY bm.id"
    ).fetchall()
    print("R15 V3 candidates in DB:", flush=True)
    for r in rows:
        d = dict(r)
        print("  id=%s %s %s %s" % (d['id'], d['manuf'], d['model_name'], d['year_from']), flush=True)
    return dict(rows[0])["id"] if rows else None


def load_db_config(db, bike_id):
    cfg_row = db.conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id = ? AND is_current = 1 "
        "ORDER BY version DESC LIMIT 1",
        (bike_id,),
    ).fetchone()
    if cfg_row is None:
        return None
    return db_row_to_config(dict(cfg_row), name="R15 V3 (DB)")


def load_spec_config():
    spec = next(
        (s for s in ALL_KNOWN_BIKES
         if "R15" in s.model_name and "V3" in s.model_name),
        None,
    )
    if spec is None:
        return None
    return spec_to_bike_config(spec)


def diff_engine(db_cfg, spec_cfg):
    fields = [
        "displacement_cc", "bore_mm", "stroke_mm",
        "peak_power_hp", "peak_power_rpm",
        "peak_torque_nm", "peak_torque_rpm",
        "idle_rpm", "redline_rpm",
        "stroke_type", "cylinder_count", "cylinder_config",
        "tuned_rpm", "powervalve",
    ]
    print("\n%-22s %-20s %-20s match" % ("field", "DB path", "spec path"), flush=True)
    print("-" * 72, flush=True)
    for f in fields:
        db_v = getattr(db_cfg.engine, f, "<missing>")
        sp_v = getattr(spec_cfg.engine, f, "<missing>")
        ok = "OK" if db_v == sp_v else "DIFF"
        print("%-22s %-20s %-20s %s" % (f, str(db_v), str(sp_v), ok), flush=True)


def check_failure_modes(cfg, label):
    print("\n=== Failure-mode check: %s ===" % label, flush=True)
    e = cfg.engine
    dc = e.dyno_curve
    if dc is None:
        print("  (a) dyno_curve is None -> 4T synthetic parabolic path will be used", flush=True)
    elif not isinstance(dc, DynoCurve):
        print("  (b) dyno_curve is %s, NOT DynoCurve" % type(dc).__name__, flush=True)
    else:
        print("  (a/b) dyno_curve OK: DynoCurve with %d points, is_at_wheel=%s" % (len(dc.rpm), dc.is_at_wheel), flush=True)
    if e.redline_rpm <= e.idle_rpm:
        print("  (c) BUG: redline_rpm (%s) <= idle_rpm (%s) -> get_torque returns 0" % (e.redline_rpm, e.idle_rpm), flush=True)
    else:
        print("  (c) RPM range OK: idle=%s, redline=%s" % (e.idle_rpm, e.redline_rpm), flush=True)
    if e.peak_torque_nm < 1.0:
        print("  (d) BUG: peak_torque_nm too small: %s" % e.peak_torque_nm, flush=True)
    else:
        print("  (d) peak_torque_nm OK: %s" % e.peak_torque_nm, flush=True)


def power_sweep(cfg, label):
    print("\n=== Power sweep: %s ===" % label, flush=True)
    print("%-8s %-10s %-10s %-8s %-10s" % ("boost%", "peak hp", "peak Nm", "ET (s)", "trap kmh"), flush=True)
    for boost in [0, 50, 100]:
        c = copy.deepcopy(cfg)
        if boost != 0:
            scale = 1.0 + boost / 100.0
            c.engine.peak_power_hp *= scale
            c.engine.peak_torque_nm *= scale
            if c.engine.dyno_curve is not None:
                c.engine.dyno_curve.torque_nm = c.engine.dyno_curve.torque_nm * scale
        r = motoquant.MotoQuantEngine(c).run(use_adaptive_dt=False, max_time=26.0)
        et = r.time_quarter if r.finished_quarter else float("nan")
        trap = getattr(r, "trap_speed_kmh", float("nan"))
        print("%-8s %-10.2f %-10.2f %-8.3f %-10.2f" % (boost, c.engine.peak_power_hp, c.engine.peak_torque_nm, et, trap), flush=True)


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    db = MotoQuantDB(db_path=db_path)
    try:
        db.connect()
    except Exception as exc:
        print("Cannot open DB at %s (%s)" % (db_path, exc), flush=True)
        return 2

    bike_id = find_r15_bike_id(db)
    if bike_id is None:
        print("No R15 V3 found in bike_models table.", flush=True)
        return 1

    db_cfg = load_db_config(db, bike_id)
    spec_cfg = load_spec_config()

    if db_cfg is None:
        print("No bike_configs row for bike_id=%s" % bike_id, flush=True)
        return 1
    if spec_cfg is None:
        print("No R15 V3 spec in ALL_KNOWN_BIKES", flush=True)
        return 1

    diff_engine(db_cfg, spec_cfg)
    check_failure_modes(db_cfg, "DB path")
    check_failure_modes(spec_cfg, "spec path")
    power_sweep(db_cfg, "DB path")
    power_sweep(spec_cfg, "spec path control")

    return 0


if __name__ == "__main__":
    sys.exit(main())
