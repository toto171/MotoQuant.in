"""
Tests for the Scrapling-backed dev-side scraping toolkit (July 19, 2026;
safety gates hardened July 2026 after the weekly audit §3.3f).

Covers four layers, all WITHOUT network:

  1. PoliteFetcher logic (motoquant/scraper/fetcher.py) — response
     classification, cache round-trip + negative-cache TTL, refresh bypass,
     per-domain rate limiting, tier escalation on block AND 5xx signals,
     stealth-tier opt-in gating — via the fetch_fns injection seam (no
     scrapling import needed, so the fast suite stays dependency-free).
  2. The robots.txt politeness gate — disallow honoured, RFC 9309 §2.3.1.4
     fail-closed on an unreachable robots.txt, Crawl-delay honoured. The
     robots.txt body is injected through the same seam.
  3. parse_bikez_detail on the committed bikez fixture — the SAME parser
     the legacy crawler uses (production path, single source of truth) —
     plus the URL-slug identity rules (multi-word brands, trailing year).
  4. The scripts/scrape_bike_specs.py CLI end-to-end through a
     pre-populated disk cache: fixture HTML → parse → substance gate →
     validate_spec → import-ready JSON → spec_from_dict round-trip (the
     exact functions `python -m motoquant.run import --spec-json` calls),
     and the negative case: a page that did not parse must be reported as
     a FAILURE, never exported.

None of this touches motoquant.db or the pinned physics baselines.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from motoquant.scraper.bikez import (
    parse_bikez_detail,
    parse_slug_identity,
    spec_from_dict,
)
from motoquant.scraper.fetcher import (
    OUTCOME_BLOCKED,
    OUTCOME_CLIENT_ERROR,
    OUTCOME_OK,
    OUTCOME_SERVER_ERROR,
    TIER_BASIC,
    TIER_BROWSER,
    TIER_STEALTH,
    FetchFailedError,
    FetchPolicy,
    PoliteFetcher,
    RobotsDisallowedError,
    cache_path_for,
    classify_response,
    looks_blocked,
)
from motoquant.scraper.validator import validate_spec

_REPO_ROOT = Path(__file__).parent.parent
FIXTURE = Path(__file__).parent / "data" / "bikez_suzuki_gsx-r_1000_2005.html"
FIXTURE_URL = "https://bikez.com/motorcycles/suzuki_gsx-r_1000_2005.php"


def _fixture_html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _ok_fn(html="<html>ok</html>", status=200, calls=None, tier=None):
    """Build an injectable fetch fn that records its calls."""

    def fn(url):
        if calls is not None:
            calls.append((tier, url))
        return status, html

    return fn


class TestLooksBlocked(unittest.TestCase):
    def test_block_statuses(self):
        for status in (403, 429, 503):
            self.assertTrue(looks_blocked(status, ""))
        for status in (200, 301, 404, 500):
            self.assertFalse(looks_blocked(status, "<html>fine</html>"))

    def test_challenge_markers_even_on_200(self):
        self.assertTrue(looks_blocked(200, "<title>Just a moment...</title>"))
        self.assertTrue(looks_blocked(200, '<div id="cf-chl-widget">'))
        self.assertFalse(looks_blocked(200, "<html>real spec page</html>"))

    def test_marker_scan_is_bounded_to_head(self):
        # A marker buried deep in a legit page must not flag it.
        html = "<html>" + "x" * 20000 + "captcha</html>"
        self.assertFalse(looks_blocked(200, html))


class TestClassifyResponse(unittest.TestCase):
    """Only a clean 200 is a success — everything else has a named outcome."""

    def test_ok_only_for_clean_200(self):
        self.assertEqual(classify_response(200, "<html>spec</html>"), OUTCOME_OK)

    def test_anti_bot_statuses_and_bodies_are_blocked(self):
        for status in (403, 429, 503):
            self.assertEqual(classify_response(status, ""), OUTCOME_BLOCKED)
        self.assertEqual(
            classify_response(200, "<title>Just a moment...</title>"), OUTCOME_BLOCKED
        )

    def test_server_errors_are_their_own_outcome(self):
        for status in (500, 502, 504):
            self.assertEqual(classify_response(status, "oops"), OUTCOME_SERVER_ERROR)

    def test_client_errors_are_not_success(self):
        # The audit's cache-poisoning root cause: these used to read as
        # "fetched fine" because looks_blocked() only knows 403/429/503.
        for status in (404, 410, 451):
            self.assertEqual(
                classify_response(status, "<html>Not found</html>"),
                OUTCOME_CLIENT_ERROR,
            )


class TestPoliteFetcherLogic(unittest.TestCase):
    """Escalation / cache / rate-limit logic via injected fetch fns."""

    def _fetcher(self, fetch_fns, **policy_kw):
        policy_kw.setdefault("respect_robots", False)  # unit-test the tiers
        policy_kw.setdefault("rate_limit_s", 0.0)
        return PoliteFetcher(FetchPolicy(**policy_kw), fetch_fns=fetch_fns)

    def test_basic_tier_success_never_escalates(self):
        calls = []
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(calls=calls, tier=TIER_BASIC),
                TIER_BROWSER: _ok_fn(calls=calls, tier=TIER_BROWSER),
            }
        )
        result = f.fetch("https://example.com/page")
        self.assertEqual(result.tier, TIER_BASIC)
        self.assertFalse(result.blocked)
        self.assertEqual([c[0] for c in calls], [TIER_BASIC])

    def test_escalates_on_403_then_succeeds_on_browser(self):
        calls = []
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(status=403, calls=calls, tier=TIER_BASIC),
                TIER_BROWSER: _ok_fn(calls=calls, tier=TIER_BROWSER),
            }
        )
        result = f.fetch("https://example.com/page")
        self.assertEqual(result.tier, TIER_BROWSER)
        self.assertFalse(result.blocked)
        self.assertEqual([c[0] for c in calls], [TIER_BASIC, TIER_BROWSER])
        self.assertEqual(f.stats["escalations"], 1)

    def test_challenge_page_escalates_even_on_200(self):
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(html="<title>Just a moment...</title>"),
                TIER_BROWSER: _ok_fn(html="<html>real</html>"),
            }
        )
        result = f.fetch("https://example.com/page")
        self.assertEqual(result.tier, TIER_BROWSER)

    def test_stealth_unreachable_unless_opted_in(self):
        calls = []
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(status=403, calls=calls, tier=TIER_BASIC),
                TIER_BROWSER: _ok_fn(status=403, calls=calls, tier=TIER_BROWSER),
                TIER_STEALTH: _ok_fn(calls=calls, tier=TIER_STEALTH),
            }
        )  # default max_tier=browser
        result = f.fetch("https://example.com/page")
        self.assertTrue(result.blocked)
        self.assertNotIn(TIER_STEALTH, [c[0] for c in calls])

        calls.clear()
        f2 = self._fetcher(
            {
                TIER_BASIC: _ok_fn(status=403, calls=calls, tier=TIER_BASIC),
                TIER_BROWSER: _ok_fn(status=403, calls=calls, tier=TIER_BROWSER),
                TIER_STEALTH: _ok_fn(calls=calls, tier=TIER_STEALTH),
            },
            max_tier=TIER_STEALTH,
        )
        result = f2.fetch("https://example.com/page")
        self.assertFalse(result.blocked)
        self.assertEqual(result.tier, TIER_STEALTH)

    def test_tier_exception_falls_through_to_next(self):
        def boom(url):
            raise OSError("driver crashed")

        f = self._fetcher({TIER_BASIC: boom, TIER_BROWSER: _ok_fn()})
        result = f.fetch("https://example.com/page")
        self.assertEqual(result.tier, TIER_BROWSER)

    def test_all_tiers_error_raises_typed(self):
        def boom(url):
            raise OSError("driver crashed")

        f = self._fetcher({TIER_BASIC: boom, TIER_BROWSER: boom})
        with self.assertRaises(FetchFailedError):
            f.fetch("https://example.com/page")

    def test_cache_round_trip_and_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            fns = {TIER_BASIC: _ok_fn(html="<html>v1</html>", calls=calls, tier="b")}
            f = self._fetcher(fns, cache_dir=Path(tmp), max_tier=TIER_BASIC)
            r1 = f.fetch("https://example.com/page")
            self.assertFalse(r1.from_cache)
            r2 = f.fetch("https://example.com/page")
            self.assertTrue(r2.from_cache)
            self.assertEqual(r2.html, "<html>v1</html>")
            self.assertEqual(len(calls), 1)  # second fetch never hit the "network"
            self.assertEqual(f.stats["cache_hits"], 1)

            # refresh=True bypasses the read but still writes
            f_refresh = self._fetcher(
                {TIER_BASIC: _ok_fn(html="<html>v2</html>", calls=calls, tier="b")},
                cache_dir=Path(tmp),
                max_tier=TIER_BASIC,
                refresh=True,
            )
            r3 = f_refresh.fetch("https://example.com/page")
            self.assertFalse(r3.from_cache)
            self.assertEqual(r3.html, "<html>v2</html>")

    def test_blocked_results_are_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = self._fetcher(
                {TIER_BASIC: _ok_fn(status=403), TIER_BROWSER: _ok_fn(status=403)},
                cache_dir=Path(tmp),
            )
            result = f.fetch("https://example.com/page")
            self.assertTrue(result.blocked)
            self.assertFalse(
                cache_path_for("https://example.com/page", Path(tmp)).exists()
            )

    def test_404_is_not_a_success_and_does_not_escalate(self):
        calls = []
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(
                    status=404,
                    html="<html>Not found</html>",
                    calls=calls,
                    tier=TIER_BASIC,
                ),
                TIER_BROWSER: _ok_fn(calls=calls, tier=TIER_BROWSER),
            }
        )
        result = f.fetch("https://example.com/gone")
        self.assertFalse(result.ok)
        self.assertEqual(result.outcome, OUTCOME_CLIENT_ERROR)
        # A definitive client answer: spinning up a browser gets the same 404.
        self.assertEqual([c[0] for c in calls], [TIER_BASIC])

    def test_404_body_is_never_re_served_as_a_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = self._fetcher(
                {TIER_BASIC: _ok_fn(status=404, html="<html>Not found</html>")},
                cache_dir=Path(tmp),
                max_tier=TIER_BASIC,
            )
            first = f.fetch("https://example.com/gone")
            self.assertFalse(first.ok)
            # It may be negative-cached (politeness), but it must come back
            # marked as a failure — never as a fetched page.
            second = f.fetch("https://example.com/gone")
            self.assertFalse(second.ok)
            self.assertEqual(second.status, 404)

    def test_server_error_escalates_instead_of_halting(self):
        calls = []
        f = self._fetcher(
            {
                TIER_BASIC: _ok_fn(status=500, calls=calls, tier=TIER_BASIC),
                TIER_BROWSER: _ok_fn(
                    html="<html>real</html>", calls=calls, tier=TIER_BROWSER
                ),
            }
        )
        result = f.fetch("https://example.com/page")
        self.assertTrue(result.ok)
        self.assertEqual(result.tier, TIER_BROWSER)
        self.assertEqual([c[0] for c in calls], [TIER_BASIC, TIER_BROWSER])
        self.assertEqual(f.stats["escalations"], 1)

    def test_exhausted_server_errors_are_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = self._fetcher(
                {TIER_BASIC: _ok_fn(status=502), TIER_BROWSER: _ok_fn(status=502)},
                cache_dir=Path(tmp),
            )
            result = f.fetch("https://example.com/page")
            self.assertFalse(result.ok)
            self.assertEqual(result.outcome, OUTCOME_SERVER_ERROR)
            # A transient origin failure must never become permanent.
            self.assertFalse(
                cache_path_for("https://example.com/page", Path(tmp)).exists()
            )

    def _write_cache_entry(self, tmp: Path, url: str, payload: dict) -> Path:
        path = cache_path_for(url, tmp)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_legacy_poisoned_cache_entry_is_not_served(self):
        """An entry written by the pre-fix code (any status = success)."""
        url = "https://example.com/page"
        with tempfile.TemporaryDirectory() as tmp:
            self._write_cache_entry(
                Path(tmp),
                url,
                {  # note: no "outcome" key — that is the legacy shape
                    "url": url,
                    "status": 404,
                    "tier": TIER_BASIC,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "html": "<html>Not found</html>",
                },
            )
            f = self._fetcher(
                {TIER_BASIC: _ok_fn(html="<html>real page</html>")},
                cache_dir=Path(tmp),
                max_tier=TIER_BASIC,
            )
            result = f.fetch(url)
            self.assertTrue(result.ok)
            self.assertEqual(result.html, "<html>real page</html>")

    def test_negative_cache_expires_but_success_cache_does_not(self):
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            # Aged failure entry → must be re-fetched.
            self._write_cache_entry(
                Path(tmp),
                "https://example.com/gone",
                {
                    "url": "https://example.com/gone",
                    "status": 404,
                    "tier": TIER_BASIC,
                    "outcome": OUTCOME_CLIENT_ERROR,
                    "fetched_at": old,
                    "html": "",
                },
            )
            # Aged success entry → still served (reproducibility contract).
            self._write_cache_entry(
                Path(tmp),
                "https://example.com/page",
                {
                    "url": "https://example.com/page",
                    "status": 200,
                    "tier": TIER_BASIC,
                    "outcome": OUTCOME_OK,
                    "fetched_at": old,
                    "html": "<html>archived</html>",
                },
            )
            f = self._fetcher(
                {TIER_BASIC: _ok_fn(html="<html>fresh</html>")},
                cache_dir=Path(tmp),
                max_tier=TIER_BASIC,
            )
            refetched = f.fetch("https://example.com/gone")
            self.assertTrue(refetched.ok)
            self.assertFalse(refetched.from_cache)

            archived = f.fetch("https://example.com/page")
            self.assertTrue(archived.from_cache)
            self.assertEqual(archived.html, "<html>archived</html>")

    def test_rate_limit_sleeps_between_same_domain_hits(self):
        sleeps = []
        f = self._fetcher({TIER_BASIC: _ok_fn()}, rate_limit_s=5.0, max_tier=TIER_BASIC)
        import motoquant.scraper.fetcher as fetcher_mod

        original_sleep = fetcher_mod.time.sleep
        fetcher_mod.time.sleep = lambda s: sleeps.append(s)
        try:
            f.fetch("https://example.com/a")
            f.fetch("https://example.com/b")  # same domain → must wait
            f.fetch("https://other.example.net/c")  # new domain → no wait
        finally:
            fetcher_mod.time.sleep = original_sleep
        self.assertEqual(len(sleeps), 1)
        self.assertGreater(sleeps[0], 0.0)
        self.assertLessEqual(sleeps[0], 5.0)

    def test_invalid_max_tier_rejected_eagerly(self):
        with self.assertRaises(ValueError):
            PoliteFetcher(FetchPolicy(max_tier="warp"), fetch_fns={})


class TestRobotsGate(unittest.TestCase):
    """The politeness gate docs/SCRAPING.md calls a hard rule.

    Every one of these drives the REAL robots path — the robots.txt body
    is injected through the same fetch_fns seam, so there is no network
    and no protego requirement (the fetcher falls back to stdlib
    urllib.robotparser when protego is absent).
    """

    PAGE_URL = "https://example.com/motorcycles/suzuki_gsx-r_1000_2005.php"

    def _fetcher(self, robots, page_calls=None, **policy_kw):
        """robots: (status, body) tuple, or an Exception to raise."""

        def basic(url):
            if url.endswith("/robots.txt"):
                if isinstance(robots, Exception):
                    raise robots
                return robots
            if page_calls is not None:
                page_calls.append(url)
            return 200, "<html>real page</html>"

        policy_kw.setdefault("rate_limit_s", 0.0)
        policy_kw.setdefault("max_tier", TIER_BASIC)
        return PoliteFetcher(
            FetchPolicy(respect_robots=True, **policy_kw),
            fetch_fns={TIER_BASIC: basic},
        )

    def test_disallowed_path_is_refused(self):
        page_calls = []
        f = self._fetcher((200, "User-agent: *\nDisallow: /motorcycles/\n"), page_calls)
        with self.assertRaises(RobotsDisallowedError):
            f.fetch(self.PAGE_URL)
        self.assertEqual(page_calls, [])  # the page was never requested
        self.assertEqual(f.stats["robots_denied"], 1)

    def test_allowed_path_passes(self):
        f = self._fetcher((200, "User-agent: *\nDisallow: /admin/\n"))
        self.assertTrue(f.fetch(self.PAGE_URL).ok)

    def test_robots_5xx_means_complete_disallow(self):
        # RFC 9309 §2.3.1.4: unreachable robots.txt → assume full disallow.
        for status in (500, 502, 503):
            f = self._fetcher((status, ""))
            with self.assertRaises(RobotsDisallowedError):
                f.fetch(self.PAGE_URL)

    def test_robots_429_means_complete_disallow(self):
        f = self._fetcher((429, ""))
        with self.assertRaises(RobotsDisallowedError):
            f.fetch(self.PAGE_URL)

    def test_robots_transport_failure_means_complete_disallow(self):
        f = self._fetcher(OSError("connection reset"))
        with self.assertRaises(RobotsDisallowedError):
            f.fetch(self.PAGE_URL)

    def test_robots_404_means_unavailable_so_full_allow(self):
        # RFC 9309 §2.3.1.3: "unavailable" (4xx) → the crawler may proceed.
        f = self._fetcher((404, "Not found"))
        self.assertTrue(f.fetch(self.PAGE_URL).ok)

    def test_robots_decision_is_cached_per_domain(self):
        robots_hits = []

        def basic(url):
            if url.endswith("/robots.txt"):
                robots_hits.append(url)
                return 200, "User-agent: *\nAllow: /\n"
            return 200, "<html>real page</html>"

        f = PoliteFetcher(
            FetchPolicy(respect_robots=True, rate_limit_s=0.0, max_tier=TIER_BASIC),
            fetch_fns={TIER_BASIC: basic},
        )
        f.fetch(self.PAGE_URL)
        f.fetch("https://example.com/motorcycles/other_2020.php")
        self.assertEqual(len(robots_hits), 1)

    def test_crawl_delay_overrides_a_shorter_rate_limit(self):
        sleeps = []
        f = self._fetcher(
            (200, "User-agent: *\nCrawl-delay: 5\nDisallow: /admin/\n"),
            rate_limit_s=0.5,
        )
        import motoquant.scraper.fetcher as fetcher_mod

        original_sleep = fetcher_mod.time.sleep
        fetcher_mod.time.sleep = lambda s: sleeps.append(s)
        try:
            f.fetch(self.PAGE_URL)
            f.fetch("https://example.com/motorcycles/other_2020.php")
        finally:
            fetcher_mod.time.sleep = original_sleep
        self.assertTrue(sleeps, "expected the crawl delay to be applied")
        # Every wait must respect the site's 5 s ask, not our 0.5 s default.
        self.assertGreater(max(sleeps), 0.5)
        self.assertLessEqual(max(sleeps), 5.0)

    def test_crawl_delay_never_shortens_our_own_rate_limit(self):
        sleeps = []
        f = self._fetcher(
            (200, "User-agent: *\nCrawl-delay: 1\n"),
            rate_limit_s=4.0,
        )
        import motoquant.scraper.fetcher as fetcher_mod

        original_sleep = fetcher_mod.time.sleep
        fetcher_mod.time.sleep = lambda s: sleeps.append(s)
        try:
            f.fetch(self.PAGE_URL)
            f.fetch("https://example.com/motorcycles/other_2020.php")
        finally:
            fetcher_mod.time.sleep = original_sleep
        self.assertGreater(max(sleeps), 1.0)

    def test_cached_pages_are_served_without_a_robots_round_trip(self):
        """Warm-cache re-parses stay free (and offline) by design."""
        with tempfile.TemporaryDirectory() as tmp:
            cache_path_for(self.PAGE_URL, Path(tmp)).write_text(
                json.dumps(
                    {
                        "url": self.PAGE_URL,
                        "status": 200,
                        "tier": TIER_BASIC,
                        "outcome": OUTCOME_OK,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "html": "<html>cached</html>",
                    }
                ),
                encoding="utf-8",
            )
            f = self._fetcher(OSError("no network"), cache_dir=Path(tmp))
            result = f.fetch(self.PAGE_URL)
            self.assertTrue(result.from_cache)


class TestBikezFixtureParse(unittest.TestCase):
    """parse_bikez_detail is the production parser — pin it on the fixture."""

    @classmethod
    def setUpClass(cls):
        cls.spec = parse_bikez_detail(_fixture_html(), FIXTURE_URL)

    def test_identity_from_url_slug(self):
        self.assertEqual(self.spec.manufacturer, "Suzuki")
        self.assertEqual(self.spec.model_name, "GSX R 1000")
        self.assertEqual(self.spec.year_from, 2005)
        self.assertEqual(self.spec.category, "sport")

    def test_engine_fields(self):
        self.assertAlmostEqual(self.spec.displacement_cc, 999.0, places=1)
        # Parser prefers the kW figure: 129.9 kW × 1.341 = 174.2 hp
        self.assertAlmostEqual(self.spec.peak_power_hp, 174.2, delta=0.2)
        self.assertEqual(self.spec.peak_power_rpm, 11000)
        # ft-lbs preferred: 81.1 × 1.356 ≈ 110.0 Nm
        self.assertAlmostEqual(self.spec.peak_torque_nm, 110.0, delta=0.3)
        self.assertEqual(self.spec.peak_torque_rpm, 9000)
        self.assertAlmostEqual(self.spec.bore_mm, 73.4, places=1)
        self.assertAlmostEqual(self.spec.stroke_mm, 59.0, places=1)
        self.assertAlmostEqual(self.spec.compression_ratio, 12.5, places=1)
        self.assertEqual(self.spec.cylinders, 4)
        self.assertEqual(self.spec.valve_config, "dohc")

    def test_chassis_and_drivetrain(self):
        self.assertAlmostEqual(self.spec.dry_mass_kg, 166.0, places=1)
        self.assertEqual(self.spec.gears, 6)
        self.assertEqual(self.spec.final_drive, "chain")
        self.assertAlmostEqual(self.spec.wheelbase_mm, 1405.0, places=0)
        self.assertEqual(self.spec.front_tire_size, "120/70ZR17")
        self.assertEqual(self.spec.rear_tire_size, "190/50ZR17")

    def test_provenance(self):
        self.assertEqual(self.spec.source_name, "bikez")
        self.assertEqual(self.spec.source_url, FIXTURE_URL)

    def test_slug_year_rule_keeps_displacement_tokens(self):
        # Regression pin for the July-19 slug fix: a 4-digit displacement
        # token mid-slug is part of the MODEL; only a trailing plausible
        # year is the year. Pre-fix this parsed as model "S" / year 1000.
        spec = parse_bikez_detail(
            "", "https://bikez.com/motorcycles/bmw_s_1000_rr_2019.php"
        )
        self.assertEqual(spec.model_name, "S 1000 RR")
        self.assertEqual(spec.year_from, 2019)

    def test_validator_accepts_fixture_spec(self):
        result = validate_spec(self.spec)
        self.assertTrue(result.is_valid, msg=str(result))


class TestSlugIdentity(unittest.TestCase):
    """URL-slug identity rules — brands first, then the trailing year."""

    def test_multiword_brands_are_not_split_into_the_model(self):
        cases = {
            "moto_guzzi_v7_iii_2021": ("Moto Guzzi", "V7 III", 2021),
            "royal_enfield_classic_350_2021": ("Royal Enfield", "CLASSIC 350", 2021),
            "mv_agusta_f4_1000_r_2010": ("Mv Agusta", "F4 1000 R", 2010),
            "harley_davidson_iron_883_2016": ("Harley Davidson", "IRON 883", 2016),
            "moto_morini_corsaro_1200_2008": ("Moto Morini", "CORSARO 1200", 2008),
        }
        for slug, expected in cases.items():
            with self.subTest(slug=slug):
                got = parse_slug_identity(f"https://bikez.com/motorcycles/{slug}.php")
                self.assertEqual(got, expected)

    def test_single_word_brands_are_untouched(self):
        cases = {
            "suzuki_gsx-r_1000_2005": ("Suzuki", "GSX R 1000", 2005),
            "bmw_s_1000_rr_2019": ("Bmw", "S 1000 RR", 2019),
            "honda_cbr_600_rr_2007": ("Honda", "CBR 600 RR", 2007),
            # Hyphenated brand slugs already worked — keep them working.
            "harley-davidson_fat_boy_2018": ("Harley Davidson", "FAT BOY", 2018),
        }
        for slug, expected in cases.items():
            with self.subTest(slug=slug):
                got = parse_slug_identity(f"https://bikez.com/motorcycles/{slug}.php")
                self.assertEqual(got, expected)

    def test_multiword_brand_flows_through_parse_bikez_detail(self):
        spec = parse_bikez_detail(
            "", "https://bikez.com/motorcycles/moto_guzzi_v7_iii_2021.php"
        )
        self.assertEqual(spec.manufacturer, "Moto Guzzi")
        self.assertEqual(spec.model_name, "V7 III")

    def test_brand_only_matches_when_both_tokens_are_present(self):
        # "indian_scout_2021" must stay Indian/SCOUT — the multi-word list
        # must not swallow a model word.
        got = parse_slug_identity("https://bikez.com/motorcycles/indian_scout_2021.php")
        self.assertEqual(got, ("Indian", "SCOUT", 2021))


class _CliHarness:
    """Shared CLI driver: warm disk cache in, (exit code, json, report) out."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import scrape_bike_specs

        cls.cli = scrape_bike_specs

    def _run_cli(self, tmp: Path, pages: dict[str, str] | None = None):
        """Drive the CLI over a warm cache. pages: {url: html}."""
        pages = pages or {FIXTURE_URL: _fixture_html()}
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        # Pre-populate the cache exactly as PoliteFetcher would have.
        for url, html in pages.items():
            cache_path_for(url, cache_dir).write_text(
                json.dumps(
                    {
                        "url": url,
                        "status": 200,
                        "tier": TIER_BASIC,
                        "outcome": OUTCOME_OK,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "html": html,
                    }
                ),
                encoding="utf-8",
            )
        out = tmp / "specs.json"
        report = tmp / "triage.md"
        code = self.cli.main(
            [
                "--urls",
                *pages,
                "--out",
                str(out),
                "--report",
                str(report),
                "--cache-dir",
                str(cache_dir),
            ]
        )
        return code, out, report


class TestScrapeCliEndToEnd(_CliHarness, unittest.TestCase):
    """Drive scripts/scrape_bike_specs.py main() through a warm disk cache
    (zero network, zero scrapling) and check the import-ready output."""

    def test_cli_emits_valid_import_ready_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, report = self._run_cli(Path(tmpdir))
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            entry = data[0]
            self.assertEqual(entry["manufacturer"], "Suzuki")
            self.assertEqual(entry["source_name"], "bikez")
            self.assertEqual(entry["source_url"], FIXTURE_URL)
            self.assertNotIn("raw_data", entry)
            self.assertNotIn("field_confidence", entry)

            # Production import path: run.py does spec_from_dict → validate.
            spec = spec_from_dict(entry)
            self.assertTrue(validate_spec(spec).is_valid)
            self.assertAlmostEqual(spec.displacement_cc, 999.0, places=1)

    def test_cli_report_surfaces_unmapped_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _, _, report = self._run_cli(Path(tmpdir))
            text = report.read_text(encoding="utf-8")
            # The fixture plants three rows FIELD_MAP does not know.
            self.assertIn("Front brakes", text)
            self.assertIn("Rake (fork angle)", text)
            self.assertIn("UNVERIFIED", text)

    def test_unmapped_helper_ignores_mapped_rows(self):
        missed = self.cli.unmapped_rows(_fixture_html())
        self.assertIn("Front brakes", missed)
        self.assertNotIn("Displacement", missed)
        self.assertNotIn("Dry weight", missed)


# A page that fetched with HTTP 200 but carries no spec table at all — a
# soft-404, a JS shell, or an interstitial the challenge markers missed.
EMPTY_PAGE_HTML = "<html><body><h1>Page not found</h1></body></html>"
EMPTY_PAGE_URL = "https://bikez.com/motorcycles/suzuki_gsx-r_9999_2005.php"

# A page whose spec table is intact but whose LABELS all drifted — the
# parser maps none of them, so the spec is empty of page-parsed physics.
DRIFTED_PAGE_HTML = (
    "<html><body><table>"
    "<tr><td>Engine size</td><td>999 ccm</td></tr>"
    "<tr><td>Max output</td><td>174 HP @ 11000 RPM</td></tr>"
    "<tr><td>Kerb mass</td><td>166 kg</td></tr>"
    "<tr><td>Cylinder count</td><td>4</td></tr>"
    "<tr><td>Gearbox</td><td>6-speed</td></tr>"
    "<tr><td>Chassis</td><td>Aluminium twin spar</td></tr>"
    "</table></body></html>"
)
DRIFTED_PAGE_URL = "https://bikez.com/motorcycles/suzuki_gsx-r_1000_2007.php"


class TestSubstanceGate(unittest.TestCase):
    """A spec is import-ready only if the PAGE parsed.

    parse_bikez_detail synthesises manufacturer/model/year from the URL
    slug and validate_spec only requires those to be non-empty, so without
    this gate a 404 body or a drifted layout validates clean and is
    exported with a clean drift signal — the inversion the audit found.
    """

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import scrape_bike_specs

        cls.cli = scrape_bike_specs

    def test_real_page_passes_the_gate(self):
        spec = parse_bikez_detail(_fixture_html(), FIXTURE_URL)
        self.assertEqual(self.cli.page_parse_failures(spec, _fixture_html()), [])

    def test_empty_page_fails_the_gate_although_the_validator_likes_it(self):
        spec = parse_bikez_detail(EMPTY_PAGE_HTML, EMPTY_PAGE_URL)
        # The validator alone is NOT a gate: it passes this happily.
        self.assertTrue(validate_spec(spec).is_valid)
        failures = self.cli.page_parse_failures(spec, EMPTY_PAGE_HTML)
        self.assertTrue(failures)
        self.assertIn("no spec table", " ".join(failures))

    def test_drifted_labels_fail_the_gate(self):
        spec = parse_bikez_detail(DRIFTED_PAGE_HTML, DRIFTED_PAGE_URL)
        self.assertTrue(validate_spec(spec).is_valid)
        failures = self.cli.page_parse_failures(spec, DRIFTED_PAGE_HTML)
        self.assertTrue(failures)
        self.assertIn("label drift", " ".join(failures))

    def test_missing_power_row_fails_the_gate(self):
        html = _fixture_html().replace("Power</td>", "Max output</td>", 1)
        spec = parse_bikez_detail(html, FIXTURE_URL)
        failures = self.cli.page_parse_failures(spec, html)
        self.assertTrue(any("peak_power_hp" in f for f in failures))


class TestCliRejectsPagesThatDidNotParse(_CliHarness, unittest.TestCase):
    """Same CLI harness, negative cases."""

    def test_unparsed_page_is_never_exported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, report = self._run_cli(
                Path(tmpdir), {EMPTY_PAGE_URL: EMPTY_PAGE_HTML}
            )
            self.assertEqual(code, 1)  # nothing accepted
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), [])
            text = report.read_text(encoding="utf-8")
            self.assertIn("Fetch / parse failures", text)
            self.assertIn(EMPTY_PAGE_URL, text)
            self.assertIn("[drift]", text)
            # It must NOT be advertised as validator-clean.
            self.assertIn("Accepted (parsed **and** validator-clean): **0**", text)

    def test_failure_is_reported_even_when_other_pages_succeed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, report = self._run_cli(
                Path(tmpdir),
                {FIXTURE_URL: _fixture_html(), DRIFTED_PAGE_URL: DRIFTED_PAGE_HTML},
            )
            # Exit 2 = "specs accepted, but read the failures first".
            self.assertEqual(code, 2)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["source_url"], FIXTURE_URL)
            text = report.read_text(encoding="utf-8")
            self.assertIn("Fetch / parse failures (investigate): **1**", text)
            self.assertIn(DRIFTED_PAGE_URL, text)

    def test_drift_signal_is_not_reported_as_clean_for_an_empty_page(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _, _, report = self._run_cli(
                Path(tmpdir), {EMPTY_PAGE_URL: EMPTY_PAGE_HTML}
            )
            text = report.read_text(encoding="utf-8")
            self.assertNotIn("(none — every row mapped)", text)


if __name__ == "__main__":
    unittest.main()
