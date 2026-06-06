"""
Resolver tests — exercise motoquant/llm/resolver.py against the live
catalog DB. These are integration tests: they need a real motoquant.db
seeded with the 327-bike catalog.

Skipped when motoquant.db is not present (e.g. CI without seeded DB).
"""

from __future__ import annotations

import os
import unittest

from motoquant.llm.resolver import (
    _normalize,
    _score_candidate,
    _strip_manufacturer_prefix,
    _tokenize,
    resolve_bike,
    resolve_venue,
)
from tests._helpers import live_db_copy

# ─── Pure-function tests (no DB) ──────────────────────────────────


class TestNormalize(unittest.TestCase):
    def test_strips_year_range(self):
        self.assertEqual(_normalize("Hayabusa (2008-2012)"), "hayabusa")
        self.assertEqual(_normalize("Z H2 SE (2024-2025)"), "z h2 se")

    def test_strips_single_year(self):
        self.assertEqual(_normalize("M 1000 RR (2025)"), "m 1000 rr")

    def test_replaces_separators(self):
        self.assertEqual(_normalize("YZF-R15"), "yzf r15")
        self.assertEqual(_normalize("V-Strom 1050"), "v strom 1050")
        self.assertEqual(_normalize("MT-09"), "mt 09")

    def test_collapses_whitespace(self):
        self.assertEqual(_normalize("  Suzuki   Hayabusa  "), "suzuki hayabusa")


class TestTokenize(unittest.TestCase):
    def test_drops_short_tokens(self):
        # 'a' is too short, dropped
        self.assertEqual(_tokenize("a Hayabusa"), {"hayabusa"})

    def test_keeps_2char_tokens(self):
        # K5, V4, R1 are meaningful — must be kept
        self.assertIn("k5", _tokenize("GSX-R 1000 K5"))
        self.assertIn("v4", _tokenize("Panigale V4"))


class TestStripManufacturerPrefix(unittest.TestCase):
    def test_basic_brands(self):
        self.assertEqual(
            _strip_manufacturer_prefix("Suzuki Hayabusa"), ("hayabusa", "suzuki")
        )
        self.assertEqual(_strip_manufacturer_prefix("KTM RC 390"), ("rc 390", "ktm"))
        self.assertEqual(
            _strip_manufacturer_prefix("Yamaha YZF-R1"), ("yzf r1", "yamaha")
        )

    def test_multiword_brands(self):
        # Royal Enfield must match before just 're'
        s, m = _strip_manufacturer_prefix("Royal Enfield Continental GT 650")
        self.assertEqual(s, "continental gt 650")
        self.assertEqual(m, "royal enfield")

    def test_no_brand(self):
        self.assertEqual(_strip_manufacturer_prefix("RC 390"), ("rc 390", None))
        self.assertEqual(_strip_manufacturer_prefix("Hayabusa"), ("hayabusa", None))


class TestScoreCandidate(unittest.TestCase):
    def test_exact_subset_scores_high(self):
        # Query is a subset of candidate tokens → near-perfect
        s = _score_candidate("Hayabusa", "Suzuki", "Hayabusa GSX1300R Gen1")
        self.assertGreaterEqual(s, 85)

    def test_year_range_ignored(self):
        # "Hayabusa" should match "Hayabusa (2008-2012)" highly
        s = _score_candidate("Suzuki Hayabusa", "Suzuki", "Hayabusa (2008-2012)")
        self.assertGreaterEqual(s, 85)

    def test_full_match(self):
        s = _score_candidate("KTM RC 390", "KTM", "RC 390 (2022-2024)")
        self.assertGreaterEqual(s, 85)

    def test_unrelated_low_score(self):
        s = _score_candidate("Hayabusa", "Yamaha", "YZF-R1")
        self.assertLess(s, 50)


# ─── Live DB integration tests ────────────────────────────────────


def _live_db_path():
    """Locate motoquant.db — skip these tests if absent."""
    for cand in [
        os.environ.get("MOTOQUANT_DB"),
        "motoquant.db",
        os.path.join(os.path.dirname(__file__), "..", "motoquant.db"),
    ]:
        if cand and os.path.exists(cand):
            return cand
    return None


def _open_db(path: str):
    """Copy DB to OS tmpfile to dodge FUSE WAL issues, then open."""
    return live_db_copy(path)


@unittest.skipUnless(_live_db_path(), "motoquant.db not found")
class TestResolveBikeLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = _open_db(_live_db_path())

    # The exact bike_id depends on the seed, but we assert a hit + that the
    # matched row's manufacturer/model contain the expected name fragment.

    def assertResolvesTo(self, query: str, expected_substring: str):
        bike_id, _ = resolve_bike(query, self.db)
        self.assertIsNotNone(bike_id, f"{query!r} did not resolve")
        row = self.db._conn.execute(
            "SELECT m.name as mfr, bm.model_name FROM bike_models bm "
            "JOIN manufacturers m ON m.id = bm.manufacturer_id WHERE bm.id=?",
            (bike_id,),
        ).fetchone()
        full = f"{row['mfr']} {row['model_name']}".lower()
        self.assertIn(
            expected_substring.lower(),
            full,
            f"{query!r} resolved to {full!r}, expected substring {expected_substring!r}",
        )

    def test_suzuki_hayabusa_with_manufacturer_prefix(self):
        self.assertResolvesTo("Suzuki Hayabusa", "hayabusa")

    def test_hayabusa_alone(self):
        self.assertResolvesTo("Hayabusa", "hayabusa")

    def test_ktm_rc_390(self):
        self.assertResolvesTo("KTM RC 390", "rc 390")

    def test_rc_390_alone(self):
        self.assertResolvesTo("RC 390", "rc 390")

    def test_yzf_r15_v4_with_year_suffix(self):
        self.assertResolvesTo("Yamaha YZF-R15 V4", "r15 v4")

    def test_r15_v4_alone(self):
        self.assertResolvesTo("R15 V4", "r15 v4")

    def test_panigale_v4(self):
        self.assertResolvesTo("Panigale V4", "panigale v4")

    def test_z_h2_se(self):
        self.assertResolvesTo("Z H2 SE", "z h2 se")

    def test_aprilia_rs_660(self):
        self.assertResolvesTo("Aprilia RS 660", "rs 660")

    def test_garbage_returns_none(self):
        bike_id, suggestions = resolve_bike("zzzzzzzzz garbage 999", self.db)
        self.assertIsNone(bike_id)


@unittest.skipUnless(_live_db_path(), "motoquant.db not found")
class TestResolveVenueLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = _open_db(_live_db_path())

    def assertVenueResolves(self, query: str):
        vid = resolve_venue(query, self.db)
        self.assertIsNotNone(vid, f"venue {query!r} did not resolve")

    def test_aamby_valley(self):
        self.assertVenueResolves("Aamby Valley")

    def test_aamby_short(self):
        self.assertVenueResolves("Aamby")

    def test_mmrt(self):
        self.assertVenueResolves("MMRT")

    def test_madras(self):
        self.assertVenueResolves("Madras")

    def test_pomona(self):
        self.assertVenueResolves("Pomona")

    def test_garbage_returns_none(self):
        self.assertIsNone(resolve_venue("zzzzzzzzz", self.db))
