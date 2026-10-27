"""
tests/test_fixwave_data_pricing.py
==================================
October 2026 core-audit fix wave — live-price freshness cache.

``fetch_live_price`` checked freshness against ``parts.retailer`` (e.g.
'superbikestore.in') but stored rows under the adapter's retailer name (e.g.
'Superbike Store'), so the cache never hit: three non-forced calls made three
network fetches. A fetched price now also stamps ``parts.last_price_check``
(the only honest moment to move it), and a cache hit returns the stored price
instead of None, so a repeated non-forced POST /api/pricing/refresh reports the
price rather than 'fetch_failed'. The retailer adapter is mocked — no HTTP.
"""

from __future__ import annotations

import datetime as dt
import unittest.mock as mock

import pytest

from motoquant.database import MotoQuantDB
from motoquant.database.pricing_refresh import fetch_live_price
from motoquant.database.retail_adapters import PriceResult

_URL = "https://www.superbikestore.in/product/akrapovic-slip-on"


@pytest.fixture
def db(tmp_path):
    d = MotoQuantDB(str(tmp_path / "pricing.db"))
    d.initialize()
    pid = d.parts.create(
        "exhaust",
        "Akrapovic",
        "Slip-On Line",
        {},
        part_number="AK-SO-1",
        price_inr=90000.0,
        retailer="superbikestore.in",
        retailer_url=_URL,
    )
    d.conn.execute(
        "UPDATE parts SET last_price_check = '2020-01-01' WHERE id = ?", (pid,)
    )
    d.conn.commit()
    yield d, pid
    d.close()


def _result(price=88000.0):
    return PriceResult(
        price_inr=price,
        in_stock=True,
        fetched_at=dt.datetime.now(dt.timezone.utc),
        source_url=_URL,
        retailer="Superbike Store",  # adapter name != parts.retailer
    )


def test_fresh_price_is_not_refetched(db):
    d, pid = db
    with mock.patch(
        "motoquant.database.retail_adapters.fetch_price", return_value=_result()
    ) as fetch:
        first = fetch_live_price(d.conn, pid)
        second = fetch_live_price(d.conn, pid)
        third = fetch_live_price(d.conn, pid)
    assert first is not None
    assert fetch.call_count == 1  # second and third served from the fresh cache
    # A cache hit is a success: it returns the stored price, not None (None
    # made POST /api/pricing/refresh report 'fetch_failed' with a null price).
    for hit in (second, third):
        assert hit is not None
        assert hit.price_inr == first.price_inr
        assert hit.in_stock is True
        assert hit.source_url == _URL
        assert hit.retailer == "Superbike Store"
        assert hit.fetched_at == first.fetched_at


def test_force_and_stale_rows_still_fetch(db):
    d, pid = db
    with mock.patch(
        "motoquant.database.retail_adapters.fetch_price", return_value=_result()
    ) as fetch:
        fetch_live_price(d.conn, pid)
        fetch_live_price(d.conn, pid, force=True)
        d.conn.execute(
            "UPDATE part_prices SET fetched_at = ? WHERE part_id = ?",
            (
                (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat(),
                pid,
            ),
        )
        fetch_live_price(d.conn, pid)
    assert fetch.call_count == 3


def test_a_real_fetch_stamps_the_check_date(db):
    d, pid = db
    with mock.patch(
        "motoquant.database.retail_adapters.fetch_price", return_value=_result()
    ):
        fetch_live_price(d.conn, pid)
    stamp = d.conn.execute(
        "SELECT last_price_check FROM parts WHERE id = ?", (pid,)
    ).fetchone()[0]
    assert stamp == dt.datetime.now(dt.timezone.utc).date().isoformat()


def test_repeated_refresh_route_serves_the_cached_price(db, monkeypatch):
    """Production path: two non-forced POST /api/pricing/refresh calls.

    Before the cache-hit fix the second call (served from the fresh cache)
    returned status 'fetch_failed' with price_inr None, although a fresh price
    had just been stored.
    """
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import motoquant.api as api_mod

    d, pid = db
    monkeypatch.setattr(api_mod, "_get_db", lambda: d.conn)
    client = TestClient(api_mod.app)
    with mock.patch(
        "motoquant.database.retail_adapters.fetch_price", return_value=_result()
    ) as fetch:
        first = client.post(f"/api/pricing/refresh/{pid}")
        second = client.post(f"/api/pricing/refresh/{pid}")
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert fetch.call_count == 1  # the second call did not hit the retailer
    a, b = first.json(), second.json()
    assert a["status"] == "refreshed" and a["price_inr"] == 88000.0
    assert b["status"] != "fetch_failed", b
    assert b["price_inr"] == 88000.0
    assert b["fetched_at"] == a["fetched_at"]
