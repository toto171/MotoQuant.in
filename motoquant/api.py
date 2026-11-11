"""
MotoQuant — FastAPI Web Server
==============================
REST API wrapper around the MotoQuant physics engine and database.
Serves the motoquant.in simulator, tools and bike library. It has no accounts
and stores nothing a visitor sends for other visitors to see.

Endpoints
---------
GET  /                        Health / welcome
GET  /api/health              JSON health check
GET  /api/bikes               List / search bikes (paginated)
GET  /api/bikes/{id}          Bike detail + default config
GET  /api/venues              List venues with current DA
POST /api/simulate            Full simulation (returns v(t), RPM(t), etc.)
POST /api/simulate/quick      Quick ET-only simulation (faster for UI sliders)
GET  /api/tires               List tire models
GET  /docs                    Every route, with request and response schemas

Run locally
-----------
    uvicorn motoquant.api:app --reload --port 8000

Deploy
------
    Set the PORT env var; render.yaml builds the Docker image.
"""

import asyncio
import copy
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import tempfile
import threading
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.datastructures import MutableHeaders

# TypedDict must come from typing_extensions on Python < 3.12 when used in
# Pydantic/FastAPI annotations (pydantic raises PydanticUserError otherwise).
# python:3.11-slim in prod hit exactly that and crash-looped — 2026-06-06.
from typing_extensions import TypedDict

from . import __version__, engine_select
from .constants import ROLLOUT_M
from .database.connection import (
    bump_catalog_generation,
    catalog_token,
)
from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .ratelimit import heavy_gate_for, rate_limit

# ─── App init ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="MotoQuant API",
    description="First-principles motorcycle drag racing simulator -- motoquant.in",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Optional Sentry error tracking. No-ops if SENTRY_DSN is not set OR if
# sentry-sdk isn't installed. See motoquant.observability for env knobs.
from motoquant.observability import init_sentry as _init_sentry  # noqa: E402

_init_sentry(app_name="motoquant-api")

# CORS. The website calls the API same-origin through its /api proxy, so it
# needs no CORS at all; browsers on other sites must not be able to drive the
# free (server-key) assistant from their visitors' browsers. Allowed: the
# public site and local development. Self-hosters add their own origins with
# MOTOQUANT_CORS_ORIGINS (comma-separated; "*" restores the old behaviour).
_DEFAULT_CORS_ORIGINS = (
    "https://motoquant.in",
    "https://www.motoquant.in",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def _cors_origins() -> list[str]:
    raw = os.environ.get("MOTOQUANT_CORS_ORIGINS", "").strip()
    if not raw:
        return list(_DEFAULT_CORS_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Request-size fuse. No legitimate JSON body is anywhere near this (chat
# messages cap at 8,000 characters); without it a multi-megabyte body is read
# and parsed in full on the 512 MB instance before validation rejects it. The
# calibration uploads keep their own 25 MB cap (MAX_UPLOAD_BYTES).
MAX_REQUEST_BYTES = 256 * 1024
_BODY_LIMIT_EXEMPT_PREFIXES = ("/api/calibrate/",)


def _too_large() -> HTTPException:
    return HTTPException(
        413, f"Request body is larger than {MAX_REQUEST_BYTES // 1024} KB"
    )


class _BodySizeLimit:
    """Refuse oversized request bodies with 413 before anything parses them."""

    def __init__(self, app, max_bytes: int = MAX_REQUEST_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("method") not in ("POST", "PUT", "PATCH")
            or scope.get("path", "").startswith(_BODY_LIMIT_EXEMPT_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return
        for name, value in scope.get("headers") or ():
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = 0
                if declared > self.max_bytes:
                    response = JSONResponse(
                        {"detail": _too_large().detail}, status_code=413
                    )
                    await response(scope, receive, send)
                    return
        received = 0

        async def limited_receive():
            # Chunked bodies carry no Content-Length: count as they arrive.
            # An HTTPException here passes through FastAPI's body reader
            # unchanged and becomes a normal 413 response.
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _too_large()
            return message

        await self.app(scope, limited_receive, send)


class _SecurityHeaders:
    """nosniff and HSTS on every API response (the API is HTTPS-only)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Strict-Transport-Security", "max-age=31536000")
            await send(message)

        await self.app(scope, receive, send_with_headers)


app.add_middleware(_BodySizeLimit)
app.add_middleware(_SecurityHeaders)


_PATH_RE = re.compile(r"(?:[A-Za-z]:)?(?:[\\/][\w.\-]+){2,}")


def _without_paths(text: str) -> str:
    """Drop file-system paths (temp files, install dirs) from a message."""
    return _PATH_RE.sub("<file>", str(text))[:300]


def _require_finish(sim, label: str | None = None) -> None:
    """422 instead of a "0.000 s" success when a run never reaches the line.

    A setup can be valid input and still not finish: very heavy, very weak and
    into a strong headwind, it runs out of the simulator's time limit. The
    run then reports a quarter-mile time of 0, which used to go out as if it
    were a real (impossibly fast) result.
    """
    if getattr(sim, "finished_quarter", True):
        return
    who = f"{label}: " if label else ""
    raise HTTPException(
        422,
        f"{who}this setup doesn't reach the quarter-mile finish line within the "
        "simulator's time limit. Check the power, weight and wind settings.",
    )


def _server_error(what: str, exc: BaseException) -> HTTPException:
    """A 500 that logs the exception (Sentry picks it up) but tells the client
    only what failed: exception text can carry file paths, SQL or internals."""
    logging.getLogger(__name__).error("%s: %s", what, exc, exc_info=exc)
    return HTTPException(500, f"{what}. Please try again.")


# Response compression -- the origin serves 50-600 KB JSON payloads (full
# catalog fetches, sim timeseries) uncompressed, which is pure egress waste
# on the free-tier instance and slow on Indian mobile links. minimum_size
# keeps tiny health/quick-sim responses uncompressed (gzip overhead > win).
# compresslevel=5: level 9 costs ~2.3x the CPU of level 5 for ~4% smaller output
# on the catalog JSON (0.5-CPU instance).
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5)

# Database row ids are SQLite INTEGERs (signed 64-bit) but the catalog never
# approaches 2**31; bounding request ids keeps absurd values (which sqlite3
# rejects with OverflowError) a clean 422 instead of a 500.
MAX_DB_ID = 2**31 - 1
DbId = Annotated[int, Field(ge=1, le=MAX_DB_ID)]


def _json_safe_float(x: float) -> float | str:
    return x if math.isfinite(x) else str(x)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """422 body in FastAPI's default shape, but always JSON-serialisable.

    The default handler echoes each offending ``input`` back; a JSON ``NaN`` /
    ``Infinity`` there makes the (strict-JSON) encoder raise, turning a plain
    validation failure into a 500. Non-finite floats are echoed as strings.
    """
    try:
        detail = jsonable_encoder(
            exc.errors(), custom_encoder={float: _json_safe_float}
        )
        content = {"detail": detail}
        json.dumps(content, allow_nan=False)
    except (TypeError, ValueError):
        content = {
            "detail": [
                {
                    "type": e.get("type"),
                    "loc": list(e.get("loc", ())),
                    "msg": e.get("msg"),
                }
                for e in exc.errors()
            ]
        }
    return JSONResponse(status_code=422, content=content)


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
        # A new connection may be a different database file: nothing cached
        # from the previous one may be served.
        bump_catalog_generation()
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


class SkippedPartDict(TypedDict):
    """One entry of ``parts_skipped_detail``: a requested part id that was NOT
    applied, and why. ``reason`` is ``"unknown_part"`` (no such catalog id),
    ``"does_not_fit"`` (the part is not compatible with the chosen bike — the
    same verdict ``GET /api/parts?bike_id=`` gives) or ``"not_applied"`` (the
    part row could not be applied). ``detail`` is a plain-language sentence."""

    id: int
    reason: str
    detail: str


class EnvironmentEchoDict(TypedDict):
    """The conditions a result was actually simulated under.

    ``name`` is the venue (or resolved location) name, ``"Custom conditions"``
    when only manual values were supplied, or ``"Default conditions"`` when the
    server defaults were used (``is_default`` is then true). Numbers are read
    off the config the engine ran, never restated from the request.
    """

    name: str
    is_default: bool
    source: str  # "default" | "manual" | "venue"
    altitude_m: float
    ambient_temp_c: float
    track_temp_c: float
    humidity_pct: float
    pressure_hpa: float
    headwind_kmh: float
    track_surface: str


class TyreLabelDict(TypedDict):
    """A catalog tyre fitted by the request (``tyres`` in quick results)."""

    position: str
    id: int
    name: str


class QuickSimResultDict(TypedDict):
    """Shape of the dict returned by the ``/api/simulate/quick`` endpoint.

    Built inline in :func:`simulate_quick`. The website's simulator and
    timeslip pages read these keys by name, so treat them as a public contract.

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
    parts_skipped: list[int]
    parts_skipped_detail: list[SkippedPartDict]
    tyres: list[TyreLabelDict]
    environment: EnvironmentEchoDict
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
    Built by :func:`_topspeed_timeseries`: ~100 Hz source, decimated to at most
    ``TOPSPEED_MAX_SERIES_POINTS`` samples (first, last and peak kept) and
    rounded to plotting precision.
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
    parts_skipped: list[int]
    parts_skipped_detail: list[SkippedPartDict]
    environment: EnvironmentEchoDict
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
    parts_skipped: list[int]
    parts_skipped_detail: list[SkippedPartDict]
    environment: EnvironmentEchoDict


# ─── Request / response models ────────────────────────────────────────────


class ConditionsRequest(BaseModel):
    """Optional race conditions shared by every simulate, compare, optimiser,
    autotune and outlaw route (and their ``/api/jobs/*`` variants).

    Precedence: ``venue_id`` (seeded venue) sets altitude and surface first; a
    resolved ``location`` / ``lat``+``lon`` then sets the environment; explicit
    values (``altitude_m``, ``ambient_temp_c``, ``track_temp_c``,
    ``humidity_pct``, ``pressure_hpa``) override both. The conditions actually
    simulated are echoed in the response's ``environment`` block."""

    location: str | None = Field(
        None, max_length=200, description="City/venue, e.g. 'Pune, IN'"
    )
    venue_id: DbId | None = Field(None, description="Seeded venue id (sets altitude)")
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    altitude_m: float | None = Field(None, ge=-500, le=8000)
    ambient_temp_c: float | None = Field(None, ge=-30, le=60)
    track_temp_c: float | None = Field(None, ge=-30, le=80)
    humidity_pct: float | None = Field(None, ge=0, le=100)
    pressure_hpa: float | None = Field(None, ge=800, le=1100)


class SimulateRequest(ConditionsRequest):
    """POST /api/simulate -- full simulation request."""

    # Bike selection -- one of these must be provided
    bike_id: DbId | None = Field(None, description="DB bike model ID")
    bike_preset: str | None = Field(
        None, description="'gsxr1000_k5' | 'yzfr1_4c8' | 'hayabusa_gen1'"
    )

    # Optional overrides (applied on top of the selected bike's defaults).
    # Bounds mirror the optimizer routes (OptimizeBuildRequest/AutotuneRequest)
    # so the sim surface can't be fed physically-impossible values that make
    # the engine return ET=0.0 nonsense as a 200 success.
    power_boost_pct: float = Field(
        0.0,
        ge=-50.0,
        le=200.0,
        description="Extra power as % of stock (e.g. 10 = +10%)",
    )
    mass_delta_kg: float = Field(
        0.0, ge=-100.0, le=200.0, description="Mass change in kg (+add, -remove)"
    )
    rider_mass_kg: float = Field(
        75.0, ge=20.0, le=250.0, description="Rider weight [kg]"
    )
    # Same cap as QuickSimRequest.part_ids.
    part_ids: list[DbId] = Field(
        default_factory=list, max_length=30, description="Part IDs to apply"
    )
    front_tire_id: DbId | None = Field(None, description="Override front tire DB ID")
    rear_tire_id: DbId | None = Field(None, description="Override rear tire DB ID")
    # venue_id / location / lat / lon / altitude_m / ambient_temp_c /
    # track_temp_c / humidity_pct / pressure_hpa come from ConditionsRequest.
    # Their bounds reject physically impossible input (humidity_pct=1e9 or
    # ambient_temp_c=500 once returned et_quarter_s 0.0 as a 200 success).
    headwind_kmh: float | None = Field(
        None, ge=-200, le=200, description="Headwind km/h (negative = tailwind)"
    )

    # Simulation options
    use_adaptive_dt: bool = Field(
        False, description="Use adaptive RK4 timestep (slower)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bike_id": 1,
                "power_boost_pct": 5.0,
                "mass_delta_kg": -3.0,
                "rider_mass_kg": 70.0,
            }
        }
    )


class QuickSimRequest(ConditionsRequest):
    """POST /api/simulate/quick -- minimal input for slider-driven UI."""

    bike_id: DbId | None = None
    bike_preset: str | None = None
    power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    rider_mass_kg: float = Field(75.0, ge=20.0, le=250.0)
    # Capped: each id costs a DB lookup + config mutation, and the list was
    # unbounded (2026-08-11 hardening) — a single request carrying tens of
    # thousands of ids became a free CPU/DB amplifier. No real build exceeds
    # ~15 parts; 30 leaves 2x headroom.
    part_ids: list[DbId] = Field(
        default_factory=list, max_length=30, description="Part IDs to apply"
    )
    front_tire_id: DbId | None = None
    rear_tire_id: DbId | None = None
    headwind_kmh: float | None = Field(None, ge=-200, le=200)


# ─── Config builder ────────────────────────────────────────────────────────

_PRESETS = {
    "gsxr1000_k5": gsxr1000_k5,
    "yzfr1_4c8": yzfr1_4c8,
    "hayabusa_gen1": hayabusa_gen1,
}


def _precheck_refs(
    *,
    bike_ids=(),
    bike_presets=(),
    venue_id: int | None = None,
    tire_ids=(),
) -> None:
    """404 on catalog ids / presets that do not exist.

    Job routes run their work on a worker thread, where an unknown id would
    only surface as a failed job on the first poll; checking up front gives the
    caller the same 404 the synchronous routes return.
    """
    for bike_id, preset in zip(bike_ids, bike_presets):
        if bike_id is None and preset and preset not in _PRESETS:
            raise HTTPException(404, f"Unknown bike_preset: {preset}")
    db = _get_db()
    if not db:
        return

    def _exists(table: str, row_id: int) -> bool:
        return db.execute(f"SELECT 1 FROM {table} WHERE id=?", (row_id,)).fetchone()

    for bike_id in bike_ids:
        if bike_id is not None and not _exists("bike_models", bike_id):
            raise HTTPException(404, f"Bike {bike_id} not found")
    if venue_id is not None and not _exists("venues", venue_id):
        raise HTTPException(404, f"Venue {venue_id} not found")
    # tire_ids come in (front, rear) pairs, as every caller passes them.
    for i, tire_id in enumerate(tire_ids):
        if tire_id is None:
            continue
        row = db.execute(
            "SELECT position FROM tire_models WHERE id=?", (tire_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, f"Tire {tire_id} not found")
        _check_tire_position(tire_id, row[0], "front" if i % 2 == 0 else "rear")


def _check_tire_position(tire_id: int, position: str | None, wanted: str) -> None:
    """422 when a tyre made for one wheel is requested for the other.

    Grip for drive traction comes from the rear tyre, so a front tyre sent as
    ``rear_tire_id`` would silently change the result. ``both`` fits either.
    """
    pos = (position or "").lower()
    if pos in ("front", "rear") and pos != wanted:
        raise HTTPException(
            422, f"Tire {tire_id} is a {pos} tyre and cannot be fitted at the {wanted}"
        )


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
    altitude_m: float | None = None,
    pressure_hpa: float | None = None,
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> BikeConfig:
    """Assemble a BikeConfig from request parameters.

    The condition arguments (``venue_id`` .. ``lon``) are the fields of
    :class:`ConditionsRequest`, applied with the same precedence and the same
    helper (:func:`_apply_conditions`) the optimiser routes use.
    """

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
        fn = _PRESETS.get(bike_preset)
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
    # An id that matches no catalog row is a client error (404), like an
    # unknown bike_id — silently returning stock-condition numbers for a
    # typo'd venue or tire looks like a valid answer.
    unknown_ref: str | None = None
    if venue_id is not None:
        db = _get_db()
        if db:
            try:
                row = db.execute(
                    "SELECT * FROM venues WHERE id=?", (venue_id,)
                ).fetchone()
                if row is None:
                    unknown_ref = f"Venue {venue_id} not found"
                else:
                    d = dict(row)
                    cfg.environment.venue_name = d["name"]
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
        if unknown_ref:
            raise HTTPException(404, unknown_ref)

    # -- Environment overrides (on top of venue) -----------------------------
    if venue_id is None:
        manual = any(
            v is not None
            for v in (
                ambient_temp_c,
                track_temp_c,
                humidity_pct,
                headwind_kmh,
                altitude_m,
                pressure_hpa,
            )
        )
        cfg.environment.venue_name = (
            CUSTOM_CONDITIONS_NAME if manual else DEFAULT_CONDITIONS_NAME
        )
    if ambient_temp_c is not None:
        cfg.environment.ambient_temp_c = ambient_temp_c
        if track_temp_c is None:
            # Same rule as a resolved place: the track runs ~7 °C over the air.
            cfg.environment.track_temp_c = ambient_temp_c + 7.0
    if track_temp_c is not None:
        cfg.environment.track_temp_c = track_temp_c
    if humidity_pct is not None:
        cfg.environment.relative_humidity_pct = humidity_pct
    if headwind_kmh is not None:
        cfg.environment.wind_speed_ms = headwind_kmh / 3.6
        cfg.environment.wind_direction_deg = 0.0  # 0 = headwind
    if any(v is not None for v in (location, lat, lon, altitude_m, pressure_hpa)):
        _apply_conditions(
            cfg,
            ConditionsRequest.model_construct(
                location=location,
                venue_id=venue_id,
                lat=lat,
                lon=lon,
                altitude_m=altitude_m,
                ambient_temp_c=ambient_temp_c,
                track_temp_c=track_temp_c,
                humidity_pct=humidity_pct,
                pressure_hpa=pressure_hpa,
            ),
        )

    # -- Tire overrides ------------------------------------------------------
    # TireParams carries ONE scalar mu_peak, and drive traction is rear-tire
    # physics — so ONLY the rear tire may set grip. A front-only selection
    # must not replace rear grip with the front tire's compound; it is still
    # checked for existence.
    db = _get_db() if (front_tire_id is not None or rear_tire_id is not None) else None
    if db:
        for tire_id in (front_tire_id, rear_tire_id):
            if tire_id is None:
                continue
            try:
                trow = db.execute(
                    "SELECT pacejka_D, mu_peak, position FROM tire_models WHERE id=?",
                    (tire_id,),
                ).fetchone()
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Failed to load tire_id=%s: %s", tire_id, e
                )
                continue
            if trow is None:
                raise HTTPException(404, f"Tire {tire_id} not found")
            if tire_id == front_tire_id:
                _check_tire_position(tire_id, dict(trow).get("position"), "front")
            if tire_id == rear_tire_id:
                _check_tire_position(tire_id, dict(trow).get("position"), "rear")
                td = dict(trow)
                mu = td.get("mu_peak") or td.get("pacejka_D")
                if mu and float(mu) > 0:
                    cfg.tires.mu_peak = float(mu)

    return cfg


# Why a requested part id was not applied (``parts_skipped_detail[].reason``).
SKIP_UNKNOWN = "unknown_part"
SKIP_DOES_NOT_FIT = "does_not_fit"
SKIP_NOT_APPLIED = "not_applied"


def _fitment_bike_row(db, bike_id: int | None, bike_preset: str | None) -> dict | None:
    """The catalog row (enriched for the compatibility engine) of the bike a
    request names, or None when it has no catalog row to judge fitment by."""
    try:
        model_id = _parts_model_id(db, bike_id, bike_preset)
        if model_id is None:
            return None
        raw = db.execute(
            "SELECT * FROM bike_models WHERE id = ?", (model_id,)
        ).fetchone()
        if raw is None:
            return None
        from .database.parts_repo import enrich_bike_row_for_fitment

        bike_row = dict(raw)
        enrich_bike_row_for_fitment(db, bike_row)
        return bike_row
    except Exception as exc:  # noqa: BLE001 — a lookup fault must not 500 the sim
        logging.getLogger(__name__).warning(
            "fitment lookup failed for bike_id=%s preset=%s: %s",
            bike_id,
            bike_preset,
            exc,
        )
        return None


def _apply_parts_to_config(
    cfg: BikeConfig,
    part_ids: list[int] | None,
    *,
    include_price_in_summary: bool = True,
    skipped: list[int] | None = None,
    skipped_detail: list[SkippedPartDict] | None = None,
    bike_id: int | None = None,
    bike_preset: str | None = None,
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
    * A part that does not fit the bike is NOT applied. ``bike_id`` /
      ``bike_preset`` identify the bike exactly as the request did (a preset
      maps to its catalog row, see :func:`_parts_model_id`); each part then
      goes through the same ``is_compatible`` engine ``GET /api/parts?bike_id``
      uses, so the sim routes and the parts list can never disagree about
      what fits. When the bike has no catalog row there is nothing to judge
      against and parts are applied as requested.
    * When ``skipped`` is a list, it is filled with the (de-duplicated, ordered)
      requested ids that were NOT applied — unknown to the catalog, not
      compatible with the bike, or dropped by a failure — so routes can report
      ``parts_skipped`` instead of silently returning numbers for a part that
      was never (or should never be) fitted. ``skipped_detail`` receives one
      ``{id, reason, detail}`` entry per skipped id, in the same order.
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

    why: dict[int, tuple[str, str]] = {}  # part id -> (reason code, plain detail)

    def _report_skipped() -> None:
        applied_ids = {p["id"] for p in parts_applied}
        missed = [p for p in dict.fromkeys(part_ids) if p not in applied_ids]
        if skipped is not None:
            skipped.extend(missed)
        if skipped_detail is not None:
            for pid in missed:
                reason, detail = why.get(
                    pid, (SKIP_NOT_APPLIED, "The part could not be applied.")
                )
                skipped_detail.append({"id": pid, "reason": reason, "detail": detail})

    db = _get_db()
    if not db:
        _report_skipped()
        return cfg, parts_applied, build_cost

    try:
        from .analysis.roi import _BOOST_CATEGORIES
        from .database.bridge import apply_part_to_config
        from .parts.compatibility import is_compatible
        from .submodels.forced_induction import VALID_BOOST_TYPES

        fit_row = _fitment_bike_row(db, bike_id, bike_preset)

        # De-duplicate while preserving order. A repeated id used to be applied
        # once per occurrence, stacking that part's param_deltas: part_ids
        # [56, 56, 56] applied ONE Akrapovic system three times (+36 hp,
        # -20.4 kg from a single exhaust) and returned the fabricated ET as a
        # 200 success (2026-07-25 audit). You cannot bolt the same exhaust on
        # twice, so the physically meaningful reading of a repeated id is one
        # part — the same rule the ROI knapsack already enforces via its
        # exclusive-category groups.
        seen: set[int] = set()
        fitting: list[dict] = []
        for pid in part_ids:
            if pid in seen:
                continue
            seen.add(pid)
            row = db.execute(
                "SELECT p.*, pc.name AS category_name FROM parts p "
                "LEFT JOIN parts_categories pc ON pc.id = p.category_id "
                "WHERE p.id=?",
                (pid,),
            ).fetchone()
            if not row:
                why[pid] = (SKIP_UNKNOWN, "No part with this id is in the catalog.")
                continue
            part_dict = dict(row)
            if fit_row is not None:
                fits, fit_reason = is_compatible(part_dict, fit_row)
                if not fits:
                    label = " ".join(
                        x
                        for x in (part_dict.get("brand"), part_dict.get("model_name"))
                        if x
                    )
                    why[pid] = (
                        SKIP_DOES_NOT_FIT,
                        f"{label or 'This part'} does not fit this bike"
                        + (f" ({fit_reason})." if fit_reason else "."),
                    )
                    continue
            fitting.append(part_dict)

        # Apply in the optimizer's canonical order (roi._apply_order: NA parts
        # before boost, then cheapest first, then id). Parts whose effects do
        # not commute (a +10 hp delta and a x1.032 power multiplier) otherwise
        # gave a different time for the same build depending on click order,
        # and the simulator disagreed with the time the Upgrades page reported.
        fitting.sort(
            key=lambda d: (
                1 if (d.get("category_name") or "").lower() in _BOOST_CATEGORIES else 0,
                d.get("price_inr") or 0.0,
                d["id"],
            )
        )
        for part_dict in fitting:
            part_dict.pop("category_name", None)
            cfg = apply_part_to_config(cfg, part_dict)
            # A part carrying a typo'd boost_type would otherwise surface as
            # a 500 when the engine's ForcedInductionModel guard fires — turn
            # it into a client-visible 422 naming the offending part.
            bt = cfg.forced_induction.boost_type
            if bt not in VALID_BOOST_TYPES:
                raise HTTPException(
                    422,
                    f"Part {part_dict['id']} ({part_dict.get('model_name', '')}) "
                    f"sets invalid boost_type {bt!r}; valid: "
                    f"{sorted(VALID_BOOST_TYPES)}",
                )
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
    except HTTPException:
        raise  # the invalid-boost_type 422 above must reach the client
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Failed to apply parts %s: %s", part_ids, exc
        )
        # Preserve prior behaviour: return whatever was assembled before the
        # exception (parts_applied may be partially populated if the failure
        # came from a late row); cfg likewise carries any deltas already
        # applied. This matches the inline try/except behaviour we replaced.

    _report_skipped()
    return cfg, parts_applied, build_cost


DEFAULT_CONDITIONS_NAME = "Default conditions"
CUSTOM_CONDITIONS_NAME = "Custom conditions"


def _environment_echo(cfg: BikeConfig) -> EnvironmentEchoDict:
    e = cfg.environment
    name = e.venue_name
    is_default = name == DEFAULT_CONDITIONS_NAME
    source = (
        "default"
        if is_default
        else "manual"
        if name == CUSTOM_CONDITIONS_NAME
        else "venue"
    )
    headwind = (
        float(e.wind_speed_ms) * 3.6 * math.cos(math.radians(e.wind_direction_deg))
    )
    return {
        "name": name,
        "is_default": is_default,
        "source": source,
        "altitude_m": float(e.altitude_m),
        "ambient_temp_c": float(e.ambient_temp_c),
        "track_temp_c": float(e.track_temp_c),
        "humidity_pct": float(e.relative_humidity_pct),
        "pressure_hpa": float(e.barometric_pressure_hpa),
        "headwind_kmh": round(headwind, 2),
        "track_surface": str(e.track_surface),
    }


def _conditions_kwargs(req) -> dict:
    """The ConditionsRequest-only fields of *req*, as ``_build_config`` kwargs."""
    return {
        "altitude_m": req.altitude_m,
        "pressure_hpa": req.pressure_hpa,
        "location": req.location,
        "lat": req.lat,
        "lon": req.lon,
    }


# ─── Stock-baseline cache ─────────────────────────────────────────────────
# A quick sim with parts needs the same bike WITHOUT parts for its delta. That
# baseline depends only on the bike/slider/venue/tyre/environment inputs, so it
# is memoised (bounded LRU, thread-safe). The key carries the catalog
# generation, so a runtime catalog write retires every entry. Values are the
# already-rounded stock ET, i.e. exactly what an uncached run would report.
_STOCK_CACHE_MAX = 256
_stock_cache: "OrderedDict[tuple, float]" = OrderedDict()
_stock_cache_lock = threading.Lock()


def _catalog_token() -> tuple:
    """Freshness token of the shared catalog connection (see catalog_token)."""
    return catalog_token(_db_conn)


def _engine_tag() -> str:
    """Which integrator ``engine_select`` would pick right now.

    Part of the stock-baseline key so a cached baseline is only ever compared
    with a run from the same engine (``MOTOQUANT_ENGINE`` is read per call and
    tests switch it). The probes behind it are computed once per process.
    """
    try:
        return "native" if engine_select.native_active() else "python"
    except Exception:  # noqa: BLE001 — native forced but unusable: the sim will raise
        return "unavailable"


def _tyre_labels(front_id: int | None, rear_id: int | None) -> list[TyreLabelDict]:
    """Names of the catalog tyres a request fitted, for result cards and slips."""
    out: list[TyreLabelDict] = []
    db = _get_db() if (front_id is not None or rear_id is not None) else None
    if not db:
        return out
    for position, tid in (("front", front_id), ("rear", rear_id)):
        if tid is None:
            continue
        row = db.execute(
            "SELECT tm.id, tmf.name AS maker, tm.model_name, tm.size_designation "
            "FROM tire_models tm LEFT JOIN tire_manufacturers tmf "
            "ON tmf.id = tm.manufacturer_id WHERE tm.id = ?",
            (tid,),
        ).fetchone()
        if row:
            d = dict(row)
            name = " ".join(
                str(x)
                for x in (d["maker"], d["model_name"], d["size_designation"])
                if x
            )
            out.append({"position": position, "id": int(d["id"]), "name": name})
    return out


def _stock_key(req: "QuickSimRequest") -> tuple:
    return (
        _catalog_token(),
        _engine_tag(),
        req.bike_id,
        req.bike_preset,
        req.power_boost_pct,
        req.mass_delta_kg,
        req.rider_mass_kg,
        req.venue_id,
        req.front_tire_id,
        req.rear_tire_id,
        req.ambient_temp_c,
        req.track_temp_c,
        req.humidity_pct,
        req.headwind_kmh,
        req.altitude_m,
        req.pressure_hpa,
        req.location,
        req.lat,
        req.lon,
    )


def _stock_cache_get(key: tuple) -> float | None:
    with _stock_cache_lock:
        et = _stock_cache.get(key)
        if et is not None:
            _stock_cache.move_to_end(key)
        return et


def _stock_cache_put(key: tuple, et: float) -> None:
    with _stock_cache_lock:
        _stock_cache[key] = et
        _stock_cache.move_to_end(key)
        while len(_stock_cache) > _STOCK_CACHE_MAX:
            _stock_cache.popitem(last=False)


# ─── Catalog response cache ───────────────────────────────────────────────
# The catalog GETs (bikes, bike detail, parts, categories, tires, venues) are
# immutable between deploys apart from the rare runtime catalog write. The
# serialized body is cached per (route, validated params) and tagged with the
# catalog generation; a write bumps the generation, which retires every entry.
# Responses carry a weak ETag and a short public Cache-Control so browsers and
# the CDN revalidate instead of re-downloading.
CATALOG_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=3600"
_CATALOG_CACHE_MAX_ENTRIES = 256
_CATALOG_CACHE_MAX_BYTES = 24 * 1024 * 1024
_CATALOG_CACHE_MAX_ENTRY_BYTES = 4 * 1024 * 1024
_catalog_cache: "OrderedDict[tuple, tuple[tuple, bytes, str]]" = OrderedDict()
_catalog_cache_bytes = 0
_catalog_cache_lock = threading.Lock()
# hits / misses, exposed for tests and diagnostics
catalog_cache_stats = {"hits": 0, "misses": 0}


def _etag_matches(header: str | None, etag: str) -> bool:
    if not header:
        return False
    want = etag.removeprefix("W/")
    for tok in header.split(","):
        tok = tok.strip()
        if tok == "*" or tok.removeprefix("W/") == want:
            return True
    return False


def _serve_catalog(request: Request | None, key: tuple, build):
    """Serve ``build()`` (a JSON-able dict) through the catalog cache.

    ``request`` is None when a route function is called directly (MCP local
    backend, tests): the plain dict is returned, uncached. Errors raised by
    ``build`` are never cached.
    """
    global _catalog_cache_bytes
    if request is None:
        return build()
    gen = _catalog_token()
    with _catalog_cache_lock:
        ent = _catalog_cache.get(key)
        if ent is not None and ent[0] == gen:
            _catalog_cache.move_to_end(key)
            catalog_cache_stats["hits"] += 1
        else:
            ent = None
    if ent is None:
        payload = build()
        try:
            raw = json.dumps(payload, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError):
            raw = json.dumps(jsonable_encoder(payload), separators=(",", ":"))
        body = raw.encode("utf-8")
        etag = 'W/"' + hashlib.sha1(body).hexdigest()[:20] + '"'
        ent = (gen, body, etag)
        with _catalog_cache_lock:
            catalog_cache_stats["misses"] += 1
            old = _catalog_cache.pop(key, None)
            if old is not None:
                _catalog_cache_bytes -= len(old[1])
            if len(body) <= _CATALOG_CACHE_MAX_ENTRY_BYTES:
                _catalog_cache[key] = ent
                _catalog_cache_bytes += len(body)
                while _catalog_cache and (
                    len(_catalog_cache) > _CATALOG_CACHE_MAX_ENTRIES
                    or _catalog_cache_bytes > _CATALOG_CACHE_MAX_BYTES
                ):
                    _, evicted = _catalog_cache.popitem(last=False)
                    _catalog_cache_bytes -= len(evicted[1])
    _, body, etag = ent
    headers = {"ETag": etag, "Cache-Control": CATALOG_CACHE_CONTROL}
    if _etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers=headers)
    return Response(content=body, media_type="application/json", headers=headers)


# ─── Endpoints ────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "service": "MotoQuant API",
        "version": __version__,
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
        # Which integrator serves simulations (Rust core or the Python
        # reference) and why. Cheap: the extension import, host-math probe
        # and source fingerprint are each computed once per process.
        "engine": engine_select.engine_info(),
    }


@app.get("/api/debug/sentry-test")
def sentry_test():
    """Deliberately raise so the FastAPI Sentry integration reports a real
    event (operator smoke test for the DSN wiring).

    Hidden (404) unless MOTOQUANT_SENTRY_SELFTEST is truthy — never exposed
    on a default deploy."""
    enabled = os.environ.get("MOTOQUANT_SENTRY_SELFTEST", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not enabled:
        raise HTTPException(404, "Not found")
    raise RuntimeError(
        "MotoQuant Sentry self-test — this event is deliberate "
        "(MOTOQUANT_SENTRY_SELFTEST is set)"
    )


# ─────────────────────────────────────────────────────────────────────────
# Anonymous telemetry endpoint
# ─────────────────────────────────────────────────────────────────────────
# Used by web/lib/telemetry.js to capture client-side events:
#   - sim_run_start / sim_run_success / sim_run_error
#   - js_error / js_unhandled_rejection
#   - bike_select / mode_change
# Privacy: no user id, no IP correlation, per-tab random session_id only.
# Storage: the server log (stdout) ONLY by default. Forwarding to PostHog is
# strictly OPT-IN for whoever runs a deployment: it stays off unless the
# operator sets POSTHOG_API_KEY (see _forward_telemetry_posthog). A
# self-hosted copy of this open-source project sends nothing anywhere.


# Bounds (2026-07-25 audit §3.5): the beacon is unauthenticated and writes
# the usage numbers the roadmap reads, so every axis it can be pushed on gets
# a ceiling — body bytes, field count, field length, requests per IP, and
# in-flight forwarding threads.
TELEMETRY_MAX_BODY_BYTES = 8 * 1024  # ~40x the largest real beacon
TELEMETRY_MAX_PROPS = 16
TELEMETRY_MAX_INFLIGHT = 8  # concurrent PostHog forwards, hard ceiling

_telemetry_pool: Any = None
_telemetry_pool_lock = threading.Lock()
_telemetry_slots = threading.BoundedSemaphore(TELEMETRY_MAX_INFLIGHT)


def _get_telemetry_pool():
    """Lazily build the bounded forwarding pool (only if a key is set)."""
    global _telemetry_pool
    if _telemetry_pool is None:
        with _telemetry_pool_lock:
            if _telemetry_pool is None:
                from concurrent.futures import ThreadPoolExecutor

                _telemetry_pool = ThreadPoolExecutor(
                    max_workers=2, thread_name_prefix="mq-telemetry"
                )
    return _telemetry_pool


def _forward_telemetry_posthog(
    event: str,
    session_id: str,
    path: str,
    props: dict,
) -> str:
    """OPT-IN server-side forward to PostHog (EU host by default).

    No-op unless the deployment operator sets POSTHOG_API_KEY, so a default
    or self-hosted install never sends telemetry anywhere (stdout log only). Runs off the event loop -- the beacon route
    is async and a blocking HTTP call would starve it. Server-side capture,
    no cookies: stays inside the privacy page's consent promise.

    Concurrency is BOUNDED (2026-07-25 audit): this used to spawn one raw
    daemon thread per beacon, so with the key set a flood of forged events
    minted unbounded threads against a 512 MB instance. Work now goes to a
    2-worker pool behind an 8-slot semaphore; beyond that beacons are dropped
    rather than queued, because telemetry must never be able to push real
    request handling off the box. Returns the disposition for tests/logs.
    """
    api_key = os.environ.get("POSTHOG_API_KEY")
    if not api_key:
        return "disabled"
    host = os.environ.get("POSTHOG_HOST", "https://eu.i.posthog.com").rstrip("/")

    if not _telemetry_slots.acquire(blocking=False):
        return "dropped_backpressure"

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
        finally:
            _telemetry_slots.release()

    try:
        _get_telemetry_pool().submit(_post)
    except Exception:  # noqa: BLE001 -- pool creation/submit must never 500
        _telemetry_slots.release()
        return "dropped_error"
    return "queued"


@app.post(
    "/api/telemetry/event",
    dependencies=[Depends(rate_limit("telemetry", 60, 60.0))],
)
async def telemetry_event(request: Request):
    """Log one anonymous client telemetry event. Always 200 — telemetry
    must never surface as a user-facing error.

    Per-IP rate limited and body-capped: the funnel events this writes
    (`signup_completed`, `sim_run_success`, …) are the numbers the roadmap
    reads, and an unfused writer lets anyone manufacture them.

    The body is read off the stream with a running ceiling rather than
    declared as a `dict` parameter — FastAPI would have parsed the whole
    thing before the handler could object.
    """
    total = 0
    chunks: list[bytes] = []
    try:
        async for chunk in request.stream():
            total += len(chunk)
            if total > TELEMETRY_MAX_BODY_BYTES:
                return {"ok": True, "dropped": "payload_too_large"}
            chunks.append(chunk)
        payload = json.loads(b"".join(chunks) or b"null")
    except Exception:  # noqa: BLE001 -- malformed beacons are dropped, not 4xx'd
        return {"ok": True, "dropped": "malformed"}
    if not isinstance(payload, dict):
        return {"ok": True}
    event = str(payload.get("event", ""))[:64] or "unknown"
    session_id = str(payload.get("session_id", ""))[:64]
    props = payload.get("props") if isinstance(payload.get("props"), dict) else {}
    safe_props = {
        str(k)[:64]: (str(v)[:200] if isinstance(v, str) else v)
        for k, v in list(props.items())[:TELEMETRY_MAX_PROPS]
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
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    request: Request = None,
):
    def _build():
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
            raise _server_error("Database error", exc)

    return _serve_catalog(
        request, ("bikes", search, manufacturer, category, limit, offset), _build
    )


@app.get("/api/bikes/{bike_id}")
def get_bike(bike_id: int = Path(..., ge=1, le=MAX_DB_ID), request: Request = None):
    def _build():
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
            raise _server_error("Database error", exc)

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
                    # stroke_type feeds the bike page's JSON-LD (2-strokes were
                    # all published as "4-stroke" without it).
                    for k in (
                        "redline_rpm",
                        "cylinder_count",
                        "cylinder_config",
                        "stroke_type",
                    ):
                        v = engine.get(k)
                        if v is not None and d.get(k) in (None, ""):
                            d[k] = v
                if aero:
                    for k in ("cd", "frontal_area_m2"):
                        v = aero.get(k)
                        if v is not None:
                            d[k] = v
                if drive:
                    for k in (
                        "front_sprocket",
                        "rear_sprocket",
                        "chain_pitch",
                        "gear_ratios",
                    ):
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

    return _serve_catalog(request, ("bike", bike_id), _build)


@app.get("/api/venues")
def list_venues(request: Request = None):
    def _build():
        db = _get_db()
        if not db:
            raise HTTPException(503, "Database unavailable")
        try:
            rows = db.execute("SELECT * FROM venues ORDER BY country, name").fetchall()
            venues = []
            for r in rows:
                v = dict(r)
                # Same name and normalisation as the ``environment`` echo of
                # the sim routes: the surface that venue is simulated on.
                v["track_surface"] = (v.get("surface_type") or "asphalt").lower()
                venues.append(v)
            return {"venues": venues}
        except Exception as exc:
            raise _server_error("Database error", exc)

    return _serve_catalog(request, ("venues",), _build)


@app.get("/api/tires")
def list_tires(
    compound: str | None = Query(None),
    manufacturer: str | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    request: Request = None,
):
    def _build():
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
            raise _server_error("Database error", exc)

    return _serve_catalog(request, ("tires", compound, manufacturer, limit), _build)


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
            **_conditions_kwargs(req),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    parts_skipped: list[int] = []
    parts_skipped_detail: list[SkippedPartDict] = []
    cfg, parts_applied, build_cost_inr = _apply_parts_to_config(
        cfg,
        req.part_ids,
        skipped=parts_skipped,
        skipped_detail=parts_skipped_detail,
        bike_id=req.bike_id,
        bike_preset=req.bike_preset,
    )

    try:
        engine = engine_select.make_engine(cfg)
        sim = engine.run(
            use_adaptive_dt=req.use_adaptive_dt,
            progress_cb=(lambda f: progress(f, "Integrating physics"))
            if progress is not None
            else None,
        )
    except Exception as exc:
        raise _server_error("Simulation error", exc)
    _require_finish(sim)

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
        "environment": _environment_echo(cfg),
        "parts_applied": parts_applied,
        "parts_skipped": parts_skipped,
        "parts_skipped_detail": parts_skipped_detail,
        "build_cost_inr": round(build_cost_inr, 0),
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
            # SimResult.traction_pct is already a 0-100 percentage.
            "traction_pct": _safe_array(sim.traction_pct, lambda v: round(float(v), 1)),
            "tire_temp_c": _safe_array(sim.T_tire, lambda v: round(float(v), 1)),
            "power_kw": _safe_array(sim.power_kw, lambda v: round(float(v), 1)),
            "F_drive_N": _safe_array(sim.F_drive, lambda v: round(float(v), 0)),
            "F_drag_N": _safe_array(sim.F_drag, lambda v: round(float(v), 0)),
        },
    }


@app.post(
    "/api/simulate",
    dependencies=[
        # Cost fuse (2026-08-11 hardening): every route here is anonymous and
        # free, so without a limit one loop could run unlimited full RK4
        # sims on the shared instance. 30/60s is generous for human-paced UI
        # use and fatal to loops. Bucket shared with /api/jobs/simulate — the
        # client falls back between the two (deploy-skew contract), so a
        # split bucket would double the effective limit.
        Depends(rate_limit("simulate", 30, 60.0)),
    ],
)
def simulate(req: SimulateRequest):
    """Synchronous full simulation (see ``_simulate_impl``)."""
    return _simulate_impl(req)


@app.post(
    "/api/simulate/quick",
    # Rate-limited on its OWN bucket (the slider UI auto-runs it, so it must
    # never drain the full-sim budget). The limit exists because each call
    # is still a full RK4 pass (~50-100 ms CPU; TWO passes with part_ids),
    # and the route previously had no fuse at all (2026-08-11 hardening).
    # Live-mode drags answer client-side now, so 30/60s covers real use.
    dependencies=[Depends(rate_limit("quick_sim", 30, 60.0))],
)
def simulate_quick(req: QuickSimRequest) -> QuickSimResultDict:
    """
    Quick ET-only simulation -- no time-series arrays.
    Returns in ~50 ms; ideal for slider-driven UI.
    """
    # Read the catalog freshness token BEFORE loading the bike: a catalog write
    # that lands between the two must not file the old baseline under the new
    # token (the catalog cache reads its token first for the same reason).
    stock_key = _stock_key(req)
    # A named place resolves to live weather, which the key cannot capture,
    # so its baseline is never served from (or written to) the cache.
    live_place = bool(req.location) or (req.lat is not None and req.lon is not None)
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
            **_conditions_kwargs(req),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    # The pre-parts config is the stock baseline. apply_part_to_config returns
    # a new config, so ``base_cfg`` stays stock; the baseline therefore runs in
    # exactly the conditions this request resolved (no second weather lookup).
    base_cfg = cfg

    # Apply selected parts
    parts_skipped: list[int] = []
    parts_skipped_detail: list[SkippedPartDict] = []
    cfg, parts_applied, build_cost_inr = _apply_parts_to_config(
        cfg,
        req.part_ids,
        skipped=parts_skipped,
        skipped_detail=parts_skipped_detail,
        bike_id=req.bike_id,
        bike_preset=req.bike_preset,
    )

    # Run stock sim for comparison if parts are applied
    # "Stock" means same slider overrides but NO parts -- shows parts-only delta
    stock_et = None
    if parts_applied:
        stock_et = None if live_place else _stock_cache_get(stock_key)
        if stock_et is None:
            try:
                stock_sim = engine_select.make_engine(copy.deepcopy(base_cfg)).run()
                if not getattr(stock_sim, "finished_quarter", True):
                    raise ValueError("stock baseline did not finish")
                stock_et = round(float(stock_sim.time_quarter), 4)
                if not live_place:
                    _stock_cache_put(stock_key, stock_et)
            except Exception:
                # Baseline comparison is optional; stock_et stays None and the
                # response simply omits the stock delta.
                pass

    try:
        engine = engine_select.make_engine(cfg)
        sim = engine.run()
    except Exception as exc:
        raise _server_error("Simulation error", exc)
    _require_finish(sim)

    result: QuickSimResultDict = {
        "tyres": _tyre_labels(req.front_tire_id, req.rear_tire_id),
        "et_quarter_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * 3.6, 2),
        "et_60ft_s": round(float(sim.time_60ft), 4),
        "et_eighth_s": round(float(sim.time_eighth), 4),
        "bike_name": cfg.name,
        "peak_power_hp": round(float(cfg.engine.peak_power_hp), 1),
        "total_mass_kg": round(float(cfg.chassis.total_mass_kg), 1),
        "parts_applied": parts_applied,
        "parts_skipped": parts_skipped,
        "parts_skipped_detail": parts_skipped_detail,
        "environment": _environment_echo(cfg),
        "build_cost_inr": round(build_cost_inr, 0),
        "stock_et_s": stock_et,
        "et_delta_s": round(float(sim.time_quarter) - stock_et, 4)
        if stock_et
        else None,
    }
    if not parts_applied and not live_place:
        # No parts changed the config, so this run IS the stock baseline.
        _stock_cache_put(stock_key, result["et_quarter_s"])
    return result


class TopSpeedRequest(ConditionsRequest):
    """POST /api/simulate/top-speed — runs until terminal velocity."""

    bike_id: DbId | None = None
    bike_preset: str | None = None
    power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    rider_mass_kg: float = Field(75.0, ge=20.0, le=250.0)
    # Same cap rationale as QuickSimRequest.part_ids (2026-08-11 hardening).
    part_ids: list[DbId] = Field(default_factory=list, max_length=30)
    front_tire_id: DbId | None = None
    rear_tire_id: DbId | None = None
    headwind_kmh: float | None = Field(None, ge=-200, le=200)
    # LSR-specific: optional override for max time/distance.
    # Bounded: n_max preallocates 18 float64 arrays of max_time_s/dt slots
    # (they grow on demand only under adaptive dt), so an unbounded value is
    # a remotely-triggerable memory bomb. Floor at 0.1 s: a max_time below
    # the solver dt raised an unhandled ValueError deep in the engine
    # (found July 11, 2026 review) — reject it at validation instead.
    # Ceiling 120 s (2026-08-11 hardening): le=300 meant ~43 MB of upfront
    # numpy allocation per fixed-dt sim on the 512 MB instance. Top-speed
    # plateaus detect at ~35 s, so 120 leaves 3x headroom (~17 MB ceiling).
    # DistanceRunRequest keeps le=300 — a 20 km LSR run genuinely needs it.
    max_time_s: float = Field(120.0, ge=0.1, le=120.0)
    include_timeseries: bool = False


# Upper bound on plotted points in the top-speed timeseries. The web chart draws
# one curve; ~2,000 points is far beyond what a chart can resolve, whereas the
# native 100 Hz stream of a 120 s run is ~12,000 points x 7 series.
TOPSPEED_MAX_SERIES_POINTS = 2000


def _topspeed_timeseries(sim) -> TopSpeedTimeseriesDict:
    """Plot-ready top-speed series: 100 Hz source, decimated and rounded.

    Keeps the first sample, the last sample and the peak-speed sample, spreads
    the rest evenly, and rounds each channel to the precision a chart can show.
    Scalar results are computed from the full-resolution run elsewhere and are
    not derived from this series.
    """
    import numpy as np

    stride = max(1, int(0.01 / max(sim.dt, 0.0001)))
    t = np.asarray(sim.t[::stride])
    n = len(t)
    if n > TOPSPEED_MAX_SERIES_POINTS:
        # One slot is reserved for the peak-speed sample, which rarely lands
        # on the even grid: without it the series came out one point over the
        # cap (2,001) whenever the peak was off-grid.
        keep = set(
            np.linspace(0, n - 1, TOPSPEED_MAX_SERIES_POINTS - 1).astype(int).tolist()
        )
        keep.add(int(np.argmax(np.asarray(sim.v[::stride]))))
        idx = np.array(sorted(keep), dtype=int)
    else:
        idx = np.arange(n)

    def pick(arr):
        return np.asarray(arr[::stride])[idx]

    v = pick(sim.v)
    return {
        "t": np.round(pick(sim.t), 3).tolist(),
        "v_ms": np.round(v, 3).tolist(),
        "v_kmh": np.round(v * 3.6, 2).tolist(),
        "rpm": np.round(pick(sim.rpm), 0).tolist(),
        "gear": pick(sim.gear).astype(int).tolist(),
        "power_kw": np.round(pick(sim.power_kw), 2).tolist(),
        "x_m": np.round(pick(sim.x), 2).tolist(),
    }


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
            **_conditions_kwargs(req),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    parts_skipped: list[int] = []
    parts_skipped_detail: list[SkippedPartDict] = []
    cfg, parts_applied, build_cost_inr = _apply_parts_to_config(
        cfg,
        req.part_ids,
        skipped=parts_skipped,
        skipped_detail=parts_skipped_detail,
        bike_id=req.bike_id,
        bike_preset=req.bike_preset,
    )

    try:
        engine = engine_select.make_engine(cfg)
        ts = engine.run_top_speed(
            max_time=req.max_time_s,
            progress_cb=(lambda f: progress(f, "Running to terminal velocity"))
            if progress is not None
            else None,
        )
    except Exception as exc:
        raise _server_error("Top-speed simulation error", exc)

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
        "parts_skipped": parts_skipped,
        "parts_skipped_detail": parts_skipped_detail,
        "environment": _environment_echo(cfg),
        "build_cost_inr": round(build_cost_inr, 0),
    }

    if req.include_timeseries:
        response["timeseries"] = _topspeed_timeseries(ts.full_sim)

    return response


@app.post(
    "/api/simulate/top-speed",
    dependencies=[
        # Same cost-fuse rationale as /api/simulate (2026-08-11 hardening);
        # bucket shared with /api/jobs/topspeed.
        Depends(rate_limit("topspeed", 30, 60.0)),
    ],
)
def simulate_top_speed(req: TopSpeedRequest) -> TopSpeedResultDict:
    """Synchronous top-speed simulation (see ``_topspeed_impl``)."""
    return _topspeed_impl(req)


class DistanceRunRequest(ConditionsRequest):
    """POST /api/simulate/distance — arbitrary distance for LSR events."""

    bike_id: DbId | None = None
    bike_preset: str | None = None
    # gt=ROLLOUT_M: the run is timed from the start beam, 1 ft from rest, so
    # a target at/before it has no timed distance (run() raises ValueError).
    distance_m: float = Field(
        ..., gt=ROLLOUT_M, le=20000, description="Target distance in meters"
    )
    power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    rider_mass_kg: float = Field(75.0, ge=20.0, le=250.0)
    # Same cap rationale as QuickSimRequest.part_ids (2026-08-11 hardening).
    part_ids: list[DbId] = Field(default_factory=list, max_length=30)
    front_tire_id: DbId | None = None
    rear_tire_id: DbId | None = None
    headwind_kmh: float | None = Field(None, ge=-200, le=200)
    # Same floor rationale as TopSpeedRequest.max_time_s (>= dt). Ceiling
    # DELIBERATELY stays at 300 (not the 2026-08-11 le=120 top-speed cap):
    # distance_m allows up to 20 km, and a Bonneville-course run at ~80 m/s
    # legitimately needs >120 s of sim time to reach the line.
    max_time_s: float = Field(120.0, ge=0.1, le=300.0)


@app.post(
    "/api/simulate/distance",
    # Cost fuse — the HEAVIEST sim route (up to 20 km / 300 s of sim time,
    # ~2.5x the top-speed ceiling). Its only protection used to be the
    # sim-quota meter, so it gets its own, tighter bucket now that every
    # route is free (open-source pivot, 2026-10-23). No job variant exists,
    # so there is no deploy-skew bucket to share.
    dependencies=[Depends(rate_limit("distance", 10, 60.0))],
)
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
            **_conditions_kwargs(req),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config error: {exc}")

    # Apply parts (distance run doesn't surface parts_applied/cost in its
    # response, but the helper handles that consistently).
    parts_skipped: list[int] = []
    parts_skipped_detail: list[SkippedPartDict] = []
    cfg, _, _ = _apply_parts_to_config(
        cfg,
        req.part_ids,
        skipped=parts_skipped,
        skipped_detail=parts_skipped_detail,
        bike_id=req.bike_id,
        bike_preset=req.bike_preset,
    )

    try:
        engine = engine_select.make_engine(cfg)
        sim = engine.run_distance(req.distance_m, max_time=req.max_time_s)
    except Exception as exc:
        raise _server_error("Distance run error", exc)

    # A degenerate config can return an empty trajectory; indexing sim.t[-1] /
    # max(sim.v) below would then raise outside the try above and 500. Surface a
    # clean 422 instead.
    if len(sim.t) == 0 or len(sim.v) == 0:
        raise HTTPException(
            422,
            "Simulation produced no trajectory for this configuration "
            "(check mass / power / distance inputs).",
        )

    # Terminal/trap values at the target distance, timed from the start beam
    # with the same rollout convention as every other split (2026-10 epoch,
    # SimResult.split_at). A run that never got there (time cap) reports its
    # last sample, as before.
    hit = sim.split_at(req.distance_m)
    if hit is not None:
        trap_time = float(hit[0])
        trap_v = float(hit[1])
    else:
        trap_time = float(sim.t[-1])
        trap_v = float(sim.v[-1])

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
        "parts_skipped": parts_skipped,
        "parts_skipped_detail": parts_skipped_detail,
        "environment": _environment_echo(cfg),
    }
    return result


@app.get("/api/parts/categories")
def list_parts_categories(request: Request = None):
    """Return all parts categories."""

    def _build():
        db = _get_db()
        if not db:
            raise HTTPException(503, "Database unavailable")
        try:
            rows = db.execute(
                "SELECT * FROM parts_categories ORDER BY display_name"
            ).fetchall()
            return {"categories": [dict(r) for r in rows]}
        except Exception as exc:
            raise _server_error("Database error", exc)

    return _serve_catalog(request, ("parts_categories",), _build)


@app.get("/api/parts")
def list_parts(
    category: str | None = Query(None, description="Filter by category name"),
    category_id: int | None = Query(
        None, ge=1, le=MAX_DB_ID, description="Filter by category ID"
    ),
    bike_id: int | None = Query(
        None, ge=1, le=MAX_DB_ID, description="Show compatibility for this bike"
    ),
    bike_preset: str | None = Query(
        None,
        max_length=64,
        description="Reference preset (gsxr1000_k5 | yzfr1_4c8 | hayabusa_gen1) to "
        "judge compatibility by, when no bike_id is given: its catalog row is "
        "used, exactly as the sim routes do for a preset request.",
    ),
    compatible_only: bool = Query(
        True,
        description="When bike_id is set: if True (default) only return compatible "
        "parts; if False, return all parts with a 'compatible' + 'fitment_reason' "
        "annotation per row.",
    ),
    search: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    fields: str | None = Query(
        None,
        pattern="^id$",
        description="'id' returns only the matching part ids "
        '({"part_ids": [...], "total", "bike_id", "compatible_only"}) instead of '
        "full rows — use with bike_id + compatible_only to learn which catalog "
        "parts fit a bike without re-downloading the catalog.",
    ),
    include_rules: bool = Query(
        False,
        description="Include each part's raw 'fitment_rules' and 'specifications' "
        "JSON (omitted by default: they are ~25% of the list payload and the "
        "compatibility verdict is already in 'compatible'/'fitment_reason').",
    ),
    request: Request = None,
):
    """Return parts catalog, optionally filtered by category and bike compatibility.

    ``total`` in the response is the number of MATCHING parts (after category /
    search / compatibility filtering, before ``limit`` slicing) so paginating
    callers can detect truncation. Cap is 5000 (the catalog is a few hundred parts).

    When ``bike_id`` (or, without one, ``bike_preset``) is provided, each
    returned part is evaluated against the
    bike's fitment rules (stroke_type, manufacturer, engine_config, displacement,
    chain_pitch). Set ``compatible_only=false`` to receive every part with an
    annotation instead of a hard filter (useful for the Streamlit/Next.js UI
    which greys-out incompatible options).
    """
    # Direct (non-HTTP) callers omit params, so FastAPI's Query defaults arrive
    # as Query objects; only a real value counts.
    ids_only = isinstance(fields, str) and fields == "id"
    with_rules = include_rules is True
    preset = bike_preset if isinstance(bike_preset, str) and bike_preset else None
    requested_bike_id = bike_id

    def _build():
        db = _get_db()
        if not db:
            raise HTTPException(503, "Database unavailable")
        # A preset stands for its catalog row (see _parts_model_id), so the
        # list a preset request gets is the list the sim routes will accept.
        bike_id = requested_bike_id
        if bike_id is None and preset is not None:
            if preset not in _PRESETS:
                raise HTTPException(404, f"Unknown bike_preset: {preset}")
            bike_id = _parts_model_id(db, None, preset)
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
                # Compatibility filtering happens in Python below -- applying the
                # SQL LIMIT first silently starved brands late in the sort order
                # (June 11 QA / parts-audit handoff). Fetch all, filter, then slice.
                sql_total = None

            rows = db.execute(query, params).fetchall()

            # -- Bike compatibility annotation / filter -----------------------
            bike_row: dict | None = None
            if bike_id is not None:
                from .database.parts_repo import enrich_bike_row_for_fitment

                raw = db.execute(
                    "SELECT * FROM bike_models WHERE id = ?", (bike_id,)
                ).fetchone()
                if raw is None:
                    raise HTTPException(404, f"Bike {bike_id} not found")
                bike_row = dict(raw)
                enrich_bike_row_for_fitment(db, bike_row)

            from .parts.compatibility import is_compatible

            parts = []
            for r in rows:
                d = dict(r)
                # Evaluate compatibility BEFORE parsing JSON fields in-place
                # (is_compatible expects the raw fitment_rules JSON string).
                if bike_row is not None:
                    compat, reason = is_compatible(d, bike_row)
                    if compatible_only and not compat:
                        continue
                    d["compatible"] = bool(compat)
                    d["fitment_reason"] = reason

                if ids_only:
                    parts.append(d["id"])
                    continue

                if not with_rules:
                    d.pop("fitment_rules", None)
                    d.pop("specifications", None)

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

            out = {
                "parts": parts,
                "total": total,
                "bike_id": bike_id,
                "compatible_only": bool(bike_id is not None and compatible_only),
            }
            if ids_only:
                out["part_ids"] = out.pop("parts")
            return out
        except HTTPException:
            raise
        except Exception as exc:
            raise _server_error("Database error", exc)

    return _serve_catalog(
        request,
        (
            "parts",
            category,
            category_id,
            bike_id,
            preset,
            bool(compatible_only),
            search,
            limit,
            ids_only,
            with_rules,
        ),
        _build,
    )


# --- A vs B Comparison ---------------------------------------------------


class CompareRequest(ConditionsRequest):
    """POST /api/simulate/compare - two builds side-by-side."""

    # Build A (baseline)
    a_bike_id: DbId | None = None
    a_bike_preset: str | None = None
    a_power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    a_mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    a_rider_mass_kg: float = Field(75.0, ge=20.0, le=250.0)
    # Same cap rationale as QuickSimRequest.part_ids (2026-08-11 hardening).
    a_part_ids: list[DbId] = Field(default_factory=list, max_length=30)
    a_front_tire_id: DbId | None = None
    a_rear_tire_id: DbId | None = None

    # Build B (modified)
    b_bike_id: DbId | None = None
    b_bike_preset: str | None = None
    b_power_boost_pct: float = Field(0.0, ge=-50.0, le=200.0)
    b_mass_delta_kg: float = Field(0.0, ge=-100.0, le=200.0)
    b_rider_mass_kg: float = Field(75.0, ge=20.0, le=250.0)
    b_part_ids: list[DbId] = Field(default_factory=list, max_length=30)
    b_front_tire_id: DbId | None = None
    b_rear_tire_id: DbId | None = None

    # Shared conditions
    headwind_kmh: float | None = Field(None, ge=-200, le=200)


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
    conditions: dict | None = None,
):
    """Build config, apply parts, run sim; return (sim, cfg, parts_applied,
    cost, parts_skipped, parts_skipped_detail).

    ``conditions`` carries the ConditionsRequest-only fields (see
    :func:`_conditions_kwargs`)."""
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
        **(conditions or {}),
    )
    parts_skipped: list[int] = []
    parts_skipped_detail: list[SkippedPartDict] = []
    cfg, parts_applied, build_cost = _apply_parts_to_config(
        cfg,
        part_ids,
        include_price_in_summary=False,
        skipped=parts_skipped,
        skipped_detail=parts_skipped_detail,
        bike_id=bike_id,
        bike_preset=bike_preset,
    )

    sim = engine_select.make_engine(cfg).run(progress_cb=progress_cb)
    return sim, cfg, parts_applied, build_cost, parts_skipped, parts_skipped_detail


def _build_summary(
    sim,
    cfg,
    parts_applied,
    build_cost,
    label,
    include_timeseries=True,
    parts_skipped=(),
    parts_skipped_detail=(),
):
    """Create a response dict from a sim run."""
    _require_finish(sim, label)
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
        "parts_skipped": list(parts_skipped),
        "parts_skipped_detail": list(parts_skipped_detail),
        "build_cost_inr": round(build_cost, 0),
    }
    if include_timeseries:
        result["timeseries"] = {
            "t_s": _sa(sim.t, lambda v: round(float(v), 4)),
            "v_kmh": _sa(sim.v, lambda v: round(float(v) * 3.6, 2)),
            "rpm": _sa(sim.rpm, lambda v: round(float(v), 0)),
            "gear": _sa(sim.gear, lambda v: int(v)),
            "accel_g": _sa(sim.a, lambda v: round(float(v) / 9.81, 3)),
            "traction_pct": _sa(sim.traction_pct, lambda v: round(float(v), 1)),
            "power_kw": _sa(sim.power_kw, lambda v: round(float(v), 1)),
        }
    return result


def _same_build(req: CompareRequest) -> bool:
    """True when builds A and B are defined by identical inputs."""

    def norm(pids):  # repeated ids are applied once, in first-seen order
        return tuple(dict.fromkeys(pids))

    return (
        req.a_bike_id == req.b_bike_id
        and req.a_bike_preset == req.b_bike_preset
        and req.a_power_boost_pct == req.b_power_boost_pct
        and req.a_mass_delta_kg == req.b_mass_delta_kg
        and req.a_rider_mass_kg == req.b_rider_mass_kg
        and norm(req.a_part_ids) == norm(req.b_part_ids)
        and req.a_front_tire_id == req.b_front_tire_id
        and req.a_rear_tire_id == req.b_rear_tire_id
    )


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
        sim_a, cfg_a, parts_a, cost_a, skipped_a, why_a = _run_build(
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
            conditions=_conditions_kwargs(req),
        )
        if progress is not None:
            progress(0.5, "Simulating build B")
        if _same_build(req):
            # Identical inputs give an identical (deterministic) run: reuse A's
            # result for B instead of integrating the same trajectory twice.
            sim_b, cfg_b, parts_b, cost_b, skipped_b, why_b = (
                sim_a,
                cfg_a,
                parts_a,
                cost_a,
                skipped_a,
                why_a,
            )
            if progress is not None:
                progress(0.98, "Simulating build B")
        else:
            sim_b, cfg_b, parts_b, cost_b, skipped_b, why_b = _run_build(
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
                conditions=_conditions_kwargs(req),
            )
    except HTTPException:
        raise  # e.g. 404 for an unknown bike_id — don't relabel as 500
    except Exception as exc:
        raise _server_error("Simulation error", exc)

    if progress is not None:
        progress(0.99, "Building comparison")
    a = _build_summary(
        sim_a,
        cfg_a,
        parts_a,
        cost_a,
        "A",
        parts_skipped=skipped_a,
        parts_skipped_detail=why_a,
    )
    b = _build_summary(
        sim_b,
        cfg_b,
        parts_b,
        cost_b,
        "B",
        parts_skipped=skipped_b,
        parts_skipped_detail=why_b,
    )

    delta_et = round(b["et_quarter_s"] - a["et_quarter_s"], 4)
    delta_trap = round(b["trap_speed_kmh"] - a["trap_speed_kmh"], 2)

    return {
        "a": a,
        "b": b,
        "environment": _environment_echo(cfg_a),
        "delta": {
            "et_s": delta_et,
            "trap_kmh": delta_trap,
            "faster": "B" if delta_et < 0 else "A" if delta_et > 0 else "tie",
            "cost_diff_inr": round(cost_b - cost_a, 0),
        },
    }


# Cost fuse for both compare routes. Each call runs TWO full RK4 passes, and
# the sim-quota meter used to be their only protection — so they get a
# tighter bucket than single-sim routes (15/60 s = 30 full sims/min, the
# same CPU ceiling as /api/simulate). ONE shared bucket: the web client
# falls back between /api/simulate/compare and /api/jobs/compare
# (deploy-skew contract), so a split bucket would double the effective
# limit. Pinned by tests/test_public_route_fuses.py.
_rl_compare = rate_limit("compare", 15, 60.0)


@app.post(
    "/api/simulate/compare",
    dependencies=[Depends(_rl_compare)],
)
def simulate_compare(req: CompareRequest):
    """Run two builds side-by-side and return full results for both.

    Rate-limited on the shared ``compare`` bucket (see ``_rl_compare``).
    """
    return _compare_impl(req)


# ─────────────────────────────────────────────────────────────────────────
# Upload size cap
# ─────────────────────────────────────────────────────────────────────────
# Both calibration routes used to do a bare `await file.read()`, materialising
# the entire body as one bytes object with no ceiling (2026-07-25 audit).
# Starlette spools a large part to a temp file, but `.read()` pulls all of it
# back into memory and it is then written to a SECOND temp file — so a single
# unauthenticated POST of a few hundred MB is an OOM kill plus a disk fill on
# the 512 MB Render instance. Both routes are anonymous, so nothing upstream
# of this cap stops such a body.
#
# 25 MB is ~100x the largest realistic Dragy/dyno export, which are text CSVs
# of a few hundred KB.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


async def _read_upload_capped(file: UploadFile) -> bytes:
    """Read an UploadFile, refusing anything over MAX_UPLOAD_BYTES.

    Reads in chunks so an oversized body is rejected without ever being fully
    held in memory — reading first and checking len() afterwards would already
    have done the damage.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                413,
                detail={
                    "error": "upload_too_large",
                    "message": (
                        f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB "
                        "limit. Dragy and dyno exports are text files of a few "
                        "hundred KB."
                    ),
                    "max_bytes": MAX_UPLOAD_BYTES,
                },
            )
        chunks.append(chunk)
    return b"".join(chunks)


# --- Dragy / Dyno Upload -------------------------------------------------


@app.post(
    "/api/calibrate/dragy",
    # These uploads are anonymous and each one parses up to 25 MB in memory
    # (2026-08-11 hardening). 6/60s is plenty for a human uploading
    # timeslips; a loop gets cut off fast.
    dependencies=[Depends(rate_limit("calibrate_upload", 6, 60.0))],
)
async def upload_dragy(
    file: UploadFile = File(..., description="Dragy CSV or JSON export"),
    bike_id: int | None = Form(
        None, ge=1, le=MAX_DB_ID, description="Bike to overlay sim against"
    ),
    bike_preset: str | None = Form(None),
):
    """
    Upload a Dragy GPS file, parse it, and optionally overlay against simulation.
    Returns parsed run data (ET, trap, splits, v(t)) and if a bike is specified,
    also runs a sim and returns the comparison overlay.
    """
    log = logging.getLogger(__name__)

    try:
        content = await _read_upload_capped(file)
        suffix = (
            ".json" if file.filename and file.filename.endswith(".json") else ".csv"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except HTTPException:
        # Pass through the 413 from _read_upload_capped — a bare
        # `except Exception` here would remask it as a generic 400 and hide
        # the real reason from the client.
        raise
    except Exception as exc:
        raise HTTPException(400, f"Failed to read upload: {_without_paths(exc)}")

    try:
        from .calibration.dragy import best_run as dragy_best, parse_dragy_file

        # to_thread: this route is async, so a blocking parse would starve
        # the single event loop (incl. /api/jobs polling) on the 0.5-CPU tier.
        runs = await asyncio.to_thread(parse_dragy_file, tmp_path)
    except Exception as exc:
        log.warning("Dragy parse error: %s", exc)
        raise HTTPException(422, f"Failed to parse Dragy file: {_without_paths(exc)}")
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
            # rollout_m=0.0: the Dragy parser times the real run from its
            # first-motion frame, so the overlay sim uses the same convention.
            sim = await asyncio.to_thread(
                engine_select.make_engine(cfg).run, rollout_m=0.0
            )
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


@app.post(
    "/api/calibrate/dyno",
    # Same upload-fuse rationale as /api/calibrate/dragy; shared bucket so
    # alternating the two routes doesn't double the effective limit.
    dependencies=[Depends(rate_limit("calibrate_upload", 6, 60.0))],
)
async def upload_dyno(
    file: UploadFile = File(
        ..., description="Dyno CSV export (DynoJet, generic, or MoTeC)"
    ),
    temp_c: float | None = Form(None, description="Ambient temperature during run [C]"),
    pressure_kpa: float | None = Form(None, description="Barometric pressure [kPa]"),
    rh_pct: float = Form(0.0, description="Relative humidity [%]"),
):
    """Upload a dyno CSV, parse it with SAE J1349 correction, return power/torque curve."""
    log = logging.getLogger(__name__)

    try:
        content = await _read_upload_capped(file)
        suffix = ".txt" if file.filename and file.filename.endswith(".txt") else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except HTTPException:
        # Pass through the 413 from _read_upload_capped — a bare
        # `except Exception` here would remask it as a generic 400 and hide
        # the real reason from the client.
        raise
    except Exception as exc:
        raise HTTPException(400, f"Failed to read upload: {_without_paths(exc)}")

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
        raise HTTPException(422, f"Failed to parse dyno file: {_without_paths(exc)}")
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

    model_config = ConfigDict(json_schema_extra={"example": {"location": "Pune, IN"}})


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


# Upstream HTTP errors (requests' HTTPError / ConnectionError messages) embed
# the full request URL — including `appid=<key>` — so any error text that
# came from an outbound call must pass through this before it is logged or
# returned. 2026-10-24: /api/venues/resolve echoed the OWM key in its 502.
_SECRET_QUERY_RE = re.compile(
    r"(?i)\b(appid|api_?key|access_token|token|key)=([^&\s'\"<>]+)"
)


def _redact_secrets(text: object, *secrets: str | None) -> str:
    """Remove every given secret value and any ``appid=``/``key=``-style query
    parameter value from ``text``."""
    out = str(text)
    for secret in secrets:
        if secret:
            out = out.replace(secret, "[REDACTED]")
    return _SECRET_QUERY_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", out)


# Successful weather lookups are reused for ten minutes. Every simulation
# route accepts a place now, and the site's Live mode re-posts on every slider
# change; without this one visitor could spend the shared upstream allowance.
_OWM_CACHE_TTL_S = 600.0
_OWM_CACHE_MAX = 256
_owm_cache: "OrderedDict[tuple, tuple[float, dict]]" = OrderedDict()
_owm_cache_lock = threading.Lock()


def _fetch_owm_for_location(
    *,
    location: str | None,
    lat: float | None,
    lon: float | None,
    altitude_m: float | None,
) -> dict | None:
    """Cached front of :func:`_fetch_owm_uncached` (errors are never cached)."""
    key = (
        (location or "").strip().lower() or None,
        None if lat is None else round(float(lat), 2),
        None if lon is None else round(float(lon), 2),
        altitude_m,
    )
    now = _time.monotonic()
    with _owm_cache_lock:
        hit = _owm_cache.get(key)
        if hit is not None and now - hit[0] < _OWM_CACHE_TTL_S:
            _owm_cache.move_to_end(key)
            return dict(hit[1])
    result = _fetch_owm_uncached(
        location=location, lat=lat, lon=lon, altitude_m=altitude_m
    )
    if isinstance(result, dict) and "_error" not in result:
        # Stamp the fetch here so a cached reading keeps the time it was
        # actually fetched, rather than the time it was served.
        result = {"fetched_at": datetime.now(timezone.utc).isoformat(), **result}
        with _owm_cache_lock:
            _owm_cache[key] = (now, dict(result))
            _owm_cache.move_to_end(key)
            while len(_owm_cache) > _OWM_CACHE_MAX:
                _owm_cache.popitem(last=False)
    return result


def _fetch_owm_uncached(
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
        # No key: Open-Meteo needs none. MOTOQUANT_OPEN_METEO=0 turns the
        # fallback off (the test suite does, so it never hits the network).
        if os.environ.get("MOTOQUANT_OPEN_METEO", "1").strip() == "0":
            return {"_error": "no_api_key"}
        return _fetch_open_meteo_uncached(
            location=location, lat=lat, lon=lon, altitude_m=altitude_m
        )

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
            # The place is visitor input: log how it was given, not what it was.
            "OWM fetch failed (by=%s): %s",
            "coords" if lat is not None and lon is not None else "name",
            _redact_secrets(f"{type(exc).__name__}: {exc}", api_key),
        )
        # The client gets a coarse, key-free reason only (status code or
        # exception class) — never the upstream message, which carries the
        # request URL with the server's API key in it.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        reason = f"HTTP {status}" if status else type(exc).__name__
        return {"_error": f"owm_error: {_redact_secrets(reason, api_key)}"}

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
    return _live_conditions(
        location_name=data.get("name") or location or "Unknown",
        country=(data.get("sys") or {}).get("country"),
        lat=resolved_lat,
        lon=resolved_lon,
        altitude_m=alt,
        temp_c=temp_c,
        humidity=humidity,
        pressure_hpa=pressure_hpa,
        wind_ms=wind_ms,
        wind_deg=wind_deg,
        provider="openweathermap",
    )


def _live_conditions(
    *,
    location_name: str,
    country: str | None,
    lat: float | None,
    lon: float | None,
    altitude_m: float,
    temp_c: float,
    humidity: float,
    pressure_hpa: float,
    wind_ms: float,
    wind_deg: float,
    provider: str,
) -> dict:
    """Environment parameters from one weather reading (sea-level pressure)."""
    from .database.weather_repo import (
        compute_air_density,
        compute_density_altitude,
        compute_power_correction,
    )

    alt = float(altitude_m)
    air_density = compute_air_density(temp_c, humidity, pressure_hpa, alt)
    da_ft = compute_density_altitude(temp_c, humidity, pressure_hpa, alt)
    pcf = compute_power_correction(temp_c, pressure_hpa, humidity, alt)
    return {
        "location_name": location_name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
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
        "provider": provider,
    }


_OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


def _fetch_open_meteo_uncached(
    *,
    location: str | None,
    lat: float | None,
    lon: float | None,
    altitude_m: float | None,
) -> dict:
    """Current conditions from Open-Meteo, which needs no API key.

    Used when the server has no OpenWeatherMap key. Open-Meteo also returns
    the ground elevation, so a searched place gets its real altitude instead
    of sea level. A trailing country code ("Pune, IN") narrows the search.
    """
    try:
        import requests  # type: ignore
    except ImportError:
        return {"_error": "requests_not_installed"}

    name = None
    country = None
    try:
        if lat is None or lon is None:
            if not location or not location.strip():
                return {"_error": "missing_location"}
            parts = [p.strip() for p in location.split(",") if p.strip()]
            query = parts[0] if parts else location.strip()
            want_cc = (
                parts[-1].upper() if len(parts) > 1 and len(parts[-1]) == 2 else None
            )
            resp = requests.get(
                _OPEN_METEO_GEOCODE,
                params={"name": query, "count": 10, "language": "en", "format": "json"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results") or []
            if want_cc:
                results = [r for r in results if r.get("country_code") == want_cc]
            if not results:
                return {"_error": "place_not_found"}
            top = results[0]
            lat, lon = float(top["latitude"]), float(top["longitude"])
            name = top.get("name")
            country = top.get("country_code")
            if altitude_m is None and top.get("elevation") is not None:
                altitude_m = float(top["elevation"])
        resp = requests.get(
            _OPEN_METEO_FORECAST,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,pressure_msl,"
                    "wind_speed_10m,wind_direction_10m"
                ),
                "wind_speed_unit": "ms",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Open-Meteo fetch failed (by=%s): %s",
            "coords" if location is None else "name",
            type(exc).__name__,
        )
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "_error": f"weather_error: {f'HTTP {status}' if status else type(exc).__name__}"
        }

    current = data.get("current") or {}
    if altitude_m is None and data.get("elevation") is not None:
        altitude_m = float(data["elevation"])
    return _live_conditions(
        location_name=name or location or "Unknown",
        country=country,
        lat=lat,
        lon=lon,
        altitude_m=float(altitude_m) if altitude_m is not None else 0.0,
        temp_c=float(current.get("temperature_2m", 25.0)),
        humidity=float(current.get("relative_humidity_2m", 50.0)),
        pressure_hpa=float(current.get("pressure_msl", 1013.25)),
        wind_ms=float(current.get("wind_speed_10m", 0.0)),
        wind_deg=float(current.get("wind_direction_10m", 0.0)),
        provider="open-meteo",
    )


@app.post(
    "/api/venues/resolve",
    # Rate-limited per IP (2026-07-25 audit): on a venue miss this falls
    # through to a live OpenWeatherMap call on the operator's server-side
    # key, with no auth and no caching of the miss — an unauthenticated
    # loop over random lat/lon drains the free allowance (60/min, 1M/mo),
    # after which the real LocationPicker on /simulator stops working.
    dependencies=[Depends(rate_limit("venue_resolve", 20, 60.0))],
)
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
                "surface_type": venue.get("surface_type"),
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
        if err == "place_not_found":
            raise HTTPException(
                404, "We couldn't find that place. Try a nearby city or pick a track."
            )
        if err.startswith(("owm_error", "weather_error")):
            # The reason is key-free by construction (an HTTP status or an
            # exception class name), never the upstream message.
            reason = err.split(":", 1)[1].strip() if ":" in err else ""
            raise HTTPException(
                502,
                "Live weather isn't available right now"
                + (f" ({reason})" if reason else "")
                + ". Pick a track or set the conditions by hand.",
            )
        if err == "missing_location":
            raise HTTPException(422, "Give a place name or coordinates.")
        raise HTTPException(
            503,
            "Live weather isn't available right now. Pick a track or set the "
            "conditions by hand.",
        )

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
        "fetched_at": owm.get("fetched_at") or datetime.now(timezone.utc).isoformat(),
        "source": owm.get("provider", "openweathermap"),
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


async def _startup_load_surrogate():
    global _SURROGATE, _SURROGATE_SOURCE
    with _SURROGATE_LOCK:
        _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()


# ─── Request / Response models ────────────────────────────────────────────


class SurrogatePredictRequest(BaseModel):
    bike_id: DbId | None = Field(None, description="DB bike_models.id (optional)")
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


@app.post(
    "/api/surrogate/predict",
    response_model=SurrogatePredictResponse,
    dependencies=[Depends(rate_limit("surrogate", 60, 60.0))],
)
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
        raise _server_error("Surrogate inference error", exc) from exc

    return SurrogatePredictResponse(
        et_s=round(et_val, 4),
        trap_kmh=round(trap_kmh, 2),
        inference_ms=round(elapsed_ms, 3),
        source=_SURROGATE_SOURCE,
        within_training_envelope=within_env,
        envelope_violations=violations,
    )


@app.post(
    "/api/surrogate/compare",
    response_model=SurrogateCompareResponse,
    dependencies=[Depends(rate_limit("surrogate", 60, 60.0))],
)
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


@app.get("/api/pricing/part/{part_id}", response_model=PartPricingOut)
def pricing_for_part(part_id: int = Path(..., ge=1, le=MAX_DB_ID)):
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
def pricing_for_bike(
    bike_id: int = Path(..., ge=1, le=MAX_DB_ID), limit: int = Query(50, ge=1, le=500)
):
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


# Hard server-side floor on how often ONE part may hit its retailer, even
# with force=true (2026-07-25 audit §3.4). force exists so an operator can
# re-check a part that just changed price; it was never meant to be a way to
# aim the 44 s worst-case outbound fetch at the same URL in a loop. The rate
# limit bounds the caller; this bounds the third party we call.
PRICING_FORCE_FLOOR_S = 3600.0


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
    """FastAPI dependency: a test seam, ``None`` in production.

    The chat routes build a client per request (the visitor's own key from
    the X-Anthropic-Key header, or the server key from ANTHROPIC_API_KEY,
    for the chosen assistant). Tests override this dependency with a fake
    client, which is then used as given.
    """
    return None


ANTHROPIC_KEY_HEADER = "x-anthropic-key"


def _visitor_key(request: Request) -> tuple[str | None, bool]:
    """(key, malformed) from the X-Anthropic-Key header.

    An absent or blank header means "use the server key". A value that does
    not look like an Anthropic key is reported as malformed and never used.
    The key stays in local variables and a per-request client only.
    """
    from .llm.client import looks_like_anthropic_key

    raw = request.headers.get(ANTHROPIC_KEY_HEADER)
    if raw is None or not raw.strip():
        return None, False
    if not looks_like_anthropic_key(raw):
        return None, True
    return raw, False


def _chat_client(req: "ChatRequest", visitor_key: str | None, override):
    """The client for this request: the test override, or a fresh client for
    the chosen assistant on the visitor's key (no env fallback) or on the
    server key."""
    if override is not None:
        return override
    from .llm.client import LLMClient

    if visitor_key is not None:
        return LLMClient(req.assistant, api_key=visitor_key, own_key=True)
    return LLMClient(req.assistant)


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
            "Classic mode only. If True, the assistant writes a 2-4 sentence "
            "summary. Set False to skip the second LLM call."
        ),
    )
    assistant: Literal["mechanic", "doctor"] = Field(
        "mechanic",
        description=(
            "Which assistant answers: 'mechanic' (Claude Sonnet 5.5, default) "
            "or 'doctor' (Claude Opus 5.5). A visitor may send their own "
            "Anthropic key in the X-Anthropic-Key header; it is used for this "
            "request only and never stored."
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
      - if error == "assistant_unavailable" (no server key and no visitor
        key) or "free_assistant_resting" (the server key's credit is used
        up): invite the visitor to add their own Anthropic key.
      - if error == "invalid_key_format" / "key_rejected": the visitor's key
        is malformed or was refused; ask them to check it.
      - if error == "rate_limited": show a polite retry-in-a-minute note.
      - if error == "refused": the model declined; suggest rephrasing.
      - if error == "parse_failed" / "sim_failed" / "agent_failed": show
        error_detail (never contains a key).
      - if error == None: render summary text; agent mode additionally
        returns ordered `blocks` ([{type, payload}]) — sim_result /
        top_speed / compare_result / build_result / outlaw_result /
        autotune_result / estimated_sim / parts / tires / web_citations —
        for rich per-type tiles. `sim_result` mirrors the LAST sim block
        for backwards compatibility with older clients.
    """

    raw_query: str
    mode: str = "classic"
    assistant: str = "mechanic"
    own_key: bool = False
    intent_type: str | None = None
    bike_name: str = ""
    bike_id: DbId | None = None
    venue_name: str | None = None
    venue_id: DbId | None = None
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


def _get_surrogate_pair():
    """Lazy surrogate accessor shared with the optimizer routes."""
    global _SURROGATE, _SURROGATE_SOURCE
    if _SURROGATE is None:
        with _SURROGATE_LOCK:
            if _SURROGATE is None:
                _SURROGATE, _SURROGATE_SOURCE = _load_surrogate()
    return _SURROGATE, _SURROGATE_SOURCE


def _chat_impl(
    req: ChatRequest, client, progress=None, heavy_gate=None, *, own_key=False
) -> dict:
    """Run one chat turn (agent or classic). Returns a ChatResponse dict.

    A per-request visitor-key client is closed (and its key dropped) when
    the turn ends, whatever happens.
    """
    try:
        payload = _chat_turn(req, client, progress, heavy_gate)
    finally:
        if own_key and hasattr(client, "close"):
            client.close()
    payload["assistant"] = req.assistant
    payload["own_key"] = bool(own_key)
    return payload


def _chat_turn(req: ChatRequest, client, progress, heavy_gate) -> dict:
    db = _get_db_facade()
    if db is None:
        raise HTTPException(status_code=503, detail="database_unavailable")

    if req.mode == "classic":
        from .llm import run_chat_pipeline

        result = run_chat_pipeline(
            req.query,
            db,
            client=client,
            run_summary=req.run_summary,
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
    # ``heavy_gate`` charges each heavy agent tool (optimizer / autotune /
    # outlaw) against the caller's per-IP ``optimize`` bucket, so asking the
    # agent for them cannot out-run the direct routes. The agent's own
    # per-turn HEAVY_OP_BUDGET and the chat buckets remain in force.
    result = run_agent_chat(
        req.query,
        db,
        client=client,
        history=history,
        progress_cb=progress,
        surrogate_getter=_get_surrogate_pair,
        heavy_gate=heavy_gate,
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


def _parse_nonneg_int_env(name: str, default: int) -> int:
    """Read a non-negative int from the environment; fall back (with a
    warning) on garbage rather than crashing the boot over a typo."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logging.getLogger(__name__).warning(
            "%s=%r is not an integer — using the default %d", name, raw, default
        )
        return default
    if value < 0:
        logging.getLogger(__name__).warning(
            "%s=%d is negative — using the default %d", name, value, default
        )
        return default
    return value


# LLM-bill fuse (open-source pivot, 2026-10-23). A turn on the server key
# spends the operator's Anthropic credit, and an agent turn is several model
# calls, so the per-minute `chat` bucket alone (20/60 s) still lets one IP
# run ~28k turns a day. This caps each client IP at MOTOQUANT_CHAT_DAILY_LIMIT
# units per rolling 24 h window, shared by /api/chat and /api/jobs/chat. A
# mechanic question costs 1 unit and a doctor question 2 (the doctor's model
# costs about twice as much). Questions asked with the visitor's own key
# skip this cap: they spend the visitor's credit, not the operator's. The
# per-minute bucket and the heavy-op gate still apply to everyone, because
# the tools run simulations on this server. 0 disables the cap.
CHAT_DAILY_LIMIT = _parse_nonneg_int_env("MOTOQUANT_CHAT_DAILY_LIMIT", 200)
CHAT_DAILY_WINDOW_S = 86400.0


def _chat_daily_cap(request: Request, assistant: str = "mechanic") -> None:
    """Charge one server-key chat turn against the per-IP daily cap (no-op
    when the limit is 0). Raises 429 when the cap is used up."""
    from . import ratelimit as _ratelimit
    from .llm.client import ASSISTANTS

    limit = CHAT_DAILY_LIMIT
    if limit <= 0:
        return
    spec = ASSISTANTS.get(assistant) or ASSISTANTS["mechanic"]
    _ratelimit.enforce(
        request, "chat_day", limit, CHAT_DAILY_WINDOW_S, cost=spec.cap_units
    )


def _enforce_classic_chat_limit(req: ChatRequest, request: Request) -> None:
    """Extra per-IP fuse for mode="classic" chat.

    Classic mode runs 1-25 real RK4 sims per request (choose_bike simulates
    up to 25 candidates, rank up to 15) with no per-message budget like the
    agent executor's, so on top of the shared 20/60s chat bucket it gets its
    own much tighter one.
    """
    if req.mode == "classic":
        rate_limit("chat_classic", 4, 60.0)(request)


def _early_chat_answer(req: ChatRequest, error: str, detail: str) -> dict:
    """A ChatResponse-shaped answer that needs no model call."""
    return {
        "raw_query": req.query,
        "mode": req.mode,
        "assistant": req.assistant,
        "own_key": False,
        "error": error,
        "error_detail": detail,
    }


def _prepare_chat(req: ChatRequest, request: Request, override):
    """Shared front half of both chat routes.

    Returns (client, own_key, early_answer). ``early_answer`` is set when
    the request can be answered without a model call (malformed key, or no
    usable server key). The daily cap is charged only for server-key turns,
    before the classic-mode bucket so a lower daily cap trips first.
    """
    from .llm.client import (
        FREE_ASSISTANT_RESTING_DETAIL,
        server_key_configured,
        server_key_resting,
    )

    visitor_key, malformed = _visitor_key(request)
    if malformed:
        return (
            None,
            False,
            _early_chat_answer(
                req,
                "invalid_key_format",
                "That does not look like an Anthropic API key. Keys start with "
                "sk-ant- and have no spaces.",
            ),
        )
    own_key = visitor_key is not None
    # Both cases below are known before any model call, so neither charges
    # the daily cap: the server key would not be used.
    if not own_key and override is None and not server_key_configured():
        return (
            None,
            False,
            _early_chat_answer(
                req,
                "assistant_unavailable",
                "No Anthropic key is set on the server (ANTHROPIC_API_KEY). "
                "Add your own key to ask questions.",
            ),
        )
    if not own_key and override is None and server_key_resting():
        return (
            None,
            False,
            _early_chat_answer(
                req, "free_assistant_resting", FREE_ASSISTANT_RESTING_DETAIL
            ),
        )
    if not own_key:
        _chat_daily_cap(request, req.assistant)
    _enforce_classic_chat_limit(req, request)
    return _chat_client(req, visitor_key, override), own_key, None


@app.get("/api/assistant")
def assistant_info() -> dict:
    """What the chat panel needs before the first question: whether the free
    (server-key) assistant can answer, the assistants on offer and the daily
    free limit in units (a doctor question costs 2, a mechanic question 1)."""
    from .llm.client import ASSISTANT_ORDER, ASSISTANTS, free_assistant_available

    return {
        "free_available": free_assistant_available(),
        "assistants": [
            {
                "id": ASSISTANTS[a].id,
                "label": ASSISTANTS[a].label,
                "model": ASSISTANTS[a].model_label,
            }
            for a in ASSISTANT_ORDER
        ],
        "default": "mechanic",
        "daily_free_limit": CHAT_DAILY_LIMIT,
    }


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit("chat", 20, 60.0))],
)
def chat(
    req: ChatRequest,
    request: Request,
    client=Depends(get_llm_client),
) -> ChatResponse:
    """End-to-end NL chat (agent mode by default; mode='classic' for the
    legacy pipeline).

    Always returns 200 with `error` populated on failure modes the user
    can recover from (bike not found, no key, key refused, credit used up,
    Anthropic rate limit, refusal). Returns 503 only if the database itself
    is unreachable; 429 when the caller trips the per-minute, the
    classic-mode or the daily chat fuse (the daily fuse applies only to
    questions answered on the server key).
    """
    llm, own_key, early = _prepare_chat(req, request, client)
    if early is not None:
        return ChatResponse(**early)
    payload = _chat_impl(req, llm, heavy_gate=heavy_gate_for(request), own_key=own_key)
    suggestions = payload.pop("bike_suggestions", None) or []
    return ChatResponse(
        **payload,
        bike_suggestions=[ChatBikeSuggestion(**s) for s in suggestions],
    )


@app.post(
    "/api/jobs/chat",
    status_code=202,
    # Same buckets as /api/chat: the web client uses either route.
    dependencies=[Depends(rate_limit("chat", 20, 60.0))],
)
def job_chat(
    req: ChatRequest,
    request: Request,
    client=Depends(get_llm_client),
):
    """Start a chat turn as a background job with live progress + Stop.

    Agent turns can run multiple sims / an optimizer pass, which on the
    0.5-CPU prod tier exceeds comfortable request time — same rationale as
    every other /api/jobs/* route. Poll GET /api/jobs/{id}; result is the
    ChatResponse-shaped dict. The X-Anthropic-Key header is read here, once;
    polls never carry it.
    """
    llm, own_key, early = _prepare_chat(req, request, client)
    if early is not None:
        return _start_job("chat", lambda _progress: early)
    gate = heavy_gate_for(request)

    def run(progress):
        try:
            return _chat_impl(req, llm, progress, gate, own_key=own_key)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001 -- the job keeps a redacted message
            from .llm.client import redact_secrets

            raise RuntimeError(redact_secrets(f"{type(e).__name__}: {e}")) from None

    try:
        return _start_job("chat", run, owner=_job_owner(request))
    except HTTPException:
        if own_key and hasattr(llm, "close"):
            llm.close()  # the job never started: drop the visitor's key now
        raise


# ═══════════════════════════════════════════════════════════════════════════
# BUILD OPTIMIZER + ECU AUTOTUNE  (/api/optimize/*, /api/autotune/*)  — Track B
# Free and anonymous like every other route. These are the heaviest compute
# paths (seconds to minutes of RK4 on the shared instance), so they carry the
# tightest per-IP buckets: optimize 6/60 s (shared with /api/jobs/outlaw) and
# autotune 6/60 s, each shared with its job-backed twin.
# The optimizer scores candidates through the loaded surrogate when available and
# in-envelope, else falls back to the full physics sim — so it always answers.
# ═══════════════════════════════════════════════════════════════════════════


class OptimizeBuildRequest(ConditionsRequest):
    """POST /api/optimize/build — best on-budget parts build for a goal."""

    bike_id: DbId | None = Field(None, description="DB bike_models.id")
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
    goal: Literal["min_et", "max_trap"] = Field(
        "min_et", description='"min_et" (faster ET) or "max_trap" (higher trap)'
    )
    profile: Literal["all", "street_legal", "drag_prep", "full_race"] = Field(
        "all", description="all | street_legal | drag_prep | full_race"
    )
    rider_weight_kg: float = Field(75.0, ge=40, le=150)
    power_boost_pct: float = Field(0.0, ge=-50, le=200)
    mass_delta_kg: float = Field(0.0, ge=-100, le=200)
    max_candidates: int | None = Field(
        None,
        ge=1,
        le=200,
        description="Cap candidate pool (latency control for full-sim fallback)",
    )

    model_config = {"populate_by_name": True}


# Reference presets → their catalog rows, so preset requests still get a
# compatibility-filtered parts pool (parts_repo.search fails closed for an
# unknown bike and returns nothing useful for bike_model_id=None).
_PRESET_MODEL_NAMES = {
    "gsxr1000_k5": "GSX-R 1000 K5/K6",
    "yzfr1_4c8": "YZF-R1 4C8",
    "hayabusa_gen1": "Hayabusa GSX1300R Gen1",
}


def _parts_model_id(conn, bike_id: int | None, bike_preset: str | None) -> int | None:
    """bike_models.id to filter parts by: the request's bike, else its preset's row."""
    if bike_id is not None:
        return bike_id
    name = _PRESET_MODEL_NAMES.get(bike_preset or "gsxr1000_k5")
    if name is None:
        return None
    row = conn.execute(
        "SELECT id FROM bike_models WHERE model_name = ? ORDER BY id LIMIT 1", (name,)
    ).fetchone()
    return int(row[0]) if row else None


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
    except HTTPException:
        # Let _build_config's own status codes (404 unknown bike_id /
        # bike_preset) pass through instead of leaking "404: ..." inside
        # a 400 body (2026-07-06 API-hygiene fix).
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    env_source = _apply_conditions(config, req)

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
            bike_model_id=_parts_model_id(conn, req.bike_id, req.bike_preset),
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
        raise _server_error("Optimization failed", exc) from exc

    # Belt-and-braces: cost-per-tenth ratios can be non-finite (a part that
    # adds cost with ~0 ET gain); bare inf/nan is not JSON-compliant and 500s
    # the route. json_safe nulls them so the response always serializes.
    from .analysis.roi import json_safe

    out = json_safe(result.to_dict())
    out["environment"] = _environment_echo(config)
    out["environment_source"] = env_source
    return out


@app.post(
    "/api/optimize/build",
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def optimize_build_route(req: OptimizeBuildRequest):
    """Synchronous build optimiser (see ``_optimize_impl``)."""
    return _optimize_impl(req)


class AutotuneRequest(ConditionsRequest):
    """POST /api/autotune/ecu — conditions-aware drag setup advisor."""

    bike_id: DbId | None = Field(None, description="DB bike_models.id")
    bike_preset: str | None = Field(None, description="Fallback preset name")
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
    # A seeded venue named by `location` races on its own surface, the same
    # as when it is chosen by venue_id.
    if vd.get("surface_type"):
        config.environment.track_surface = str(vd["surface_type"]).lower()


def _apply_conditions(config: BikeConfig, req: ConditionsRequest) -> str:
    """Apply the request's optional location / manual conditions to *config*.

    Returns a short source tag (``config_default``, the resolver's source, or a
    ``resolution_*`` failure marker). Afterwards ``config.environment`` is the
    single source of truth for what is simulated — and for what the response
    echoes (see :func:`_environment_echo`).
    """
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
            if config.environment.venue_name == DEFAULT_CONDITIONS_NAME:
                config.environment.venue_name = req.location or "Resolved location"
        except HTTPException as exc:
            env_source = f"resolution_unavailable_{exc.status_code}"
        except Exception as exc:
            logging.getLogger(__name__).warning("env resolve failed: %s", exc)
            env_source = "resolution_error"

    # Explicit condition overrides take precedence over any resolution.
    manual = False
    if req.altitude_m is not None:
        config.environment.altitude_m = req.altitude_m
        manual = True
    if req.ambient_temp_c is not None:
        config.environment.ambient_temp_c = req.ambient_temp_c
        if req.track_temp_c is None:
            # Same rule as a resolved place: the track runs ~7 °C over the air.
            config.environment.track_temp_c = req.ambient_temp_c + 7.0
        manual = True
    if req.track_temp_c is not None:
        config.environment.track_temp_c = req.track_temp_c
        manual = True
    if req.humidity_pct is not None:
        config.environment.relative_humidity_pct = req.humidity_pct
        manual = True
    if req.pressure_hpa is not None:
        config.environment.barometric_pressure_hpa = req.pressure_hpa
        manual = True
    if manual and config.environment.venue_name == DEFAULT_CONDITIONS_NAME:
        config.environment.venue_name = CUSTOM_CONDITIONS_NAME
    return env_source


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
    except HTTPException:
        # Let _build_config's own status codes (404 unknown bike_id /
        # bike_preset) pass through instead of leaking "404: ..." inside
        # a 400 body (2026-07-06 API-hygiene fix).
        raise
    except Exception as exc:
        raise HTTPException(400, f"Config construction failed: {exc}") from exc

    env_source = _apply_conditions(config, req)

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
        raise _server_error("Autotune failed", exc) from exc

    out = result.to_dict()
    out["environment_source"] = env_source
    # Keep the autotune block's keys; add the shared echo markers so every
    # route labels default / custom / venue conditions the same way.
    echo = _environment_echo(config)
    out["environment"] = {
        **out.get("environment", {}),
        "location": echo["name"],
        "name": echo["name"],
        "is_default": echo["is_default"],
        "source": echo["source"],
        "track_surface": echo["track_surface"],
        "headwind_kmh": echo["headwind_kmh"],
    }
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


def _job_owner(request: Request) -> str | None:
    """Client identity for the per-client job cap, or None to skip that cap.

    Without the site-proxy secret, every visitor who comes through the website
    reaches us from one of Vercel's addresses, so a per-IP cap would throttle
    them all together. The cap applies only once the proxy vouches for the
    real visitor IP (motoquant.ratelimit.proxy_secret_configured).
    """
    from .ratelimit import client_ip, proxy_secret_configured

    return client_ip(request) if proxy_secret_configured() else None


def _start_job(kind: str, runner, owner: str | None = None) -> dict:
    from .jobs import JobCapacityError, create_job

    try:
        job = create_job(kind, runner, owner=owner)
    except JobCapacityError as exc:
        raise HTTPException(429, str(exc)) from exc
    return {"job_id": job.id, "kind": kind, "status": job.status}


@app.post(
    "/api/jobs/simulate",
    status_code=202,
    dependencies=[
        # Cost fuse shared with the sync /api/simulate route it wraps
        # (2026-08-11 hardening) — see that route for the rationale.
        Depends(rate_limit("simulate", 30, 60.0)),
    ],
)
def job_simulate(req: SimulateRequest, request: Request):
    """Start a full simulation as a background job (real progress)."""
    _precheck_refs(
        bike_ids=[req.bike_id],
        bike_presets=[req.bike_preset],
        venue_id=req.venue_id,
        tire_ids=[req.front_tire_id, req.rear_tire_id],
    )
    return _start_job(
        "simulate",
        lambda progress: _simulate_impl(req, progress),
        owner=_job_owner(request),
    )


@app.post(
    "/api/jobs/topspeed",
    status_code=202,
    dependencies=[
        # Cost fuse shared with the sync /api/simulate/top-speed route.
        Depends(rate_limit("topspeed", 30, 60.0)),
    ],
)
def job_topspeed(req: TopSpeedRequest, request: Request):
    """Start a top-speed run as a background job (real progress)."""
    _precheck_refs(
        bike_ids=[req.bike_id],
        bike_presets=[req.bike_preset],
        venue_id=req.venue_id,
        tire_ids=[req.front_tire_id, req.rear_tire_id],
    )
    return _start_job(
        "topspeed",
        lambda progress: _topspeed_impl(req, progress),
        owner=_job_owner(request),
    )


@app.post(
    "/api/jobs/optimize",
    status_code=202,
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def job_optimize(req: OptimizeBuildRequest, request: Request):
    """Start the build optimiser as a background job (real progress)."""
    _precheck_refs(
        bike_ids=[req.bike_id], bike_presets=[req.bike_preset], venue_id=req.venue_id
    )
    return _start_job(
        "optimize",
        lambda progress: _optimize_impl(req, progress),
        owner=_job_owner(request),
    )


@app.post(
    "/api/jobs/autotune",
    status_code=202,
    dependencies=[Depends(rate_limit("autotune", 6, 60.0))],
)
def job_autotune(req: AutotuneRequest, request: Request):
    """Start the ECU autotune as a background job (real progress)."""
    _precheck_refs(
        bike_ids=[req.bike_id], bike_presets=[req.bike_preset], venue_id=req.venue_id
    )
    return _start_job(
        "autotune",
        lambda progress: _autotune_impl(req, progress),
        owner=_job_owner(request),
    )


class OutlawRequest(ConditionsRequest):
    """POST /api/jobs/outlaw — composed outlaw/open-class max-effort build.

    Pipeline: best drag_prep rubber → full_race parts knapsack (budget
    unlimited unless capped) → gearing + launch autotune on the modified
    bike → combined verification sim.
    """

    bike_id: DbId | None = Field(None, description="DB bike_models.id")
    bike_preset: str | None = Field(
        None, description="Fallback preset: gsxr1000_k5 | yzfr1_4c8 | hayabusa_gen1"
    )
    budget_inr: float | None = Field(
        None, ge=0, le=5_000_000, description="null / 0 = no limit"
    )
    goal: str = Field("min_et")
    rider_weight_kg: float = Field(75.0, ge=40, le=150)
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

    env_source = _apply_conditions(config, req)

    surrogate, surrogate_source = _get_surrogate_pair()

    from .analysis.outlaw import optimize_outlaw
    from .database.parts_repo import PartsRepository
    from .database.tire_repo import TireRepository

    try:
        out = optimize_outlaw(
            config,
            PartsRepository(conn),
            TireRepository(conn),
            bike_model_id=_parts_model_id(conn, req.bike_id, req.bike_preset),
            budget_inr=req.budget_inr,
            goal=req.goal,
            surrogate=surrogate,
            surrogate_source=surrogate_source,
            max_candidates=req.max_candidates,
            progress_cb=progress,
        )
        out["environment"] = _environment_echo(config)
        out["environment_source"] = env_source
        return out
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
    # Shares the `optimize` bucket: the outlaw pipeline IS an optimizer pass
    # plus an autotune, so alternating the two can't double the CPU budget.
    dependencies=[Depends(rate_limit("optimize", 6, 60.0))],
)
def job_outlaw(req: OutlawRequest, request: Request):
    """Start the composed outlaw/open-class build as a background job."""
    _precheck_refs(
        bike_ids=[req.bike_id], bike_presets=[req.bike_preset], venue_id=req.venue_id
    )
    return _start_job(
        "outlaw",
        lambda progress: _outlaw_impl(req, progress),
        owner=_job_owner(request),
    )


@app.post(
    "/api/jobs/compare",
    status_code=202,
    dependencies=[Depends(_rl_compare)],
)
def job_compare(req: CompareRequest, request: Request):
    """Start an A-vs-B comparison as a background job (real progress).

    Shares the ``compare`` rate-limit bucket with the sync
    /api/simulate/compare route it wraps — the two must stay behaviourally
    identical (deploy-skew fallback contract)."""
    _precheck_refs(
        bike_ids=[req.a_bike_id, req.b_bike_id],
        bike_presets=[req.a_bike_preset, req.b_bike_preset],
        venue_id=req.venue_id,
        tire_ids=[
            req.a_front_tire_id,
            req.a_rear_tire_id,
            req.b_front_tire_id,
            req.b_rear_tire_id,
        ],
    )
    return _start_job(
        "compare",
        lambda progress: _compare_impl(req, progress),
        owner=_job_owner(request),
    )


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
        # The finished result is held as compressed JSON; splice its bytes into
        # the envelope instead of decoding and re-encoding a multi-MB object on
        # every poll.
        raw = job.result_json()
        if raw is not None:
            head = json.dumps(out, separators=(",", ":")).encode("utf-8")
            return Response(
                content=head[:-1] + b',"result":' + raw + b"}",
                media_type="application/json",
            )
        out["result"] = None
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


async def _start_keepwarm_loop() -> None:
    try:
        from .keepwarm import start_keepwarm

        start_keepwarm()
    except Exception:  # noqa: BLE001 — keep-warm is best-effort only
        logging.getLogger(__name__).warning("keep-warm init failed", exc_info=True)


async def _probe_physics_engine() -> None:
    """Run the engine selector's one-time probes (extension import, host-math
    check, source fingerprint) at boot instead of on the first /api/health or
    simulation, and log which integrator this process serves with."""
    try:
        info = engine_select.engine_info()
        logging.getLogger(__name__).info(
            "physics engine: %s (mode=%s%s)",
            info.get("engine"),
            info.get("mode"),
            f", fallback: {info['fallback_reason']}"
            if info.get("fallback_reason")
            else "",
        )
    except Exception:  # noqa: BLE001 — diagnostics only; sims still select per call
        logging.getLogger(__name__).warning("engine probe failed", exc_info=True)


async def _ensure_runtime_schema() -> None:
    """Guarded ALTER so an older catalog gains the ``category_tag`` column.

    Deliberately creates ONLY what live code uses. There are no accounts and
    no server-side saved runs; scripts/patch_2026_11_10_remove_accounts.py
    drops their tables from shipped databases and nothing recreates them.
    """
    try:
        db = _get_db()
        if not db:
            return
        try:
            db.execute("ALTER TABLE bike_configs ADD COLUMN category_tag TEXT")
            db.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
    except Exception:  # noqa: BLE001 — schema top-up is best-effort
        logging.getLogger(__name__).warning(
            "runtime schema ensure failed", exc_info=True
        )


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Startup hooks, in registration order: surrogate load, keep-warm loop,
    physics-engine probe, runtime-schema top-up."""
    await _startup_load_surrogate()
    await _start_keepwarm_loop()
    await _probe_physics_engine()
    await _ensure_runtime_schema()
    yield


app.router.lifespan_context = _lifespan
