"""In-memory per-IP rate limiting for cost-bearing public endpoints.

Why this exists: every route is free and anonymous. /api/chat spends real
LLM-provider tokens per call (the deployment operator's bill), and
/api/optimize/build + /api/autotune/ecu each pin the 0.5-CPU instance for
seconds-to-minutes of RK4 work. Without a fuse, one scraper hitting any of
these can exhaust the LLM quota or take the public instance down for
everyone. The limiter is stdlib-only and per-instance (fine for a
single-replica deployment), and resets on restart by design.

Buckets may use DIFFERENT windows (60 s per-minute fuses alongside the
86400 s daily chat cap). Each key therefore remembers its own window, and
eviction only ever drops a key once ITS OWN window has elapsed — never on
the window of whichever caller happened to trigger the sweep.

Not a general DDoS defence — that belongs at the edge. This is a cost
fuse.
"""

from __future__ import annotations

import hmac
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

# Address ranges a reverse proxy we may trust under AUTO can connect from:
# RFC 1918 private IPv4 and RFC 4193 unique-local IPv6 (loopback is handled
# separately). Listed explicitly rather than via ``is_private``, which is
# also True for the documentation ranges (192.0.2.0/24, 198.51.100.0/24,
# 203.0.113.0/24), link-local, 0.0.0.0/8 and more: none of those is where a
# proxy we run lives, and a client that reaches the API from one of them
# must not be able to choose its own bucket key.
_PRIVATE_PROXY_NETS = tuple(
    ipaddress.ip_network(n)
    for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
)

# Cloudflare's published edge ranges (https://www.cloudflare.com/ips/, as
# served on 2026-11-11). Render serves every web service through Cloudflare,
# custom domains included, so on Render the address its proxy reports for a
# request is one of these, not the client. See _render_cloudflare_client_ip().
# If Cloudflare adds a range, requests from it simply fall back to keying on
# the edge address (the behaviour before this list existed); never to a value
# the client chose.
_CLOUDFLARE_NETS = tuple(
    ipaddress.ip_network(n)
    for n in (
        "173.245.48.0/20",
        "103.21.244.0/22",
        "103.22.200.0/22",
        "103.31.4.0/22",
        "141.101.64.0/18",
        "108.162.192.0/18",
        "190.93.240.0/20",
        "188.114.96.0/20",
        "197.234.240.0/22",
        "198.41.128.0/17",
        "162.158.0.0/15",
        "104.16.0.0/13",
        "104.24.0.0/14",
        "172.64.0.0/13",
        "131.0.72.0/22",
        "2400:cb00::/32",
        "2606:4700::/32",
        "2803:f800::/32",
        "2405:b500::/32",
        "2405:8100::/32",
        "2a06:98c0::/29",
        "2c0f:f248::/32",
    )
)

#: The header in which Cloudflare passes the address that connected to it.
CF_CONNECTING_IP_HEADER = "cf-connecting-ip"

# One-time notes on what AUTO decided, so the choice is visible in the log
# rather than silent (keyed by decision; never logs header contents).
_auto_notes: set[str] = set()


def _note_once(key: str, level: int, msg: str, *args) -> None:
    if key not in _auto_notes:
        _auto_notes.add(key)
        logger.log(level, msg, *args)


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


def _peer_kind(peer: str | None) -> str:
    """Classify the socket peer for AUTO trust.

    * ``"local"``: a loopback address, a unix socket (no peer address) or an
      in-process transport (Starlette's TestClient reports "testclient").
    * ``"private"``: an RFC 1918 / RFC 4193 address, e.g. the Docker bridge
      gateway (172.17.0.1) that a host-side Caddy or nginx reaches a
      ``-p 8000:8000`` container from, or a proxy container on a user
      network (172.18.0.x).
    * ``"public"``: anything else, including a client hitting the API
      directly over the internet.

    IPv4-mapped IPv6 (``::ffff:172.17.0.1``, what a dual-stack listener
    reports for an IPv4 peer) is judged as the IPv4 address it carries.
    """
    if not peer:
        return "local"
    try:
        addr = ipaddress.ip_address(peer)
    except ValueError:
        return "local"  # not an IP at all -> not a network peer
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped
    if addr.is_loopback:
        return "local"
    if any(addr in net for net in _PRIVATE_PROXY_NETS):
        return "private"
    return "public"


def _effective_hops(peer: str | None, has_xff: bool = False) -> int:
    hops = trusted_proxy_hops()
    if hops is not None:
        return hops
    # AUTO. Render injects RENDER=true into every service and its proxy
    # APPENDS the peer it saw, so exactly one hop is trusted there. That peer
    # is Cloudflare's edge rather than the client; client_ip() takes the
    # client from Cloudflare (_render_cloudflare_client_ip).
    if os.environ.get("RENDER"):
        return 1
    # Off Render, trust one hop when the peer is on this machine or on a
    # private network: that is where the reverse proxy of a self-hosted
    # deployment connects from (docs/SELF_HOSTING.md section 4b). An API
    # reached directly over the internet sees a public peer and ignores the
    # header, so such a client cannot mint a fresh bucket per request by
    # rotating a spoofed X-Forwarded-For. A private peer that is NOT a proxy
    # (clients on the same LAN, or an L4 NAT such as rootless Docker or a
    # Kubernetes NodePort that rewrites every source to a private address)
    # needs MOTOQUANT_TRUSTED_PROXY_HOPS=0.
    kind = _peer_kind(peer)
    if kind == "local":
        return 1
    if kind == "private":
        if has_xff:
            _note_once(
                "private",
                logging.INFO,
                "rate limits: trusting one X-Forwarded-For hop from private "
                "peer %s (AUTO). If clients reach the API directly from a "
                "private network or through an L4 NAT, set %s=0.",
                peer,
                TRUSTED_PROXY_HOPS_ENV,
            )
        return 1
    if has_xff:
        _note_once(
            "public",
            logging.WARNING,
            "rate limits: ignoring X-Forwarded-For from public peer %s (AUTO); "
            "every request from it shares one bucket. If a reverse proxy you "
            "run connects from a public address, set %s=1; otherwise the "
            "header was client-sent and ignoring it is correct.",
            peer,
            TRUSTED_PROXY_HOPS_ENV,
        )
    return 0


#: Shared secret between the website's proxy and the API. When it is set on
#: both sides, the site's /api middleware (web/middleware.js) sends the
#: visitor's IP in PROXY_CLIENT_IP_HEADER together with the secret in
#: PROXY_AUTH_HEADER. Without it every visitor who reaches the API through the
#: site appears as one of Vercel's egress addresses and shares their rate-limit
#: buckets. Unset (the default, and every self-hosted copy that does not proxy
#: through Vercel): the headers are ignored.
PROXY_SECRET_ENV = "MOTOQUANT_PROXY_SECRET"
PROXY_AUTH_HEADER = "x-motoquant-proxy-auth"
PROXY_CLIENT_IP_HEADER = "x-motoquant-client-ip"
_MIN_PROXY_SECRET_LEN = 16


def proxy_secret_configured() -> bool:
    """True when the site-proxy secret is set (read per call, for tests)."""
    return len(os.environ.get(PROXY_SECRET_ENV, "")) >= _MIN_PROXY_SECRET_LEN


def _proxied_client_ip(request: Request) -> str | None:
    """The visitor IP the website's proxy vouched for, or None.

    Trusted only when the request carries the shared secret (constant-time
    compare) and the IP header parses as an address; anything else falls back
    to the X-Forwarded-For logic in :func:`client_ip`.
    """
    secret = os.environ.get(PROXY_SECRET_ENV, "")
    if len(secret) < _MIN_PROXY_SECRET_LEN:
        return None
    sent = request.headers.get(PROXY_AUTH_HEADER, "")
    if not sent or not hmac.compare_digest(sent.encode(), secret.encode()):
        return None
    raw = request.headers.get(PROXY_CLIENT_IP_HEADER, "").strip()
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def _is_cloudflare_edge(addr: str | None) -> bool:
    """True when ``addr`` is inside Cloudflare's published edge ranges."""
    if not addr:
        return False
    try:
        ip = ipaddress.ip_address(addr.strip())
    except ValueError:
        return False
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    return any(ip in net for net in _CLOUDFLARE_NETS)


def _is_private_hop(addr: str | None) -> bool:
    try:
        ip = ipaddress.ip_address((addr or "").strip())
    except ValueError:
        return False
    return ip.is_loopback or any(ip in net for net in _PRIVATE_PROXY_NETS)


def _past_private_hops(request: Request, seen: str | None) -> str | None:
    """When ``seen`` is a private (proxy-internal) address, the nearest
    X-Forwarded-For hop to its left that is not private; else ``seen``.

    Never steps over a public or malformed entry, so it cannot reach a value
    the client sent.
    """
    if not _is_private_hop(seen):
        return seen
    hops = [
        h.strip()
        for line in request.headers.getlist("x-forwarded-for")
        for h in line.split(",")
        if h.strip()
    ]
    for hop in reversed(hops):
        if _is_private_hop(hop):
            continue
        return hop[:_MAX_HOP_LEN]
    return seen


def _render_cloudflare_client_ip(request: Request, seen: str | None) -> str | None:
    """The client address Cloudflare reported, for a request that reached a
    Render service through Cloudflare; otherwise None.

    ``seen`` is the address the trusted proxy hops reported (see
    :func:`client_ip`). On Render the path is client -> Cloudflare ->
    Render's proxy -> uvicorn. Cloudflare appends the client to
    X-Forwarded-For and Render's proxy then appends the Cloudflare edge
    address it saw, so the one hop Render's proxy vouches for is a Cloudflare
    address that changes from request to request. (Render does not document
    the chain; it matches Cloudflare's documented append, the CF-RAY on every
    api.motoquant.in response and what Render users have observed.) Keying on
    it gave a client calling the API directly a fresh bucket on almost every
    call: on 2026-11-11, 35 direct calls to a 30-per-minute route all
    returned 200.

    When ``seen`` is inside Cloudflare's ranges, Cloudflare is the proxy that
    saw the client, and it passes that address in CF-Connecting-IP, the
    header its guide to restoring visitor IPs trusts from its own ranges.
    Cloudflare refuses a request whose client sent that header itself
    (checked on 2026-11-11: 403 "error code: 1000" from Cloudflare, on both
    api.motoquant.in and the onrender.com name). A Worker calling another
    Cloudflare zone arrives with a fixed Cloudflare address there.
    True-Client-IP is not used: Cloudflare passes a client-sent one through
    unchanged. This steps exactly one proxy further, never more, so a
    caller whose own address is in Cloudflare's ranges (a Worker, say) keys on
    that address and never on anything it sent.

    Only on Render (the RENDER env var), where every request passes
    Cloudflare. A self-hosted API can be called by a Cloudflare Worker
    directly, and a Worker may set CF-Connecting-IP itself on such a request;
    operators behind Cloudflare restore the visitor IP in their own reverse
    proxy instead (docs/SELF_HOSTING.md section 3b).

    No header, more than one header line, or a value that is not an address
    returns None, and the caller keeps keying on ``seen``: the old behaviour,
    never a value the client chose. Each of those cases, and a header that
    arrives while ``seen`` is outside the list, logs one warning (no
    addresses) so a deploy where this never engages shows in the log.
    """
    if not os.environ.get("RENDER"):
        return None
    values = request.headers.getlist(CF_CONNECTING_IP_HEADER)
    # Render adds its own internal proxy after the one that saw Cloudflare:
    # measured on 2026-11-12 (GET /api/whoami), the chain uvicorn receives is
    # "<client>, <Cloudflare edge>, <Render 10.x>", so the hop one trusted
    # proxy vouches for is Render's private address, not Cloudflare's. Step
    # left over Render's private hops to the first public one. A client can
    # only add entries LEFT of what Cloudflare appends, so a private hop on
    # the right always came from Render.
    seen = _past_private_hops(request, seen)
    if not _is_cloudflare_edge(seen):
        if values:
            _note_once(
                "cloudflare-unlisted",
                logging.WARNING,
                "rate limits: a request carries %s, but the address Render's "
                "proxy reported is not in Cloudflare's published ranges, so "
                "the header is not trusted and the request keys on that "
                "address. If Cloudflare has added ranges, update "
                "_CLOUDFLARE_NETS in motoquant/ratelimit.py.",
                CF_CONNECTING_IP_HEADER,
            )
        return None
    ip = None
    if len(values) == 1:
        try:
            ip = str(ipaddress.ip_address(values[0].strip()))
        except ValueError:
            ip = None
    if ip is None:
        _note_once(
            "cloudflare-missing",
            logging.WARNING,
            "rate limits: a request reached the API through Cloudflare without "
            "exactly one valid %s header; it keys on the Cloudflare edge "
            "address, so per-IP limits cannot group that client's requests",
            CF_CONNECTING_IP_HEADER,
        )
        return None
    _note_once(
        "cloudflare",
        logging.INFO,
        "rate limits: requests reach the API through Render's Cloudflare edge; "
        "keying on the client address in %s",
        CF_CONNECTING_IP_HEADER,
    )
    return ip


def client_ip(request: Request) -> str:
    """Best-effort client IP — the ONE place this repo derives a client
    identity from a request (every rate-limit bucket keys on it).

    X-Forwarded-For is honoured only for the configured number of trusted
    proxies (``MOTOQUANT_TRUSTED_PROXY_HOPS``; AUTO = 1 on Render or when the
    socket peer is loopback or a private RFC 1918 / ULA address, else 0).
    Each trusted proxy APPENDS the peer it observed, so with N trusted
    proxies the client is the N-th hop from the RIGHT. Every hop left of that
    is whatever the client itself sent — an attacker who rotates a spoofed
    value on every request would otherwise get a fresh bucket each time and
    bypass the fuse entirely.

    Repeated X-Forwarded-For header lines are joined in order, so a spoofed
    first line cannot shadow the line a proxy added.

    On Render the hop its proxy appends is Cloudflare's edge, not the
    client; :func:`_render_cloudflare_client_ip` then takes the client from
    Cloudflare.
    """
    return _client_identity(request)[0]


def _client_identity(request: Request) -> tuple[str, str, str | None]:
    """(client ip, rule that chose it, trusted-hop address) for client_ip()."""
    proxied = _proxied_client_ip(request)
    if proxied:
        return proxied, "site_proxy", None
    peer = request.client.host if request.client else None
    lines = request.headers.getlist("x-forwarded-for")
    hops_trusted = _effective_hops(peer, has_xff=bool(lines))
    seen = peer
    rule = "peer"
    if hops_trusted > 0:
        hops = [h.strip() for line in lines for h in line.split(",") if h.strip()]
        if hops:
            # Fewer entries than trusted proxies means every entry was added
            # by a trusted proxy; the leftmost is then the outermost peer.
            idx = -hops_trusted if len(hops) >= hops_trusted else 0
            seen = hops[idx][:_MAX_HOP_LEN]
            rule = "forwarded_for"
    cf = _render_cloudflare_client_ip(request, seen)
    if cf:
        return cf, "cloudflare_connecting_ip", seen
    return seen or "unknown", rule, seen


def _addr_class(addr: str | None, client: str | None = None) -> str:
    """A label for an address that never reveals it (except "you")."""
    if not addr:
        return "absent"
    try:
        ip = ipaddress.ip_address(addr.strip())
    except ValueError:
        return "invalid"
    if client and str(ip) == client:
        return "you"
    if _is_cloudflare_edge(str(ip)):
        return "cloudflare"
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return "private"
    return "other_public"


def describe_client(request: Request) -> dict:
    """What the API sees of the caller, for GET /api/whoami.

    Reveals the caller's own address (which they already know) and only a
    class for every other address on the path, so it is safe to serve to
    anyone. Used to check that per-IP limits key on the real client behind
    each public hostname.
    """
    ip, rule, seen = _client_identity(request)
    hops = [
        h.strip()
        for line in request.headers.getlist("x-forwarded-for")
        for h in line.split(",")
        if h.strip()
    ]
    cf_values = request.headers.getlist(CF_CONNECTING_IP_HEADER)
    if not cf_values:
        cf_class = "absent"
    elif len(cf_values) > 1:
        cf_class = "multiple"
    else:
        cf_class = _addr_class(cf_values[0], ip)
    return {
        "client_ip": ip,
        "rule": rule,
        "host": (request.headers.get("host") or "")[:100],
        "peer": _addr_class(request.client.host if request.client else None, ip),
        "forwarded_for": [_addr_class(h, ip) for h in hops][:10],
        "trusted_hop": _addr_class(seen, ip) if seen else None,
        "cf_connecting_ip": cf_class,
        "true_client_ip": bool(request.headers.get("true-client-ip")),
        "cdn_loop": (request.headers.get("cdn-loop") or "")[:100] or None,
        "on_render": bool(os.environ.get("RENDER")),
    }


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


def check(key: str, limit: int, window_s: float, cost: int = 1) -> tuple[bool, int]:
    """Count ``cost`` units (default one hit) against ``key``. Returns
    (allowed, retry_after_s)."""
    now = time.monotonic()
    with _LOCK:
        if len(_WINDOWS) > _MAX_KEYS:
            _evict_locked(now)
        t0, count, _ = _WINDOWS.get(key, (now, 0, window_s))
        if now - t0 > window_s:
            t0, count = now, 0
        count += max(1, int(cost))
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


def enforce(
    request: Request, name: str, limit: int, window_s: float, cost: int = 1
) -> None:
    """Count ``cost`` units (default one hit) for this client against bucket
    ``name``; raise 429 when over ``limit``. The imperative form of
    :func:`rate_limit`, for callers whose limit or cost is known only at
    request time (e.g. the daily chat cap, where a doctor question costs 2)."""
    if not RATE_LIMIT_ENABLED:
        return
    ip = client_ip(request)
    allowed, retry_after = check(f"{name}:{ip}", limit, window_s, cost)
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
        enforce(request, name, limit, window_s)

    return _dep


def reset() -> None:
    """Test helper: clear all windows."""
    with _LOCK:
        _WINDOWS.clear()
