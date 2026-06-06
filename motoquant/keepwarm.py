"""Self-ping keep-warm loop for Render's free tier.

Render free web services spin down after 15 minutes without *inbound*
traffic, and the GitHub Actions keep-alive cron (.github/workflows/
keepalive.yml) is throttled by GitHub to fire only every 1-8 hours in
practice — far short of its `*/14` schedule. Result (observed 2026-06-01 →
2026-06-06): the service slept between pings, every ping then hit a
multi-minute cold start, timed out, and the service went straight back to
sleep. Every keep-alive run failed with curl exit 28.

This module closes the gap from inside the app: once the service is awake
(woken by the GH cron, a deploy, or any visitor), a background task pings
its own public URL every ``MOTOQUANT_KEEPWARM_INTERVAL_S`` seconds (default
600 s) during the active window, which counts as inbound traffic and keeps
the instance warm. Outside the window the loop idles, the service sleeps
overnight as designed, and the next morning's GH-cron ping (or first
visitor) wakes it for the day.

Budget: the active window mirrors keepalive.yml (UTC 00:00-18:59 ≈ IST
05:30-23:59) → ~19 h/day ≈ 589 instance-hours in a 31-day month, inside
Render's 750 h/mo free allowance.

Hardening (2026-06-07): interval 600 s → 420 s and one in-iteration retry
60 s after a failed ping. Rationale: the loop lives inside the service it
keeps warm — if a single transient miss opens a >15-min idle gap, Render
sleeps the service, the loop dies with it, and the next wake waits on the
throttled GitHub cron (1-8 h). At 420 s even one fully missed iteration
leaves the worst-case gap at 840 s, inside the 15-min threshold; the 60 s
retry covers the common one-blip case long before that.

Activation: only when ``RENDER_EXTERNAL_URL`` is present (Render injects it
automatically) or ``MOTOQUANT_KEEPWARM_URL`` is set explicitly. Local dev,
CI, and the desktop sidecar never start the loop. Failures are logged and
swallowed — this must never affect API availability.
"""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger("motoquant.keepwarm")

#: Hours (UTC) during which the loop actively self-pings. Mirrors the
#: ``*/14 0-18 * * *`` cron window in .github/workflows/keepalive.yml.
ACTIVE_HOURS_UTC = range(19)

DEFAULT_INTERVAL_S = 420  # 7 min — two misses still fit Render's 15-min timer
RETRY_DELAY_S = 60.0  # in-iteration retry after a failed ping


def _resolve_base_url() -> str:
    """Public base URL to ping, or '' when keep-warm should stay off."""
    return (
        os.environ.get("MOTOQUANT_KEEPWARM_URL")
        or os.environ.get("RENDER_EXTERNAL_URL")
        or ""
    ).rstrip("/")


def _ping(url: str, timeout_s: float = 30.0) -> int | None:
    """Synchronous GET (run in a worker thread). Returns status or None."""
    req = urllib.request.Request(url, headers={"User-Agent": "motoquant-keepwarm/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status
    except Exception as exc:  # noqa: BLE001 — diagnostics only, never raise
        logger.warning("keep-warm ping to %s failed: %s", url, exc)
        return None


def _in_active_window(now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    return current.hour in ACTIVE_HOURS_UTC


async def _keepwarm_loop(health_url: str, interval_s: float) -> None:
    logger.info(
        "keep-warm loop started: %s every %.0fs during UTC hours %d-%d",
        health_url,
        interval_s,
        ACTIVE_HOURS_UTC[0],
        ACTIVE_HOURS_UTC[-1],
    )
    while True:
        try:
            if _in_active_window():
                status = await asyncio.to_thread(_ping, health_url)
                if status == 200:
                    logger.debug("keep-warm ping OK")
                else:
                    # In-iteration retry (2026-06-07 hardening): a single
                    # transient miss must never open a >15-min gap — Render
                    # would sleep the service, taking this loop down with it
                    # (it cannot resurrect itself; the next wake would wait
                    # on the throttled GitHub cron, potentially for hours).
                    logger.warning(
                        "keep-warm ping returned %s — retrying in %.0fs",
                        status,
                        RETRY_DELAY_S,
                    )
                    await asyncio.sleep(RETRY_DELAY_S)
                    status = await asyncio.to_thread(_ping, health_url)
                    if status == 200:
                        logger.info("keep-warm retry OK")
                    else:
                        logger.warning("keep-warm retry also failed (%s)", status)
            else:
                logger.debug("keep-warm idle (outside active window)")
        except Exception:  # noqa: BLE001 — the loop must survive anything
            logger.warning("keep-warm iteration failed", exc_info=True)
        await asyncio.sleep(interval_s)


def start_keepwarm() -> asyncio.Task[None] | None:
    """Start the background loop if configured. Safe to call unconditionally.

    Returns the task (so callers/tests can cancel it) or None when disabled.
    Must be called from within a running event loop (e.g. a FastAPI startup
    hook).
    """
    base_url = _resolve_base_url()
    if not base_url:
        logger.info(
            "keep-warm disabled (no RENDER_EXTERNAL_URL / MOTOQUANT_KEEPWARM_URL)"
        )
        return None
    try:
        interval_s = float(
            os.environ.get("MOTOQUANT_KEEPWARM_INTERVAL_S", DEFAULT_INTERVAL_S)
        )
    except ValueError:
        interval_s = float(DEFAULT_INTERVAL_S)
    interval_s = max(60.0, interval_s)  # floor: never hammer more than 1/min
    health_url = f"{base_url}/api/health"
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("keep-warm not started: no running event loop")
        return None
    return loop.create_task(
        _keepwarm_loop(health_url, interval_s), name="motoquant-keepwarm"
    )
