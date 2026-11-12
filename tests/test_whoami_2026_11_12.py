"""GET /api/whoami: what the API counts the caller as, without leaking the
other addresses on the path. Used to check per-IP limits on each public
hostname (api.motoquant.in, the onrender.com name, the site proxy)."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import ratelimit  # noqa: E402

RENDER_PROXY = ("10.201.3.4", 40000)
CLIENT = "49.36.0.7"
EDGE = "162.158.1.2"  # inside Cloudflare's 162.158.0.0/15


def _app():
    app = FastAPI()

    @app.get("/who")
    def who(request: Request):
        return ratelimit.describe_client(request)

    return app


@pytest.fixture()
def on_render(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv(ratelimit.TRUSTED_PROXY_HOPS_ENV, "1")
    monkeypatch.delenv(ratelimit.PROXY_SECRET_ENV, raising=False)
    monkeypatch.setattr(ratelimit, "_auto_notes", set())
    yield monkeypatch


def test_describes_the_cloudflare_path_without_other_addresses(on_render):
    client = TestClient(_app(), client=RENDER_PROXY)
    headers = {
        "x-forwarded-for": f"8.8.4.4, {CLIENT}, {EDGE}",
        "cf-connecting-ip": CLIENT,
        "cdn-loop": "cloudflare; loops=1",
    }
    out = client.get("/who", headers=headers).json()
    assert out["client_ip"] == CLIENT
    assert out["rule"] == "cloudflare_connecting_ip"
    assert out["forwarded_for"] == ["other_public", "you", "cloudflare"]
    assert out["trusted_hop"] == "cloudflare"
    assert out["cf_connecting_ip"] == "you"
    assert out["peer"] == "private"
    assert out["cdn_loop"] == "cloudflare; loops=1"
    text = json.dumps(out)
    for addr in ("8.8.4.4", EDGE, "10.201.3.4"):
        assert addr not in text


def test_rule_matches_client_ip_on_every_path(on_render):
    app = FastAPI()

    @app.get("/both")
    def both(request: Request):
        return {
            "ip": ratelimit.client_ip(request),
            "who": ratelimit.describe_client(request)["client_ip"],
        }

    client = TestClient(app, client=RENDER_PROXY)
    for headers in (
        {"x-forwarded-for": f"{CLIENT}, {EDGE}", "cf-connecting-ip": CLIENT},
        {"x-forwarded-for": f"{CLIENT}, 8.8.8.8"},
        {},
    ):
        r = client.get("/both", headers=headers).json()
        assert r["ip"] == r["who"]


def test_whoami_route_is_served_and_rate_limited(monkeypatch):
    import motoquant.api as api

    monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", True)
    ratelimit.reset()
    client = TestClient(api.app)
    r = client.get("/api/whoami")
    assert r.status_code == 200 and "rule" in r.json()
    codes = [client.get("/api/whoami").status_code for _ in range(25)]
    assert 429 in codes
    ratelimit.reset()
