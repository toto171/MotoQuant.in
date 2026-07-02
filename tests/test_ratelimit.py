"""Tests for motoquant/ratelimit.py — the cost fuse on public endpoints.

Exercises the real FastAPI dependency path via a minimal TestClient app,
plus the window arithmetic directly.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import ratelimit  # noqa: E402


@pytest.fixture(autouse=True)
def _clean():
    ratelimit.reset()
    yield
    ratelimit.reset()


class TestCheck:
    def test_allows_up_to_limit(self):
        for _ in range(5):
            allowed, _ = ratelimit.check("k", limit=5, window_s=60)
            assert allowed

    def test_blocks_over_limit_with_retry_after(self):
        for _ in range(5):
            ratelimit.check("k", limit=5, window_s=60)
        allowed, retry = ratelimit.check("k", limit=5, window_s=60)
        assert not allowed
        assert 1 <= retry <= 61

    def test_keys_are_isolated(self):
        for _ in range(5):
            ratelimit.check("a", limit=5, window_s=60)
        allowed, _ = ratelimit.check("b", limit=5, window_s=60)
        assert allowed

    def test_window_expiry_resets(self, monkeypatch):
        t = [1000.0]
        monkeypatch.setattr(ratelimit.time, "monotonic", lambda: t[0])
        for _ in range(5):
            ratelimit.check("k", limit=5, window_s=60)
        t[0] += 61
        allowed, _ = ratelimit.check("k", limit=5, window_s=60)
        assert allowed

    def test_table_bound_fail_open(self):
        # Overflow the key table; the limiter must fail open, not raise.
        for i in range(ratelimit._MAX_KEYS + 10):
            ratelimit.check(f"k{i}", limit=5, window_s=60)
        allowed, _ = ratelimit.check("fresh", limit=5, window_s=60)
        assert allowed


class TestDependency:
    def _app(self, limit=3):
        app = FastAPI()

        @app.get(
            "/limited",
            dependencies=[Depends(ratelimit.rate_limit("test", limit, 60))],
        )
        def limited():
            return {"ok": True}

        return app

    def test_429_after_limit_via_http(self):
        client = TestClient(self._app(limit=3))
        for _ in range(3):
            assert client.get("/limited").status_code == 200
        resp = client.get("/limited")
        assert resp.status_code == 429
        assert resp.headers.get("retry-after")
        assert resp.json()["detail"]["error"] == "rate_limited"

    def test_x_forwarded_for_distinguishes_clients(self):
        client = TestClient(self._app(limit=2))
        for _ in range(2):
            assert (
                client.get(
                    "/limited", headers={"x-forwarded-for": "198.51.100.1"}
                ).status_code
                == 200
            )
        # third from same forwarded IP -> blocked
        assert (
            client.get(
                "/limited", headers={"x-forwarded-for": "198.51.100.1"}
            ).status_code
            == 429
        )
        # different forwarded IP -> allowed
        assert (
            client.get(
                "/limited", headers={"x-forwarded-for": "198.51.100.2"}
            ).status_code
            == 200
        )

    def test_kill_switch(self, monkeypatch):
        monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", False)
        client = TestClient(self._app(limit=1))
        for _ in range(5):
            assert client.get("/limited").status_code == 200
