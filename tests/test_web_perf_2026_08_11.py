"""
Regression tests for the August-11-2026 web-performance batch.

(Lives in its own module — tests/test_hardening_2026_08_11.py is owned by
the same-day API DoS/cost-fuse batch.)

1. ``web/next.config.js`` cache headers: /surrogate/{model,bikes}.json
   (~330 KB pair, fetched by lib/surrogate.js on every simulator boot)
   previously shipped with no Cache-Control at all, so every visit
   re-transferred the pair. The config now declares
   ``public, max-age=3600, stale-while-revalidate=86400`` for
   ``/surrogate/:path*``. The test executes the REAL config module's
   ``headers()`` in Node — the exact function ``next build``/``next
   start`` calls — so reverting the config entry fails it.

2. Simulator boot parts-fetch dedup: boot used to fetch the full
   593-part catalog plain (``/api/parts?limit=2000``) and then, the
   moment ``setBike()`` landed, the re-annotate effect fetched the SAME
   catalog again with ``bike_id=`` — two transfers of the heaviest boot
   payload on every load. Boot now issues ONE bike-annotated fetch and
   records the annotated bike id (``annotatedBikeRef``) so the effect
   skips its boot-time duplicate. There is no JS unit-test runner in
   web/ (no vitest/jest — the page is verified by ``next build`` +
   verify-web.mjs), so this pins the fix at source level: the assertions
   are on the exact load-bearing lines a revert restores/removes, not on
   incidental formatting.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"

SURROGATE_CACHE_CONTROL = "public, max-age=3600, stale-while-revalidate=86400"


@unittest.skipIf(shutil.which("node") is None, "node not available")
class TestNextConfigCacheHeaders(unittest.TestCase):
    """Execute next.config.js's async headers() — the production path."""

    @classmethod
    def setUpClass(cls):
        script = (
            "require('./next.config.js').headers()"
            ".then((h) => console.log(JSON.stringify(h)))"
        )
        out = subprocess.run(
            ["node", "-e", script],
            cwd=WEB_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode != 0:
            raise AssertionError(f"headers() failed to execute: {out.stderr}")
        cls.headers = json.loads(out.stdout)

    def test_surrogate_assets_get_swr_cache_control(self):
        rule = next(
            (h for h in self.headers if h.get("source") == "/surrogate/:path*"),
            None,
        )
        self.assertIsNotNone(rule, "no /surrogate/:path* headers rule declared")
        cc = next(
            (
                h["value"]
                for h in rule.get("headers", [])
                if h.get("key", "").lower() == "cache-control"
            ),
            None,
        )
        self.assertEqual(cc, SURROGATE_CACHE_CONTROL)

    def test_no_immutable_rule_on_unhashed_public_paths(self):
        # Nothing in web/public is content-hashed (checked 2026-08-11), so an
        # `immutable` policy anywhere here would poison caches on asset regen.
        for rule in self.headers:
            for h in rule.get("headers", []):
                if h.get("key", "").lower() == "cache-control":
                    self.assertNotIn("immutable", h["value"], rule["source"])


class TestSimulatorBootPartsDedup(unittest.TestCase):
    """Pin the single-transfer boot parts fetch in web/app/simulator/page.js."""

    @classmethod
    def setUpClass(cls):
        cls.src = (WEB_DIR / "app" / "simulator" / "page.js").read_text(
            encoding="utf-8"
        )

    def test_boot_has_no_plain_parts_catalog_fetch(self):
        # The pre-fix boot line — a plain, un-annotated full-catalog transfer
        # that the re-annotate effect immediately repeated with bike_id=.
        # The un-annotated URL survives only as the no-bikes fallback branch
        # (`bootBike ? … : `), never as an unconditional fetch.
        self.assertNotIn("fetch(`${API}/api/parts?limit=2000`)", self.src)
        self.assertIn("?bike_id=${bootBike.id}&compatible_only=false", self.src)

    def test_re_annotate_effect_skips_boot_annotated_bike(self):
        # The guard that stops setBike() at boot from re-transferring the
        # catalog the boot fetch already annotated.
        self.assertIn("annotatedBikeRef.current === bike.id) return;", self.src)
        # And the boot side records what it annotated (rows-present gated so a
        # failed boot parts fetch still lets the effect recover the catalog).
        self.assertIn(
            "if (partsData.parts?.length) annotatedBikeRef.current = bootBike.id;",
            self.src,
        )

    def test_boot_progress_still_counts_five_fetches(self):
        # The boot bar ticks 1/5 per settled fetch; the dedup must not have
        # changed the fetch count the accounting is based on.
        self.assertIn("setBootProgress((v) => Math.min(1, v + 0.2));", self.src)
        self.assertEqual(self.src.count("tick(fetch("), 5)


if __name__ == "__main__":
    unittest.main()
