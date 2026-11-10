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


class TestPerKeyWindows:
    """Buckets with DIFFERENT windows share one table (60 s per-minute fuses
    beside the 86400 s daily chat cap). Eviction must judge each key by its
    OWN window — the old sweep used the triggering caller's window, so a
    distinct-key flood of 60 s calls wiped daily counters after a minute."""

    def _clock(self, monkeypatch, start=1000.0):
        t = [start]
        monkeypatch.setattr(ratelimit.time, "monotonic", lambda: t[0])
        return t

    def test_flood_cannot_reset_a_daily_counter(self, monkeypatch):
        t = self._clock(monkeypatch)
        key = "chat_day:203.0.113.9"
        for _ in range(3):
            assert ratelimit.check(key, 3, 86400)[0]
        assert not ratelimit.check(key, 3, 86400)[0]
        t[0] += 120  # past every 60 s window, well inside the day
        for i in range(ratelimit._MAX_KEYS + 10):
            ratelimit.check(f"flood:{i}", 5, 60)
        allowed, retry = ratelimit.check(key, 3, 86400)
        assert not allowed, "a 60 s-window flood evicted the daily counter"
        assert retry > 3600

    def test_stale_short_windows_are_swept_by_a_long_window_call(self, monkeypatch):
        t = self._clock(monkeypatch)
        for i in range(ratelimit._MAX_KEYS + 1):
            ratelimit.check(f"minute:{i}", 5, 60)
        t[0] += 120  # every minute bucket is now expired by ITS OWN window
        ratelimit.check("chat_day:198.51.100.7", 200, 86400)
        # The old sweep used the caller's 86400 s window, kept every stale
        # minute bucket, and could only shed two keys per call.
        assert len(ratelimit._WINDOWS) == 1

    def test_overflow_evicts_closest_to_expiry_first(self, monkeypatch):
        t = self._clock(monkeypatch)
        ratelimit.check("long:a", 10, 86400)  # oldest start, latest expiry
        t[0] += 30
        for i in range(ratelimit._MAX_KEYS + 5):
            ratelimit.check(f"short:{i}", 10, 60)
        assert "long:a" in ratelimit._WINDOWS

    def test_window_is_stored_per_key(self):
        ratelimit.check("a", 5, 60)
        ratelimit.check("b", 5, 86400)
        assert ratelimit._WINDOWS["a"][2] == 60
        assert ratelimit._WINDOWS["b"][2] == 86400


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

    def test_rightmost_forwarded_hop_is_the_key(self):
        """Render APPENDS the peer it saw, so with one trusted proxy the
        RIGHTMOST X-Forwarded-For hop is the real client; the leftmost is
        whatever the caller sent. Rotating a spoofed leftmost hop must NOT
        mint a fresh bucket — that would bypass every fuse in the API (and
        since the open-source pivot the fuses are the only protection)."""
        client = TestClient(self._app(limit=2))
        for spoof in ("192.0.2.1", "192.0.2.2"):
            r = client.get(
                "/limited", headers={"x-forwarded-for": f"{spoof}, 203.0.113.5"}
            )
            assert r.status_code == 200
        r = client.get(
            "/limited", headers={"x-forwarded-for": "192.0.2.3, 203.0.113.5"}
        )
        assert r.status_code == 429
        # A different REAL client (rightmost hop) still has its own bucket.
        r = client.get(
            "/limited", headers={"x-forwarded-for": "192.0.2.3, 203.0.113.6"}
        )
        assert r.status_code == 200

    def test_daily_window_message_reads_per_day(self):
        app = FastAPI()

        @app.get(
            "/daily",
            dependencies=[Depends(ratelimit.rate_limit("chat_day", 1, 86400.0))],
        )
        def daily():
            return {"ok": True}

        client = TestClient(app)
        assert client.get("/daily").status_code == 200
        resp = client.get("/daily")
        assert resp.status_code == 429
        msg = resp.json()["detail"]["message"]
        assert "per day" in msg and "Try again later" in msg

    def test_kill_switch(self, monkeypatch):
        monkeypatch.setattr(ratelimit, "RATE_LIMIT_ENABLED", False)
        client = TestClient(self._app(limit=1))
        for _ in range(5):
            assert client.get("/limited").status_code == 200
