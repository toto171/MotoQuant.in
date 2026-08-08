"""
MotoQuant MCP server — the drag-sim engine as AI tools, over stdio.
====================================================================

A self-contained Model Context Protocol server so any MCP client (Claude
Desktop, Claude Code, …) can ask the physics engine real questions:

    "what does 16/45 vs 16/47 do to my Hayabusa's 60-foot?"

Design notes (deliberate, see docs/MCP.md)
------------------------------------------
* **Stdlib only.** No ``mcp`` SDK dependency — the stdio transport is
  newline-delimited JSON-RPC 2.0, which is ~60 lines of framing. Nothing
  here is added to ``requirements-api.txt``; the prod image stays lean.
* **Two backends, one tool surface.**
  - ``http`` (default) talks to the hosted API at ``MOTOQUANT_API_URL``
    (default ``https://motoquant-api.onrender.com``) with ``urllib``.
    Zero install beyond Python.
  - ``local`` (``MOTOQUANT_MCP_LOCAL=1``) imports ``motoquant.api`` and
    calls the *same* internal functions the HTTP routes call, against the
    local ``motoquant.db``. No network, no cold start, and it unlocks
    arbitrary sprocket what-ifs (see ``gearing_impact``).
* **Compact results.** Every tool returns small JSON with units baked into
  the field names (``et_s``, ``trap_kmh``) — no time-series arrays. LLM
  context is the scarce resource here, not bandwidth.
* **Honest sign convention.** ``et_delta_s`` is always *after − before*:
  negative = faster. Same as the REST API and the CLI.

Run
---
    python -m motoquant.mcp_server              # hosted API backend
    MOTOQUANT_MCP_LOCAL=1 python -m motoquant.mcp_server
    python -m motoquant.mcp_server --selftest   # in-process smoke test
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

# ─── Constants ────────────────────────────────────────────────────────────

SERVER_NAME = "motoquant"
SERVER_VERSION = "0.1.0"

# MCP revisions whose stdio transport + tool shapes this server implements.
# We echo the client's version when we know it, else fall back to our latest.
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
DEFAULT_PROTOCOL_VERSION = "2025-06-18"

DEFAULT_API_URL = "https://motoquant-api.onrender.com"
# The hosted API runs on Render's free tier: a cold instance can take ~50 s to
# answer the first request. 90 s leaves headroom without hanging forever.
DEFAULT_TIMEOUT_S = 90.0

PRESETS = ("gsxr1000_k5", "yzfr1_4c8", "hayabusa_gen1")

INSTRUCTIONS = (
    "MotoQuant simulates motorcycle quarter-mile drag runs from first "
    "principles (RK4 over 15 physics sub-models), not from lookup tables. "
    "Pick a bike with search_bikes (or a bike_preset), then simulate. "
    "ET is elapsed time over 402.3 m; trap speed is the speed crossing that "
    "line; the 60-foot split is the launch-quality number. All et_delta_s "
    "values are after-minus-before, so negative means faster. Published "
    "accuracy: weighted mean |error| ~0.27 s across 277 matched real-world "
    "benchmarks — good for ranking builds and what-ifs, not for claiming a "
    "specific bike will run an exact ET."
)


class ToolError(Exception):
    """A tool failed in a way the *model* should see and can act on."""


# ─── Backends ─────────────────────────────────────────────────────────────


class HttpBackend:
    """Talks to the hosted REST API with stdlib urllib."""

    kind = "http"
    supports_direct_gearing = False

    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT_S):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- transport ---------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url = f"{url}?{urllib.parse.urlencode(clean)}"
        data = None
        headers = {"Accept": "application/json", "User-Agent": "motoquant-mcp/0.1"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                body = json.loads(exc.read().decode("utf-8"))
                detail = body.get("detail") or json.dumps(body)[:300]
            except Exception:  # noqa: BLE001 - body may be HTML/empty
                detail = exc.reason or ""
            raise ToolError(f"API error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ToolError(
                f"Could not reach the MotoQuant API at {self.base_url} "
                f"({exc.reason}). The hosted free tier cold-starts slowly; "
                "retry, or run the server with MOTOQUANT_MCP_LOCAL=1."
            ) from exc
        except TimeoutError as exc:
            raise ToolError(
                f"Timed out after {self.timeout:.0f}s waiting for "
                f"{self.base_url}. Free-tier cold start can take ~50s — retry."
            ) from exc

    # -- semantic operations ----------------------------------------------
    def list_bikes(self, **kw: Any) -> dict:
        return self._request("GET", "/api/bikes", params=kw)

    def get_bike(self, bike_id: int) -> dict:
        return self._request("GET", f"/api/bikes/{bike_id}")

    def list_venues(self) -> dict:
        return self._request("GET", "/api/venues")

    def list_parts(self, **kw: Any) -> dict:
        if "compatible_only" in kw and kw["compatible_only"] is not None:
            kw["compatible_only"] = "true" if kw["compatible_only"] else "false"
        return self._request("GET", "/api/parts", params=kw)

    def simulate_quick(self, payload: dict) -> dict:
        return self._request("POST", "/api/simulate/quick", payload=payload)

    def top_speed(self, payload: dict) -> dict:
        return self._request("POST", "/api/simulate/top-speed", payload=payload)

    def compare(self, payload: dict) -> dict:
        return self._request("POST", "/api/simulate/compare", payload=payload)


class LocalBackend:
    """Imports ``motoquant`` and calls the same functions the API routes call.

    Not a re-implementation: every method below dispatches into
    ``motoquant.api`` so the MCP surface can never silently drift from the
    REST surface (the two share ``_build_config`` / ``_apply_parts_to_config``
    / ``_compare_impl`` verbatim).
    """

    kind = "local"
    supports_direct_gearing = True

    def __init__(self) -> None:
        self._api: Any = None
        self._http_exc: Any = None

    def _mod(self) -> Any:
        if self._api is None:
            try:
                from fastapi import HTTPException

                from . import api as api_mod
            except ImportError as exc:  # pragma: no cover - env-dependent
                raise ToolError(
                    "Local mode needs the API dependencies "
                    "(pip install -r requirements-api.txt). Unset "
                    f"MOTOQUANT_MCP_LOCAL to use the hosted API instead. ({exc})"
                ) from exc
            self._api = api_mod
            self._http_exc = HTTPException
        return self._api

    def _call(self, fn: Callable[..., Any], *a: Any, **kw: Any) -> Any:
        self._mod()
        try:
            return fn(*a, **kw)
        except self._http_exc as exc:  # type: ignore[misc]
            raise ToolError(f"API error {exc.status_code}: {exc.detail}") from exc
        except ToolError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface engine faults to the model
            raise ToolError(f"{type(exc).__name__}: {exc}") from exc

    # -- semantic operations ----------------------------------------------
    # NOTE: the GET routes declare FastAPI ``Query(...)`` defaults, which are
    # only resolved by the request layer. Calling them as plain functions
    # means EVERY parameter must be passed explicitly — an omitted one binds a
    # ``Query`` object straight into SQLite ("type 'Query' is not supported").
    def list_bikes(self, **kw: Any) -> dict:
        api = self._mod()
        return self._call(
            api.list_bikes,
            search=kw.get("search"),
            manufacturer=kw.get("manufacturer"),
            category=kw.get("category"),
            limit=kw.get("limit") or 100,
            offset=kw.get("offset") or 0,
        )

    def get_bike(self, bike_id: int) -> dict:
        api = self._mod()
        return self._call(api.get_bike, bike_id)

    def list_venues(self) -> dict:
        api = self._mod()
        return self._call(api.list_venues)

    def list_parts(self, **kw: Any) -> dict:
        api = self._mod()
        return self._call(
            api.list_parts,
            category=kw.get("category"),
            category_id=None,
            bike_id=kw.get("bike_id"),
            compatible_only=bool(kw.get("compatible_only", True)),
            search=kw.get("search"),
            limit=kw.get("limit") or 500,
        )

    def simulate_quick(self, payload: dict) -> dict:
        api = self._mod()
        return self._call(api.simulate_quick, api.QuickSimRequest(**payload))

    def top_speed(self, payload: dict) -> dict:
        api = self._mod()
        return self._call(api._topspeed_impl, api.TopSpeedRequest(**payload))

    def compare(self, payload: dict) -> dict:
        api = self._mod()
        return self._call(api._compare_impl, api.CompareRequest(**payload))

    # -- local-only: arbitrary sprocket swap -------------------------------
    def simulate_gearing(self, base: dict, front: int, rear: int) -> dict:
        """Run one sim with the final drive forced to ``front``/``rear`` teeth.

        Uses the production config builder, then overrides the two sprocket
        fields ``DrivetrainParams.final_ratio`` actually reads.
        """
        api = self._mod()
        from .physics import MotoQuantEngine

        def _run() -> dict:
            cfg = api._build_config(
                bike_id=base.get("bike_id"),
                bike_preset=base.get("bike_preset"),
                power_boost_pct=base.get("power_boost_pct", 0.0),
                mass_delta_kg=base.get("mass_delta_kg", 0.0),
                rider_mass_kg=base.get("rider_mass_kg", 75.0),
                venue_id=base.get("venue_id"),
                ambient_temp_c=base.get("ambient_temp_c"),
                humidity_pct=base.get("humidity_pct"),
                headwind_kmh=base.get("headwind_kmh"),
            )
            cfg = copy.deepcopy(cfg)
            cfg.drivetrain.front_sprocket = int(front)
            cfg.drivetrain.rear_sprocket = int(rear)
            sim = MotoQuantEngine(cfg).run()
            return {
                "front_sprocket": int(front),
                "rear_sprocket": int(rear),
                "final_drive_ratio": round(rear / front, 4),
                "et_s": round(float(sim.time_quarter), 4),
                "trap_kmh": round(float(sim.speed_quarter) * 3.6, 2),
                "et_60ft_s": round(float(sim.time_60ft), 4),
                "et_eighth_s": round(float(sim.time_eighth), 4),
                "bike_name": cfg.name,
            }

        return self._call(_run)


def make_backend() -> HttpBackend | LocalBackend:
    """Pick a backend from the environment (``MOTOQUANT_MCP_LOCAL``)."""
    if os.environ.get("MOTOQUANT_MCP_LOCAL", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return LocalBackend()
    base = os.environ.get("MOTOQUANT_API_URL", DEFAULT_API_URL)
    try:
        timeout = float(os.environ.get("MOTOQUANT_MCP_TIMEOUT", DEFAULT_TIMEOUT_S))
    except ValueError:
        timeout = DEFAULT_TIMEOUT_S
    return HttpBackend(base, timeout)


# ─── Shared argument plumbing ─────────────────────────────────────────────

_BIKE_PROPS = {
    "bike_id": {
        "type": "integer",
        "description": "Catalog bike id from search_bikes. Preferred.",
    },
    "bike_preset": {
        "type": "string",
        "enum": list(PRESETS),
        "description": "Hand-curated reference bike, used when bike_id is absent.",
    },
}

_CONDITION_PROPS = {
    "rider_mass_kg": {
        "type": "number",
        "minimum": 20,
        "maximum": 250,
        "description": "Rider + gear mass in kg (default 75).",
    },
    "power_boost_pct": {
        "type": "number",
        "minimum": -50,
        "maximum": 200,
        "description": "Blanket power change in % (10 = +10%). Use parts for real mods.",
    },
    "mass_delta_kg": {
        "type": "number",
        "minimum": -100,
        "maximum": 200,
        "description": "Mass added (+) or removed (-) from the bike, kg.",
    },
    "venue_id": {
        "type": "integer",
        "description": "Venue id from list_venues — sets altitude + surface.",
    },
    "ambient_temp_c": {"type": "number", "minimum": -30, "maximum": 60},
    "humidity_pct": {"type": "number", "minimum": 0, "maximum": 100},
    "headwind_kmh": {
        "type": "number",
        "minimum": -200,
        "maximum": 200,
        "description": "Headwind in km/h; negative is a tailwind.",
    },
}

_SIM_KEYS = (
    "bike_id",
    "bike_preset",
    "rider_mass_kg",
    "power_boost_pct",
    "mass_delta_kg",
    "venue_id",
    "ambient_temp_c",
    "humidity_pct",
    "headwind_kmh",
)


def _sim_payload(args: dict, *, part_ids: list[int] | None = None) -> dict:
    """Project tool arguments onto the API's sim request shape."""
    payload = {k: args[k] for k in _SIM_KEYS if args.get(k) is not None}
    if not payload.get("bike_id") and not payload.get("bike_preset"):
        raise ToolError("Provide bike_id (from search_bikes) or bike_preset.")
    if part_ids:
        payload["part_ids"] = part_ids
    return payload


def _need_int(args: dict, key: str) -> int:
    val = args.get(key)
    if val is None:
        raise ToolError(f"Missing required argument: {key}")
    try:
        return int(val)
    except (TypeError, ValueError):
        raise ToolError(f"{key} must be an integer, got {val!r}") from None


def _slim_bike(row: dict) -> dict:
    # /api/bikes rows come from _bike_row_to_summary, which renames
    # model_name -> model and year_from -> year. Accept both spellings so a
    # future shape change degrades instead of silently dropping the model name.
    out: dict[str, Any] = {}
    for out_key, candidates in (
        ("id", ("id",)),
        ("manufacturer", ("manufacturer",)),
        ("model", ("model", "model_name")),
        ("year", ("year", "year_from")),
        ("year_to", ("year_to",)),
        ("category", ("category",)),
        ("displacement_cc", ("displacement_cc",)),
        ("peak_power_hp", ("peak_power_hp",)),
        ("dry_mass_kg", ("dry_mass_kg",)),
        ("wet_mass_kg", ("wet_mass_kg",)),
        ("cylinder_config", ("cylinder_config",)),
        ("front_sprocket", ("front_sprocket",)),
        ("rear_sprocket", ("rear_sprocket",)),
        ("chain_pitch", ("chain_pitch",)),
    ):
        for cand in candidates:
            if row.get(cand) is not None:
                out[out_key] = row[cand]
                break
    return out


def _slim_sim(res: dict) -> dict:
    """Quick-sim response → compact, unit-suffixed result."""
    out = {
        "bike": res.get("bike_name"),
        "et_s": res.get("et_quarter_s"),
        "trap_kmh": res.get("trap_speed_kmh"),
        "et_60ft_s": res.get("et_60ft_s"),
        "et_eighth_s": res.get("et_eighth_s"),
        "peak_power_hp": res.get("peak_power_hp"),
        "total_mass_kg": res.get("total_mass_kg"),
    }
    if res.get("parts_applied"):
        out["parts_applied"] = [
            {
                "id": p.get("id"),
                "name": f"{p.get('brand', '')} {p.get('name', '')}".strip(),
            }
            for p in res["parts_applied"]
        ]
        out["build_cost_inr"] = res.get("build_cost_inr")
        out["stock_et_s"] = res.get("stock_et_s")
        out["et_delta_s"] = res.get("et_delta_s")
    return out


# ─── Tool implementations ─────────────────────────────────────────────────


def _t_search_bikes(backend: Any, args: dict) -> dict:
    limit = min(int(args.get("limit") or 15), 50)
    res = backend.list_bikes(
        search=args.get("query"),
        manufacturer=args.get("manufacturer"),
        category=args.get("category"),
        limit=limit,
        offset=0,
    )
    return {
        "total_matching": res.get("total"),
        "returned": len(res.get("bikes", [])),
        "bikes": [_slim_bike(b) for b in res.get("bikes", [])],
    }


def _t_get_bike(backend: Any, args: dict) -> dict:
    row = backend.get_bike(_need_int(args, "bike_id"))
    out = _slim_bike(row)
    for k in (
        "peak_power_rpm",
        "peak_torque_nm",
        "peak_torque_rpm",
        "redline_rpm",
        "bore_mm",
        "stroke_mm",
        "compression_ratio",
        "wheelbase_mm",
        "cd",
        "frontal_area_m2",
        "tire_mu_peak",
        "validation_et_s",
        "validation_trap_kmh",
        "validation_source",
    ):
        if row.get(k) is not None:
            out[k] = row[k]
    fitments = row.get("tire_fitments") or []
    out["oem_tires"] = [
        {
            "position": f.get("position"),
            "tire": f"{f.get('manufacturer', '')} {f.get('model', '')}".strip(),
            "size": f.get("size_designation"),
        }
        for f in fitments
        if f.get("fitment_type") == "oem"
    ][:4]
    return out


def _t_simulate_quarter_mile(backend: Any, args: dict) -> dict:
    part_ids = [int(p) for p in (args.get("part_ids") or [])]
    res = backend.simulate_quick(_sim_payload(args, part_ids=part_ids))
    out = _slim_sim(res)
    out["note"] = "ET/trap over 402.3 m from a full RK4 run; 60ft is launch quality."
    return out


def _t_simulate_top_speed(backend: Any, args: dict) -> dict:
    payload = _sim_payload(
        args, part_ids=[int(p) for p in (args.get("part_ids") or [])]
    )
    payload["include_timeseries"] = False
    res = backend.top_speed(payload)
    return {
        "bike": res.get("bike_name"),
        "top_speed_kmh": res.get("terminal_velocity_kmh"),
        "top_speed_mph": res.get("terminal_velocity_mph"),
        "time_to_terminal_s": res.get("time_to_terminal_s"),
        "distance_to_terminal_m": res.get("distance_to_terminal_m"),
        "terminal_gear": res.get("terminal_gear"),
        "terminal_rpm": res.get("terminal_rpm"),
        "reached_plateau": res.get("reached_plateau"),
        "note": (
            "Unrestricted unless the bike carries a factory speed limiter. "
            "Top-speed accuracy is weaker than ET accuracy (fleet bias ~+25 km/h)."
        ),
    }


def _t_compare_bikes(backend: Any, args: dict) -> dict:
    def side(prefix: str) -> dict:
        sub = {k[2:]: v for k, v in args.items() if k.startswith(prefix)}
        if not sub.get("bike_id") and not sub.get("bike_preset"):
            raise ToolError(f"Provide {prefix}bike_id or {prefix}bike_preset.")
        return sub

    a, b = side("a_"), side("b_")
    payload: dict[str, Any] = {}
    for tag, src in (("a", a), ("b", b)):
        for key in (
            "bike_id",
            "bike_preset",
            "rider_mass_kg",
            "power_boost_pct",
            "mass_delta_kg",
        ):
            if src.get(key) is not None:
                payload[f"{tag}_{key}"] = src[key]
        if src.get("part_ids"):
            payload[f"{tag}_part_ids"] = [int(p) for p in src["part_ids"]]
    for shared in ("venue_id", "ambient_temp_c", "humidity_pct", "headwind_kmh"):
        if args.get(shared) is not None:
            payload[shared] = args[shared]

    res = backend.compare(payload)

    def summary(side_res: dict) -> dict:
        return {
            "bike": side_res.get("bike_name"),
            "et_s": side_res.get("et_quarter_s"),
            "trap_kmh": side_res.get("trap_speed_kmh"),
            "et_60ft_s": side_res.get("et_60ft_s"),
            "et_eighth_s": side_res.get("et_eighth_s"),
            "peak_power_hp": side_res.get("peak_power_hp"),
            "total_mass_kg": side_res.get("total_mass_kg"),
        }

    delta = res.get("delta", {})
    return {
        "a": summary(res.get("a", {})),
        "b": summary(res.get("b", {})),
        "delta": {
            "et_s": delta.get("et_s"),
            "trap_kmh": delta.get("trap_kmh"),
            "faster": delta.get("faster"),
            "cost_diff_inr": delta.get("cost_diff_inr"),
        },
        "note": "delta.et_s is B minus A — negative means B is faster.",
    }


def _t_list_venues(backend: Any, _args: dict) -> dict:
    rows = backend.list_venues().get("venues", [])
    return {
        "venues": [
            {
                "id": v.get("id"),
                "name": v.get("name"),
                "city": v.get("city"),
                "country": v.get("country"),
                "altitude_m": v.get("altitude_m"),
                "surface": v.get("surface_type"),
            }
            for v in rows
        ]
    }


def _t_search_parts(backend: Any, args: dict) -> dict:
    limit = min(int(args.get("limit") or 20), 60)
    kw: dict[str, Any] = {"limit": 500 if args.get("bike_id") else limit}
    if args.get("bike_id"):
        kw["bike_id"] = _need_int(args, "bike_id")
        kw["compatible_only"] = True
    if args.get("category"):
        kw["category"] = args["category"]
    if args.get("query"):
        kw["search"] = args["query"]
    res = backend.list_parts(**kw)
    parts = res.get("parts", [])[:limit]
    return {
        "total_matching": res.get("total"),
        "compatibility_filtered": bool(args.get("bike_id")),
        "parts": [
            {
                "id": p.get("id"),
                "brand": p.get("brand"),
                "name": p.get("model_name"),
                "category": p.get("category_name"),
                "price_inr": p.get("price_inr"),
                "power_delta_hp": p.get("power_delta_hp"),
                "mass_delta_kg": p.get("mass_delta_kg"),
            }
            for p in parts
        ],
    }


def _t_part_impact(backend: Any, args: dict) -> dict:
    part_id = _need_int(args, "part_id")
    base = _sim_payload(args)
    stock = backend.simulate_quick(dict(base))
    modded = backend.simulate_quick(dict(base, part_ids=[part_id]))
    applied = modded.get("parts_applied") or []
    if not applied:
        raise ToolError(
            f"Part {part_id} was not applied — it may not exist, or it is not "
            "compatible with this bike. Use search_parts with bike_id first."
        )
    et_a = float(stock["et_quarter_s"])
    et_b = float(modded["et_quarter_s"])
    cost = modded.get("build_cost_inr") or 0.0
    gain_s = et_a - et_b
    return {
        "part": {
            "id": applied[0].get("id"),
            "name": f"{applied[0].get('brand', '')} {applied[0].get('name', '')}".strip(),
            "price_inr": cost or None,
        },
        "bike": modded.get("bike_name"),
        "stock_et_s": round(et_a, 4),
        "modified_et_s": round(et_b, 4),
        "et_delta_s": round(et_b - et_a, 4),
        "trap_delta_kmh": round(
            float(modded["trap_speed_kmh"]) - float(stock["trap_speed_kmh"]), 2
        ),
        "cost_per_tenth_inr": (
            round(cost / (gain_s * 10.0), 0) if cost and gain_s > 1e-6 else None
        ),
        "note": "et_delta_s is after minus before — negative means faster.",
    }


def _sprocket_index(backend: Any, args: dict) -> tuple[dict[int, int], dict[int, int]]:
    """Map tooth-count → catalog part id for front and rear sprockets.

    The hosted API has no gearing parameter, so over HTTP a tooth-count swap is
    expressed as fitting the catalog sprocket that carries that count in its
    ``param_overrides`` (``drivetrain.front_sprocket`` / ``rear_sprocket``).
    Local mode never comes here — it sets the field directly.
    """
    kw: dict[str, Any] = {"category": "sprocket", "limit": 500}
    if args.get("bike_id"):
        kw["bike_id"] = int(args["bike_id"])
        kw["compatible_only"] = True
    front: dict[int, int] = {}
    rear: dict[int, int] = {}
    for p in backend.list_parts(**kw).get("parts", []):
        ov = p.get("param_overrides")
        if isinstance(ov, str):
            try:
                ov = json.loads(ov)
            except json.JSONDecodeError:
                continue
        if not isinstance(ov, dict):
            continue
        for key, table in (
            ("drivetrain.front_sprocket", front),
            ("drivetrain.rear_sprocket", rear),
        ):
            teeth = ov.get(key)
            if teeth is not None:
                table.setdefault(int(teeth), int(p["id"]))
    return front, rear


def _pick_sprockets(
    front_idx: dict[int, int], rear_idx: dict[int, int], front: int, rear: int
) -> list[int]:
    missing = []
    if front not in front_idx:
        missing.append(f"front {front}T")
    if rear not in rear_idx:
        missing.append(f"rear {rear}T")
    if missing:
        raise ToolError(
            "Over the hosted API a sprocket swap is expressed as a catalog part, "
            f"and none exists for {', '.join(missing)} on this bike. Available "
            f"front: {sorted(front_idx)}; rear: {sorted(rear_idx)}. Run the MCP "
            "server with MOTOQUANT_MCP_LOCAL=1 for arbitrary tooth counts."
        )
    return [front_idx[front], rear_idx[rear]]


def _t_gearing_impact(backend: Any, args: dict) -> dict:
    front_a, rear_a = _need_int(args, "front_a"), _need_int(args, "rear_a")
    front_b, rear_b = _need_int(args, "front_b"), _need_int(args, "rear_b")
    for teeth in (front_a, front_b):
        if not 8 <= teeth <= 30:
            raise ToolError(f"front sprocket {teeth}T is outside 8-30T.")
    for teeth in (rear_a, rear_b):
        if not 25 <= teeth <= 80:
            raise ToolError(f"rear sprocket {teeth}T is outside 25-80T.")

    base = _sim_payload(args)

    if getattr(backend, "supports_direct_gearing", False):
        a = backend.simulate_gearing(base, front_a, rear_a)
        b = backend.simulate_gearing(base, front_b, rear_b)
        method = "direct sprocket override (local physics)"
    else:
        front_idx, rear_idx = _sprocket_index(backend, args)
        ids_a = _pick_sprockets(front_idx, rear_idx, front_a, rear_a)
        ids_b = _pick_sprockets(front_idx, rear_idx, front_b, rear_b)
        payload = {
            f"a_{k}": v for k, v in base.items() if k in ("bike_id", "bike_preset")
        }
        payload.update(
            {f"b_{k}": v for k, v in base.items() if k in ("bike_id", "bike_preset")}
        )
        for key in ("rider_mass_kg", "power_boost_pct", "mass_delta_kg"):
            if base.get(key) is not None:
                payload[f"a_{key}"] = base[key]
                payload[f"b_{key}"] = base[key]
        for shared in ("venue_id", "ambient_temp_c", "humidity_pct", "headwind_kmh"):
            if base.get(shared) is not None:
                payload[shared] = base[shared]
        payload["a_part_ids"] = ids_a
        payload["b_part_ids"] = ids_b
        res = backend.compare(payload)
        ra, rb = res.get("a", {}), res.get("b", {})

        def _side(side_res: dict, f_t: int, r_t: int) -> dict:
            return {
                "front_sprocket": f_t,
                "rear_sprocket": r_t,
                "final_drive_ratio": round(r_t / f_t, 4),
                "et_s": side_res.get("et_quarter_s"),
                "trap_kmh": side_res.get("trap_speed_kmh"),
                "et_60ft_s": side_res.get("et_60ft_s"),
                "et_eighth_s": side_res.get("et_eighth_s"),
                "bike_name": side_res.get("bike_name"),
            }

        a, b = _side(ra, front_a, rear_a), _side(rb, front_b, rear_b)
        method = (
            "catalog sprocket parts via /api/simulate/compare (hosted API"
            f"{'' if args.get('bike_id') else ', fitment NOT checked — no bike_id'})"
        )

    return {
        "bike": a.get("bike_name"),
        "a": a,
        "b": b,
        "delta": {
            "et_s": round(float(b["et_s"]) - float(a["et_s"]), 4),
            "trap_kmh": round(float(b["trap_kmh"]) - float(a["trap_kmh"]), 2),
            "et_60ft_s": round(float(b["et_60ft_s"]) - float(a["et_60ft_s"]), 4),
            "faster": "B"
            if b["et_s"] < a["et_s"]
            else "A"
            if b["et_s"] > a["et_s"]
            else "tie",
        },
        "method": method,
        "note": (
            "Deltas are B minus A — negative means B is faster. A numerically "
            "taller rear sprocket shortens the final drive: quicker off the line, "
            "lower top speed, and an extra shift may cost more than it gains."
        ),
    }


# ─── Tool registry ────────────────────────────────────────────────────────


def _schema(props: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": props,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_bikes",
        "description": (
            "Search the 541-bike catalog by free text, manufacturer or category. "
            "Returns catalog ids to feed the simulation tools. Always start here "
            "when the user names a bike."
        ),
        "inputSchema": _schema(
            {
                "query": {
                    "type": "string",
                    "description": "Free text matched against manufacturer + model, e.g. 'hayabusa'.",
                },
                "manufacturer": {
                    "type": "string",
                    "description": "Exact manufacturer name.",
                },
                "category": {
                    "type": "string",
                    "description": "sport | naked | cruiser | adventure | touring | scooter …",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            }
        ),
        "handler": _t_search_bikes,
    },
    {
        "name": "get_bike",
        "description": (
            "Full spec sheet for one catalog bike: power, torque, mass, gearing, "
            "aero, OEM tires, and any published real-world benchmark ET on record."
        ),
        "inputSchema": _schema({"bike_id": _BIKE_PROPS["bike_id"]}, ["bike_id"]),
        "handler": _t_get_bike,
    },
    {
        "name": "simulate_quarter_mile",
        "description": (
            "Run a full physics quarter-mile pass and return ET, trap speed, the "
            "60-foot and eighth-mile splits. Optionally bolt on catalog parts "
            "(part_ids) to see the modified-vs-stock delta."
        ),
        "inputSchema": _schema(
            {
                **_BIKE_PROPS,
                **_CONDITION_PROPS,
                "part_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Catalog part ids from search_parts to fit before running.",
                },
            }
        ),
        "handler": _t_simulate_quarter_mile,
    },
    {
        "name": "simulate_top_speed",
        "description": (
            "Run until terminal velocity: top speed in km/h and mph, the time and "
            "distance to reach it, and the gear/RPM it tops out in."
        ),
        "inputSchema": _schema(
            {
                **_BIKE_PROPS,
                **_CONDITION_PROPS,
                "part_ids": {"type": "array", "items": {"type": "integer"}},
            }
        ),
        "handler": _t_simulate_top_speed,
    },
    {
        "name": "compare_bikes",
        "description": (
            "Head-to-head: two bikes (or two builds of the same bike) under "
            "identical conditions, with the ET/trap delta and a winner."
        ),
        "inputSchema": _schema(
            {
                "a_bike_id": {"type": "integer"},
                "a_bike_preset": {"type": "string", "enum": list(PRESETS)},
                "a_part_ids": {"type": "array", "items": {"type": "integer"}},
                "a_power_boost_pct": {"type": "number", "minimum": -50, "maximum": 200},
                "a_mass_delta_kg": {"type": "number", "minimum": -100, "maximum": 200},
                "a_rider_mass_kg": {"type": "number", "minimum": 20, "maximum": 250},
                "b_bike_id": {"type": "integer"},
                "b_bike_preset": {"type": "string", "enum": list(PRESETS)},
                "b_part_ids": {"type": "array", "items": {"type": "integer"}},
                "b_power_boost_pct": {"type": "number", "minimum": -50, "maximum": 200},
                "b_mass_delta_kg": {"type": "number", "minimum": -100, "maximum": 200},
                "b_rider_mass_kg": {"type": "number", "minimum": 20, "maximum": 250},
                "venue_id": _CONDITION_PROPS["venue_id"],
                "ambient_temp_c": _CONDITION_PROPS["ambient_temp_c"],
                "humidity_pct": _CONDITION_PROPS["humidity_pct"],
                "headwind_kmh": _CONDITION_PROPS["headwind_kmh"],
            }
        ),
        "handler": _t_compare_bikes,
    },
    {
        "name": "list_venues",
        "description": (
            "The seeded drag venues with altitude and surface. Pass a venue_id to "
            "the sim tools so density altitude and grip match the real strip."
        ),
        "inputSchema": _schema({}),
        "handler": _t_list_venues,
    },
    {
        "name": "search_parts",
        "description": (
            "Search the 593-part catalog. Pass bike_id to return ONLY parts that "
            "actually fit that bike (chain pitch, engine layout, displacement, "
            "stroke type are all checked)."
        ),
        "inputSchema": _schema(
            {
                "bike_id": {
                    "type": "integer",
                    "description": "Filter to parts compatible with this bike. Strongly recommended.",
                },
                "category": {
                    "type": "string",
                    "description": "exhaust | ecu | air_filter | sprocket | chain | clutch_kit | "
                    "quickshifter | nitrous | boost_kit | suspension | brakes | battery | "
                    "fuel_system | swingarm_ext | wheelie_bar | lockup_clutch | lowering_kit",
                },
                "query": {
                    "type": "string",
                    "description": "Brand or model text search.",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 60},
            }
        ),
        "handler": _t_search_parts,
    },
    {
        "name": "part_impact",
        "description": (
            "What one part is worth on one bike: runs stock and modified passes "
            "and returns the ET delta, trap delta and cost per tenth in INR."
        ),
        "inputSchema": _schema(
            {
                **_BIKE_PROPS,
                **_CONDITION_PROPS,
                "part_id": {
                    "type": "integer",
                    "description": "Catalog part id from search_parts.",
                },
            },
            ["part_id"],
        ),
        "handler": _t_part_impact,
    },
    {
        "name": "gearing_impact",
        "description": (
            "Sprocket what-if: compare two front/rear tooth combinations (e.g. "
            "16/45 vs 16/47) on the same bike and see what it does to the 60-foot, "
            "ET and trap speed. This is the classic drag-tuning question."
        ),
        "inputSchema": _schema(
            {
                **_BIKE_PROPS,
                **_CONDITION_PROPS,
                "front_a": {
                    "type": "integer",
                    "description": "Setup A front sprocket teeth.",
                },
                "rear_a": {
                    "type": "integer",
                    "description": "Setup A rear sprocket teeth.",
                },
                "front_b": {
                    "type": "integer",
                    "description": "Setup B front sprocket teeth.",
                },
                "rear_b": {
                    "type": "integer",
                    "description": "Setup B rear sprocket teeth.",
                },
            },
            ["front_a", "rear_a", "front_b", "rear_b"],
        ),
        "handler": _t_gearing_impact,
    },
]

TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


def public_tools() -> list[dict[str, Any]]:
    """Tool descriptors as sent over the wire (handlers stripped)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t["inputSchema"],
        }
        for t in TOOLS
    ]


# ─── JSON-RPC / MCP server ────────────────────────────────────────────────

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPServer:
    """Stateless MCP request handler (transport-agnostic)."""

    def __init__(self, backend: Any | None = None):
        self.backend = backend if backend is not None else make_backend()
        self.initialized = False

    # -- dispatch ----------------------------------------------------------
    def handle(self, msg: Any) -> dict | None:
        """Handle one decoded JSON-RPC message. Returns None for notifications."""
        if not isinstance(msg, dict):
            return _error(None, INVALID_REQUEST, "Request must be a JSON object")
        method = msg.get("method")
        msg_id = msg.get("id")
        if not isinstance(method, str):
            return _error(msg_id, INVALID_REQUEST, "Missing 'method'")
        params = msg.get("params") or {}
        if not isinstance(params, dict):
            return _error(msg_id, INVALID_PARAMS, "'params' must be an object")

        if msg_id is None:  # notification — never answered
            if method == "notifications/initialized":
                self.initialized = True
            return None

        try:
            if method == "initialize":
                return _result(msg_id, self._initialize(params))
            if method == "ping":
                return _result(msg_id, {})
            if method == "tools/list":
                return _result(msg_id, {"tools": public_tools()})
            if method == "tools/call":
                return _result(msg_id, self._call_tool(params))
        except ToolError as exc:
            return _result(msg_id, _tool_failure(str(exc)))
        except Exception as exc:  # noqa: BLE001 - never kill the loop
            return _error(msg_id, INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")
        return _error(msg_id, METHOD_NOT_FOUND, f"Unknown method: {method}")

    # -- methods -----------------------------------------------------------
    def _initialize(self, params: dict) -> dict:
        requested = params.get("protocolVersion")
        version = (
            requested
            if requested in SUPPORTED_PROTOCOL_VERSIONS
            else DEFAULT_PROTOCOL_VERSION
        )
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": SERVER_NAME,
                "title": "MotoQuant Pro — motorcycle drag physics",
                "version": SERVER_VERSION,
            },
            "instructions": INSTRUCTIONS,
        }

    def _call_tool(self, params: dict) -> dict:
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise ToolError("'arguments' must be an object")
        tool = TOOLS_BY_NAME.get(name)
        if tool is None:
            raise ToolError(
                f"Unknown tool {name!r}. Available: {', '.join(TOOLS_BY_NAME)}"
            )
        for key in tool["inputSchema"].get("required", []):
            if args.get(key) is None:
                raise ToolError(f"Missing required argument: {key}")
        payload = tool["handler"](self.backend, args)
        return {
            "content": [{"type": "text", "text": json.dumps(payload, default=str)}],
            "isError": False,
        }


def _result(msg_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _tool_failure(message: str) -> dict:
    """Tool-level failures ride back as a result with isError, per MCP spec —
    the model should see and recover from them, not the transport."""
    return {"content": [{"type": "text", "text": message}], "isError": True}


def serve(server: MCPServer, stdin: Any, stdout: Any) -> None:
    """Newline-delimited JSON-RPC loop (the MCP stdio transport)."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            _write(stdout, _error(None, PARSE_ERROR, f"Invalid JSON: {exc}"))
            continue
        if isinstance(msg, list):  # JSON-RPC batch
            responses = [r for r in (server.handle(m) for m in msg) if r is not None]
            for resp in responses:
                _write(stdout, resp)
            continue
        response = server.handle(msg)
        if response is not None:
            _write(stdout, response)


def _write(stdout: Any, payload: dict) -> None:
    stdout.write(json.dumps(payload, default=str) + "\n")
    stdout.flush()


# ─── Entrypoint ───────────────────────────────────────────────────────────


def selftest() -> int:
    """Drive the handshake + tools/list against ourselves, no network."""
    import io

    script = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "selftest", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "ping"},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope"}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(m) for m in script) + "\n")
    stdout = io.StringIO()
    server = MCPServer(backend=make_backend())
    serve(server, stdin, stdout)
    replies = [json.loads(x) for x in stdout.getvalue().splitlines()]

    ok = True

    def check(label: str, cond: bool) -> None:
        nonlocal ok
        ok = ok and cond
        print(f"  [{'ok' if cond else 'FAIL'}] {label}")

    print(f"MotoQuant MCP selftest — backend={server.backend.kind}")
    check("4 responses (notification produced none)", len(replies) == 4)
    init = replies[0].get("result", {})
    check(
        "initialize returns a supported protocolVersion",
        init.get("protocolVersion") in SUPPORTED_PROTOCOL_VERSIONS,
    )
    check(
        "initialize advertises tools capability",
        "tools" in init.get("capabilities", {}),
    )
    check("client marked us initialized", server.initialized)
    tools = replies[1].get("result", {}).get("tools", [])
    check(f"tools/list returned {len(tools)} tools", len(tools) == len(TOOLS))
    check(
        "every tool has a name, description and object schema",
        all(
            t.get("name")
            and t.get("description")
            and t.get("inputSchema", {}).get("type") == "object"
            for t in tools
        ),
    )
    check("ping answered", replies[2].get("result") == {})
    check(
        "unknown tool is an isError result, not a transport error",
        replies[3].get("result", {}).get("isError") is True,
    )
    print("selftest PASSED" if ok else "selftest FAILED")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m motoquant.mcp_server",
        description="MotoQuant MCP server (stdio JSON-RPC). See docs/MCP.md.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the handshake against ourselves and exit (no network).",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Force the local backend (same as MOTOQUANT_MCP_LOCAL=1).",
    )
    parser.add_argument("--api-url", default=None, help="Override MOTOQUANT_API_URL.")
    args = parser.parse_args(argv)

    if args.local:
        os.environ["MOTOQUANT_MCP_LOCAL"] = "1"
    if args.api_url:
        os.environ["MOTOQUANT_API_URL"] = args.api_url

    if args.selftest:
        return selftest()

    backend = make_backend()
    print(
        f"motoquant mcp server ready (backend={backend.kind}, {len(TOOLS)} tools)",
        file=sys.stderr,
    )
    try:
        serve(MCPServer(backend=backend), sys.stdin, sys.stdout)
    except (KeyboardInterrupt, BrokenPipeError):  # pragma: no cover
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
