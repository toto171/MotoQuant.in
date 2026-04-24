"""
motoquant.database.retail_adapters
====================================
Per-retailer HTML scraping adapters for live Indian-market parts pricing.

Design rules (from repo convention — see motoquant/scraper/bikez.py pattern):
  * stdlib-only: urllib.request + re.  No BeautifulSoup, no requests.
  * Each adapter is a single function: fetch_<retailer>(url) → PriceResult | None
  * Returns None on any unrecoverable error (network, parse, 429, 503).
  * Caller is responsible for rate-limiting (see RateLimiter below).

Rate limiter
------------
  * One concurrent request per retailer (serialised via per-domain token bucket).
  * Global cap: 5 requests/second across all adapters.
  * 429/503 triggers exponential back-off up to MAX_BACKOFF_S seconds,
    then returns None so the caller can persist "checked but unavailable".

Usage
-----
    from motoquant.database.retail_adapters import fetch_price, ADAPTERS

    result = fetch_price("https://powertronicecu.com/product/bazzaz-z-fi-tc/")
    if result:
        print(result.price_inr, result.in_stock)
"""

from __future__ import annotations

import logging
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────

@dataclass
class PriceResult:
    price_inr: float | None        # None = page found but price hidden / OOS
    in_stock: bool
    fetched_at: datetime
    source_url: str
    retailer: str


# ─────────────────────────────────────────────────────────────────
# Rate limiter — token-bucket per domain + global 5 req/s cap
# ─────────────────────────────────────────────────────────────────

_GLOBAL_LOCK = threading.Lock()
_DOMAIN_LOCKS: dict[str, threading.Lock] = {}
_LAST_REQUEST_TIME: float = 0.0  # epoch seconds
GLOBAL_MIN_INTERVAL_S: float = 0.20  # 5 req/s = 1 every 200 ms
MAX_BACKOFF_S: float = 30.0
_REQUEST_TIMEOUT_S: int = 10


def _domain_lock(url: str) -> threading.Lock:
    domain = urlparse(url).netloc
    with _GLOBAL_LOCK:
        if domain not in _DOMAIN_LOCKS:
            _DOMAIN_LOCKS[domain] = threading.Lock()
        return _DOMAIN_LOCKS[domain]


def _throttled_fetch(url: str, *, headers: dict[str, str] | None = None) -> bytes | None:
    """
    Fetch *url* respecting the global 5 req/s cap and per-domain serialisation.
    Retries once with exponential back-off on 429/503; returns None on failure.
    """
    global _LAST_REQUEST_TIME

    domain_lock = _domain_lock(url)
    default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MotoQuantPricingBot/1.0; "
            "+https://motoquant.in/pricing-bot)"
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9",
        "Accept-Language": "en-IN,en;q=0.8",
    }
    if headers:
        default_headers.update(headers)

    backoff = 2.0
    for attempt in range(3):
        with domain_lock:
            # Global rate throttle
            with _GLOBAL_LOCK:
                now = time.monotonic()
                wait = GLOBAL_MIN_INTERVAL_S - (now - _LAST_REQUEST_TIME)
                if wait > 0:
                    time.sleep(wait)
                _LAST_REQUEST_TIME = time.monotonic()

            try:
                req = urllib.request.Request(url, headers=default_headers)
                with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_S) as resp:
                    return resp.read()
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503):
                    sleep_for = min(backoff, MAX_BACKOFF_S)
                    log.warning("HTTP %d from %s — backing off %.1fs", exc.code, url, sleep_for)
                    time.sleep(sleep_for)
                    backoff *= 2
                    continue
                log.debug("HTTP %d from %s — skipping", exc.code, url)
                return None
            except Exception as exc:
                log.debug("fetch error %s: %s", url, exc)
                return None
    return None


# ─────────────────────────────────────────────────────────────────
# Generic HTML price extractors (reused across adapters)
# ─────────────────────────────────────────────────────────────────

_INR_PATTERNS = [
    # ₹ symbol variants followed by number
    re.compile(r'[₹\u20b9]\s*([\d,]+(?:\.\d{1,2})?)', re.UNICODE),
    # "Rs." or "INR" prefix
    re.compile(r'(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)', re.IGNORECASE),
    # WooCommerce/Shopify JSON: "price":"NNNN" or woocommerce_price: NNNN
    re.compile(r'"(?:price|regular_price|sale_price)"\s*:\s*"?([\d]+(?:\.\d{1,2})?)"?'),
    # data-price="NNNN" attribute
    re.compile(r'data-price=["\']?([\d]+(?:\.\d{1,2})?)["\']?'),
]
_OOS_PATTERNS = re.compile(
    r'out.of.stock|sold.out|not.available|unavailable|out_of_stock',
    re.IGNORECASE,
)


def _extract_price_inr(html: str) -> float | None:
    import html as _html_mod
    html = _html_mod.unescape(html)  # decode &#8377; -> ₹, &amp; etc.
    for pat in _INR_PATTERNS:
        m = pat.search(html)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw)
                if 50.0 <= val <= 2_000_000.0:   # sanity: ₹50 – ₹20L
                    return val
            except ValueError:
                pass
    return None


def _extract_in_stock(html: str) -> bool:
    """True unless we can positively identify an OOS signal."""
    return not bool(_OOS_PATTERNS.search(html))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────
# Adapter: Powertronic ECU (powertronicecu.com) — Indian ECU shop
# ─────────────────────────────────────────────────────────────────

def fetch_powertronicecu(url: str) -> PriceResult | None:
    """Scrape a Powertronic product page (WooCommerce)."""
    raw = _throttled_fetch(url)
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    price = _extract_price_inr(html)
    in_stock = _extract_in_stock(html)
    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="Powertronic ECU",
    )


# ─────────────────────────────────────────────────────────────────
# Adapter: Motomiu (motomiu.com) — general mods shop
# ─────────────────────────────────────────────────────────────────

def fetch_motomiu(url: str) -> PriceResult | None:
    """Scrape a Motomiu product page (Shopify)."""
    raw = _throttled_fetch(url)
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    # Shopify stores price in a JSON blob: "price":NNNN (paise → rupees)
    m = re.search(r'"price"\s*:\s*(\d+)', html)
    price = None
    if m:
        paise = float(m.group(1))
        # Shopify stores price in paise (× 100) but some themes store in rupees
        # Heuristic: if value > 100000 treat as paise, else rupees
        price = paise / 100.0 if paise > 100_000 else paise
        if not (50.0 <= price <= 2_000_000.0):
            price = None
    if price is None:
        price = _extract_price_inr(html)
    in_stock = _extract_in_stock(html)
    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="Motomiu",
    )


# ─────────────────────────────────────────────────────────────────
# Adapter: K&N India (knfilters.com/en-in) — air filters
# ─────────────────────────────────────────────────────────────────

def fetch_kn_india(url: str) -> PriceResult | None:
    """Scrape K&N India product page."""
    raw = _throttled_fetch(url, headers={"Accept-Language": "en-IN,en;q=0.9"})
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    price = _extract_price_inr(html)
    in_stock = _extract_in_stock(html)
    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="K&N India",
    )


# ─────────────────────────────────────────────────────────────────
# Adapter: Motodelic (motodelic.com) — general mod shop
# ─────────────────────────────────────────────────────────────────

def fetch_motodelic(url: str) -> PriceResult | None:
    """Scrape a Motodelic product page (WooCommerce)."""
    raw = _throttled_fetch(url)
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    price = _extract_price_inr(html)
    in_stock = _extract_in_stock(html)
    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="Motodelic",
    )


# ─────────────────────────────────────────────────────────────────
# Adapter: Amazon.in (sprockets / chains / OEM parts)
# Uses the public product page — no API key needed for price.
# ─────────────────────────────────────────────────────────────────

_AMAZON_PRICE_PATTERNS = [
    re.compile(r'"priceAmount"\s*:\s*([\d.]+)'),          # JSON-LD
    re.compile(r'class="a-price-whole"[^>]*>\s*([\d,]+)'),
    re.compile(r'"price"\s*:\s*"?([\d.]+)"?'),
]


def fetch_amazon_in(url: str) -> PriceResult | None:
    """Scrape an Amazon.in product page for INR price."""
    raw = _throttled_fetch(url, headers={
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")

    price = None
    for pat in _AMAZON_PRICE_PATTERNS:
        m = pat.search(html)
        if m:
            raw_val = m.group(1).replace(",", "")
            try:
                val = float(raw_val)
                if 50.0 <= val <= 2_000_000.0:
                    price = val
                    break
            except ValueError:
                pass

    in_stock = _extract_in_stock(html)
    # Amazon-specific OOS signal
    if "currently unavailable" in html.lower():
        in_stock = False

    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="Amazon.in",
    )


# ─────────────────────────────────────────────────────────────────
# Adapter: Akrapovic India (akrapovic.com)
# Akrapovic's site uses Cloudflare — we attempt the fetch but
# gracefully return None on a CF challenge rather than crashing.
# Their regional pricing is also in EUR; we store None for price_inr
# and let the estimate_landing_cost_inr() caller do currency conversion.
# ─────────────────────────────────────────────────────────────────

_CF_CHALLENGE = re.compile(r'Cloudflare|cf-browser-verification|__cf_chl', re.IGNORECASE)


def fetch_akrapovic(url: str) -> PriceResult | None:
    """Scrape Akrapovic product page. Returns None on Cloudflare challenge."""
    raw = _throttled_fetch(url)
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    if _CF_CHALLENGE.search(html):
        log.info("Akrapovic: Cloudflare challenge on %s — returning None", url)
        return None
    price = _extract_price_inr(html)
    in_stock = _extract_in_stock(html)
    return PriceResult(
        price_inr=price,
        in_stock=in_stock,
        fetched_at=_now_utc(),
        source_url=url,
        retailer="Akrapovic India",
    )


# ─────────────────────────────────────────────────────────────────
# Domain-router: pick the right adapter from a URL
# ─────────────────────────────────────────────────────────────────

#: Map of netloc substrings → adapter function
ADAPTERS: dict[str, Callable[[str], PriceResult | None]] = {
    "powertronicecu.com": fetch_powertronicecu,
    "motomiu.com":        fetch_motomiu,
    "knfilters.com":      fetch_kn_india,
    "motodelic.com":      fetch_motodelic,
    "amazon.in":          fetch_amazon_in,
    "akrapovic.com":      fetch_akrapovic,
}


def fetch_price(url: str) -> PriceResult | None:
    """
    Route *url* to the correct adapter and return a :class:`PriceResult`.

    Falls back to the generic HTML extractor for unknown domains so we always
    attempt a fetch rather than silently skipping new retailers.
    """
    netloc = urlparse(url).netloc.lower().lstrip("www.")
    for domain, fn in ADAPTERS.items():
        if domain in netloc:
            return fn(url)
    # Generic fallback — works for most WooCommerce / Shopify storefronts
    raw = _throttled_fetch(url)
    if raw is None:
        return None
    html = raw.decode("utf-8", errors="replace")
    return PriceResult(
        price_inr=_extract_price_inr(html),
        in_stock=_extract_in_stock(html),
        fetched_at=_now_utc(),
        source_url=url,
        retailer=netloc,
    )


__all__ = [
    "PriceResult",
    "fetch_price",
    "ADAPTERS",
    "fetch_powertronicecu",
    "fetch_motomiu",
    "fetch_kn_india",
    "fetch_motodelic",
    "fetch_amazon_in",
    "fetch_akrapovic",
]
