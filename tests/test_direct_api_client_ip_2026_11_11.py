"""Per-IP limits must group a client that calls the API directly on Render.

Measured on 2026-11-11 against the live deploy of e6a2743: 35 calls to
``POST /api/simulate/quick`` (30 per 60 s) from one IPv4 straight to
https://api.motoquant.in all returned 200, in parallel and over one
keep-alive connection alike. The same 35 through https://motoquant.in, where
the site's middleware vouches for the visitor IP, gave 30 x 200 then 5 x 429.

Render serves every web service through Cloudflare: each api.motoquant.in
response carries a CF-RAY, and the name resolves through
``*.onrender.com`` to ``*.cdn.cloudflare.net``. Cloudflare appends the client
to X-Forwarded-For and Render's proxy then appends the Cloudflare edge address
it saw, so the one hop that ``MOTOQUANT_TRUSTED_PROXY_HOPS=1`` trusts was a
Cloudflare address that changes from request to request, and nearly every
call got a fresh bucket. Every per-IP fuse, the chat limits and the daily chat
cap among them, could be bypassed by calling the API directly.

``client_ip()`` now takes the client from CF-Connecting-IP when the trusted
hop is a Cloudflare address, on Render only, stepping exactly one proxy
further. A client cannot send that header itself: on 2026-11-11 Cloudflare
answered such a request to api.motoquant.in with 403 "error code: 1000"
before it reached Render. The requests below are what uvicorn receives on Render: a 10.x socket
peer (Render's proxy), X-Forwarded-For ``[whatever the client sent,] client,
Cloudflare edge``, and CF-Connecting-IP as Cloudflare set it.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile

import pytest

pytest.importorskip("fastapi")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import ratelimit  # noqa: E402

RENDER_PROXY = ("10.201.3.4", 40000)  # Render's proxy, the socket peer
CLIENT = "49.36.0.7"
OTHER_CLIENT = "49.36.0.8"
WORKER = "2a06:98c0:3600::103"  # what a Cloudflare Worker arrives as
SECRET = "test-proxy-secret-" + "x" * 24  # dummy, compared in memory only


def _edge(i: int) -> str:
    """A different Cloudflare edge address per request (162.158.0.0/15)."""
    return f"162.158.{i % 256}.{i // 256 + 1}"


def _via_cloudflare(client: str, i: int, sent_xff: str | None = None) -> dict:
    """Headers as uvicorn sees them on Render for request number ``i``."""
    chain = f"{client}, {_edge(i)}"
    if sent_xff:
        chain = f"{sent_xff}, {chain}"
    return {"x-forwarded-for": chain, "cf-connecting-ip": client}


@pytest.fixture(params=["1", None], ids=["hops=1 (dashboard)", "hops=auto"])
def on_render(request, monkeypatch):
    """The production environment: RENDER set by Render, and
    MOTOQUANT_TRUSTED_PROXY_HOPS either pinned to 1 (as on the live service)
    or unset (AUTO)."""
    monkeypatch.setenv("RENDER", "true")
    if request.param is None:
        monkeypatch.delenv(ratelimit.TRUSTED_PROXY_HOPS_ENV, raising=False)
    else:
        monkeypatch.setenv(ratelimit.TRUSTED_PROXY_HOPS_ENV, request.param)
    monkeypatch.delenv(ratelimit.PROXY_SECRET_ENV, raising=False)
    monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_auto_notes", set())
    ratelimit.reset()
    yield monkeypatch
    ratelimit.reset()


@pytest.fixture()
def off_render(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv(ratelimit.TRUSTED_PROXY_HOPS_ENV, raising=False)
    monkeypatch.delenv(ratelimit.PROXY_SECRET_ENV, raising=False)
    monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_auto_notes", set())
    ratelimit.reset()
    yield monkeypatch
    ratelimit.reset()


def _app(limit: int = 3) -> FastAPI:
    app = FastAPI()

    @app.get("/x", dependencies=[Depends(ratelimit.rate_limit("t", limit, 60))])
    def x():
        return {"ok": True}

    return app


def _codes(client: TestClient, headers_list) -> list[int]:
    return [client.get("/x", headers=h).status_code for h in headers_list]


# ─── the measured bug, on the real route ─────────────────────────────────

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")


@pytest.fixture(scope="module")
def api_app():
    tmp = tempfile.NamedTemporaryFile(
        prefix="mq_direct_ip_", suffix=".db", delete=False
    )
    tmp.close()
    shutil.copyfile(_REPO_DB, tmp.name)
    prior = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = tmp.name
    import motoquant.api as api_mod

    api_mod._db_conn = None
    api_mod._db_facade = None
    try:
        yield api_mod.app
    finally:
        api_mod._db_conn = None
        api_mod._db_facade = None
        if prior is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = prior
        os.unlink(tmp.name)


def test_direct_calls_to_quick_sim_trip_the_limit(api_app, on_render):
    """The live measurement, replayed: 35 direct calls to the 30-per-minute
    quick simulation, each through a different Cloudflare edge address. The
    rate-limit dependency counts each call before the body is validated, so
    an out-of-range body keeps the test fast without running a simulation."""
    client = TestClient(api_app, client=RENDER_PROXY)
    body = {"power_boost_pct": 999}  # rejected after the limiter has counted
    codes = [
        client.post(
            "/api/simulate/quick", json=body, headers=_via_cloudflare(CLIENT, i)
        ).status_code
        for i in range(35)
    ]
    assert 429 not in codes[:30], codes
    assert codes[30:] == [429] * 5, codes
    assert "quick_sim:" + CLIENT in ratelimit._WINDOWS
    assert not any(k.startswith("quick_sim:162.158.") for k in ratelimit._WINDOWS)
    # Another visitor still has a bucket of their own.
    r = client.post(
        "/api/simulate/quick", json=body, headers=_via_cloudflare(OTHER_CLIENT, 99)
    )
    assert r.status_code != 429


# ─── on Render ───────────────────────────────────────────────────────────


def test_rotating_client_sent_headers_stay_in_one_bucket(on_render):
    """Whatever the client sends in X-Forwarded-For, True-Client-IP or
    X-Real-IP sits left of what Cloudflare and Render add, and Cloudflare
    sets CF-Connecting-IP itself."""
    client = TestClient(_app(limit=3), client=RENDER_PROXY)
    headers = []
    for i in range(6):
        spoof = f"198.51.100.{i + 1}"
        h = _via_cloudflare(CLIENT, i, sent_xff=f"{spoof}, 104.16.0.{i + 1}")
        h["true-client-ip"] = spoof
        h["x-real-ip"] = spoof
        headers.append(h)
    assert _codes(client, headers) == [200, 200, 200, 429, 429, 429]
    assert list(ratelimit._WINDOWS) == ["t:" + CLIENT]


@pytest.mark.parametrize(
    "caller", [WORKER, "172.70.1.2"], ids=["worker", "cloudflare-egress"]
)
def test_a_caller_inside_cloudflare_ranges_keys_on_its_own_address(on_render, caller):
    """A Worker (or anything else calling from Cloudflare's own addresses)
    looks like one more Cloudflare hop. The limiter steps one proxy past
    Render's, never further, so it keys on that address and never reaches the
    X-Forwarded-For value the caller sent."""
    client = TestClient(_app(limit=2), client=RENDER_PROXY)
    headers = [
        _via_cloudflare(caller, i, sent_xff=f"198.51.100.{i + 1}") for i in range(3)
    ]
    assert _codes(client, headers) == [200, 200, 429]
    assert list(ratelimit._WINDOWS) == ["t:" + caller]


def test_without_cloudflare_in_front_the_header_is_ignored(on_render, caplog):
    """If Render ever stops fronting services with Cloudflare (or Cloudflare
    connects from a range missing from the list), the hop its proxy appends
    is not a Cloudflare address and CF-Connecting-IP is not trusted: the key
    stays the appended hop, as before this change, and the log says so once,
    without addresses."""
    client = TestClient(_app(limit=2), client=RENDER_PROXY)
    headers = [
        {
            "x-forwarded-for": f"198.51.100.{i + 1}, {CLIENT}",
            "cf-connecting-ip": f"192.0.2.{i + 1}",
        }
        for i in range(3)
    ]
    with caplog.at_level(logging.WARNING, logger="motoquant.ratelimit"):
        assert _codes(client, headers) == [200, 200, 429]
    assert list(ratelimit._WINDOWS) == ["t:" + CLIENT]
    notes = [r.getMessage() for r in caplog.records if "Cloudflare" in r.getMessage()]
    assert len(notes) == 1, notes
    assert CLIENT not in notes[0] and "192.0.2." not in notes[0]


@pytest.mark.parametrize(
    "cf_headers",
    [
        [],
        [("cf-connecting-ip", "not-an-ip")],
        [("cf-connecting-ip", CLIENT), ("cf-connecting-ip", OTHER_CLIENT)],
    ],
    ids=["missing", "not-an-address", "two-lines"],
)
def test_an_unusable_cloudflare_header_keys_on_the_edge(on_render, caplog, cf_headers):
    """No header, a value that is not an address, or two header lines: the key
    stays the Cloudflare edge address (the old behaviour) rather than any
    value a client could have chosen, and the log says so once, without
    addresses."""
    client = TestClient(_app(), client=RENDER_PROXY)
    with caplog.at_level(logging.WARNING, logger="motoquant.ratelimit"):
        for _ in range(2):
            client.get(
                "/x",
                headers=[("x-forwarded-for", f"{CLIENT}, {_edge(7)}"), *cf_headers],
            )
    assert list(ratelimit._WINDOWS) == ["t:" + _edge(7)]
    notes = [r.getMessage() for r in caplog.records if "Cloudflare" in r.getMessage()]
    assert len(notes) == 1, notes
    assert CLIENT not in notes[0] and _edge(7) not in notes[0]


def test_the_site_proxy_still_wins(on_render):
    """Visitors who come through motoquant.in key on the IP the site vouches
    for, not on the Vercel egress address Cloudflare reports."""
    on_render.setenv(ratelimit.PROXY_SECRET_ENV, SECRET)
    client = TestClient(_app(), client=RENDER_PROXY)
    headers = _via_cloudflare("3.0.0.1", 1, sent_xff=CLIENT)  # Vercel egress
    headers[ratelimit.PROXY_AUTH_HEADER] = SECRET
    headers[ratelimit.PROXY_CLIENT_IP_HEADER] = CLIENT
    client.get("/x", headers=headers)
    assert list(ratelimit._WINDOWS) == ["t:" + CLIENT]


def test_the_choice_is_logged_once_without_addresses(on_render, caplog):
    client = TestClient(_app(limit=100), client=RENDER_PROXY)
    with caplog.at_level(logging.INFO, logger="motoquant.ratelimit"):
        for i in range(3):
            client.get("/x", headers=_via_cloudflare(CLIENT, i))
    notes = [r.getMessage() for r in caplog.records if "Cloudflare" in r.getMessage()]
    assert len(notes) == 1, notes
    assert CLIENT not in notes[0] and "162.158." not in notes[0]


# ─── off Render: the header is never trusted ─────────────────────────────


@pytest.mark.parametrize(
    "peer, xff",
    [
        (("104.16.0.9", 40000), None),  # Cloudflare address hitting uvicorn
        (("172.17.0.1", 40000), "198.51.100.1, 104.16.0.9"),  # behind nginx
        (("127.0.0.1", 40000), "104.16.0.9"),  # proxy on the same host
    ],
    ids=["direct", "docker-proxy", "loopback-proxy"],
)
def test_self_hosted_ignores_cf_connecting_ip(off_render, peer, xff):
    """A self-hosted API can be called by a Cloudflare Worker directly, and
    such a Worker may set CF-Connecting-IP itself. Off Render the header
    must never choose the bucket."""
    client = TestClient(_app(limit=2), client=peer)
    headers = []
    for i in range(3):
        h = {"cf-connecting-ip": f"192.0.2.{i + 1}"}
        if xff:
            h["x-forwarded-for"] = xff
        headers.append(h)
    assert _codes(client, headers) == [200, 200, 429]
    assert list(ratelimit._WINDOWS) == ["t:104.16.0.9"]


# ─── the range check ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "addr, expected",
    [
        ("162.158.4.1", True),
        ("104.23.255.254", True),
        ("::ffff:172.64.0.1", True),  # IPv4-mapped, as a dual-stack hop reads
        ("2606:4700:10::6816:1", True),
        (WORKER, True),
        (CLIENT, False),
        ("104.32.0.1", False),  # just past 104.24.0.0/14
        ("10.201.3.4", False),
        ("2001:db8::1", False),
        ("not-an-ip", False),
        ("", False),
        (None, False),
    ],
)
def test_cloudflare_ranges(addr, expected):
    assert ratelimit._is_cloudflare_edge(addr) is expected
