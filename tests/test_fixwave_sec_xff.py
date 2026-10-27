"""Regression tests: rate limits must not be bypassable by rotating
``X-Forwarded-For`` when no appending proxy sits in front of the API.

Audit finding (2026-10-23): ``client_ip`` always trusted the rightmost XFF
hop. On an API reached directly (the open-source
``uvicorn motoquant.api:app`` path) every request could carry a fresh
``X-Forwarded-For: 10.0.0.N`` and land in a fresh bucket, so every cost fuse
(chat, optimizer, autotune, simulate, uploads) was fully bypassable.

Now XFF is honoured only for ``MOTOQUANT_TRUSTED_PROXY_HOPS`` trusted proxies;
unset means AUTO (1 hop on Render, where the edge appends the peer it saw, or
when the socket peer is loopback or a private RFC 1918 / ULA address, i.e.
where a self-hosted reverse proxy connects from; otherwise the header is
ignored).

Review follow-up (2026-10-24): the first version of AUTO trusted only a
loopback peer, so the documented self-hosting setup (the Docker image behind
Caddy or nginx, docs/SELF_HOSTING.md section 4b) reached the container from
the Docker bridge gateway 172.17.0.1 and keyed EVERY visitor on that one
address, putting all users in one bucket.

``TestClient(..., client=(ip, port))`` sets the ASGI socket peer, i.e. what
uvicorn reports as ``request.client.host`` for a direct connection.
"""

from __future__ import annotations

import logging
import types

import pytest

pytest.importorskip("fastapi")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import ratelimit  # noqa: E402

_ENV = "MOTOQUANT_TRUSTED_PROXY_HOPS"  # literal: the operator-facing name
REMOTE_PEER = ("203.0.113.50", 40000)  # a client hitting uvicorn directly
RENDER_EDGE = ("10.201.3.4", 40000)  # Render's proxy, on a private network


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv(_ENV, raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_auto_notes", set())
    ratelimit.reset()
    yield
    ratelimit.reset()


def _app(limit=3):
    app = FastAPI()

    @app.get("/x", dependencies=[Depends(ratelimit.rate_limit("t", limit, 60))])
    def x():
        return {"ok": True}

    return app


def _codes(client, headers_list):
    return [client.get("/x", headers=h).status_code for h in headers_list]


class TestDirectDeployment:
    def test_rotating_spoofed_xff_cannot_mint_buckets(self):
        client = TestClient(_app(limit=3), client=REMOTE_PEER)
        codes = _codes(client, [{"x-forwarded-for": f"10.0.0.{i}"} for i in range(6)])
        assert codes == [200, 200, 200, 429, 429, 429], codes

    def test_rotating_rightmost_hop_cannot_mint_buckets(self):
        client = TestClient(_app(limit=3), client=REMOTE_PEER)
        codes = _codes(
            client, [{"x-forwarded-for": f"1.2.3.4, 9.9.9.{i}"} for i in range(5)]
        )
        assert codes == [200, 200, 200, 429, 429], codes

    def test_key_is_the_socket_peer(self):
        client = TestClient(_app(), client=REMOTE_PEER)
        client.get("/x", headers={"x-forwarded-for": "10.9.9.9"})
        assert "t:203.0.113.50" in ratelimit._WINDOWS
        assert not any("10.9.9.9" in k for k in ratelimit._WINDOWS)

    def test_explicit_zero_ignores_xff_even_from_loopback(self, monkeypatch):
        monkeypatch.setenv(_ENV, "0")
        client = TestClient(_app(limit=2), client=("127.0.0.1", 5000))
        codes = _codes(client, [{"x-forwarded-for": f"10.0.0.{i}"} for i in range(3)])
        assert codes == [200, 200, 429], codes


class TestTrustedProxies:
    def test_render_auto_trusts_one_appended_hop(self, monkeypatch):
        """Production on Render keeps working with no configuration: the edge
        appends the client it saw, so the rightmost hop is the real client and
        a spoofed leftmost hop is ignored."""
        monkeypatch.setenv("RENDER", "true")
        client = TestClient(_app(limit=2), client=RENDER_EDGE)
        for spoof in ("192.0.2.1", "192.0.2.2"):
            r = client.get("/x", headers={"x-forwarded-for": f"{spoof}, 49.36.0.7"})
            assert r.status_code == 200
        r = client.get("/x", headers={"x-forwarded-for": "192.0.2.3, 49.36.0.7"})
        assert r.status_code == 429
        # A different real client has its own bucket.
        r = client.get("/x", headers={"x-forwarded-for": "192.0.2.3, 49.36.0.8"})
        assert r.status_code == 200

    def test_without_render_a_private_peer_is_trusted_by_default(self):
        """Off Render, a proxy on a private network (here the address Render
        happens to use, 10.x) still gets its one appended hop trusted."""
        client = TestClient(_app(limit=2), client=RENDER_EDGE)
        codes = _codes(client, [{"x-forwarded-for": f"49.36.0.{i}"} for i in range(3)])
        assert codes == [200, 200, 200], codes

    def test_explicit_one_hop(self, monkeypatch):
        monkeypatch.setenv(_ENV, "1")
        client = TestClient(_app(), client=RENDER_EDGE)
        client.get("/x", headers={"x-forwarded-for": "6.6.6.6, 49.36.0.7"})
        assert "t:49.36.0.7" in ratelimit._WINDOWS

    def test_two_hops_take_second_from_right(self, monkeypatch):
        monkeypatch.setenv(_ENV, "2")
        client = TestClient(_app(limit=1), client=RENDER_EDGE)
        # spoof, real client (added by proxy 1), proxy 1 (added by proxy 2)
        assert (
            client.get(
                "/x", headers={"x-forwarded-for": "6.6.6.6, 49.36.0.7, 10.0.0.2"}
            ).status_code
            == 200
        )
        assert "t:49.36.0.7" in ratelimit._WINDOWS
        assert (
            client.get(
                "/x", headers={"x-forwarded-for": "7.7.7.7, 49.36.0.7, 10.0.0.2"}
            ).status_code
            == 429
        )

    def test_same_host_proxy_is_trusted_under_auto(self):
        client = TestClient(_app(), client=("127.0.0.1", 5000))
        client.get("/x", headers={"x-forwarded-for": "6.6.6.6, 49.36.0.7"})
        assert "t:49.36.0.7" in ratelimit._WINDOWS

    def test_repeated_header_lines_are_joined_in_order(self, monkeypatch):
        """A client-sent first XFF line must not shadow the line a proxy
        added: with 1 trusted hop the LAST entry across all lines wins."""
        monkeypatch.setenv(_ENV, "1")
        req = types.SimpleNamespace(
            client=types.SimpleNamespace(host="10.201.3.4"),
            headers=_Headers(
                [("x-forwarded-for", "6.6.6.6"), ("x-forwarded-for", "49.36.0.7")]
            ),
        )
        assert ratelimit.client_ip(req) == "49.36.0.7"

    def test_env_name_is_the_documented_one(self):
        assert ratelimit.TRUSTED_PROXY_HOPS_ENV == _ENV

    @pytest.mark.parametrize("bad", ["abc", "-1", "1.5"])
    def test_invalid_setting_fails_closed(self, monkeypatch, bad):
        monkeypatch.setenv(_ENV, bad)
        assert ratelimit.trusted_proxy_hops() == 0
        client = TestClient(_app(limit=1), client=("127.0.0.1", 5000))
        codes = _codes(client, [{"x-forwarded-for": f"10.0.0.{i}"} for i in range(2)])
        assert codes == [200, 429], codes


DOCKER_BRIDGE = ("172.17.0.1", 40000)  # host-side Caddy/nginx -> -p 8000:8000


class TestSelfHostedBehindProxy:
    """The documented self-hosting topology (docs/SELF_HOSTING.md section 4b):
    the Docker image behind Caddy or nginx. The container sees the proxy's
    private address as its socket peer, never the client's."""

    def test_docker_bridge_gateway_peer_keys_on_the_real_client(self):
        """Before the fix, every visitor keyed on 172.17.0.1, so the third
        DIFFERENT client was refused by a limit of 2."""
        client = TestClient(_app(limit=2), client=DOCKER_BRIDGE)
        codes = _codes(
            client,
            [{"x-forwarded-for": ip} for ip in ("49.36.0.7", "49.36.0.8", "49.36.0.9")],
        )
        assert codes == [200, 200, 200], codes
        assert "t:49.36.0.7" in ratelimit._WINDOWS
        assert not any("172.17.0.1" in k for k in ratelimit._WINDOWS)

    def test_one_client_behind_the_proxy_is_still_limited(self):
        client = TestClient(_app(limit=2), client=DOCKER_BRIDGE)
        codes = _codes(client, [{"x-forwarded-for": "49.36.0.7"}] * 3)
        assert codes == [200, 200, 429], codes

    def test_spoofed_leftmost_hop_behind_the_proxy_is_ignored(self):
        """nginx/Caddy APPEND the client they saw; whatever the client sent
        on the left of it cannot pick the bucket."""
        client = TestClient(_app(limit=2), client=DOCKER_BRIDGE)
        codes = _codes(
            client,
            [{"x-forwarded-for": f"10.0.0.{i}, 49.36.0.7"} for i in range(3)],
        )
        assert codes == [200, 200, 429], codes

    @pytest.mark.parametrize(
        "peer",
        [
            "172.18.0.5",  # a proxy container on a user-defined network
            "192.168.1.20",  # a proxy elsewhere on the LAN
            "fd12:3456::1",  # IPv6 unique-local
            "::ffff:172.17.0.1",  # IPv4 peer as a dual-stack listener reports it
        ],
    )
    def test_other_private_proxy_addresses(self, peer):
        client = TestClient(_app(), client=(peer, 40000))
        client.get("/x", headers={"x-forwarded-for": "49.36.0.7"})
        assert "t:49.36.0.7" in ratelimit._WINDOWS

    @pytest.mark.parametrize(
        "peer",
        [
            "203.0.113.50",  # documentation range (is_private is True for it)
            "198.51.100.7",  # documentation range
            "169.254.10.1",  # link-local
            "100.64.0.1",  # shared / CGNAT
            "49.36.0.7",  # ordinary public address
        ],
    )
    def test_non_proxy_ranges_are_not_trusted(self, peer):
        client = TestClient(_app(limit=2), client=(peer, 40000))
        codes = _codes(client, [{"x-forwarded-for": f"10.0.0.{i}"} for i in range(3)])
        assert codes == [200, 200, 429], codes

    def test_explicit_zero_turns_private_trust_off(self, monkeypatch):
        """Clients on the same LAN, or an L4 NAT that rewrites every source to
        a private address, are not proxies: the operator opts out."""
        monkeypatch.setenv(_ENV, "0")
        client = TestClient(_app(limit=2), client=DOCKER_BRIDGE)
        codes = _codes(client, [{"x-forwarded-for": f"49.36.0.{i}"} for i in range(3)])
        assert codes == [200, 200, 429], codes

    def test_auto_decisions_are_logged_once(self, caplog):
        caplog.set_level(logging.INFO, logger=ratelimit.logger.name)
        private = TestClient(_app(limit=100), client=DOCKER_BRIDGE)
        public = TestClient(_app(limit=100), client=REMOTE_PEER)
        for _ in range(3):
            private.get("/x", headers={"x-forwarded-for": "49.36.0.7"})
            public.get("/x", headers={"x-forwarded-for": "10.0.0.1"})
        msgs = [r.getMessage() for r in caplog.records]
        trusted = [m for m in msgs if "trusting one X-Forwarded-For hop" in m]
        ignored = [m for m in msgs if "ignoring X-Forwarded-For" in m]
        assert len(trusted) == 1 and "172.17.0.1" in trusted[0], msgs
        assert len(ignored) == 1 and "203.0.113.50" in ignored[0], msgs
        assert all(_ENV in m for m in trusted + ignored)
        # The header's contents never reach the log.
        assert not any("49.36.0.7" in m or "10.0.0.1" in m for m in msgs)

    @pytest.mark.parametrize("peer", [REMOTE_PEER, DOCKER_BRIDGE])
    def test_no_xff_logs_nothing(self, caplog, peer):
        caplog.set_level(logging.INFO, logger=ratelimit.logger.name)
        TestClient(_app(), client=peer).get("/x")
        assert not caplog.records


class _Headers:
    """Minimal multi-value header bag (Starlette's Headers API subset)."""

    def __init__(self, items):
        self._items = items

    def getlist(self, key):
        return [v for k, v in self._items if k == key]

    def get(self, key, default=None):
        vals = self.getlist(key)
        return vals[0] if vals else default


class TestRealChatRoute:
    """The production /api/chat daily cap (the LLM-bill fuse) on a direct
    deployment: rotating XFF must not reset it."""

    def test_daily_chat_cap_survives_xff_rotation(self, monkeypatch):
        api_mod = pytest.importorskip("motoquant.api")
        stub = types.SimpleNamespace(is_configured=False, provider="stub")
        api_mod.app.dependency_overrides[api_mod.get_llm_client] = lambda: stub
        monkeypatch.setattr(api_mod, "CHAT_DAILY_LIMIT", 1)
        try:
            client = TestClient(
                api_mod.app, raise_server_exceptions=False, client=REMOTE_PEER
            )
            r1 = client.post(
                "/api/chat",
                json={"query": "how fast is a K5"},
                headers={"x-forwarded-for": "10.0.0.1"},
            )
            r2 = client.post(
                "/api/chat",
                json={"query": "how fast is a K5"},
                headers={"x-forwarded-for": "10.0.0.2"},
            )
        finally:
            api_mod.app.dependency_overrides.pop(api_mod.get_llm_client, None)
        assert r1.status_code == 200, r1.text[:300]
        assert r2.status_code == 429, r2.text[:300]
        assert r2.json()["detail"]["error"] == "rate_limited"

    def test_daily_chat_cap_is_per_client_behind_a_docker_proxy(self, monkeypatch):
        """Behind the documented Caddy/nginx proxy, one visitor using up the
        daily chat cap must not lock out the next visitor (before the fix
        both keyed on the bridge gateway 172.17.0.1)."""
        api_mod = pytest.importorskip("motoquant.api")
        stub = types.SimpleNamespace(is_configured=False, provider="stub")
        api_mod.app.dependency_overrides[api_mod.get_llm_client] = lambda: stub
        monkeypatch.setattr(api_mod, "CHAT_DAILY_LIMIT", 1)
        body = {"query": "how fast is a K5"}
        try:
            client = TestClient(
                api_mod.app, raise_server_exceptions=False, client=DOCKER_BRIDGE
            )
            a1 = client.post(
                "/api/chat", json=body, headers={"x-forwarded-for": "49.36.0.7"}
            )
            a2 = client.post(
                "/api/chat", json=body, headers={"x-forwarded-for": "49.36.0.7"}
            )
            b1 = client.post(
                "/api/chat", json=body, headers={"x-forwarded-for": "49.36.0.8"}
            )
        finally:
            api_mod.app.dependency_overrides.pop(api_mod.get_llm_client, None)
        assert a1.status_code == 200, a1.text[:300]
        assert a2.status_code == 429, a2.text[:300]
        assert b1.status_code == 200, b1.text[:300]
