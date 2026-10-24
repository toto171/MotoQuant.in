"""
/api/venues/resolve must never leak the server's OpenWeatherMap API key.

requests' HTTPError / ConnectionError messages embed the full request URL,
query string included — ``...weather?appid=<key>&units=metric&q=...`` — and
the route used to return ``str(exc)`` in its 502 detail and log it verbatim
(reproduced 2026-10-24). These tests drive the REAL route through
TestClient with a stubbed ``requests.get`` and assert the key reaches
neither the response body nor any log record.
"""

from __future__ import annotations

import logging

import pytest

pytest.importorskip("fastapi")
requests = pytest.importorskip("requests")

from fastapi.testclient import TestClient  # noqa: E402

import motoquant.api as api  # noqa: E402

SECRET = "SECRET-OWM-KEY-5f3a9c"
URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    f"?appid={SECRET}&units=metric&q=Atlantis"
)


class _Resp:
    def __init__(self, exc):
        self._exc = exc

    def raise_for_status(self):
        raise self._exc

    def json(self):  # pragma: no cover - never reached
        return {}


def _http_error_with_response(status: int) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = status
    resp.url = URL
    return requests.HTTPError(
        f"{status} Client Error: Unauthorized for url: {URL}", response=resp
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", SECRET)
    # Sweep scripts imported by earlier test modules run
    # ``logging.getLogger("motoquant").setLevel(logging.ERROR)`` at import,
    # which would filter the route's WARNING before caplog sees it (the
    # full-suite failure of 2026-10-24). Neutralise inherited logger state
    # for the duration of each test so the log assertions are order-proof.
    monkeypatch.setattr(logging.getLogger("motoquant"), "level", logging.NOTSET)
    monkeypatch.setattr(logging.getLogger("motoquant.api"), "disabled", False)
    # Skip the seeded-venue lookup: the OWM fallback is the path under test.
    monkeypatch.setattr(api, "_get_db", lambda: None)
    return TestClient(api.app)


@pytest.mark.parametrize(
    "make_exc,expected_reason",
    [
        (lambda: requests.HTTPError(f"401 Client Error: Unauthorized for url: {URL}"),
         "HTTPError"),
        (lambda: _http_error_with_response(401), "HTTP 401"),
        (lambda: requests.ConnectionError(
            "HTTPSConnectionPool(host='api.openweathermap.org', port=443): Max "
            f"retries exceeded with url: /data/2.5/weather?appid={SECRET}&q=x"),
         "ConnectionError"),
    ],
)  # fmt: skip
def test_upstream_error_never_leaks_the_key(
    client, monkeypatch, caplog, make_exc, expected_reason
):
    exc = make_exc()

    def fake_get(*args, **kwargs):
        if isinstance(exc, requests.ConnectionError):
            raise exc
        return _Resp(exc)

    monkeypatch.setattr(requests, "get", fake_get)
    with caplog.at_level(logging.DEBUG, logger="motoquant.api"):
        r = client.post("/api/venues/resolve", json={"location": "Atlantis Nowhere"})
    assert r.status_code == 502
    assert SECRET not in r.text
    assert "appid" not in r.text
    assert expected_reason in r.json()["detail"]
    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "OWM fetch failed" in logged  # the failure is still logged...
    assert SECRET not in logged  # ...just without the key
    assert "appid=[REDACTED]" in logged or expected_reason == "HTTP 401"


def test_redact_secrets_helper():
    msg = f"boom for url: {URL} and again {SECRET}; key=abc&api_key=def token=ghi"
    out = api._redact_secrets(msg, SECRET)
    assert SECRET not in out
    for leaked in ("abc", "def", "ghi"):
        assert f"={leaked}" not in out
    assert "appid=[REDACTED]" in out
    assert api._redact_secrets("no secrets here", None) == "no secrets here"


def test_log_assertions_survive_a_muted_motoquant_logger(client, monkeypatch, caplog):
    """Regression: the sweep scripts mute the ``motoquant`` logger at import.

    Simulate that inherited state inside the test (AFTER the fixture reset)
    and assert the redacted failure record is still captured — the old
    ``caplog.at_level(logging.DEBUG)`` (root only) failed exactly here.
    """
    logging.getLogger("motoquant").setLevel(logging.ERROR)
    exc = requests.HTTPError(f"401 Client Error: Unauthorized for url: {URL}")
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Resp(exc))
    with caplog.at_level(logging.DEBUG, logger="motoquant.api"):
        r = client.post("/api/venues/resolve", json={"location": "Atlantis Nowhere"})
    assert r.status_code == 502 and SECRET not in r.text
    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "OWM fetch failed" in logged
    assert SECRET not in logged
