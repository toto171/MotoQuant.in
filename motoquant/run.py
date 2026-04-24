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

    python -m motoquant.run nl "optimize my Hayabusa for 35C at Aamby Valley"
                            # Phase 4C: NL tuning interface
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from .config_io import load_config, save_config
from .constants import MS_TO_KMH, MS_TO_MPH, QUARTER_MILE_M, G
from .defaults import (
    aamby_valley_summer,
    aamby_valley_winter,
    gsxr1000_k5,
    hayabusa_gen1,
    yzfr1_4c8,
)
from .models import BikeConfig
from .physics import MotoQuantEngine, SimResult

__all__ = ["main"]

# Default database path (next to the motoquant package)
DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "motoquant.db")

# ═══════════════════════════════════════════
# PHASE 1 LEGACY REGISTRIES (backward compat)
# ═══════════════════════════════════════════

BIKE_REGISTRY = {
    "k5": ("Suzuki GSX-R 1000 K5/K6", gsxr1000_k5),
    "r1": ("Yamaha YZF-R1 4C8", yzfr1_4c8),
    "busa": ("Suzuki Hayabusa Gen1", hayabusa_gen1),
}

BIKE_ALIASES = {
    "gsxr": "k5",
    "gsxr1000": "k5",
    "gsxr-1000": "k5",
    "yzfr1": "r1",
    "4c8": "r1",
    "crossplane": "r1",
    "hayabusa": "busa",
    "gsx1300": "busa",
    "gsx1300r": "busa",
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

    db_path = getattr(args, "db", None) or os.environ.get(
        "MOTOQUANT_DB", DEFAULT_DB_PATH
    )
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

    print(f"\n{'=' * 72}")
    print(f"  MotoQuant Pro v{__version__} — Motorcycle Drag Racing Simulation Engine")
    print("  15 sub-models | RK4 @ 1ms | Phase 2 Database-Integrated")
    print(f"{'=' * 72}")


def print_result(
    config: BikeConfig,
    result: SimResult,
    elapsed_ms: float,
    label: str = None,
    compact: bool = False,
):
    """Print a complete simulation result in human-readable format."""
    title = label or config.name
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"  Venue: {config.environment.venue_name}")
    print(f"{'=' * 72}")

    env = config.environment
    rho = env.air_density()
    da = env.density_altitude_ft()
    print("\n  Environment:")
    print(f"    Altitude:          {env.altitude_m:.0f} m")
    print(f"    Air temp:          {env.ambient_temp_c:.1f} C")
    print(f"    Humidity:          {env.relative_humidity_pct:.0f}%")
    print(f"    Air density:       {rho:.4f} kg/m3")
    print(f"    Density altitude:  {da:.0f} ft")
    if env.wind_speed_ms > 0:
        print(
            f"    Wind:              {env.wind_speed_ms:.1f} m/s @ {env.wind_direction_deg:.0f} deg"
        )
    if env.track_gradient_pct != 0:
        print(f"    Track gradient:    {env.track_gradient_pct:+.2f}%")

    # Split times
    print(f"\n  {'Split':<16} {'Time':>8}   {'Speed (km/h)':>12}  {'Speed (mph)':>11}")
    print(f"  {'-' * 52}")
    splits = [
        ("60-foot", result.time_60ft, result.speed_60ft),
        ("330-foot", result.time_330ft, result.speed_330ft),
        ("1/8 mile", result.time_eighth, result.speed_eighth),
        ("1000-foot", result.time_1000ft, result.speed_1000ft),
        ("1/4 mile", result.time_quarter, result.speed_quarter),
    ]
    for name, t, s in splits:
        if t > 0:
            print(
                f"  {name:<16} {t:.3f} s  {s * MS_TO_KMH:8.1f} km/h  {s * MS_TO_MPH:8.1f} mph"
            )

    if not compact:
        # Performance metrics
        print("\n  Performance Metrics:")
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
            print(
                f"    Tire temp range:     {np.min(result.T_tire):.1f} - {np.max(result.T_tire):.1f} C"
            )
        if len(result.traction_pct) > 0:
            print(f"    Peak traction use:   {np.max(result.traction_pct):.1f}%")

        engine = MotoQuantEngine(config)
        m_eff = engine.effective_mass(0)
        print(
            f"    Effective mass (1st): {m_eff:.1f} kg ({m_eff / config.chassis.total_mass_kg * 100:.1f}% of static)"
        )
        a_wheelie = engine.max_accel_before_wheelie(0, 0)
        print(f"    Wheelie limit:       {a_wheelie / G:.2f} g ({a_wheelie:.1f} m/s2)")

    print(
        f"\n  Simulation: {len(result.t)} steps, {elapsed_ms:.1f} ms runtime, dt={result.dt * 1000:.1f} ms"
    )
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
            "peak_accel_g": round(float(np.max(result.a)), 3)
            if len(result.a) > 0
            else 0,
            "peak_rpm": int(np.max(result.rpm)) if len(result.rpm) > 0 else 0,
            "peak_power_kw": round(float(np.max(result.power_kw)), 2)
            if len(result.power_kw) > 0
            else 0,
            "peak_power_hp": round(float(np.max(result.power_kw)) * 1.341, 1)
            if len(result.power_kw) > 0
            else 0,
            "gears_used": int(np.max(result.gear)) if len(result.gear) > 0 else 0,
            "tire_temp_min_c": round(float(np.min(result.T_tire)), 1)
            if len(result.T_tire) > 0
            else 0,
            "tire_temp_max_c": round(float(np.max(result.T_tire)), 1)
            if len(result.T_tire) > 0
            else 0,
            "peak_traction_pct": round(float(np.max(result.traction_pct)), 1)
            if len(result.traction_pct) > 0
            else 0,
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
        writer.writerow(
            [
                "time_s",
                "position_m",
                "velocity_ms",
                "velocity_kmh",
                "accel_g",
                "rpm",
                "gear",
                "slip_ratio",
                "traction_pct",
                "N_front_N",
                "N_rear_N",
                "F_drive_N",
                "F_drag_N",
                "F_rr_N",
                "tire_temp_C",
                "clutch_temp_C",
                "boost_bar",
                "power_kw",
                "r_eff_m",
            ]
        )
        for i in range(n):
            writer.writerow(
                [
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
                ]
            )
    print(f"  Time-history exported: {path} ({n} rows x 19 channels)")


def print_comparison(entries, results):
    """Print a side-by-side comparison table. entries = [(label, config), ...]"""
    print(f"\n{'=' * 72}")
    print("  COMPARISON TABLE")
    print(f"{'=' * 72}")
    print(f"\n  {'Metric':<20}", end="")
    for label, _ in entries:
        short = label[:14]
        print(f"  {short:>14}", end="")
    print()
    print(f"  {'-' * 20}", end="")
    for _ in entries:
        print(f"  {'-' * 14}", end="")
    print()

    metrics = [
        ("60-ft (s)", lambda r: f"{r.time_60ft:.3f}"),
        ("1/8 mile ET (s)", lambda r: f"{r.time_eighth:.3f}"),
        ("1/4 mile ET (s)", lambda r: f"{r.time_quarter:.3f}"),
        ("Trap speed (km/h)", lambda r: f"{r.speed_quarter * MS_TO_KMH:.1f}"),
        ("Trap speed (mph)", lambda r: f"{r.speed_quarter * MS_TO_MPH:.1f}"),
        ("Peak accel (g)", lambda r: f"{np.max(r.a):.2f}" if len(r.a) > 0 else "N/A"),
        (
            "Peak power (HP)",
            lambda r: (
                f"{np.max(r.power_kw) * 1.341:.0f}" if len(r.power_kw) > 0 else "N/A"
            ),
        ),
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


def run_bike(
    config: BikeConfig,
    dt: float = 0.001,
    distance: float = QUARTER_MILE_M,
    verbose: bool = True,
    label: str = None,
) -> SimResult:
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
        sep += f"  {'-' * w}"
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
        print("  Schema version: 1")
        stats = db.stats()
        print(f"  Venues seeded: {stats['venues']}")
        print(f"  Seasonal records: {stats['venue_seasonal']}")
        print(f"  Parts categories: {stats.get('parts_categories', 0)}")
        db.close()

    elif action == "seed":
        db = ensure_db(args)
        from .database.seed import seed_all

        counts = seed_all(db)
        print("\n  Database seeded:")
        print(f"    Bikes:  {counts['bikes']} reference platforms")
        print(f"    Tires:  {counts['tires']} models")
        print(f"    Parts:  {counts['parts']} performance parts")
        stats = db.stats()
        print("\n  Total records:")
        for table, count in stats.items():
            if count > 0:
                print(f"    {table:20s}  {count}")
        db.close()

    elif action == "stats":
        db = ensure_db(args)
        stats = db.stats()
        print(f"\n  MotoQuant Database: {db.path}")
        print(f"  {'Table':20s}  {'Count':>6}")
        print(f"  {'-' * 30}")
        for table, count in stats.items():
            print(f"  {table:20s}  {count:6d}")
        db.close()

    else:
        print(f"  Unknown db action: {action}")
        print("  Available: init, seed, stats")


def cmd_bikes(args):
    """Handle 'bikes' subcommand: list/search bikes from DB."""
    db = ensure_db(args)

    # Handle fitments subcommand
    if getattr(args, "fitments", None):
        bike = db.bikes.get(args.fitments)
        if not bike:
            print(f"\n  Error: no bike found with ID {args.fitments}")
            db.close()
            return

        fitments = db.tires.get_bike_fitments(args.fitments)
        if not fitments:
            print(
                f"\n  No tire fitments found for {bike['manufacturer_name']} {bike['model_name']}"
            )
            db.close()
            return

        print(
            f"\n  Tire Fitments for {bike['manufacturer_name']} {bike['model_name']} ({bike.get('model_code', '-')}):"
        )
        if args.json_out:
            print(json.dumps(fitments, indent=2, default=str))
        else:
            headers = [
                "Position",
                "Type",
                "Tire",
                "Compound",
                "Size",
                "Grip (µ)",
                "Price INR",
                "Default",
            ]
            rows = []
            for f in fitments:
                rows.append(
                    [
                        f["position"].upper(),
                        f["fitment_type"].upper(),
                        f"{f['tire_manufacturer']} {f['model_name']}",
                        f.get("compound_type", "-"),
                        f.get("size_designation", "-"),
                        f"{f['mu_peak']:.2f}" if f.get("mu_peak") else "-",
                        f"{f['price_inr']:.0f}" if f.get("price_inr") else "-",
                        "✓" if f.get("is_default") else "",
                    ]
                )
            print_table(headers, rows)
        db.close()
        return

    # Regular bikes search
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
        headers = [
            "ID",
            "Manufacturer",
            "Model",
            "Code",
            "Years",
            "cc",
            "HP",
            "Mass",
            "Quality",
            "ET (val)",
        ]
        rows = []
        for b in results:
            years = ""
            if b.get("year_from"):
                years = str(b["year_from"])
                if b.get("year_to") and b["year_to"] != b["year_from"]:
                    years += f"-{b['year_to']}"
            et = f"{b['validation_et_s']:.2f}" if b.get("validation_et_s") else "-"
            rows.append(
                [
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
                ]
            )
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
                weather_id = db.weather.fetch_live(
                    venue_id, api_key=api_key, track_temp_c=args.track_temp
                )
                if weather_id:
                    env = db.weather.to_environment(weather_id)
                    if verbose:
                        wr = db.weather.get(weather_id)
                        print(f"\n  Live weather fetched for venue {venue_id}:")
                        print(
                            f"    Temp: {wr['ambient_temp_c']:.1f} C | "
                            f"RH: {wr['relative_humidity_pct']:.0f}% | "
                            f"DA: {wr['density_altitude_ft']:.0f} ft | "
                            f"PCF: {wr['power_correction_factor']:.4f}"
                        )
                else:
                    print("  Warning: live weather fetch failed, using seasonal data")
            else:
                print(
                    "  Warning: no API key set (OPENWEATHERMAP_API_KEY). Using seasonal data."
                )

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
                    print(
                        f"  Applied: {part['brand']} {part['model_name']} "
                        f"({part['category_display']})"
                        f"{'  INR ' + str(int(part.get('price_inr') or 0)) if part.get('price_inr') else ''}"
                    )

        # ── Apply tire overrides ──
        tire_mods = []
        front_tire_id = getattr(args, "front_tire", None)
        rear_tire_id = getattr(args, "rear_tire", None)

        if rear_tire_id:
            rear_tire_params = db.tires.tire_to_params(rear_tire_id)
            if rear_tire_params is None:
                print(f"  Warning: rear tire ID {rear_tire_id} not found, skipping")
            else:
                # Apply rear tire parameters to config
                config.tires.mu_peak = rear_tire_params.mu_peak
                config.tires.mu_slide = rear_tire_params.mu_slide
                config.tires.load_sensitivity_k = rear_tire_params.load_sensitivity_k
                config.tires.pacejka_B = rear_tire_params.pacejka_B
                config.tires.pacejka_C = rear_tire_params.pacejka_C
                config.tires.pacejka_D = rear_tire_params.pacejka_D
                config.tires.pacejka_E = rear_tire_params.pacejka_E
                config.tires.rear_rolling_radius_m = (
                    rear_tire_params.rear_rolling_radius_m
                )
                config.tires.rear_size = rear_tire_params.rear_size
                config.tires.rear_model = rear_tire_params.rear_model
                config.tires.rear_pressure_psi = rear_tire_params.rear_pressure_psi
                config.tires.rear_mass_kg = rear_tire_params.rear_mass_kg
                config.tires.rear_inertia_kgm2 = rear_tire_params.rear_inertia_kgm2
                config.tires.optimal_temp_c = rear_tire_params.optimal_temp_c
                config.tires.reversion_temp_c = rear_tire_params.reversion_temp_c
                config.tires.thermal_conductivity = (
                    rear_tire_params.thermal_conductivity
                )
                config.tires.tread_mass_kg = rear_tire_params.tread_mass_kg
                config.tires.specific_heat_rubber = (
                    rear_tire_params.specific_heat_rubber
                )
                config.tires.crr_base = rear_tire_params.crr_base
                config.tires.crr_speed_coeff = rear_tire_params.crr_speed_coeff
                config.tires.crr_temp_coeff = rear_tire_params.crr_temp_coeff
                config.tires.growth_coeff = rear_tire_params.growth_coeff
                config.tires.tire_construction = rear_tire_params.tire_construction
                tire_mods.append(
                    f"rear: {rear_tire_params.rear_model} ({rear_tire_params.rear_size})"
                )
                if verbose:
                    print(
                        f"  Rear tire: {rear_tire_params.rear_model} ({rear_tire_params.rear_size})"
                    )

        if front_tire_id:
            front_tire_params = db.tires.tire_to_params(front_tire_id)
            if front_tire_params is None:
                print(f"  Warning: front tire ID {front_tire_id} not found, skipping")
            else:
                # Apply front tire rolling radius only (front doesn't dominate drag traction)
                config.tires.front_rolling_radius_m = (
                    front_tire_params.rear_rolling_radius_m
                )
                config.tires.front_size = front_tire_params.rear_size
                config.tires.front_pressure_psi = front_tire_params.rear_pressure_psi
                config.tires.front_mass_kg = front_tire_params.rear_mass_kg
                config.tires.front_inertia_kgm2 = front_tire_params.rear_inertia_kgm2
                tire_mods.append(
                    f"front: {front_tire_params.rear_model} ({front_tire_params.rear_size})"
                )
                if verbose:
                    print(
                        f"  Front tire: {front_tire_params.rear_model} ({front_tire_params.rear_size})"
                    )

        # ── Run simulation ──
        if verbose and not output_json:
            print_banner()

        label_mod = config.name
        mods_list = []
        if parts_ids:
            mods_list.append(f"+{len(parts_ids)} parts")
        if tire_mods:
            mods_list.append(f"+{len(tire_mods)} tires")
        if mods_list:
            label_mod += f"  [{', '.join(mods_list)}]"

        result = run_bike(
            config, dt=args.dt, distance=args.distance, verbose=verbose, label=label_mod
        )

        # ── Compare stock ──
        if args.compare_stock and parts_ids:
            stock_config = db.bikes.to_config(config_id, environment=env)
            stock_result = run_bike(
                stock_config,
                dt=args.dt,
                distance=args.distance,
                verbose=verbose,
                label=f"{stock_config.name}  [STOCK]",
            )
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
            run_id = archive_run(
                db, config_id, venue_id, weather_id, result, parts_ids or None
            )
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
        print(f"  {'=' * 50}")
        print(f"  City:      {venue.get('city', '-')}, {venue.get('state', '-')}")
        print(f"  Country:   {venue.get('country', '-')}")
        print(f"  Altitude:  {venue['altitude_m']:.0f} m")
        lat = venue.get("latitude")
        lon = venue.get("longitude")
        if lat and lon:
            print(f"  Coords:    {lat:.4f}, {lon:.4f}")
        print(f"  Surface:   {venue.get('surface_type', '-')}")
        print(
            f"  Timing:    {'Yes' if venue.get('has_timing_system') else 'No'}"
            f" ({venue.get('timing_system_type', '-')})"
        )
        print(f"  VHT:       {'Yes' if venue.get('has_vht') else 'No'}")

        # Seasonal DA table
        seasonal = db.venues.get_all_seasonal(args.detail)
        if seasonal:
            print("\n  Monthly Density Altitude (ft) & Conditions:")
            headers = ["Month", "Temp C", "RH %", "Press hPa", "Wind m/s", "DA ft"]
            month_names = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            rows = []
            for s in seasonal:
                m = s["month"]
                rows.append(
                    [
                        month_names[m - 1],
                        f"{s['avg_temp_c']:.0f}",
                        f"{s['avg_humidity_pct']:.0f}",
                        f"{s['avg_pressure_hpa']:.0f}",
                        f"{s['avg_wind_speed_ms']:.1f}",
                        f"{s['avg_density_alt_ft']:.0f}",
                    ]
                )
            print_table(headers, rows)

            best = db.venues.best_da_month(args.detail)
            worst = db.venues.worst_da_month(args.detail)
            if best and worst:
                print(
                    f"  Best month:  {month_names[best['month'] - 1]} "
                    f"(DA {best['avg_density_alt_ft']:.0f} ft)"
                )
                print(
                    f"  Worst month: {month_names[worst['month'] - 1]} "
                    f"(DA {worst['avg_density_alt_ft']:.0f} ft)"
                )
                delta = worst["avg_density_alt_ft"] - best["avg_density_alt_ft"]
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
                rows.append(
                    [
                        v["id"],
                        v["name"],
                        v.get("city") or "-",
                        v.get("state") or "-",
                        f"{v['altitude_m']:.0f}",
                        v.get("surface_type") or "-",
                        "Yes" if v.get("has_timing_system") else "No",
                    ]
                )
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
            headers = [
                "ID",
                "Manufacturer",
                "Model",
                "Size",
                "Compound",
                "mu_peak",
                "Conf",
                "Weighted",
                "INR",
            ]
            rows = []
            for t in results:
                rows.append(
                    [
                        t["id"],
                        t["manufacturer_name"],
                        t["model_name"],
                        t["size_designation"],
                        t["compound_type"],
                        f"{t['mu_peak']:.2f}" if t.get("mu_peak") else "-",
                        f"{t.get('confidence', 0):.2f}",
                        f"{t.get('weighted_grip', 0):.3f}",
                        f"{int(t['price_inr']):,}" if t.get("price_inr") else "-",
                    ]
                )
            print("\n  Tire Grip Ranking (weighted by confidence):")
            print_table(headers, rows)

    elif args.value_rank:
        results = db.tires.rank_by_value(position=args.position or "rear")
        if not results:
            print("  No Indian-available tires with pricing found.")
        else:
            headers = ["ID", "Manufacturer", "Model", "mu_peak", "INR", "Grip/1K INR"]
            rows = []
            for t in results:
                rows.append(
                    [
                        t["id"],
                        t["manufacturer_name"],
                        t["model_name"],
                        f"{t['mu_peak']:.2f}",
                        f"{int(t['price_inr']):,}",
                        f"{t['grip_per_1k_inr']:.4f}",
                    ]
                )
            print("\n  Tire Value Ranking (Indian market, grip per INR 1000):")
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
            headers = [
                "ID",
                "Manufacturer",
                "Model",
                "Size",
                "Type",
                "Pos",
                "mu",
                "INR",
                "India",
            ]
            rows = []
            for t in results:
                rows.append(
                    [
                        t["id"],
                        t["manufacturer_name"],
                        t["model_name"],
                        t["size_designation"],
                        t["compound_type"],
                        t["position"],
                        f"{t['mu_peak']:.2f}" if t.get("mu_peak") else "-",
                        f"{int(t['price_inr']):,}" if t.get("price_inr") else "-",
                        "Y" if t.get("available_india") else "N",
                    ]
                )
            print(f"\n  Tires ({len(results)} results):")
            print_table(headers, rows)

    db.close()


def cmd_parts(args):
    """Handle 'parts' subcommand."""
    import json as _json

    db = ensure_db(args)

    # ── --impact MODE: show ET/trap delta for a single part ─────────────
    if getattr(args, "impact", None):
        if not args.bike_id:
            print("  Error: --impact requires --bike-id")
            db.close()
            return 1
        part_id = args.impact
        bike_id = args.bike_id

        part = db.parts.get(part_id)
        if part is None:
            print(f"  Error: part {part_id} not found")
            db.close()
            return 1
        config_row = db.bikes.get_current_config(bike_id)
        if config_row is None:
            print(f"  Error: no config for bike {bike_id}")
            db.close()
            return 1
        config = db.bikes.to_config(config_row["id"])
        model_row = db.bikes.get_model(bike_id)
        bike_name = (
            f"{model_row['manufacturer_name']} {model_row['model_name']}"
            if model_row
            else f"Bike {bike_id}"
        )

        # Compatibility check via existing engine
        from .database.parts_repo import _enrich_bike_row_for_fitment
        from .parts.compatibility import is_compatible

        bike_row = dict(model_row) if model_row else {"id": bike_id}
        _enrich_bike_row_for_fitment(db._conn, bike_row)
        compatible, reason = is_compatible(part, bike_row)

        # Run base + modified simulations (venue bakes into config via env params)
        from .physics import MotoQuantEngine

        base_result = MotoQuantEngine(config).run()
        modified_config = db.parts.apply_to_config(part_id, config)
        mod_result = MotoQuantEngine(modified_config).run()

        delta_et = mod_result.time_quarter - base_result.time_quarter
        delta_trap = mod_result.speed_quarter - base_result.speed_quarter
        price = part.get("price_inr") or 0.0
        cost_per_tenth = (
            (price / abs(delta_et * 10)) if abs(delta_et) > 1e-6 else float("inf")
        )

        if getattr(args, "output_json", False):
            out = {
                "bike": bike_name,
                "part": f"{part['brand']} {part['model_name']}",
                "part_id": part_id,
                "category": part.get("category_display") or part.get("category_name"),
                "compatible": compatible,
                "fitment_reason": reason,
                "price_inr": price,
                "base_et_s": round(base_result.time_quarter, 4),
                "modified_et_s": round(mod_result.time_quarter, 4),
                "delta_et_s": round(delta_et, 4),
                "base_trap_ms": round(base_result.speed_quarter, 3),
                "modified_trap_ms": round(mod_result.speed_quarter, 3),
                "delta_trap_ms": round(delta_trap, 3),
                "cost_per_tenth_inr": (
                    round(cost_per_tenth, 0) if cost_per_tenth < 1e9 else None
                ),
            }
            print(_json.dumps(out, indent=2))
        else:
            print(f"\n  MOD IMPACT — {bike_name}")
            print(f"  Part: [{part_id}] {part['brand']} {part['model_name']}")
            cat = part.get("category_display") or part.get("category_name") or "?"
            print(f"  Category: {cat}")
            print(f"  Price: ₹{price:,.0f}" if price else "  Price: —")
            print(
                f"  Fitment: {'✓ compatible' if compatible else '✗ INCOMPATIBLE'} — {reason}"
            )
            print(f"  {'─' * 60}")
            print(
                f"  Base ET:      {base_result.time_quarter:7.4f}s   "
                f"Trap: {base_result.speed_quarter * 3.6:6.2f} km/h"
            )
            print(
                f"  Modified ET:  {mod_result.time_quarter:7.4f}s   "
                f"Trap: {mod_result.speed_quarter * 3.6:6.2f} km/h"
            )
            sign = "+" if delta_et >= 0 else ""
            sign_t = "+" if delta_trap >= 0 else ""
            print(
                f"  Δ ET:         {sign}{delta_et:7.4f}s   "
                f"Δ Trap: {sign_t}{delta_trap * 3.6:.2f} km/h"
            )
            if cost_per_tenth < 1e9:
                print(f"  Cost / tenth: ₹{cost_per_tenth:,.0f}")
            else:
                print("  Cost / tenth: — (no measurable gain)")
            if not compatible:
                print(
                    "\n  ⚠  Part is not compatible with this bike. "
                    "Delta shown is theoretical only."
                )
        db.close()
        return 0

    if args.build_cost:
        part_ids = [int(p.strip()) for p in args.build_cost.split(",")]
        cost = db.parts.estimate_build_cost(part_ids, "inr")
        print("\n  Build Cost Estimate:")
        print(f"  {'Part':<40} {'Category':<14} {'INR':>10} {'Avail':>6}")
        print(f"  {'-' * 74}")
        for p in cost["parts"]:
            avail = "Yes" if p["available"] else "No"
            print(
                f"  {p['name']:<40} {p['category']:<14} {p['price']:>10,.0f} {avail:>6}"
            )
        print(f"  {'-' * 74}")
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
        # Bike-id compat filter (handled inside parts_repo.search)
        bike_id_filter = getattr(args, "bike_id", None)
        if bike_id_filter:
            search_kwargs["bike_model_id"] = bike_id_filter

        results = db.parts.search(**search_kwargs)
        if not results:
            hint = (
                " (no parts compatible with this bike — try a different --category)"
                if bike_id_filter
                else " — run: python -m motoquant.run db seed"
            )
            print(f"  No parts found.{hint}")
        elif getattr(args, "output_json", False):
            out = [
                {
                    "id": p["id"],
                    "category": p.get("category_display") or p.get("category_name"),
                    "brand": p["brand"],
                    "model": p["model_name"],
                    "price_inr": p.get("price_inr"),
                    "availability": p.get("availability"),
                }
                for p in results
            ]
            print(_json.dumps(out, indent=2))
        else:
            headers = ["ID", "Category", "Brand", "Model", "INR", "Avail"]
            rows = []
            for p in results:
                rows.append(
                    [
                        p["id"],
                        p["category_display"],
                        p["brand"],
                        p["model_name"],
                        f"{int(p['price_inr']):,}" if p.get("price_inr") else "-",
                        p.get("availability", "-"),
                    ]
                )
            title = (
                f"\n  Parts compatible with bike {bike_id_filter} ({len(results)} results):"
                if bike_id_filter
                else f"\n  Parts ({len(results)} results):"
            )
            print(title)
            print_table(headers, rows)

    db.close()


def cmd_weather(args):
    """Handle 'weather' subcommand."""
    db = ensure_db(args)

    # ── refresh-all: poll every venue ──────────────────────────────────────
    if getattr(args, "refresh_all", False):
        from .database.weather_refresh import refresh_all_venues

        api_key = getattr(args, "api_key", None) or os.environ.get(
            "OPENWEATHERMAP_API_KEY"
        )
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
        print(
            "  Error: --venue-id required for weather commands (or use --refresh-all)"
        )
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
        record_id = db.weather.fetch_live(
            venue_id, api_key=api_key, track_temp_c=args.track_temp
        )
        if record_id:
            wr = db.weather.get(record_id)
            print(f"\n  Live weather fetched for {venue['name']}:")
            print(f"    Temp:         {wr['ambient_temp_c']:.1f} C")
            print(f"    Humidity:     {wr['relative_humidity_pct']:.0f}%")
            print(f"    Pressure:     {wr['barometric_pressure_hpa']:.1f} hPa")
            print(f"    Dew point:    {wr['dew_point_c']:.1f} C")
            print(
                f"    Wind:         {wr['wind_speed_ms']:.1f} m/s @ {wr['wind_direction_deg']:.0f} deg"
            )
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
                rows.append(
                    [
                        r["recorded_at"][:19],
                        f"{r['ambient_temp_c']:.1f}",
                        f"{r['relative_humidity_pct']:.0f}",
                        f"{r['density_altitude_ft']:.0f}",
                        f"{r['power_correction_factor']:.4f}",
                    ]
                )
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
            print(
                f"  Use --fetch to get live data, or seasonal averages are available via 'venues --detail {venue_id}'"
            )

    db.close()


def cmd_leaderboard(args):
    """Handle 'leaderboard' subcommand."""
    db = ensure_db(args)
    results = db.sim_runs.leaderboard(venue_id=args.venue_id, limit=args.limit or 20)

    if not results:
        print("  No simulation runs recorded yet.")
        print("  Use: python -m motoquant.run sim --bike-id 1 --save-run")
    else:
        headers = [
            "Rank",
            "Manufacturer",
            "Model",
            "ET (s)",
            "Trap (km/h)",
            "60ft (s)",
            "Config ID",
        ]
        rows = []
        for i, r in enumerate(results, 1):
            rows.append(
                [
                    i,
                    r.get("manufacturer_name", "-"),
                    r.get("model_name", "-"),
                    f"{r['et_quarter_s']:.3f}",
                    f"{r['trap_speed_kmh']:.1f}" if r.get("trap_speed_kmh") else "-",
                    f"{r['time_60ft_s']:.3f}" if r.get("time_60ft_s") else "-",
                    r["bike_config_id"],
                ]
            )
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
        headers = [
            "Run ID",
            "ET (s)",
            "Trap (km/h)",
            "60ft (s)",
            "Version",
            "Date",
            "Parts",
        ]
        rows = []
        for r in results:
            parts = json.loads(r["applied_parts"]) if r.get("applied_parts") else []
            rows.append(
                [
                    r["id"],
                    f"{r['et_quarter_s']:.3f}",
                    f"{r['trap_speed_kmh']:.1f}" if r.get("trap_speed_kmh") else "-",
                    f"{r['time_60ft_s']:.3f}" if r.get("time_60ft_s") else "-",
                    r.get("sim_version") or "-",
                    r["created_at"][:19] if r.get("created_at") else "-",
                    f"{len(parts)} mods" if parts else "stock",
                ]
            )
        print("\n  Run History:")
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
        from .scraper.importer import import_batch
        from .scraper.validator import score_spec, validate_spec
    except ImportError as e:
        print(f"  Scraper module not available: {e}")
        return

    manufacturer = args.manufacturer
    if not manufacturer:
        print(
            "  Error: specify --manufacturer NAME  or  --bulk  for a full catalog run"
        )
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

                        def raise_for_status(self):
                            pass

                    return _R()
            except Exception as err:

                class _Err:
                    status_code = 0
                    text = ""
                    error = err

                    def raise_for_status(self):
                        raise OSError(str(self.error))

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
            print(
                f"  {status} {spec.manufacturer} {spec.model_name} "
                f"({spec.year_from or '?'})  "
                f"conf={score:.2f}  "
                f"{spec.displacement_cc or '?'}cc  "
                f"{spec.peak_power_hp or '?'}hp"
                f"{warnings_str}"
            )
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
            DEFAULT_CHECKPOINT,
            print_checkpoint_status,
            run_bulk_scrape,
        )
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
        print(
            f"  {'#':>3}  {'Manufacturer':<22} {'P':>2}  {'cc+':>5}  {'Years':<11}  Categories"
        )
        print(f"  {'─' * 3}  {'─' * 22} {'─' * 2}  {'─' * 5}  {'─' * 11}  {'─' * 20}")
        for i, e in enumerate(SCRAPE_CATALOG, 1):
            cats = "/".join(e.get("categories", []))
            yr = f"{e.get('year_from', 2000)}-{e.get('year_to', 2026)}"
            print(
                f"  {i:>3}  {e['manufacturer']:<22} {e.get('priority', 3):>2}  "
                f"{e.get('min_cc', 600):>5}  {yr:<11}  {cats}"
            )
        return

    # ── Actual bulk run ───────────────────────────────────────────────────────
    dry_run = getattr(args, "dry_run", False)
    resume = not getattr(args, "no_resume", False)
    priority = getattr(args, "priority", 3)
    only = getattr(args, "only", None)
    limit = getattr(args, "limit", 300) or 300
    rate = getattr(args, "rate", 1.5) or 1.5

    print("\n  MotoQuant Bulk Scraper")
    print("  ─────────────────────────────────────────────")
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
        # Re-seed tire fitments so newly-imported bikes get OEM tire links
        try:
            from .database.seed import seed_bike_tire_fitments

            n_fits = seed_bike_tire_fitments(db)
            print(f"    Tire fitments:   {n_fits} (rebuilt for new bikes)")
        except Exception as e:
            print(f"    Tire fitment refresh skipped: {e}")

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
        print("\nAvailable venues (built-in):")
        for key, (desc, _) in VENUE_REGISTRY.items():
            print(f"  {key:16s}  {desc}")
        print("\n  (default)         Sea Level Reference (0m, 25C, 50% RH)")
        # Also show DB info if available
        try:
            db = get_db(args)
            db.initialize()
            stats = db.stats()
            if stats.get("bike_models", 0) > 0:
                print(f"\nDatabase ({db.path}):")
                print(
                    f"  Bikes: {stats['bike_models']} | "
                    f"Tires: {stats['tire_models']} | "
                    f"Venues: {stats['venues']} | "
                    f"Parts: {stats['parts']}"
                )
                print(
                    "  Use subcommands for full DB access: bikes, sim, venues, tires, parts"
                )
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


def cmd_calibrate(args):
    """Handle 'calibrate' subcommand — Phase 3 data import and calibration."""
    import json as _json

    if not hasattr(args, "cal_command") or args.cal_command is None:
        print("Usage: motoquant calibrate <sub-command>")
        print("  import-dragy FILE   Parse a Dragy GPS timer export file")
        print("  import-dyno FILE    Parse a dyno CSV and apply SAE J1349 correction")
        print("  import-ecu  FILE    Parse a Woolich/PC-Link/MoTeC ECU log file")
        print("  overlay     FILE    Compare simulation against a real GPS run")
        return 0

    if args.cal_command == "import-dragy":
        try:
            from .calibration.dragy import DragParseError, best_run, parse_dragy_file
        except ImportError as exc:
            print(f"  Calibration module not available: {exc}")
            return 1

        try:
            runs = parse_dragy_file(args.file)
        except FileNotFoundError:
            print(f"  File not found: {args.file}")
            return 1
        except DragParseError as exc:
            print(f"  Parse error: {exc}")
            return 1

        if not runs:
            print("  No valid quarter-mile runs detected in file.")
            return 1

        display_runs = [best_run(runs)] if args.best else runs

        if args.output_json:
            print(_json.dumps([r.to_dict() for r in display_runs], indent=2))
        else:
            print(f"\n  Dragy import: {args.file}")
            print(f"  Runs detected: {len(runs)}")
            for r in display_runs:
                splits = r.splits()
                print(f"\n  Run #{r.run_index + 1}")
                print(f"    ET (1/4 mile) : {r.et_quarter:.4f} s")
                print(
                    f"    Trap speed    : {r.trap_speed_kmh:.1f} km/h  ({r.trap_speed_mph:.1f} mph)"
                )
                print(f"    Sample rate   : {r.sample_rate_hz:.1f} Hz")
                print(f"    Duration      : {r.duration_s:.2f} s")
                if splits:
                    print("    Splits        :", end="")
                    for name, et in splits.items():
                        print(f"  {name}={et:.3f}s", end="")
                    print()
        return 0

    if args.cal_command == "import-dyno":
        try:
            from .calibration.dyno import DynoParseError, parse_dyno_file
        except ImportError as exc:
            print(f"  Calibration module not available: {exc}")
            return 1

        kw = {}
        if hasattr(args, "temp") and args.temp is not None:
            kw["temp_c"] = args.temp
        if hasattr(args, "pressure") and args.pressure is not None:
            kw["pressure_kpa"] = args.pressure
        if hasattr(args, "rh") and args.rh is not None:
            kw["rh_pct"] = args.rh
        kw["is_at_wheel"] = not getattr(args, "crank", False)

        try:
            result = parse_dyno_file(args.file, **kw)
        except FileNotFoundError:
            print(f"  File not found: {args.file}")
            return 1
        except DynoParseError as exc:
            print(f"  Parse error: {exc}")
            return 1

        if args.output_json:
            print(_json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\n  Dyno import: {args.file}")
            print(
                f"  Peak power  : {result.peak_power_kw:.1f} kW  ({result.peak_power_hp:.0f} hp)"
                f"  @ {result.rpm_at_peak_power:.0f} rpm"
            )
            print(
                f"  Peak torque : {result.peak_torque_nm:.1f} Nm"
                f"  @ {result.rpm_at_peak_torque:.0f} rpm"
            )
            print(
                f"  SAE CF      : {result.correction_factor:.5f}"
                f"  ({'corrected' if result.correction_factor != 1.0 else 'uncorrected'})"
            )
            print(f"  At wheel    : {result.is_at_wheel}")
        return 0

    if args.cal_command == "overlay":
        try:
            from .calibration.dragy import DragParseError, best_run, parse_dragy_file
            from .calibration.overlay import compare_runs
            from .defaults import gsxr1000_k5
        except ImportError as exc:
            print(f"  Calibration module not available: {exc}")
            return 1

        try:
            runs = parse_dragy_file(args.file)
        except (FileNotFoundError, DragParseError) as exc:
            print(f"  {exc}")
            return 1
        if not runs:
            print("  No valid runs in file.")
            return 1

        real = best_run(runs) if args.best else runs[0]

        # Load config from DB if --bike-id given, else use default K5
        db_path = getattr(args, "db", None)
        cfg = None
        if getattr(args, "bike_id", None):
            try:
                from .database.bridge import bike_row_to_config
                from .database.connection import connect

                conn = connect(db_path)
                row = conn.execute(
                    "SELECT * FROM bike_models WHERE id=?", (args.bike_id,)
                ).fetchone()
                if row:
                    cfg = bike_row_to_config(dict(row))
            except Exception:
                pass
        if cfg is None:
            cfg = gsxr1000_k5()

        from .physics import MotoQuantEngine

        sim = MotoQuantEngine(cfg).run()
        cmp = compare_runs(real, sim)
        if args.output_json:
            print(_json.dumps(cmp.to_dict(), indent=2))
        else:
            cmp.print_report()
        return 0

    if args.cal_command == "import-ecu":
        try:
            from .calibration.ecu import ECUParseError, parse_ecu_file
        except ImportError as exc:
            print(f"  Calibration module not available: {exc}")
            return 1

        try:
            log = parse_ecu_file(args.file)
        except FileNotFoundError:
            print(f"  File not found: {args.file}")
            return 1
        except ECUParseError as exc:
            print(f"  Parse error: {exc}")
            return 1

        if args.output_json:
            print(_json.dumps(log.to_dict(), indent=2))
            return 0

        print(f"\n  ECU log import: {args.file}")
        print(f"  Logger type  : {log.logger_type}")
        print(f"  Sample rate  : {log.sample_rate_hz:.0f} Hz")
        print(f"  Total samples: {log.n_samples:,}")
        print(f"  Channels     : {', '.join(log.channel_names)}")
        print(f"  Runs detected: {len(log.runs)}")

        display_runs = [log.best_run()] if (args.best and log.best_run()) else log.runs

        for run in display_runs:
            import math

            print(f"\n  Run #{run.run_index + 1}")
            if not math.isnan(run.et_quarter):
                print(f"    ET (1/4 mile) : {run.et_quarter:.4f} s")
                print(f"    Trap speed    : {run.trap_speed_kmh:.1f} km/h")
            else:
                print("    ET (1/4 mile) : not reached")
            print(f"    Peak RPM      : {run.peak_rpm:.0f} rpm")
            print(f"    Peak speed    : {run.peak_speed_ms * 3.6:.1f} km/h")
            print(f"    Launch RPM    : {run.launch_rpm:.0f} rpm")
            print(f"    Duration      : {run.duration_s:.2f} s")

            if not args.best:
                splits = run.splits()
                if splits:
                    print("    Splits        :", end="")
                    for name, et in splits.items():
                        print(f"  {name}={et:.3f}s", end="")
                    print()

        if getattr(args, "channels", False):
            print("\n  All channels in file:")
            for ch in log.channel_names:
                print(f"    {ch}")
        return 0

    print(f"  Unknown calibrate sub-command: {args.cal_command}")
    return 1


# ═══════════════════════════════════════════
# PHASE 4 — ANALYSIS SUBCOMMAND
# ═══════════════════════════════════════════


def cmd_analysis(args):
    """Handle 'analysis' subcommand: roi and sobol sub-commands."""
    import json as _json

    sub = getattr(args, "analysis_command", None)

    # ── analysis roi ─────────────────────────────────────────────
    if sub == "roi":
        from .analysis.roi import compute_parts_roi, find_best_build, rank_categories

        db = ensure_db(args)
        parts_repo = db.parts

        # Resolve bike
        if args.bike_id:
            config_row = db.bikes.get_current_config(args.bike_id)
            if config_row is None:
                print(f"  Error: no config found for bike model ID {args.bike_id}.")
                return 1
            config = db.bikes.to_config(config_row["id"])
            model_row = db.bikes.get_model(args.bike_id)
            if model_row:
                bike_name = (
                    f"{model_row['manufacturer_name']} {model_row['model_name']}"
                )
                if model_row.get("model_code"):
                    bike_name += f" {model_row['model_code']}"
            else:
                bike_name = f"Bike {args.bike_id}"
            bike_mid = args.bike_id
        else:
            from .defaults import gsxr1000_k5

            config = gsxr1000_k5()
            bike_name = "GSX-R 1000 K5 (default)"
            bike_mid = None

        # Resolve parts list
        if args.part_ids:
            part_ids = [int(x) for x in args.part_ids.split(",")]
        elif args.category:
            raw = parts_repo.search(category=args.category, limit=200)
            part_ids = [p["id"] for p in raw]
        else:
            raw = parts_repo.search(limit=200)
            part_ids = [p["id"] for p in raw]

        if getattr(args, "optimize", False):
            # Budget-optimised build
            budget = args.budget or 100_000
            build = find_best_build(
                base_config=config,
                budget_inr=budget,
                parts_repo=parts_repo,
                part_ids=part_ids if args.part_ids else None,
                category_filter=args.category or None,
                bike_model_id=bike_mid,
            )
            if getattr(args, "output_json", False):
                out = {
                    "bike": bike_name,
                    "budget_inr": build.budget_inr,
                    "total_cost_inr": build.total_cost_inr,
                    "base_et_s": round(build.base_et_s, 4),
                    "modified_et_s": round(build.modified_et_s, 4),
                    "delta_et_s": round(build.delta_et_s, 4),
                    "delta_trap_ms": round(build.delta_trap_ms, 4),
                    "selected_parts": [
                        {
                            "part_id": p.part_id,
                            "name": p.part_name,
                            "category": p.category_display,
                            "price_inr": p.price_inr,
                            "delta_et_s": round(p.delta_et_s, 4),
                            "roi_score": round(p.roi_score, 4),
                            "cost_per_tenth_inr": (
                                round(p.cost_per_tenth_inr, 0)
                                if p.cost_per_tenth_inr < 1e9
                                else None
                            ),
                        }
                        for p in build.selected_parts
                    ],
                }
                print(_json.dumps(out, indent=2))
            else:
                print(f"\n  ╔══ BUILD OPTIMIZER — {bike_name} ══╗")
                print(build.summary())
                print(
                    f"\n  Parts evaluated: {build.parts_evaluated}  "
                    f"(skipped {build.parts_skipped_incompatible} incompatible, "
                    f"{build.parts_skipped_no_gain} no-gain)"
                )
            return 0

        # Individual ROI ranking
        results = compute_parts_roi(
            base_config=config,
            part_ids=part_ids,
            parts_repo=parts_repo,
            bike_model_id=bike_mid,
        )

        if getattr(args, "output_json", False):
            out = {
                "bike": bike_name,
                "base_et": round(results[0].base_et_s, 4) if results else None,
                "parts": [
                    {
                        "part_id": r.part_id,
                        "name": r.part_name,
                        "category": r.category_display,
                        "price_inr": r.price_inr,
                        "delta_et_s": round(r.delta_et_s, 4),
                        "delta_trap_ms": round(r.delta_trap_ms, 4),
                        "roi_score": round(r.roi_score, 4),
                        "cost_per_tenth_inr": (
                            round(r.cost_per_tenth_inr, 0)
                            if r.cost_per_tenth_inr < 1e9
                            else None
                        ),
                        "availability": r.availability,
                    }
                    for r in results
                ],
            }
            print(_json.dumps(out, indent=2))
        else:
            base_et = results[0].base_et_s if results else 0.0
            print(f"\n  ╔══ PARTS ROI RANKING — {bike_name} ══╗")
            print(f"  Base ET: {base_et:.3f}s\n")
            print(
                f"  {'ID':>3}  {'Part':<35} {'ΔET':>10}  {'ROI':>8}  {'Cost/tenth':>14}  Price"
            )
            print("  " + "─" * 82)
            for r in results:
                sign = "▲" if r.delta_et_s > 0 else ("▼" if r.delta_et_s < 0 else "─")
                et_s = f"{abs(r.delta_et_s):.3f}s {sign}"
                roi = f"{r.roi_score:.3f}" if r.roi_score < 999 else "∞"
                cpt = (
                    f"₹{r.cost_per_tenth_inr:,.0f}"
                    if r.cost_per_tenth_inr < 1e9
                    else "no gain"
                )
                price = f"₹{r.price_inr:,.0f}" if r.price_inr else "free"
                print(
                    f"  [{r.part_id:>3}] {r.part_name:<35} {et_s:>10}  {roi:>8}  {cpt:>14}  {price}"
                )

            if getattr(args, "by_category", False):
                print("\n  ── CATEGORY SUMMARY ──")
                cats = rank_categories(results)
                for c in cats:
                    print(
                        f"  {c['category']:<28}  best ΔET={c['best_et_gain_s']:.3f}s  "
                        f"ROI={c['best_roi']:.3f}  avg ₹/tenth={c['avg_cost_per_tenth']:,.0f}  "
                        f"({c['improving_count']}/{c['part_count']} parts help)"
                    )

        return 0

    # ── analysis sobol ────────────────────────────────────────────
    if sub == "sobol":
        from .analysis.sobol import (
            compute_sobol_indices,
            compute_sobol_subset,
        )

        # Resolve bike config
        if args.bike_id:
            db = ensure_db(args)
            config_row = db.bikes.get_current_config(args.bike_id)
            if config_row is None:
                print(f"  Error: no config found for bike model ID {args.bike_id}.")
                return 1
            config = db.bikes.to_config(config_row["id"])
            model_row = db.bikes.get_model(args.bike_id)
            if model_row:
                bike_name = (
                    f"{model_row['manufacturer_name']} {model_row['model_name']}"
                )
                if model_row.get("model_code"):
                    bike_name += f" {model_row['model_code']}"
            else:
                bike_name = f"Bike {args.bike_id}"
        else:
            from .defaults import gsxr1000_k5

            config = gsxr1000_k5()
            bike_name = "GSX-R 1000 K5 (default)"

        n_samples = getattr(args, "n_samples", 128)
        verbose = not getattr(args, "output_json", False)

        if getattr(args, "params", None):
            param_keys = [p.strip() for p in args.params.split(",")]
            result = compute_sobol_subset(
                config,
                param_keys=param_keys,
                n_samples=n_samples,
                verbose=verbose,
            )
        else:
            result = compute_sobol_indices(
                config,
                n_samples=n_samples,
                verbose=verbose,
            )

        if getattr(args, "output_json", False):
            d = result.to_dict()
            d["bike"] = bike_name
            print(_json.dumps(d, indent=2))
        else:
            print(f"\n  ╔══ SOBOL SENSITIVITY — {bike_name} ══╗")
            result.print_table()
            print(
                "\n  S1  = first-order index (direct effect, higher = more influential)\n"
                "  ST  = total-order index (direct + interaction effects)\n"
                "  ±   = 95% CI half-width (smaller = more reliable estimate)\n"
                "  Interact = ST - S1 (non-zero = interacts with other params)\n"
            )

        return 0

    # ── analysis optimize ───────────────────────────────────────────
    if sub == "optimize":
        from .analysis.bayesian_opt import optimize_build

        # Resolve bike config
        if args.bike_id:
            db = ensure_db(args)
            config_row = db.bikes.get_current_config(args.bike_id)
            if config_row is None:
                print(f"  Error: no config found for bike model ID {args.bike_id}.")
                return 1
            config = db.bikes.to_config(config_row["id"])
            model_row = db.bikes.get_model(args.bike_id)
            if model_row:
                bike_name = (
                    f"{model_row['manufacturer_name']} {model_row['model_name']}"
                )
                if model_row.get("model_code"):
                    bike_name += f" {model_row['model_code']}"
            else:
                bike_name = f"Bike {args.bike_id}"
        else:
            from .defaults import gsxr1000_k5

            config = gsxr1000_k5()
            bike_name = "GSX-R 1000 K5 (default)"

        budget = getattr(args, "budget", 100_000) or 100_000
        n_iter = getattr(args, "iterations", 50) or 50
        verbose = not getattr(args, "output_json", False)

        try:
            result = optimize_build(
                config=config,
                budget_inr=budget,
                n_iterations=n_iter,
                verbose=verbose,
            )
        except ImportError as exc:
            print(f"  Error: BoTorch not installed — {exc}")
            print(
                "  Install with: pip install botorch gpytorch --break-system-packages"
            )
            return 1

        if getattr(args, "output_json", False):
            out = result.to_dict()
            out["bike"] = bike_name
            import json as _json

            print(_json.dumps(out, indent=2))
        else:
            print(f"\n  ╔══ BAYESIAN BUILD OPTIMIZER — {bike_name} ══╗")
            print(result.summary())

        return 0

    # ── analysis recommend ──────────────────────────────────────
    if sub == "recommend":
        from .analysis.recommendations import (
            BuildProfile,
            generate_upgrade_path,
            get_category_upgrade_order,
            recommend_build,
        )

        db = ensure_db(args)
        parts_repo = db.parts

        # Resolve bike
        if getattr(args, "bike_id", None):
            config_row = db.bikes.get_current_config(args.bike_id)
            if config_row is None:
                print(f"  Error: no config found for bike model ID {args.bike_id}.")
                return 1
            config = db.bikes.to_config(config_row["id"])
            model_row = db.bikes.get_model(args.bike_id)
            if model_row:
                bike_name = (
                    f"{model_row['manufacturer_name']} {model_row['model_name']}"
                )
                if model_row.get("model_code"):
                    bike_name += f" {model_row['model_code']}"
            else:
                bike_name = f"Bike {args.bike_id}"
            bike_mid = args.bike_id
        else:
            from .defaults import gsxr1000_k5

            config = gsxr1000_k5()
            bike_name = "GSX-R 1000 K5 (default)"
            bike_mid = None

        # Resolve profile
        profile_name = getattr(args, "profile", "all")
        try:
            profile = BuildProfile(profile_name)
        except ValueError:
            print(
                f"  Error: unknown profile '{profile_name}'. Use: all, street_legal, drag_prep, full_race"
            )
            return 1

        budget = getattr(args, "budget", 100_000)

        # Mode: upgrade-path vs single recommendation vs category-order
        mode = getattr(args, "mode", "recommend")

        if mode == "upgrade-path":
            n_tiers = getattr(args, "tiers", 3)
            path = generate_upgrade_path(
                base_config=config,
                parts_repo=parts_repo,
                profile=profile,
                bike_model_id=bike_mid,
                n_tiers=n_tiers,
            )
            if getattr(args, "output_json", False):
                print(_json.dumps(path.to_dict(), indent=2))
            else:
                print(f"\n{path.summary()}")
            return 0

        if mode == "category-order":
            result = get_category_upgrade_order(
                base_config=config,
                parts_repo=parts_repo,
                profile=profile,
                bike_model_id=bike_mid,
            )
            if getattr(args, "output_json", False):
                out = [
                    {
                        "rank": e["rank"],
                        "category": e["category"],
                        "et_gain_s": e["et_gain_s"],
                        "price_inr": e["price_inr"],
                        "reason": e["reason"],
                    }
                    for e in result
                ]
                print(_json.dumps(out, indent=2))
            else:
                print(f"\n  ╔══ CATEGORY UPGRADE ORDER — {bike_name} ══╗")
                print(f"  Profile: {profile.value}")
                for e in result:
                    print(f"  {e['rank']:>2}. {e['category']:<20} {e['reason']}")
            return 0

        # Default: single budget recommendation
        rec = recommend_build(
            base_config=config,
            budget_inr=budget,
            parts_repo=parts_repo,
            profile=profile,
            bike_model_id=bike_mid,
        )
        if getattr(args, "output_json", False):
            print(_json.dumps(rec.to_dict(), indent=2))
        else:
            print(f"\n{rec.summary()}")

        return 0

    # ── analysis surrogate ───────────────────────────────────────
    if sub == "surrogate":
        return _cmd_analysis_surrogate(args)

    print(f"  Unknown analysis sub-command: {sub}")
    return 1


def _cmd_analysis_surrogate(args) -> int:
    """Handle 'analysis surrogate' sub-commands: generate, train, predict, evaluate."""
    from .analysis.surrogate_data import (
        SurrogateDataset,
        generate_training_data,
    )
    from .analysis.surrogate_xgb import XGBSurrogate, train_surrogate

    sub2 = getattr(args, "surrogate_command", None)
    db_path = getattr(args, "db", None) or "motoquant.db"

    def _load_config(bike_id):
        """Load BikeConfig from DB by ID, or fall back to K5 default."""
        if bike_id is not None:
            from .database.bridge import db_row_to_config
            from .database.connection import MotoQuantDB

            db = MotoQuantDB(db_path)
            with db.connect() as conn:
                row = conn.execute(
                    "SELECT * FROM bikes WHERE id = ?", (bike_id,)
                ).fetchone()
            if row is None:
                print(f"  Bike ID {bike_id} not found in DB.")
                return None
            return db_row_to_config(dict(row))
        from .defaults import gsxr1000_k5

        return gsxr1000_k5()

    # ── generate ─────────────────────────────────────────────────
    if sub2 == "generate":
        n = args.n_samples
        seed = args.seed
        out = args.output
        bike_id = getattr(args, "bike_id", None)

        config = _load_config(bike_id)
        if config is None:
            return 1

        bike_label = f"bike_id={bike_id}" if bike_id else "GSX-R 1000 K5 (default)"
        print(f"  Generating {n:,} surrogate training samples")
        print(f"  Template  : {bike_label}")
        print(f"  Seed      : {seed}")
        print(f"  Output    : {out}")
        print()

        def _progress(done, total):
            pct = done / total * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"\r  [{bar}] {done:>6}/{total}  ({pct:.0f}%)", end="", flush=True)

        dataset = generate_training_data(
            config,
            n_samples=n,
            seed=seed,
            progress_callback=_progress,
        )
        print()  # newline after progress bar

        dataset.save(out)
        rate = len(dataset) / max(dataset.elapsed_s, 0.001)
        print(f"  ✓ Saved {len(dataset):,} samples → {out}")
        print(f"    Elapsed : {dataset.elapsed_s:.1f}s  ({rate:.0f} sims/s)")

        if getattr(args, "output_json", False):
            import json

            print(
                json.dumps(
                    {
                        "n_collected": len(dataset),
                        "n_requested": n,
                        "elapsed_s": round(dataset.elapsed_s, 2),
                        "output": out,
                    }
                )
            )
        return 0

    # ── train ────────────────────────────────────────────────────
    if sub2 == "train":
        data_path = args.data
        model_path = args.model_out
        test_frac = getattr(args, "test_fraction", 0.15)

        if not __import__("pathlib").Path(data_path).exists():
            print(f"  Data file not found: {data_path}")
            print("  Run: analysis surrogate generate --output <file.npz>")
            return 1

        print(f"  Loading dataset : {data_path}")
        dataset = SurrogateDataset.load(data_path)
        print(f"  Samples loaded  : {len(dataset):,}")
        print(f"  Training XGBoost surrogate (test fraction = {test_frac:.0%}) …")

        model, metrics = train_surrogate(
            dataset,
            test_fraction=test_frac,
            verbose=False,
        )
        model.save(model_path)
        print(f"  ✓ Model saved → {model_path}")
        metrics.print_report()

        if getattr(args, "output_json", False):
            import json

            print(json.dumps({"model": model_path, "metrics": metrics.to_dict()}))
        return 0

    # ── evaluate ─────────────────────────────────────────────────
    if sub2 == "evaluate":
        model_path = args.model
        data_path = args.data
        test_frac = getattr(args, "test_fraction", 0.15)

        for p in (model_path, data_path):
            if not __import__("pathlib").Path(p).exists():
                print(f"  File not found: {p}")
                return 1

        model = XGBSurrogate.load(model_path)
        dataset = SurrogateDataset.load(data_path)
        _, test_ds = dataset.split(test_fraction=test_frac, seed=0)
        X_te, y_et_te, y_trap_te = test_ds.to_arrays()

        print(f"  Model   : {model_path}  (trained on {model.n_train:,} samples)")
        print(
            f"  Dataset : {data_path}  ({len(dataset):,} total → {len(test_ds):,} test)"
        )
        metrics = model.evaluate(X_te, y_et_te, y_trap_te)
        metrics.print_report()

        # Feature importance
        imp = model.feature_importance()
        print("\n  Feature Importance (ET model, gain-based):")
        for name, score in list(imp.items())[:8]:
            bar = "█" * int(score * 400)
            print(f"    {name:<28} {score:.4f}  {bar}")

        if getattr(args, "output_json", False):
            import json

            print(json.dumps({"metrics": metrics.to_dict(), "feature_importance": imp}))
        return 0

    # ── train-dnn ────────────────────────────────────────────────
    if sub2 == "train-dnn":
        from .analysis.surrogate_dnn import DNNSurrogate, train_dnn_surrogate

        data_path = args.data
        model_path = args.model_out
        test_frac = getattr(args, "test_fraction", 0.15)
        epochs = getattr(args, "epochs", 300)
        filter_pw = getattr(args, "filter_min_pw", 0.12)

        if not __import__("pathlib").Path(data_path).exists():
            print(f"  Data file not found: {data_path}")
            print("  Run: analysis surrogate generate --output <file.npz>")
            return 1

        backend = (
            "torch" if __import__("importlib").util.find_spec("torch") else "sklearn"
        )
        print(
            f"  Backend         : {backend} ({'GPU available' if backend == 'torch' and __import__('torch').cuda.is_available() else 'CPU'})"
        )
        print(f"  Loading dataset : {data_path}")
        dataset = SurrogateDataset.load(data_path)
        if filter_pw > 0:
            dataset = dataset.filter(min_power_to_weight=filter_pw)
        print(f"  Samples         : {len(dataset):,}")
        print(f"  Epochs          : up to {epochs} (early stopping patience=25)")
        print("  Architecture    : 21 → 256 → 512 → 512 → 256 → 2 (ET + trap)")
        print()

        model, metrics = train_dnn_surrogate(
            dataset,
            test_fraction=test_frac,
            epochs=epochs,
            verbose=True,
        )
        model.save(model_path)
        print(f"\n  ✓ Model saved → {model_path}")
        metrics.print_report()

        if getattr(args, "output_json", False):
            import json

            print(
                json.dumps(
                    {
                        "model": model_path,
                        "backend": model.backend,
                        "metrics": metrics.to_dict(),
                    }
                )
            )
        return 0

    # ── predict ──────────────────────────────────────────────────
    if sub2 == "predict":
        model_path = args.model
        bike_id = getattr(args, "bike_id", None)

        if not __import__("pathlib").Path(model_path).exists():
            print(f"  Model file not found: {model_path}")
            print("  Run: analysis surrogate train / train-dnn to create a model")
            return 1

        config = _load_config(bike_id)
        if config is None:
            return 1

        # Auto-detect model type from saved payload
        import joblib as _jl

        _payload = _jl.load(model_path)
        if (
            "torch_state_dict" in _payload
            or ("backend" in _payload and _payload["backend"] == "torch")
            or "sklearn_et" in _payload
        ):
            from .analysis.surrogate_dnn import DNNSurrogate

            model = DNNSurrogate.load(model_path)
        else:
            model = XGBSurrogate.load(model_path)
        et, trap = model.predict_config(config)
        trap_kmh = trap * 3.6

        if getattr(args, "output_json", False):
            import json

            print(json.dumps({"et_s": round(et, 4), "trap_kmh": round(trap_kmh, 2)}))
        else:
            bike_label = f"bike_id={bike_id}" if bike_id else "GSX-R 1000 K5 (default)"
            print(f"  Bike    : {bike_label}")
            print(f"  ET      : {et:.3f}s")
            print(f"  Trap    : {trap_kmh:.1f} km/h")
        return 0

    print(f"  Unknown surrogate sub-command: {sub2!r}")
    print("  Valid sub-commands: generate, train, evaluate, predict")
    return 1


# ═══════════════════════════════════════════
# NL (NATURAL LANGUAGE) COMMAND
# ═══════════════════════════════════════════


def cmd_pricing(args):
    """
    Indian-market parts pricing refresh / health-check.

    Verbs:
      refresh  — fill `retailer_url` + bump `last_price_check` for every part
      status   — coverage snapshot (what fraction of parts have price/URL/recent check)
      stale    — list parts whose last_price_check is older than --days (default 30)
    """
    from .database.pricing_refresh import (
        coverage_report,
        estimate_landing_cost_inr,
        refresh_retailer_urls,
        stale_parts,
    )

    verb = getattr(args, "pricing_action", None)
    output_json = getattr(args, "output_json", False)

    db = ensure_db(args)
    conn = db.conn

    if verb == "refresh":
        summary = refresh_retailer_urls(
            conn,
            only_missing=not getattr(args, "overwrite", False),
            dry_run=getattr(args, "dry_run", False),
        )
        payload = {
            "total": summary.total,
            "urls_filled": summary.urls_filled,
            "check_stamps_updated": summary.check_stamps_updated,
            "skipped_no_retailer": summary.skipped_no_retailer,
            "dry_run": bool(getattr(args, "dry_run", False)),
        }
        if output_json:
            print(json.dumps(payload, indent=2))
        else:
            print()
            print(
                f"  Pricing refresh ({'dry-run' if payload['dry_run'] else 'committed'}):"
            )
            print(f"    Total parts .............. {summary.total}")
            print(f"    URLs filled .............. {summary.urls_filled}")
            print(f"    Check-stamps updated ..... {summary.check_stamps_updated}")
            print(f"    Skipped (no retailer) .... {summary.skipped_no_retailer}")
        db.close()
        return 0

    if verb == "status":
        report = coverage_report(conn)
        # Add a sample landing-cost projection so the user can eyeball the
        # GST+courier+duty math on a "typical" ₹25k part at a click.
        report["sample_25000_domestic_inr"] = estimate_landing_cost_inr(
            25_000.0, retailer="MotoParts India"
        )
        report["sample_25000_imported_inr"] = estimate_landing_cost_inr(
            25_000.0, retailer="Akrapovic EU"
        )
        if output_json:
            print(json.dumps(report, indent=2))
        else:
            print()
            print("  Parts pricing coverage:")
            print(f"    Total parts ............... {report['total_parts']}")
            print(
                f"    With retailer ............. {report['with_retailer']}"
                f" ({report['retailer_coverage_pct']} %)"
            )
            print(
                f"    With retailer_url ......... {report['with_retailer_url']}"
                f" ({report['url_coverage_pct']} %)"
            )
            print(
                f"    With price_inr ............ {report['with_price_inr']}"
                f" ({report['price_coverage_pct']} %)"
            )
            print(
                f"    Refreshed last 30 days .... {report['refreshed_last_30_days']}"
                f" ({report['freshness_pct']} %)"
            )
            print()
            print("  Landing-cost sample (₹25 000 sticker):")
            print(
                f"    Domestic (GST+courier) .... ₹{report['sample_25000_domestic_inr']:,.0f}"
            )
            print(
                f"    Imported (+30 % duty) ..... ₹{report['sample_25000_imported_inr']:,.0f}"
            )
        db.close()
        return 0

    if verb == "stale":
        days = getattr(args, "days", None) or 30
        rows = stale_parts(conn, days_threshold=days)
        if output_json:
            print(
                json.dumps(
                    [
                        {
                            "id": r[0],
                            "brand": r[1],
                            "model_name": r[2],
                            "last_check": r[3],
                        }
                        for r in rows
                    ],
                    indent=2,
                )
            )
        else:
            if not rows:
                print(f"  No parts stale beyond {days} days. ✓")
            else:
                print(f"  Parts needing refresh (>{days} days old): {len(rows)}")
                print_table(
                    ["ID", "Brand", "Model", "Last check"],
                    [
                        (r[0], (r[1] or "-")[:24], (r[2] or "-")[:40], r[3])
                        for r in rows[:50]
                    ],
                )
                if len(rows) > 50:
                    print(
                        f"  ... and {len(rows) - 50} more (run with --json for the full list)"
                    )
        db.close()
        return 0

    print("  Error: no pricing action specified. Use: refresh | status | stale")
    db.close()
    return 1


def cmd_nl(args):
    """
    Natural language tuning interface.
    Takes a user query like "optimize my Hayabusa for 35°C at Aamby Valley"
    and translates it into simulation parameters and results.
    """
    from .nlp import NLSimRunner, format_nl_result

    query = getattr(args, "query", None)
    if not query:
        print("  Error: No query provided. Usage: nl 'your query here'")
        return 1

    db = ensure_db(args)
    runner = NLSimRunner(db)

    try:
        result = runner.run_query(query)
        output = format_nl_result(result)
        print(output)

        if getattr(args, "output_json", False):
            import json as _json

            # Remove non-JSON-serializable objects if present
            json_result = {k: v for k, v in result.items() if k != "config"}
            print(_json.dumps(json_result, indent=2))

        return 0

    except Exception as e:
        print(f"  Error running query: {e}")
        import traceback

        if getattr(args, "verbose", False):
            traceback.print_exc()
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="motoquant",
        description="MotoQuant Pro — Motorcycle Drag Racing Simulation Engine (Phase 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"Path to MotoQuant database (default: {DEFAULT_DB_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── db ──
    p_db = subparsers.add_parser("db", help="Database management")
    p_db.add_argument(
        "db_action",
        choices=["init", "seed", "stats"],
        help="init: create tables | seed: load reference data | stats: show counts",
    )

    # ── bikes ──
    p_bikes = subparsers.add_parser("bikes", help="List/search bikes in database")
    p_bikes.add_argument("--search", "-s", type=str, help="Search by model name")
    p_bikes.add_argument(
        "--manufacturer", "-m", type=str, help="Filter by manufacturer"
    )
    p_bikes.add_argument(
        "--category", type=str, help="Filter by category (sport/naked/cruiser)"
    )
    p_bikes.add_argument(
        "--displacement", type=str, help="Filter by cc range (e.g., 900-1300)"
    )
    p_bikes.add_argument("--power-min", type=float, help="Minimum HP")
    p_bikes.add_argument(
        "--quality",
        type=str,
        choices=[
            "scraped",
            "spec_sheet",
            "verified",
            "dyno_validated",
            "track_validated",
        ],
        help="Filter by data quality",
    )
    p_bikes.add_argument("--limit", type=int, default=50)
    p_bikes.add_argument("--json", dest="json_out", action="store_true")
    p_bikes.add_argument(
        "--fitments",
        type=int,
        metavar="BIKE_ID",
        help="Show OEM/recommended tire fitments for a specific bike ID",
    )

    # ── sim ──
    p_sim = subparsers.add_parser("sim", help="Run quarter-mile simulation")
    # DB-based bike selection
    p_sim.add_argument("--bike-id", type=int, help="Bike model ID from database")
    # Legacy bike selection (backward compat within sim subcommand)
    p_sim.add_argument(
        "--bike", dest="bike_legacy", type=str, help="Legacy built-in bike (k5/r1/busa)"
    )
    p_sim.add_argument(
        "--config", dest="config_file", type=str, help="Path to JSON config file"
    )
    # Venue / weather
    p_sim.add_argument("--venue-id", type=int, help="Venue ID from database")
    p_sim.add_argument(
        "--venue",
        dest="venue_legacy",
        type=str,
        help="Legacy venue (aamby-winter/aamby-summer)",
    )
    p_sim.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        metavar="1-12",
        help="Month for seasonal weather (1-12, default: current)",
    )
    p_sim.add_argument(
        "--weather-live",
        action="store_true",
        help="Fetch live weather from API (requires OPENWEATHERMAP_API_KEY)",
    )
    p_sim.add_argument("--api-key", type=str, help="OpenWeatherMap API key")
    p_sim.add_argument(
        "--track-temp", type=float, help="Override track surface temp (C)"
    )
    # Parts
    p_sim.add_argument(
        "--apply-parts",
        type=str,
        help="Comma-separated part IDs to apply (e.g., 3,5,8)",
    )
    p_sim.add_argument(
        "--compare-stock", action="store_true", help="Run stock vs modified comparison"
    )
    # Tires
    p_sim.add_argument(
        "--front-tire",
        type=int,
        metavar="TIRE_ID",
        help="Override front tire (DB tire_model ID). See: tires --grip-rank",
    )
    p_sim.add_argument(
        "--rear-tire",
        type=int,
        metavar="TIRE_ID",
        help="Override rear tire (DB tire_model ID). See: tires --grip-rank",
    )
    # Archival
    p_sim.add_argument(
        "--save-run", action="store_true", help="Save simulation result to database"
    )
    # Sim parameters
    p_sim.add_argument(
        "--distance",
        "-d",
        type=float,
        default=QUARTER_MILE_M,
        help="Simulation distance in meters",
    )
    p_sim.add_argument("--dt", type=float, default=0.001, help="Timestep (s)")
    # Output
    p_sim.add_argument("--json", "-j", dest="json_out", action="store_true")
    p_sim.add_argument("--csv", type=str, metavar="FILE")
    p_sim.add_argument("--quiet", "-q", action="store_true")

    # ── venues ──
    p_venues = subparsers.add_parser("venues", help="List venues and seasonal data")
    p_venues.add_argument(
        "--detail", type=int, metavar="ID", help="Show detailed info for a venue"
    )
    p_venues.add_argument("--country", type=str, default=None)
    p_venues.add_argument("--include-inactive", action="store_true")

    # ── tires ──
    p_tires = subparsers.add_parser("tires", help="Tire library")
    p_tires.add_argument(
        "--grip-rank",
        action="store_true",
        help="Rank tires by grip (weighted by confidence)",
    )
    p_tires.add_argument(
        "--value-rank",
        action="store_true",
        help="Rank tires by grip per rupee (Indian market)",
    )
    p_tires.add_argument(
        "--compound",
        type=str,
        choices=["street", "sport", "race", "drag_dot", "drag_slick"],
    )
    p_tires.add_argument("--position", type=str, choices=["front", "rear"])
    p_tires.add_argument("--manufacturer", type=str)
    p_tires.add_argument(
        "--india-only", action="store_true", help="Only show tires available in India"
    )

    # ── parts ──
    p_parts = subparsers.add_parser("parts", help="Performance parts catalog")
    p_parts.add_argument(
        "--category", type=str, help="Filter by category (sprocket/ecu/exhaust/...)"
    )
    p_parts.add_argument("--brand", type=str)
    p_parts.add_argument("--search", type=str)
    p_parts.add_argument("--max-price", type=float, help="Max price in INR")
    p_parts.add_argument("--available", action="store_true", help="Only in-stock items")
    p_parts.add_argument(
        "--bike-id",
        type=int,
        help="Filter parts to those compatible with a specific bike (by bike_model_id)",
    )
    p_parts.add_argument(
        "--build-cost",
        type=str,
        metavar="IDS",
        help="Calculate total cost for part IDs (e.g., 3,5,8,12)",
    )
    p_parts.add_argument(
        "--impact",
        type=int,
        metavar="PART_ID",
        help="Show ET/trap impact of applying a single part to --bike-id (requires --bike-id)",
    )
    p_parts.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output JSON instead of human-readable table",
    )

    # ── weather ──
    p_weather = subparsers.add_parser("weather", help="Weather data and DA tracking")
    p_weather.add_argument(
        "--venue-id", type=int, help="Venue ID (required unless --refresh-all)"
    )
    p_weather.add_argument(
        "--refresh-all",
        action="store_true",
        help="Poll OWM for all venues and store weather records",
    )
    p_weather.add_argument(
        "--stale-minutes",
        type=int,
        default=60,
        help="Skip venues with data newer than N min (default: 60)",
    )
    p_weather.add_argument(
        "--venue-ids-filter",
        type=int,
        nargs="+",
        help="Limit --refresh-all to specific venue IDs",
    )
    p_weather.add_argument(
        "--fetch", action="store_true", help="Fetch live weather from API"
    )
    p_weather.add_argument(
        "--da-trend", action="store_true", help="Show density altitude trend"
    )
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
    p_scrape_mode.add_argument(
        "--manufacturer", help="Single manufacturer to scrape (e.g. 'Suzuki')"
    )
    p_scrape_mode.add_argument(
        "--bulk",
        action="store_true",
        help="Bulk-scrape ALL manufacturers in the catalog "
        "(resumes from checkpoint if interrupted)",
    )
    p_scrape.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max bikes per manufacturer (default: 50 single / 300 bulk)",
    )
    p_scrape.add_argument(
        "--category",
        default=None,
        help="Filter by category (sport/naked/cruiser/adventure/touring)",
    )
    p_scrape.add_argument(
        "--min-cc", type=float, default=0, help="Minimum displacement to include (cc)"
    )
    p_scrape.add_argument(
        "--dry-run", action="store_true", help="Validate/count without writing to DB"
    )
    # Bulk-only options
    p_scrape.add_argument(
        "--priority",
        type=int,
        default=3,
        help="(bulk) Only scrape manufacturers with priority ≤ N "
        "(1=top, 2=standard, 3=all)",
    )
    p_scrape.add_argument(
        "--only",
        default=None,
        metavar="MFR",
        help="(bulk) Only scrape this manufacturer from the catalog",
    )
    p_scrape.add_argument(
        "--no-resume",
        action="store_true",
        help="(bulk) Start fresh, ignoring any saved checkpoint",
    )
    p_scrape.add_argument(
        "--checkpoint",
        default=None,
        metavar="FILE",
        help="(bulk) Path to checkpoint JSON file",
    )
    p_scrape.add_argument(
        "--rate",
        type=float,
        default=1.5,
        help="(bulk) Seconds between HTTP requests (default: 1.5)",
    )
    p_scrape.add_argument(
        "--status", action="store_true", help="(bulk) Show checkpoint status and exit"
    )
    p_scrape.add_argument(
        "--list-catalog",
        action="store_true",
        help="(bulk) List all manufacturers in the catalog and exit",
    )

    # ── import ──
    p_import = subparsers.add_parser(
        "import",
        help="Import bikes into database from known-bikes list or JSON file",
    )
    p_import_src = p_import.add_mutually_exclusive_group(required=True)
    p_import_src.add_argument(
        "--known-bikes",
        action="store_true",
        help="Import the built-in curated known-bikes list (22 bikes)",
    )
    p_import_src.add_argument(
        "--spec-json",
        metavar="FILE",
        help="Path to JSON file with bike spec(s) to import",
    )
    p_import.add_argument(
        "--dry-run", action="store_true", help="Validate without writing to DB"
    )

    # ── calibrate ────────────────────────────────────────────────────────
    p_cal = subparsers.add_parser(
        "calibrate",
        help="Import real run data for validation and calibration (Phase 3)",
    )
    p_cal_sub = p_cal.add_subparsers(
        dest="cal_command", help="Calibration sub-commands"
    )

    p_cal_dragy = p_cal_sub.add_parser(
        "import-dragy",
        help="Parse a Dragy GPS timer CSV or JSON file and display run summary",
    )
    p_cal_dragy.add_argument(
        "file", metavar="FILE", help="Path to Dragy .csv or .json export file"
    )
    p_cal_dragy.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output run summary as JSON",
    )
    p_cal_dragy.add_argument(
        "--best",
        action="store_true",
        help="Show only the best (lowest ET) run from the file",
    )

    # calibrate import-dyno
    p_cal_dyno = p_cal_sub.add_parser(
        "import-dyno",
        help="Parse a DynoJet/generic dyno CSV and apply SAE J1349 correction",
    )
    p_cal_dyno.add_argument("file", metavar="FILE", help="Path to dyno .csv file")
    p_cal_dyno.add_argument(
        "--temp",
        type=float,
        metavar="°C",
        help="Ambient temperature at dyno run (°C) for SAE J1349",
    )
    p_cal_dyno.add_argument(
        "--pressure",
        type=float,
        metavar="kPa",
        help="Absolute barometric pressure (kPa) for SAE J1349",
    )
    p_cal_dyno.add_argument(
        "--rh",
        type=float,
        default=0.0,
        metavar="PCT",
        help="Relative humidity %% (default: 0)",
    )
    p_cal_dyno.add_argument(
        "--crank",
        action="store_true",
        help="Mark curve as crank (engine) power, not wheel power",
    )
    p_cal_dyno.add_argument(
        "--json", action="store_true", dest="output_json", help="Output as JSON"
    )

    # calibrate overlay — compare sim to GPS run
    p_cal_ov = p_cal_sub.add_parser(
        "overlay",
        help="Compare simulation against a real GPS drag run (sim vs real v(t))",
    )
    p_cal_ov.add_argument("file", metavar="FILE", help="Dragy CSV/JSON file")
    p_cal_ov.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        help="Bike DB ID to use for simulation (default: GSX-R 1000 K5)",
    )
    p_cal_ov.add_argument(
        "--best", action="store_true", help="Use best run in file (default: first run)"
    )
    p_cal_ov.add_argument(
        "--json", action="store_true", dest="output_json", help="Output as JSON"
    )

    # calibrate import-ecu — parse ECU log
    p_cal_ecu = p_cal_sub.add_parser(
        "import-ecu",
        help="Parse a Woolich Racing, Power Commander PC-Link, or MoTeC i2 ECU log",
    )
    p_cal_ecu.add_argument(
        "file", metavar="FILE", help="Path to ECU log file (.csv or .tsv)"
    )
    p_cal_ecu.add_argument(
        "--best",
        action="store_true",
        help="Show only the best (lowest ET) run from the file",
    )
    p_cal_ecu.add_argument(
        "--channels", action="store_true", help="List all channels detected in the file"
    )
    p_cal_ecu.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output log summary as JSON",
    )

    # ── analysis (Phase 4) ───────────────────────────────────────────────────
    p_analysis = subparsers.add_parser(
        "analysis",
        help="Phase 4: Parts ROI ranking and Sobol sensitivity analysis",
    )
    p_analysis_sub = p_analysis.add_subparsers(
        dest="analysis_command", help="Analysis sub-commands"
    )

    # analysis roi
    p_roi = p_analysis_sub.add_parser(
        "roi",
        help="Rank parts by ROI (ET gain per rupee). Optionally find the best build within a budget.",
    )
    p_roi.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        help="Bike DB ID to use as baseline (default: GSX-R 1000 K5)",
    )
    p_roi.add_argument(
        "--part-ids",
        metavar="ID,ID,...",
        help="Comma-separated part IDs to evaluate (default: all parts)",
    )
    p_roi.add_argument(
        "--category",
        metavar="CAT",
        help="Restrict to one parts category (e.g. exhaust, ecu_flash)",
    )
    p_roi.add_argument(
        "--optimize",
        action="store_true",
        help="Find the best combination within --budget (knapsack DP)",
    )
    p_roi.add_argument(
        "--budget",
        type=float,
        default=100_000,
        metavar="INR",
        help="Budget for --optimize in rupees (default: 100000)",
    )
    p_roi.add_argument(
        "--by-category", action="store_true", help="Also print a category-level summary"
    )
    p_roi.add_argument(
        "--json", action="store_true", dest="output_json", help="Output as JSON"
    )

    # analysis sobol
    p_sobol = p_analysis_sub.add_parser(
        "sobol",
        help="Global sensitivity analysis: which parameters drive ET variance the most?",
    )
    p_sobol.add_argument(
        "--bike-id", type=int, metavar="ID", help="Bike DB ID (default: GSX-R 1000 K5)"
    )
    p_sobol.add_argument(
        "--n-samples",
        type=int,
        default=128,
        metavar="N",
        help="Base sample count N (total sims = N×(k+2), default: 128)",
    )
    p_sobol.add_argument(
        "--params",
        metavar="KEY,KEY,...",
        help=(
            "Comma-separated subset of params to analyse. "
            "Valid keys: "
            + ", ".join(
                [
                    "peak_power",
                    "dry_mass",
                    "aero_cd",
                    "frontal_area",
                    "tire_mu",
                    "rolling_radius",
                    "reaction_time",
                    "redline_rpm",
                    "primary_ratio",
                    "final_drive_ratio",
                ]
            )
        ),
    )
    p_sobol.add_argument(
        "--json", action="store_true", dest="output_json", help="Output results as JSON"
    )

    # ── analysis recommend ──────────────────────────────────────
    p_rec = p_analysis_sub.add_parser(
        "recommend",
        help="Smart build recommendation with synergy/compatibility analysis and upgrade paths",
    )
    p_rec.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        help="Bike DB ID to use as baseline (default: GSX-R 1000 K5)",
    )
    p_rec.add_argument(
        "--budget",
        type=float,
        default=100_000,
        metavar="INR",
        help="Budget in rupees (default: 100000)",
    )
    p_rec.add_argument(
        "--profile",
        default="all",
        choices=["all", "street_legal", "drag_prep", "full_race"],
        help="Build profile filter (default: all)",
    )
    p_rec.add_argument(
        "--mode",
        default="recommend",
        choices=["recommend", "upgrade-path", "category-order"],
        help="Output mode: recommend (single build), upgrade-path (tiered), category-order (priority list)",
    )
    p_rec.add_argument(
        "--tiers",
        type=int,
        default=3,
        metavar="N",
        help="Number of tiers for upgrade-path mode (default: 3)",
    )
    p_rec.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output as JSON",
    )

    # ── analysis optimize ────────────────────────────────────────
    p_opt = p_analysis_sub.add_parser(
        "optimize",
        help="Phase 4: Bayesian optimization for continuous multi-variable build tuning within budget",
    )
    p_opt.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        help="Bike DB ID to use as baseline (default: GSX-R 1000 K5)",
    )
    p_opt.add_argument(
        "--budget",
        type=float,
        default=100_000,
        metavar="INR",
        help="Budget in rupees (default: 100000)",
    )
    p_opt.add_argument(
        "--iterations",
        type=int,
        default=50,
        metavar="N",
        help="Number of BO iterations (each runs one physics sim; default: 50)",
    )
    p_opt.add_argument(
        "--json", action="store_true", dest="output_json", help="Output as JSON"
    )

    # ── analysis surrogate ───────────────────────────────────────
    p_surr = p_analysis_sub.add_parser(
        "surrogate",
        help="Phase 4B: XGBoost surrogate model — generate training data, train, evaluate, predict",
    )
    p_surr_sub = p_surr.add_subparsers(
        dest="surrogate_command", help="Surrogate sub-commands"
    )

    # analysis surrogate generate
    p_sg = p_surr_sub.add_parser(
        "generate",
        help="Generate Sobol-sampled training data by running the physics engine N times",
    )
    p_sg.add_argument(
        "--n-samples",
        type=int,
        default=2048,
        dest="n_samples",
        metavar="N",
        help="Number of valid training samples to collect (default: 2048; use 50000 for production)",
    )
    p_sg.add_argument(
        "--seed", type=int, default=42, help="Sobol scramble seed (default: 42)"
    )
    p_sg.add_argument(
        "--output",
        default="surrogate_data.npz",
        metavar="FILE",
        help="Output .npz file path (default: surrogate_data.npz)",
    )
    p_sg.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        dest="bike_id",
        help="DB bike ID to use as structural template (default: GSX-R 1000 K5)",
    )
    p_sg.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Also print summary as JSON",
    )

    # analysis surrogate train
    p_st = p_surr_sub.add_parser(
        "train",
        help="Train XGBoost surrogate on a generated .npz dataset",
    )
    p_st.add_argument(
        "--data",
        default="surrogate_data.npz",
        metavar="FILE",
        help="Input .npz training data file (default: surrogate_data.npz)",
    )
    p_st.add_argument(
        "--model-out",
        default="surrogate.pkl",
        metavar="FILE",
        dest="model_out",
        help="Output .pkl model file (default: surrogate.pkl)",
    )
    p_st.add_argument(
        "--test-fraction",
        type=float,
        default=0.15,
        dest="test_fraction",
        metavar="F",
        help="Fraction of data held out for test evaluation (default: 0.15)",
    )
    p_st.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Also print metrics as JSON",
    )

    # analysis surrogate evaluate
    p_se = p_surr_sub.add_parser(
        "evaluate",
        help="Evaluate a trained surrogate model against a dataset",
    )
    p_se.add_argument(
        "--model",
        default="surrogate.pkl",
        metavar="FILE",
        help="Trained surrogate .pkl file (default: surrogate.pkl)",
    )
    p_se.add_argument(
        "--data",
        default="surrogate_data.npz",
        metavar="FILE",
        help="Dataset .npz file (default: surrogate_data.npz)",
    )
    p_se.add_argument(
        "--test-fraction",
        type=float,
        default=0.15,
        dest="test_fraction",
        metavar="F",
        help="Fraction used for test evaluation (default: 0.15)",
    )
    p_se.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Also print metrics as JSON",
    )

    # analysis surrogate train-dnn
    p_sdnn = p_surr_sub.add_parser(
        "train-dnn",
        help="Phase 4A: Train a 4-layer MLP surrogate (PyTorch if available, else sklearn)",
    )
    p_sdnn.add_argument(
        "--data",
        default="surrogate_data.npz",
        metavar="FILE",
        help="Input .npz training data file (default: surrogate_data.npz)",
    )
    p_sdnn.add_argument(
        "--model-out",
        default="surrogate_dnn.pkl",
        metavar="FILE",
        dest="model_out",
        help="Output .pkl model file (default: surrogate_dnn.pkl)",
    )
    p_sdnn.add_argument(
        "--epochs",
        type=int,
        default=300,
        metavar="N",
        help="Maximum training epochs (default: 300; early stopping applies)",
    )
    p_sdnn.add_argument(
        "--test-fraction",
        type=float,
        default=0.15,
        metavar="F",
        dest="test_fraction",
        help="Fraction held out for evaluation (default: 0.15)",
    )
    p_sdnn.add_argument(
        "--filter-min-pw",
        type=float,
        default=0.12,
        metavar="HP/KG",
        dest="filter_min_pw",
        help="Minimum power/weight ratio to keep (default: 0.12 hp/kg)",
    )
    p_sdnn.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Also print metrics as JSON",
    )

    # analysis surrogate predict
    p_sp = p_surr_sub.add_parser(
        "predict",
        help="Predict ET + trap speed for a bike using the surrogate model",
    )
    p_sp.add_argument(
        "--model",
        default="surrogate.pkl",
        metavar="FILE",
        help="Trained surrogate .pkl file (default: surrogate.pkl)",
    )
    p_sp.add_argument(
        "--bike-id",
        type=int,
        metavar="ID",
        dest="bike_id",
        help="DB bike ID to predict (default: GSX-R 1000 K5)",
    )
    p_sp.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output prediction as JSON",
    )

    # ── nl (Natural Language) ────────────────────────────────────────
    # ── pricing ──
    p_pricing = subparsers.add_parser(
        "pricing",
        help="Indian-market parts pricing refresh + coverage reports",
    )
    p_pricing_sub = p_pricing.add_subparsers(
        dest="pricing_action", help="refresh | status | stale"
    )

    p_pricing_refresh = p_pricing_sub.add_parser(
        "refresh",
        help="Populate retailer_url + last_price_check for every part",
    )
    p_pricing_refresh.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing retailer_url (default: only fill if NULL)",
    )
    p_pricing_refresh.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Show what would change; do not commit",
    )
    p_pricing_refresh.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Machine-readable output",
    )

    p_pricing_status = p_pricing_sub.add_parser(
        "status", help="Coverage report (price / retailer / URL / freshness %s)"
    )
    p_pricing_status.add_argument("--json", action="store_true", dest="output_json")

    p_pricing_stale = p_pricing_sub.add_parser(
        "stale", help="List parts whose last_price_check is > --days old"
    )
    p_pricing_stale.add_argument(
        "--days",
        type=int,
        default=30,
        help="Staleness threshold in days (default: 30)",
    )
    p_pricing_stale.add_argument("--json", action="store_true", dest="output_json")

    p_nl = subparsers.add_parser(
        "nl",
        help="Phase 4C: Natural language tuning interface",
    )
    p_nl.add_argument(
        "query",
        metavar="QUERY",
        nargs="?",
        help="Natural language query (e.g., 'optimize my Hayabusa for 35C at Aamby Valley with 50000 INR budget')",
    )
    p_nl.add_argument(
        "--json", action="store_true", dest="output_json", help="Output result as JSON"
    )
    p_nl.add_argument(
        "--verbose", action="store_true", help="Print debug info on error"
    )

    return parser


# ═══════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════

SUBCOMMAND_MAP = {
    "db": cmd_db,
    "bikes": cmd_bikes,
    "sim": cmd_sim,
    "venues": cmd_venues,
    "tires": cmd_tires,
    "parts": cmd_parts,
    "weather": cmd_weather,
    "leaderboard": cmd_leaderboard,
    "history": cmd_history,
    "scrape": cmd_scrape,
    "import": cmd_import,
    "calibrate": cmd_calibrate,
    "analysis": cmd_analysis,
    "nl": cmd_nl,
    "pricing": cmd_pricing,
}


def main(args_list=None):
    """Phase 2 subcommand-based entry point."""
    parser = build_parser()
    args = parser.parse_args(args_list)

    if not hasattr(args, "command") or args.command is None:
        parser.print_help()
        return 0

    handler = SUBCOMMAND_MAP.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    import sys

    sys.exit(main() or 0)
