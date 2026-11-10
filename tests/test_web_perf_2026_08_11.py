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


class TestSimulatorPartsTransfer(unittest.TestCase):
    """The full parts catalog crosses the wire once per page load.

    The simulator used to re-download the whole catalog on every bike change
    just to learn which parts fit. It now goes through two helpers in
    ``web/lib/api.js``: a memoised catalog fetch, and an ids-only compatibility
    request per bike. These tests pin that shape so a direct per-bike catalog
    fetch cannot creep back into the page.
    """

    @classmethod
    def setUpClass(cls):
        cls.api = (WEB_DIR / "lib" / "api.js").read_text(encoding="utf-8")
        sim_dir = WEB_DIR / "components" / "sim"
        cls.sim_sources = {
            path.relative_to(WEB_DIR).as_posix(): path.read_text(encoding="utf-8")
            for path in [
                *sim_dir.glob("*.js"),
                WEB_DIR / "app" / "simulator" / "page.js",
            ]
        }

    def test_simulator_fetches_parts_only_through_the_helpers(self):
        # /api/parts/categories is a tiny list and is fine; a parts-list URL
        # built inside the page is the regression.
        offenders = [
            name for name, src in self.sim_sources.items() if "/api/parts?" in src
        ]
        self.assertEqual(offenders, [], "parts list fetched outside lib/api.js")
        state = self.sim_sources["components/sim/useSimulatorState.js"]
        self.assertIn("getPartsCatalog()", state)
        self.assertIn("getCompatiblePartIds(", state)

    def test_catalog_fetch_is_memoised_and_unscoped(self):
        body = self.api[self.api.index("export function getPartsCatalog()") :]
        body = body[: body.index("export async function getCompatiblePartIds")]
        self.assertIn("if (_partsPromise) return _partsPromise;", body)
        # No bike id: one response serves every bike for the page lifetime.
        self.assertIn("/api/parts?limit=5000", body)
        self.assertNotIn("bike_id", body)
        # A failed load must not be cached forever.
        self.assertIn("_partsPromise = null;", body)

    def test_per_bike_request_is_ids_only(self):
        body = self.api[self.api.index("export async function getCompatiblePartIds") :]
        body = body[: body.index("\n}\n") + 3]
        self.assertIn("compatible_only=true", body)
        self.assertIn("fields=id", body)
        self.assertIn("{ signal }", body)  # superseded bike changes are abortable


if __name__ == "__main__":
    unittest.main()
