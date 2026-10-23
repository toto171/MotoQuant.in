"""
Web lookup tools for the MotoQuant chat agent.

Two capabilities, both server-side and defensive:

  web_search(query)  -- search the public web. Provider selected via env:
                          SEARCH_PROVIDER=brave   + SEARCH_API_KEY  (Brave Search API)
                          SEARCH_PROVIDER=serper  + SEARCH_API_KEY  (serper.dev)
                        With no key configured it falls back to the free
                        DuckDuckGo HTML endpoint (no account needed; fragile
                        by nature, so failures degrade to an empty result
                        with a note rather than an exception).
  web_fetch(url)     -- fetch a page and return readable text (tags stripped,
                        whitespace collapsed, hard-capped size).

Security posture:
  * web_fetch refuses non-http(s) schemes and private/loopback/link-local
    hosts (SSRF guard — the API runs on Render next to internal endpoints).
  * Responses are size-capped (512 KB raw, 8 KB extracted text) so a hostile
    page cannot balloon the LLM context or the process memory.
  * All failures return {"error": ...} instead of raising — the agent loop
    treats tool errors as data.

Uses `requests` (pinned explicitly in requirements-api.txt) with a stdlib
urllib fallback, mirroring the
weather_repo / bikez lazy-import pattern.
"""

from __future__ import annotations

import html as _html
import ipaddress
import json
import logging
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_S = 12.0
SEARCH_TIMEOUT_S = 10.0
MAX_RAW_BYTES = 512 * 1024
MAX_TEXT_CHARS = 8_000
MAX_RESULTS = 8
# Redirects are followed manually so the SSRF guard can re-run on every hop
# (see _http_get). Bound the chain to stop redirect loops.
MAX_REDIRECTS = 5
_UA = (
    "Mozilla/5.0 (compatible; MotoQuantBot/1.0; +https://motoquant.in) python-requests"
)


def web_enabled() -> bool:
    """Web tools are on unless explicitly disabled."""
    return os.environ.get("MOTOQUANT_WEB_TOOLS", "1").lower() not in (
        "0",
        "false",
        "off",
    )


# ─── SSRF guard ───────────────────────────────────────────────────────────


def _host_is_private(host: str) -> bool:
    """True when `host` resolves to a private / loopback / link-local IP."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return True  # unresolvable — refuse
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return True
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return True
    return False


def _check_url(url: str) -> str | None:
    """Return an error string if `url` must not be fetched, else None."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return "invalid URL"
    if parsed.scheme not in ("http", "https"):
        return f"unsupported scheme {parsed.scheme!r} (http/https only)"
    if not parsed.hostname:
        return "URL has no host"
    if _host_is_private(parsed.hostname):
        return "host resolves to a private or reserved address"
    return None


# ─── HTTP plumbing ────────────────────────────────────────────────────────


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """urllib redirect handler that never auto-follows — a 3xx surfaces as an
    HTTPError so the caller can re-validate the target against the SSRF guard."""

    def redirect_request(self, *args, **kwargs):  # noqa: D102
        return None


def _http_get_once(
    url: str, *, timeout: float, headers: dict[str, str]
) -> tuple[int, bytes, str | None]:
    """Single GET with automatic redirects DISABLED.

    Returns (status, body[:MAX_RAW_BYTES], location_header_or_None). The body
    is only meaningful for a final (non-redirect) response.
    """
    try:
        import requests  # lazy — transitive dep, pinned in requirements-api.txt

        # stream=True defers the body download; we read only the first
        # MAX_RAW_BYTES, so the connection must be explicitly closed or it
        # leaks out of the pool (we never consume the rest of the stream).
        resp = requests.get(
            url, timeout=timeout, headers=headers, stream=True, allow_redirects=False
        )
        try:
            body = resp.raw.read(MAX_RAW_BYTES, decode_content=True) or b""
            return resp.status_code, body, resp.headers.get("Location")
        finally:
            resp.close()
    except ImportError:
        pass
    opener = urllib.request.build_opener(_NoRedirectHandler)
    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=timeout) as resp:  # noqa: S310
            return resp.status, resp.read(MAX_RAW_BYTES), resp.headers.get("Location")
    except urllib.error.HTTPError as exc:
        # With _NoRedirectHandler a 3xx is raised here; read its Location.
        loc = exc.headers.get("Location") if exc.headers else None
        return exc.code, b"", loc


def _http_get(
    url: str, *, timeout: float, headers: dict[str, str] | None = None
) -> tuple[int, bytes]:
    """GET `url` following redirects MANUALLY, returning (status, body).

    Every redirect hop's target is re-checked with :func:`_check_url` before it
    is fetched. ``requests``/``urllib`` would otherwise follow a 3xx from an
    allowed public page straight to an internal address (cloud-metadata
    169.254.169.254, localhost, RFC-1918), bypassing the initial guard entirely
    — the classic redirect-based SSRF. (Residual: a host that rebinds DNS
    between the guard's resolution and the socket's connect is not closed here;
    the practically-exploitable hole is the unchecked redirect, which is.)
    """
    hdrs = {"User-Agent": _UA, "Accept-Language": "en"}
    if headers:
        hdrs.update(headers)
    # `timeout` is the budget for the WHOLE redirect chain, not per hop — else a
    # server could chain MAX_REDIRECTS slow hops for (MAX_REDIRECTS+1)*timeout
    # of wall time. Each hop gets whatever is left on the deadline.
    deadline = time.monotonic() + timeout
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("fetch exceeded total timeout across redirects")
        status, body, location = _http_get_once(
            current, timeout=max(0.5, remaining), headers=hdrs
        )
        if status in (301, 302, 303, 307, 308) and location:
            target = urllib.parse.urljoin(current, location)
            err = _check_url(target)
            if err:
                raise ValueError(f"blocked redirect to a disallowed host ({err})")
            current = target
            continue
        return status, body
    raise ValueError(f"too many redirects (> {MAX_REDIRECTS})")


def _extract_text(raw: bytes) -> str:
    """Crude but dependency-free HTML → readable text."""
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""
    # Drop script/style/nav noise before stripping tags.
    text = re.sub(
        r"<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()[:MAX_TEXT_CHARS]


# ─── Search providers ─────────────────────────────────────────────────────


def _search_brave(query: str, api_key: str, count: int) -> list[dict]:
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
        {"q": query, "count": count}
    )
    status, body = _http_get(
        url,
        timeout=SEARCH_TIMEOUT_S,
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
    )
    if status != 200:
        raise RuntimeError(f"Brave search HTTP {status}")
    data = json.loads(body)
    out = []
    for item in (data.get("web") or {}).get("results", [])[:count]:
        out.append(
            {
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "snippet": item.get("description") or "",
            }
        )
    return out


def _search_serper(query: str, api_key: str, count: int) -> list[dict]:
    try:
        import requests
    except ImportError as e:  # pragma: no cover - requests is pinned
        raise RuntimeError("requests package unavailable for serper search") from e
    resp = requests.post(
        "https://google.serper.dev/search",
        timeout=SEARCH_TIMEOUT_S,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": count},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Serper search HTTP {resp.status_code}")
    data = resp.json()
    out = []
    for item in data.get("organic", [])[:count]:
        out.append(
            {
                "title": item.get("title") or "",
                "url": item.get("link") or "",
                "snippet": item.get("snippet") or "",
            }
        )
    return out


_DDG_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>'
    r".*?"
    r'(?:<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>)?',
    re.DOTALL,
)


def _ddg_decode_href(href: str) -> str:
    """DuckDuckGo HTML wraps result URLs as /l/?uddg=<encoded>."""
    if "uddg=" in href:
        qs = urllib.parse.urlparse(href).query
        params = urllib.parse.parse_qs(qs)
        if params.get("uddg"):
            return params["uddg"][0]
    return href


def _search_duckduckgo(query: str, count: int) -> list[dict]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    status, body = _http_get(url, timeout=SEARCH_TIMEOUT_S)
    if status != 200:
        raise RuntimeError(f"DuckDuckGo HTTP {status}")
    text = body.decode("utf-8", errors="replace")
    out = []
    for m in _DDG_RESULT_RE.finditer(text):
        title = re.sub(r"<[^>]+>", "", m.group("title") or "").strip()
        snippet = re.sub(r"<[^>]+>", "", m.group("snippet") or "").strip()
        href = _ddg_decode_href(_html.unescape(m.group("href") or ""))
        if title and href.startswith("http"):
            out.append(
                {
                    "title": _html.unescape(title),
                    "url": href,
                    "snippet": _html.unescape(snippet),
                }
            )
        if len(out) >= count:
            break
    return out


# ─── Public surface ───────────────────────────────────────────────────────


def web_search(query: str, *, max_results: int = 5) -> dict:
    """Search the web. Returns {"results": [{title,url,snippet}], "provider": str}
    or {"error": str, "results": []} — never raises."""
    if not web_enabled():
        return {"error": "web tools disabled (MOTOQUANT_WEB_TOOLS=0)", "results": []}
    query = (query or "").strip()
    if not query:
        return {"error": "empty query", "results": []}
    count = max(1, min(int(max_results or 5), MAX_RESULTS))

    provider = (os.environ.get("SEARCH_PROVIDER") or "").lower()
    api_key = os.environ.get("SEARCH_API_KEY")
    attempts: list[tuple[str, Exception]] = []

    if provider == "brave" and api_key:
        try:
            return {
                "provider": "brave",
                "results": _search_brave(query, api_key, count),
            }
        except Exception as e:  # noqa: BLE001
            attempts.append(("brave", e))
    elif provider == "serper" and api_key:
        try:
            return {
                "provider": "serper",
                "results": _search_serper(query, api_key, count),
            }
        except Exception as e:  # noqa: BLE001
            attempts.append(("serper", e))

    try:
        return {
            "provider": "duckduckgo",
            "results": _search_duckduckgo(query, count),
        }
    except Exception as e:  # noqa: BLE001
        attempts.append(("duckduckgo", e))

    detail = "; ".join(f"{name}: {exc}" for name, exc in attempts)
    logger.warning("web_search failed (%s): %s", query[:80], detail)
    return {"error": f"search unavailable ({detail})", "results": []}


def web_fetch(url: str) -> dict:
    """Fetch a page as readable text. Returns {"url", "text"} or {"error"} —
    never raises."""
    if not web_enabled():
        return {"error": "web tools disabled (MOTOQUANT_WEB_TOOLS=0)"}
    url = (url or "").strip()
    err = _check_url(url)
    if err:
        return {"error": err, "url": url}
    try:
        status, body = _http_get(url, timeout=FETCH_TIMEOUT_S)
    except Exception as e:  # noqa: BLE001
        return {"error": f"fetch failed: {type(e).__name__}: {e}", "url": url}
    if status >= 400:
        return {"error": f"HTTP {status}", "url": url}
    text = _extract_text(body)
    if not text:
        return {"error": "no readable text extracted", "url": url}
    return {"url": url, "text": text}
