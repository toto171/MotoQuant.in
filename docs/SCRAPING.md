# Web scraping toolkit (Scrapling, dev-side)

> Added July 19, 2026. The toolkit fetches bike-spec pages with
> [Scrapling](https://github.com/D4Vinci/Scrapling) (BSD-3) and parses them
> with the repo's existing stdlib parser. It exists to make *fetching*
> reliable again (the legacy `requests` crawler is bot-walled off
> bikez.com); it does NOT change the honest-data pipeline — every scraped
> spec still goes through the validator and operator adjudication before
> any import.

## Hard rules

1. **Dev-side only.** `scrapling` lives in `requirements-scrape.txt` and
   must NEVER be added to `requirements-api.txt` — the prod image (Render,
   512 MB) carries no scraping stack. `motoquant/scraper/fetcher.py` only
   soft-imports scrapling; without it installed you get a typed
   `ScraplingNotInstalled` error at fetch time and everything else
   (parsing, tests, imports) works.
2. **Scraped data is UNVERIFIED.** The output JSON is an *input to
   adjudication*, not to the DB. Read the triage report, cross-check
   anything surprising, then dry-run the import. Nothing in the toolkit
   writes to `motoquant.db`.
3. **Politeness is not optional.** robots.txt is respected and **fails
   closed**, requests are rate-limited per domain (the larger of 1.5 s and
   the site's `Crawl-delay`), and raw HTML is disk-cached so re-parses
   never re-hit a site. The stealth tier is opt-in only.
4. **A page must prove it parsed.** Identity (manufacturer/model/year)
   comes from the URL slug, so the validator alone cannot tell a real spec
   page from a 404 body. The substance gate below is what makes
   "validator-clean" mean something.

## The two gates

`validate_spec` checks *physical plausibility*; it does **not** check that
anything was read off the page. `parse_bikez_detail` synthesises
manufacturer, model and year from the URL slug, and those are the only
fields the validator requires — so before this was fixed (weekly audit
2026-07-25 §3.3f) a 404 page, a JS shell or a renamed spec table produced
an "import-ready", validator-clean spec **with a clean drift signal**.

So there are two gates, in this order:

| Gate | Where | Rule |
|---|---|---|
| Substance | `page_parse_failures()` in `scripts/scrape_bike_specs.py` | the spec table must yield ≥ `MIN_MAPPED_ROWS` (6) mapped rows **and** a page-parsed `Displacement` and `Power` |
| Validator | `motoquant/scraper/validator.py` | physical bounds, unit corrections, consistency warnings |

A page that fails the substance gate is reported under **"Fetch / parse
failures — INVESTIGATE"**, never exported. The report distinguishes
"0 table rows" (error page / JS shell / bad fetch) from "N rows present,
only M mapped" (the site renamed its labels — real drift).

**Exit codes:** `0` = specs accepted and nothing failed · `1` = nothing
accepted · `2` = specs accepted but some pages failed to fetch or parse
(read the report before trusting the run).

## Install

```bash
pip install -r requirements-scrape.txt
```

Browser tier: needs a Chromium. On a dev machine `playwright install
chromium` once. In Claude sandboxes pass
`--browser-executable /opt/pw-browsers/chromium` (do NOT run
`playwright install`; the sandbox pin differs from scrapling's).

### The stealth tier — read this before using it

`--max-tier stealth` runs Camoufox (a hardened Firefox, ~700 MB via
`camoufox fetch`) **with `solve_cloudflare=True`**. Be clear about what
that means: it is not just a different user agent — it sits through and
*clears a Cloudflare anti-bot interstitial*, i.e. it deliberately defeats
a measure the site put up to keep automated clients out.

That is why the tier is unreachable by default (`max_tier` defaults to
`browser`) and why it must stay a conscious operator decision:

- Use it only where you have a **legitimate basis to access the content**
  — your own site, a site whose owner has said yes, or content you are
  otherwise entitled to fetch. "The data is public" is not a basis on its
  own; the interstitial is the site's stated preference.
- It does not override robots.txt — the politeness gate still runs first,
  and a `Disallow` still refuses the fetch.
- Never wire it into an unattended/scheduled job. Operator machines,
  operator-initiated runs.
- If a site walls you off and you have no standing to be there, the honest
  outcome is a gap in the catalog, not a harder fetcher. bikez.com itself
  bot-walls this repo's sessions — that gap is recorded, not defeated.

## Architecture

```
scripts/scrape_bike_specs.py        CLI driver (sources → JSON + triage report)
motoquant/scraper/fetcher.py        PoliteFetcher: cache → robots → rate limit
                                    → tier escalation (basic → browser → stealth)
motoquant/scraper/bikez.py          parse_bikez_detail() — the SAME stdlib
                                    parser the legacy crawler used (single
                                    source of parsing truth)
motoquant/scraper/validator.py      validate_spec() gate on every result
```

### Response handling

Every response is classified before anything else happens:

| Outcome | Trigger | Behaviour |
|---|---|---|
| `ok` | HTTP 200, no challenge markers | cached, returned |
| `blocked` | 403/429/503 or a challenge body (even on HTTP 200) | escalate to the next tier; never cached |
| `server_error` | 5xx | escalate (a flaky origin must not stop the run); never cached |
| `client_error` | any other non-200 (404/410/…) | no escalation — a heavier tier gets the same answer; negative-cached briefly |

Escalation runs up to `--max-tier` (default `browser`; `stealth` never
runs unless asked).

**Cache semantics.** Successful pages are cached **forever** on purpose —
the cache is the reproducibility store that makes re-parses free and
offline. Failures are not: a 404 is negative-cached for
`failure_cache_ttl_s` (15 min) purely so a resumed run does not hammer a
dead URL, then re-checked; blocked and 5xx responses are never written at
all, so re-running with a higher `--max-tier` retries immediately. Cache
entries written before this classification existed (any status counted as
a success) are detected on read and discarded — a one-time self-heal.

### robots.txt (fails closed)

Per RFC 9309 §2.3.1:

- **2xx** → the rules are applied, and a `Crawl-delay` is honoured as
  `max(crawl_delay, --rate-limit)`.
- **4xx** ("unavailable", e.g. 404) → full allow.
- **5xx, 429, or a transport failure** ("unreachable") → **complete
  disallow**. The run stops rather than guessing.

protego parses robots.txt when installed; otherwise the stdlib
`urllib.robotparser` is used, so the gate is always live — it is never
silently skipped because a dependency is missing. Cached pages are served
without a robots round-trip (a warm re-parse touches no network).

## Usage

```bash
# Explicit detail pages
python scripts/scrape_bike_specs.py \
    --urls https://bikez.com/motorcycles/suzuki_gsx-r_1000_2005.php

# Crawl a manufacturer listing (gap-fill): 20 bikes, 400cc floor
python scripts/scrape_bike_specs.py --manufacturer Suzuki \
    --limit 20 --min-cc 400 --max-tier browser

# Outputs (defaults):
#   reports/scraped_specs_<date>.json   import-ready spec list
#   reports/scrape_triage_<date>.md     validation + fetch-tier + drift report
#   scrape_cache/                       raw HTML cache (gitignored)
```

Then, after adjudicating the triage report:

```bash
python -m motoquant.run --db /tmp/scrape-check.db db init
python -m motoquant.run --db /tmp/scrape-check.db \
    import --spec-json reports/scraped_specs_<date>.json --dry-run
```

The triage report's **"Unmapped spec-table rows"** section lists source
rows the parser didn't recognise — that's the drift signal to watch when a
site changes its labels (the parser fails loud in the report instead of
silently dropping fields).

## Sandbox caveat

Claude remote sessions have registry-only egress (pypi/npm — everything
else 403s at the proxy), so live scrapes must run on a real machine or an
open-network environment. The toolkit's fetch layer, both real fetch tiers
(curl_cffi + local Chromium), parsing, validation, and the `import
--spec-json --dry-run` chain were all verified against a localhost fixture
server in-sandbox on July 19, 2026.

## Tests

`tests/test_scrapling_fetcher.py` — fetcher logic runs with zero network
and zero scrapling (injection seam), the parser is pinned on a committed
bikez fixture, and the CLI is driven end-to-end through a warm disk cache.
The robots.txt gate is covered by feeding robots bodies through the same
seam (disallow honoured, 5xx/429/transport-failure → complete disallow,
`Crawl-delay` honoured), and the substance gate is pinned from both sides:
the fixture passes it, while an empty page and a label-drifted page are
rejected as failures even though `validate_spec` accepts both.
