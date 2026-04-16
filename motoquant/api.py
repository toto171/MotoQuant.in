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


def _get_db():
    """Return a live DB connection or None if DB unavailable."""
    try:
        from .database.connection import MotoQuantDB

        db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
        db = MotoQuantDB(db_path)
        return db.conn
    except Exception:
        return None


def _bike_row_to_summary(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "manufacturer": row.get("manufacturer"),
        "model": row.get("model"),
        "year": row.get("year"),
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
) -> BikeConfig:
    """Assemble a BikeConfig from request parameters."""

    # ── Base config ─────────────────────────────────────────────────────
    cfg: BikeConfig | None = None

    if bike_id is not None:
        db = _get_db()
        if db:
            try:
                from .database.bridge import bike_row_to_config

                row = db.execute(
                    "SELECT * FROM bike_models WHERE id=?", (bike_id,)
                ).fetchone()
                if row:
                    cfg = bike_row_to_config(dict(row))
            except Exception:
                pass

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
        cfg.engine.peak_power_hp *= 1.0 + power_boost_pct / 100.0

    if mass_delta_kg != 0.0:
        cfg.chassis.dry_mass_kg += mass_delta_kg

    cfg.rider.mass_kg = rider_mass_kg

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
                    if d.get("surface_grip_multiplier") is not None:
                        cfg.environment.surface_grip_multiplier = float(
                            d["surface_grip_multiplier"]
                        )
            except Exception:
                pass

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
        query = "SELECT * FROM bike_models WHERE 1=1"
        params: list[Any] = []

        if search:
            query += " AND (manufacturer LIKE ? OR model LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if manufacturer:
            query += " AND LOWER(manufacturer) = LOWER(?)"
            params.append(manufacturer)
        if category:
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)

        query += " ORDER BY manufacturer, model LIMIT ? OFFSET ?"
        params += [limit, offset]

        rows = db.execute(query, params).fetchall()
        total = db.execute(
            "SELECT COUNT(*) FROM bike_models WHERE 1=1"
            + (" AND (manufacturer LIKE ? OR model LIKE ?)" if search else ""),
            [f"%{search}%", f"%{search}%"] if search else [],
        ).fetchone()[0]

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
        row = db.execute("SELECT * FROM bike_models WHERE id=?", (bike_id,)).fetchone()
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")

    if not row:
        raise HTTPException(404, f"Bike {bike_id} not found")

    d = dict(row)
    # Attach OEM tire fitments
    try:
        fitments = db.execute(
            """SELECT tf.position, tf.fitment_type,
                      tm.manufacturer, tm.model, tm.size_front, tm.size_rear,
                      tm.id as tire_id
               FROM bike_tire_fitments tf
               JOIN tire_models tm ON tf.tire_model_id = tm.id
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
        query = "SELECT * FROM tire_models WHERE 1=1"
        params: list[Any] = []
        if compound:
            query += " AND LOWER(compound_type) = LOWER(?)"
            params.append(compound)
        if manufacturer:
            query += " AND LOWER(manufacturer) LIKE LOWER(?)"
            params.append(f"%{manufacturer}%")
        query += " ORDER BY manufacturer, model LIMIT ?"
        params.append(limit)
        rows = db.execute(query, params).fetchall()
        return {"tires": [dict(r) for r in rows]}
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
    idx = range(0, len(sim.t), step)

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
            "manufacturer": cfg.name.split(" ")[0] if cfg.name else "Unknown",
            "model": cfg.name,
            "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
            "dry_mass_kg": round(float(cfg.chassis.dry_mass_kg), 1),
        },
        "timeseries": {
            "t_s": [round(float(sim.t[i]), 4) for i in idx],
            "v_kmh": [round(float(sim.v[i]) * 3.6, 2) for i in idx],
            "x_m": [round(float(sim.x[i]), 2) for i in idx],
            "rpm": [round(float(sim.rpm[i]), 0) for i in idx]
            if hasattr(sim, "rpm")
            else [],
            "gear": [int(sim.gear[i]) for i in idx] if hasattr(sim, "gear") else [],
            "accel_g": [round(float(sim.a[i]) / 9.81, 3) for i in idx],
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
        )
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run()
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    return {
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * 3.6, 2),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "et_eighth_s": round(float(sim.time_eighth), 4),
        "bike_name": cfg.name,
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.dry_mass_kg + req.rider_mass_kg), 1),
    }


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
                      bm.manufacturer, bm.model, bm.year,
                      sr.created_at
               FROM sim_runs sr
               LEFT JOIN bike_models bm ON sr.bike_model_id = bm.id
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
