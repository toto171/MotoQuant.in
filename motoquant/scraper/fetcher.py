"""
MotoQuant Pro — Scrapling-backed polite fetch layer (dev-side tooling)
======================================================================
Escalating three-tier fetcher for bike-data scraping runs:

    basic   → scrapling.Fetcher      (curl_cffi, Chrome TLS impersonation)
    browser → scrapling.DynamicFetcher (Playwright Chromium, renders JS)
    stealth → scrapling.StealthyFetcher (Camoufox; requires a ~700 MB
              browser download via `camoufox fetch` — OPT-IN only)

On a block signal (403/429/503 or an anti-bot challenge page) the fetch
escalates to the next tier, up to ``FetchPolicy.max_tier``. Every fetch is
polite by construction: per-domain rate limiting, robots.txt respected
(parsed with protego), and raw HTML cached to disk so re-parses and
resumed runs never re-hit the site.

This module is DEV-SIDE ONLY. scrapling is NOT in requirements-api.txt and
must never be: the production image imports nothing from here. Install the
toolkit with ``pip install -r requirements-scrape.txt``. All scrapling
imports are lazy, so merely importing this module (or running the test
suite without scrapling) is safe — a typed ScraplingNotInstalled error is
raised only when a real network fetch is attempted.

Parsing stays where it always was: ``bikez.parse_bikez_detail`` and friends
(stdlib regex — see the "stdlib-only parsing" note in CLAUDE.md). This
module only replaces the fragile fetching layer that got the original
crawler blocked.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Tiers ────────────────────────────────────────────────────────────────

TIER_BASIC = "basic"
TIER_BROWSER = "browser"
TIER_STEALTH = "stealth"
TIER_ORDER: tuple[str, ...] = (TIER_BASIC, TIER_BROWSER, TIER_STEALTH)

# ── Block detection ──────────────────────────────────────────────────────

BLOCK_STATUSES = frozenset({403, 429, 503})
# Lowercase substrings that mark an anti-bot challenge page even when the
# HTTP status is 200 (Cloudflare and friends often 200 the interstitial).
CHALLENGE_MARKERS: tuple[str, ...] = (
    "cf-chl",
    "challenge-platform",
    "just a moment",
    "attention required",
    "verify you are human",
    "are you a robot",
    "ddos-guard",
    "px-captcha",
    "captcha-delivery",
)
# Only this much of the body is scanned for markers — challenge pages are
# tiny; real spec pages can be hundreds of KB.
_MARKER_SCAN_BYTES = 6000

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class ScraplingNotInstalled(RuntimeError):
    """Raised when a network fetch is attempted without scrapling installed."""

    def __init__(self) -> None:
        super().__init__(
            "scrapling is not installed — this is a dev-side toolkit "
            "dependency. Install it with: pip install -r requirements-scrape.txt "
            "(NEVER add it to requirements-api.txt; the prod image must not "
            "carry a scraping stack)."
        )


class RobotsDisallowedError(RuntimeError):
    """Raised when robots.txt disallows the requested URL for our agent."""


class FetchFailedError(RuntimeError):
    """Raised when every allowed tier errored (network/driver failures)."""


@dataclass
class FetchResult:
    """One fetched page. ``blocked`` means every allowed tier was refused."""

    url: str
    status: int
    html: str
    tier: str
    from_cache: bool = False
    blocked: bool = False


@dataclass
class FetchPolicy:
    """Politeness + escalation knobs for a scraping run."""

    rate_limit_s: float = 1.5
    timeout_s: float = 30.0
    retries: int = 2
    respect_robots: bool = True
    # Stealth (Camoufox) is deliberately NOT reachable by default: it needs
    # a separate browser download and is only justified against hard walls.
    max_tier: str = TIER_BROWSER
    cache_dir: Path | None = None
    refresh: bool = False  # True → ignore cache reads (still writes)
    user_agent: str = DEFAULT_USER_AGENT
    # Explicit Chromium path for the browser tier (e.g. the pre-installed
    # /opt/pw-browsers build in Claude sandboxes). None → Playwright default.
    browser_executable: str | None = None

    def allowed_tiers(self) -> tuple[str, ...]:
        if self.max_tier not in TIER_ORDER:
            raise ValueError(
                f"max_tier must be one of {TIER_ORDER}, got {self.max_tier!r}"
            )
        return TIER_ORDER[: TIER_ORDER.index(self.max_tier) + 1]


def cache_path_for(url: str, cache_dir: Path) -> Path:
    """Deterministic cache location for a URL (stable across runs/tests)."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return Path(cache_dir) / f"{digest}.json"


def looks_blocked(status: int, html: str) -> bool:
    """True when a response smells like an anti-bot refusal."""
    if status in BLOCK_STATUSES:
        return True
    head = html[:_MARKER_SCAN_BYTES].lower()
    return any(marker in head for marker in CHALLENGE_MARKERS)


# Injection seam: a fetch function takes a URL and returns (status, html).
FetchFn = Callable[[str], tuple[int, str]]


class PoliteFetcher:
    """
    Rate-limited, robots-respecting, cached, tier-escalating page fetcher.

    ``fetch_fns`` maps tier name → FetchFn and exists so tests (and dry
    runs) can exercise the full cache/rate-limit/escalation logic with zero
    network and zero scrapling. When omitted, real scrapling fetchers are
    built lazily on first use.
    """

    def __init__(
        self,
        policy: FetchPolicy | None = None,
        fetch_fns: dict[str, FetchFn] | None = None,
    ) -> None:
        self.policy = policy or FetchPolicy()
        self.policy.allowed_tiers()  # validate max_tier eagerly
        self._fetch_fns = fetch_fns
        self._last_request: dict[str, float] = {}  # domain → monotonic ts
        self._robots_cache: dict[str, object | None] = {}  # domain → parser
        self.stats: dict[str, int] = {
            "fetched": 0,
            "cache_hits": 0,
            "escalations": 0,
            "blocked": 0,
            "robots_denied": 0,
        }
        if self.policy.cache_dir is not None:
            Path(self.policy.cache_dir).mkdir(parents=True, exist_ok=True)

    # ── public API ───────────────────────────────────────────────────────

    def fetch(self, url: str) -> FetchResult:
        """Fetch one URL through cache → robots → rate limit → tiers."""
        cached = self._cache_read(url)
        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached

        if self.policy.respect_robots and not self._robots_allows(url):
            self.stats["robots_denied"] += 1
            raise RobotsDisallowedError(
                f"robots.txt disallows {url} for our user agent — refusing "
                "to fetch (override with respect_robots=False only if you "
                "have the site owner's blessing)."
            )

        self._rate_limit(url)

        last_result: FetchResult | None = None
        last_error: Exception | None = None
        for tier in self.policy.allowed_tiers():
            try:
                status, html = self._fetch_fn(tier)(url)
            except ScraplingNotInstalled:
                raise
            except Exception as exc:  # driver/network failure → try next tier
                logger.warning("fetch %s failed on tier=%s: %s", url, tier, exc)
                last_error = exc
                continue
            self.stats["fetched"] += 1
            result = FetchResult(url=url, status=status, html=html, tier=tier)
            if not looks_blocked(status, html):
                self._cache_write(result)
                return result
            last_result = result
            logger.info(
                "blocked on tier=%s (status=%s) for %s — escalating", tier, status, url
            )
            self.stats["escalations"] += 1

        if last_result is None:
            raise FetchFailedError(
                f"every allowed tier errored for {url}: {last_error}"
            ) from last_error
        last_result.blocked = True
        self.stats["blocked"] += 1
        return last_result

    # ── cache ────────────────────────────────────────────────────────────

    def _cache_read(self, url: str) -> FetchResult | None:
        if self.policy.cache_dir is None or self.policy.refresh:
            return None
        path = cache_path_for(url, self.policy.cache_dir)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("unreadable cache entry %s: %s", path, exc)
            return None
        return FetchResult(
            url=data["url"],
            status=int(data["status"]),
            html=data["html"],
            tier=data.get("tier", TIER_BASIC),
            from_cache=True,
        )

    def _cache_write(self, result: FetchResult) -> None:
        if self.policy.cache_dir is None:
            return
        path = cache_path_for(result.url, self.policy.cache_dir)
        payload = {
            "url": result.url,
            "status": result.status,
            "tier": result.tier,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "html": result.html,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    # ── politeness ───────────────────────────────────────────────────────

    def _rate_limit(self, url: str) -> None:
        domain = urllib.parse.urlparse(url).netloc
        now = time.monotonic()
        last = self._last_request.get(domain)
        if last is not None:
            wait = self.policy.rate_limit_s - (now - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request[domain] = time.monotonic()

    def _robots_allows(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc
        if domain not in self._robots_cache:
            self._robots_cache[domain] = self._load_robots(parsed)
        parser = self._robots_cache[domain]
        if parser is None:
            return True  # robots.txt unfetchable/unparseable → default allow
        return bool(parser.can_fetch(url, self.policy.user_agent))  # type: ignore[attr-defined]

    def _load_robots(self, parsed_url) -> object | None:
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            from protego import Protego
        except ImportError:
            logger.warning(
                "protego not installed — skipping robots.txt check "
                "(install via requirements-scrape.txt)"
            )
            return None
        try:
            # robots.txt itself always goes through the cheapest tier only
            # and is exempt from the robots gate (it IS the gate).
            self._rate_limit(robots_url)
            status, body = self._fetch_fn(TIER_BASIC)(robots_url)
        except Exception as exc:
            logger.info("could not fetch %s (%s) — default allow", robots_url, exc)
            return None
        if status != 200:
            return None
        try:
            return Protego.parse(body)
        except Exception as exc:  # malformed robots.txt → default allow
            logger.info("could not parse %s (%s) — default allow", robots_url, exc)
            return None

    # ── real fetchers (lazy scrapling imports) ───────────────────────────

    def _fetch_fn(self, tier: str) -> FetchFn:
        if self._fetch_fns is not None:
            fn = self._fetch_fns.get(tier)
            if fn is None:
                raise FetchFailedError(f"no fetch fn injected for tier={tier!r}")
            return fn
        return self._build_real_fetcher(tier)

    def _build_real_fetcher(self, tier: str) -> FetchFn:
        try:
            import scrapling.fetchers as sf
        except ImportError as exc:
            raise ScraplingNotInstalled() from exc
        policy = self.policy

        if tier == TIER_BASIC:

            def basic(url: str) -> tuple[int, str]:
                resp = sf.Fetcher.get(
                    url,
                    impersonate="chrome",
                    stealthy_headers=True,
                    timeout=policy.timeout_s,  # seconds
                    retries=policy.retries,
                )
                return resp.status, resp.html_content

            return basic

        if tier == TIER_BROWSER:

            def browser(url: str) -> tuple[int, str]:
                kwargs: dict = {
                    "headless": True,
                    "disable_resources": True,  # skip images/fonts/media
                    "timeout": policy.timeout_s * 1000,  # milliseconds
                }
                if policy.browser_executable:
                    kwargs["executable_path"] = policy.browser_executable
                resp = sf.DynamicFetcher.fetch(url, **kwargs)
                return resp.status, resp.html_content

            return browser

        if tier == TIER_STEALTH:

            def stealth(url: str) -> tuple[int, str]:
                resp = sf.StealthyFetcher.fetch(
                    url,
                    headless=True,
                    solve_cloudflare=True,
                    timeout=max(policy.timeout_s, 60.0) * 1000,  # milliseconds
                )
                return resp.status, resp.html_content

            return stealth

        raise ValueError(f"unknown tier {tier!r}")
