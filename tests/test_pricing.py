"""
MotoQuant — Indian-Market Parts Pricing Tests
=============================================
Covers :mod:`motoquant.database.pricing_refresh`:

* Retailer URL template coverage + format correctness
* ``_build_search_terms`` brand-dedup logic
* ``estimate_landing_cost_inr`` GST, courier, and import-duty math
* ``refresh_retailer_urls`` end-to-end against a seeded DB
  (idempotent + ``only_missing`` + ``dry_run`` + ``overwrite``)
* ``stale_parts`` threshold behaviour
* ``coverage_report`` shape
"""

from __future__ import annotations

import os
import sys
import unittest

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motoquant.database import MotoQuantDB
from motoquant.database.pricing_refresh import (
    COURIER_INR,
    GST_RATE,
    IMPORT_DUTY_RATE,
    RETAILER_SEARCH_TEMPLATES,
    RefreshSummary,
    _build_search_terms,
    _search_url,
    coverage_report,
    estimate_landing_cost_inr,
    refresh_retailer_urls,
    stale_parts,
)

# ─────────────────────────────────────────────────────────────────
# Unit tests — pure helpers (no DB)
# ─────────────────────────────────────────────────────────────────


class TestBuildSearchTerms:
    def test_empty_brand(self):
        assert _build_search_terms("", "Stage 2 Filter") == "Stage 2 Filter"

    def test_empty_model(self):
        assert _build_search_terms("Akrapovic", "") == "Akrapovic"

    def test_no_overlap(self):
        assert _build_search_terms("Akrapovic", "Evolution Line Ti") == (
            "Akrapovic Evolution Line Ti"
        )

    def test_model_starts_with_brand_exact(self):
        # "SBS Carbon pad V9" + brand "SBS" → "SBS Carbon pad V9"  (no doubling)
        assert _build_search_terms("SBS", "SBS Carbon pad V9") == "SBS Carbon pad V9"

    def test_model_starts_with_brand_case_insensitive(self):
        assert _build_search_terms("DNA", "dna Stage 2 Filter") == "DNA Stage 2 Filter"

    def test_multi_word_brand_first_token_dedup(self):
        # "JT Sprockets" + "JT Front Sprocket 15T" → don't need to re-emit "JT"
        result = _build_search_terms("JT Sprockets", "JT Front Sprocket 15T")
        assert result == "JT Sprockets Front Sprocket 15T"

    def test_ampersand_brand_preserved(self):
        assert _build_search_terms("K&N", "K&N Drop-In Filter") == "K&N Drop-In Filter"


class TestSearchURL:
    def test_known_retailer_template(self):
        url = _search_url("MotoParts India", "Akrapovic", "Evolution Line")
        assert url.startswith("https://www.mototorque.in/search?q=")
        assert "Akrapovic" in url
        assert "Evolution" in url
        assert "%20" in url  # URL-encoded space

    def test_unknown_retailer_falls_back_to_mototorque(self):
        url = _search_url("ThereIsNoSuchShop", "SC-Project", "CR-T")
        assert url.startswith("https://www.mototorque.in/search?q=")

    def test_special_chars_encoded(self):
        url = _search_url("MotoParts India", "K&N", "Drop-In")
        # & must be encoded or it terminates the query string
        assert "%26" in url or "&amp;" in url

    def test_brand_dedup_reflected_in_url(self):
        url = _search_url("MotoParts India", "SBS", "SBS Carbon Pad")
        # Decoded path should NOT contain "SBS SBS"
        from urllib.parse import unquote

        assert "SBS SBS" not in unquote(url)

    def test_every_template_has_q_placeholder(self):
        for retailer, template in RETAILER_SEARCH_TEMPLATES.items():
            assert "{q}" in template, f"{retailer} template missing {{q}}"


# ─────────────────────────────────────────────────────────────────
# Landing-cost math
# ─────────────────────────────────────────────────────────────────


class TestLandingCostINR:
    def test_bare_sticker_adds_gst_and_courier(self):
        # 10 000 × 1.18 + 250 = 12 050
        assert estimate_landing_cost_inr(10_000.0) == pytest.approx(12_050.0, abs=0.1)

    def test_gst_rate_matches_constant(self):
        # 100 × (1 + GST) + courier
        expected = 100.0 * (1.0 + GST_RATE) + COURIER_INR
        assert estimate_landing_cost_inr(100.0) == pytest.approx(expected, abs=0.01)

    def test_eu_retailer_triggers_import_duty(self):
        base = estimate_landing_cost_inr(10_000.0)
        bumped = estimate_landing_cost_inr(10_000.0, retailer="Akrapovic EU")
        # Imported should be ~30 % more expensive
        assert bumped == pytest.approx(base * (1.0 + IMPORT_DUTY_RATE), abs=0.5)

    def test_japan_retailer_triggers_duty(self):
        bumped = estimate_landing_cost_inr(10_000.0, retailer="Öhlins (Japan)")
        assert bumped > estimate_landing_cost_inr(10_000.0)

    def test_india_retailer_no_duty(self):
        domestic = estimate_landing_cost_inr(10_000.0, retailer="MotoParts India")
        bare = estimate_landing_cost_inr(10_000.0)
        assert domestic == pytest.approx(bare, abs=0.1)

    def test_import_only_availability_bumps(self):
        with_flag = estimate_landing_cost_inr(
            10_000.0, retailer="MotoParts India", availability="import_only"
        )
        # even domestic retailer + import_only adds duty
        assert with_flag > estimate_landing_cost_inr(
            10_000.0, retailer="MotoParts India"
        )

    def test_zero_sticker(self):
        # 0 × 1.18 + 250 = 250
        assert estimate_landing_cost_inr(0.0) == pytest.approx(COURIER_INR, abs=0.1)


# ─────────────────────────────────────────────────────────────────
# DB refresh tests — use a temp DB seeded with a handful of parts
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
def seeded_db(tmp_path):
    """Fresh MotoQuant DB + a few known parts, with URLs cleared."""
    db_path = str(tmp_path / "motoquant_pricing.db")
    db = MotoQuantDB(db_path)
    db.initialize()

    # Insert a minimal fixture set: 3 parts with retailer, 1 without.
    # category_id 1 = any existing category (schema seeds categories).
    conn = db.conn
    cat_id = conn.execute(
        "SELECT id FROM parts_categories ORDER BY id LIMIT 1"
    ).fetchone()["id"]

    conn.executemany(
        """
        INSERT INTO parts (
            category_id, brand, model_name, part_number,
            specifications, retailer, retailer_url, last_price_check
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                cat_id,
                "Akrapovic",
                "Evolution Line Ti",
                "AK-EL-TI-001",
                "{}",
                "MotoParts India",
                None,
                None,
            ),
            (
                cat_id,
                "SBS",
                "SBS Carbon Pad V9",
                "SBS-V9-001",
                "{}",
                "Grand Pitstop",
                None,
                None,
            ),
            (
                cat_id,
                "SC-Project",
                "CR-T Carbon",
                "SCP-CRT-001",
                "{}",
                "Superbike India",
                "https://existing.example.com/foo",
                "2020-01-01",
            ),
            (cat_id, "NoRetailer", "Orphan Part", "ORPH-001", "{}", None, None, None),
        ],
    )
    conn.commit()

    yield db
    db.close()


class TestRefreshRetailerURLs:
    def test_fills_missing_urls(self, seeded_db):
        summary = refresh_retailer_urls(seeded_db.conn, only_missing=True)
        assert isinstance(summary, RefreshSummary)
        assert summary.total == 4
        assert summary.skipped_no_retailer == 1  # the "NoRetailer" row
        # Two rows had NULL urls + a retailer → should be filled
        assert summary.urls_filled == 2

    def test_only_missing_preserves_existing(self, seeded_db):
        refresh_retailer_urls(seeded_db.conn, only_missing=True)
        row = seeded_db.conn.execute(
            "SELECT retailer_url FROM parts WHERE brand = 'SC-Project'"
        ).fetchone()
        assert row["retailer_url"] == "https://existing.example.com/foo"

    def test_overwrite_replaces_existing(self, seeded_db):
        refresh_retailer_urls(seeded_db.conn, only_missing=False)
        row = seeded_db.conn.execute(
            "SELECT retailer_url FROM parts WHERE brand = 'SC-Project'"
        ).fetchone()
        assert row["retailer_url"] != "https://existing.example.com/foo"
        assert row["retailer_url"].startswith("https://www.superbikestore.com/")
        assert "CR-T" in row["retailer_url"] or "CR%2DT" in row["retailer_url"]

    def test_stamps_updated_for_all_with_retailer(self, seeded_db):
        refresh_retailer_urls(seeded_db.conn, only_missing=True)
        stamps = seeded_db.conn.execute(
            "SELECT brand, last_price_check FROM parts"
        ).fetchall()
        stamps_by_brand = {r["brand"]: r["last_price_check"] for r in stamps}
        # The three parts with retailers should all have a fresh stamp
        assert stamps_by_brand["Akrapovic"] is not None
        assert stamps_by_brand["SBS"] is not None
        assert stamps_by_brand["SC-Project"] is not None
        # The orphan (no retailer) is untouched — stamp remains NULL
        assert stamps_by_brand["NoRetailer"] is None

    def test_dry_run_does_not_commit(self, seeded_db):
        summary = refresh_retailer_urls(seeded_db.conn, dry_run=True)
        assert summary.urls_filled == 2
        urls = seeded_db.conn.execute(
            "SELECT retailer_url FROM parts WHERE brand IN ('Akrapovic', 'SBS')"
        ).fetchall()
        assert all(u["retailer_url"] is None for u in urls)

    def test_idempotent_second_run(self, seeded_db):
        first = refresh_retailer_urls(seeded_db.conn, only_missing=True)
        second = refresh_retailer_urls(seeded_db.conn, only_missing=True)
        # Second pass: nothing left to fill
        assert first.urls_filled == 2
        assert second.urls_filled == 0
        # But stamps still get refreshed (harmless bookkeeping)
        assert second.check_stamps_updated == 3

    def test_fills_use_correct_retailer_template(self, seeded_db):
        refresh_retailer_urls(seeded_db.conn, only_missing=True)
        akra = seeded_db.conn.execute(
            "SELECT retailer_url FROM parts WHERE brand = 'Akrapovic'"
        ).fetchone()["retailer_url"]
        sbs = seeded_db.conn.execute(
            "SELECT retailer_url FROM parts WHERE brand = 'SBS'"
        ).fetchone()["retailer_url"]
        assert "mototorque.in" in akra  # MotoParts India template
        assert "grandpitstop.com" in sbs  # Grand Pitstop template


class TestStaleParts:
    def test_lists_never_checked(self, seeded_db):
        # With only_missing, orphan part has no stamp and is thus stale
        rows = stale_parts(seeded_db.conn, days_threshold=30)
        brands = [r[1] for r in rows]
        assert "Akrapovic" in brands
        assert "SBS" in brands
        # The SC-Project row was stamped 2020-01-01 → definitely stale
        assert "SC-Project" in brands

    def test_returns_oldest_first(self, seeded_db):
        rows = stale_parts(seeded_db.conn, days_threshold=30)
        # SC-Project has '2020-01-01'; the null-stamp rows default to '1970-01-01',
        # so they should actually rank first in the "oldest" sort. Ensure ordering
        # is ascending by last_price_check.
        stamps = [r[3] for r in rows]
        assert stamps == sorted(stamps)

    def test_threshold_excludes_recent(self, seeded_db):
        # Stamp one row to "today" and make sure it drops out
        seeded_db.conn.execute(
            "UPDATE parts SET last_price_check = date('now') WHERE brand = 'SBS'"
        )
        seeded_db.conn.commit()
        rows = stale_parts(seeded_db.conn, days_threshold=30)
        brands = [r[1] for r in rows]
        assert "SBS" not in brands


class TestCoverageReport:
    def test_shape_contains_expected_keys(self, seeded_db):
        report = coverage_report(seeded_db.conn)
        for key in (
            "total_parts",
            "with_price_inr",
            "with_retailer",
            "with_retailer_url",
            "refreshed_last_30_days",
            "price_coverage_pct",
            "retailer_coverage_pct",
            "url_coverage_pct",
            "freshness_pct",
        ):
            assert key in report

    def test_counts_match_db(self, seeded_db):
        report = coverage_report(seeded_db.conn)
        assert report["total_parts"] == 4
        assert report["with_retailer"] == 3  # 3 have a retailer, orphan does not

    def test_coverage_percentages_never_negative_or_above_100(self, seeded_db):
        report = coverage_report(seeded_db.conn)
        for k in (
            "price_coverage_pct",
            "retailer_coverage_pct",
            "url_coverage_pct",
            "freshness_pct",
        ):
            assert 0.0 <= report[k] <= 100.0

    def test_after_refresh_url_coverage_jumps(self, seeded_db):
        before = coverage_report(seeded_db.conn)
        refresh_retailer_urls(seeded_db.conn, only_missing=True)
        after = coverage_report(seeded_db.conn)
        assert after["with_retailer_url"] > before["with_retailer_url"]


# ═══════════════════════════════════════════════════════════════════════════
# Live pricing adapter tests — all HTTP calls mocked via unittest.mock
# ═══════════════════════════════════════════════════════════════════════════

import datetime
import unittest.mock as _mock


class TestRetailAdapters(unittest.TestCase):
    """Unit tests for the retail_adapters module — no real HTTP."""

    def _make_response(self, body: str, status: int = 200):
        """Build a fake urllib response context manager."""
        raw = body.encode("utf-8")
        resp = _mock.MagicMock()
        resp.__enter__ = _mock.MagicMock(return_value=resp)
        resp.__exit__ = _mock.MagicMock(return_value=False)
        resp.read = _mock.MagicMock(return_value=raw)
        resp.status = status
        return resp

    def test_woocommerce_price_extraction(self):
        """Generic WooCommerce price pattern should parse INR symbol."""
        from motoquant.database.retail_adapters import _extract_price_inr

        html = '<span class="price"><span class="woocommerce-Price-amount">&#8377;12,500.00</span></span>'
        price = _extract_price_inr(html)
        self.assertIsNotNone(price)
        self.assertAlmostEqual(price, 12500.0, places=0)

    def test_rs_prefix_extraction(self):
        """'Rs.' price prefix should be parsed."""
        from motoquant.database.retail_adapters import _extract_price_inr

        html = '<div class="price">Rs. 8,999</div>'
        price = _extract_price_inr(html)
        self.assertIsNotNone(price)
        self.assertAlmostEqual(price, 8999.0, places=0)

    def test_oos_detection(self):
        """Out-of-stock signal should flip in_stock to False."""
        from motoquant.database.retail_adapters import _extract_in_stock

        self.assertFalse(_extract_in_stock("This product is Out of Stock"))
        self.assertFalse(_extract_in_stock("sold out"))
        self.assertTrue(_extract_in_stock("In Stock — ships in 2 days"))

    def test_fetch_price_mocked_powertronic(self):
        """fetch_price should call adapter and return PriceResult on success."""
        from motoquant.database.retail_adapters import fetch_price

        fake_html = "<html><body>Price: &#8377;6,500 Add to cart</body></html>"
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(fake_html)
        ):
            result = fetch_price("https://powertronicecu.com/product/z-fi-tc/")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.price_inr, 6500.0, places=0)
        self.assertTrue(result.in_stock)
        self.assertEqual(result.retailer, "Powertronic ECU")

    def test_fetch_price_oos_mocked(self):
        """OOS page should return in_stock=False."""
        from motoquant.database.retail_adapters import fetch_price

        fake_html = "<html><body>Rs. 14,000 — Out of Stock</body></html>"
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(fake_html)
        ):
            result = fetch_price("https://motodelic.com/product/k-n-filter/")
        self.assertIsNotNone(result)
        self.assertFalse(result.in_stock)

    def test_fetch_price_network_error_returns_none(self):
        """Network error should return None gracefully (no exception raised)."""
        import urllib.error

        from motoquant.database.retail_adapters import fetch_price

        with _mock.patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")
        ):
            result = fetch_price("https://motomiu.com/product/exhaust/")
        self.assertIsNone(result)

    def test_cloudflare_challenge_returns_none(self):
        """Cloudflare challenge page should return None for Akrapovic adapter."""
        from motoquant.database.retail_adapters import fetch_akrapovic

        cf_html = (
            "<html><title>Just a moment...</title><body>Cloudflare Ray ID</body></html>"
        )
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(cf_html)
        ):
            result = fetch_akrapovic("https://akrapovic.com/en/motorcycle/product/123")
        self.assertIsNone(result)

    # ─────────────────────────────────────────────────────────────────
    # April 29, 2026 — adapters added for 11 new Indian retailer surfaces
    # (Mototorque, Grand Pitstop, Superbike Store, Race Dynamics, Healtech,
    # YSS, Battery Bhai, Dynojet, IndiaMart, Tyrebazaar, Tyrekart). Each
    # tested with a mocked HTML page containing realistic INR markup.
    # ─────────────────────────────────────────────────────────────────

    def test_adapter_registry_count_apr29(self):
        """Registry should contain >=17 named adapters after April 29 expansion."""
        from motoquant.database.retail_adapters import ADAPTERS

        self.assertGreaterEqual(len(ADAPTERS), 17)
        # The 11 new domains must be routable
        new_domains = [
            "mototorque.in",
            "grandpitstop.com",
            "superbikestore.com",
            "racedynamics.in",
            "healtech-india.com",
            "yssindia.in",
            "batterybhai.com",
            "dynojetindia.com",
            "indiamart.com",
            "tyrebazaar.com",
            "tyrekart.com",
        ]
        for d in new_domains:
            self.assertIn(d, ADAPTERS, f"missing adapter for {d}")

    def test_fetch_mototorque_shopify_paise(self):
        """Mototorque adapter handles Shopify paise-encoded prices."""
        from motoquant.database.retail_adapters import fetch_mototorque

        html = '<script>var product = {"price":1850000,"available":true};</script>'  # ₹18,500 in paise
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_mototorque("https://mototorque.in/products/akrapovic-r15")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Mototorque")
        self.assertAlmostEqual(r.price_inr, 18500.0, places=0)
        self.assertTrue(r.in_stock)

    def test_fetch_grandpitstop_inr_symbol(self):
        from motoquant.database.retail_adapters import fetch_grandpitstop

        html = '<div class="product-price">&#8377;3,250</div>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_grandpitstop("https://grandpitstop.com/products/jt-sprocket")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Grand Pitstop")
        self.assertAlmostEqual(r.price_inr, 3250.0, places=0)

    def test_fetch_superbikestore_woocommerce(self):
        from motoquant.database.retail_adapters import fetch_superbikestore

        html = '<span class="woocommerce-Price-amount">Rs. 1,25,000</span>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_superbikestore(
                "https://superbikestore.com/product/akrapovic-titanium-hayabusa"
            )
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Superbike Store")
        self.assertAlmostEqual(r.price_inr, 125000.0, places=0)

    def test_fetch_racedynamics_ecu(self):
        from motoquant.database.retail_adapters import fetch_racedynamics

        html = "<p>Powertronic Z-Fi TC — INR 38,500</p>"
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_racedynamics("https://racedynamics.in/product/zfi-tc/")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Race Dynamics")
        self.assertAlmostEqual(r.price_inr, 38500.0, places=0)

    def test_fetch_healtech_india_quickshifter(self):
        from motoquant.database.retail_adapters import fetch_healtech_india

        html = '<div class="price">&#8377;14,750</div><p>In stock</p>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_healtech_india("https://healtech-india.com/product/qse")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "HealTech India")
        self.assertTrue(r.in_stock)

    def test_fetch_yssindia_suspension(self):
        from motoquant.database.retail_adapters import fetch_yssindia

        html = '<span class="amount">Rs. 28,500</span>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_yssindia("https://yssindia.in/product/g-series-rear/")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "YSS India")
        self.assertAlmostEqual(r.price_inr, 28500.0, places=0)

    def test_fetch_batterybhai_jsonld(self):
        from motoquant.database.retail_adapters import fetch_batterybhai

        # JSON-LD style price embedding (typical of React SPAs)
        html = '<script type="application/ld+json">{"@type":"Product","offers":{"price":"5499.00","priceCurrency":"INR"}}</script>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_batterybhai("https://batterybhai.com/product/shorai-lfx")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Battery Bhai")
        self.assertAlmostEqual(r.price_inr, 5499.0, places=0)

    def test_fetch_indiamart_ask_price_marks_oos(self):
        """IndiaMart 'Ask Price' / 'Get Latest Price' should mark in_stock=False."""
        from motoquant.database.retail_adapters import fetch_indiamart

        html = '<h3>Akrapovic Slip On</h3><span class="price">&#8377;45,000</span><a>Get Latest Price</a>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_indiamart(
                "https://www.indiamart.com/proddetail/akrapovic-slip-on-12345.html"
            )
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "IndiaMart")
        self.assertFalse(r.in_stock)

    def test_fetch_tyrebazaar(self):
        from motoquant.database.retail_adapters import fetch_tyrebazaar

        html = '<div class="tyre-price">&#8377;4,250</div>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_tyrebazaar("https://tyrebazaar.com/mrf-zapper-fy")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Tyrebazaar")
        self.assertAlmostEqual(r.price_inr, 4250.0, places=0)

    def test_fetch_tyrekart(self):
        from motoquant.database.retail_adapters import fetch_tyrekart

        html = '<span class="amount">Rs. 6,800</span>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_tyrekart("https://www.tyrekart.com/ceat-zoom-d")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Tyrekart")
        self.assertAlmostEqual(r.price_inr, 6800.0, places=0)

    def test_fetch_dynojet_india_pcv(self):
        from motoquant.database.retail_adapters import fetch_dynojet_india

        html = '<div class="price">&#8377;28,500</div>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_dynojet_india("https://dynojetindia.com/product/pcv/")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Dynojet India")
        self.assertAlmostEqual(r.price_inr, 28500.0, places=0)

    def test_fetch_price_routes_new_domain(self):
        """fetch_price() should route to the new adapter for tyrebazaar.com."""
        from motoquant.database.retail_adapters import fetch_price

        html = '<div class="price">&#8377;3,999</div>'
        with _mock.patch(
            "urllib.request.urlopen", return_value=self._make_response(html)
        ):
            r = fetch_price("https://tyrebazaar.com/some-tire-product")
        self.assertIsNotNone(r)
        self.assertEqual(r.retailer, "Tyrebazaar")
        self.assertAlmostEqual(r.price_inr, 3999.0, places=0)


class TestLandingCostMath(unittest.TestCase):
    """Unit tests for estimate_landing_cost_inr()."""

    def test_domestic_indian_part(self):
        """Indian-stocked part: sticker × 1.18 + 250 courier."""
        from motoquant.database.pricing_refresh import (
            COURIER_INR,
            GST_RATE,
            estimate_landing_cost_inr,
        )

        sticker = 10_000.0
        expected = sticker * (1 + GST_RATE) + COURIER_INR
        result = estimate_landing_cost_inr(sticker, retailer="Grand Pitstop")
        self.assertAlmostEqual(result, expected, places=1)

    def test_us_sourced_part_has_import_duty(self):
        """US-sourced retailer should add 30% import duty on top of GST + courier."""
        from motoquant.database.pricing_refresh import (
            COURIER_INR,
            GST_RATE,
            IMPORT_DUTY_RATE,
            estimate_landing_cost_inr,
        )

        sticker = 10_000.0
        base = sticker * (1 + GST_RATE) + COURIER_INR
        expected = base * (1 + IMPORT_DUTY_RATE)
        result = estimate_landing_cost_inr(sticker, retailer="RevZilla USA")
        self.assertAlmostEqual(result, expected, places=1)

    def test_import_only_availability(self):
        """availability='import_only' triggers import duty even for neutral retailer."""
        from motoquant.database.pricing_refresh import (
            COURIER_INR,
            GST_RATE,
            IMPORT_DUTY_RATE,
            estimate_landing_cost_inr,
        )

        sticker = 5_000.0
        base = sticker * (1 + GST_RATE) + COURIER_INR
        expected = base * (1 + IMPORT_DUTY_RATE)
        result = estimate_landing_cost_inr(sticker, availability="import_only")
        self.assertAlmostEqual(result, expected, places=1)


class TestStaleLivePrices(unittest.TestCase):
    """Unit tests for stale_live_prices() against an in-memory DB."""

    def _make_db(self):
        import sqlite3

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.executescript("""
            CREATE TABLE parts (
                id INTEGER PRIMARY KEY, brand TEXT, model_name TEXT,
                retailer TEXT, price_inr REAL, retailer_url TEXT
            );
            CREATE TABLE part_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER NOT NULL,
                retailer TEXT NOT NULL,
                source_url TEXT NOT NULL,
                price_inr REAL,
                in_stock INTEGER NOT NULL DEFAULT 1,
                fetched_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
                created_at TEXT DEFAULT (datetime('now','utc')),
                UNIQUE(part_id, retailer)
            );
        """)
        conn.execute(
            "INSERT INTO parts (id, brand, model_name, retailer) VALUES (1, 'Akra', 'Evo Ti', 'Akrapovic India')"
        )
        conn.execute(
            "INSERT INTO parts (id, brand, model_name, retailer) VALUES (2, 'KN', 'HA-1099', 'K&N India')"
        )
        conn.commit()
        return conn

    def test_all_parts_stale_when_no_prices(self):
        """All parts are stale when part_prices table is empty."""
        from motoquant.database.pricing_refresh import stale_live_prices

        conn = self._make_db()
        stale = stale_live_prices(conn, days_threshold=14)
        self.assertEqual(
            len(stale), 2, "both parts should be stale with empty price table"
        )

    def test_fresh_price_not_in_stale_list(self):
        """A part with a price fetched today should NOT appear in stale list."""
        from motoquant.database.pricing_refresh import stale_live_prices

        conn = self._make_db()
        conn.execute(
            "INSERT INTO part_prices (part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
            "VALUES (1, 'Akrapovic India', 'http://x.com', 45000.0, 1, datetime('now','utc'))"
        )
        conn.commit()
        stale = stale_live_prices(conn, days_threshold=14)
        part_ids = [s[0] for s in stale]
        self.assertNotIn(1, part_ids, "part 1 was just fetched and should not be stale")
        self.assertIn(2, part_ids, "part 2 has no price and should be stale")

    def test_old_price_is_stale(self):
        """A price fetched 20 days ago should appear in stale list with 14-day threshold."""
        from motoquant.database.pricing_refresh import stale_live_prices

        conn = self._make_db()
        twenty_days_ago = (
            datetime.date.today() - datetime.timedelta(days=20)
        ).isoformat() + "T00:00:00"
        conn.execute(
            "INSERT INTO part_prices (part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
            "VALUES (2, 'K&N India', 'http://x.com', 2500.0, 1, ?)",
            (twenty_days_ago,),
        )
        conn.commit()
        stale = stale_live_prices(conn, days_threshold=14)
        part_ids = [s[0] for s in stale]
        self.assertIn(
            2, part_ids, "price from 20 days ago is stale at 14-day threshold"
        )
