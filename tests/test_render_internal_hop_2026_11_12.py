"""Per-IP limits on Render must see past Render's own internal proxy.

GET /api/whoami on production (2026-11-12) showed the chain uvicorn receives
for a direct call, on both api.motoquant.in and the onrender.com name:

    X-Forwarded-For: <client>, <Cloudflare edge>, <Render 10.x>
    socket peer:     <Render 10.x>
    CF-Connecting-IP: <client>

#164 assumed "<client>, <Cloudflare edge>" with one trusted hop, so the hop
it checked was Render's private 10.x address, the Cloudflare branch never
engaged, and every direct caller keyed on one of a few rotating Render
addresses: 35 direct calls to api.motoquant.in all returned 200.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import Depends, FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import ratelimit  # noqa: E402

CLIENT = "49.36.0.7"


def _edge(i: int) -> str:
    return f"162.158.{i % 256}.{i // 256 + 1}"  # inside 162.158.0.0/15


def _render_internal(i: int) -> str:
    return f"10.29.{i % 200}.{(i * 7) % 250 + 1}"


def _chain(client: str, i: int, sent: str | None = None) -> tuple[dict, tuple]:
    internal = _render_internal(i)
    xff = f"{client}, {_edge(i)}, {internal}"
    if sent:
        xff = f"{sent}, {xff}"
    return {"x-forwarded-for": xff, "cf-connecting-ip": client}, (internal, 40000)


@pytest.fixture(params=["1", None], ids=["hops=1", "hops=auto"])
def on_render(request, monkeypatch):
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


def _who_app():
    app = FastAPI()

    @app.get("/who")
    def who(request: Request):
        return ratelimit.describe_client(request)

    return app


def test_the_production_chain_keys_on_the_client(on_render):
    headers, peer = _chain(CLIENT, 3)
    out = TestClient(_who_app(), client=peer).get("/who", headers=headers).json()
    assert out["client_ip"] == CLIENT
    assert out["rule"] == "cloudflare_connecting_ip"


@pytest.mark.parametrize(
    "sent", ["8.8.4.4", "10.0.0.9", "8.8.4.4, 10.0.0.9", "garbage"]
)
def test_client_sent_hops_cannot_change_the_key(on_render, sent):
    headers, peer = _chain(CLIENT, 5, sent=sent)
    out = TestClient(_who_app(), client=peer).get("/who", headers=headers).json()
    assert out["client_ip"] == CLIENT


def test_a_non_cloudflare_hop_never_trusts_cf_connecting_ip(on_render):
    # If the first public hop is not Cloudflare, a CF-Connecting-IP value is
    # not believed (the request keys on the hop as before).
    headers = {"x-forwarded-for": "8.8.8.8, 10.29.1.2", "cf-connecting-ip": "1.2.3.4"}
    out = (
        TestClient(_who_app(), client=("10.29.1.2", 40000))
        .get("/who", headers=headers)
        .json()
    )
    assert out["client_ip"] != "1.2.3.4"


def test_thirty_five_direct_calls_hit_the_limit(on_render):
    """The 2026-11-12 measurement replayed: a different edge and Render
    address on every call, 30 allowed per minute."""
    app = FastAPI()

    @app.post("/x", dependencies=[Depends(ratelimit.rate_limit("quick_sim", 30, 60.0))])
    def x():
        return {"ok": True}

    codes = []
    for i in range(35):
        headers, peer = _chain(CLIENT, i)
        codes.append(
            TestClient(app, client=peer).post("/x", headers=headers).status_code
        )
    assert codes[:30] == [200] * 30
    assert codes[30:] == [429] * 5
    # Another client is unaffected.
    headers, peer = _chain("49.36.0.8", 99)
    assert TestClient(app, client=peer).post("/x", headers=headers).status_code == 200
