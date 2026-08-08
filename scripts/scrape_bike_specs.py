#!/usr/bin/env python3
"""
Scrapling-backed bike-spec scraper (dev-side toolkit).

Fetches motorcycle detail pages (bikez.com format) through the polite
three-tier fetch layer in ``motoquant/scraper/fetcher.py``, parses them
with the SAME stdlib parser the legacy crawler used
(``bikez.parse_bikez_detail`` — one source of parsing truth), validates
every spec with ``validator.validate_spec``, and emits:

  1. an import-ready JSON list for
     ``python -m motoquant.run import --spec-json OUT --dry-run``
  2. a markdown triage report: per-bike validation status, fetch-tier
     stats, and any spec-table rows the parser did NOT map (so silent
     label drift on the source site is visible, not swallowed).

Two gates stand between a fetched page and the import-ready JSON:

  * the **substance gate** (``page_parse_failures``) — the spec table must
    actually have parsed (displacement + power + >= MIN_MAPPED_ROWS mapped
    rows). Identity alone is not evidence: manufacturer/model/year come
    from the URL slug, so a 404 body or a drifted layout would otherwise
    validate clean. Pages that fail this are reported as FAILURES.
  * the **validator gate** (``validate_spec``) — physical bounds.

Exit codes: 0 = specs accepted and nothing failed, 1 = nothing accepted,
2 = specs accepted but some pages failed to fetch/parse (read the report).

Scraped specs are UNVERIFIED data. The honest-data contract applies: an
operator (or session) must adjudicate the triage report BEFORE importing —
nothing here writes to motoquant.db.

Install deps:  pip install -r requirements-scrape.txt
This tooling must never become a production (requirements-api.txt) dep.

Examples:
    # Explicit detail pages
    python scripts/scrape_bike_specs.py \
        --urls https://bikez.com/motorcycles/suzuki_gsx-r_1000_2005.php \
        --out reports/scraped_specs.json

    # Crawl a manufacturer listing (gap-fill), 20 bikes, 400cc floor
    python scripts/scrape_bike_specs.py --manufacturer Suzuki --limit 20 \
        --min-cc 400 --max-tier browser

Sandbox note: Claude remote sessions have registry-only egress — run live
scrapes from a real machine (or an open-network environment). The disk
cache (--cache-dir) makes re-parses free afterwards.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant.scraper.bikez import (  # noqa: E402
    BASE_URL,
    FIELD_MAP,
    _find_links_matching,
    _parse_table_rows,
    parse_bikez_detail,
)
from motoquant.scraper.fetcher import (  # noqa: E402
    TIER_ORDER,
    FetchPolicy,
    FetchResult,
    PoliteFetcher,
    RobotsDisallowedError,
)
from motoquant.scraper.validator import validate_spec  # noqa: E402

# BikeSpec fields worth exporting for `import --spec-json` (identity +
# physics-relevant numerics + provenance). raw_data / field_confidence /
# scraped_at are deliberately excluded — spec_from_dict re-stamps those.
EXPORT_FIELDS = (
    "manufacturer",
    "model_name",
    "year_from",
    "year_to",
    "category",
    "displacement_cc",
    "bore_mm",
    "stroke_mm",
    "compression_ratio",
    "peak_power_hp",
    "peak_power_rpm",
    "peak_torque_nm",
    "peak_torque_rpm",
    "fuel_system",
    "cooling",
    "valve_config",
    "cylinders",
    "gears",
    "final_drive",
    "dry_mass_kg",
    "wet_mass_kg",
    "wheelbase_mm",
    "seat_height_mm",
    "fuel_capacity_l",
    "front_tire_size",
    "rear_tire_size",
    "source_name",
    "source_url",
)

DETAIL_PAGE_RE = re.compile(r"\d{4}\.php$")

# ── Page-substance gate (the validator alone is NOT a gate) ──────────────
# parse_bikez_detail always synthesises manufacturer/model/year from the
# URL slug, and validate_spec only requires those two to be non-empty. So
# a 404 body, a JS shell, or a page whose table labels drifted would sail
# through as a "validator-clean", import-ready spec WITH a clean drift
# signal — the exact inversion of this tool's purpose. A page therefore
# has to prove it actually parsed before its spec can be exported.
MIN_MAPPED_ROWS = 6
# (spec attribute, source row label) pairs that must come FROM THE PAGE.
REQUIRED_PAGE_FIELDS = (
    ("displacement_cc", "Displacement"),
    ("peak_power_hp", "Power"),
)

# Reject kinds that mean "something is wrong with the fetch or the site",
# as opposed to "this bike was deliberately filtered out".
FAILURE_KINDS = ("fetch", "robots", "drift")


def page_parse_failures(spec, html: str) -> list[str]:
    """Reasons the PAGE itself yielded too little to trust the spec.

    Empty list → the spec table really parsed. Anything else must be
    reported as a fetch/drift failure, never as a clean spec.
    """
    rows = _parse_table_rows(html)
    mapped = len(getattr(spec, "raw_data", None) or {})
    failures: list[str] = []
    if mapped < MIN_MAPPED_ROWS:
        if not rows:
            failures.append(
                f"no spec table found (0 rows, {len(html)} bytes) — error page, "
                "JS shell, or a layout change"
            )
        else:
            failures.append(
                f"{len(rows)} table row(s) on the page but only {mapped} mapped "
                f"(need >= {MIN_MAPPED_ROWS}) — likely label drift"
            )
    for attr, label in REQUIRED_PAGE_FIELDS:
        if getattr(spec, attr, None) is None:
            failures.append(f"no '{label}' row parsed ({attr} missing)")
    return failures


def spec_to_export_dict(spec) -> dict:
    """Non-None EXPORT_FIELDS of a BikeSpec as a plain importable dict."""
    out = {}
    for name in EXPORT_FIELDS:
        value = getattr(spec, name, None)
        if value is not None and value != "":
            out[name] = value
    return out


def unmapped_rows(html: str) -> list[str]:
    """Spec-table row labels the bikez FIELD_MAP does not recognise.

    Mirrors the parser's matching rule (exact key, else case-insensitive
    substring) so the triage report surfaces real drift on the source
    site instead of the parser silently dropping renamed rows.
    """
    rows = _parse_table_rows(html)
    known = [k.lower() for k in FIELD_MAP]
    missed = []
    for key in rows:
        low = key.lower()
        if low in known or any(k in low for k in known):
            continue
        missed.append(key)
    return missed


def discover_detail_urls(
    fetcher: PoliteFetcher, manufacturer: str, limit: int
) -> list[str]:
    """Crawl a bikez manufacturer listing page for detail-page URLs."""
    slug = manufacturer.lower().replace(" ", "_")
    listing_url = f"{BASE_URL}/motorcycles/{slug}_motorcycles.php"
    result = fetcher.fetch(listing_url)
    if not result.ok:
        print(f"  !! listing page unusable ({result.failure_reason()}): {listing_url}")
        return []
    links = _find_links_matching(
        result.html, r"/motorcycles/" + slug + r"[_-].+\.php", BASE_URL
    )
    detail = [u for u in links if DETAIL_PAGE_RE.search(u)]
    return detail[:limit]


def run_scrape(
    fetcher: PoliteFetcher,
    urls: list[str],
    min_cc: float,
) -> tuple[list[dict], list[dict]]:
    """Fetch+parse+validate every URL. Returns (accepted, rejected) rows.

    Each row: {url, spec, validation, unmapped, tier, from_cache, kind} for
    the report; accepted rows also carry the import-ready "export" dict.
    ``kind`` is one of fetch / robots / drift (things that need
    investigating) or filter / invalid (things that were legitimately
    turned away).
    """
    accepted: list[dict] = []
    rejected: list[dict] = []
    for url in urls:
        try:
            result: FetchResult = fetcher.fetch(url)
        except RobotsDisallowedError as exc:
            rejected.append(
                {"url": url, "kind": "robots", "reason": f"robots.txt: {exc}"}
            )
            print(f"  -- robots disallow: {url}")
            continue
        except Exception as exc:
            rejected.append(
                {"url": url, "kind": "fetch", "reason": f"fetch failed: {exc}"}
            )
            print(f"  !! fetch failed: {url} — {exc}")
            continue
        if not result.ok:
            reason = result.failure_reason()
            rejected.append({"url": url, "kind": "fetch", "reason": reason})
            print(f"  !! {reason}: {url}")
            continue

        spec = parse_bikez_detail(result.html, url)
        row = {
            "url": url,
            "spec": spec,
            "unmapped": unmapped_rows(result.html),
            "tier": result.tier,
            "from_cache": result.from_cache,
        }

        # The substance gate runs BEFORE the validator so a page that never
        # parsed can never be reported as validator-clean.
        drift = page_parse_failures(spec, result.html)
        if drift:
            row["kind"] = "drift"
            row["reason"] = "; ".join(drift)
            rejected.append(row)
            print(f"  !! did not parse: {url} — {row['reason']}")
            continue

        if min_cc and spec.displacement_cc and spec.displacement_cc < min_cc:
            row["kind"] = "filter"
            row["reason"] = f"below --min-cc ({spec.displacement_cc:.0f}cc)"
            rejected.append(row)
            continue

        validation = validate_spec(spec)
        row["validation"] = validation
        if validation.is_valid:
            row["export"] = spec_to_export_dict(spec)
            accepted.append(row)
            print(
                f"  ok {spec.manufacturer} {spec.model_name} "
                f"({spec.year_from or '?'}) — {spec.displacement_cc or '?'}cc "
                f"{spec.peak_power_hp or 0:.0f}hp  [{result.tier}"
                f"{', cache' if result.from_cache else ''}]"
            )
        else:
            row["kind"] = "invalid"
            row["reason"] = "; ".join(validation.errors) or "validation failed"
            rejected.append(row)
            print(f"  -- invalid: {url} — {row['reason']}")
    return accepted, rejected


def write_report(
    path: Path,
    accepted: list[dict],
    rejected: list[dict],
    fetcher: PoliteFetcher,
    out_json: Path,
) -> None:
    failures = [r for r in rejected if r.get("kind") in FAILURE_KINDS]
    skipped = [r for r in rejected if r.get("kind") not in FAILURE_KINDS]
    lines = [
        "# Scrape triage report",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
        f"by scripts/scrape_bike_specs.py",
        "",
        f"- Accepted (parsed **and** validator-clean): **{len(accepted)}** "
        f"→ `{out_json}`",
        f"- Fetch / parse failures (investigate): **{len(failures)}**",
        f"- Skipped or invalid: **{len(skipped)}**",
        f"- Fetch stats: {fetcher.stats}",
        "",
        "> Scraped specs are **UNVERIFIED**. Adjudicate below, then dry-run:",
        f"> `python -m motoquant.run --db /tmp/scrape-check.db import "
        f"--spec-json {out_json} --dry-run`",
        "",
        "## Accepted",
        "",
        "| Bike | Year | cc | hp | kg | Tier | Warnings |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in accepted:
        s = row["spec"]
        v = row["validation"]
        warns = "; ".join(v.warnings) if v.warnings else "—"
        lines.append(
            f"| {s.manufacturer} {s.model_name} | {s.year_from or '?'} "
            f"| {s.displacement_cc or '?'} | {s.peak_power_hp or '?'} "
            f"| {s.dry_mass_kg or s.wet_mass_kg or '?'} | {row['tier']} | {warns} |"
        )
    lines += [
        "",
        "## Fetch / parse failures — INVESTIGATE",
        "",
        "> A page that did not parse is never exported. These are blocked "
        "fetches, HTTP errors, robots refusals, and pages whose spec table "
        "was missing or unrecognised (site-layout drift).",
        "",
    ]
    if failures:
        for row in failures:
            lines.append(
                f"- [{row.get('kind', '?')}] {row['url']} — "
                f"{row.get('reason', 'unknown')}"
            )
    else:
        lines.append("(none)")

    lines += ["", "## Skipped / invalid", ""]
    if skipped:
        for row in skipped:
            lines.append(
                f"- [{row.get('kind', '?')}] {row['url']} — "
                f"{row.get('reason', 'unknown')}"
            )
    else:
        lines.append("(none)")

    all_unmapped: dict[str, int] = {}
    for row in accepted + rejected:
        for key in row.get("unmapped", []):
            all_unmapped[key] = all_unmapped.get(key, 0) + 1
    lines += [
        "",
        "## Unmapped spec-table rows (parser drift signal)",
        "",
    ]
    if all_unmapped:
        for key, n in sorted(all_unmapped.items(), key=lambda kv: -kv[1]):
            lines.append(f"- `{key}` × {n}")
    elif failures:
        lines.append(
            "(no unmapped rows — but see the failures above; a page that "
            "returned nothing to parse also reports nothing here)"
        )
    else:
        lines.append("(none — every row mapped)")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrapling-backed bike-spec scraper (dev-side toolkit)"
    )
    src = parser.add_argument_group("sources (one required)")
    src.add_argument("--urls", nargs="+", help="Explicit detail-page URLs")
    src.add_argument("--url-file", help="File with one detail-page URL per line")
    src.add_argument("--manufacturer", help="Crawl a bikez manufacturer listing")
    parser.add_argument("--limit", type=int, default=25, help="Max detail pages")
    parser.add_argument("--min-cc", type=float, default=0.0, help="Displacement floor")
    stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    parser.add_argument("--out", default=f"reports/scraped_specs_{stamp}.json")
    parser.add_argument("--report", default=f"reports/scrape_triage_{stamp}.md")
    parser.add_argument("--cache-dir", default="scrape_cache")
    parser.add_argument("--rate-limit", type=float, default=1.5)
    parser.add_argument("--max-tier", choices=TIER_ORDER, default="browser")
    parser.add_argument("--browser-executable", default=None)
    parser.add_argument(
        "--refresh", action="store_true", help="Bypass cache reads (still writes)"
    )
    args = parser.parse_args(argv)

    if not (args.urls or args.url_file or args.manufacturer):
        parser.error("specify --urls, --url-file, or --manufacturer")

    policy = FetchPolicy(
        rate_limit_s=args.rate_limit,
        max_tier=args.max_tier,
        cache_dir=Path(args.cache_dir),
        refresh=args.refresh,
        browser_executable=args.browser_executable,
    )
    fetcher = PoliteFetcher(policy)

    urls: list[str] = []
    if args.urls:
        urls += args.urls
    if args.url_file:
        urls += [
            line.strip()
            for line in Path(args.url_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    if args.manufacturer:
        print(f"Discovering {args.manufacturer} detail pages…")
        urls += discover_detail_urls(fetcher, args.manufacturer, args.limit)
    urls = list(dict.fromkeys(urls))[: args.limit]
    if not urls:
        print("No URLs to scrape.")
        return 1

    print(f"Scraping {len(urls)} page(s) [max tier: {args.max_tier}]…")
    accepted, rejected = run_scrape(fetcher, urls, args.min_cc)

    out_json = Path(args.out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps([row["export"] for row in accepted], indent=2), encoding="utf-8"
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(report_path, accepted, rejected, fetcher, out_json)

    failures = [r for r in rejected if r.get("kind") in FAILURE_KINDS]
    print(
        f"\nDone: {len(accepted)} accepted / {len(failures)} fetch-parse "
        f"failures / {len(rejected) - len(failures)} skipped."
        f"\n  specs  → {out_json}\n  triage → {report_path}"
        f"\nNext: adjudicate the triage report, then dry-run the import."
    )
    if not accepted:
        return 1
    if failures:
        print(
            "WARNING: some pages did not fetch or did not parse — see the "
            "'Fetch / parse failures' section before trusting this run."
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
