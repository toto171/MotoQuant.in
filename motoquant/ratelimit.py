"""In-memory per-IP rate limiting for cost-bearing public endpoints.

Why this exists: /api/chat spends real LLM-provider tokens per call, and
/api/optimize/build + /api/autotune/ecu each pin the 0.5-CPU Render
instance for seconds-to-minutes of RK4 work. Before commercial launch,
one scraper hitting any of these can exhaust the LLM quota or take the
service down for everyone. This mirrors motoquant/auth.py's
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


def client_ip(request: Request) -> str:
    """Best-effort client IP behind the trusted proxy — the ONE place this repo
    derives a client identity from a request (rate-limit bucketing).

    Render terminates TLS upstream and *appends* the peer it observed to
    X-Forwarded-For, so with exactly one trusted proxy the RIGHTMOST hop is
    the real client. The leftmost hop is whatever the client itself sent — an
    attacker who rotates a spoofed leftmost value on every request would get a
    fresh bucket each time and bypass the fuse entirely. Take the rightmost."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        hops = [h.strip() for h in fwd.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"


def check(key: str, limit: int, window_s: float) -> tuple[bool, int]:
    """Count one hit against ``key``. Returns (allowed, retry_after_s)."""
    now = time.monotonic()
    with _LOCK:
        if len(_WINDOWS) > _MAX_KEYS:
            # Drop expired windows first.
            for k in [k for k, (t0, _) in _WINDOWS.items() if now - t0 > window_s]:
                del _WINDOWS[k]
            if len(_WINDOWS) > _MAX_KEYS:
                # Still oversized (a distinct-key flood): evict OLDEST-first
                # rather than clear() everything. Clearing wiped recent,
                # legitimate counters too (fail-open), letting a real abuser's
                # in-window count reset alongside everyone else's. Oldest-first
                # keeps the freshest counters intact.
                to_drop = len(_WINDOWS) - _MAX_KEYS + 1
                for k, _ in sorted(_WINDOWS.items(), key=lambda kv: kv[1][0])[:to_drop]:
                    _WINDOWS.pop(k, None)
        t0, count = _WINDOWS.get(key, (now, 0))
        if now - t0 > window_s:
            t0, count = now, 0
        count += 1
        _WINDOWS[key] = (t0, count)
        if count > limit:
            return False, max(1, int(window_s - (now - t0)) + 1)
        return True, 0


def heavy_gate_for(request: Request, name: str = "optimize", limit: int = 6):
    """Build a ``() -> bool`` fuse bound to this request's client IP.

    Captured at route time (job bodies run later on a worker with no Request
    in scope). Each call counts one hit against the same per-IP bucket the
    direct optimize/autotune routes use, so asking the chat agent for the
    heavy tools cannot out-run calling them directly."""
    ip = client_ip(request)

    def _gate() -> bool:
        if not RATE_LIMIT_ENABLED:
            return True
        allowed, _ = check(f"{name}:{ip}", limit, 60.0)
        return allowed

    return _gate


def rate_limit(name: str, limit: int, window_s: float = 60.0):
    """FastAPI dependency factory.

    Usage: ``@app.post(..., dependencies=[Depends(rate_limit("chat", 20))])``

    429 body carries a machine-readable error plus Retry-After so clients
    can back off politely.
    """

    def _dep(request: Request) -> None:
        if not RATE_LIMIT_ENABLED:
            return
        ip = client_ip(request)
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
