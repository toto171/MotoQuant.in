"""Launch hardening found by the pre-marketing security review (2026-11-11).

* Visitors who reach the API through the website arrive from Vercel's
  addresses, so they shared rate-limit buckets. The site's /api middleware now
  vouches for the real visitor IP with a shared secret
  (MOTOQUANT_PROXY_SECRET); without the secret the header is ignored.
* One client may hold at most MAX_RUNNING_PER_OWNER background jobs, but only
  when its identity can be trusted.
* CORS allows the public site and local development, not every origin.
* Request bodies over MAX_REQUEST_BYTES get 413 before anything parses them.
* API responses carry nosniff and HSTS.
* 500 responses no longer echo exception text.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from motoquant import jobs, observability, ratelimit  # noqa: E402

# A dummy shared secret, built at runtime and only ever compared in memory.
SECRET = "test-proxy-secret-" + "x" * 24


# ─── client_ip and the site proxy ────────────────────────────────────────


def _ip_app():
    app = FastAPI()

    @app.get("/ip")
    def ip(request: ratelimit.Request):
        return {"ip": ratelimit.client_ip(request)}

    return app


@pytest.fixture()
def no_proxy_env(monkeypatch):
    monkeypatch.delenv(ratelimit.PROXY_SECRET_ENV, raising=False)
    monkeypatch.delenv(ratelimit.TRUSTED_PROXY_HOPS_ENV, raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(ratelimit, "_auto_notes", set())
    yield monkeypatch


def _get_ip(headers):
    client = TestClient(_ip_app(), client=("203.0.113.50", 40000))
    return client.get("/ip", headers=headers).json()["ip"]


def test_proxied_ip_used_only_with_the_right_secret(no_proxy_env):
    no_proxy_env.setenv(ratelimit.PROXY_SECRET_ENV, SECRET)
    vouched = {
        ratelimit.PROXY_AUTH_HEADER: SECRET,
        ratelimit.PROXY_CLIENT_IP_HEADER: "49.36.0.7",
    }
    assert _get_ip(vouched) == "49.36.0.7"
    # Wrong secret, missing secret, or a value that is not an IP: ignored.
    wrong = dict(vouched, **{ratelimit.PROXY_AUTH_HEADER: SECRET + "y"})
    assert _get_ip(wrong) == "203.0.113.50"
    assert _get_ip({ratelimit.PROXY_CLIENT_IP_HEADER: "49.36.0.7"}) == "203.0.113.50"
    bad_ip = dict(vouched, **{ratelimit.PROXY_CLIENT_IP_HEADER: "not-an-ip"})
    assert _get_ip(bad_ip) == "203.0.113.50"


def test_proxy_headers_ignored_when_no_secret_is_configured(no_proxy_env):
    sent = {
        ratelimit.PROXY_AUTH_HEADER: SECRET,
        ratelimit.PROXY_CLIENT_IP_HEADER: "49.36.0.7",
    }
    assert _get_ip(sent) == "203.0.113.50"
    # A too-short secret on the server counts as not configured.
    no_proxy_env.setenv(ratelimit.PROXY_SECRET_ENV, "short")
    assert _get_ip(dict(sent, **{ratelimit.PROXY_AUTH_HEADER: "short"})) == (
        "203.0.113.50"
    )
    assert ratelimit.proxy_secret_configured() is False


def test_sentry_scrubber_drops_the_proxy_secret():
    event = {
        "request": {
            "headers": {
                "X-Motoquant-Proxy-Auth": SECRET,
                "X-Motoquant-Client-Ip": "49.36.0.7",
                "User-Agent": "ua",
            }
        }
    }
    headers = observability.scrub_event(event)["request"]["headers"]
    assert "X-Motoquant-Proxy-Auth" not in headers
    assert headers["User-Agent"] == "ua"


# ─── per-client job cap ──────────────────────────────────────────────────


@pytest.fixture()
def clean_jobs():
    with jobs._LOCK:
        jobs._JOBS.clear()
    yield
    with jobs._LOCK:
        for job in jobs._JOBS.values():
            job.cancel_requested = True
        jobs._JOBS.clear()


def _blocking_runner(release: threading.Event):
    def run(progress):
        release.wait(5)
        return {"ok": True}

    return run


def test_one_owner_cannot_take_every_job_slot(clean_jobs):
    release = threading.Event()
    try:
        for _ in range(jobs.MAX_RUNNING_PER_OWNER):
            jobs.create_job("simulate", _blocking_runner(release), owner="1.2.3.4")
        with pytest.raises(jobs.JobCapacityError):
            jobs.create_job("simulate", _blocking_runner(release), owner="1.2.3.4")
        # Another client still gets a slot, and an unknown owner is not capped.
        jobs.create_job("simulate", _blocking_runner(release), owner="5.6.7.8")
        jobs.create_job("simulate", _blocking_runner(release), owner=None)
    finally:
        release.set()


# ─── API middleware and errors ───────────────────────────────────────────

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")


@pytest.fixture(scope="module")
def api_client():
    tmp = tempfile.NamedTemporaryFile(
        prefix="mq_hardening_", suffix=".db", delete=False
    )
    tmp.close()
    shutil.copyfile(_REPO_DB, tmp.name)
    prior = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = tmp.name
    import motoquant.api as api_mod

    api_mod._db_conn = None
    api_mod._db_facade = None
    try:
        yield TestClient(api_mod.app), api_mod
    finally:
        api_mod._db_conn = None
        api_mod._db_facade = None
        if prior is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = prior
        os.unlink(tmp.name)


def test_cors_allows_the_site_but_not_other_origins(api_client):
    client, _ = api_client
    preflight = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-anthropic-key",
    }
    ok = client.options(
        "/api/chat", headers={"Origin": "https://motoquant.in", **preflight}
    )
    assert ok.headers.get("access-control-allow-origin") == "https://motoquant.in"
    evil = client.options(
        "/api/chat", headers={"Origin": "https://evil.example", **preflight}
    )
    assert "access-control-allow-origin" not in evil.headers


def test_oversized_bodies_get_413(api_client):
    client, api_mod = api_client
    big = b'{"q": "' + b"a" * (api_mod.MAX_REQUEST_BYTES + 10) + b'"}'
    r = client.post(
        "/api/venues/resolve",
        content=big,
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413

    def chunks():  # no Content-Length: counted as it streams
        yield b'{"q": "'
        for _ in range(api_mod.MAX_REQUEST_BYTES // 4096 + 2):
            yield b"a" * 4096
        yield b'"}'

    r = client.post(
        "/api/venues/resolve",
        content=chunks(),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413


def test_api_responses_carry_security_headers(api_client):
    client, _ = api_client
    r = client.get("/api/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert "max-age=" in r.headers.get("strict-transport-security", "")


def test_server_errors_do_not_echo_exception_text(api_client):
    _, api_mod = api_client
    err = api_mod._server_error(
        "Database error", RuntimeError("no such table at /srv/app/x.db")
    )
    assert err.status_code == 500
    assert "/srv/app" not in err.detail
    assert err.detail.startswith("Database error")


# ─── search API keys are not forwarded across hosts ──────────────────────


def test_redirect_to_another_host_drops_caller_headers(monkeypatch):
    from motoquant.llm import webtools

    seen = []

    def fake_once(url, *, timeout, headers):
        seen.append((url, dict(headers)))
        if len(seen) == 1:
            return 302, b"", "https://elsewhere.example/landing"
        return 200, b"ok", None

    monkeypatch.setattr(webtools, "_http_get_once", fake_once)
    monkeypatch.setattr(webtools, "_check_url", lambda url: None)
    status, _ = webtools._http_get(
        "https://api.search.brave.com/res/v1/web/search?q=x",
        timeout=5,
        headers={"X-Subscription-Token": "token-value"},
    )
    assert status == 200
    assert seen[0][1].get("X-Subscription-Token") == "token-value"
    assert "X-Subscription-Token" not in seen[1][1]
