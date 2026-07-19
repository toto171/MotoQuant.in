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
3. **Politeness is not optional.** robots.txt is respected (protego),
   requests are rate-limited per domain (default 1.5 s), and raw HTML is
   disk-cached so re-parses never re-hit a site. The stealth tier is
   opt-in only.

## Install

```bash
pip install -r requirements-scrape.txt
```

Browser tier: needs a Chromium. On a dev machine `playwright install
chromium` once. In Claude sandboxes pass
`--browser-executable /opt/pw-browsers/chromium` (do NOT run
`playwright install`; the sandbox pin differs from scrapling's).

Stealth tier (Camoufox, ~700 MB download via `camoufox fetch`): operator
machines only, and only against hard anti-bot walls.

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

Escalation: a 403/429/503 or an anti-bot challenge page (Cloudflare
"just a moment" etc., even on HTTP 200) bumps the fetch to the next tier,
up to `--max-tier` (default `browser`; `stealth` never runs unless asked).

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
