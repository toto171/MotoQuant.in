"""
Tests for the Scrapling-backed dev-side scraping toolkit (July 19, 2026).

Covers three layers, all WITHOUT network:

  1. PoliteFetcher logic (motoquant/scraper/fetcher.py) — cache round-trip,
     refresh bypass, per-domain rate limiting, tier escalation on block
     signals, stealth-tier opt-in gating — via the fetch_fns injection seam
     (no scrapling import needed, so the fast suite stays dependency-free).
  2. parse_bikez_detail on the committed bikez fixture — the SAME parser
     the legacy crawler uses (production path, single source of truth).
  3. The scripts/scrape_bike_specs.py CLI end-to-end through a
     pre-populated disk cache: fixture HTML → parse → validate_spec →
     import-ready JSON → spec_from_dict round-trip (the exact functions
     `python -m motoquant.run import --spec-json` calls).

None of this touches motoquant.db or the pinned physics baselines.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from motoquant.scraper.bikez import parse_bikez_detail, spec_from_dict
from motoquant.scraper.fetcher import (
    TIER_BASIC,
    TIER_BROWSER,
    TIER_STEALTH,
    FetchFailedError,
    FetchPolicy,
    PoliteFetcher,
    cache_path_for,
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


class TestScrapeCliEndToEnd(unittest.TestCase):
    """Drive scripts/scrape_bike_specs.py main() through a warm disk cache
    (zero network, zero scrapling) and check the import-ready output."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import scrape_bike_specs

        cls.cli = scrape_bike_specs

    def _run_cli(self, tmp: Path) -> tuple[int, Path, Path]:
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        # Pre-populate the cache exactly as PoliteFetcher would have.
        cache_path_for(FIXTURE_URL, cache_dir).write_text(
            json.dumps(
                {
                    "url": FIXTURE_URL,
                    "status": 200,
                    "tier": TIER_BASIC,
                    "html": _fixture_html(),
                }
            ),
            encoding="utf-8",
        )
        out = tmp / "specs.json"
        report = tmp / "triage.md"
        code = self.cli.main(
            [
                "--urls",
                FIXTURE_URL,
                "--out",
                str(out),
                "--report",
                str(report),
                "--cache-dir",
                str(cache_dir),
            ]
        )
        return code, out, report

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


if __name__ == "__main__":
    unittest.main()
