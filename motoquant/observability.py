"""
motoquant.observability
========================
Optional production error tracking via Sentry.

Soft-dep: `sentry-sdk` is listed in requirements-api.txt but the import
gracefully no-ops if the package is missing OR no DSN is configured. This
means a developer running locally without `SENTRY_DSN` set sees zero
behaviour change, and a CI run without the package installed doesn't
break either.

Activation
----------
Set ONE env var on Railway (or wherever the API is deployed):
    SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>

Optional knobs:
    SENTRY_ENVIRONMENT       — defaults to "production" if SENTRY_DSN is set,
                               else "development". Override with e.g. "staging".
    SENTRY_TRACES_SAMPLE_RATE — float 0.0–1.0, default 0.05 (5 % of requests
                                get full performance traces). Tune down for
                                high-traffic; up for early-stage debugging.
    SENTRY_RELEASE           — defaults to motoquant.__version__.

Why env-gated?
--------------
We don't want to ship a hardcoded DSN — different environments (Railway prod,
staging, the user's local laptop) need their own DSN. A hardcoded DSN also
leaks to anyone who clones the repo. Env-gating means each deploy supplies
its own observability namespace.
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_INITIALISED = False


def init_sentry(*, app_name: str = "motoquant-api") -> bool:
    """
    Initialise Sentry if SENTRY_DSN is set AND sentry-sdk is importable.
    Returns True if Sentry was initialised, False otherwise (silent no-op).

    Idempotent — safe to call from multiple entry points (FastAPI startup,
    CLI, scheduled tasks).
    """
    global _INITIALISED
    if _INITIALISED:
        return True

    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        log.debug("SENTRY_DSN not set — observability disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        log.warning(
            "SENTRY_DSN is set but sentry-sdk is not installed. "
            "Run `pip install sentry-sdk[fastapi]` to enable error tracking."
        )
        print(
            "[observability] Sentry NOT active — SENTRY_DSN is set but sentry-sdk "
            "is not installed (add sentry-sdk[fastapi] to requirements-api.txt)",
            flush=True,
        )
        return False

    sample_rate = _safe_float("SENTRY_TRACES_SAMPLE_RATE", 0.05)
    environment = os.environ.get(
        "SENTRY_ENVIRONMENT", "production" if dsn else "development"
    )
    release = os.environ.get("SENTRY_RELEASE")
    if release is None:
        try:
            from motoquant import __version__ as _mq_version

            release = f"{app_name}@{_mq_version}"
        except Exception:
            release = None

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=sample_rate,
        # Send PII (e.g. usernames) only if explicitly opted in. Default off
        # to keep us on the safe side of DPDP Act + similar privacy regs.
        send_default_pii=os.environ.get("SENTRY_SEND_PII", "").lower() == "true",
        # Auto-instrument FastAPI requests + capture WARNING+ logs as breadcrumbs
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        # Tag every event with the app name so multi-app projects can filter
        before_send=lambda event, _hint: _tag_app(event, app_name),
    )
    _INITIALISED = True
    log.info("Sentry initialised — environment=%s release=%s", environment, release)
    # Also print to stdout. Render/uvicorn do NOT surface INFO from the
    # `motoquant.observability` logger by default, and sentry_sdk.init() is
    # itself silent — so without this line a running deploy gives no signal that
    # error tracking is live (exactly the ambiguity hit on 2026-07-01). This
    # only fires when a DSN is set, so a DSN-free local/CI run stays completely
    # silent, per this module's "invisible unless SENTRY_DSN" contract.
    print(
        f"[observability] Sentry active — environment={environment} release={release}",
        flush=True,
    )
    return True


def _safe_float(env_var: str, default: float) -> float:
    """Parse an env var as float; return default on missing/malformed."""
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        log.warning("Invalid float in $%s=%r — using default %s", env_var, raw, default)
        return default


def _tag_app(event: dict[str, Any], app_name: str) -> dict[str, Any]:
    """Add `app: <app_name>` to the tags of every Sentry event."""
    tags = event.get("tags") or {}
    if isinstance(tags, dict):
        tags["app"] = app_name
    else:
        tags = {"app": app_name}
    event["tags"] = tags
    return event


def is_initialised() -> bool:
    """Return True if init_sentry() has successfully initialised Sentry.

    Lets other modules (e.g. an API health/debug route) report activation state
    without re-reading the env or re-running init.
    """
    return _INITIALISED


__all__ = ["init_sentry", "is_initialised"]
