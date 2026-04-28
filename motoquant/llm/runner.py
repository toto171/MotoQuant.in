"""
runner -- end-to-end chat pipeline shared by CLI and API.

This is the single source of truth for "given a NL query + DB, run the sim
and produce a summary". Both `motoquant chat` and `POST /api/chat` call into
this module so the two surfaces never drift.

Pure data in, structured data out. No printing, no HTTP -- the caller
formats / serializes as appropriate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from ..constants import MS_TO_KMH, MS_TO_MPH
from ..physics import MotoQuantEngine
from .client import LLMClient, LLMNotConfiguredError
from .parse_query import ParsedSimRequest, parse_query
from .summarize import summarize_result

__all__ = ["ChatResult", "run_chat_pipeline"]


# ───────────────────────────────────────────────────────────────────
# ChatResult -- structured return value
# ───────────────────────────────────────────────────────────────────


@dataclass
class ChatResult:
    """End-to-end result of a chat query.

    Sentinel semantics:
      - error == None and bike_id != None and sim_result != None  -> success
      - error == "bike_not_found"                                  -> use bike_suggestions
      - error == "llm_not_configured"                              -> ANTHROPIC_API_KEY missing
      - error == "parse_failed"                                    -> Claude refused / bad response
      - error == "sim_failed"                                      -> physics blew up
    """

    raw_query: str
    bike_name: str = ""
    bike_id: int | None = None
    venue_name: str | None = None
    venue_id: int | None = None
    parsed_notes: str = ""
    optimization_goal: str = "minimize_et"

    # Populated when bike_id is None and we want to show alternatives in the UI.
    bike_suggestions: list[dict[str, Any]] = field(default_factory=list)

    # Populated on success.
    sim_result: dict[str, Any] | None = None
    summary: str | None = None

    # Failure mode (None on success).
    error: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ───────────────────────────────────────────────────────────────────
# Public entry point
# ───────────────────────────────────────────────────────────────────


def run_chat_pipeline(
    query: str,
    db: Any,
    *,
    client: LLMClient | None = None,
    run_summary: bool = True,
    suggestion_limit: int = 5,
) -> ChatResult:
    """End-to-end: parse -> resolve -> run sim -> summarize.

    Args:
      query: User's NL string.
      db: MotoQuantDB (initialized).
      client: Optional LLMClient. Defaults to module singleton.
      run_summary: If False, skip the summarization LLM call (saves a
        token round-trip for callers that just want structured data).
      suggestion_limit: Max bike suggestions to return on bike_not_found.

    Returns:
      ChatResult. Caller is responsible for formatting (CLI panel,
      JSON over HTTP, etc.). Never raises -- all failures surface via
      the `error` field.
    """
    result = ChatResult(raw_query=query)

    # ── 1. Parse with Claude ──────────────────────────────────────────
    try:
        parsed = parse_query(query, db=db, client=client)
    except LLMNotConfiguredError as e:
        result.error = "llm_not_configured"
        result.error_detail = str(e)
        return result
    except Exception as e:  # noqa: BLE001 -- intentional broad catch on edge
        result.error = "parse_failed"
        result.error_detail = f"{type(e).__name__}: {e}"
        return result

    result.bike_name = parsed.bike_name
    result.bike_id = parsed.bike_id
    result.venue_name = parsed.venue_name
    result.venue_id = parsed.venue_id
    result.parsed_notes = parsed.notes
    result.optimization_goal = parsed.optimization_goal

    # ── 2. Bike-not-found: return suggestions, do not run sim ─────────
    if parsed.bike_id is None:
        result.error = "bike_not_found"
        result.error_detail = (
            f"Could not match '{parsed.bike_name}' to any bike in the catalog."
        )
        result.bike_suggestions = _bike_suggestions(
            db, parsed.bike_name, limit=suggestion_limit
        )
        return result

    # ── 3. Build config + apply env overrides ─────────────────────────
    try:
        config_row = db.bikes.get_current_config(parsed.bike_id)
    except Exception as e:  # noqa: BLE001
        result.error = "sim_failed"
        result.error_detail = f"db.bikes.get_current_config: {e}"
        return result

    if config_row is None:
        result.error = "sim_failed"
        result.error_detail = f"No bike_configs row for bike_id {parsed.bike_id}"
        return result

    env = None
    if parsed.venue_id is not None:
        try:
            env = db.venues.to_environment(
                parsed.venue_id, month=datetime.now().month
            )
        except Exception:
            env = None  # fall through to bike's default environment

    try:
        config = db.bikes.to_config(config_row["id"], environment=env)
    except Exception as e:  # noqa: BLE001
        result.error = "sim_failed"
        result.error_detail = f"db.bikes.to_config: {e}"
        return result

    if config is None:
        result.error = "sim_failed"
        result.error_detail = f"to_config returned None for {config_row['id']}"
        return result

    _apply_env_overrides(config, parsed)
    _apply_power_boost(config, parsed)

    # ── 4. Run sim ────────────────────────────────────────────────────
    try:
        engine = MotoQuantEngine(config)
        sim = engine.run()
    except Exception as e:  # noqa: BLE001
        result.error = "sim_failed"
        result.error_detail = f"MotoQuantEngine.run: {type(e).__name__}: {e}"
        return result

    sim_dict: dict[str, Any] = {
        "et_s": round(float(sim.time_quarter), 4),
        "trap_speed_kmh": round(float(sim.speed_quarter) * MS_TO_KMH, 1),
        "trap_speed_mph": round(float(sim.speed_quarter) * MS_TO_MPH, 1),
        "sixty_foot_s": round(float(sim.time_60ft), 4),
        "peak_accel_g": round(float(np.max(sim.a)), 2),
    }

    # Splits: only include if the sim object exposes them as floats.
    for attr, key in (
        ("time_330ft", "330ft_s"),
        ("time_eighth", "eighth_s"),
        ("time_1000ft", "1000ft_s"),
    ):
        val = getattr(sim, attr, None)
        if val is not None:
            try:
                sim_dict[key] = round(float(val), 4)
            except (TypeError, ValueError):
                pass

    result.sim_result = sim_dict

    # ── 5. Summarize via Claude (optional) ────────────────────────────
    if run_summary:
        try:
            result.summary = summarize_result(parsed, sim_dict, client=client)
        except Exception as e:  # noqa: BLE001
            # Don't fail the whole chat just because summarization tripped --
            # the caller still gets the sim numbers.
            result.summary = f"(summary failed: {type(e).__name__}: {e})"

    return result


# ───────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────


def _apply_env_overrides(config: Any, parsed: ParsedSimRequest) -> None:
    """Mutate config.environment in place from parsed query overrides."""
    if parsed.ambient_temp_c is not None:
        config.environment.ambient_temp_c = float(parsed.ambient_temp_c)
    if parsed.humidity_pct is not None:
        config.environment.relative_humidity_pct = float(parsed.humidity_pct)
    if parsed.altitude_m is not None:
        config.environment.altitude_m = float(parsed.altitude_m)
    if parsed.headwind_kmh is not None:
        config.environment.wind_speed_ms = float(parsed.headwind_kmh) / 3.6
        config.environment.wind_direction_deg = 0  # head-on


def _apply_power_boost(config: Any, parsed: ParsedSimRequest) -> None:
    """Scale stock power/torque by the parsed power_boost_pct."""
    if not parsed.power_boost_pct:
        return
    multiplier = 1.0 + float(parsed.power_boost_pct) / 100.0
    config.engine.peak_power_hp *= multiplier
    config.engine.peak_torque_nm *= multiplier
    # If a stored dyno curve exists, scale it too so /api/simulate?bike_id
    # picks up the boost (avoids the documented dead-knob bug).
    dyno = getattr(config.engine, "dyno_curve", None)
    if dyno is not None and getattr(dyno, "torque_nm", None) is not None:
        try:
            dyno.torque_nm = [t * multiplier for t in dyno.torque_nm]
        except (TypeError, AttributeError):
            pass


def _bike_suggestions(
    db: Any, bike_name: str, *, limit: int = 5
) -> list[dict[str, Any]]:
    """Return up to `limit` bikes that loosely match bike_name.

    Strategy: try the existing fuzzy search with progressively shorter
    prefixes of the LLM-extracted name. Empty list if no DB or no hits.
    """
    if not bike_name or db is None:
        return []

    # Try the full name, then each whitespace-split token from longest first.
    queries: list[str] = [bike_name]
    tokens = sorted(
        (t for t in bike_name.replace("-", " ").split() if len(t) >= 3),
        key=len,
        reverse=True,
    )
    for tok in tokens:
        if tok not in queries:
            queries.append(tok)

    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for q in queries:
        try:
            rows = db.bikes.search(name_contains=q)
        except Exception:
            continue
        for row in rows or []:
            rid = row.get("id")
            if rid in seen:
                continue
            seen.add(rid)
            out.append(
                {
                    "id": rid,
                    "manufacturer": row.get("manufacturer_name"),
                    "model": row.get("model_name"),
                    "year_range": _format_year_range(row),
                }
            )
            if len(out) >= limit:
                return out
    return out


def _format_year_range(row: dict[str, Any]) -> str | None:
    start = row.get("year_start")
    end = row.get("year_end")
    if not start:
        return None
    if not end or end == start:
        return str(start)
    return f"{start}-{end}"
