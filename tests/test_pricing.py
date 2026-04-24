"""
MotoQuant Pro — Indian-Market Parts Pricing Tests
=================================================
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
