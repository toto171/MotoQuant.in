#!/usr/bin/env python3
"""
MotoQuant Pro — CLI Runner (Phase 2)
====================================
Full-featured CLI for quarter-mile simulations with database integration.

Phase 1 (legacy) commands — fully backward-compatible:
    python -m motoquant.run                              # All 3 built-in bikes
    python -m motoquant.run --bike k5                    # Built-in preset
    python -m motoquant.run --bike k5 --venue aamby-winter
    python -m motoquant.run --config my_bike.json        # JSON config
    python -m motoquant.run --export-config k5 k5.json   # Export config
    python -m motoquant.run --list                        # List legacy presets

Phase 2 (database) commands — new:
    python -m motoquant.run db init                       # Initialize database
    python -m motoquant.run db seed                       # Seed reference data
    python -m motoquant.run db stats                      # Show counts

    python -m motoquant.run bikes                         # List all bikes in DB
    python -m motoquant.run bikes --search "hayabusa"     # Search by name
    python -m motoquant.run bikes --category sport --displacement 900-1300

    python -m motoquant.run sim --bike-id 3               # Sim from DB
    python -m motoquant.run sim --bike-id 3 --venue-id 1 --month 1
    python -m motoquant.run sim --bike-id 3 --weather-live
    python -m motoquant.run sim --bike-id 3 --apply-parts 5,8,12
    python -m motoquant.run sim --bike-id 3 --apply-parts 5 --compare-stock
    python -m motoquant.run sim --bike-id 3 --save-run

    python -m motoquant.run venues                        # List venues
    python -m motoquant.run venues --detail 1             # Venue + seasonal DA

    python -m motoquant.run tires                         # List tires
    python -m motoquant.run tires --grip-rank             # Rank by grip
    python -m motoquant.run tires --value-rank            # Rank by grip/rupee

    python -m motoquant.run parts                         # List parts
    python -m motoquant.run parts --category sprocket
    python -m motoquant.run parts --build-cost 3,5,8,12   # Total cost

    python -m motoquant.run weather --venue-id 1          # Latest weather
    python -m motoquant.run weather --venue-id 1 --fetch  # Fetch live
    python -m motoquant.run weather --venue-id 1 --da-trend

    python -m motoquant.run leaderboard                   # Best ETs
    python -m motoquant.run history --bike-id 3            # Run history
"""

import argparse
import csv
import json
import sys
import time
import os
import numpy as np
from pathlib import Path
from datetime import datetime

from .models import BikeConfig, EnvironmentParams
from .physics import (
    MotoQuantEngine, SimResult,
    QUARTER_MILE_M, EIGHTH_MILE_M, MS_TO_KMH, MS_TO_MPH, G,
)
from .defaults import (
    gsxr1000_k5, yzfr1_4c8, hayabusa_gen1,
    aamby_valley_winter, aamby_valley_summer,
)
from .config_io import save_config, load_config

__all__ = ["main"]

# Default database path (next to the motoquant package)
DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "motoquant.db")

# ═══════════════════════════════════════════
# PHASE 1 LEGACY REGISTRIES (backward compat)
# ═══════════════════════════════════════════

BIKE_REGISTRY = {
    "k5":   ("Suzuki GSX-R 1000 K5/K6", gsxr1000_k5),
    "r1":   ("Yamaha YZF-R1 4C8",       yzfr1_4c8),
    "busa": ("Suzuki Hayabusa Gen1",     hayabusa_gen1),
}

BIKE_ALIASES = {
    "gsxr": "k5", "gsxr1000": "k5", "gsxr-1000": "k5",
    "yzfr1": "r1", "4c8": "r1", "crossplane": "r1",
    "hayabusa": "busa", "gsx1300": "busa", "gsx1300r": "busa",
}

VENUE_REGISTRY = {
    "aamby-winter": ("Aamby Valley (TVR Winter)", aamby_valley_winter),
    "aamby-summer": ("Aamby Valley (TVR Summer)", aamby_valley_summer),
}


def resolve_bike(name: str) -> str:
    name = name.lower().strip()
    return BIKE_ALIASES.get(name, name)


# ═══════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════

def get_db(args):
    """Lazily open the MotoQuant database."""
    from .database import MotoQuantDB
    db_path = getattr(args, "db", None) or os.environ.get("MOTOQUANT_DB", DEFAULT_DB_PATH)
    return MotoQuantDB(db_path)


def ensure_db(args):
    """Open DB and ensure it's initialized."""
    db = get_db(args)
    db.initialize()
    return db


# ═══════════════════════════════════════════
# OUTPUT FORMATTING
# ═══════════════════════════════════════════

def print_banner():
    from . import __version__
    print(f"\n{'='*72}")
    print(f"  MotoQuant Pro v{__version__} — Motorcycle Drag Racing Simulation Engine")
    print(f"  15 sub-models | RK4 @ 1ms | Phase 2 Database-Integrated")
    print(f"{'='*72}")


def print_result(config: BikeConfig, result: SimResult, elapsed_ms: float,
                 label: str = None, compact: bool = False):
    """Print a complete simulation result in human-readable format."""
    title = label or config.name
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"  Venue: {config.environment.venue_name}")
    print(f"{'='*72}")

    env = config.environment
    rho = env.air_density()
    da = env.density_altitude_ft()
    print(f"\n  Environment:")
    print(f"    Altitude:          {env.altitude_m:.0f} m")
    print(f"    Air temp:          {env.ambient_temp_c:.1f} C")
    print(f"    Humidity:          {env.relative_humidity_pct:.0f}%")
    print(f"    Air density:       {rho:.4f} kg/m3")
    print(f"    Density altitude:  {da:.0f} ft")
    if env.wind_speed_ms > 0:
        print(f"    Wind:              {env.wind_speed_ms:.1f} m/s @ {env.wind_direction_deg:.0f} deg")
    if env.track_gradient_pct != 0:
        print(f"    Track gradient:    {env.track_gradient_pct:+.2f}%")

    # Split times
    print(f"\n  {'Split':<16} {'Time':>8}   {'Speed (km/h)':>12}  {'Speed (mph)':>11}")
    print(f"  {'-'*52}")
    splits = [
        ("60-foot",    result.time_60ft,    result.speed_60ft),
        ("330-foot",   result.time_330ft,   result.speed_330ft),
        ("1/8 mile",   result.time_eighth,  result.speed_eighth),
        ("1000-foot",  result.time_1000ft,  result.speed_1000ft),
        ("1/4 mile",   result.time_quarter, result.speed_quarter),
    ]
    for name, t, s in splits:
        if t > 0:
            print(f"  {name:<16} {t:.3f} s  {s * MS_TO_KMH:8.1f} km/h  {s * MS_TO_MPH:8.1f} mph")

    if not compact:
        # Performance metrics
        print(f"\n  Performance Metrics:")
        if len(result.a) > 0:
            print(f"    Peak acceleration:   {np.max(result.a):.2f} g")
        if len(result.rpm) > 0:
            print(f"    Peak RPM:            {np.max(result.rpm):.0f}")
        if len(result.power_kw) > 0:
            pk = np.max(result.power_kw)
            print(f"    Peak wheel power:    {pk:.1f} kW ({pk * 1.341:.1f} HP)")
        if len(result.gear) > 0:
            print(f"    Gears used:          1-{int(np.max(result.gear))}")
        if len(result.T_tire) > 0:
            print(f"    Tire temp range:     {np.min(result.T_tire):.1f} - {np.max(result.T_tire):.1f} C")
        if len(result.traction_pct) > 0:
            print(f"    Peak traction use:   {np.max(result.traction_pct):.1f}%")

        engine = MotoQuantEngine(config)
        m_eff = engine.effective_mass(0)
        print(f"    Effective mass (1st): {m_eff:.1f} kg ({m_eff/config.chassis.total_mass_kg*100:.1f}% of static)")
        a_wheelie = engine.max_accel_before_wheelie(0, 0)
        print(f"    Wheelie limit:       {a_wheelie/G:.2f} g ({a_wheelie:.1f} m/s2)")

    print(f"\n  Simulation: {len(result.t)} steps, {elapsed_ms:.1f} ms runtime, dt={result.dt*1000:.1f} ms")
    print()


def result_to_dict(config: BikeConfig, result: SimResult) -> dict:
    """Convert simulation result to a JSON-serializable dict."""
    return {
        "bike": config.name,
        "venue": config.environment.venue_name,
        "environment": {
            "altitude_m": config.environment.altitude_m,
            "ambient_temp_c": config.environment.ambient_temp_c,
            "humidity_pct": config.environment.relative_humidity_pct,
            "air_density_kgm3": config.environment.air_density(),
            "density_altitude_ft": config.environment.density_altitude_ft(),
        },
        "splits": {
            "sixty_foot_s": round(result.time_60ft, 4),
            "sixty_foot_kmh": round(result.speed_60ft * MS_TO_KMH, 2),
            "three30_foot_s": round(result.time_330ft, 4),
            "eighth_mile_s": round(result.time_eighth, 4),
            "eighth_mile_kmh": round(result.speed_eighth * MS_TO_KMH, 2),
            "thousand_foot_s": round(result.time_1000ft, 4),
            "quarter_mile_s": round(result.time_quarter, 4),
            "quarter_mile_kmh": round(result.speed_quarter * MS_TO_KMH, 2),
            "quarter_mile_mph": round(result.speed_quarter * MS_TO_MPH, 2),
        },
        "metrics": {
            "peak_accel_g": round(float(np.max(result.a)), 3) if len(result.a) > 0 else 0,
            "peak_rpm": int(np.max(result.rpm)) if len(result.rpm) > 0 else 0,
            "peak_power_kw": round(float(np.max(result.power_kw)), 2) if len(result.power_kw) > 0 else 0,
            "peak_power_hp": round(float(np.max(result.power_kw)) * 1.341, 1) if len(result.power_kw) > 0 else 0,
            "gears_used": int(np.max(result.gear)) if len(result.gear) > 0 else 0,
            "tire_temp_min_c": round(float(np.min(result.T_tire)), 1) if len(result.T_tire) > 0 else 0,
            "tire_temp_max_c": round(float(np.max(result.T_tire)), 1) if len(result.T_tire) > 0 else 0,
            "peak_traction_pct": round(float(np.max(result.traction_pct)), 1) if len(result.traction_pct) > 0 else 0,
        },
        "simulation": {
            "steps": len(result.t),
            "dt_ms": result.dt * 1000,
        },
    }


def export_csv(result: SimResult, path: str):
    """Export full time-history data to CSV for post-processing."""
    n = len(result.t)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "position_m", "velocity_ms", "velocity_kmh",
            "accel_g", "rpm", "gear", "slip_ratio", "traction_pct",
            "N_front_N", "N_rear_N", "F_drive_N", "F_drag_N", "F_rr_N",
            "tire_temp_C", "clutch_temp_C", "boost_bar",
            "power_kw", "r_eff_m",
        ])
        for i in range(n):
            writer.writerow([
                f"{result.t[i]:.4f}",
                f"{result.x[i]:.4f}",
                f"{result.v[i]:.4f}",
                f"{result.v[i] * MS_TO_KMH:.2f}",
                f"{result.a[i]:.4f}",
                f"{result.rpm[i]:.0f}",
                f"{result.gear[i]:.0f}",
                f"{result.slip[i]:.6f}",
                f"{result.traction_pct[i]:.2f}",
                f"{result.N_front[i]:.1f}",
                f"{result.N_rear[i]:.1f}",
                f"{result.F_drive[i]:.1f}",
                f"{result.F_drag[i]:.1f}",
                f"{result.F_rr[i]:.1f}",
                f"{result.T_tire[i]:.2f}",
                f"{result.T_clutch[i]:.2f}",
                f"{result.P_boost[i]:.4f}",
                f"{result.power_kw[i]:.3f}",
                f"{result.r_eff[i]:.5f}",
            ])
    print(f"  Time-history exported: {path} ({n} rows x 19 channels)")


def print_comparison(entries, results):
    """Print a side-by-side comparison table. entries = [(label, config), ...]"""
    print(f"\n{'='*72}")
    print("  COMPARISON TABLE")
    print(f"{'='*72}")
    print(f"\n  {'Metric':<20}", end="")
    for label, _ in entries:
        short = label[:14]
        print(f"  {short:>14}", end="")
    print()
    print(f"  {'-'*20}", end="")
    for _ in entries:
        print(f"  {'-'*14}", end="")
    print()

    metrics = [
        ("60-ft (s)",         lambda r: f"{r.time_60ft:.3f}"),
        ("1/8 mile ET (s)",   lambda r: f"{r.time_eighth:.3f}"),
        ("1/4 mile ET (s)",   lambda r: f"{r.time_quarter:.3f}"),
        ("Trap speed (km/h)", lambda r: f"{r.speed_quarter * MS_TO_KMH:.1f}"),
        ("Trap speed (mph)",  lambda r: f"{r.speed_quarter * MS_TO_MPH:.1f}"),
        ("Peak accel (g)",    lambda r: f"{np.max(r.a):.2f}" if len(r.a) > 0 else "N/A"),
        ("Peak power (HP)",   lambda r: f"{np.max(r.power_kw) * 1.341:.0f}" if len(r.power_kw) > 0 else "N/A"),
    ]

    for label, fn in metrics:
        print(f"  {label:<20}", end="")
        for entry_label, _ in entries:
            print(f"  {fn(results[entry_label]):>14}", end="")
        print()

    # Delta row if exactly 2 entries (stock vs modified)
    if len(entries) == 2:
        r_a = results[entries[0][0]]
        r_b = results[entries[1][0]]
        dt = r_b.time_quarter - r_a.time_quarter
        ds = (r_b.speed_quarter - r_a.speed_quarter) * MS_TO_KMH
        print(f"\n  Delta (QM ET):    {dt:+.3f} s")
        print(f"  Delta (trap):     {ds:+.1f} km/h")
    print()


# ═══════════════════════════════════════════
# SIMULATION RUNNER
# ═══════════════════════════════════════════

def run_bike(config: BikeConfig, dt: float = 0.001,
             distance: float = QUARTER_MILE_M, verbose: bool = True,
             label: str = None) -> SimResult:
    """Run simulation for a single bike configuration."""
    engine = MotoQuantEngine(config, dt=dt)
    t0 = time.perf_counter()
    result = engine.run(distance=distance, max_time=20.0)
    elapsed = (time.perf_counter() - t0) * 1000.0
    if verbose:
        print_result(config, result, elapsed, label=label)
    return result


def archive_run(db, config_id, venue_id, weather_id, result, parts_ids=None):
    """Save a simulation result to the database."""
    from . import __version__
    return db.sim_runs.record(
        bike_config_id=config_id,
        venue_id=venue_id,
        weather_record_id=weather_id,
        et_quarter_s=result.time_quarter,
        trap_speed_kmh=result.speed_quarter * MS_TO_KMH,
        et_eighth_s=result.time_eighth,
        speed_eighth_kmh=result.speed_eighth * MS_TO_KMH,
        time_60ft_s=result.time_60ft,
        speed_60ft_kmh=result.speed_60ft * MS_TO_KMH,
        time_330ft_s=result.time_330ft,
        time_1000ft_s=result.time_1000ft,
        sim_version=__version__,
        dt_s=result.dt,
        distance_m=result.x[-1] if len(result.x) > 0 else 0,
        split_times={
            "time_60ft": result.time_60ft,
            "time_330ft": result.time_330ft,
            "time_eighth": result.time_eighth,
            "time_1000ft": result.time_1000ft,
            "time_quarter": result.time_quarter,
            "speed_quarter_kmh": result.speed_quarter * MS_TO_KMH,
        },
        applied_parts=parts_ids,
    )


# ═══════════════════════════════════════════
# TABLE PRINTER
# ═══════════════════════════════════════════

def print_table(headers, rows, col_widths=None):
    """Generic table printer for CLI output."""
    if not col_widths:
        col_widths = []
        for i, h in enumerate(headers):
            w = len(h)
            for row in rows:
                if i < len(row):
                    w = max(w, len(str(row[i])))
            col_widths.append(min(w + 2, 40))

    # Header
    header_line = ""
    for h, w in zip(headers, col_widths):
        header_line += f"  {h:<{w}}"
    print(f"\n{header_line}")
    sep = ""
    for w in col_widths:
        sep += f"  {'-'*w}"
    print(sep)

    # Rows
    for row in rows:
        line = ""
        for val, w in zip(row, col_widths):
            s = str(val) if val is not None else "-"
            line += f"  {s:<{w}}"
        print(line)
    print()


# ═══════════════════════════════════════════
# SUBCOMMAND HANDLERS
# ═══════════════════════════════════════════

def cmd_db(args):
    """Handle 'db' subcommand: init, seed, stats."""
    action = args.db_action

    if action == "init":
        db = get_db(args)
        db.initialize()
        print(f"  Database initialized: {db.path}")
        print(f"  Schema version: 1")
        stats = db.stats()
        print(f"  Venues seeded: {stats['venues']}")
        print(f"  Seasonal records: {stats['venue_seasonal']}")
        print(f"  Parts categories: {stats.get('parts_categories', 0)}")
        db.close()

    elif action == "seed":
        db = ensure_db(args)
        from .database.seed import seed_all
        counts = seed_all(db)
        print(f"\n  Database seeded:")
        print(f"    Bikes:  {counts['bikes']} reference platforms")
        print(f"    Tires:  {counts['tires']} models")
        print(f"    Parts:  {counts['parts']} performance parts")
        stats = db.stats()
        print(f"\n  Total records:")
        for table, count in stats.items():
            if count > 0:
                print(f"    {table:20s}  {count}")
        db.close()

    elif action == "stats":
        db = ensure_db(args)
        stats = db.stats()
        print(f"\n  MotoQuant Database: {db.path}")
        print(f"  {'Table':20s}  {'Count':>6}")
        print(f"  {'-'*30}")
        for table, count in stats.items():
            print(f"  {table:20s}  {count:6d}")
        db.close()

    else:
        print(f"  Unknown db action: {action}")
        print(f"  Available: init, seed, stats")


def cmd_bikes(args):
    """Handle 'bikes' subcommand: list/search bikes from DB."""
    db = ensure_db(args)

    search_kwargs = {}
    if args.search:
        search_kwargs["name_contains"] = args.search
    if args.manufacturer:
        search_kwargs["manufacturer"] = args.manufacturer
    if args.category:
        search_kwargs["category"] = args.category
    if args.displacement:
        # Parse "900-1300" or "1000"
        parts = args.displacement.split("-")
        if len(parts) == 2:
            search_kwargs["displacement_min"] = float(parts[0])
            search_kwargs["displacement_max"] = float(parts[1])
        else:
            search_kwargs["displacement_min"] = float(parts[0]) - 50
            search_kwargs["displacement_max"] = float(parts[0]) + 50
    if args.power_min:
        search_kwargs["power_min"] = args.power_min
    if args.quality:
        search_kwargs["data_quality"] = args.quality

    results = db.bikes.search(**search_kwargs, limit=args.limit or 50)

    if not results:
        print("\n  No bikes found matching criteria.")
        print("  Try: python -m motoquant.run db seed  (to populate reference bikes)")
        db.close()
        return

    if args.json_out:
        print(json.dumps(results, indent=2, default=str))
    else:
        headers = ["ID", "Manufacturer", "Model", "Code", "Years", "cc", "HP", "Mass", "Quality", "ET (val)"]
        rows = []
        for b in results:
            years = ""
            if b.get("year_from"):
                years = str(b["year_from"])
                if b.get("year_to") and b["year_to"] != b["year_from"]:
                    years += f"-{b['year_to']}"
            et = f"{b['validation_et_s']:.2f}" if b.get("validation_et_s") else "-"
            rows.append([
                b["id"],
                b.get("manufacturer_name", "-"),
                b["model_name"],
                b.get("model_code") or "-",
                years or "-",
                f"{b['displacement_cc']:.0f}" if b.get("displacement_cc") else "-",
                f"{b['peak_power_hp']:.0f}" if b.get("peak_power_hp") else "-",
                f"{b['dry_mass_kg']:.0f}" if b.get("dry_mass_kg") else "-",
                b.get("data_quality", "-"),
                et,
            ])
        print(f"\n  Bikes ({len(results)} results):")
        print_table(headers, rows)

    db.close()


def cmd_sim(args):
    """Handle 'sim' subcommand: run simulation from DB."""
    output_json = args.json_out
    verbose = not args.quiet and not output_json

    # ── Resolve bike config ──
    if args.bike_id:
        db = ensure_db(args)
        config_row = db.bikes.get_current_config(args.bike_id)
        if config_row is None:
            print(f"  Error: no config found for bike model ID {args.bike_id}")
            db.close()
            sys.exit(1)
        config_id = config_row["id"]

        # Resolve environment
        env = None
        venue_id = args.venue_id
        weather_id = None

        if args.weather_live and venue_id:
            api_key = args.api_key or os.environ.get("OPENWEATHERMAP_API_KEY")
            if api_key:
                weather_id = db.weather.fetch_live(venue_id, api_key=api_key,
                                                    track_temp_c=args.track_temp)
                if weather_id:
                    env = db.weather.to_environment(weather_id)
                    if verbose:
                        wr = db.weather.get(weather_id)
                        print(f"\n  Live weather fetched for venue {venue_id}:")
                        print(f"    Temp: {wr['ambient_temp_c']:.1f} C | "
                              f"RH: {wr['relative_humidity_pct']:.0f}% | "
                              f"DA: {wr['density_altitude_ft']:.0f} ft | "
                              f"PCF: {wr['power_correction_factor']:.4f}")
                else:
                    print("  Warning: live weather fetch failed, using seasonal data")
            else:
                print("  Warning: no API key set (OPENWEATHERMAP_API_KEY). Using seasonal data.")

        if env is None and venue_id:
            month = args.month or datetime.now().month
            env = db.venues.to_environment(venue_id, month=month)

        config = db.bikes.to_config(config_id, environment=env)
        if config is None:
            print(f"  Error: could not reconstruct config ID {config_id}")
            db.close()
            sys.exit(1)

        # ── Apply parts ──
        parts_ids = []
        if args.apply_parts:
            from .database.bridge import apply_part_to_config
            parts_ids = [int(p.strip()) for p in args.apply_parts.split(",")]
            for pid in parts_ids:
                part = db.parts.get(pid)
                if part is None:
                    print(f"  Warning: part ID {pid} not found, skipping")
                    continue
                config = apply_part_to_config(config, part)
                if verbose:
                    print(f"  Applied: {part['brand']} {part['model_name']} "
                          f"({part['category_display']})"
                          f"{'  INR ' + str(int(part.get('price_inr') or 0)) if part.get('price_inr') else ''}")

        # ── Run simulation ──
        if verbose and not output_json:
            print_banner()

        label_mod = config.name
        if parts_ids:
            label_mod += f"  [+{len(parts_ids)} mods]"

        result = run_bike(config, dt=args.dt, distance=args.distance,
                          verbose=verbose, label=label_mod)

        # ── Compare stock ──
        if args.compare_stock and parts_ids:
            stock_config = db.bikes.to_config(config_id, environment=env)
            stock_result = run_bike(stock_config, dt=args.dt, distance=args.distance,
                                    verbose=verbose, label=f"{stock_config.name}  [STOCK]")
            entries = [
                (f"{stock_config.name} [STOCK]", stock_config),
                (label_mod, config),
            ]
            comparison_results = {
                f"{stock_config.name} [STOCK]": stock_result,
                label_mod: result,
            }
            print_comparison(entries, comparison_results)

            # Build cost
            cost_info = db.parts.estimate_build_cost(parts_ids, "inr")
            print(f"  Build cost: INR {cost_info['total']:,.0f}")
            if cost_info["unavailable_count"] > 0:
                print(f"  ({cost_info['unavailable_count']} parts not in stock)")
            dt_et = result.time_quarter - stock_result.time_quarter
            if cost_info["total"] > 0 and dt_et < 0:
                cost_per_tenth = cost_info["total"] / (abs(dt_et) * 10)
                print(f"  Cost per 0.1s ET gain: INR {cost_per_tenth:,.0f}")

        # ── Save run ──
        if args.save_run:
            run_id = archive_run(db, config_id, venue_id, weather_id,
                                  result, parts_ids or None)
            if verbose:
                print(f"  Run archived: ID {run_id}")

        # ── CSV export ──
        if args.csv:
            export_csv(result, args.csv)

        # ── JSON output ──
        if output_json:
            out = result_to_dict(config, result)
            out["config_id"] = config_id
            if venue_id:
                out["venue_id"] = venue_id
            if weather_id:
                out["weather_record_id"] = weather_id
            if parts_ids:
                out["applied_parts"] = parts_ids
            print(json.dumps(out, indent=2))

        db.close()
        return result

    elif args.bike_legacy:
        # Phase 1 legacy: --bike k5 etc.
        key = resolve_bike(args.bike_legacy)
        if key not in BIKE_REGISTRY:
            print(f"  Error: unknown bike '{args.bike_legacy}'")
            print(f"  Available: {', '.join(BIKE_REGISTRY.keys())}")
            sys.exit(1)
        config = BIKE_REGISTRY[key][1]()

        if args.venue_legacy:
            if args.venue_legacy not in VENUE_REGISTRY:
                print(f"  Error: unknown venue '{args.venue_legacy}'")
                sys.exit(1)
            VENUE_REGISTRY[args.venue_legacy][1](config)

        if verbose:
            print_banner()
        result = run_bike(config, dt=args.dt, distance=args.distance, verbose=verbose)
        if args.csv:
            export_csv(result, args.csv)
        if output_json:
            print(json.dumps(result_to_dict(config, result), indent=2))
        return result

    elif args.config_file:
        config = load_config(args.config_file)
        if verbose:
            print_banner()
        result = run_bike(config, dt=args.dt, distance=args.distance, verbose=verbose)
        if args.csv:
            export_csv(result, args.csv)
        if output_json:
            print(json.dumps(result_to_dict(config, result), indent=2))
        return result

    else:
        print("  Error: specify --bike-id, --bike, or --config")
        sys.exit(1)


def cmd_venues(args):
    """Handle 'venues' subcommand."""
    db = ensure_db(args)

    if args.detail is not None:
        venue = db.venues.get(args.detail)
        if venue is None:
            print(f"  Venue ID {args.detail} not found.")
            db.close()
            return

        print(f"\n  {venue['name']}")
        print(f"  {'='*50}")
        print(f"  City:      {venue.get('city', '-')}, {venue.get('state', '-')}")
        print(f"  Country:   {venue.get('country', '-')}")
        print(f"  Altitude:  {venue['altitude_m']:.0f} m")
        lat = venue.get('latitude')
        lon = venue.get('longitude')
        if lat and lon:
            print(f"  Coords:    {lat:.4f}, {lon:.4f}")
        print(f"  Surface:   {venue.get('surface_type', '-')}")
        print(f"  Timing:    {'Yes' if venue.get('has_timing_system') else 'No'}"
              f" ({venue.get('timing_system_type', '-')})")
        print(f"  VHT:       {'Yes' if venue.get('has_vht') else 'No'}")

        # Seasonal DA table
        seasonal = db.venues.get_all_seasonal(args.detail)
        if seasonal:
            print(f"\n  Monthly Density Altitude (ft) & Conditions:")
            headers = ["Month", "Temp C", "RH %", "Press hPa", "Wind m/s", "DA ft"]
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            rows = []
            for s in seasonal:
                m = s["month"]
                rows.append([
                    month_names[m - 1],
                    f"{s['avg_temp_c']:.0f}",
                    f"{s['avg_humidity_pct']:.0f}",
                    f"{s['avg_pressure_hpa']:.0f}",
                    f"{s['avg_wind_speed_ms']:.1f}",
                    f"{s['avg_density_alt_ft']:.0f}",
                ])
            print_table(headers, rows)

            best = db.venues.best_da_month(args.detail)
            worst = db.venues.worst_da_month(args.detail)
            if best and worst:
                print(f"  Best month:  {month_names[best['month']-1]} "
                      f"(DA {best['avg_density_alt_ft']:.0f} ft)")
                print(f"  Worst month: {month_names[worst['month']-1]} "
                      f"(DA {worst['avg_density_alt_ft']:.0f} ft)")
                delta = worst['avg_density_alt_ft'] - best['avg_density_alt_ft']
                print(f"  Seasonal DA swing: {delta:.0f} ft")
    else:
        venues = db.venues.list_all(
            country=args.country,
            active_only=not args.include_inactive,
        )
        if not venues:
            print("  No venues found. Run: python -m motoquant.run db init")
        else:
            headers = ["ID", "Name", "City", "State", "Alt (m)", "Surface", "Timing"]
            rows = []
            for v in venues:
                rows.append([
                    v["id"],
                    v["name"],
                    v.get("city") or "-",
                    v.get("state") or "-",
                    f"{v['altitude_m']:.0f}",
                    v.get("surface_type") or "-",
                    "Yes" if v.get("has_timing_system") else "No",
                ])
            print(f"\n  Venues ({len(venues)} total):")
            print_table(headers, rows)

    db.close()


def cmd_tires(args):
    """Handle 'tires' subcommand."""
    db = ensure_db(args)

    if args.grip_rank:
        results = db.tires.rank_by_grip(
            position=args.position or "rear",
            compound_type=args.compound,
        )
        if not results:
            print("  No tires found. Run: python -m motoquant.run db seed")
        else:
            headers = ["ID", "Manufacturer", "Model", "Size", "Compound",
                       "mu_peak", "Conf", "Weighted", "INR"]
            rows = []
            for t in results:
                rows.append([
                    t["id"],
                    t["manufacturer_name"],
                    t["model_name"],
                    t["size_designation"],
                    t["compound_type"],
                    f"{t['mu_peak']:.2f}" if t.get("mu_peak") else "-",
                    f"{t.get('confidence', 0):.2f}",
                    f"{t.get('weighted_grip', 0):.3f}",
                    f"{int(t['price_inr']):,}" if t.get("price_inr") else "-",
                ])
            print(f"\n  Tire Grip Ranking (weighted by confidence):")
            print_table(headers, rows)

    elif args.value_rank:
        results = db.tires.rank_by_value(position=args.position or "rear")
        if not results:
            print("  No Indian-available tires with pricing found.")
        else:
            headers = ["ID", "Manufacturer", "Model", "mu_peak", "INR", "Grip/1K INR"]
            rows = []
            for t in results:
                rows.append([
                    t["id"],
                    t["manufacturer_name"],
                    t["model_name"],
                    f"{t['mu_peak']:.2f}",
                    f"{int(t['price_inr']):,}",
                    f"{t['grip_per_1k_inr']:.4f}",
                ])
            print(f"\n  Tire Value Ranking (Indian market, grip per INR 1000):")
            print_table(headers, rows)

    else:
        search_kwargs = {}
        if args.compound:
            search_kwargs["compound_type"] = args.compound
        if args.position:
            search_kwargs["position"] = args.position
        if args.manufacturer:
            search_kwargs["manufacturer"] = args.manufacturer
        if args.india_only:
            search_kwargs["available_india"] = True

        results = db.tires.search(**search_kwargs)
        if not results:
            print("  No tires found. Run: python -m motoquant.run db seed")
        else:
            headers = ["ID", "Manufacturer", "Model", "Size", "Type", "Pos",
                       "mu", "INR", "India"]
            rows = []
            for t in results:
                rows.append([
                    t["id"],
                    t["manufacturer_name"],
                    t["model_name"],
                    t["size_designation"],
                    t["compound_type"],
                    t["position"],
                    f"{t['mu_peak']:.2f}" if t.get("mu_peak") else "-",
                    f"{int(t['price_inr']):,}" if t.get("price_inr") else "-",
                    "Y" if t.get("available_india") else "N",
                ])
            print(f"\n  Tires ({len(results)} results):")
            print_table(headers, rows)

    db.close()


def cmd_parts(args):
    """Handle 'parts' subcommand."""
    db = ensure_db(args)

    if args.build_cost:
        part_ids = [int(p.strip()) for p in args.build_cost.split(",")]
        cost = db.parts.estimate_build_cost(part_ids, "inr")
        print(f"\n  Build Cost Estimate:")
        print(f"  {'Part':<40} {'Category':<14} {'INR':>10} {'Avail':>6}")
        print(f"  {'-'*74}")
        for p in cost["parts"]:
            avail = "Yes" if p["available"] else "No"
            print(f"  {p['name']:<40} {p['category']:<14} {p['price']:>10,.0f} {avail:>6}")
        print(f"  {'-'*74}")
        print(f"  {'TOTAL':<56} {cost['total']:>10,.0f} {cost['currency']}")
        if cost["unavailable_count"] > 0:
            print(f"  ({cost['unavailable_count']} item(s) not in stock)")
    else:
        search_kwargs = {}
        if args.category:
            search_kwargs["category"] = args.category
        if args.brand:
            search_kwargs["brand"] = args.brand
        if args.search:
            search_kwargs["name_contains"] = args.search
        if args.max_price:
            search_kwargs["max_price_inr"] = args.max_price
        if args.available:
            search_kwargs["available_only"] = True

        results = db.parts.search(**search_kwargs)
        if not results:
            print("  No parts found. Run: python -m motoquant.run db seed")
        else:
            headers = ["ID", "Category", "Brand", "Model", "INR", "Avail"]
            rows = []
            for p in results:
                rows.append([
                    p["id"],
                    p["category_display"],
                    p["brand"],
                    p["model_name"],
                    f"{int(p['price_inr']):,}" if p.get("price_inr") else "-",
                    p.get("availability", "-"),
                ])
            print(f"\n  Parts ({len(results)} results):")
            print_table(headers, rows)

    db.close()


def cmd_weather(args):
    """Handle 'weather' subcommand."""
    db = ensure_db(args)

    # ── refresh-all: poll every venue ──────────────────────────────────────
    if getattr(args, "refresh_all", False):
        from .database.weather_refresh import refresh_all_venues

        api_key = getattr(args, "api_key", None) or os.environ.get("OPENWEATHERMAP_API_KEY")
        stale = getattr(args, "stale_minutes", 60)
        venue_ids = getattr(args, "venue_ids_filter", None)

        print(f"\n  Refreshing weather for all venues  (stale_threshold={stale}min)…")
        print("  " + "─" * 60)

        summary = refresh_all_venues(
            db=db,
            api_key=api_key,
            stale_minutes=stale,
            venue_ids=venue_ids,
        )

        print(str(summary))
        db.close()
        return

    venue_id = args.venue_id

    if not venue_id:
        print("  Error: --venue-id required for weather commands (or use --refresh-all)")
        db.close()
        sys.exit(1)

    venue = db.venues.get(venue_id)
    if venue is None:
        print(f"  Venue ID {venue_id} not found.")
        db.close()
        return

    if args.fetch:
        api_key = args.api_key or os.environ.get("OPENWEATHERMAP_API_KEY")
        if not api_key:
            print("  Error: set OPENWEATHERMAP_API_KEY or use --api-key")
            db.close()
            sys.exit(1)
        record_id = db.weather.fetch_live(venue_id, api_key=api_key,
                                           track_temp_c=args.track_temp)
        if record_id:
            wr = db.weather.get(record_id)
            print(f"\n  Live weather fetched for {venue['name']}:")
            print(f"    Temp:         {wr['ambient_temp_c']:.1f} C")
            print(f"    Humidity:     {wr['relative_humidity_pct']:.0f}%")
            print(f"    Pressure:     {wr['barometric_pressure_hpa']:.1f} hPa")
            print(f"    Dew point:    {wr['dew_point_c']:.1f} C")
            print(f"    Wind:         {wr['wind_speed_ms']:.1f} m/s @ {wr['wind_direction_deg']:.0f} deg")
            print(f"    Track temp:   {wr['track_temp_c']:.1f} C")
            print(f"    Air density:  {wr['air_density_kgm3']:.4f} kg/m3")
            print(f"    DA:           {wr['density_altitude_ft']:.0f} ft")
            print(f"    Power corr:   {wr['power_correction_factor']:.4f}")
            print(f"    Record ID:    {record_id}")
        else:
            print("  Fetch failed. Check API key and network connection.")

    elif args.da_trend:
        records = db.weather.da_trend(venue_id, limit=args.limit or 50)
        if not records:
            print(f"  No weather records for {venue['name']}.")
        else:
            headers = ["Date/Time", "Temp C", "RH %", "DA ft", "PCF"]
            rows = []
            for r in records:
                rows.append([
                    r["recorded_at"][:19],
                    f"{r['ambient_temp_c']:.1f}",
                    f"{r['relative_humidity_pct']:.0f}",
                    f"{r['density_altitude_ft']:.0f}",
                    f"{r['power_correction_factor']:.4f}",
                ])
            print(f"\n  DA Trend for {venue['name']} ({len(records)} records):")
            print_table(headers, rows)

    else:
        # Show latest
        wr = db.weather.latest(venue_id)
        if wr:
            print(f"\n  Latest weather for {venue['name']}:")
            print(f"    Recorded:     {wr['recorded_at'][:19]}")
            print(f"    Source:       {wr['source']}")
            print(f"    Temp:         {wr['ambient_temp_c']:.1f} C")
            print(f"    Humidity:     {wr['relative_humidity_pct']:.0f}%")
            print(f"    DA:           {wr['density_altitude_ft']:.0f} ft")
            print(f"    PCF:          {wr['power_correction_factor']:.4f}")
        else:
            print(f"  No weather records for {venue['name']}.")
            print(f"  Use --fetch to get live data, or seasonal averages are available via 'venues --detail {venue_id}'")

    db.close()


def cmd_leaderboard(args):
    """Handle 'leaderboard' subcommand."""
    db = ensure_db(args)
    results = db.sim_runs.leaderboard(venue_id=args.venue_id, limit=args.limit or 20)

    if not results:
        print("  No simulation runs recorded yet.")
        print("  Use: python -m motoquant.run sim --bike-id 1 --save-run")
    else:
        headers = ["Rank", "Manufacturer", "Model", "ET (s)", "Trap (km/h)",
                    "60ft (s)", "Config ID"]
        rows = []
        for i, r in enumerate(results, 1):
            rows.append([
                i,
                r.get("manufacturer_name", "-"),
                r.get("model_name", "-"),
                f"{r['et_quarter_s']:.3f}",
                f"{r['trap_speed_kmh']:.1f}" if r.get("trap_speed_kmh") else "-",
                f"{r['time_60ft_s']:.3f}" if r.get("time_60ft_s") else "-",
                r["bike_config_id"],
            ])
        venue_note = ""
        if args.venue_id:
            venue = db.venues.get(args.venue_id)
            if venue:
                venue_note = f" at {venue['name']}"
        print(f"\n  Leaderboard{venue_note}:")
        print_table(headers, rows)

    db.close()


def cmd_history(args):
    """Handle 'history' subcommand."""
    db = ensure_db(args)
    results = db.sim_runs.history(
        bike_config_id=args.bike_id,
        venue_id=args.venue_id,
        limit=args.limit or 20,
    )

    if not results:
        print("  No simulation runs found for this filter.")
    else:
        headers = ["Run ID", "ET (s)", "Trap (km/h)", "60ft (s)", "Version", "Date", "Parts"]
        rows = []
        for r in results:
            parts = json.loads(r["applied_parts"]) if r.get("applied_parts") else []
            rows.append([
                r["id"],
                f"{r['et_quarter_s']:.3f}",
                f"{r['trap_speed_kmh']:.1f}" if r.get("trap_speed_kmh") else "-",
                f"{r['time_60ft_s']:.3f}" if r.get("time_60ft_s") else "-",
                r.get("sim_version") or "-",
                r["created_at"][:19] if r.get("created_at") else "-",
                f"{len(parts)} mods" if parts else "stock",
            ])
        print(f"\n  Run History:")
        print_table(headers, rows)

    db.close()


# ═══════════════════════════════════════════
# SCRAPER COMMANDS
# ═══════════════════════════════════════════

def cmd_scrape(args):
    """Handle 'scrape --manufacturer X' — crawl bikez.com for one manufacturer."""
    try:
        import urllib.request
        from .scraper.bikez import crawl_bikez
        from .scraper.validator import validate_spec, score_spec
        from .scraper.importer import import_batch
    except ImportError as e:
        print(f"  Scraper module not available: {e}")
        return

    manufacturer = args.manufacturer
    if not manufacturer:
        print("  Error: specify --manufacturer NAME  or  --bulk  for a full catalog run")
        print("  Run 'scrape --list-catalog' to see all available manufacturers.")
        return
    limit = args.limit or 50
    category_filter = args.category
    min_cc = args.min_cc or 0
    dry_run = args.dry_run

    print(f"\n  Scraping bikez.com: {manufacturer}  (limit={limit}, dry_run={dry_run})")
    print("  " + "─" * 60)

    # Use a simple urllib opener (no external deps)
    class _Session:
        def get(self, url, timeout=15):
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MotoQuantPro/2.0 (+research)"},
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    class _R:
                        status_code = resp.status
                        text = resp.read().decode("utf-8", errors="replace")
                        def raise_for_status(self): pass
                    return _R()
            except Exception as e:
                class _Err:
                    status_code = 0
                    text = ""
                    def raise_for_status(self): raise IOError(str(e))
                return _Err()

    session = _Session()
    specs = []
    validated = 0
    skipped = 0

    try:
        for spec in crawl_bikez(
            manufacturer=manufacturer,
            session=session,
            limit=limit,
            category_filter=category_filter,
            min_displacement_cc=min_cc,
        ):
            from .scraper.validator import validate_spec
            result = validate_spec(spec)
            score = score_spec(spec, result)
            status = "✓" if result.is_valid else "✗"
            warnings_str = f" [{len(result.warnings)}W]" if result.warnings else ""
            print(f"  {status} {spec.manufacturer} {spec.model_name} "
                  f"({spec.year_from or '?'})  "
                  f"conf={score:.2f}  "
                  f"{spec.displacement_cc or '?'}cc  "
                  f"{spec.peak_power_hp or '?'}hp"
                  f"{warnings_str}")
            if result.is_valid:
                specs.append(spec)
                validated += 1
            else:
                skipped += 1
    except Exception as e:
        print(f"  Crawl error: {e}")
        if not specs:
            return

    print(f"\n  Scraped: {validated} valid, {skipped} invalid/skipped")

    if dry_run:
        print("  (dry-run: not importing)")
        return

    if not specs:
        print("  Nothing to import.")
        return

    db = ensure_db(args)
    summary = import_batch(db, specs, dry_run=False)
    print(f"  Imported: {summary['imported']}  Errors: {summary['errors']}")
    db.close()


def cmd_scrape_bulk(args):
    """Handle 'scrape --bulk' — multi-manufacturer crawl with checkpoint/resume."""
    try:
        from .scraper.bulk_scrape import (
            run_bulk_scrape, print_checkpoint_status, DEFAULT_CHECKPOINT
        )
        from .scraper.catalog import all_manufacturers, priority_manufacturers
    except ImportError as e:
        print(f"  Bulk scrape module not available: {e}")
        return

    checkpoint = getattr(args, "checkpoint", None) or DEFAULT_CHECKPOINT

    # ── Status-only mode ──────────────────────────────────────────────────────
    if getattr(args, "status", False):
        print_checkpoint_status(checkpoint)
        return

    # ── Show catalog ──────────────────────────────────────────────────────────
    if getattr(args, "list_catalog", False):
        from .scraper.catalog import SCRAPE_CATALOG
        print(f"\n  Bulk scrape catalog  ({len(SCRAPE_CATALOG)} manufacturers)")
        print(f"  {'#':>3}  {'Manufacturer':<22} {'P':>2}  {'cc+':>5}  {'Years':<11}  Categories")
        print(f"  {'─'*3}  {'─'*22} {'─'*2}  {'─'*5}  {'─'*11}  {'─'*20}")
        for i, e in enumerate(SCRAPE_CATALOG, 1):
            cats = "/".join(e.get("categories", []))
            yr = f"{e.get('year_from',2000)}-{e.get('year_to',2026)}"
            print(f"  {i:>3}  {e['manufacturer']:<22} {e.get('priority',3):>2}  "
                  f"{e.get('min_cc',600):>5}  {yr:<11}  {cats}")
        return

    # ── Actual bulk run ───────────────────────────────────────────────────────
    dry_run  = getattr(args, "dry_run", False)
    resume   = not getattr(args, "no_resume", False)
    priority = getattr(args, "priority", 3)
    only     = getattr(args, "only", None)
    limit    = getattr(args, "limit", 300) or 300
    rate     = getattr(args, "rate", 1.5) or 1.5

    print(f"\n  MotoQuant Bulk Scraper")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Checkpoint : {checkpoint}")
    print(f"  Resume     : {resume}")
    print(f"  Dry run    : {dry_run}")
    print(f"  Priority   ≤ {priority}")
    if only:
        print(f"  Only       : {only}")
    print(f"  Rate limit : {rate:.1f}s/request")
    print(f"  Per-mfr cap: {limit}")

    db = ensure_db(args)
    result = run_bulk_scrape(
        db=db,
        checkpoint_path=checkpoint,
        resume=resume,
        dry_run=dry_run,
        priority=priority,
        only_manufacturer=only,
        rate_limit_s=rate,
        per_mfr_limit=limit,
        verbose=True,
    )
    db.close()

    print()
    for line in result.summary_lines():
        print(line)


def cmd_import(args):
    """Handle 'import' subcommand — import bikes into DB."""
    try:
        from .scraper.importer import import_batch
        from .scraper.validator import validate_spec
    except ImportError as e:
        print(f"  Scraper module not available: {e}")
        return

    db = ensure_db(args)

    if args.known_bikes:
        from .scraper.known_bikes import ALL_KNOWN_BIKES
        specs = ALL_KNOWN_BIKES
        print(f"\n  Importing {len(specs)} curated known bikes…")
    elif args.spec_json:
        import json as _json
        from .scraper.bikez import spec_from_dict
        with open(args.spec_json) as fh:
            data = _json.load(fh)
        if isinstance(data, list):
            specs = [spec_from_dict(d) for d in data]
        else:
            specs = [spec_from_dict(data)]
        print(f"\n  Importing {len(specs)} bikes from {args.spec_json}…")
    else:
        print("  Error: specify --known-bikes or --spec-json FILE")
        db.close()
        return

    dry_run = args.dry_run
    summary = import_batch(db, specs, dry_run=dry_run)

    status = "[DRY RUN] " if dry_run else ""
    print(f"  {status}Results:")
    print(f"    Imported:        {summary['imported']}")
    print(f"    Skipped invalid: {summary['skipped_invalid']}")
    print(f"    Errors:          {summary['errors']}")

    if not dry_run:
        total = db.bikes.count_models()
        print(f"    Total in DB:     {total}")

    db.close()


# ═══════════════════════════════════════════
# LEGACY (Phase 1) MAIN — backward compat
# ═══════════════════════════════════════════

def legacy_main(args_list=None):
    """
    Phase 1 CLI for backward compatibility.
    Called when no subcommand is detected.
    """
    parser = argparse.ArgumentParser(
        prog="motoquant",
        description="MotoQuant Pro — Motorcycle Drag Racing Simulation Engine",
        epilog="Phase 2 commands: db, bikes, sim, venues, tires, parts, weather, leaderboard, history\n"
               "Run 'python -m motoquant.run <command> --help' for details.\n\n"
               "Legacy examples:\n"
               "  python -m motoquant.run --bike k5 --venue aamby-winter\n"
               "  python -m motoquant.run --config my_bike.json --csv output.csv\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--bike", "-b", type=str, default=None)
    parser.add_argument("--config", "-c", type=str, default=None)
    parser.add_argument("--venue", "-v", type=str, default=None)
    parser.add_argument("--distance", "-d", type=float, default=QUARTER_MILE_M)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--csv", type=str, default=None, metavar="FILE")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--export-config", nargs=2, metavar=("BIKE", "FILE"))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--db", type=str, default=None)

    args = parser.parse_args(args_list)

    if args.list:
        print("\nAvailable bikes (built-in):")
        for key, (desc, _) in BIKE_REGISTRY.items():
            print(f"  {key:8s}  {desc}")
        print(f"\nAliases: {', '.join(f'{a}->{v}' for a, v in BIKE_ALIASES.items())}")
        print(f"\nAvailable venues (built-in):")
        for key, (desc, _) in VENUE_REGISTRY.items():
            print(f"  {key:16s}  {desc}")
        print(f"\n  (default)         Sea Level Reference (0m, 25C, 50% RH)")
        # Also show DB info if available
        try:
            db = get_db(args)
            db.initialize()
            stats = db.stats()
            if stats.get("bike_models", 0) > 0:
                print(f"\nDatabase ({db.path}):")
                print(f"  Bikes: {stats['bike_models']} | "
                      f"Tires: {stats['tire_models']} | "
                      f"Venues: {stats['venues']} | "
                      f"Parts: {stats['parts']}")
                print(f"  Use subcommands for full DB access: bikes, sim, venues, tires, parts")
            db.close()
        except Exception:
            pass
        return

    if args.export_config:
        bike_key = resolve_bike(args.export_config[0])
        out_path = args.export_config[1]
        if bike_key not in BIKE_REGISTRY:
            print(f"Error: unknown bike '{args.export_config[0]}'")
            sys.exit(1)
        config = BIKE_REGISTRY[bike_key][1]()
        save_config(config, out_path)
        print(f"Config saved: {out_path}")
        return

    # Build bike list
    bikes = []
    if args.config:
        config = load_config(args.config)
        bikes.append((Path(args.config).stem, config))
    elif args.bike:
        key = resolve_bike(args.bike)
        if key not in BIKE_REGISTRY:
            print(f"Error: unknown bike '{args.bike}'")
            sys.exit(1)
        bikes.append((key, BIKE_REGISTRY[key][1]()))
    else:
        for key, (_, factory) in BIKE_REGISTRY.items():
            bikes.append((key, factory()))

    # Apply venue
    if args.venue:
        if args.venue not in VENUE_REGISTRY:
            print(f"Error: unknown venue '{args.venue}'")
            sys.exit(1)
        venue_fn = VENUE_REGISTRY[args.venue][1]
        for _, config in bikes:
            venue_fn(config)

    if not args.quiet and not args.json:
        print_banner()

    results = {}
    json_outputs = []
    for name, config in bikes:
        verbose = not args.quiet and not args.json
        result = run_bike(config, dt=args.dt, distance=args.distance, verbose=verbose)
        results[name] = result
        if args.json:
            json_outputs.append(result_to_dict(config, result))
        if args.csv:
            if len(bikes) == 1:
                csv_path = args.csv
            else:
                stem = Path(args.csv).stem
                ext = Path(args.csv).suffix or ".csv"
                csv_path = f"{stem}_{name}{ext}"
            export_csv(result, csv_path)

    if args.json:
        if len(json_outputs) == 1:
            print(json.dumps(json_outputs[0], indent=2))
        else:
            print(json.dumps(json_outputs, indent=2))
        return

    if len(bikes) > 1 and not args.quiet:
        print_comparison(bikes, results)

    return results


# ═══════════════════════════════════════════
# ARGUMENT PARSER  (Phase 2 subcommands)
# ═══════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="motoquant",
        description="MotoQuant Pro — Motorcycle Drag Racing Simulation Engine (Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", type=str, default=None,
                        help=f"Path to MotoQuant database (default: {DEFAULT_DB_PATH})")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── db ──
    p_db = subparsers.add_parser("db", help="Database management")
    p_db.add_argument("db_action", choices=["init", "seed", "stats"],
                      help="init: create tables | seed: load reference data | stats: show counts")

    # ── bikes ──
    p_bikes = subparsers.add_parser("bikes", help="List/search bikes in database")
    p_bikes.add_argument("--search", "-s", type=str, help="Search by model name")
    p_bikes.add_argument("--manufacturer", "-m", type=str, help="Filter by manufacturer")
    p_bikes.add_argument("--category", type=str, help="Filter by category (sport/naked/cruiser)")
    p_bikes.add_argument("--displacement", type=str, help="Filter by cc range (e.g., 900-1300)")
    p_bikes.add_argument("--power-min", type=float, help="Minimum HP")
    p_bikes.add_argument("--quality", type=str,
                         choices=["scraped", "spec_sheet", "verified", "dyno_validated", "track_validated"],
                         help="Filter by data quality")
    p_bikes.add_argument("--limit", type=int, default=50)
    p_bikes.add_argument("--json", dest="json_out", action="store_true")

    # ── sim ──
    p_sim = subparsers.add_parser("sim", help="Run quarter-mile simulation")
    # DB-based bike selection
    p_sim.add_argument("--bike-id", type=int, help="Bike model ID from database")
    # Legacy bike selection (backward compat within sim subcommand)
    p_sim.add_argument("--bike", dest="bike_legacy", type=str,
                       help="Legacy built-in bike (k5/r1/busa)")
    p_sim.add_argument("--config", dest="config_file", type=str,
                       help="Path to JSON config file")
    # Venue / weather
    p_sim.add_argument("--venue-id", type=int, help="Venue ID from database")
    p_sim.add_argument("--venue", dest="venue_legacy", type=str,
                       help="Legacy venue (aamby-winter/aamby-summer)")
    p_sim.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12",
                       help="Month for seasonal weather (1-12, default: current)")
    p_sim.add_argument("--weather-live", action="store_true",
                       help="Fetch live weather from API (requires OPENWEATHERMAP_API_KEY)")
    p_sim.add_argument("--api-key", type=str, help="OpenWeatherMap API key")
    p_sim.add_argument("--track-temp", type=float, help="Override track surface temp (C)")
    # Parts
    p_sim.add_argument("--apply-parts", type=str,
                       help="Comma-separated part IDs to apply (e.g., 3,5,8)")
    p_sim.add_argument("--compare-stock", action="store_true",
                       help="Run stock vs modified comparison")
    # Archival
    p_sim.add_argument("--save-run", action="store_true",
                       help="Save simulation result to database")
    # Sim parameters
    p_sim.add_argument("--distance", "-d", type=float, default=QUARTER_MILE_M,
                       help="Simulation distance in meters")
    p_sim.add_argument("--dt", type=float, default=0.001, help="Timestep (s)")
    # Output
    p_sim.add_argument("--json", "-j", dest="json_out", action="store_true")
    p_sim.add_argument("--csv", type=str, metavar="FILE")
    p_sim.add_argument("--quiet", "-q", action="store_true")

    # ── venues ──
    p_venues = subparsers.add_parser("venues", help="List venues and seasonal data")
    p_venues.add_argument("--detail", type=int, metavar="ID",
                          help="Show detailed info for a venue")
    p_venues.add_argument("--country", type=str, default=None)
    p_venues.add_argument("--include-inactive", action="store_true")

    # ── tires ──
    p_tires = subparsers.add_parser("tires", help="Tire library")
    p_tires.add_argument("--grip-rank", action="store_true",
                         help="Rank tires by grip (weighted by confidence)")
    p_tires.add_argument("--value-rank", action="store_true",
                         help="Rank tires by grip per rupee (Indian market)")
    p_tires.add_argument("--compound", type=str,
                         choices=["street", "sport", "race", "drag_dot", "drag_slick"])
    p_tires.add_argument("--position", type=str, choices=["front", "rear"])
    p_tires.add_argument("--manufacturer", type=str)
    p_tires.add_argument("--india-only", action="store_true",
                         help="Only show tires available in India")

    # ── parts ──
    p_parts = subparsers.add_parser("parts", help="Performance parts catalog")
    p_parts.add_argument("--category", type=str, help="Filter by category (sprocket/ecu/exhaust/...)")
    p_parts.add_argument("--brand", type=str)
    p_parts.add_argument("--search", type=str)
    p_parts.add_argument("--max-price", type=float, help="Max price in INR")
    p_parts.add_argument("--available", action="store_true", help="Only in-stock items")
    p_parts.add_argument("--build-cost", type=str, metavar="IDS",
                         help="Calculate total cost for part IDs (e.g., 3,5,8,12)")

    # ── weather ──
    p_weather = subparsers.add_parser("weather", help="Weather data and DA tracking")
    p_weather.add_argument("--venue-id", type=int,
                           help="Venue ID (required unless --refresh-all)")
    p_weather.add_argument("--refresh-all", action="store_true",
                           help="Poll OWM for all venues and store weather records")
    p_weather.add_argument("--stale-minutes", type=int, default=60,
                           help="Skip venues with data newer than N min (default: 60)")
    p_weather.add_argument("--venue-ids-filter", type=int, nargs="+",
                           help="Limit --refresh-all to specific venue IDs")
    p_weather.add_argument("--fetch", action="store_true",
                           help="Fetch live weather from API")
    p_weather.add_argument("--da-trend", action="store_true",
                           help="Show density altitude trend")
    p_weather.add_argument("--api-key", type=str)
    p_weather.add_argument("--track-temp", type=float)
    p_weather.add_argument("--limit", type=int, default=50)

    # ── leaderboard ──
    p_lb = subparsers.add_parser("leaderboard", help="Best ETs across all runs")
    p_lb.add_argument("--venue-id", type=int, help="Filter by venue")
    p_lb.add_argument("--limit", type=int, default=20)

    # ── history ──
    p_hist = subparsers.add_parser("history", help="Simulation run history")
    p_hist.add_argument("--bike-id", type=int, help="Filter by bike config ID")
    p_hist.add_argument("--venue-id", type=int, help="Filter by venue")
    p_hist.add_argument("--limit", type=int, default=20)

    # ── scrape ──
    p_scrape = subparsers.add_parser(
        "scrape",
        help="Crawl bikez.com for specs and import into DB",
    )
    p_scrape_mode = p_scrape.add_mutually_exclusive_group()
    p_scrape_mode.add_argument("--manufacturer",
                               help="Single manufacturer to scrape (e.g. 'Suzuki')")
    p_scrape_mode.add_argument("--bulk", action="store_true",
                               help="Bulk-scrape ALL manufacturers in the catalog "
                                    "(resumes from checkpoint if interrupted)")
    p_scrape.add_argument("--limit", type=int, default=None,
                          help="Max bikes per manufacturer (default: 50 single / 300 bulk)")
    p_scrape.add_argument("--category", default=None,
                          help="Filter by category (sport/naked/cruiser/adventure/touring)")
    p_scrape.add_argument("--min-cc", type=float, default=0,
                          help="Minimum displacement to include (cc)")
    p_scrape.add_argument("--dry-run", action="store_true",
                          help="Validate/count without writing to DB")
    # Bulk-only options
    p_scrape.add_argument("--priority", type=int, default=3,
                          help="(bulk) Only scrape manufacturers with priority ≤ N "
                               "(1=top, 2=standard, 3=all)")
    p_scrape.add_argument("--only", default=None, metavar="MFR",
                          help="(bulk) Only scrape this manufacturer from the catalog")
    p_scrape.add_argument("--no-resume", action="store_true",
                          help="(bulk) Start fresh, ignoring any saved checkpoint")
    p_scrape.add_argument("--checkpoint", default=None, metavar="FILE",
                          help="(bulk) Path to checkpoint JSON file")
    p_scrape.add_argument("--rate", type=float, default=1.5,
                          help="(bulk) Seconds between HTTP requests (default: 1.5)")
    p_scrape.add_argument("--status", action="store_true",
                          help="(bulk) Show checkpoint status and exit")
    p_scrape.add_argument("--list-catalog", action="store_true",
                          help="(bulk) List all manufacturers in the catalog and exit")

    # ── import ──
    p_import = subparsers.add_parser(
        "import",
        help="Import bikes into database from known-bikes list or JSON file",
    )
    p_import_src = p_import.add_mutually_exclusive_group(required=True)
    p_import_src.add_argument("--known-bikes", action="store_true",
                               help="Import the built-in curated known-bikes list (22 bikes)")
    p_import_src.add_argument("--spec-json", metavar="FILE",
                               help="Path to JSON file with bike spec(s) to import")
    p_import.add_argument("--dry-run", action="store_true",
                          help="Validate without writing to DB")

    return parser


# ═══════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════

def main():
    """
    Main CLI entry point.

    Detects whether the user is invoking Phase 2 subcommands or
    Phase 1 legacy flags, and routes accordingly.
    """
    known_commands = {"db", "bikes", "sim", "venues", "tires", "parts",
                      "weather", "leaderboard", "history", "scrape", "import"}

    # Check if ANY positional arg is a known subcommand
    # (handles cases like `--db /path db init`)
    has_subcommand = False
    for arg in sys.argv[1:]:
        if arg in known_commands:
            has_subcommand = True
            break

    if has_subcommand:
        # Phase 2 subcommand mode
        parser = build_parser()
        args = parser.parse_args()

        dispatch = {
            "db":           cmd_db,
            "bikes":        cmd_bikes,
            "sim":          cmd_sim,
            "venues":       cmd_venues,
            "tires":        cmd_tires,
            "parts":        cmd_parts,
            "weather":      cmd_weather,
            "leaderboard":  cmd_leaderboard,
            "history":      cmd_history,
            "scrape":       lambda a: cmd_scrape_bulk(a) if getattr(a, "bulk", False) or getattr(a, "status", False) or getattr(a, "list_catalog", False) else cmd_scrape(a),
            "import":       cmd_import,
        }

        handler = dispatch.get(args.command)
        if handler:
            handler(args)
        else:
            parser.print_help()
    else:
        # Phase 1 legacy mode (--bike, --config, --list, etc.)
        legacy_main()


if __name__ == "__main__":
    main()
