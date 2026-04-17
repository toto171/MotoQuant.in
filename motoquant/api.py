"""
MotoQuant Pro — FastAPI Web Server
====================================
REST API wrapper around the MotoQuant physics engine and database.
Serves the motoquant.in web simulator, public leaderboard, and bike library.

Endpoints
---------
GET  /                        Health / welcome
GET  /api/health              JSON health check
GET  /api/bikes               List / search bikes (paginated)
GET  /api/bikes/{id}          Bike detail + default config
GET  /api/venues              List venues with current DA
POST /api/simulate            Full simulation (returns v(t), RPM(t), etc.)
POST /api/simulate/quick      Quick ET-only simulation (faster for UI sliders)
GET  /api/leaderboard         Top simulation results
GET  /api/tires               List tire models

Run locally
-----------
    cd "Vehicle Dynamics"
    uvicorn motoquant.api:app --reload --port 8000

Deploy (Railway / Render / DigitalOcean App Platform)
------
    Set PORT env var; Railway auto-detects the Procfile.
"""

import copy
import json
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .physics import MotoQuantEngine

# ─── App init ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="MotoQuant Pro API",
    description="First-principles motorcycle drag racing simulator — motoquant.in",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Next.js frontend on any origin during early development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── DB helper ────────────────────────────────────────────────────────────

_db_conn = None  # module-level singleton — one connection, reused across requests


def _get_db():
    """Return a live DB connection or None if DB unavailable.

    Uses a module-level singleton to avoid creating (and leaking) a new
    connection on every request.  SQLite is single-writer anyway, so a
    shared connection is the correct approach for a read-heavy API.
    """
    global _db_conn
    if _db_conn is not None:
        try:
            # Quick liveness check — will throw if connection is closed/broken
            _db_conn.execute("SELECT 1")
            return _db_conn
        except Exception as e:
            logging.getLogger(__name__).warning(
                "DB liveness check failed, reconnecting: %s", e
            )
            _db_conn = None  # stale — reconnect below

    try:
        from .database.connection import MotoQuantDB

        db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
        db = MotoQuantDB(db_path)
        _db_conn = db.conn
        return _db_conn
    except Exception as e:
        logging.getLogger(__name__).error(
            "Failed to initialize database at %s: %s", db_path, e, exc_info=True
        )
        return None


def _bike_row_to_summary(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "manufacturer": row.get("manufacturer"),  # from JOIN alias
        "model": row.get("model_name"),
        "year": row.get("year_from"),
        "category": row.get("category"),
        "displacement_cc": row.get("displacement_cc"),
        "peak_power_hp": row.get("peak_power_hp"),
        "dry_mass_kg": row.get("dry_mass_kg"),
        "data_quality": row.get("data_quality"),
    }


# ─── Request / response models ────────────────────────────────────────────


class SimulateRequest(BaseModel):
    """POST /api/simulate — full simulation request."""

    # Bike selection — one of these must be provided
    bike_id: int | None = Field(None, description="DB bike model ID")
    bike_preset: str | None = Field(
        None, description="'gsxr1000_k5' | 'yzfr1_4c8' | 'hayabusa_gen1'"
    )

    # Optional overrides (applied on top of the selected bike's defaults)
    power_boost_pct: float = Field(
        0.0, description="Extra power as % of stock (e.g. 10 = +10%)"
    )
    mass_delta_kg: float = Field(0.0, description="Mass change in kg (+add, -remove)")
    rider_mass_kg: float = Field(75.0, description="Rider weight [kg]")
    front_tire_id: int | None = Field(None, description="Override front tire DB ID")
    rear_tire_id: int | None = Field(None, description="Override rear tire DB ID")
    venue_id: int | None = Field(
        None, description="Venue for DA and surface conditions"
    )

    # Environment overrides (applied on top of venue defaults if set)
    ambient_temp_c: float | None = Field(None, description="Ambient temperature °C")
    track_temp_c: float | None = Field(None, description="Track surface temperature °C")
    humidity_pct: float | None = Field(None, description="Relative humidity 0-100%")
    headwind_kmh: float | None = Field(None, description="Headwind km/h (negative = tailwind)")

    # Simulation options
    use_adaptive_dt: bool = Field(
        False, description="Use adaptive RK4 timestep (slower)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bike_id": 1,
                "power_boost_pct": 5.0,
                "mass_delta_kg": -3.0,
                "rider_mass_kg": 70.0,
            }
        }


class QuickSimRequest(BaseModel):
    """POST /api/simulate/quick — minimal input for slider-driven UI."""

    bike_id: int | None = None
    bike_preset: str | None = None
    power_boost_pct: float = 0.0
    mass_delta_kg: float = 0.0
    rider_mass_kg: float = 75.0
    part_ids: list[int] = Field(default_factory=list, description="Part IDs to apply")
    front_tire_id: int | None = None
    rear_tire_id: int | None = None
    venue_id: int | None = None
    # Environment overrides
    ambient_temp_c: float | None = None
    track_temp_c: float | None = None
    humidity_pct: float | None = None
    headwind_kmh: float | None = None


# ─── Config builder ────────────────────────────────────────────────────────


def _build_config(
    bike_id: int | None,
    bike_preset: str | None,
    power_boost_pct: float,
    mass_delta_kg: float,
    rider_mass_kg: float,
    venue_id: int | None = None,
    front_tire_id: int | None = None,
    rear_tire_id: int | None = None,
    ambient_temp_c: float | None = None,
    track_temp_c: float | None = None,
    humidity_pct: float | None = None,
    headwind_kmh: float | None = None,
) -> BikeConfig:
    """Assemble a BikeConfig from request parameters."""

    # ── Base config ─────────────────────────────────────────────────────
    cfg: BikeConfig | None = None

    if bike_id is not None:
        db = _get_db()
        if db:
            try:
                from .database.bridge import db_row_to_config

                # Get bike name from bike_models + manufacturers
                name_row = db.execute(
                    """SELECT bm.model_name, m.name AS manufacturer
                       FROM bike_models bm
                       JOIN manufacturers m ON bm.manufacturer_id = m.id
                       WHERE bm.id = ?""",
                    (bike_id,),
                ).fetchone()
                bike_name = "DB Bike"
                if name_row:
                    nr = dict(name_row)
                    bike_name = f"{nr['manufacturer']} {nr['model_name']}"

                # Get the full physics config from bike_configs table
                cfg_row = db.execute(
                    """SELECT * FROM bike_configs
                       WHERE bike_model_id = ? AND is_current = 1
                       ORDER BY version DESC LIMIT 1""",
                    (bike_id,),
                ).fetchone()
                if cfg_row:
                    cfg = db_row_to_config(dict(cfg_row), name=bike_name)
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "Failed to load config for bike_id=%s: %s", bike_id, exc
                )

    if cfg is None and bike_preset:
        presets = {
            "gsxr1000_k5": gsxr1000_k5,
            "yzfr1_4c8": yzfr1_4c8,
            "hayabusa_gen1": hayabusa_gen1,
        }
        fn = presets.get(bike_preset)
        if fn:
            cfg = fn()

    if cfg is None:
        cfg = gsxr1000_k5()  # default fallback

    cfg = copy.deepcopy(cfg)

    # ── Apply overrides ──────────────────────────────────────────────────
    if power_boost_pct != 0.0:
        scale = 1.0 + power_boost_pct / 100.0
        cfg.engine.peak_power_hp *= scale
        cfg.engine.peak_torque_nm *= scale
        # Scale dyno curve too — the engine reads torque from here, not peak_power_hp
        if cfg.engine.dyno_curve is not None:
            cfg.engine.dyno_curve.torque_nm = cfg.engine.dyno_curve.torque_nm * scale

    if mass_delta_kg != 0.0:
        cfg.chassis.dry_mass_kg += mass_delta_kg

    # Set rider mass in both places — physics engine reads from chassis.rider_mass_kg
    cfg.rider.mass_kg = rider_mass_kg
    cfg.chassis.rider_mass_kg = rider_mass_kg

    # ── Venue conditions ────────────────────────────────────────────────
    if venue_id is not None:
        db = _get_db()
        if db:
            try:
                row = db.execute(
                    "SELECT * FROM venues WHERE id=?", (venue_id,)
                ).fetchone()
                if row:
                    d = dict(row)
                    if d.get("altitude_m") is not None:
                        cfg.environment.altitude_m = float(d["altitude_m"])
                    # Derive grip multiplier from surface_type
                    surface = (d.get("surface_type") or "asphalt").lower()
                    grip_map = {
                        "concrete": 1.05,   # prepped concrete (NHRA-style)
                        "asphalt": 1.00,     # baseline
                        "prepped": 1.10,     # VHT-prepped
                    }
                    cfg.environment.surface_grip_multiplier = grip_map.get(
                        surface, 1.00
                    )
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to load venue %s: %s", venue_id, e
                )

    # ── Environment overrides (on top of venue) ──────────────────────────
    if ambient_temp_c is not None:
        cfg.environment.ambient_temp_c = ambient_temp_c
    if track_temp_c is not None:
        cfg.environment.track_temp_c = track_temp_c
    if humidity_pct is not None:
        cfg.environment.relative_humidity_pct = humidity_pct
    if headwind_kmh is not None:
        cfg.environment.wind_speed_ms = headwind_kmh / 3.6
        cfg.environment.wind_direction_deg = 0.0  # 0 = headwind

    # ── Tire overrides ──────────────────────────────────────────────────
    # If a tire ID is provided, look up the tire's mu_peak and apply it
    for tire_id in (front_tire_id, rear_tire_id):
        if tire_id is not None:
            db = _get_db()
            if db:
                try:
                    trow = db.execute(
                        "SELECT pacejka_D, mu_peak FROM tire_models WHERE id=?",
                        (tire_id,),
                    ).fetchone()
                    if trow:
                        td = dict(trow)
                        mu = td.get("mu_peak") or td.get("pacejka_D")
                        if mu and float(mu) > 0:
                            cfg.tires.mu_peak = float(mu)
                except Exception as e:
                    logging.getLogger(__name__).warning(
                        "Failed to load tire_id=%s: %s", tire_id, e
                    )

    return cfg


# ─── Endpoints ────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "service": "MotoQuant Pro API",
        "version": "0.3.0",
        "tagline": "The physics of faster",
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/api/health")
def health():
    db = _get_db()
    db_ok = False
    bike_count = 0
    if db:
        try:
            bike_count = db.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
            db_ok = True
        except Exception:
            pass
    return {
        "status": "ok",
        "database": "connected" if db_ok else "unavailable",
        "bike_count": bike_count,
    }


@app.get("/api/bikes")
def list_bikes(
    search: str | None = Query(None, description="Search by model/manufacturer"),
    manufacturer: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    try:
        query = """SELECT bm.*, m.name AS manufacturer
                   FROM bike_models bm
                   JOIN manufacturers m ON bm.manufacturer_id = m.id
                   WHERE 1=1"""
        params: list[Any] = []

        if search:
            query += " AND (m.name LIKE ? OR bm.model_name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if manufacturer:
            query += " AND LOWER(m.name) = LOWER(?)"
            params.append(manufacturer)
        if category:
            query += " AND LOWER(bm.category) = LOWER(?)"
            params.append(category)

        query += " ORDER BY m.name, bm.model_name LIMIT ? OFFSET ?"
        params += [limit, offset]

        rows = db.execute(query, params).fetchall()

        count_query = """SELECT COUNT(*) FROM bike_models bm
                         JOIN manufacturers m ON bm.manufacturer_id = m.id
                         WHERE 1=1"""
        count_params: list[Any] = []
        if search:
            count_query += " AND (m.name LIKE ? OR bm.model_name LIKE ?)"
            count_params += [f"%{search}%", f"%{search}%"]

        total = db.execute(count_query, count_params).fetchone()[0]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "bikes": [_bike_row_to_summary(dict(r)) for r in rows],
        }
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


@app.get("/api/bikes/{bike_id}")
def get_bike(bike_id: int):
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    try:
        row = db.execute(
            """SELECT bm.*, m.name AS manufacturer
               FROM bike_models bm
               JOIN manufacturers m ON bm.manufacturer_id = m.id
               WHERE bm.id = ?""",
            (bike_id,),
        ).fetchone()
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")

    if not row:
        raise HTTPException(404, f"Bike {bike_id} not found")

    d = _bike_row_to_summary(dict(row))
    # Attach OEM tire fitments
    try:
        fitments = db.execute(
            """SELECT tf.position, tf.fitment_type,
                      tmfr.name AS manufacturer, tm.model_name AS model,
                      tm.size_designation, tm.compound_type,
                      tm.id AS tire_id
               FROM bike_tire_fitments tf
               JOIN tire_models tm ON tf.tire_model_id = tm.id
               JOIN tire_manufacturers tmfr ON tm.manufacturer_id = tmfr.id
               WHERE tf.bike_model_id = ?""",
            (bike_id,),
        ).fetchall()
        d["tire_fitments"] = [dict(f) for f in fitments]
    except Exception:
        d["tire_fitments"] = []

    return d


@app.get("/api/venues")
def list_venues():
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        rows = db.execute("SELECT * FROM venues ORDER BY country, name").fetchall()
        return {"venues": [dict(r) for r in rows]}
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


@app.get("/api/tires")
def list_tires(
    compound: str | None = Query(None),
    manufacturer: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        query = """SELECT tm.*, tmfr.name AS manufacturer
                   FROM tire_models tm
                   JOIN tire_manufacturers tmfr ON tm.manufacturer_id = tmfr.id
                   WHERE 1=1"""
        params: list[Any] = []
        if compound:
            query += " AND LOWER(tm.compound_type) = LOWER(?)"
            params.append(compound)
        if manufacturer:
            query += " AND LOWER(tmfr.name) LIKE LOWER(?)"
            params.append(f"%{manufacturer}%")
        query += " ORDER BY tmfr.name, tm.model_name LIMIT ?"
        params.append(limit)
        rows = db.execute(query, params).fetchall()
        # Reshape to frontend-friendly format
        tires = []
        for r in rows:
            d = dict(r)
            d["model"] = d.get("model_name", "")
            tires.append(d)
        return {"tires": tires}
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


@app.post("/api/simulate")
def simulate(req: SimulateRequest):
    """
    Full quarter-mile simulation.

    Returns complete time-series arrays (v, RPM, gear, etc.) plus scalar
    milestones (ET, trap speed, splits).

    The arrays are down-sampled to 100 Hz for a reasonable response size.
    """
    try:
        cfg = _build_config(
            bike_id=req.bike_id,
            bike_preset=req.bike_preset,
            power_boost_pct=req.power_boost_pct,
            mass_delta_kg=req.mass_delta_kg,
            rider_mass_kg=req.rider_mass_kg,
            venue_id=req.venue_id,
            front_tire_id=req.front_tire_id,
            rear_tire_id=req.rear_tire_id,
            ambient_temp_c=req.ambient_temp_c,
            track_temp_c=req.track_temp_c,
            humidity_pct=req.humidity_pct,
            headwind_kmh=req.headwind_kmh,
        )
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run(use_adaptive_dt=req.use_adaptive_dt)
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    # Down-sample to ~100 Hz (every 10th point at 1 ms default dt)
    step = max(1, len(sim.t) // 1000)
    idx = list(range(0, len(sim.t), step))

    def _safe_array(arr, transform, fallback=None):
        """Safely extract + transform a sim array, guarding against None/empty."""
        if arr is None or (hasattr(arr, '__len__') and len(arr) == 0):
            return [] if fallback is None else fallback
        return [transform(arr[i]) for i in idx if i < len(arr)]

    # Robust manufacturer extraction
    _mfr = "Unknown"
    if cfg.name:
        parts = cfg.name.split(" ", 1)
        _mfr = parts[0] if parts else cfg.name

    # Build response — convert numpy to Python floats for JSON
    return {
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * 3.6, 2),
        "trap_speed_ms": round(float(sim.speed_quarter), 3),
        "splits": {
            "60ft_s": round(float(sim.time_60ft), 4),
            "330ft_s": round(float(sim.time_330ft), 4),
            "660ft_s": round(float(sim.time_eighth), 4),
            "1000ft_s": round(float(sim.time_1000ft), 4),
            "1320ft_s": round(float(sim.time_quarter), 4),
        },
        "bike": {
            "manufacturer": _mfr,
            "model": cfg.name or "Unknown",
            "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
            "dry_mass_kg": round(float(cfg.chassis.dry_mass_kg), 1),
        },
        "config": {
            "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
            "peak_torque_nm": round(float(cfg.engine.peak_torque_nm), 1),
            "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
            "dry_mass_kg": round(float(cfg.chassis.dry_mass_kg), 1),
            "displacement_cc": cfg.engine.displacement_cc,
            "redline_rpm": cfg.engine.redline_rpm,
            "gear_count": len(cfg.drivetrain.gear_ratios) if cfg.drivetrain.gear_ratios else 0,
            "cd": round(float(cfg.aero.cd), 3) if hasattr(cfg, 'aero') and cfg.aero else None,
            "rider_mass_kg": round(float(cfg.chassis.rider_mass_kg), 1),
        },
        "timeseries": {
            "t_s": _safe_array(sim.t, lambda v: round(float(v), 4)),
            "v_kmh": _safe_array(sim.v, lambda v: round(float(v) * 3.6, 2)),
            "x_m": _safe_array(sim.x, lambda v: round(float(v), 2)),
            "rpm": _safe_array(sim.rpm, lambda v: round(float(v), 0)),
            "gear": _safe_array(sim.gear, lambda v: int(v)),
            "accel_g": _safe_array(sim.a, lambda v: round(float(v) / 9.81, 3)),
            "traction_pct": _safe_array(sim.traction_pct, lambda v: round(float(v) * 100, 1)),
            "tire_temp_c": _safe_array(sim.T_tire, lambda v: round(float(v), 1)),
            "power_kw": _safe_array(sim.power_kw, lambda v: round(float(v), 1)),
            "F_drive_N": _safe_array(sim.F_drive, lambda v: round(float(v), 0)),
            "F_drag_N": _safe_array(sim.F_drag, lambda v: round(float(v), 0)),
        },
    }


@app.post("/api/simulate/quick")
def simulate_quick(req: QuickSimRequest):
    """
    Quick ET-only simulation — no time-series arrays.
    Returns in ~50 ms; ideal for slider-driven UI.
    """
    try:
        cfg = _build_config(
            bike_id=req.bike_id,
            bike_preset=req.bike_preset,
            power_boost_pct=req.power_boost_pct,
            mass_delta_kg=req.mass_delta_kg,
            rider_mass_kg=req.rider_mass_kg,
            venue_id=req.venue_id,
            front_tire_id=req.front_tire_id,
            rear_tire_id=req.rear_tire_id,
            ambient_temp_c=req.ambient_temp_c,
            track_temp_c=req.track_temp_c,
            humidity_pct=req.humidity_pct,
            headwind_kmh=req.headwind_kmh,
        )
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    # Apply selected parts
    build_cost_inr = 0.0
    parts_applied = []
    if req.part_ids:
        db = _get_db()
        if db:
            try:
                from .database.bridge import apply_part_to_config

                for pid in req.part_ids:
                    row = db.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
                    if row:
                        part_dict = dict(row)
                        cfg = apply_part_to_config(cfg, part_dict)
                        parts_applied.append({
                            "id": part_dict["id"],
                            "name": part_dict.get("model_name", ""),
                            "brand": part_dict.get("brand", ""),
                            "price_inr": part_dict.get("price_inr"),
                        })
                        if part_dict.get("price_inr"):
                            build_cost_inr += float(part_dict["price_inr"])
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to apply parts %s: %s", req.part_ids, e
                )

    # Run stock sim for comparison if parts are applied
    # "Stock" means same slider overrides but NO parts — shows parts-only delta
    stock_et = None
    if parts_applied:
        try:
            stock_cfg = _build_config(
                bike_id=req.bike_id,
                bike_preset=req.bike_preset,
                power_boost_pct=req.power_boost_pct,
                mass_delta_kg=req.mass_delta_kg,
                rider_mass_kg=req.rider_mass_kg,
                venue_id=req.venue_id,
                front_tire_id=req.front_tire_id,
                rear_tire_id=req.rear_tire_id,
                ambient_temp_c=req.ambient_temp_c,
                track_temp_c=req.track_temp_c,
                humidity_pct=req.humidity_pct,
                headwind_kmh=req.headwind_kmh,
            )
            stock_sim = MotoQuantEngine(stock_cfg).run()
            stock_et = round(float(stock_sim.time_quarter), 4)
        except Exception:
            pass

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run()
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    result = {
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * 3.6, 2),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "et_eighth_s": round(float(sim.time_eighth), 4),
        "bike_name": cfg.name,
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
        "parts_applied": parts_applied,
        "build_cost_inr": round(build_cost_inr, 0),
        "stock_et_s": stock_et,
        "et_delta_s": round(float(sim.time_quarter) - stock_et, 4) if stock_et else None,
    }
    return result


@app.get("/api/parts/categories")
def list_parts_categories():
    """Return all parts categories."""
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        rows = db.execute(
            "SELECT * FROM parts_categories ORDER BY display_name"
        ).fetchall()
        return {"categories": [dict(r) for r in rows]}
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


@app.get("/api/parts")
def list_parts(
    category: str | None = Query(None, description="Filter by category name"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    bike_id: int | None = Query(None, description="Show compatibility for this bike"),
    search: str | None = Query(None),
    limit: int = Query(100, le=200),
):
    """Return parts catalog, optionally filtered by category and bike compatibility."""
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        query = """SELECT p.*, pc.name as category_name, pc.display_name as category_display
                   FROM parts p
                   JOIN parts_categories pc ON p.category_id = pc.id
                   WHERE 1=1"""
        params: list[Any] = []

        if category:
            query += " AND LOWER(pc.name) = LOWER(?)"
            params.append(category)
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if search:
            query += " AND (p.brand LIKE ? OR p.model_name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]

        query += " ORDER BY pc.display_name, p.brand, p.model_name LIMIT ?"
        params.append(limit)

        rows = db.execute(query, params).fetchall()
        parts = []
        for r in rows:
            d = dict(r)
            # Parse JSON fields for frontend
            for field in ("param_overrides", "param_deltas", "param_multipliers",
                          "specifications", "compatible_bikes"):
                if d.get(field) and isinstance(d[field], str):
                    try:
                        d[field] = json.loads(d[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            parts.append(d)

        return {"parts": parts, "total": len(parts)}
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


@app.get("/api/leaderboard")
def leaderboard(limit: int = Query(20, le=100)):
    """Return the top simulation runs saved to the local database."""
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    try:
        # sim_runs table stores saved runs from the CLI `sim save-run` command
        rows = db.execute(
            """SELECT sr.id, sr.et_quarter_s, sr.trap_speed_kmh,
                      m.name AS manufacturer, bm.model_name AS model,
                      bm.year_from AS year, sr.created_at
               FROM sim_runs sr
               LEFT JOIN bike_configs bc ON sr.bike_config_id = bc.id
               LEFT JOIN bike_models bm ON bc.bike_model_id = bm.id
               LEFT JOIN manufacturers m ON bm.manufacturer_id = m.id
               ORDER BY sr.et_quarter_s ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return {
            "leaderboard": [dict(r) for r in rows],
            "total": len(rows),
        }
    except Exception:
        # sim_runs table may not exist yet — return empty
        return {"leaderboard": [], "total": 0}
