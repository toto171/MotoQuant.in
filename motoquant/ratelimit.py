"""In-memory per-IP rate limiting for cost-bearing public endpoints.

Why this exists: /api/chat spends real LLM-provider tokens per call, and
/api/optimize/build + /api/autotune/ecu each pin the 0.5-CPU Render
instance for seconds-to-minutes of RK4 work. Before commercial launch,
one scraper hitting any of these can exhaust the LLM quota or take the
paid service down for everyone. This mirrors motoquant/auth.py's
in-process login-failure limiter: stdlib-only, per-instance (fine for a
single-replica deployment), resets on restart by design.

Not a general DDoS defence — that belongs at the edge. This is a cost
fuse.
"""

from __future__ import annotations

import os
import threading
import time

from fastapi import HTTPException, Request

# key -> (window_start_monotonic, count). Fixed-window counting: simple,
# O(1), and precise enough for a cost fuse (worst case a burst of
# 2x limit straddling a window edge).
_WINDOWS: dict[str, tuple[float, int]] = {}
_LOCK = threading.Lock()

# Bound the table so hostile traffic can't grow memory without limit.
_MAX_KEYS = 10_000

# Global kill-switch for tests / emergencies.
RATE_LIMIT_ENABLED = os.environ.get("MOTOQUANT_RATE_LIMIT", "true").lower() not in (
    "0",
    "false",
    "no",
)


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Render terminates TLS upstream, so the
    peer address is the proxy — prefer the first X-Forwarded-For hop."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def check(key: str, limit: int, window_s: float) -> tuple[bool, int]:
    """Count one hit against ``key``. Returns (allowed, retry_after_s)."""
    now = time.monotonic()
    with _LOCK:
        if len(_WINDOWS) > _MAX_KEYS:
            # Drop expired windows first; if still oversized, start fresh
            # (fail-open: better to briefly forget counts than to OOM).
            for k in [k for k, (t0, _) in _WINDOWS.items() if now - t0 > window_s]:
                del _WINDOWS[k]
            if len(_WINDOWS) > _MAX_KEYS:
                _WINDOWS.clear()
        t0, count = _WINDOWS.get(key, (now, 0))
        if now - t0 > window_s:
            t0, count = now, 0
        count += 1
        _WINDOWS[key] = (t0, count)
        if count > limit:
            return False, max(1, int(window_s - (now - t0)) + 1)
        return True, 0


def rate_limit(name: str, limit: int, window_s: float = 60.0):
    """FastAPI dependency factory.

    Usage: ``@app.post(..., dependencies=[Depends(rate_limit("chat", 20))])``

    429 body carries a machine-readable error plus Retry-After so clients
    can back off politely.
    """

    def _dep(request: Request) -> None:
        if not RATE_LIMIT_ENABLED:
            return
        ip = _client_ip(request)
        allowed, retry_after = check(f"{name}:{ip}", limit, window_s)
        if not allowed:
            raise HTTPException(
                429,
                detail={
                    "error": "rate_limited",
                    "message": (
                        f"Too many {name} requests — limit is {limit} per "
                        f"{int(window_s)}s. Try again shortly."
                    ),
                    "retry_after_s": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

    return _dep


def reset() -> None:
    """Test helper: clear all windows."""
    with _LOCK:
        _WINDOWS.clear()
