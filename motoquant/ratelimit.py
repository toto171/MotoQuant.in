"""In-memory per-IP rate limiting for cost-bearing public endpoints.

Why this exists: every route is free and anonymous. /api/chat spends real
LLM-provider tokens per call (the deployment operator's bill), and
/api/optimize/build + /api/autotune/ecu each pin the 0.5-CPU instance for
seconds-to-minutes of RK4 work. Without a fuse, one scraper hitting any of
these can exhaust the LLM quota or take the public instance down for
everyone. This mirrors motoquant/auth.py's in-process login-failure
limiter: stdlib-only, per-instance (fine for a single-replica deployment),
resets on restart by design.

Buckets may use DIFFERENT windows (60 s per-minute fuses alongside the
86400 s daily chat cap). Each key therefore remembers its own window, and
eviction only ever drops a key once ITS OWN window has elapsed — never on
the window of whichever caller happened to trigger the sweep.

Not a general DDoS defence — that belongs at the edge. This is a cost
fuse.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import threading
import time

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# key -> (window_start_monotonic, count, window_s). Fixed-window counting:
# simple, O(1), and precise enough for a cost fuse (worst case a burst of
# 2x limit straddling a window edge). The window length is stored PER KEY so
# eviction can honour it — see check().
_WINDOWS: dict[str, tuple[float, int, float]] = {}
_LOCK = threading.Lock()

# Bound the table so hostile traffic can't grow memory without limit.
_MAX_KEYS = 10_000

# Global kill-switch for tests / emergencies.
RATE_LIMIT_ENABLED = os.environ.get("MOTOQUANT_RATE_LIMIT", "true").lower() not in (
    "0",
    "false",
    "no",
)


# How many reverse proxies in front of the API append to X-Forwarded-For.
# Explicit integer >= 0; 0 means "never trust the header". Unset means AUTO
# (see trusted_proxy_hops()). Read per request so an operator (or a test)
# can change it without re-importing.
TRUSTED_PROXY_HOPS_ENV = "MOTOQUANT_TRUSTED_PROXY_HOPS"

# Longest X-Forwarded-For hop we will use as a bucket key (bounds memory if a
# trusted proxy ever forwards garbage).
_MAX_HOP_LEN = 64

_warned_bad_env: set[str] = set()


def trusted_proxy_hops() -> int | None:
    """Configured trusted-proxy hop count, or None for AUTO.

    An unparseable or negative value fails CLOSED to 0 (the header is never
    trusted) with a one-time warning, rather than silently trusting it.
    """
    raw = os.environ.get(TRUSTED_PROXY_HOPS_ENV)
    if raw is None or raw.strip() == "":
        return None
    try:
        hops = int(raw.strip())
        if hops < 0:
            raise ValueError
    except ValueError:
        if raw not in _warned_bad_env:
            _warned_bad_env.add(raw)
            logger.warning(
                "%s=%r is not a non-negative integer; X-Forwarded-For will "
                "NOT be trusted (every client keys on the socket peer)",
                TRUSTED_PROXY_HOPS_ENV,
                raw,
            )
        return 0
    return hops


def _peer_is_same_host(peer: str | None) -> bool:
    """True when the socket peer can only be a proxy on this machine: a
    loopback address, a unix socket (no peer address) or an in-process
    transport (Starlette's TestClient reports "testclient"). A remote client
    always shows up as a routable IP here."""
    if not peer:
        return True
    try:
        return ipaddress.ip_address(peer).is_loopback
    except ValueError:
        return True  # not an IP at all -> not a network peer


def _effective_hops(peer: str | None) -> int:
    hops = trusted_proxy_hops()
    if hops is not None:
        return hops
    # AUTO. Render injects RENDER=true into every service and its edge proxy
    # APPENDS the peer it saw, so exactly one hop is trusted there. Off
    # Render, trust one hop only from a same-host reverse proxy; an API
    # reached directly (the open-source `uvicorn motoquant.api:app` path)
    # ignores the header, so a client cannot mint a fresh bucket per request
    # by rotating a spoofed X-Forwarded-For.
    if os.environ.get("RENDER"):
        return 1
    return 1 if _peer_is_same_host(peer) else 0


def client_ip(request: Request) -> str:
    """Best-effort client IP — the ONE place this repo derives a client
    identity from a request (every rate-limit bucket keys on it).

    X-Forwarded-For is honoured only for the configured number of trusted
    proxies (``MOTOQUANT_TRUSTED_PROXY_HOPS``; AUTO = 1 on Render or behind a
    same-host proxy, else 0). Each trusted proxy APPENDS the peer it observed,
    so with N trusted proxies the client is the N-th hop from the RIGHT. Every
    hop left of that is whatever the client itself sent — an attacker who
    rotates a spoofed value on every request would otherwise get a fresh
    bucket each time and bypass the fuse entirely.

    Repeated X-Forwarded-For header lines are joined in order, so a spoofed
    first line cannot shadow the line a proxy added.
    """
    peer = request.client.host if request.client else None
    hops_trusted = _effective_hops(peer)
    if hops_trusted > 0:
        lines = request.headers.getlist("x-forwarded-for")
        hops = [h.strip() for line in lines for h in line.split(",") if h.strip()]
        if hops:
            # Fewer entries than trusted proxies means every entry was added
            # by a trusted proxy; the leftmost is then the outermost peer.
            idx = -hops_trusted if len(hops) >= hops_trusted else 0
            return hops[idx][:_MAX_HOP_LEN]
    return peer or "unknown"


def _evict_locked(now: float) -> None:
    """Shrink the table back under _MAX_KEYS. Caller holds _LOCK.

    Expiry is judged on each key's OWN stored window. The previous version
    dropped every key older than the CALLER's window_s, so under a
    distinct-key flood a 60 s-bucket call wiped daily-bucket counters after
    only a minute — silently resetting the LLM-bill fuse for every client.
    """
    for k in [k for k, (t0, _c, win) in _WINDOWS.items() if now - t0 > win]:
        del _WINDOWS[k]
    if len(_WINDOWS) > _MAX_KEYS:
        # Still oversized (a distinct-key flood): evict the counters CLOSEST
        # TO EXPIRY first rather than clear() everything. Clearing wiped
        # recent, legitimate counters too (fail-open), letting a real
        # abuser's in-window count reset alongside everyone else's. Ordering
        # by expiry time (t0 + own window) — not by start time — keeps a
        # long-window counter that started hours ago (and still has hours to
        # run) ahead of a minute-bucket that is about to lapse anyway.
        to_drop = len(_WINDOWS) - _MAX_KEYS + 1
        by_expiry = sorted(_WINDOWS.items(), key=lambda kv: kv[1][0] + kv[1][2])
        for k, _ in by_expiry[:to_drop]:
            _WINDOWS.pop(k, None)


def check(key: str, limit: int, window_s: float) -> tuple[bool, int]:
    """Count one hit against ``key``. Returns (allowed, retry_after_s)."""
    now = time.monotonic()
    with _LOCK:
        if len(_WINDOWS) > _MAX_KEYS:
            _evict_locked(now)
        t0, count, _ = _WINDOWS.get(key, (now, 0, window_s))
        if now - t0 > window_s:
            t0, count = now, 0
        count += 1
        _WINDOWS[key] = (t0, count, window_s)
        if count > limit:
            return False, max(1, int(window_s - (now - t0)) + 1)
        return True, 0


def _describe_window(window_s: float) -> str:
    if window_s >= 86400 and window_s % 86400 == 0:
        days = int(window_s // 86400)
        return "day" if days == 1 else f"{days} days"
    if window_s >= 3600 and window_s % 3600 == 0:
        hours = int(window_s // 3600)
        return "hour" if hours == 1 else f"{hours} hours"
    return f"{int(window_s)}s"


def enforce(request: Request, name: str, limit: int, window_s: float) -> None:
    """Count one hit for this client against bucket ``name``; raise 429 when
    over ``limit``. The imperative form of :func:`rate_limit`, for callers
    whose limit is read at request time (e.g. the daily chat cap)."""
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
                    f"{_describe_window(window_s)}. "
                    + ("Try again shortly." if window_s < 3600 else "Try again later.")
                ),
                "retry_after_s": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit(name: str, limit: int, window_s: float = 60.0):
    """FastAPI dependency factory.

    Usage: ``@app.post(..., dependencies=[Depends(rate_limit("chat", 20))])``

    429 body carries a machine-readable error plus Retry-After so clients
    can back off politely.
    """

    def _dep(request: Request) -> None:
        enforce(request, name, limit, window_s)

    return _dep


def reset() -> None:
    """Test helper: clear all windows."""
    with _LOCK:
        _WINDOWS.clear()
