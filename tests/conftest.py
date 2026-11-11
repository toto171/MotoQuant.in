"""Shared pytest fixtures / session hygiene.

The rate limiter (motoquant/ratelimit.py) keeps process-global window
state, which is correct for a single-worker production server. In the test
session, FastAPI's TestClient always presents the same client host
("testclient"), so cost-fuse hits on /api/chat, /api/optimize/build, and
/api/autotune/ecu accumulate across every test module and eventually 429 a
legitimate call. Reset the limiter before each test so the fuse is only
ever exercised deliberately (tests that assert 429 do their own bursts).
"""

import os

import pytest

# Without an OpenWeatherMap key the API falls back to Open-Meteo over the
# network. Tests must not depend on the network: turn the fallback off for the
# session (tests of the fallback itself stub the HTTP calls and switch it on).
os.environ.setdefault("MOTOQUANT_OPEN_METEO", "0")


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    try:
        from motoquant import ratelimit

        ratelimit.reset()
    except Exception:
        pass
    # The weather-lookup cache is process-global too; a test that stubs the
    # upstream must not be answered by another test's cached lookup.
    try:
        import sys

        api = sys.modules.get("motoquant.api")
        if api is not None:
            with api._owm_cache_lock:
                api._owm_cache.clear()
    except Exception:
        pass
    yield
