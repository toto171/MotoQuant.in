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

Key scrubbing
-------------
Every event and transaction passes through :func:`scrub_event` before it
leaves the process, whatever SENTRY_SEND_PII says: the X-Anthropic-Key,
Authorization and X-Api-Key request headers are removed and any
``sk-ant-...`` substring anywhere in the event (messages, exception
values, stack-frame variables, breadcrumbs, request bodies) becomes
"[redacted]".

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
import re
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
        # STDOUT on purpose: Render surfaces stdout in the deploy log, while
        # log.warning is invisible without a logging config. DSN-free runs
        # never reach this branch, so local/CI stays completely silent.
        print("[observability] Sentry NOT active — sentry-sdk missing")
        log.warning(
            "SENTRY_DSN is set but sentry-sdk is not installed. "
            "Run `pip install sentry-sdk[fastapi]` to enable error tracking."
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

    # Keep the LLM SDK AUTO-integrations off. The Anthropic one captures
    # provider errors at the SDK boundary as handled:no BEFORE our
    # llm/client.py translation runs, and can attach prompts and request
    # data to events. Our LLM layer owns provider-error handling and
    # redaction. The OpenAI one stays off too (the chat layer is Claude only;
    # this guards against a stray install). (`disabled_integrations` needs
    # sentry-sdk >= 2.11; see the floor in requirements-api.txt.)
    disabled_integrations: list[Any] = []
    try:
        from sentry_sdk.integrations.openai import OpenAIIntegration

        disabled_integrations.append(OpenAIIntegration())
    except Exception:  # noqa: BLE001 - ImportError, or sentry's DidNotEnable when openai is absent
        pass
    try:
        from sentry_sdk.integrations.anthropic import AnthropicIntegration

        disabled_integrations.append(AnthropicIntegration())
    except Exception:  # noqa: BLE001 - ImportError, or sentry's DidNotEnable
        pass

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
        disabled_integrations=disabled_integrations,
        # Scrub keys out of every event (kept on even with SENTRY_SEND_PII),
        # then tag it with the app name so multi-app projects can filter.
        before_send=lambda event, _hint: _before_send(event, app_name),
        before_send_transaction=lambda event, _hint: scrub_event(event),
    )
    _INITIALISED = True
    # STDOUT on purpose (see the ImportError branch above): only fires when a
    # DSN is present, so DSN-free local/CI runs stay completely silent.
    print(
        f"[observability] Sentry active — environment={environment} release={release}"
    )
    log.info("Sentry initialised — environment=%s release=%s", environment, release)
    return True


def is_initialised() -> bool:
    """True once init_sentry() has successfully initialised the SDK."""
    return _INITIALISED


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


# Request headers that carry credentials. Compared case-insensitively with
# "_" and "-" treated alike, because Sentry and ASGI spell them both ways.
_SECRET_HEADERS = {
    "x-anthropic-key",
    "authorization",
    "x-api-key",
    "x-motoquant-proxy-auth",
}
_SECRET_RE = re.compile(r"sk-ant-[^\s\"'<>\\]*")
_REDACTED = "[redacted]"


def _is_secret_header(name: Any) -> bool:
    return isinstance(name, str) and name.strip().lower().replace("_", "-") in (
        _SECRET_HEADERS
    )


def _scrub(node: Any, depth: int = 0) -> Any:
    if depth > 50:
        return node
    if isinstance(node, str):
        return _SECRET_RE.sub(_REDACTED, node)
    if isinstance(node, dict):
        return {
            k: (_REDACTED if _is_secret_header(k) else _scrub(v, depth + 1))
            for k, v in node.items()
        }
    if isinstance(node, list):
        # Header lists arrive as [[name, value], ...] in some integrations.
        out = []
        for item in node:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 2
                and _is_secret_header(item[0])
            ):
                out.append([item[0], _REDACTED])
            else:
                out.append(_scrub(item, depth + 1))
        return out
    if isinstance(node, tuple):
        return tuple(_scrub(v, depth + 1) for v in node)
    return node


def scrub_event(event: dict[str, Any]) -> dict[str, Any]:
    """Remove credential headers and redact every ``sk-ant-`` substring.

    Never raises: a scrubber failure drops the event rather than sending it
    unscrubbed.
    """
    try:
        request = event.get("request")
        if isinstance(request, dict) and isinstance(request.get("headers"), dict):
            request["headers"] = {
                k: v for k, v in request["headers"].items() if not _is_secret_header(k)
            }
        return _scrub(event)
    except Exception:  # noqa: BLE001
        return None  # type: ignore[return-value]


def _before_send(event: dict[str, Any], app_name: str) -> dict[str, Any] | None:
    scrubbed = scrub_event(event)
    return None if scrubbed is None else _tag_app(scrubbed, app_name)


def _tag_app(event: dict[str, Any], app_name: str) -> dict[str, Any]:
    """Add `app: <app_name>` to the tags of every Sentry event."""
    tags = event.get("tags") or {}
    if isinstance(tags, dict):
        tags["app"] = app_name
    else:
        tags = {"app": app_name}
    event["tags"] = tags
    return event


__all__ = ["init_sentry", "is_initialised", "scrub_event"]
