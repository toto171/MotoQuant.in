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
    Set PORT env var; Render builds via render.yaml (Docker).
"""

import asyncio
import copy
import json
import logging
import os
import sqlite3
import tempfile
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# TypedDict must come from typing_extensions on Python < 3.12 when used in
# Pydantic/FastAPI annotations (pydantic raises PydanticUserError otherwise).
# python:3.11-slim in prod hit exactly that and crash-looped — 2026-06-06.
from typing_extensions import TypedDict

from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .physics import MotoQuantEngine
from .ratelimit import rate_limit

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


class AppliedPartDict(TypedDict, total=False):
    """Shape of one entry in ``QuickSimResultDict.parts_applied``.

    Mirrors the ``AppliedPart`` TypeScript interface in
    ``desktop/src/types/api.ts``. Built inside :func:`_apply_parts_to_config`.

    ``total=False`` because ``price_inr`` is omitted when the caller passes
    ``include_price_in_summary=False`` (currently only ``_run_build``). The
    other three keys are always populated.
    """

    id: int
    name: str
    brand: str
    price_inr: float | None


class QuickSimResultDict(TypedDict):
    """Shape of the dict returned by the ``/api/simulate/quick`` endpoint.

    Mirrors the ``QuickSimResponse`` TypeScript interface in
    ``desktop/src/types/api.ts``. Built inline in :func:`simulate_quick`.

    Keep field names + types in lockstep with
    ``desktop/src/types/api.ts::QuickSimResponse`` — any drift between the
    two silently breaks the desktop BuildPage slider UI.

    ``stock_et_s`` and ``et_delta_s`` are nullable because they are only
    populated when ``parts_applied`` is non-empty (otherwise "stock" equals
    the current run and the delta is meaningless).
    """

    et_quarter_s: float
    trap_speed_kmh: float
    et_60ft_s: float
    et_eighth_s: float
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float
    parts_applied: list[AppliedPartDict]
    build_cost_inr: float
    stock_et_s: float | None
    et_delta_s: float | None


class LsrSplitDict(TypedDict):
    """One LSR split entry inside a :class:`TopSpeedResultDict`.

    Built inline in :func:`simulate_top_speed`. Keys are emitted at three
    units (m/s + km/h + mph) so the web simulator can display whichever
    unit the user prefers without round-tripping the conversion.
    """

    time_s: float
    speed_ms: float
    speed_kmh: float
    speed_mph: float


class TopSpeedTimeseriesDict(TypedDict):
    """Downsampled timeseries payload for ``/api/simulate/top-speed``.

    Only populated when the request sets ``include_timeseries=True``.
    Stride is chosen in :func:`simulate_top_speed` so the payload is
    ~100 Hz regardless of the underlying solver ``dt``.
    """

    t: list[float]
    v_ms: list[float]
    v_kmh: list[float]
    rpm: list[float]
    gear: list[int]
    power_kw: list[float]
    x_m: list[float]


class TopSpeedResultDict(TypedDict, total=False):
    """Shape of the dict returned by ``/api/simulate/top-speed``.

    Built inline in :func:`simulate_top_speed`. ``timeseries`` is the only
    optional key (hence ``total=False``); it appears iff the request sets
    ``include_timeseries=True``. All other keys are always populated.
    """

    terminal_velocity_ms: float
    terminal_velocity_kmh: float
    terminal_velocity_mph: float
    time_to_terminal_s: float
    distance_to_terminal_m: float
    terminal_power_kw: float
    terminal_power_hp: float
    terminal_gear: int
    terminal_rpm: float
    reached_plateau: bool
    lsr_splits: dict[str, LsrSplitDict]
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float
    parts_applied: list[AppliedPartDict]
    build_cost_inr: float
    timeseries: TopSpeedTimeseriesDict


class DistanceResultDict(TypedDict):
    """Shape of the dict returned by ``/api/simulate/distance``.

    Built inline in :func:`simulate_distance`. All keys are always
    populated — there is no optional ``timeseries`` branch because the
    distance endpoint only surfaces the trap values at the target.
    """

    distance_m: float
    time_s: float
    trap_speed_ms: float
    trap_speed_kmh: float
    trap_speed_mph: float
    peak_velocity_kmh: float
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float


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
                    try:
                        cfg = db_row_to_config(dict(cfg_row), name=bike_name)
                    except Exception as exc:
                        # A config row EXISTS but failed to parse (corrupted
                        # JSON blob, interrupted reseed). That is a data-
                        # integrity failure, not "bike not found" — surface
                        # it as a 500 so it gets noticed, instead of the
                        # misleading 404 this used to produce.
                        logging.getLogger(__name__).error(
                            "Corrupt bike_configs row for bike_id=%s: %s",
                            bike_id,
                            exc,
                            exc_info=True,
                        )
                        raise HTTPException(
                            500,
                            f"Config data for bike {bike_id} failed to load "
                            "— data integrity issue, not a bad bike id",
                        )
            except HTTPException:
                raise
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "Failed to load config for bike_id=%s: %s", bike_id, exc
                )

    if bike_id is not None and cfg is None:
        # Previously this fell through to the K5 default silently -- a typo'd
        # bike_id returned GSX-R 1000 results with no error (June 11 QA bug #1).
        raise HTTPException(404, f"Bike {bike_id} not found")

    if cfg is None and bike_preset:
        presets = {
            "gsxr1000_k5": gsxr1000_k5,
            "yzfr1_4c8": yzfr1_4c8,
            "hayabusa_gen1": hayabusa_gen1,
        }
        fn = presets.get(bike_preset)
        if fn:
            cfg = fn()
        else:
            # Same bug class as the bike_id fallthrough above: a typo'd
            # preset silently returned K5 results with no error.
            raise HTTPException(404, f"Unknown bike_preset: {bike_preset}")

    if cfg is None:
        cfg = gsxr1000_k5()  # default fallback (no bike specified at all)

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
                    # Route the venue's surface type into track_surface — the
                    # real field EnvironmentalModel reads. (The old code wrote a
                    # phantom `surface_grip_multiplier` attribute that nothing
                    # consumed, so venue surface had zero effect on the sim.)
                    cfg.environment.track_surface = (
                        d.get("surface_type") or "asphalt"
                    ).lower()
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
    # TireParams carries ONE scalar mu_peak, and drive traction is rear-tire
    # physics — so ONLY the rear tire may set grip. Previously the loop ran
    # (front, rear) and both wrote the same field: a front-only selection
    # silently replaced rear grip with the front tire's compound.
    for tire_id in (rear_tire_id,):
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


def _apply_parts_to_config(
    cfg: BikeConfig,
    part_ids: list[int] | None,
    *,
    include_price_in_summary: bool = True,
) -> tuple[BikeConfig, list[AppliedPartDict], float]:
    """Apply a list of selected ``part_ids`` to *cfg* and report what was used.

    Centralises the "load each part from the DB, mutate cfg via
    ``apply_part_to_config``, build a parts_applied summary, accumulate
    INR build cost" loop that was previously duplicated across four API
    endpoints (simulate_quick, simulate_top_speed, simulate_distance,
    _run_build).  Behaviour byte-identical to the prior inline blocks:

    * If ``part_ids`` is empty / None, returns ``(cfg, [], 0.0)`` unchanged.
    * If the DB is unavailable, swallows the failure and returns
      ``(cfg, [], 0.0)`` so callers can degrade gracefully — matching the
      prior "if db:" guarded paths.
    * If any single part row raises while being applied, the whole batch
      is logged and dropped (mirrors the prior outer ``try/except``).
    * The ``parts_applied`` dict shape is ``{id, name, brand[, price_inr]}``
      — the optional ``price_inr`` key is omitted when
      ``include_price_in_summary=False`` (used by ``_run_build`` whose
      legacy summary did not include it).

    Returns
    -------
    tuple[BikeConfig, list[dict], float]
        Mutated config (same object), list of per-part summary dicts,
        and the accumulated build cost in INR (0.0 when no priced parts
        were applied or the DB was unavailable).
    """
    parts_applied: list[AppliedPartDict] = []
    build_cost: float = 0.0
    if not part_ids:
        return cfg, parts_applied, build_cost

    db = _get_db()
    if not db:
        return cfg, parts_applied, build_cost

    try:
        from .database.bridge import apply_part_to_config

        for pid in part_ids:
            row = db.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
            if not row:
                continue
            part_dict = dict(row)
            cfg = apply_part_to_config(cfg, part_dict)
            summary: AppliedPartDict = {
                "id": part_dict["id"],
                "name": part_dict.get("model_name", ""),
                "brand": part_dict.get("brand", ""),
            }
            if include_price_in_summary:
                summary["price_inr"] = part_dict.get("price_inr")
            parts_applied.append(summary)
            if part_dict.get("price_inr"):
                build_cost += float(part_dict["price_inr"])
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Failed to apply parts %s: %s", part_ids, exc
        )
        # Preserve prior behaviour: return whatever was assembled before the
        # exception (parts_applied may be partially populated if the failure
        # came from a late row); cfg likewise carries any deltas already
        # applied. This matches the inline try/except behaviour we replaced.

    return cfg, parts_applied, build_cost


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
            # Health endpoint reports the failure as database=unavailable
            # below instead of raising.
            pass
    return {
        "status": "ok",
        "database": "connected" if db_ok else "unavailable",
        "bike_count": bike_count,
    }


# ─────────────────────────────────────────────────────────────────────────
# Free-tier sim metering (commercial launch, July 2026)
# ─────────────────────────────────────────────────────────────────────────
# FULL simulations (sync + job-backed, top-speed, distance) are metered per
# identity per UTC day via motoquant/usage.py. Quick sims stay unmetered --
# the web UI fires them on every slider move, so a daily cap there would
# break the live-preview UX; the full run with charts is the free-tier
# quota unit. During the open beta (MOTOQUANT_BILLING_ENFORCE falsy) the
# quota is advisory: counts are recorded, X-Sims-Remaining is exposed, but
# nothing is blocked. Flipping the env var arms the 402.


def _sim_identity_and_tier(request: Request) -> tuple[str, str]:
    """Resolve the metering identity: user id when a valid bearer token is
    present, else a hashed client IP (never stored raw -- privacy page)."""
    authz = request.headers.get("authorization", "")
    if authz.lower().startswith("bearer "):
        try:
            from . import auth as _auth
            from .usage import user_identity

            payload = _auth._decode_token(authz.split(" ", 1)[1])
            if payload and payload.get("type") == "access":
                conn = _auth._get_conn()
                try:
                    user = _auth._users.get_user_by_id(conn, int(payload["sub"]))
                finally:
                    conn.close()
                if user:
                    return user_identity(user["id"]), user.get("tier", "free")
        except Exception:  # noqa: BLE001 -- metering must never break sims
            pass
    from .usage import anon_identity

    fwd = request.headers.get("x-forwarded-for")
    ip = (
        fwd.split(",")[0].strip()
        if fwd
        else (request.client.host if request.client else "unknown")
    )
    return anon_identity(ip), "free"


def _meter_full_sim(request: Request, response: Response) -> None:
    """FastAPI dependency: count this full sim and (when billing is
    enforced) 402 free-tier callers past the daily quota."""
    try:
        from .database.connection import connect as _db_connect
        from .usage import record_and_check

        identity, tier = _sim_identity_and_tier(request)
        conn = _db_connect()
        try:
            st = record_and_check(conn, identity, tier=tier)
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 -- metering must never break sims
        logging.getLogger(__name__).warning("sim metering failed", exc_info=True)
        return
    if st.limit is not None:
        response.headers["X-Sims-Limit"] = str(st.limit)
        response.headers["X-Sims-Remaining"] = str(st.remaining)
    if not st.allowed:
        try:
            from . import auth as _auth
        except Exception:  # noqa: BLE001
            return
        if _auth.BILLING_ENFORCE:
            raise HTTPException(
                402,
                detail={
                    "error": "quota_exceeded",
                    "message": (
                        f"Free tier includes {st.limit} full simulations per "
                        "day. Upgrade to Pro for unlimited runs."
                    ),
                    "upgrade_url": f"{os.environ.get('MOTOQUANT_BASE_URL', 'https://motoquant.in')}/pricing",
                },
            )


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


def _forward_telemetry_posthog(
    event: str,
    session_id: str,
    path: str,
    props: dict,
) -> None:
    """Env-gated server-side forward to PostHog (project "Motoquant", EU).

    No-op unless POSTHOG_API_KEY is set, so behaviour without the key is
    unchanged (stdout log only). Fires on a daemon thread -- the beacon
    route is async and a blocking HTTP call would starve the event loop.
    Server-side capture, no cookies: stays inside the privacy page's
    consent promise.
    """
    api_key = os.environ.get("POSTHOG_API_KEY")
    if not api_key:
        return
    host = os.environ.get("POSTHOG_HOST", "https://eu.i.posthog.com").rstrip("/")

    def _post() -> None:
        try:
            import urllib.request

            payload = json.dumps(
                {
                    "api_key": api_key,
                    "event": event,
                    "distinct_id": session_id or "anonymous",
                    "properties": {**props, "path": path, "source": "api"},
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{host}/i/v0/e/",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:  # noqa: BLE001 -- telemetry must never surface
            pass

    threading.Thread(target=_post, daemon=True).start()


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
    viewport = (
        payload.get("viewport") if isinstance(payload.get("viewport"), dict) else {}
    )
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
        _forward_telemetry_posthog(event, session_id, path, safe_props)
    except Exception:
        # Telemetry is fire-and-forget; a logging failure must never 500
        # the client beacon.
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
        # Mirror ALL row-query filters — total previously ignored
        # manufacturer/category, so filtered pagination reported the full
        # catalog count (e.g. 38 cruisers with total: 501).
        if manufacturer:
            count_query += " AND LOWER(m.name) = LOWER(?)"
            count_params.append(manufacturer)
        if category:
            count_query += " AND LOWER(bm.category) = LOWER(?)"
            count_params.append(category)

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
    limit: int = Query(1000, le=5000),
):
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        count_query = """SELECT COUNT(*)
                   FROM tire_models tm
                   JOIN tire_manufacturers tmfr ON tm.manufacturer_id = tmfr.id
                   WHERE 1=1"""
        query = """SELECT tm.*, tmfr.name AS manufacturer
                   FROM tire_models tm
                   JOIN tire_manufacturers tmfr ON tm.manufacturer_id = tmfr.id
                   WHERE 1=1"""
        params: list[Any] = []
        if compound:
            count_query += " AND LOWER(tm.compound_type) = LOWER(?)"
            query += " AND LOWER(tm.compound_type) = LOWER(?)"
            params.append(compound)
        if manufacturer:
            count_query += " AND LOWER(tmfr.name) LIKE LOWER(?)"
            query += " AND LOWER(tmfr.name) LIKE LOWER(?)"
            params.append(f"%{manufacturer}%")
        total = db.execute(count_query, params).fetchone()[0]
        query += " ORDER BY tmfr.name, tm.model_name LIMIT ?"
        params.append(limit)
        rows = db.execute(query, params).fetchall()
        # Reshape to frontend-friendly format
        tires = []
        for r in rows:
            d = dict(r)
            d["model"] = d.get("model_name", "")
            tires.append(d)
        return {"tires": tires, "total": total}
    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}")


def _simulate_impl(req: SimulateRequest, progress=None):
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
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run(
            use_adaptive_dt=req.use_adaptive_dt,
            progress_cb=(lambda f: progress(f, "Integrating physics"))
            if progress is not None
            else None,
        )
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


@app.post("/api/simulate", dependencies=[Depends(_meter_full_sim)])
def simulate(req: SimulateRequest):
    """Synchronous full simulation (see ``_simulate_impl``)."""
    return _simulate_impl(req)


@app.post("/api/simulate/quick")
def simulate_quick(req: QuickSimRequest) -> QuickSimResultDict:
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
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    # Apply selected parts
    cfg, parts_applied, build_cost_inr = _apply_parts_to_config(cfg, req.part_ids)

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
            # Baseline comparison is optional; stock_et stays None and the
            # response simply omits the stock delta.
            pass

    try:
        engine = MotoQuantEngine(cfg)
        sim = engine.run()
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    result: QuickSimResultDict = {
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
    # LSR-specific: optional override for max time/distance.
    # Bounded: n_max preallocates 17 float64 arrays of max_time_s/dt slots,
    # so an unbounded value is a remotely-triggerable memory bomb.
    max_time_s: float = Field(120.0, gt=0, le=300.0)
    include_timeseries: bool = False


def _topspeed_impl(req: TopSpeedRequest, progress=None) -> TopSpeedResultDict:
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
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    cfg, parts_applied, build_cost_inr = _apply_parts_to_config(cfg, req.part_ids)

    try:
        engine = MotoQuantEngine(cfg)
        ts = engine.run_top_speed(
            max_time=req.max_time_s,
            progress_cb=(lambda f: progress(f, "Running to terminal velocity"))
            if progress is not None
            else None,
        )
    except Exception as exc:
        raise HTTPException(500, f"Top-speed simulation error: {exc}")

    # Format LSR splits with km/h + mph for convenience
    splits_fmt: dict[str, LsrSplitDict] = {}
    for k, v in ts.lsr_splits.items():
        splits_fmt[k] = {
            "time_s": round(v["time_s"], 3),
            "speed_ms": round(v["speed_ms"], 2),
            "speed_kmh": round(v["speed_ms"] * 3.6, 1),
            "speed_mph": round(v["speed_ms"] * 2.23694, 1),
        }

    response: TopSpeedResultDict = {
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
        timeseries: TopSpeedTimeseriesDict = {
            "t": sim.t[::stride].tolist(),
            "v_ms": sim.v[::stride].tolist(),
            "v_kmh": (sim.v[::stride] * 3.6).tolist(),
            "rpm": sim.rpm[::stride].tolist(),
            "gear": sim.gear[::stride].tolist(),
            "power_kw": sim.power_kw[::stride].tolist(),
            "x_m": sim.x[::stride].tolist(),
        }
        response["timeseries"] = timeseries

    return response


@app.post("/api/simulate/top-speed", dependencies=[Depends(_meter_full_sim)])
def simulate_top_speed(req: TopSpeedRequest) -> TopSpeedResultDict:
    """Synchronous top-speed simulation (see ``_topspeed_impl``)."""
    return _topspeed_impl(req)


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
    max_time_s: float = Field(120.0, gt=0, le=300.0)


@app.post("/api/simulate/distance", dependencies=[Depends(_meter_full_sim)])
def simulate_distance(req: DistanceRunRequest) -> DistanceResultDict:
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
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    # Apply parts (distance run doesn't surface parts_applied/cost in its
    # response, but the helper handles that consistently).
    cfg, _, _ = _apply_parts_to_config(cfg, req.part_ids)

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

    result: DistanceResultDict = {
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

    ``total`` in the response is the number of MATCHING parts (after category /
    search / compatibility filtering, before ``limit`` slicing) so paginating
    callers can detect truncation. Cap is 5000 (563-part catalog as of Jun 2026).

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

        query += " ORDER BY pc.display_name, p.brand, p.model_name"
        if bike_id is None:
            # Plain catalog listing: SQL LIMIT is safe, but COUNT first for total.
            count_q = query.replace(
                "SELECT p.*, pc.name as category_name, pc.display_name as category_display",
                "SELECT COUNT(*)",
                1,
            ).split(" ORDER BY")[0]
            sql_total = db.execute(count_q, params).fetchone()[0]
            query += " LIMIT ?"
            params.append(limit)
        else:
            # Compatibility filtering happens in Python below -- applying the SQL
            # LIMIT first silently starved brands late in the sort order
            # (June 11 QA / parts-audit handoff). Fetch all, filter, then slice.
            sql_total = None

        rows = db.execute(query, params).fetchall()

        # ── Bike compatibility annotation / filter ─────────────────────────
        bike_row: dict | None = None
        if bike_id is not None:
            from .database.parts_repo import enrich_bike_row_for_fitment
            from .parts.compatibility import is_compatible  # noqa: F401

            raw = db.execute(
                "SELECT * FROM bike_models WHERE id = ?", (bike_id,)
            ).fetchone()
            if raw is None:
                raise HTTPException(404, f"Bike {bike_id} not found")
            bike_row = dict(raw)
            enrich_bike_row_for_fitment(db, bike_row)

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

        total = sql_total if sql_total is not None else len(parts)
        if bike_id is not None and len(parts) > limit:
            parts = parts[:limit]

        return {
            "parts": parts,
            "total": total,
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
    auth_user: dict = Depends(require_tier("pro")),  # noqa: B008
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

    # Attribute the run to the signed-in user (no-op for anonymous saves).
    if auth_user and auth_user.get("id"):
        try:
            db.execute(
                "UPDATE sim_runs SET user_id = ? WHERE id = ?",
                (auth_user["id"], cur.lastrowid),
            )
            db.commit()
        except sqlite3.Error:
            logging.getLogger(__name__).warning(
                "sim_runs.user_id attribution failed (column missing?)",
                exc_info=True,
            )

    return {
        "run_id": cur.lastrowid,
        "bike_id": req.bike_id,
        "bike_config_id": bike_config_id,
        "saved_to_account": bool(auth_user and auth_user.get("id")),
    }


@app.get("/api/leaderboard")
def leaderboard(
    limit: int = Query(20, le=100),
    venue_id: int | None = Query(None, description="Filter to one venue"),
):
    """Return the top simulation runs saved to the local database,
    optionally filtered to a single venue (per-venue leaderboards)."""
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    try:
        # sim_runs table stores saved runs from the CLI `sim save-run` command
        query = """SELECT sr.id, sr.et_quarter_s, sr.trap_speed_kmh,
                      m.name AS manufacturer, bm.model_name AS model,
                      bm.year_from AS year, v.name AS venue, sr.created_at
               FROM sim_runs sr
               LEFT JOIN bike_configs bc ON sr.bike_config_id = bc.id
               LEFT JOIN bike_models bm ON bc.bike_model_id = bm.id
               LEFT JOIN manufacturers m ON bm.manufacturer_id = m.id
               LEFT JOIN venues v ON sr.venue_id = v.id
               WHERE sr.et_quarter_s IS NOT NULL"""
        params: list[Any] = []
        if venue_id is not None:
            query += " AND sr.venue_id = ?"
            params.append(venue_id)
        query += " ORDER BY sr.et_quarter_s ASC LIMIT ?"
        params.append(limit)
        rows = db.execute(query, params).fetchall()
        return {
            "leaderboard": [dict(r) for r in rows],
            "total": len(rows),
        }
    except sqlite3.OperationalError as exc:
        # sim_runs table may not exist yet on a fresh DB -- return empty,
        # but say so in the logs instead of swallowing silently.
        logging.getLogger(__name__).warning("leaderboard query failed: %s", exc)
        return {"leaderboard": [], "total": 0}


@app.get("/api/runs/{run_id}")
def get_public_run(run_id: int):
    """Public, immutable view of one saved sim run — powers the shareable
    /r/[id] timeslip pages (the WhatsApp/OG share loop). Only exposes the
    run's results + bike/venue names, never the owning account."""
    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")
    try:
        row = db.execute(
            """SELECT sr.id, sr.et_quarter_s, sr.trap_speed_kmh,
                      sr.et_eighth_s, sr.time_60ft_s, sr.time_330ft_s,
                      sr.time_1000ft_s, sr.created_at,
                      m.name AS manufacturer, bm.model_name AS model,
                      bm.year_from AS year, v.name AS venue
               FROM sim_runs sr
               LEFT JOIN bike_configs bc ON sr.bike_config_id = bc.id
               LEFT JOIN bike_models bm ON bc.bike_model_id = bm.id
               LEFT JOIN manufacturers m ON bm.manufacturer_id = m.id
               LEFT JOIN venues v ON sr.venue_id = v.id
               WHERE sr.id = ?""",
            (run_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        logging.getLogger(__name__).warning("run lookup failed: %s", exc)
        row = None
    if not row:
        raise HTTPException(404, "Run not found")
    return dict(row)


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
    progress_cb=None,
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
    cfg, parts_applied, build_cost = _apply_parts_to_config(
        cfg, part_ids, include_price_in_summary=False
    )

    sim = MotoQuantEngine(cfg).run(progress_cb=progress_cb)
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


def _compare_impl(req: CompareRequest, progress=None):
    """Run two builds side-by-side. ``progress(frac, stage)`` maps build A to
    0→0.48 and build B to 0.5→0.98 so the /api/jobs poller shows real
    integration progress across both sims."""

    def _span(lo, hi, stage):
        if progress is None:
            return None
        return lambda f: progress(lo + (hi - lo) * min(1.0, max(0.0, f)), stage)

    try:
        if progress is not None:
            progress(0.01, "Simulating build A")
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
            progress_cb=_span(0.01, 0.48, "Simulating build A"),
        )
        if progress is not None:
            progress(0.5, "Simulating build B")
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
            progress_cb=_span(0.5, 0.98, "Simulating build B"),
        )
    except HTTPException:
        raise  # e.g. 404 for an unknown bike_id — don't relabel as 500
    except Exception as exc:
        raise HTTPException(500, f"Simulation error: {exc}")

    if progress is not None:
        progress(0.99, "Building comparison")
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


@app.post("/api/simulate/compare")
def simulate_compare(req: CompareRequest):
    """Run two builds side-by-side and return full results for both."""
    return _compare_impl(req)


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

        # to_thread: this route is async, so a blocking parse would starve
        # the single event loop (incl. /api/jobs polling) on the 0.5-CPU tier.
        runs = await asyncio.to_thread(parse_dragy_file, tmp_path)
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
            # Full RK4 run takes seconds on prod hardware — keep it off
            # the event loop.
            sim = await asyncio.to_thread(MotoQuantEngine(cfg).run)
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

        dyno_result = await asyncio.to_thread(
            parse_dyno_file,
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

    bike_id: int = Field(..., description="DB bike model ID to correct")
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
    notes: str | None = Field(None, max_length=2000, description="Free-form context")

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
        "peak_power_hp",
        "peak_torque_nm",
        "peak_power_rpm",
        "peak_torque_rpm",
        "displacement_cc",
        "bore_mm",
        "stroke_mm",
        "compression_ratio",
        "dry_mass_kg",
        "wet_mass_kg",
        "cylinder_count",
        "wheelbase_mm",
        "seat_height_mm",
        "fuel_capacity_l",
    }
    # Fields that live inside bike_configs JSON blobs
    _BLOB_FIELD_MAP = {
        "front_sprocket": "drivetrain_params",
        "rear_sprocket": "drivetrain_params",
        "gear_ratios": "drivetrain_params",
        "redline_rpm": "engine_params",
        "cd": "aero_params",
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
        # Probe helper: malformed/missing config blob degrades to None.
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
        VALID_CORRECTION_FIELDS,
        SpecCorrectionsRepository,
    )

    db = _get_db()
    if not db:
        raise HTTPException(503, "Database unavailable")

    # Validate field_name against whitelist
    if req.field_name not in VALID_CORRECTION_FIELDS:
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

import time as _time  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_SURROGATE = None  # DNNSurrogate | XGBSurrogate | None — set at startup
_SURROGATE_SOURCE = "none"  # "dnn" | "xgb" | "none"
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

    try:
        from motoquant.analysis.surrogate_numpy import NumpySurrogate

        npz_path = repo_root / "artifacts" / "surrogate" / "surrogate_numpy.npz"
        if npz_path.exists():
            m = NumpySurrogate.load(npz_path)
            _log.info("Surrogate: loaded numpy MLP from %s", npz_path)
            return m, "numpy"
    except Exception as exc:
        _log.warning("Surrogate numpy load failed: %s", exc)

    _log.warning("Surrogate: no model available (place surrogate_dnn.pkl at repo root)")
    return None, "none"


@app.on_event("startup")
async def _startup_load_surrogate():
    global _SURROGATE, _SURROGATE_SOURCE
    with _SURROGATE_LOCK:
        _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()


# ─── Request / Response models ────────────────────────────────────────────


class SurrogatePredictRequest(BaseModel):
    bike_id: int | None = Field(None, description="DB bike_models.id (optional)")
    power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    aero_cd_override: float | None = Field(None, ge=0.30, le=1.20)
    tire_mu_override: float | None = Field(None, ge=0.50, le=1.80)
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


def _check_envelope(fvec, model=None):
    """Check the feature vector against the model's training envelope.

    v2 numpy artifacts embed per-feature train min/max (covers the full
    501-bike catalog); models without one fall back to the static
    FEATURE_BOUNDS table over the 14 base features. Returns (ok, violations).
    """
    try:
        from motoquant.analysis.surrogate_data import FEATURE_BOUNDS, FEATURE_NAMES

        env = getattr(model, "envelope", None)
        if env is not None:
            env_min, env_max = env
            names = getattr(model, "feature_names", FEATURE_NAMES)
            violations = [
                str(names[i])
                for i in range(min(len(fvec), len(env_min)))
                if not (env_min[i] <= float(fvec[i]) <= env_max[i])
            ]
            return len(violations) == 0, violations

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
        within_env, violations = _check_envelope(fvec, _SURROGATE)
        # Boost state is invisible to the feature vector — flag boosted configs
        # so clients know the surrogate is predicting the NA equivalent.
        if getattr(getattr(config, "forced_induction", None), "is_boosted", False):
            within_env = False
            violations = [*violations, "forced_induction_active"]

        # Feature schemas are append-only (v1 models take the first 21 of the
        # 26 v2 features); trim for models that declare a narrower input.
        n_feat = getattr(_SURROGATE, "n_features", None) or len(
            getattr(_SURROGATE, "feature_names", None) or fvec
        )
        t0 = _time.perf_counter()
        et_arr, trap_arr = _SURROGATE.predict(fvec[:n_feat].reshape(1, -1))
        elapsed_ms = (_time.perf_counter() - t0) * 1000.0

        et_val = float(et_arr[0]) if hasattr(et_arr, "__len__") else float(et_arr)
        trap_val = (
            float(trap_arr[0]) if hasattr(trap_arr, "__len__") else float(trap_arr)
        )
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
    # Mirrors a row from get_cheapest_prices(); price/url/timestamp may be NULL
    # for catalog rows that have no live price yet.
    retailer: str | None = None
    price_inr: float | None = None
    in_stock: bool
    fetched_at: str | None = None
    source_url: str | None = None
    is_stale: bool


class PartPricingOut(BaseModel):
    part_id: int
    part_name: str
    seed_price_inr: float | None = None
    cheapest_live_inr: float | None = None
    prices: list[PricingEntryOut]
    all_stale: bool


class BikePricingSummaryItem(BaseModel):
    part_id: int
    part_name: str
    category: str
    seed_price_inr: float | None = None
    cheapest_live_inr: float | None = None
    cheapest_retailer: str | None = None
    in_stock: bool | None = None


class BikePricingSummaryOut(BaseModel):
    bike_id: int
    bike_name: str
    items: list[BikePricingSummaryItem]
    total_cheapest_inr: float


class PricingRefreshOut(BaseModel):
    part_id: int
    retailer: str | None = None
    price_inr: float | None = None
    in_stock: bool | None = None
    fetched_at: str | None = None
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

    cheapest_live = (
        prices[0]["price_inr"] if prices and prices[0]["price_inr"] else None
    )
    all_stale = bool(prices) and all(p["is_stale"] for p in prices)

    return PartPricingOut(
        part_id=part_id,
        part_name="{} {}".format(
            part_row["brand"] or "", part_row["model_name"] or ""
        ).strip(),
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
        cheapest_inr = (
            cheapest["price_inr"] if cheapest and cheapest["price_inr"] else None
        )
        if cheapest_inr:
            total += cheapest_inr
        elif pr["price_inr"]:
            total += pr["price_inr"]

        items.append(
            {
                "part_id": pr["id"],
                "part_name": "{} {}".format(
                    pr["brand"] or "", pr["model_name"] or ""
                ).strip(),
                "category": pr["category"] or "",
                "seed_price_inr": pr["price_inr"],
                "cheapest_live_inr": cheapest_inr,
                "cheapest_retailer": cheapest["retailer"] if cheapest else None,
                "in_stock": cheapest["in_stock"] if cheapest else None,
            }
        )

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


class ChatMessage(BaseModel):
    """One prior conversation turn (client-held history)."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=8000)


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
    messages: list[ChatMessage] | None = Field(
        None,
        max_length=24,
        description=(
            "Optional prior conversation turns (oldest first) so follow-up "
            "questions keep their context. The server is stateless — the "
            "client holds the transcript."
        ),
    )
    mode: str = Field(
        "agent",
        pattern="^(agent|classic)$",
        description=(
            "'agent' (default) = multi-step tool-calling agent: multi-turn "
            "conversations, real optimizer/autotune access, web lookup, "
            "estimated sims for unknown bikes. 'classic' = the legacy "
            "single-shot parse→dispatch→summarize pipeline."
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
      - if error == "llm_not_configured": show a banner telling the operator
        to set the provider key (GROQ_API_KEY by default — see LLM_PROVIDER).
      - if error == "rate_limited": show a polite retry-in-a-minute note.
      - if error == "parse_failed" / "sim_failed" / "agent_failed": show
        error_detail.
      - if error == None: render summary text; agent mode additionally
        returns ordered `blocks` ([{type, payload}]) — sim_result /
        top_speed / compare_result / build_result / outlaw_result /
        autotune_result / estimated_sim / parts / tires / web_citations —
        for rich per-type tiles. `sim_result` mirrors the LAST sim block
        for backwards compatibility with older clients.
    """

    raw_query: str
    mode: str = "classic"
    intent_type: str | None = None
    bike_name: str = ""
    bike_id: int | None = None
    venue_name: str | None = None
    venue_id: int | None = None
    parsed_notes: str = ""
    optimization_goal: str = "minimize_et"
    bike_suggestions: list[ChatBikeSuggestion] = Field(default_factory=list)
    sim_result: dict[str, Any] | None = None
    # Classic-pipeline intent payloads (previously computed then DROPPED at
    # this boundary — the July 2 audit's "ChatResponse SimDict" item).
    compare_result: dict[str, Any] | None = None
    rank_result: dict[str, Any] | None = None
    recommend_result: dict[str, Any] | None = None
    explain_result: dict[str, Any] | None = None
    choose_bike_result: dict[str, Any] | None = None
    # Agent-mode payloads
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    sims_run: int = 0
    summary: str | None = None
    error: str | None = None
    error_detail: str | None = None


def _make_chat_meter(request: Request):
    """Capture the caller's sim-quota identity at route time; return a
    meter(n)->bool callback the agent's tool executor calls per full sim.

    Returns True when the sim may run. Metering failures never block chat.
    """
    try:
        identity, tier = _sim_identity_and_tier(request)
    except Exception:  # noqa: BLE001
        return None

    def meter(n: int) -> bool:
        try:
            from .database.connection import connect as _db_connect
            from .usage import record_and_check

            conn = _db_connect()
            try:
                st = None
                for _ in range(max(1, int(n))):
                    st = record_and_check(conn, identity, tier=tier)
            finally:
                conn.close()
            if st is not None and not st.allowed:
                from . import auth as _auth

                return not _auth.BILLING_ENFORCE
            return True
        except Exception:  # noqa: BLE001 — metering must never break chat
            logging.getLogger(__name__).warning(
                "chat sim metering failed", exc_info=True
            )
            return True

    return meter


def _get_surrogate_pair():
    """Lazy surrogate accessor shared with the optimizer routes."""
    global _SURROGATE, _SURROGATE_SOURCE
    if _SURROGATE is None:
        with _SURROGATE_LOCK:
            if _SURROGATE is None:
                _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()
    return _SURROGATE, _SURROGATE_SOURCE


def _chat_impl(req: ChatRequest, client, meter_cb, progress=None) -> dict:
    """Run one chat turn (agent or classic). Returns a ChatResponse dict."""
    db = _get_db_facade()
    if db is None:
        raise HTTPException(status_code=503, detail="database_unavailable")

    if req.mode == "classic":
        from .llm import run_chat_pipeline

        result = run_chat_pipeline(
            req.query, db, client=client, run_summary=req.run_summary
        )
        return {
            "raw_query": result.raw_query,
            "mode": "classic",
            "intent_type": result.intent_type,
            "bike_name": result.bike_name,
            "bike_id": result.bike_id,
            "venue_name": result.venue_name,
            "venue_id": result.venue_id,
            "parsed_notes": result.parsed_notes,
            "optimization_goal": result.optimization_goal,
            "bike_suggestions": result.bike_suggestions,
            "sim_result": result.sim_result,
            "compare_result": result.compare_result,
            "rank_result": result.rank_result,
            "recommend_result": result.recommend_result,
            "explain_result": result.explain_result,
            "choose_bike_result": result.choose_bike_result,
            "summary": result.summary,
            "error": result.error,
            "error_detail": result.error_detail,
        }

    from .llm.agent import run_agent_chat

    history = [m.model_dump() for m in (req.messages or [])]
    result = run_agent_chat(
        req.query,
        db,
        client=client,
        history=history,
        progress_cb=progress,
        meter_cb=meter_cb,
        surrogate_getter=_get_surrogate_pair,
    )
    return {
        "raw_query": result.raw_query,
        "mode": "agent",
        "blocks": result.blocks,
        "tool_trace": result.tool_trace,
        "sims_run": result.sims_run,
        # Back-compat: older clients read summary + sim_result only.
        "summary": result.reply,
        "sim_result": result.last_block("sim_result"),
        "error": result.error,
        "error_detail": result.error_detail,
    }


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit("chat", 20, 60.0))],
)
def chat(
    req: ChatRequest, request: Request, client=Depends(get_llm_client)
) -> ChatResponse:
    """End-to-end NL chat (agent mode by default; mode='classic' for the
    legacy pipeline).

    Always returns 200 with `error` populated on failure modes the user
    can recover from (bike not found, LLM not configured, rate limited).
    Returns 503 only if the database itself is unreachable.
    """
    payload = _chat_impl(req, client, _make_chat_meter(request))
    suggestions = payload.pop("bike_suggestions", None) or []
    return ChatResponse(
        **payload,
        bike_suggestions=[ChatBikeSuggestion(**s) for s in suggestions],
    )


@app.post(
    "/api/jobs/chat",
    status_code=202,
    dependencies=[Depends(rate_limit("chat", 20, 60.0))],
)
def job_chat(req: ChatRequest, request: Request, client=Depends(get_llm_client)):
    """Start a chat turn as a background job with live progress + Stop.

    Agent turns can run multiple sims / an optimizer pass, which on the
    0.5-CPU prod tier exceeds comfortable request time — same rationale as
    every other /api/jobs/* route. Poll GET /api/jobs/{id}; result is the
    ChatResponse-shaped dict.
    """
    meter = _make_chat_meter(request)
    return _start_job("chat", lambda progress: _chat_impl(req, client, meter, progress))


# ------- END ws/backend-surrogate-pricing additions ----------------------
# Lines below here are reserved for Stream 5 auth router mounts:
#   from motoquant.auth import router as auth_router
#   app.include_router(auth_router)


# ═══════════════════════════════════════════════════════════════════════════
# BUILD OPTIMIZER + ECU AUTOTUNE  (/api/optimize/*, /api/autotune/*)  — Track B
# Public (no auth): the free demo surface, like /simulate/quick + /venues/resolve.
# The optimizer scores candidates through the loaded surrogate when available and
# in-envelope, else falls back to the full physics sim — so it always answers.
# ═══════════════════════════════════════════════════════════════════════════


class OptimizeBuildRequest(BaseModel):
    """POST /api/optimize/build — best on-budget parts build for a goal."""

    bike_id: int | None = Field(None, description="DB bike_models.id")
    bike_preset: str | None = Field(
        None, description="Fallback preset: gsxr1000_k5 | yzfr1_4c8 | hayabusa_gen1"
    )
    budget_inr: float | None = Field(
        None,
        ge=0,
        le=5_000_000,
        description=(
            "Max spend [INR]. null / omitted / 0 = NO LIMIT (outlaw / open "
            "class semantics — resolved server-side to the ₹5M internal cap, "
            "which exceeds the price of every compatible part combined)"
        ),
    )
    goal: str = Field(
        "min_et", description='"min_et" (faster ET) or "max_trap" (higher trap)'
    )
    profile: str = Field(
        "all", description="all | street_legal | drag_prep | full_race"
    )
    rider_weight_kg: float = Field(75.0, ge=40, le=150)
    power_boost_pct: float = Field(0.0, ge=-50, le=200)
    mass_delta_kg: float = Field(0.0, ge=-100, le=200)
    venue_id: int | None = Field(
        None, description="Optional venue for ambient conditions"
    )
    max_candidates: int | None = Field(
        None,
        ge=1,
        le=200,
        description="Cap candidate pool (latency control for full-sim fallback)",
    )

    model_config = {"populate_by_name": True}


def _optimize_impl(req: OptimizeBuildRequest, progress=None):
    """
    Return the best parts combination for a bike within a budget, optimised for
    ``goal``.  Each part is compatibility-checked; at most one part per exclusive
    category (exhaust/ecu/air_filter/clutch/quickshifter/battery).  Response
    includes per-part ROI, predicted ET/trap delta, cost-per-tenth, synergies,
    warnings, category priority, and the next-best upgrade beyond budget.
    """
    conn = _get_db()
    if conn is None:
        raise HTTPException(503, "Database unavailable")

    try:
        config = _build_config(
            bike_id=req.bike_id,
            bike_preset=req.bike_preset,
            power_boost_pct=req.power_boost_pct,
            mass_delta_kg=req.mass_delta_kg,
            rider_mass_kg=req.rider_weight_kg,
            venue_id=req.venue_id,
        )
    except Exception as exc:
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    # Lazy-load the surrogate (same pattern as /api/surrogate/predict).
    global _SURROGATE, _SURROGATE_SOURCE
    if _SURROGATE is None:
        with _SURROGATE_LOCK:
            if _SURROGATE is None:
                _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()

    from .analysis.build_optimizer import optimize_build
    from .database.parts_repo import PartsRepository

    # None / 0 budget = "no limit": resolve to the ₹5M ceiling. NEVER pass
    # inf into the knapsack — roi.py allocates one DP bucket per ₹100 and
    # int(inf // 100) raises OverflowError.
    resolved_budget = (
        5_000_000.0
        if req.budget_inr is None or req.budget_inr <= 0
        else float(req.budget_inr)
    )

    try:
        result = optimize_build(
            config,
            resolved_budget,
            PartsRepository(conn),
            goal=req.goal,
            profile=req.profile,
            bike_model_id=req.bike_id,
            surrogate=_SURROGATE,
            surrogate_source=_SURROGATE_SOURCE,
            max_candidates=req.max_candidates,
            progress_cb=progress,
        )
    except HTTPException:
        raise  # e.g. 404 for an unknown bike_id — don't relabel as 500
    except Exception as exc:
        logging.getLogger(__name__).error(
            "optimize_build failed: %s", exc, exc_info=True
        )
        raise HTTPException(500, f"Optimization failed: {exc}") from exc

    # Belt-and-braces: cost-per-tenth ratios can be non-finite (a part that
    # adds cost with ~0 ET gain); bare inf/nan is not JSON-compliant and 500s
    # the route. json_safe nulls them so the response always serializes.
    from .analysis.roi import json_safe

    return json_safe(result.to_dict())


@app.post(
    "/api/optimize/build",
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def optimize_build_route(req: OptimizeBuildRequest):
    """Synchronous build optimiser (see ``_optimize_impl``)."""
    return _optimize_impl(req)


class AutotuneRequest(BaseModel):
    """POST /api/autotune/ecu — conditions-aware drag setup advisor."""

    bike_id: int | None = Field(None, description="DB bike_models.id")
    bike_preset: str | None = Field(None, description="Fallback preset name")
    location: str | None = Field(
        None, max_length=200, description="City/venue, e.g. 'Pune, IN'"
    )
    venue_id: int | None = Field(None, description="Seeded venue id (sets altitude)")
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    altitude_m: float | None = Field(None, ge=-500, le=8000)
    ambient_temp_c: float | None = Field(None, ge=-30, le=60)
    track_temp_c: float | None = Field(None, ge=-30, le=80)
    humidity_pct: float | None = Field(None, ge=0, le=100)
    pressure_hpa: float | None = Field(None, ge=800, le=1100)
    rider_weight_kg: float = Field(75.0, ge=40, le=150)
    gear_span: int = Field(
        3, ge=1, le=6, description="± sprocket-tooth sweep half-width"
    )
    launch_steps: int = Field(6, ge=2, le=10, description="Launch-RPM sweep resolution")

    model_config = {"populate_by_name": True}


def _apply_resolved_env(config, vd: dict) -> None:
    """Apply a /api/venues/resolve response dict onto config.environment."""
    if vd.get("temperature_c") is not None:
        t = float(vd["temperature_c"])
        config.environment.ambient_temp_c = t
        config.environment.track_temp_c = t + 7.0  # track typically ~7°C over air
    if vd.get("humidity_pct") is not None:
        config.environment.relative_humidity_pct = float(vd["humidity_pct"])
    if vd.get("pressure_hpa") is not None:
        config.environment.barometric_pressure_hpa = float(vd["pressure_hpa"])
    if vd.get("altitude_m") is not None:
        config.environment.altitude_m = float(vd["altitude_m"])
    if vd.get("venue_name"):
        config.environment.venue_name = vd["venue_name"]


def _autotune_impl(req: AutotuneRequest, progress=None):
    """
    Recommend a conditions-aware launch setup (final drive / gearing, launch RPM,
    tyre pressure, fuel & timing trim) for a bike at a given location/conditions,
    with the atmospheric rationale (density altitude, air density, power
    correction) shown.  Atmospherics are consumed from the venue/weather
    resolver and the environment model — never re-derived.
    """
    try:
        config = _build_config(
            bike_id=req.bike_id,
            bike_preset=req.bike_preset,
            power_boost_pct=0.0,
            mass_delta_kg=0.0,
            rider_mass_kg=req.rider_weight_kg,
            venue_id=req.venue_id,
        )
    except Exception as exc:
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    env_source = "config_default"
    if req.location or (req.lat is not None and req.lon is not None):
        try:
            resolved = resolve_venue(
                VenueResolveRequest(
                    location=req.location,
                    lat=req.lat,
                    lon=req.lon,
                    altitude_m=req.altitude_m,
                )
            )
            _apply_resolved_env(config, resolved)
            env_source = resolved.get("source", "resolved")
        except HTTPException as exc:
            env_source = f"resolution_unavailable_{exc.status_code}"
        except Exception as exc:
            logging.getLogger(__name__).warning("autotune env resolve failed: %s", exc)
            env_source = "resolution_error"

    # Explicit condition overrides take precedence over any resolution.
    if req.altitude_m is not None:
        config.environment.altitude_m = req.altitude_m
    if req.ambient_temp_c is not None:
        config.environment.ambient_temp_c = req.ambient_temp_c
    if req.track_temp_c is not None:
        config.environment.track_temp_c = req.track_temp_c
    if req.humidity_pct is not None:
        config.environment.relative_humidity_pct = req.humidity_pct
    if req.pressure_hpa is not None:
        config.environment.barometric_pressure_hpa = req.pressure_hpa

    from .analysis.ecu_autotune import autotune

    try:
        result = autotune(
            config,
            gear_span=req.gear_span,
            launch_steps=req.launch_steps,
            progress_cb=progress,
        )
    except HTTPException:
        raise  # e.g. 404 for an unknown bike_id — don't relabel as 500
    except Exception as exc:
        logging.getLogger(__name__).error("autotune failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Autotune failed: {exc}") from exc

    out = result.to_dict()
    out["environment_source"] = env_source
    return out


@app.post(
    "/api/autotune/ecu",
    dependencies=[Depends(rate_limit("autotune", 6, 60.0))],
)
def autotune_ecu_route(req: AutotuneRequest):
    """Synchronous autotune (see ``_autotune_impl``)."""
    return _autotune_impl(req)


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND JOBS + REAL PROGRESS  (/api/jobs/*) — added 2026-06-07
#
# The website's progress bars poll these instead of showing a spinner.
# POST /api/jobs/{simulate|topspeed|autotune|optimize} starts the work on a
# daemon thread and returns 202 + job_id immediately; GET /api/jobs/{id}
# reports {status, progress 0..1, stage, result|error}. The registry is
# in-memory (single Render instance) with TTL eviction — motoquant/jobs.py.
# The synchronous routes above are unchanged (desktop app + older clients).
# ═══════════════════════════════════════════════════════════════════════════


def _start_job(kind: str, runner) -> dict:
    from .jobs import JobCapacityError, create_job

    try:
        job = create_job(kind, runner)
    except JobCapacityError as exc:
        raise HTTPException(429, str(exc)) from exc
    return {"job_id": job.id, "kind": kind, "status": job.status}


@app.post(
    "/api/jobs/simulate",
    status_code=202,
    dependencies=[Depends(_meter_full_sim)],
)
def job_simulate(req: SimulateRequest):
    """Start a full simulation as a background job (real progress)."""
    return _start_job("simulate", lambda progress: _simulate_impl(req, progress))


@app.post(
    "/api/jobs/topspeed",
    status_code=202,
    dependencies=[Depends(_meter_full_sim)],
)
def job_topspeed(req: TopSpeedRequest):
    """Start a top-speed run as a background job (real progress)."""
    return _start_job("topspeed", lambda progress: _topspeed_impl(req, progress))


@app.post(
    "/api/jobs/optimize",
    status_code=202,
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def job_optimize(req: OptimizeBuildRequest):
    """Start the build optimiser as a background job (real progress)."""
    return _start_job("optimize", lambda progress: _optimize_impl(req, progress))


@app.post(
    "/api/jobs/autotune",
    status_code=202,
    dependencies=[Depends(rate_limit("autotune", 6, 60.0))],
)
def job_autotune(req: AutotuneRequest):
    """Start the ECU autotune as a background job (real progress)."""
    return _start_job("autotune", lambda progress: _autotune_impl(req, progress))


class OutlawRequest(BaseModel):
    """POST /api/jobs/outlaw — composed outlaw/open-class max-effort build.

    Pipeline: best drag_prep rubber → full_race parts knapsack (budget
    unlimited unless capped) → gearing + launch autotune on the modified
    bike → combined verification sim.
    """

    bike_id: int | None = Field(None, description="DB bike_models.id")
    bike_preset: str | None = Field(
        None, description="Fallback preset: gsxr1000_k5 | yzfr1_4c8 | hayabusa_gen1"
    )
    budget_inr: float | None = Field(
        None, ge=0, le=5_000_000, description="null / 0 = no limit"
    )
    goal: str = Field("min_et")
    rider_weight_kg: float = Field(75.0, ge=40, le=150)
    venue_id: int | None = Field(None)
    max_candidates: int | None = Field(None, ge=1, le=200)


def _outlaw_impl(req: OutlawRequest, progress=None) -> dict:
    conn = _get_db()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        config = _build_config(
            bike_id=req.bike_id,
            bike_preset=req.bike_preset,
            power_boost_pct=0.0,
            mass_delta_kg=0.0,
            rider_mass_kg=req.rider_weight_kg,
            venue_id=req.venue_id,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    surrogate, surrogate_source = _get_surrogate_pair()

    from .analysis.outlaw import optimize_outlaw
    from .database.parts_repo import PartsRepository
    from .database.tire_repo import TireRepository

    try:
        return optimize_outlaw(
            config,
            PartsRepository(conn),
            TireRepository(conn),
            bike_model_id=req.bike_id,
            budget_inr=req.budget_inr,
            goal=req.goal,
            surrogate=surrogate,
            surrogate_source=surrogate_source,
            max_candidates=req.max_candidates,
            progress_cb=progress,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).error(
            "optimize_outlaw failed: %s", exc, exc_info=True
        )
        raise HTTPException(500, f"Outlaw build failed: {exc}") from exc


@app.post(
    "/api/jobs/outlaw",
    status_code=202,
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def job_outlaw(req: OutlawRequest):
    """Start the composed outlaw/open-class build as a background job."""
    return _start_job("outlaw", lambda progress: _outlaw_impl(req, progress))


@app.post("/api/jobs/compare", status_code=202)
def job_compare(req: CompareRequest):
    """Start an A-vs-B comparison as a background job (real progress).

    No metering dependency on purpose — the synchronous /api/simulate/compare
    route has never been metered, and the job route must stay behaviourally
    identical to the sync route it wraps (deploy-skew fallback contract)."""
    return _start_job("compare", lambda progress: _compare_impl(req, progress))


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    """Poll a background job: status, progress (0..1), stage, result/error."""
    from .jobs import get_job

    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Unknown or expired job (results are kept ~15 min)")
    out = {
        "job_id": job.id,
        "kind": job.kind,
        "status": job.status,
        "progress": round(job.progress, 4),
        "stage": job.stage,
    }
    if job.status == "done":
        out["result"] = job.result
    elif job.status == "error":
        out["error"] = job.error
    return out


@app.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str):
    """
    Request cancellation of a running job (the website's Stop button).

    Cooperative: the worker thread stops at its next progress tick. Terminal
    jobs (done / error / cancelled) are returned unchanged — cancelling a
    finished job is a no-op, not an error.
    """
    from .jobs import cancel_job

    job = cancel_job(job_id)
    if job is None:
        raise HTTPException(404, "Unknown or expired job (results are kept ~15 min)")
    return {
        "job_id": job.id,
        "kind": job.kind,
        "status": job.status,
        "cancel_requested": job.cancel_requested,
    }


# ─────────────────────────────────────────────
# Keep-warm self-ping (Render free tier) — added 2026-06-06.
#
# No-op everywhere except where RENDER_EXTERNAL_URL / MOTOQUANT_KEEPWARM_URL
# is set (Render injects the former automatically). See motoquant/keepwarm.py
# for the full rationale; wrapped so a failure here can never block boot.
# ─────────────────────────────────────────────


@app.on_event("startup")
async def _start_keepwarm_loop() -> None:
    try:
        from .keepwarm import start_keepwarm

        start_keepwarm()
    except Exception:  # noqa: BLE001 — keep-warm is best-effort only
        logging.getLogger(__name__).warning("keep-warm init failed", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# AUTH / SUBSCRIPTIONS / PAYMENTS router mounts (Phase 6 — June 2026)
# The S5 routers existed since April but were never mounted (the
# "reserved for Stream 5" comment above) — /api/auth/* 404'd in prod while
# three routes were already tier-gated. Mounting is wrapped so a missing
# optional dep (python-jose, email-validator) can never block boot:
# require_tier already degrades to a no-op stub in that case.
# ═══════════════════════════════════════════════════════════════════════════

try:
    from .auth import get_current_user as _get_current_user, router as _auth_router
    from .payments import router as _payments_router
    from .subscriptions import router as _subscriptions_router

    app.include_router(_auth_router, prefix="/api/auth")
    app.include_router(_subscriptions_router, prefix="/api/subscriptions")
    app.include_router(_payments_router, prefix="/api/payments")

    @app.get("/api/me/runs")
    def my_runs(
        user: dict = Depends(_get_current_user),  # noqa: B008
        limit: int = Query(25, le=100),
    ):
        """Saved runs for the signed-in user (powers the account Garage)."""
        db = _get_db()
        if not db:
            raise HTTPException(503, "Database unavailable")
        try:
            rows = db.execute(
                """SELECT sr.id, sr.et_quarter_s, sr.trap_speed_kmh,
                          sr.et_eighth_s, sr.time_60ft_s, sr.notes,
                          sr.created_at,
                          m.name AS manufacturer, bm.model_name AS model,
                          bm.year_from AS year, v.name AS venue
                   FROM sim_runs sr
                   LEFT JOIN bike_configs bc ON sr.bike_config_id = bc.id
                   LEFT JOIN bike_models bm ON bc.bike_model_id = bm.id
                   LEFT JOIN manufacturers m ON bm.manufacturer_id = m.id
                   LEFT JOIN venues v ON sr.venue_id = v.id
                   WHERE sr.user_id = ?
                   ORDER BY sr.id DESC
                   LIMIT ?""",
                (user["id"], limit),
            ).fetchall()
            return {"runs": [dict(r) for r in rows], "count": len(rows)}
        except sqlite3.Error:
            return {"runs": [], "count": 0}

except ImportError as _exc:  # pragma: no cover — optional-deps fallback
    logging.getLogger(__name__).warning(
        "Auth/subscriptions/payments routers not mounted: %s", _exc
    )


@app.on_event("startup")
async def _ensure_phase6_schema() -> None:
    """Guarded ALTERs so pre-June-2026 DBs gain run-attribution + auth tables."""
    try:
        db = _get_db()
        if not db:
            return
        try:
            db.execute("ALTER TABLE sim_runs ADD COLUMN user_id INTEGER")
            db.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
        try:
            db.execute("ALTER TABLE bike_configs ADD COLUMN category_tag TEXT")
            db.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
        from .database import (
            subscriptions_repo as _subs_repo,
            users_repo as _users_repo,
        )
        from .database.connection import connect as _db_connect

        conn = _db_connect()
        try:
            _users_repo.ensure_tables(conn)
            _subs_repo.ensure_tables(conn)
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — schema top-up is best-effort
        logging.getLogger(__name__).warning(
            "phase6 schema ensure failed", exc_info=True
        )
