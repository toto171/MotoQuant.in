#!/usr/bin/env python3
"""
Seed OEM tire fitments for the 3 vintage two-stroke bikes that ship with ZERO
tire fitments in the catalog (the July-3 query-driven planner closed every other
2T bike; these three fell through because their period bias-ply sizes are not in
the planner's radial fitment tables).

Bikes handled (resolved by manufacturer + model-name pattern, not hard-coded id):
  - Suzuki  GT750 'Water Buffalo'  (1971-1977)  front 3.25-19  rear 4.00-18
  - Kawasaki 750 H2 Mach IV        (1972-1975)  front 3.25-19  rear 4.00-18
  - Yezdi   250 Classic (Ideal Jawa)(1978-1996) 3.25-16 front & rear (interchangeable wheels)

Period-correct OEM sizes are 1970s/80s bias-ply inch-dash designations. The catalog
stores such vintage sizes in their standard metric-dash equivalents (matching how the
DB already stores e.g. the RE Bullet 500's period 3.25-19 as "90/90-19"), which is what
the spec validator accepts. The authentic inch designation is preserved in the tire
model_name and in each fitment's notes, together with a source citation:
        3.25-19  ->  90/90-19
        4.00-18  ->  110/90-18
        3.25-16  ->  90/90-16
Grip is set to a period-appropriate bias-ply mu_peak ~1.00 (task band 0.95-1.05) with
standard Pacejka/thermal template values and construction='bias'.

IDEMPOTENT: safe to run repeatedly. Tires are created via TireRepository.create()
(id-preserving upsert on manufacturer+model+size) and fitments are check-then-insert
(skipped if the exact bike/tire/position/oem row already exists). Re-running is a no-op.

This script is DATA-ONLY. It does NOT modify seed.py and does NOT change physics.
It mirrors the existing seeding layer (tire_repo.create + link_bike_fitment).

Usage:
    python3 scripts/seed_vintage_2t_fitments.py [--db PATH] [--dry-run]

  --db      path to the SQLite DB (default: $MOTOQUANT_DB or ./motoquant.db)
  --dry-run resolve bikes and report what would change, write nothing
"""

from __future__ import annotations

import argparse
import os
import sys

# Allow "python3 scripts/seed_vintage_2t_fitments.py" from the repo root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.database.tire_repo import TireRepository  # noqa: E402

# Generic OEM-spec manufacturer: signals a size-accurate period fitment rather than
# claiming a specific commercial product (only the SIZE is source-verified, not brand).
OEM_MFR = "OE Bias-Ply"

# ── Tire definitions (metric-dash size_designation the validator accepts; authentic
#    vintage inch designation kept in `vintage` and the model_name) ────────────────
TIRES = {
    "front_19": {
        "model": "OE Bias-Ply 3.25-19",
        "size": "90/90-19",
        "position": "front",
        "vintage": "3.25-19",
        "width": 90,
        "aspect": 90,
        "rim": 19,
        "mass": 3.6,
        "tread": 1.6,
        "inertia": 0.36,
    },
    "rear_18": {
        "model": "OE Bias-Ply 4.00-18",
        "size": "110/90-18",
        "position": "rear",
        "vintage": "4.00-18",
        "width": 110,
        "aspect": 90,
        "rim": 18,
        "mass": 4.9,
        "tread": 2.1,
        "inertia": 0.52,
    },
    "both_16": {
        "model": "OE Bias-Ply 3.25-16",
        "size": "90/90-16",
        "position": "both",
        "vintage": "3.25-16",
        "width": 90,
        "aspect": 90,
        "rim": 16,
        "mass": 3.6,
        "tread": 1.7,
        "inertia": 0.30,
    },
}

# ── Bikes + their front/rear tire keys + source citation ─────────────────────────
BIKES = [
    {
        "name": "Suzuki GT750 'Water Buffalo'",
        "mfr": "Suzuki",
        "model_like": "GT750%",
        "front": "front_19",
        "rear": "rear_18",
        "source": (
            "Suzuki GT750 (1973-74) factory spec front 3.25-19 / rear 4.00-18 "
            "[motorcyclespecifications.com; moto-data.net; ultimatespecs.com]"
        ),
    },
    {
        "name": "Kawasaki 750 H2 Mach IV",
        "mfr": "Kawasaki",
        "model_like": "%H2 Mach IV%",
        "front": "front_19",
        "rear": "rear_18",
        "source": (
            "Kawasaki H2 750 Mach IV (1972-75) front 3.25-19 / rear 4.00-18 "
            "[KGF Classic Cars 1975 example 3.25-19 54H / 4.00-18 64H; Pirelli H2/H2A-C fitment catalog]"
        ),
    },
    {
        "name": "Yezdi 250 Classic (Ideal Jawa)",
        "mfr": "Yezdi",
        "model_like": "250 Classic%",
        "front": "both_16",
        "rear": "both_16",
        "source": (
            "Ideal Jawa Yezdi 250 Classic 3.25-16 front & rear on interchangeable 1.86x16 rims "
            "[xBhp 'Tyres for Yezdi/Jawa 3.25x16'; DriveSpark; MRF Moto D 3.25x16 fitment]"
        ),
    },
]


def _tire_kwargs(t: dict) -> dict:
    """Period bias-ply Pacejka/thermal/physical template for one tire size."""
    rr = (t["rim"] * 25.4 / 2 + t["width"] * (t["aspect"] / 100.0)) / 1000.0
    mu_peak = 1.00  # period bias-ply, task band 0.95-1.05
    return {
        "width_mm": t["width"],
        "aspect_ratio": t["aspect"],
        "rim_diameter_inch": t["rim"],
        # Pacejka Magic Formula (bias-ply: lower stiffness than radial)
        "pacejka_B": 9.0,
        "pacejka_C": 1.55,
        "pacejka_D": mu_peak,
        "pacejka_E": -0.30,
        # Friction
        "mu_peak": mu_peak,
        "mu_slide": round(mu_peak * 0.80, 3),
        "load_sensitivity_k": 0.0,
        # Thermal
        "optimal_temp_c": 45.0,
        "reversion_temp_c": 105.0,
        "thermal_conductivity": 0.20,
        "tread_mass_kg": t["tread"],
        "specific_heat": 1700.0,
        # Physical
        "rolling_radius_m": round(rr, 5),
        "inertia_kgm2": t["inertia"],
        "growth_coeff": 2e-09,
        "mass_kg": t["mass"],
        # Rolling resistance (bias-ply higher than radial)
        "crr_base": 0.014,
        "crr_speed_coeff": 2.5e-05,
        "crr_temp_coeff": -0.0002,
        # Pressure (period recommendations, psi)
        "recommended_psi": 28.0,
        "drag_pressure_psi": 26.0,
        # Construction / provenance
        "construction": "bias",
        "data_source": "vintage OEM size (see fitment notes); Pacejka templated",
        "confidence": 0.45,
        # 90/90-19, 110/90-18 and 90/90-16 are all common Indian-market sizes.
        "available_india": 1,
    }


def _resolve_bikes(conn, mfr: str, model_like: str) -> list[tuple[int, str]]:
    rows = conn.execute(
        "SELECT b.id, b.model_name FROM bike_models b "
        "JOIN manufacturers m ON b.manufacturer_id = m.id "
        "WHERE LOWER(m.name) = LOWER(?) AND b.model_name LIKE ? "
        "ORDER BY b.id",
        (mfr, model_like),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _fitment_exists(conn, bike_id: int, tire_id: int, position: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM bike_tire_fitments "
            "WHERE bike_model_id = ? AND tire_model_id = ? AND position = ? "
            "AND fitment_type = 'oem'",
            (bike_id, tire_id, position),
        ).fetchone()
        is not None
    )


def _count_fitments(conn, bike_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM bike_tire_fitments WHERE bike_model_id = ?",
        (bike_id,),
    ).fetchone()[0]


def seed_vintage_2t_fitments(db: MotoQuantDB, dry_run: bool = False) -> dict:
    """Seed the OEM fitments. Returns a stats dict."""
    conn = db.connect()
    repo = TireRepository(conn)
    stats = {
        "bikes_matched": 0,
        "bikes_skipped": 0,
        "tires_ensured": 0,
        "fitments_inserted": 0,
        "fitments_existing": 0,
        "detail": [],
    }

    # Cache tire ids so a size shared across bikes (3.25-19 / 4.00-18) is created once.
    tire_ids: dict[str, int] = {}

    def _ensure_tire(tkey: str) -> int:
        if tkey in tire_ids:
            return tire_ids[tkey]
        t = TIRES[tkey]
        if dry_run:
            existing = conn.execute(
                "SELECT tm.id FROM tire_models tm JOIN tire_manufacturers m "
                "ON tm.manufacturer_id = m.id "
                "WHERE m.name = ? AND tm.model_name = ? AND tm.size_designation = ?",
                (OEM_MFR, t["model"], t["size"]),
            ).fetchone()
            tid = existing[0] if existing else -1
        else:
            tid = repo.create(
                OEM_MFR,
                t["model"],
                t["size"],
                compound_type="vintage",
                position=t["position"],
                **_tire_kwargs(t),
            )
            stats["tires_ensured"] += 1
        tire_ids[tkey] = tid
        return tid

    for bike in BIKES:
        matches = _resolve_bikes(conn, bike["mfr"], bike["model_like"])
        if not matches:
            stats["bikes_skipped"] += 1
            stats["detail"].append(
                {"name": bike["name"], "status": "SKIPPED — no matching bike row"}
            )
            continue

        for bike_id, model_name in matches:
            stats["bikes_matched"] += 1
            before = _count_fitments(conn, bike_id)
            for position in ("front", "rear"):
                tkey = bike[position]
                tire_id = _ensure_tire(tkey)
                t = TIRES[tkey]
                notes = (
                    f"OEM {t['vintage']} bias-ply ({position}); "
                    f"stored as {t['size']} metric-dash equivalent. {bike['source']}"
                )
                if dry_run:
                    already = tire_id != -1 and _fitment_exists(
                        conn, bike_id, tire_id, position
                    )
                    if already:
                        stats["fitments_existing"] += 1
                    else:
                        stats["fitments_inserted"] += 1
                    continue

                if _fitment_exists(conn, bike_id, tire_id, position):
                    stats["fitments_existing"] += 1
                    continue
                repo.link_bike_fitment(
                    bike_id,
                    tire_id,
                    position,
                    fitment_type="oem",
                    is_default=True,  # invariant: every OEM fitment is is_default=1
                    notes=notes,
                )
                stats["fitments_inserted"] += 1
            after = _count_fitments(conn, bike_id)
            stats["detail"].append(
                {
                    "name": bike["name"],
                    "bike_id": bike_id,
                    "model_name": model_name,
                    "fitments_before": before,
                    "fitments_after": after if not dry_run else before,
                    "status": "ok",
                }
            )

    if not dry_run:
        conn.commit()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--db",
        default=os.environ.get("MOTOQUANT_DB", "motoquant.db"),
        help="Path to SQLite DB (default: $MOTOQUANT_DB or ./motoquant.db)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing.",
    )
    args = ap.parse_args()

    db = MotoQuantDB(db_path=args.db)
    stats = seed_vintage_2t_fitments(db, dry_run=args.dry_run)
    db.close()

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"[{mode}] DB: {args.db}")
    for d in stats["detail"]:
        if d.get("status") == "ok":
            print(
                f"  {d['name']} (id {d['bike_id']}): "
                f"{d['fitments_before']} -> {d['fitments_after']} fitments"
            )
        else:
            print(f"  {d['name']}: {d['status']}")
    print(
        f"  bikes_matched={stats['bikes_matched']} "
        f"bikes_skipped={stats['bikes_skipped']} "
        f"tires_ensured={stats['tires_ensured']} "
        f"fitments_inserted={stats['fitments_inserted']} "
        f"fitments_existing={stats['fitments_existing']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
