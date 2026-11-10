"""
MotoQuant — Scrapling-backed polite fetch layer (dev-side tooling)
==================================================================
Escalating three-tier fetcher for bike-data scraping runs:

    basic   → scrapling.Fetcher      (curl_cffi, Chrome TLS impersonation)
    browser → scrapling.DynamicFetcher (Playwright Chromium, renders JS)
    stealth → scrapling.StealthyFetcher (Camoufox; requires a ~700 MB
              browser download via `camoufox fetch` — OPT-IN only)

Every response is classified (``classify_response``) into one of four
outcomes, and only ``ok`` is ever treated as a successful fetch:

    ok            HTTP 200 with no anti-bot challenge markers
    blocked       403/429/503 or a challenge page (even on HTTP 200)
    server_error  5xx — transient; the next tier is tried
    client_error  any other non-200 (404/410/…) — a definitive answer,
                  so escalating a browser at it would just waste a request

``blocked`` and ``server_error`` both escalate to the next tier, up to
``FetchPolicy.max_tier``. **Only ``ok`` responses are cached as
successes**; a failure is never re-served as if it were a page (the cache
is a reproducibility store, not a way to make a 404 permanent).

Every fetch is polite by construction: per-domain rate limiting (the
larger of ``rate_limit_s`` and the site's robots.txt ``Crawl-delay``),
robots.txt respected, and raw HTML cached to disk so re-parses and
resumed runs never re-hit the site.

robots.txt handling follows RFC 9309 §2.3.1 and **fails closed**: if
robots.txt is unreachable (5xx, 429, or a network/driver error) we assume
complete disallow. Only an explicit "unavailable" (404/410/other 4xx)
means full allow. protego is used when installed; otherwise the stdlib
``urllib.robotparser`` is the fallback, so the politeness gate is always
live — never silently skipped.

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
import urllib.robotparser
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

# ── Response classification ──────────────────────────────────────────────

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

OUTCOME_OK = "ok"
OUTCOME_BLOCKED = "blocked"
OUTCOME_SERVER_ERROR = "server_error"
OUTCOME_CLIENT_ERROR = "client_error"

# Outcomes that justify trying the next (heavier) tier. A 5xx is included
# because a flaky origin — or an edge that 500s at curl_cffi but serves a
# real browser — must not stop escalation dead.
ESCALATING_OUTCOMES = frozenset({OUTCOME_BLOCKED, OUTCOME_SERVER_ERROR})

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
    """Raised when robots.txt disallows the URL, or is unreachable.

    Unreachable counts as disallowed on purpose: RFC 9309 §2.3.1.4 says a
    crawler must assume complete disallow when robots.txt cannot be
    fetched due to server errors.
    """


class FetchFailedError(RuntimeError):
    """Raised when every allowed tier errored (network/driver failures)."""


@dataclass
class FetchResult:
    """One fetched page.

    ``outcome`` is the authoritative signal — use ``result.ok``. ``blocked``
    is kept as the narrower "every allowed tier was refused by an anti-bot
    wall" flag.
    """

    url: str
    status: int
    html: str
    tier: str
    from_cache: bool = False
    blocked: bool = False
    outcome: str = OUTCOME_OK

    @property
    def ok(self) -> bool:
        """True only for a genuine 200 with no challenge markers."""
        return self.outcome == OUTCOME_OK

    def failure_reason(self) -> str:
        """Human-readable reason for a non-ok result (empty when ok)."""
        if self.ok:
            return ""
        if self.outcome == OUTCOME_BLOCKED:
            return f"blocked at every allowed tier (status {self.status})"
        if self.outcome == OUTCOME_SERVER_ERROR:
            return f"server error at every allowed tier (status {self.status})"
        return f"HTTP {self.status}"


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
    # Successful (200) pages are cached FOREVER on purpose: the cache is
    # the reproducibility store that makes re-parses free. Failures are a
    # different animal — a 404/410 is negative-cached only long enough to
    # stop a resumed run hammering the same dead URL, then re-checked.
    failure_cache_ttl_s: float = 900.0
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
    """True when a response smells like an anti-bot refusal.

    Narrow by design: 403/429/503 or a challenge body. A 404 or a 500 is
    *not* a block — see ``classify_response`` for the full picture.
    """
    if status in BLOCK_STATUSES:
        return True
    head = html[:_MARKER_SCAN_BYTES].lower()
    return any(marker in head for marker in CHALLENGE_MARKERS)


def classify_response(status: int, html: str) -> str:
    """Map (status, body) → one of the OUTCOME_* constants."""
    if looks_blocked(status, html):
        return OUTCOME_BLOCKED
    if 500 <= status <= 599:
        return OUTCOME_SERVER_ERROR
    if status != 200:
        return OUTCOME_CLIENT_ERROR
    return OUTCOME_OK


# ── robots.txt ───────────────────────────────────────────────────────────


class _StdlibRobotsParser:
    """protego-shaped adapter over stdlib ``urllib.robotparser``.

    Used when protego is not installed so the politeness gate is always
    enforced (protego is better at wildcards; stdlib handles the common
    Allow/Disallow/Crawl-delay cases and never silently allows everything).
    """

    def __init__(self, body: str) -> None:
        self._rp = urllib.robotparser.RobotFileParser()
        self._rp.parse(body.splitlines())
        # RobotFileParser refuses everything until it believes it has read
        # a file; mark it read now that we have parsed a real body.
        self._rp.modified()

    def can_fetch(self, url: str, user_agent: str) -> bool:  # protego arg order
        return bool(self._rp.can_fetch(user_agent, url))

    def crawl_delay(self, user_agent: str):
        try:
            return self._rp.crawl_delay(user_agent)
        except Exception:  # pragma: no cover — defensive
            return None


def parse_robots_body(body: str):
    """Parse robots.txt content with protego, falling back to stdlib."""
    try:
        from protego import Protego
    except ImportError:
        return _StdlibRobotsParser(body)
    try:
        return Protego.parse(body)
    except Exception as exc:  # malformed for protego → stdlib is lenient
        logger.info("protego could not parse robots.txt (%s) — using stdlib", exc)
        return _StdlibRobotsParser(body)


ROBOTS_PARSER = "parser"
ROBOTS_ALLOW_ALL = "allow_all"
ROBOTS_DISALLOW_ALL = "disallow_all"


@dataclass
class RobotsRules:
    """Decision object for one domain's robots.txt."""

    mode: str
    parser: object | None = None
    crawl_delay_s: float = 0.0
    reason: str = ""

    def allows(self, url: str, user_agent: str) -> bool:
        if self.mode == ROBOTS_ALLOW_ALL:
            return True
        if self.mode == ROBOTS_DISALLOW_ALL:
            return False
        return bool(self.parser.can_fetch(url, user_agent))  # type: ignore[union-attr]


# Injection seam: a fetch function takes a URL and returns (status, html).
FetchFn = Callable[[str], tuple[int, str]]


STAT_KEYS: tuple[str, ...] = (
    "fetched",
    "cache_hits",
    "escalations",
    "blocked",
    "failed",
    "robots_denied",
)


class PoliteFetcher:
    """
    Rate-limited, robots-respecting, cached, tier-escalating page fetcher.

    ``fetch_fns`` maps tier name → FetchFn and exists so tests (and dry
    runs) can exercise the full cache/rate-limit/escalation/robots logic
    with zero network and zero scrapling. When omitted, real scrapling
    fetchers are built lazily on first use.
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
        self._robots_cache: dict[str, RobotsRules] = {}  # domain → decision
        self.stats: dict[str, int] = dict.fromkeys(STAT_KEYS, 0)
        if self.policy.cache_dir is not None:
            Path(self.policy.cache_dir).mkdir(parents=True, exist_ok=True)

    # ── public API ───────────────────────────────────────────────────────

    def fetch(self, url: str) -> FetchResult:
        """Fetch one URL through cache → robots → rate limit → tiers.

        Returns a FetchResult whose ``ok`` flag is the only thing a caller
        should trust: a non-ok result carries the status and reason but its
        ``html`` is failure output, never a page.
        """
        cached = self._cache_read(url)
        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached

        if self.policy.respect_robots:
            rules = self._robots_for(url)
            if not rules.allows(url, self.policy.user_agent):
                self.stats["robots_denied"] += 1
                detail = f" ({rules.reason})" if rules.reason else ""
                raise RobotsDisallowedError(
                    f"robots.txt disallows {url} for our user agent{detail} — "
                    "refusing to fetch (override with respect_robots=False "
                    "only if you have the site owner's blessing)."
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
            outcome = classify_response(status, html)
            result = FetchResult(
                url=url,
                status=status,
                html=html,
                tier=tier,
                outcome=outcome,
                blocked=(outcome == OUTCOME_BLOCKED),
            )
            if outcome == OUTCOME_OK:
                self._cache_write(result)
                return result
            if outcome not in ESCALATING_OUTCOMES:
                # Definitive client answer (404/410/…): a heavier tier would
                # get the same thing. Negative-cached with a short TTL, never
                # as a success.
                logger.info("HTTP %s for %s — not escalating", status, url)
                self.stats["failed"] += 1
                self._cache_write(result)
                return result
            last_result = result
            logger.info(
                "%s on tier=%s (status=%s) for %s — escalating",
                outcome,
                tier,
                status,
                url,
            )
            self.stats["escalations"] += 1

        if last_result is None:
            raise FetchFailedError(
                f"every allowed tier errored for {url}: {last_error}"
            ) from last_error
        if last_result.outcome == OUTCOME_BLOCKED:
            last_result.blocked = True
            self.stats["blocked"] += 1
        else:
            self.stats["failed"] += 1
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
        status = int(data["status"])
        html = data["html"]
        # Entries written before outcomes existed carry no marker. The old
        # writer treated ANY status as a success, so such an entry with a
        # non-200 status is poison: drop it outright (one-time self-heal of
        # caches written before this fix) rather than re-serving a 404 body
        # as a page forever.
        recorded_outcome = data.get("outcome")
        outcome = recorded_outcome or classify_response(status, html)
        if outcome != OUTCOME_OK:
            if recorded_outcome is None:
                logger.info(
                    "discarding legacy cached failure (status %s) for %s", status, url
                )
                return None
            if self._failure_entry_expired(data):
                logger.info("stale cached failure for %s — refetching", url)
                return None
        return FetchResult(
            url=data["url"],
            status=status,
            html=html,
            tier=data.get("tier", TIER_BASIC),
            from_cache=True,
            outcome=outcome,
            blocked=(outcome == OUTCOME_BLOCKED),
        )

    def _failure_entry_expired(self, data: dict) -> bool:
        stamp = data.get("fetched_at")
        if not stamp:
            return True
        try:
            written = datetime.fromisoformat(stamp)
        except ValueError:
            return True
        if written.tzinfo is None:
            written = written.replace(tzinfo=timezone.utc)
        age_s = (datetime.now(timezone.utc) - written).total_seconds()
        return age_s > self.policy.failure_cache_ttl_s

    def _cache_write(self, result: FetchResult) -> None:
        """Persist a fetch. Only ``ok`` and definitive client errors land.

        A blocked/5xx response is never written: re-running with a higher
        --max-tier (or after the wall lifts) must be able to retry at once.
        """
        if self.policy.cache_dir is None:
            return
        if result.outcome not in (OUTCOME_OK, OUTCOME_CLIENT_ERROR):
            return
        path = cache_path_for(result.url, self.policy.cache_dir)
        payload = {
            "url": result.url,
            "status": result.status,
            "tier": result.tier,
            "outcome": result.outcome,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "html": result.html,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    # ── politeness ───────────────────────────────────────────────────────

    def _effective_delay(self, domain: str) -> float:
        """max(configured rate limit, robots.txt Crawl-delay) for a domain."""
        rules = self._robots_cache.get(domain)
        crawl_delay = rules.crawl_delay_s if rules is not None else 0.0
        return max(self.policy.rate_limit_s, crawl_delay)

    def _rate_limit(self, url: str) -> None:
        domain = urllib.parse.urlparse(url).netloc
        now = time.monotonic()
        last = self._last_request.get(domain)
        if last is not None:
            wait = self._effective_delay(domain) - (now - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request[domain] = time.monotonic()

    def _robots_for(self, url: str) -> RobotsRules:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc
        if domain not in self._robots_cache:
            self._robots_cache[domain] = self._load_robots(parsed)
        return self._robots_cache[domain]

    def _load_robots(self, parsed_url) -> RobotsRules:
        """Fetch + parse robots.txt for one domain, failing CLOSED.

        RFC 9309 §2.3.1: 2xx → apply the rules; "unavailable" (4xx) → full
        allow; "unreachable" (5xx, 429, transport failure) → assume
        complete disallow.
        """
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            # robots.txt itself always goes through the cheapest tier only
            # and is exempt from the robots gate (it IS the gate).
            self._rate_limit(robots_url)
            status, body = self._fetch_fn(TIER_BASIC)(robots_url)
        except ScraplingNotInstalled:
            raise
        except Exception as exc:
            reason = f"{robots_url} unreachable ({exc}) — RFC 9309 §2.3.1.4 disallow"
            logger.warning("%s", reason)
            return RobotsRules(mode=ROBOTS_DISALLOW_ALL, reason=reason)

        if status == 429 or 500 <= status <= 599:
            reason = (
                f"{robots_url} returned {status} — unreachable, "
                "RFC 9309 §2.3.1.4 requires assuming complete disallow"
            )
            logger.warning("%s", reason)
            return RobotsRules(mode=ROBOTS_DISALLOW_ALL, reason=reason)

        if status != 200:
            reason = f"{robots_url} returned {status} — treated as unavailable"
            logger.info("%s (full allow per RFC 9309 §2.3.1.3)", reason)
            return RobotsRules(mode=ROBOTS_ALLOW_ALL, reason=reason)

        parser = parse_robots_body(body)
        delay = parser.crawl_delay(self.policy.user_agent)
        try:
            crawl_delay_s = float(delay) if delay else 0.0
        except (TypeError, ValueError):
            crawl_delay_s = 0.0
        if crawl_delay_s > self.policy.rate_limit_s:
            logger.info(
                "%s asks for Crawl-delay %.1fs (> our %.1fs) — honouring it",
                parsed_url.netloc,
                crawl_delay_s,
                self.policy.rate_limit_s,
            )
        return RobotsRules(
            mode=ROBOTS_PARSER, parser=parser, crawl_delay_s=crawl_delay_s
        )

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
                # solve_cloudflare=True makes Camoufox sit through and clear
                # a Cloudflare interstitial. This tier is opt-in only and is
                # documented in docs/SCRAPING.md — use it solely where you
                # have a legitimate basis to access the content.
                resp = sf.StealthyFetcher.fetch(
                    url,
                    headless=True,
                    solve_cloudflare=True,
                    timeout=max(policy.timeout_s, 60.0) * 1000,  # milliseconds
                )
                return resp.status, resp.html_content

            return stealth

        raise ValueError(f"unknown tier {tier!r}")
