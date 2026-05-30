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
import sqlite3
import tempfile
from datetime import datetime, timezone
from typing import Any, TypedDict

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .physics import MotoQuantEngine

# ─── Auth dependency (imported early so Depends() default-args resolve) ───────
# Wrapped in try/except so the server still starts without python-jose installed
# (tests stub this out; production must have all deps in requirements-api.txt).
try:
    from .auth import require_tier as require_tier  # noqa: PLC0414
except ImportError:  # pragma: no cover
    def require_tier(_tier: str):  # type: ignore[misc]
        """Stub — replace by installing python-jose[cryptography]."""

        def _noop() -> dict:
            return {}

        return _noop  # callers wrap with Depends(require_tier(...))


# ─── App init ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="MotoQuant Pro API",
    description="First-principles motorcycle drag racing simulator -- motoquant.in",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Optional Sentry error tracking. No-ops if SENTRY_DSN is not set OR if
# sentry-sdk isn't installed. See motoquant.observability for env knobs.
from motoquant.observability import init_sentry as _init_sentry  # noqa: E402
_init_sentry(app_name="motoquant-api")

# CORS -- allow the Next.js frontend on any origin during early development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── DB helper ────────────────────────────────────────────────────────────

_db_conn = None  # module-level singleton -- one connection, reused across requests


def _get_db():
    """Return a live DB connection or None if DB unavailable.

    Uses a module-level singleton to avoid creating (and leaking) a new
    connection on every request.  SQLite is single-writer anyway, so a
    shared connection is the correct approach for a read-heavy API.
    """
    global _db_conn
    if _db_conn is not None:
        try:
            # Quick liveness check -- will throw if connection is closed/broken
            _db_conn.execute("SELECT 1")
            return _db_conn
        except Exception as e:
            logging.getLogger(__name__).warning(
                "DB liveness check failed, reconnecting: %s", e
            )
            _db_conn = None  # stale -- reconnect below

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


class BikeRowSummary(TypedDict):
    """Shape of the dict returned by :func:`_bike_row_to_summary`.

    Mirrors the ``BikeSummary`` TypeScript interface in
    ``desktop/src/types/api.ts``. Every field is nullable because
    ``row.get(...)`` returns ``None`` for any column the DB row is missing
    (e.g. a partially-scraped bike with no ``peak_power_hp``). ``id`` is
    nullable at the type level for symmetry with the other fields and to
    survive a hypothetical row that lacks a JOIN — in practice the DB
    schema guarantees ``id`` is an ``INTEGER PRIMARY KEY``.

    Keep field names + types in lockstep with
    ``desktop/src/types/api.ts::BikeSummary`` — any drift between the two
    silently breaks the desktop UI's typing guarantees.
    """

    id: int | None
    manufacturer: str | None
    model: str | None
    year: int | None
    category: str | None
    displacement_cc: float | None
    peak_power_hp: float | None
    dry_mass_kg: float | None
    data_quality: str | None


def _bike_row_to_summary(row: dict[str, Any]) -> BikeRowSummary:
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
    """POST /api/simulate -- full simulation request."""

    # Bike selection -- one of these must be provided
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
    ambient_temp_c: float | None = Field(None, description="Ambient temperature C")
    track_temp_c: float | None = Field(None, description="Track surface temperature C")
    humidity_pct: float | None = Field(None, description="Relative humidity 0-100%")
    headwind_kmh: float | None = Field(
        None, description="Headwind km/h (negative = tailwind)"
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
    """POST /api/simulate/quick -- minimal input for slider-driven UI."""

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

    # -- Base config ---------------------------------------------------------
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

    # -- Apply overrides -----------------------------------------------------
    if power_boost_pct != 0.0:
        scale = 1.0 + power_boost_pct / 100.0
        cfg.engine.peak_power_hp *= scale
        cfg.engine.peak_torque_nm *= scale
        # Scale dyno curve too -- the engine reads torque from here, not peak_power_hp
        if cfg.engine.dyno_curve is not None:
            cfg.engine.dyno_curve.torque_nm = cfg.engine.dyno_curve.torque_nm * scale

    if mass_delta_kg != 0.0:
        cfg.chassis.dry_mass_kg += mass_delta_kg

    # Set rider mass in both places -- physics engine reads from chassis.rider_mass_kg
    cfg.rider.mass_kg = rider_mass_kg
    cfg.chassis.rider_mass_kg = rider_mass_kg

    # -- Venue conditions ----------------------------------------------------
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
                        "concrete": 1.05,  # prepped concrete (NHRA-style)
                        "asphalt": 1.00,  # baseline
                        "prepped": 1.10,  # VHT-prepped
                    }
                    cfg.environment.surface_grip_multiplier = grip_map.get(
                        surface, 1.00
                    )
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to load venue %s: %s", venue_id, e
                )

    # -- Environment overrides (on top of venue) -----------------------------
    if ambient_temp_c is not None:
        cfg.environment.ambient_temp_c = ambient_temp_c
    if track_temp_c is not None:
        cfg.environment.track_temp_c = track_temp_c
    if humidity_pct is not None:
        cfg.environment.relative_humidity_pct = humidity_pct
    if headwind_kmh is not None:
        cfg.environment.wind_speed_ms = headwind_kmh / 3.6
        cfg.environment.wind_direction_deg = 0.0  # 0 = headwind

    # -- Tire overrides ------------------------------------------------------
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


# ─────────────────────────────────────────────────────────────────────────
# Anonymous telemetry endpoint
# ─────────────────────────────────────────────────────────────────────────
# Used by web/lib/telemetry.js to capture client-side events:
#   - sim_run_start / sim_run_success / sim_run_error
#   - js_error / js_unhandled_rejection
#   - bike_select / mode_change
# Privacy: no user id, no IP correlation, per-tab random session_id only.
# Storage: stdout (Railway log stream); ship to PostHog/Logfire later
# without changing the client.

@app.post("/api/telemetry/event")
async def telemetry_event(payload: dict = None):
    """Log one anonymous client telemetry event. Always 200 — telemetry
    must never surface as a user-facing error."""
    if payload is None or not isinstance(payload, dict):
        return {"ok": True}
    event = str(payload.get("event", ""))[:64] or "unknown"
    session_id = str(payload.get("session_id", ""))[:64]
    props = payload.get("props") if isinstance(payload.get("props"), dict) else {}
    safe_props = {
        str(k)[:64]: (str(v)[:200] if isinstance(v, str) else v)
        for k, v in list(props.items())[:32]
        if isinstance(v, (str, int, float, bool, type(None)))
    }
    viewport = payload.get("viewport") if isinstance(payload.get("viewport"), dict) else {}
    path = str(payload.get("path", ""))[:128]
    ua = str(payload.get("ua", ""))[:200]
    try:
        logging.getLogger(__name__).info(
            "TELEMETRY event=%s session=%s path=%s vw=%sx%s ua=%s props=%s",
            event,
            session_id[:8],
            path,
            viewport.get("w"),
            viewport.get("h"),
            ua[:80],
            safe_props,
        )
    except Exception:
        pass
    return {"ok": True}


@app.get("/api/bikes")
def list_bikes(
    search: str | None = Query(None, description="Search by model/manufacturer"),
    manufacturer: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(100, le=5000),
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

    # Expose all bike_models columns (not just the summary subset)
    full = dict(row)
    d = _bike_row_to_summary(full)
    # Merge in remaining headline columns that detail pages need
    for extra in (
        "model_code",
        "year_to",
        "subcategory",
        "cylinder_count",
        "cylinder_config",
        "bore_mm",
        "stroke_mm",
        "compression_ratio",
        "peak_power_rpm",
        "peak_torque_nm",
        "peak_torque_rpm",
        "wet_mass_kg",
        "wheelbase_mm",
        "seat_height_mm",
        "fuel_capacity_l",
        "validation_et_s",
        "validation_trap_kmh",
        "validation_source",
    ):
        if extra in full:
            d[extra] = full[extra]

    # Attach latest bike_config JSON sub-blocks (aero, drivetrain, engine extras, tire)
    try:
        cfg_row = db.execute(
            """SELECT engine_params, aero_params, drivetrain_params, tire_params,
                      chassis_params, config_name
               FROM bike_configs
               WHERE bike_model_id = ? AND is_current = 1
               ORDER BY version DESC
               LIMIT 1""",
            (bike_id,),
        ).fetchone()
        if cfg_row:
            import json as _json

            def _safe_parse(blob):
                if not blob:
                    return {}
                try:
                    return _json.loads(blob)
                except Exception:
                    return {}

            engine = _safe_parse(cfg_row["engine_params"])
            aero = _safe_parse(cfg_row["aero_params"])
            drive = _safe_parse(cfg_row["drivetrain_params"])
            tire = _safe_parse(cfg_row["tire_params"])
            chassis = _safe_parse(cfg_row["chassis_params"])

            # Expose common simulation-relevant fields at top level
            if engine:
                for k in ("redline_rpm", "cylinder_count", "cylinder_config"):
                    v = engine.get(k)
                    if v is not None and d.get(k) in (None, ""):
                        d[k] = v
            if aero:
                for k in ("cd", "frontal_area_m2"):
                    v = aero.get(k)
                    if v is not None:
                        d[k] = v
            if drive:
                for k in ("front_sprocket", "rear_sprocket", "chain_pitch"):
                    v = drive.get(k)
                    if v is not None:
                        d[k] = v
            if tire:
                # Expose mu_peak so the bike-detail UI can show grip class
                # alongside the raw tire model. Other tire fields stay
                # tucked inside tire_params for the detail-card expander.
                v = tire.get("mu_peak")
                if v is not None:
                    d["tire_mu_peak"] = v
            if chassis:
                # CoG height is stored as mm in chassis_params (matches
                # wheelbase_mm / seat_height_mm convention). Expose both units
                # so the detail page can format consistently.
                cog_mm = chassis.get("cog_height_mm")
                if cog_mm is None and chassis.get("cog_height_m") is not None:
                    cog_mm = chassis["cog_height_m"] * 1000.0
                if cog_mm is not None:
                    d["cog_height_mm"] = cog_mm
                    d["cog_height_m"] = cog_mm / 1000.0
                # Derived: wet mass = dry + fluids + fuel (bike_models.wet_mass_kg
                # is rarely populated by the scraper; config has the components).
                if d.get("wet_mass_kg") in (None, 0):
                    dry = chassis.get("dry_mass_kg")
                    fluid = chassis.get("fluid_mass_kg") or 0.0
                    fuel = chassis.get("fuel_mass_kg") or 0.0
                    if dry is not None:
                        d["wet_mass_kg"] = round(dry + fluid + fuel, 1)
                        d["wet_mass_derived"] = True
            # Derived: wheelbase in meters for display
            if d.get("wheelbase_mm") is not None:
                d["wheelbase_m"] = d["wheelbase_mm"] / 1000.0
    except Exception:
        # Detail page degrades gracefully if JSON blobs are malformed.
        pass

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
    limit: int = Query(200, le=5000),
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
        if arr is None or (hasattr(arr, "__len__") and len(arr) == 0):
            return [] if fallback is None else fallback
        return [transform(arr[i]) for i in idx if i < len(arr)]

    # Robust manufacturer extraction
    _mfr = "Unknown"
    if cfg.name:
        parts = cfg.name.split(" ", 1)
        _mfr = parts[0] if parts else cfg.name

    # Build response -- convert numpy to Python floats for JSON
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
            "gear_count": len(cfg.drivetrain.gear_ratios)
            if cfg.drivetrain.gear_ratios
            else 0,
            "cd": round(float(cfg.aero.cd), 3)
            if hasattr(cfg, "aero") and cfg.aero
            else None,
            "rider_mass_kg": round(float(cfg.chassis.rider_mass_kg), 1),
        },
        "timeseries": {
            "t_s": _safe_array(sim.t, lambda v: round(float(v), 4)),
            "v_kmh": _safe_array(sim.v, lambda v: round(float(v) * 3.6, 2)),
            "x_m": _safe_array(sim.x, lambda v: round(float(v), 2)),
            "rpm": _safe_array(sim.rpm, lambda v: round(float(v), 0)),
            "gear": _safe_array(sim.gear, lambda v: int(v)),
            "accel_g": _safe_array(sim.a, lambda v: round(float(v) / 9.81, 3)),
            "traction_pct": _safe_array(
                sim.traction_pct, lambda v: round(float(v) * 100, 1)
            ),
            "tire_temp_c": _safe_array(sim.T_tire, lambda v: round(float(v), 1)),
            "power_kw": _safe_array(sim.power_kw, lambda v: round(float(v), 1)),
            "F_drive_N": _safe_array(sim.F_drive, lambda v: round(float(v), 0)),
            "F_drag_N": _safe_array(sim.F_drag, lambda v: round(float(v), 0)),
        },
    }


@app.post("/api/simulate/quick")
def simulate_quick(req: QuickSimRequest):
    """
    Quick ET-only simulation -- no time-series arrays.
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
                    row = db.execute(
                        "SELECT * FROM parts WHERE id=?", (pid,)
                    ).fetchone()
                    if row:
                        part_dict = dict(row)
                        cfg = apply_part_to_config(cfg, part_dict)
                        parts_applied.append(
                            {
                                "id": part_dict["id"],
                                "name": part_dict.get("model_name", ""),
                                "brand": part_dict.get("brand", ""),
                                "price_inr": part_dict.get("price_inr"),
                            }
                        )
                        if part_dict.get("price_inr"):
                            build_cost_inr += float(part_dict["price_inr"])
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to apply parts %s: %s", req.part_ids, e
                )

    # Run stock sim for comparison if parts are applied
    # "Stock" means same slider overrides but NO parts -- shows parts-only delta
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
        "et_delta_s": round(float(sim.time_quarter) - stock_et, 4)
        if stock_et
        else None,
    }
    return result


class TopSpeedRequest(BaseModel):
    """POST /api/simulate/top-speed — runs until terminal velocity."""

    bike_id: int | None = None
    bike_preset: str | None = None
    power_boost_pct: float = 0.0
    mass_delta_kg: float = 0.0
    rider_mass_kg: float = 75.0
    part_ids: list[int] = Field(default_factory=list)
    front_tire_id: int | None = None
    rear_tire_id: int | None = None
    venue_id: int | None = None
    ambient_temp_c: float | None = None
    track_temp_c: float | None = None
    humidity_pct: float | None = None
    headwind_kmh: float | None = None
    # LSR-specific: optional override for max time/distance
    max_time_s: float = 120.0
    include_timeseries: bool = False


@app.post("/api/simulate/top-speed")
def simulate_top_speed(req: TopSpeedRequest):
    """
    Run the simulation until terminal velocity is reached.

    Returns terminal velocity (km/h + mph), time/distance to reach it,
    power at terminal, gear, RPM, and LSR split times (1/4 mi, 1/2 mi,
    1 km, 1 mi, 2 mi). Ideal for top-speed runs and land speed record
    events.
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

    build_cost_inr = 0.0
    parts_applied = []
    if req.part_ids:
        db = _get_db()
        if db:
            try:
                from .database.bridge import apply_part_to_config

                for pid in req.part_ids:
                    row = db.execute(
                        "SELECT * FROM parts WHERE id=?", (pid,)
                    ).fetchone()
                    if row:
                        part_dict = dict(row)
                        cfg = apply_part_to_config(cfg, part_dict)
                        parts_applied.append(
                            {
                                "id": part_dict["id"],
                                "name": part_dict.get("model_name", ""),
                                "brand": part_dict.get("brand", ""),
                                "price_inr": part_dict.get("price_inr"),
                            }
                        )
                        if part_dict.get("price_inr"):
                            build_cost_inr += float(part_dict["price_inr"])
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to apply parts %s: %s", req.part_ids, e
                )

    try:
        engine = MotoQuantEngine(cfg)
        ts = engine.run_top_speed(max_time=req.max_time_s)
    except Exception as exc:
        raise HTTPException(500, f"Top-speed simulation error: {exc}")

    # Format LSR splits with km/h + mph for convenience
    splits_fmt = {}
    for k, v in ts.lsr_splits.items():
        splits_fmt[k] = {
            "time_s": round(v["time_s"], 3),
            "speed_ms": round(v["speed_ms"], 2),
            "speed_kmh": round(v["speed_ms"] * 3.6, 1),
            "speed_mph": round(v["speed_ms"] * 2.23694, 1),
        }

    response = {
        "terminal_velocity_ms": round(ts.terminal_velocity_ms, 2),
        "terminal_velocity_kmh": round(ts.terminal_velocity_kmh, 1),
        "terminal_velocity_mph": round(ts.terminal_velocity_mph, 1),
        "time_to_terminal_s": round(ts.time_to_terminal_s, 2),
        "distance_to_terminal_m": round(ts.distance_to_terminal_m, 1),
        "terminal_power_kw": round(ts.terminal_power_kw, 1),
        "terminal_power_hp": round(ts.terminal_power_kw * 1.341, 1),
        "terminal_gear": ts.terminal_gear,
        "terminal_rpm": round(ts.terminal_rpm, 0),
        "reached_plateau": ts.reached_plateau,
        "lsr_splits": splits_fmt,
        "bike_name": cfg.name,
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
        "parts_applied": parts_applied,
        "build_cost_inr": round(build_cost_inr, 0),
    }

    if req.include_timeseries:
        # Downsample to 100 Hz (every 10 ms) for web payload sanity
        sim = ts.full_sim
        stride = max(1, int(0.01 / max(sim.dt, 0.0001)))
        response["timeseries"] = {
            "t": sim.t[::stride].tolist(),
            "v_ms": sim.v[::stride].tolist(),
            "v_kmh": (sim.v[::stride] * 3.6).tolist(),
            "rpm": sim.rpm[::stride].tolist(),
            "gear": sim.gear[::stride].tolist(),
            "power_kw": sim.power_kw[::stride].tolist(),
            "x_m": sim.x[::stride].tolist(),
        }

    return response


class DistanceRunRequest(BaseModel):
    """POST /api/simulate/distance — arbitrary distance for LSR events."""

    bike_id: int | None = None
    bike_preset: str | None = None
    distance_m: float = Field(
        ..., gt=0, le=20000, description="Target distance in meters"
    )
    power_boost_pct: float = 0.0
    mass_delta_kg: float = 0.0
    rider_mass_kg: float = 75.0
    part_ids: list[int] = Field(default_factory=list)
    front_tire_id: int | None = None
    rear_tire_id: int | None = None
    venue_id: int | None = None
    ambient_temp_c: float | None = None
    track_temp_c: float | None = None
    humidity_pct: float | None = None
    headwind_kmh: float | None = None
    max_time_s: float = 120.0


@app.post("/api/simulate/distance")
def simulate_distance(req: DistanceRunRequest):
    """
    Run the simulation to an arbitrary target distance.

    Use for LSR events: standing mile (1609.344 m), standing kilo (1000 m),
    1/2 mile (804.672 m), Bonneville short course (3218 m), etc.
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

    if req.part_ids:
        db = _get_db()
        if db:
            try:
                from .database.bridge import apply_part_to_config

                for pid in req.part_ids:
                    row = db.execute(
                        "SELECT * FROM parts WHERE id=?", (pid,)
                    ).fetchone()
                    if row:
                        cfg = apply_part_to_config(cfg, dict(row))
            except Exception as e:
                logging.getLogger(__name__).warning("Parts apply failed: %s", e)

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run_distance(req.distance_m, max_time=req.max_time_s)
    except Exception as exc:
        raise HTTPException(500, f"Distance run error: {exc}")

    # Terminal/trap values at the target distance
    import numpy as np

    target_idx = int(np.searchsorted(sim.x, req.distance_m))
    if target_idx >= len(sim.t):
        target_idx = len(sim.t) - 1
    trap_time = float(sim.t[target_idx])
    trap_v = float(sim.v[target_idx])

    return {
        "distance_m": req.distance_m,
        "time_s": round(trap_time, 3),
        "trap_speed_ms": round(trap_v, 2),
        "trap_speed_kmh": round(trap_v * 3.6, 1),
        "trap_speed_mph": round(trap_v * 2.23694, 1),
        "peak_velocity_kmh": round(float(max(sim.v)) * 3.6, 1),
        "bike_name": cfg.name,
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
    }


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
    compatible_only: bool = Query(
        True,
        description="When bike_id is set: if True (default) only return compatible "
        "parts; if False, return all parts with a 'compatible' + 'fitment_reason' "
        "annotation per row.",
    ),
    search: str | None = Query(None),
    limit: int = Query(500, le=5000),
):
    """Return parts catalog, optionally filtered by category and bike compatibility.

    Default limit raised from 100→500 so the full 465-part catalog fits in one
    page. Cap raised to 1000 to leave headroom as the catalog grows.

    When ``bike_id`` is provided, each returned part is evaluated against the
    bike's fitment rules (stroke_type, manufacturer, engine_config, displacement,
    chain_pitch). Set ``compatible_only=false`` to receive every part with an
    annotation instead of a hard filter (useful for the Streamlit/Next.js UI
    which greys-out incompatible options).
    """
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

        # ── Bike compatibility annotation / filter ─────────────────────────
        bike_row: dict | None = None
        if bike_id is not None:
            from .database.parts_repo import _enrich_bike_row_for_fitment
            from .parts.compatibility import is_compatible  # noqa: F401

            raw = db.execute(
                "SELECT * FROM bike_models WHERE id = ?", (bike_id,)
            ).fetchone()
            if raw is None:
                raise HTTPException(404, f"Bike {bike_id} not found")
            bike_row = dict(raw)
            _enrich_bike_row_for_fitment(db, bike_row)

        parts = []
        for r in rows:
            d = dict(r)
            # Evaluate compatibility BEFORE parsing JSON fields in-place
            # (is_compatible expects the raw fitment_rules JSON string).
            if bike_row is not None:
                from .parts.compatibility import is_compatible

                compat, reason = is_compatible(d, bike_row)
                if compatible_only and not compat:
                    continue
                d["compatible"] = bool(compat)
                d["fitment_reason"] = reason

            # Parse JSON fields for frontend
            for field in (
                "param_overrides",
                "param_deltas",
                "param_multipliers",
                "specifications",
                "compatible_bikes",
                "fitment_rules",
            ):
                if d.get(field) and isinstance(d[field], str):
                    try:
                        d[field] = json.loads(d[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            parts.append(d)

        return {
            "parts": parts,
            "total": len(parts),
            "bike_id": bike_id,
            "compatible_only": bool(bike_id is not None and compatible_only),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


class SaveRunRequest(BaseModel):
    """POST /api/simulate/save — persist a sim result to the sim_runs table
    so it surfaces on /api/leaderboard and the desktop History tab."""

    bike_id: int
    venue_id: int | None = None
    et_quarter_s: float
    trap_speed_kmh: float
    et_60ft_s: float | None = None
    et_eighth_s: float | None = None
    et_1000ft_s: float | None = None
    notes: str | None = None


@app.post("/api/simulate/save", status_code=201)
def save_simulation(
    req: SaveRunRequest,
    _auth: dict = Depends(require_tier("pro")),  # noqa: B008
):
    """Persist a single sim result to sim_runs. Resolves the incoming
    bike_models.id to a bike_configs.id using the seed's 1:1 mapping."""
    from . import __version__

    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    row = db.execute(
        "SELECT id FROM bike_configs WHERE bike_model_id = ? "
        "ORDER BY is_current DESC LIMIT 1",
        (req.bike_id,),
    ).fetchone()
    if not row:
        raise HTTPException(
            404,
            f"No bike_config found for bike_model_id={req.bike_id}. "
            "Re-seed with `python -m motoquant.run import --known-bikes`.",
        )
    bike_config_id = row["id"]

    split_times = {
        "time_60ft": req.et_60ft_s,
        "time_eighth": req.et_eighth_s,
        "time_1000ft": req.et_1000ft_s,
        "time_quarter": req.et_quarter_s,
        "speed_quarter_kmh": req.trap_speed_kmh,
    }

    try:
        cur = db.execute(
            """INSERT INTO sim_runs
               (bike_config_id, venue_id, et_quarter_s, trap_speed_kmh,
                et_eighth_s, time_60ft_s, time_1000ft_s,
                sim_version, split_times_json, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                bike_config_id,
                req.venue_id,
                req.et_quarter_s,
                req.trap_speed_kmh,
                req.et_eighth_s,
                req.et_60ft_s,
                req.et_1000ft_s,
                __version__,
                json.dumps(split_times),
                req.notes,
            ),
        )
        db.commit()
    except sqlite3.Error as exc:
        raise HTTPException(500, f"Failed to persist run: {exc}")

    return {
        "run_id": cur.lastrowid,
        "bike_id": req.bike_id,
        "bike_config_id": bike_config_id,
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
        # sim_runs table may not exist yet -- return empty
        return {"leaderboard": [], "total": 0}


# --- A vs B Comparison ---------------------------------------------------


class CompareRequest(BaseModel):
    """POST /api/simulate/compare - two builds side-by-side."""

    # Build A (baseline)
    a_bike_id: int | None = None
    a_bike_preset: str | None = None
    a_power_boost_pct: float = 0.0
    a_mass_delta_kg: float = 0.0
    a_rider_mass_kg: float = 75.0
    a_part_ids: list[int] = Field(default_factory=list)
    a_front_tire_id: int | None = None
    a_rear_tire_id: int | None = None

    # Build B (modified)
    b_bike_id: int | None = None
    b_bike_preset: str | None = None
    b_power_boost_pct: float = 0.0
    b_mass_delta_kg: float = 0.0
    b_rider_mass_kg: float = 75.0
    b_part_ids: list[int] = Field(default_factory=list)
    b_front_tire_id: int | None = None
    b_rear_tire_id: int | None = None

    # Shared conditions
    venue_id: int | None = None
    ambient_temp_c: float | None = None
    track_temp_c: float | None = None
    humidity_pct: float | None = None
    headwind_kmh: float | None = None


def _run_build(
    bike_id,
    bike_preset,
    power_boost_pct,
    mass_delta_kg,
    rider_mass_kg,
    part_ids,
    front_tire_id,
    rear_tire_id,
    venue_id,
    ambient_temp_c,
    track_temp_c,
    humidity_pct,
    headwind_kmh,
):
    """Build config, apply parts, run sim, return (sim, cfg, parts_applied, cost)."""
    cfg = _build_config(
        bike_id=bike_id,
        bike_preset=bike_preset,
        power_boost_pct=power_boost_pct,
        mass_delta_kg=mass_delta_kg,
        rider_mass_kg=rider_mass_kg,
        venue_id=venue_id,
        front_tire_id=front_tire_id,
        rear_tire_id=rear_tire_id,
        ambient_temp_c=ambient_temp_c,
        track_temp_c=track_temp_c,
        humidity_pct=humidity_pct,
        headwind_kmh=headwind_kmh,
    )
    build_cost = 0.0
    parts_applied = []
    if part_ids:
        db = _get_db()
        if db:
            try:
                from .database.bridge import apply_part_to_config

                for pid in part_ids:
                    row = db.execute(
                        "SELECT * FROM parts WHERE id=?", (pid,)
                    ).fetchone()
                    if row:
                        pd = dict(row)
                        cfg = apply_part_to_config(cfg, pd)
                        parts_applied.append(
                            {
                                "id": pd["id"],
                                "name": pd.get("model_name", ""),
                                "brand": pd.get("brand", ""),
                            }
                        )
                        if pd.get("price_inr"):
                            build_cost += float(pd["price_inr"])
            except Exception as e:
                logging.getLogger(__name__).warning("Parts apply error: %s", e)

    sim = MotoQuantEngine(cfg).run()
    return sim, cfg, parts_applied, build_cost


def _build_summary(sim, cfg, parts_applied, build_cost, label, include_timeseries=True):
    """Create a response dict from a sim run."""
    step = max(1, len(sim.t) // 1000)
    idx = list(range(0, len(sim.t), step))

    def _sa(arr, transform):
        if arr is None or (hasattr(arr, "__len__") and len(arr) == 0):
            return []
        return [transform(arr[i]) for i in idx if i < len(arr)]

    result = {
        "label": label,
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * 3.6, 2),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "et_eighth_s": round(float(sim.time_eighth), 4),
        "bike_name": cfg.name or "Unknown",
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
        "parts_applied": parts_applied,
        "build_cost_inr": round(build_cost, 0),
    }
    if include_timeseries:
        result["timeseries"] = {
            "t_s": _sa(sim.t, lambda v: round(float(v), 4)),
            "v_kmh": _sa(sim.v, lambda v: round(float(v) * 3.6, 2)),
            "rpm": _sa(sim.rpm, lambda v: round(float(v), 0)),
            "gear": _sa(sim.gear, lambda v: int(v)),
            "accel_g": _sa(sim.a, lambda v: round(float(v) / 9.81, 3)),
            "traction_pct": _sa(sim.traction_pct, lambda v: round(float(v) * 100, 1)),
            "power_kw": _sa(sim.power_kw, lambda v: round(float(v), 1)),
        }
    return result


@app.post("/api/simulate/compare")
def simulate_compare(req: CompareRequest):
    """Run two builds side-by-side and return full results for both."""
    try:
        sim_a, cfg_a, parts_a, cost_a = _run_build(
            req.a_bike_id,
            req.a_bike_preset,
            req.a_power_boost_pct,
            req.a_mass_delta_kg,
            req.a_rider_mass_kg,
            req.a_part_ids,
            req.a_front_tire_id,
            req.a_rear_tire_id,
            req.venue_id,
            req.ambient_temp_c,
            req.track_temp_c,
            req.humidity_pct,
            req.headwind_kmh,
        )
        sim_b, cfg_b, parts_b, cost_b = _run_build(
            req.b_bike_id,
            req.b_bike_preset,
            req.b_power_boost_pct,
            req.b_mass_delta_kg,
            req.b_rider_mass_kg,
            req.b_part_ids,
            req.b_front_tire_id,
            req.b_rear_tire_id,
            req.venue_id,
            req.ambient_temp_c,
            req.track_temp_c,
            req.humidity_pct,
            req.headwind_kmh,
        )
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    a = _build_summary(sim_a, cfg_a, parts_a, cost_a, "A")
    b = _build_summary(sim_b, cfg_b, parts_b, cost_b, "B")

    delta_et = round(b["et_quarter_s"] - a["et_quarter_s"], 4)
    delta_trap = round(b["trap_speed_kmh"] - a["trap_speed_kmh"], 2)

    return {
        "a": a,
        "b": b,
        "delta": {
            "et_s": delta_et,
            "trap_kmh": delta_trap,
            "faster": "B" if delta_et < 0 else "A" if delta_et > 0 else "tie",
            "cost_diff_inr": round(cost_b - cost_a, 0),
        },
    }


# --- Dragy / Dyno Upload -------------------------------------------------


@app.post("/api/calibrate/dragy")
async def upload_dragy(
    file: UploadFile = File(..., description="Dragy CSV or JSON export"),
    bike_id: int | None = Form(None, description="Bike to overlay sim against"),
    bike_preset: str | None = Form(None),
    _auth: dict = Depends(require_tier("studio")),  # noqa: B008
):
    """
    Upload a Dragy GPS file, parse it, and optionally overlay against simulation.
    Returns parsed run data (ET, trap, splits, v(t)) and if a bike is specified,
    also runs a sim and returns the comparison overlay.
    """
    log = logging.getLogger(__name__)

    try:
        content = await file.read()
        suffix = (
            ".json" if file.filename and file.filename.endswith(".json") else ".csv"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(400, f"Failed to read upload: {exc}")

    try:
        from .calibration.dragy import best_run as dragy_best, parse_dragy_file

        runs = parse_dragy_file(tmp_path)
    except Exception as exc:
        log.warning("Dragy parse error: %s", exc)
        raise HTTPException(422, f"Failed to parse Dragy file: {exc}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not runs:
        raise HTTPException(422, "No valid runs detected in the Dragy file")

    best = dragy_best(runs)

    def _run_to_dict(run):
        splits = run.splits()
        step = max(1, len(run.timestamps) // 200)
        return {
            "et_quarter_s": round(float(run.et_quarter), 4),
            "trap_speed_kmh": round(float(run.trap_speed_ms) * 3.6, 2),
            "trap_speed_ms": round(float(run.trap_speed_ms), 3),
            "splits": {k: round(float(v), 4) for k, v in splits.items()},
            "n_samples": len(run.timestamps),
            "duration_s": round(float(run.timestamps[-1]), 2),
            "timeseries": {
                "t_s": [
                    round(float(run.timestamps[i]), 4)
                    for i in range(0, len(run.timestamps), step)
                ],
                "v_kmh": [
                    round(float(run.velocity_ms[i]) * 3.6, 2)
                    for i in range(0, len(run.velocity_ms), step)
                ],
                "x_m": [
                    round(float(run.distance_m[i]), 2)
                    for i in range(0, len(run.distance_m), step)
                ],
            },
        }

    result = {
        "runs_detected": len(runs),
        "best_run": _run_to_dict(best),
        "all_runs": [_run_to_dict(r) for r in runs],
        "filename": file.filename,
    }

    if bike_id is not None or bike_preset is not None:
        try:
            cfg = _build_config(
                bike_id=bike_id,
                bike_preset=bike_preset,
                power_boost_pct=0,
                mass_delta_kg=0,
                rider_mass_kg=75,
            )
            sim = MotoQuantEngine(cfg).run()
            from .calibration.overlay import compare_runs

            comparison = compare_runs(best, sim)
            result["overlay"] = {
                "sim_et_s": round(float(sim.time_quarter), 4),
                "sim_trap_kmh": round(float(sim.speed_quarter) * 3.6, 2),
                "et_error_s": round(float(comparison.et_error_s), 4),
                "et_error_pct": round(float(comparison.et_error_pct), 2),
                "trap_error_kmh": round(float(comparison.trap_error_ms) * 3.6, 2),
                "v_rmse_kmh": round(float(comparison.rmse_ms) * 3.6, 2),
                "bike_name": cfg.name,
                "sim_timeseries": {
                    "t_s": [
                        round(float(sim.t[i]), 4)
                        for i in range(0, len(sim.t), max(1, len(sim.t) // 200))
                    ],
                    "v_kmh": [
                        round(float(sim.v[i]) * 3.6, 2)
                        for i in range(0, len(sim.v), max(1, len(sim.v) // 200))
                    ],
                },
            }
        except Exception as exc:
            log.warning("Overlay failed for bike_id=%s: %s", bike_id, exc)
            result["overlay_error"] = str(exc)

    return result


@app.post("/api/calibrate/dyno")
async def upload_dyno(
    file: UploadFile = File(
        ..., description="Dyno CSV export (DynoJet, generic, or MoTeC)"
    ),
    temp_c: float | None = Form(None, description="Ambient temperature during run [C]"),
    pressure_kpa: float | None = Form(None, description="Barometric pressure [kPa]"),
    rh_pct: float = Form(0.0, description="Relative humidity [%]"),
    _auth: dict = Depends(require_tier("studio")),  # noqa: B008
):
    """Upload a dyno CSV, parse it with SAE J1349 correction, return power/torque curve."""
    log = logging.getLogger(__name__)

    try:
        content = await file.read()
        suffix = ".txt" if file.filename and file.filename.endswith(".txt") else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(400, f"Failed to read upload: {exc}")

    try:
        from .calibration.dyno import parse_dyno_file

        dyno_result = parse_dyno_file(
            tmp_path,
            temp_c=temp_c,
            pressure_kpa=pressure_kpa,
            rh_pct=rh_pct,
        )
    except Exception as exc:
        log.warning("Dyno parse error: %s", exc)
        raise HTTPException(422, f"Failed to parse dyno file: {exc}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    n = len(dyno_result.rpm)
    step = max(1, n // 200)
    idx = list(range(0, n, step))

    return {
        "peak_power_hp": round(float(dyno_result.peak_power_kw) * 1.34102, 1),
        "peak_power_kw": round(float(dyno_result.peak_power_kw), 2),
        "peak_torque_nm": round(float(dyno_result.peak_torque_nm), 2),
        "rpm_at_peak_power": round(float(dyno_result.rpm_at_peak_power), 0),
        "rpm_at_peak_torque": round(float(dyno_result.rpm_at_peak_torque), 0),
        "correction_factor": round(float(dyno_result.correction_factor), 4),
        "is_at_wheel": dyno_result.is_at_wheel,
        "n_points": n,
        "filename": file.filename,
        "curve": {
            "rpm": [round(float(dyno_result.rpm[i]), 0) for i in idx],
            "power_hp": [
                round(float(dyno_result.power_kw[i]) * 1.34102, 2) for i in idx
            ],
            "torque_nm": [round(float(dyno_result.torque_nm[i]), 2) for i in idx],
        },
    }


# --- Bike Suggestions (user submissions) ---------------------------------


class BikeSuggestionRequest(BaseModel):
    """POST /api/bikes/suggest -- user-submitted bike addition request."""

    make: str = Field(
        ..., min_length=1, max_length=60, description="Manufacturer (e.g. 'Kawasaki')"
    )
    model: str = Field(
        ..., min_length=1, max_length=80, description="Model name (e.g. 'ZX-6R 636')"
    )
    year: int | None = Field(None, ge=1960, le=2099, description="Model year")
    displacement_cc: float | None = Field(
        None, gt=0, le=5000, description="Engine displacement in cc"
    )
    peak_power_hp: float | None = Field(
        None, gt=0, le=600, description="Peak power (hp)"
    )
    dry_mass_kg: float | None = Field(None, gt=0, le=800, description="Dry mass (kg)")
    category: str | None = Field(
        None,
        max_length=40,
        description="sport / naked / cruiser / adv / drag / touring",
    )
    notes: str | None = Field(
        None, max_length=2000, description="Free-form rider context"
    )
    submitter_email: str | None = Field(
        None, max_length=254, description="Optional -- reply address"
    )
    source_url: str | None = Field(
        None, max_length=500, description="Optional spec-sheet URL"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "make": "Kawasaki",
                "model": "ZX-6R 636",
                "year": 2024,
                "displacement_cc": 636,
                "peak_power_hp": 128,
                "dry_mass_kg": 196,
                "category": "sport",
                "notes": "Would love to see this in the simulator",
                "submitter_email": "rider@example.com",
            }
        }


@app.post("/api/bikes/suggest", status_code=201)
def suggest_bike(req: BikeSuggestionRequest):
    """
    Submit a bike to be added to the catalog.

    Returns `201 Created` with the suggestion id on success. Plausibility
    violations (displacement > 3500cc, etc.) are stored anyway but flagged for
    manual review; the `flagged_out_of_bounds` field in the response tells the
    client whether the submission was accepted as-is or flagged.
    """
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    try:
        # Reuse the shared DB connection directly -- the repo only needs a
        # connection-like object, so we skip the MotoQuantDB facade here.
        from .database.bike_suggestions_repo import BikeSuggestionsRepository

        repo = BikeSuggestionsRepository(db)
        result = repo.create(
            make=req.make,
            model=req.model,
            year=req.year,
            displacement_cc=req.displacement_cc,
            peak_power_hp=req.peak_power_hp,
            dry_mass_kg=req.dry_mass_kg,
            category=req.category,
            notes=req.notes,
            submitter_email=req.submitter_email,
            source_url=req.source_url,
        )
    except ValueError as exc:
        # Empty make/model -- shouldn't happen thanks to Pydantic min_length, but belt-and-braces
        raise HTTPException(422, str(exc))
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Failed to store bike suggestion: %s", exc, exc_info=True
        )
        raise HTTPException(500, f"Database error: {exc}")

    return {
        "id": result["id"],
        "status": "pending",
        "flagged_out_of_bounds": result["flagged_out_of_bounds"],
        "issues": result["issues"],
        "message": (
            "Thanks! Your submission is queued for review."
            if not result["flagged_out_of_bounds"]
            else "Submission stored, but some fields are out of expected range and will be manually verified."
        ),
    }


# --- Spec Corrections (user-submitted field-level fixes) -----------------


class SpecCorrectionRequest(BaseModel):
    """POST /api/specs/correct — propose a correction for one spec field."""

    bike_id: int = Field(
        ..., description="DB bike model ID to correct"
    )
    field_name: str = Field(
        ...,
        max_length=80,
        description=(
            "Field to correct — must be one of the allowed spec fields "
            "(see GET /api/specs/correction-fields for the full list)"
        ),
    )
    proposed_value: str = Field(
        ..., max_length=500, description="Corrected value as a string"
    )
    source_url: str | None = Field(
        None, max_length=500, description="URL of supporting evidence (optional)"
    )
    submitter_email: str | None = Field(
        None, max_length=254, description="Optional reply address"
    )
    notes: str | None = Field(
        None, max_length=2000, description="Free-form context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bike_id": 42,
                "field_name": "peak_power_hp",
                "proposed_value": "185.5",
                "source_url": "https://example.com/r15-dyno-2024.pdf",
                "submitter_email": "rider@example.com",
                "notes": "Indian Autos Mag wheel-dyno, stock R15 V4, July 2024 issue",
            }
        }


def _fetch_current_value(db, bike_id: int, field_name: str) -> str | None:
    """
    Snapshot the current value of ``field_name`` from the DB for the audit trail.
    Returns None if the field can't be found cleanly (non-blocking — we always
    store the correction regardless).
    """
    # Fields that live directly on bike_models as columns
    _HEADLINE_COLS = {
        "peak_power_hp", "peak_torque_nm", "peak_power_rpm", "peak_torque_rpm",
        "displacement_cc", "bore_mm", "stroke_mm", "compression_ratio",
        "dry_mass_kg", "wet_mass_kg", "cylinder_count", "wheelbase_mm",
        "seat_height_mm", "fuel_capacity_l",
    }
    # Fields that live inside bike_configs JSON blobs
    _BLOB_FIELD_MAP = {
        "front_sprocket":  "drivetrain_params",
        "rear_sprocket":   "drivetrain_params",
        "gear_ratios":     "drivetrain_params",
        "redline_rpm":     "engine_params",
        "cd":              "aero_params",
        "frontal_area_m2": "aero_params",
    }
    try:
        if field_name in _HEADLINE_COLS:
            row = db.execute(
                f"SELECT {field_name} FROM bike_models WHERE id = ?",  # noqa: S608
                (bike_id,),
            ).fetchone()
            if row:
                val = row[0]
                return str(val) if val is not None else None
        elif field_name in _BLOB_FIELD_MAP:
            blob_col = _BLOB_FIELD_MAP[field_name]
            cfg_row = db.execute(
                f"SELECT {blob_col} FROM bike_configs "  # noqa: S608
                "WHERE bike_model_id = ? AND is_current = 1 ORDER BY version DESC LIMIT 1",
                (bike_id,),
            ).fetchone()
            if cfg_row and cfg_row[0]:
                blob = json.loads(cfg_row[0])
                val = blob.get(field_name)
                return str(val) if val is not None else None
    except Exception:
        pass
    return None


@app.get("/api/specs/correction-fields")
def list_correction_fields():
    """Return the set of field names that users can propose corrections for.

    Shape: ``[{value, label}, ...]`` — standard dropdown-source format. The
    list is sorted by ``value`` so the dropdown ordering is stable across
    deploys.
    """
    from .database.spec_corrections_repo import FIELD_LABELS, VALID_CORRECTION_FIELDS

    return [
        {"value": field, "label": FIELD_LABELS.get(field, field)}
        for field in sorted(VALID_CORRECTION_FIELDS)
    ]


@app.post("/api/specs/correct", status_code=201)
def submit_spec_correction(req: SpecCorrectionRequest):
    """
    Submit a user correction for a single spec field on a bike model.

    Stored as ``status='pending'`` — not applied to the catalog until a
    maintainer reviews it.  The ``field_name`` must be in the whitelist
    returned by ``GET /api/specs/correction-fields``.

    Returns ``201 Created`` with ``{id, status, message}`` on success.
    """
    from .database.spec_corrections_repo import (
        SpecCorrectionsRepository,
        VALID_CORRECTION_FIELDS,
    )

    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    # Validate field_name against whitelist
    if req.field_name not in VALID_CORRECTION_FIELDS:
        from .database.spec_corrections_repo import FIELD_LABELS
        raise HTTPException(
            422,
            f"field_name {req.field_name!r} is not correctable. "
            f"Valid fields: {sorted(VALID_CORRECTION_FIELDS)}",
        )

    # Confirm bike exists
    bike_row = db.execute(
        """SELECT bm.id, bm.model_name, m.name AS manufacturer
           FROM bike_models bm
           JOIN manufacturers m ON bm.manufacturer_id = m.id
           WHERE bm.id = ?""",
        (req.bike_id,),
    ).fetchone()
    if not bike_row:
        raise HTTPException(404, f"Bike {req.bike_id} not found")

    # Snapshot current value for the audit trail
    current_value = _fetch_current_value(db, req.bike_id, req.field_name)

    try:
        repo = SpecCorrectionsRepository(db)
        result = repo.create(
            bike_model_id=req.bike_id,
            field_name=req.field_name,
            proposed_value=req.proposed_value,
            current_value=current_value,
            source_url=req.source_url,
            submitter_email=req.submitter_email,
            notes=req.notes,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Failed to store spec correction: %s", exc, exc_info=True
        )
        raise HTTPException(500, f"Database error: {exc}")

    bike_label = f"{dict(bike_row)['manufacturer']} {dict(bike_row)['model_name']}"
    return {
        "id": result["id"],
        "status": "pending",
        "bike": bike_label,
        "field": req.field_name,
        "message": (
            "Thanks! Your correction is queued for review. "
            "If accepted, it will be applied to the catalog in the next release."
        ),
    }


# --- Venue Resolve (auto race-environment setup) -------------------------


class VenueResolveRequest(BaseModel):
    """POST /api/venues/resolve -- resolve a location to a race environment."""

    location: str | None = Field(
        None,
        max_length=200,
        description="City, venue name, or 'City, Country' (e.g. 'Pune, IN')",
    )
    lat: float | None = Field(
        None, ge=-90, le=90, description="Latitude (decimal degrees)"
    )
    lon: float | None = Field(
        None, ge=-180, le=180, description="Longitude (decimal degrees)"
    )
    altitude_m: float | None = Field(
        None,
        ge=-500,
        le=8000,
        description="Elevation above sea level [m]. Overrides OWM's estimate if provided.",
    )

    class Config:
        json_schema_extra = {"example": {"location": "Pune, IN"}}


def _match_seeded_venue(db, location: str) -> dict | None:
    """Return a seeded venue dict if `location` matches name/short_name/city (case-insensitive)."""
    if not location:
        return None
    needle = f"%{location.strip()}%"
    try:
        row = db.execute(
            """SELECT * FROM venues
               WHERE LOWER(name) LIKE LOWER(?)
                  OR LOWER(short_name) LIKE LOWER(?)
                  OR LOWER(city) LIKE LOWER(?)
               ORDER BY
                 CASE
                   WHEN LOWER(short_name) = LOWER(?) THEN 0
                   WHEN LOWER(name) = LOWER(?) THEN 1
                   WHEN LOWER(city) = LOWER(?) THEN 2
                   ELSE 3
                 END
               LIMIT 1""",
            (
                needle,
                needle,
                needle,
                location.strip(),
                location.strip(),
                location.strip(),
            ),
        ).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logging.getLogger(__name__).warning("Venue match query failed: %s", e)
        return None


def _fetch_owm_for_location(
    *,
    location: str | None,
    lat: float | None,
    lon: float | None,
    altitude_m: float | None,
) -> dict | None:
    """
    Fetch current conditions via OpenWeatherMap for either a city name or
    lat/lon. Returns a dict of computed environment params, or None if the
    API key is missing or the upstream request fails.

    Uses the same HTTP path as `motoquant.database.weather_repo` so we stay
    consistent with the offline weather refresh pipeline.
    """
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return {"_error": "no_api_key"}

    try:
        import requests  # type: ignore
    except ImportError:
        return {"_error": "requests_not_installed"}

    params: dict[str, Any] = {
        "appid": api_key,
        "units": "metric",
    }
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    elif location:
        params["q"] = location
    else:
        return {"_error": "missing_location"}

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "OWM fetch failed for location=%r lat=%s lon=%s: %s",
            location,
            lat,
            lon,
            exc,
        )
        return {"_error": f"owm_error: {exc}"}

    # Parse response -- OWM returns Celsius + hPa + m/s when units=metric
    main = data.get("main", {}) or {}
    wind = data.get("wind", {}) or {}
    coord = data.get("coord", {}) or {}

    temp_c = float(main.get("temp", 25.0))
    humidity = float(main.get("humidity", 50.0))
    pressure_hpa = float(main.get("pressure", 1013.25))
    wind_ms = float(wind.get("speed", 0.0))
    wind_deg = float(wind.get("deg", 0.0))

    resolved_lat = float(coord.get("lat", lat)) if coord.get("lat") is not None else lat
    resolved_lon = float(coord.get("lon", lon)) if coord.get("lon") is not None else lon

    # Use caller-provided altitude if given, else assume sea-level (OWM free tier
    # doesn't return elevation; users should pass it if their venue is high-altitude).
    alt = float(altitude_m) if altitude_m is not None else 0.0

    # Reuse the atmospheric helpers from weather_repo to keep logic in one place
    from .database.weather_repo import (
        compute_air_density,
        compute_density_altitude,
        compute_power_correction,
    )

    air_density = compute_air_density(temp_c, humidity, pressure_hpa, alt)
    da_ft = compute_density_altitude(temp_c, humidity, pressure_hpa, alt)
    pcf = compute_power_correction(temp_c, pressure_hpa, humidity, alt)

    return {
        "location_name": data.get("name") or location or "Unknown",
        "country": (data.get("sys") or {}).get("country"),
        "latitude": resolved_lat,
        "longitude": resolved_lon,
        "altitude_m": alt,
        "temperature_c": round(temp_c, 2),
        "humidity_pct": round(humidity, 1),
        "pressure_hpa": round(pressure_hpa, 2),
        "pressure_kpa": round(pressure_hpa / 10.0, 3),
        "wind_speed_ms": round(wind_ms, 2),
        "wind_direction_deg": round(wind_deg, 1),
        "air_density_kgm3": round(float(air_density), 4),
        "density_altitude_ft": round(float(da_ft), 0),
        "density_altitude_m": round(float(da_ft) * 0.3048, 0),
        "power_correction_factor": round(float(pcf), 4),
    }


@app.post("/api/venues/resolve")
def resolve_venue(req: VenueResolveRequest):
    """
    Resolve a race location into ready-to-simulate environment parameters.

    Resolution order:
      1. If `location` matches a seeded venue (by name, short_name, or city),
         return the seeded venue's environment data plus the most recent
         weather record if available.
      2. Otherwise, fall back to OpenWeatherMap for live conditions
         (requires `OPENWEATHERMAP_API_KEY` env var). Computes air density,
         density altitude, and SAE power correction locally.

    The response shape is identical for both paths so the frontend can always
    read `temperature_c`, `humidity_pct`, etc., without branching.
    """
    if not (req.location or (req.lat is not None and req.lon is not None)):
        raise HTTPException(
            422,
            "Provide either `location` (city/venue name) or both `lat` and `lon`.",
        )

    log = logging.getLogger(__name__)
    db = _get_db()

    # ─── Path 1: seeded venue match ──────────────────────────────────────
    if db and req.location:
        venue = _match_seeded_venue(db, req.location)
        if venue:
            alt = float(venue.get("altitude_m") or 0.0)

            # Try to attach the most recent weather record for richer data
            latest = None
            try:
                wr = db.execute(
                    """SELECT * FROM weather_records
                       WHERE venue_id = ?
                       ORDER BY recorded_at DESC LIMIT 1""",
                    (venue["id"],),
                ).fetchone()
                latest = dict(wr) if wr else None
            except Exception as exc:
                log.warning("weather lookup for venue %s failed: %s", venue["id"], exc)

            if latest:
                temp_c = float(latest.get("ambient_temp_c") or 25.0)
                humidity = float(latest.get("relative_humidity_pct") or 50.0)
                pressure = float(latest.get("barometric_pressure_hpa") or 1013.25)
                air_density = float(latest.get("air_density_kgm3") or 0.0)
                da_ft = float(latest.get("density_altitude_ft") or 0.0)
                pcf = float(latest.get("power_correction_factor") or 1.0)
                fetched_at = latest.get("recorded_at")
                weather_source = latest.get("source") or "seeded_weather"
            else:
                # No weather record -- compute ISA-standard defaults at this altitude
                temp_c, humidity, pressure = 25.0, 50.0, 1013.25
                from .database.weather_repo import (
                    compute_air_density,
                    compute_density_altitude,
                    compute_power_correction,
                )

                air_density = compute_air_density(temp_c, humidity, pressure, alt)
                da_ft = compute_density_altitude(temp_c, humidity, pressure, alt)
                pcf = compute_power_correction(temp_c, pressure, humidity, alt)
                fetched_at = None
                weather_source = "isa_standard"
            # Canonical resolution source -- UI keys off this to label the banner.
            # The underlying weather provenance is preserved separately in `weather_source`.
            source = "seeded_venue"

            return {
                "matched_venue_id": venue["id"],
                "venue_name": venue.get("name"),
                "location_name": venue.get("name"),
                "city": venue.get("city"),
                "country": venue.get("country"),
                "latitude": venue.get("latitude"),
                "longitude": venue.get("longitude"),
                "altitude_m": alt,
                "temperature_c": round(temp_c, 2),
                "humidity_pct": round(humidity, 1),
                "pressure_hpa": round(pressure, 2),
                "pressure_kpa": round(pressure / 10.0, 3),
                "air_density_kgm3": round(air_density, 4),
                "density_altitude_ft": round(da_ft, 0),
                "density_altitude_m": round(da_ft * 0.3048, 0),
                "power_correction_factor": round(pcf, 4),
                "fetched_at": fetched_at,
                "source": source,
                "weather_source": weather_source,
            }

    # ─── Path 2: live OWM fetch ──────────────────────────────────────────
    owm = _fetch_owm_for_location(
        location=req.location,
        lat=req.lat,
        lon=req.lon,
        altitude_m=req.altitude_m,
    )
    if owm is None or owm.get("_error"):
        err = (owm or {}).get("_error", "unknown")
        if err == "no_api_key":
            raise HTTPException(
                503,
                "Live weather unavailable: OPENWEATHERMAP_API_KEY is not configured on the server.",
            )
        if err == "requests_not_installed":
            raise HTTPException(
                503, "Live weather unavailable: `requests` package missing."
            )
        if err.startswith("owm_error"):
            raise HTTPException(502, f"OpenWeatherMap upstream error: {err[11:]}")
        raise HTTPException(422, f"Could not resolve location: {err}")

    return {
        "matched_venue_id": None,
        "venue_name": None,
        "location_name": owm["location_name"],
        "city": owm["location_name"],
        "country": owm.get("country"),
        "latitude": owm["latitude"],
        "longitude": owm["longitude"],
        "altitude_m": owm["altitude_m"],
        "temperature_c": owm["temperature_c"],
        "humidity_pct": owm["humidity_pct"],
        "pressure_hpa": owm["pressure_hpa"],
        "pressure_kpa": owm["pressure_kpa"],
        "wind_speed_ms": owm["wind_speed_ms"],
        "wind_direction_deg": owm["wind_direction_deg"],
        "air_density_kgm3": owm["air_density_kgm3"],
        "density_altitude_ft": owm["density_altitude_ft"],
        "density_altitude_m": owm["density_altitude_m"],
        "power_correction_factor": owm["power_correction_factor"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "openweathermap",
    }


# ═══════════════════════════════════════════════════════════════════════════
# SURROGATE MODEL INFERENCE  (/api/surrogate/*)
# Loaded once at startup into app.state.  Falls back DNN -> XGBoost.
# ═══════════════════════════════════════════════════════════════════════════

import os as _os
import time as _time
from pathlib import Path as _Path

_SURROGATE = None          # DNNSurrogate | XGBSurrogate | None — set at startup
_SURROGATE_SOURCE = "none" # "dnn" | "xgb" | "none"
_SURROGATE_LOCK = __import__("threading").Lock()


def _load_surrogate():
    """Try DNN first, fall back to XGBoost. Returns (model, label)."""
    repo_root = _Path(__file__).parent.parent
    dnn_path = repo_root / "surrogate_dnn.pkl"
    xgb_path = repo_root / "surrogate.pkl"
    _log = logging.getLogger(__name__)

    try:
        from motoquant.analysis.surrogate_dnn import DNNSurrogate
        if dnn_path.exists():
            m = DNNSurrogate.load(dnn_path)
            _log.info("Surrogate: loaded DNN from %s", dnn_path)
            return m, "dnn"
    except Exception as exc:
        _log.warning("Surrogate DNN load failed: %s", exc)

    try:
        from motoquant.analysis.surrogate_xgb import XGBSurrogate
        if xgb_path.exists():
            m = XGBSurrogate.load(xgb_path)
            _log.info("Surrogate: loaded XGBoost from %s", xgb_path)
            return m, "xgb"
    except Exception as exc:
        _log.warning("Surrogate XGB load failed: %s", exc)

    _log.warning("Surrogate: no model available (place surrogate_dnn.pkl at repo root)")
    return None, "none"


@app.on_event("startup")
async def _startup_load_surrogate():
    global _SURROGATE, _SURROGATE_SOURCE
    with _SURROGATE_LOCK:
        _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()


# ─── Request / Response models ────────────────────────────────────────────


class SurrogatePredictRequest(BaseModel):
    bike_id: int = Field(None, description="DB bike_models.id (optional)")
    power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    aero_cd_override: float = Field(None, ge=0.30, le=1.20)
    tire_mu_override: float = Field(None, ge=0.50, le=1.80)
    altitude_m: float = Field(0.0, ge=0.0, le=5000.0)
    rider_weight_kg: float = Field(75.0, ge=40.0, le=150.0)

    model_config = {"populate_by_name": True}


class SurrogatePredictResponse(BaseModel):
    et_s: float
    trap_kmh: float
    inference_ms: float
    source: str
    within_training_envelope: bool
    envelope_violations: list


class SurrogateCompareRequest(BaseModel):
    config_a: SurrogatePredictRequest
    config_b: SurrogatePredictRequest


class SurrogateCompareResponse(BaseModel):
    a: SurrogatePredictResponse
    b: SurrogatePredictResponse
    delta_et_s: float
    delta_trap_kmh: float
    faster: str


# ─── Helpers ─────────────────────────────────────────────────────────────


def _check_envelope(fvec):
    """Check each BASE feature against FEATURE_BOUNDS. Returns (ok, violations)."""
    try:
        from motoquant.analysis.surrogate_data import FEATURE_NAMES, FEATURE_BOUNDS
        violations = []
        for i, name in enumerate(FEATURE_NAMES):
            if name not in FEATURE_BOUNDS:
                continue
            lo, hi = FEATURE_BOUNDS[name]
            if float(fvec[i]) < lo or float(fvec[i]) > hi:
                violations.append(name)
        return len(violations) == 0, violations
    except Exception:
        return True, []


def _config_from_surrogate_request(req):
    """
    Build a BikeConfig from a SurrogatePredictRequest.
    Delegates to _build_config() so DB lookup / preset fallback / override
    scaling stay consistent with all other simulate endpoints.
    Additional overrides (aero, tire) applied afterward.
    """
    config = _build_config(
        bike_id=req.bike_id,
        bike_preset=None,
        power_boost_pct=req.power_boost_pct,
        mass_delta_kg=req.mass_delta_kg,
        rider_mass_kg=req.rider_weight_kg,
    )
    if req.aero_cd_override is not None:
        config.aero.cd = req.aero_cd_override
    if req.tire_mu_override is not None:
        config.tires.mu_peak = req.tire_mu_override
    return config


# ─── Routes ──────────────────────────────────────────────────────────────


@app.post("/api/surrogate/predict", response_model=SurrogatePredictResponse)
def surrogate_predict(
    req: SurrogatePredictRequest,
    _auth: dict = Depends(require_tier("pro")),  # noqa: B008
):
    """
    Fast surrogate-model inference — target p95 < 5 ms.

    Applies power/mass/aero/tire overrides then calls the loaded DNN or
    XGBoost model.  ``within_training_envelope`` is False when any feature
    exceeds the Sobol training bounds, signalling the prediction may be
    unreliable.
    """
    global _SURROGATE, _SURROGATE_SOURCE
    if _SURROGATE is None:
        with _SURROGATE_LOCK:
            if _SURROGATE is None:
                _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()
    if _SURROGATE is None:
        raise HTTPException(
            503,
            "Surrogate model not available — train and place surrogate_dnn.pkl at repo root",
        )

    try:
        config = _config_from_surrogate_request(req)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    try:
        from motoquant.analysis.surrogate_data import config_to_feature_vector
        fvec = config_to_feature_vector(config)
        within_env, violations = _check_envelope(fvec)

        t0 = _time.perf_counter()
        et_arr, trap_arr = _SURROGATE.predict(fvec.reshape(1, -1))
        elapsed_ms = (_time.perf_counter() - t0) * 1000.0

        et_val = float(et_arr[0]) if hasattr(et_arr, "__len__") else float(et_arr)
        trap_val = float(trap_arr[0]) if hasattr(trap_arr, "__len__") else float(trap_arr)
        # Both DNN and XGB store trap internally in m/s; convert to km/h
        trap_kmh = trap_val * 3.6 if trap_val < 200.0 else trap_val

    except Exception as exc:
        raise HTTPException(500, f"Surrogate inference error: {exc}") from exc

    return SurrogatePredictResponse(
        et_s=round(et_val, 4),
        trap_kmh=round(trap_kmh, 2),
        inference_ms=round(elapsed_ms, 3),
        source=_SURROGATE_SOURCE,
        within_training_envelope=within_env,
        envelope_violations=violations,
    )


@app.post("/api/surrogate/compare", response_model=SurrogateCompareResponse)
def surrogate_compare(
    req: SurrogateCompareRequest,
    _auth: dict = Depends(require_tier("pro")),  # noqa: B008
):
    """
    Compare two configs via the surrogate — ideal for BuildPage part-swap sweeps.
    Returns per-config predictions and a delta summary.
    """
    resp_a = surrogate_predict(req.config_a)
    resp_b = surrogate_predict(req.config_b)

    delta_et = round(resp_b.et_s - resp_a.et_s, 4)
    delta_trap = round(resp_b.trap_kmh - resp_a.trap_kmh, 2)
    if abs(delta_et) < 0.001:
        faster = "tie"
    elif delta_et < 0:
        faster = "b"
    else:
        faster = "a"

    return SurrogateCompareResponse(
        a=resp_a,
        b=resp_b,
        delta_et_s=delta_et,
        delta_trap_kmh=delta_trap,
        faster=faster,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LIVE PRICING  (/api/pricing/*)
# ═══════════════════════════════════════════════════════════════════════════


class PricingEntryOut(BaseModel):
    retailer: str
    price_inr: float = Field(None)
    in_stock: bool
    fetched_at: str
    source_url: str
    is_stale: bool


class PartPricingOut(BaseModel):
    part_id: int
    part_name: str
    seed_price_inr: float = Field(None)
    cheapest_live_inr: float = Field(None)
    prices: list
    all_stale: bool


class BikePricingSummaryItem(BaseModel):
    part_id: int
    part_name: str
    category: str
    seed_price_inr: float = Field(None)
    cheapest_live_inr: float = Field(None)
    cheapest_retailer: str = Field(None)
    in_stock: bool = Field(None)


class BikePricingSummaryOut(BaseModel):
    bike_id: int
    bike_name: str
    items: list
    total_cheapest_inr: float


class PricingRefreshOut(BaseModel):
    part_id: int
    retailer: str = Field(None)
    price_inr: float = Field(None)
    in_stock: bool = Field(None)
    fetched_at: str = Field(None)
    status: str


@app.get("/api/pricing/part/{part_id}", response_model=PartPricingOut)
def pricing_for_part(part_id: int):
    """
    Return the 3 cheapest live prices for *part_id* from the part_prices table.
    Flags stale rows (>14 days).  Falls back gracefully when no live prices exist.
    """
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database unavailable")

    part_row = db.execute(
        "SELECT id, brand, model_name, price_inr FROM parts WHERE id = ?",
        (part_id,),
    ).fetchone()
    if part_row is None:
        raise HTTPException(404, f"Part {part_id} not found")

    from motoquant.database.pricing_refresh import get_cheapest_prices
    prices = get_cheapest_prices(db, part_id, limit=3)

    cheapest_live = prices[0]["price_inr"] if prices and prices[0]["price_inr"] else None
    all_stale = bool(prices) and all(p["is_stale"] for p in prices)

    return PartPricingOut(
        part_id=part_id,
        part_name="{} {}".format(part_row["brand"] or "", part_row["model_name"] or "").strip(),
        seed_price_inr=part_row["price_inr"],
        cheapest_live_inr=cheapest_live,
        prices=prices,
        all_stale=all_stale,
    )


@app.get("/api/pricing/bike/{bike_id}", response_model=BikePricingSummaryOut)
def pricing_for_bike(bike_id: int, limit: int = Query(50, ge=1, le=500)):
    """
    Pricing summary for all parts in the catalog, showing the cheapest live
    retailer per part.  ``total_cheapest_inr`` sums the cheapest price per part
    (useful for estimating a full-build landed cost).
    """
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database unavailable")

    bike_row = db.execute(
        "SELECT id, model_name FROM bike_models WHERE id = ?", (bike_id,)
    ).fetchone()
    if bike_row is None:
        raise HTTPException(404, f"Bike {bike_id} not found")

    part_rows = db.execute(
        """
        SELECT p.id, p.brand, p.model_name, p.price_inr,
               pc.name AS category
          FROM parts p
          JOIN parts_categories pc ON pc.id = p.category_id
         LIMIT ?
        """,
        (limit,),
    ).fetchall()

    from motoquant.database.pricing_refresh import get_cheapest_prices

    items = []
    total = 0.0

    for pr in part_rows:
        prices = get_cheapest_prices(db, pr["id"], limit=1)
        cheapest = prices[0] if prices else None
        cheapest_inr = cheapest["price_inr"] if cheapest and cheapest["price_inr"] else None
        if cheapest_inr:
            total += cheapest_inr
        elif pr["price_inr"]:
            total += pr["price_inr"]

        items.append({
            "part_id": pr["id"],
            "part_name": "{} {}".format(pr["brand"] or "", pr["model_name"] or "").strip(),
            "category": pr["category"] or "",
            "seed_price_inr": pr["price_inr"],
            "cheapest_live_inr": cheapest_inr,
            "cheapest_retailer": cheapest["retailer"] if cheapest else None,
            "in_stock": cheapest["in_stock"] if cheapest else None,
        })

    return BikePricingSummaryOut(
        bike_id=bike_id,
        bike_name=bike_row["model_name"],
        items=items,
        total_cheapest_inr=round(total, 2),
    )


@app.post("/api/pricing/refresh/{part_id}", response_model=PricingRefreshOut)
def refresh_part_price(part_id: int, force: bool = Query(False)):
    """
    Trigger a live price refresh for a single part.

    Uses the part's ``retailer_url`` field to hit the live retailer page.
    Set ``force=true`` to bypass the 14-day freshness check.

    NOTE: This endpoint is intentionally open for now.  Stream 5 (auth)
    will wrap it with admin-role gating via ``app.include_router(auth_router)``.
    """
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database unavailable")

    part_row = db.execute(
        "SELECT id, brand, model_name, retailer, retailer_url FROM parts WHERE id = ?",
        (part_id,),
    ).fetchone()
    if part_row is None:
        raise HTTPException(404, f"Part {part_id} not found")

    if not part_row["retailer_url"]:
        return PricingRefreshOut(
            part_id=part_id,
            retailer=part_row["retailer"],
            price_inr=None,
            in_stock=None,
            fetched_at=None,
            status="no_url",
        )

    from motoquant.database.pricing_refresh import fetch_live_price
    result = fetch_live_price(db, part_id, force=force)

    if result is None:
        return PricingRefreshOut(
            part_id=part_id,
            retailer=part_row["retailer"],
            price_inr=None,
            in_stock=None,
            fetched_at=None,
            status="fetch_failed",
        )

    return PricingRefreshOut(
        part_id=part_id,
        retailer=result.retailer,
        price_inr=result.price_inr,
        in_stock=result.in_stock,
        fetched_at=result.fetched_at.isoformat(),
        status="refreshed",
    )


# ─────────────────────────────────────────────────────────────────
# Phase A: Claude-powered chat endpoint
# ─────────────────────────────────────────────────────────────────


_db_facade = None  # MotoQuantDB instance (provides .bikes, .venues, etc.)


def _get_db_facade():
    """Return the MotoQuantDB facade (with repos), reconnecting if needed.

    Distinct from `_get_db()` which returns a raw sqlite3.Connection.
    The chat runner uses the facade so it can call db.bikes.search(),
    db.venues.to_environment(), etc.
    """
    global _db_facade
    if _db_facade is not None:
        try:
            _db_facade.conn.execute("SELECT 1")
            return _db_facade
        except Exception:
            _db_facade = None  # stale, rebuild

    try:
        from .database.connection import MotoQuantDB

        db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
        _db_facade = MotoQuantDB(db_path)
        return _db_facade
    except Exception as e:
        logging.getLogger(__name__).error(
            "Failed to initialize MotoQuantDB at %s: %s",
            os.environ.get("MOTOQUANT_DB", "motoquant.db"),
            e,
            exc_info=True,
        )
        return None


def get_llm_client():
    """FastAPI dependency. Tests override via app.dependency_overrides."""
    from .llm import get_default_client

    return get_default_client()


class ChatRequest(BaseModel):
    """POST /api/chat -- ask MotoQuant a question in natural language."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description=(
            "Natural-language tuning query. "
            "Example: 'How fast is my K5 in 35C heat at Aamby Valley?'"
        ),
    )
    run_summary: bool = Field(
        True,
        description=(
            "If True, Claude writes a 2-4 sentence prose summary. "
            "Set False to skip the second LLM call (saves tokens / latency)."
        ),
    )


class ChatBikeSuggestion(BaseModel):
    id: int | None = None
    manufacturer: str | None = None
    model: str | None = None
    year_range: str | None = None


class ChatResponse(BaseModel):
    """Full chat response. error == None means success.

    Frontends should:
      - if error == "bike_not_found": render bike_suggestions as clickable
        chips so the user can pick a bike and re-run.
      - if error == "llm_not_configured": show a banner pointing the
        operator at ANTHROPIC_API_KEY (this is a server-side config issue).
      - if error == "parse_failed" or "sim_failed": show error_detail.
      - if error == None: render sim_result tiles + summary text.
    """

    raw_query: str
    bike_name: str = ""
    bike_id: int | None = None
    venue_name: str | None = None
    venue_id: int | None = None
    parsed_notes: str = ""
    optimization_goal: str = "minimize_et"
    bike_suggestions: list[ChatBikeSuggestion] = Field(default_factory=list)
    sim_result: dict[str, Any] | None = None
    summary: str | None = None
    error: str | None = None
    error_detail: str | None = None


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, client=Depends(get_llm_client)) -> ChatResponse:
    """End-to-end NL chat: parse with Claude, run physics, summarize.

    Always returns 200 with `error` populated on failure modes the user
    can recover from (bike not found, LLM not configured). Returns 503
    only if the database itself is unreachable.
    """
    db = _get_db_facade()
    if db is None:
        raise HTTPException(status_code=503, detail="database_unavailable")

    from .llm import run_chat_pipeline

    result = run_chat_pipeline(
        req.query, db, client=client, run_summary=req.run_summary
    )
    return ChatResponse(
        raw_query=result.raw_query,
        bike_name=result.bike_name,
        bike_id=result.bike_id,
        venue_name=result.venue_name,
        venue_id=result.venue_id,
        parsed_notes=result.parsed_notes,
        optimization_goal=result.optimization_goal,
        bike_suggestions=[
            ChatBikeSuggestion(**s) for s in result.bike_suggestions
        ],
        sim_result=result.sim_result,
        summary=result.summary,
        error=result.error,
        error_detail=result.error_detail,
    )


# ------- END ws/backend-surrogate-pricing additions ----------------------
# Lines below here are reserved for Stream 5 auth router mounts:
#   from motoquant.auth import router as auth_router
#   app.include_router(auth_router)
