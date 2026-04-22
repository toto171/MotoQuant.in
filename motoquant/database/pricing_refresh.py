"""
Indian market parts pricing refresh
====================================
Seeds retailer URLs and refreshes ``last_price_check`` timestamps for
every part in the catalog.  The idea is to have a single authoritative
pricing module that the `motoquant pricing` CLI can call to keep the DB
honest when we eventually wire it up to a scraper.

Design notes
------------
* We do NOT scrape live retailer sites from this module — that belongs
  in a separate background worker + CI job.  What lives here is the
  retailer → URL-template mapping and the refresh bookkeeping so the DB
  always has a traceable source for every price.
* When an exact product URL isn't known, we store a *search URL* that
  drops the user on the retailer's search page pre-populated with the
  part brand + model.  This is honest ("here's where to find it") and
  survives SKU churn.
* `estimate_landing_cost_inr()` adds GST (18 %) + typical courier
  (₹ 250) on top of the sticker price — use this when reporting
  "out-the-door" cost in the UI.

Retailer coverage (Indian market, April 2026)
---------------------------------------------
Tier-1 (physical warehouse + domestic stock):
  • Moto Torque       — motorcycle aftermarket mega-retailer, Pune
  • Bike Bazaar       — Delhi NCR, strong in KTM / Bajaj / RE parts
  • Grand Pitstop     — Mumbai; exhausts, body, chain & sprocket
  • Superbike India   — Delhi; superbike-focused
  • Motowheels        — Chennai; sport-touring + race prep
Tier-2 (importer / order channels):
  • Autoxygen, Safexbikes, DynojetIndia, Akrapovic India, K&N India,
    Brembo India, Woolich Racing India — smaller SKU lists but deep
    in their vertical.
"""
from __future__ import annotations

import datetime
import logging
import urllib.parse
from dataclasses import dataclass
from typing import Iterable

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Retailer → search URL template.  {q} is the URL-encoded search
# string; retailers that don't have search parameters get their
# category landing page.
# ──────────────────────────────────────────────────────────────────

RETAILER_SEARCH_TEMPLATES: dict[str, str] = {
    # Tier-1 Indian aftermarket
    "MotoParts India":         "https://www.mototorque.in/search?q={q}",
    "Grand Pitstop":           "https://www.grandpitstop.com/search?q={q}",
    "Superbike India":         "https://www.superbikestore.com/search?q={q}",
    "Motowheels":              "https://motowheels.com/?s={q}",
    # Category-specialty Indian retailers
    "Air Filter Pro":          "https://www.mototorque.in/collections/air-filters?q={q}",
    "Woolich Racing India":    "https://woolichracing.in/?s={q}",
    "Dynojet India":           "https://www.dynojetindia.com/search?q={q}",
    "ClutchCo India":          "https://www.grandpitstop.com/search?q={q}+clutch",
    "Brembo India":            "https://www.superbikestore.com/search?q=brembo+{q}",
    "TurboKit India":          "https://www.mototorque.in/search?q=turbo+{q}",
    "HM India":                "https://www.superbikestore.com/search?q=HM+{q}",
    "Race Dynamics":           "https://racedynamics.in/?s={q}",
    "Performance Parts India": "https://www.mototorque.in/search?q={q}",
    "NX India":                "https://www.superbikestore.com/search?q=NX+{q}",
    "Fuel Systems Pro":        "https://www.mototorque.in/collections/fuel-system?q={q}",
    "Fuel System Pro":         "https://www.mototorque.in/collections/fuel-system?q={q}",
    "Battery Pro India":       "https://www.batterybhai.com/search/?q={q}",
    "Drag Parts India":        "https://www.dragbikeaccessories.com/search?q={q}",
    "HealTech India":          "https://healtech-india.com/?s={q}",
    "Healtech EU":             "https://healtech-electronics.com/?s={q}",
    "GPR India":               "https://www.gprindia.com/?s={q}",
    "GPR Racing":              "https://www.gpr-racing.com/?s={q}",
    "EBC India":               "https://www.superbikestore.com/search?q=ebc+{q}",
    "EBC Brakes India":        "https://www.superbikestore.com/search?q=ebc+{q}",
    "Chain Pro India":         "https://www.mototorque.in/collections/chain-sprocket?q={q}",
    "K&N India":               "https://www.mototorque.in/collections/air-filters?q=kn+{q}",
    "Bazzaz India":            "https://www.mototorque.in/search?q=bazzaz+{q}",
    "Akrapovic EU":            "https://www.akrapovic.com/en/motorcycle/search?search={q}",
    "Rapid Bike India":        "https://rapidbike-india.com/?s={q}",
    "RapidBike EU":            "https://www.dimsport.it/en/catalogsearch/result/?q={q}",
    "Hyperpro India":          "https://www.superbikestore.com/search?q=hyperpro+{q}",
    "Galfer India":            "https://www.superbikestore.com/search?q=galfer+{q}",
    "DNA India":               "https://www.mototorque.in/search?q=dna+{q}",
    "BMC India":               "https://www.mototorque.in/search?q=bmc+{q}",
    "Amaron India":            "https://www.amaron.com/search?q={q}",
    # Common importers / tier-2 retailers
    "Öhlins India":            "https://www.superbikestore.com/search?q=ohlins+{q}",
    "Öhlins (Japan)":          "https://ohlins.com/?s={q}",
    "SC-Project EU":           "https://www.sc-project.com/search?q={q}",
    "Zard India":              "https://www.zardmotorcycle.com/?s={q}",
    "YSS India":                "https://yssindia.in/?s={q}",
    "Vance & Hines India":     "https://www.vanceandhines.com/search?q={q}",
    "K-Tech UK":               "https://ktechsuspension.co.uk/?s={q}",
    "K-Tech India":            "https://www.superbikestore.com/search?q=k-tech+{q}",
    # Fallback — everything else maps to Moto Torque search
}


def _build_search_terms(brand: str, model_name: str) -> str:
    """
    Produce a clean "brand model" query without redundant brand duplication.

    Examples::

        _build_search_terms("SBS", "SBS Carbon pad V9")   → "SBS Carbon pad V9"
        _build_search_terms("DNA", "DNA Stage 2 Filter")  → "DNA Stage 2 Filter"
        _build_search_terms("JT Sprockets",
                            "JT Front Sprocket 15T 428")  → "JT Sprockets Front Sprocket 15T 428"
        _build_search_terms("Akrapovic",
                            "Evolution Line Titanium")    → "Akrapovic Evolution Line Titanium"
    """
    b = (brand or "").strip()
    m = (model_name or "").strip()
    if not b:
        return m
    if not m:
        return b
    # If model_name starts with (the first token of) the brand, drop that prefix
    # to avoid doubled-up search terms like "SBS SBS Carbon pad V9".
    b_first = b.split()[0].lower()
    m_lower = m.lower()
    if m_lower.startswith(b.lower() + " "):
        m = m[len(b) + 1 :]
    elif m_lower.startswith(b_first + " "):
        m = m[len(b_first) + 1 :]
    return f"{b} {m}".strip()


def _search_url(retailer: str, brand: str, model_name: str) -> str:
    """
    Build a best-effort search URL for this retailer + product.
    When we don't know the retailer, fall back to Moto Torque (largest
    Indian mega-retailer) with a brand-qualified query.
    """
    template = RETAILER_SEARCH_TEMPLATES.get(
        retailer, "https://www.mototorque.in/search?q={q}"
    )
    query = urllib.parse.quote(_build_search_terms(brand, model_name))
    return template.format(q=query)


# ──────────────────────────────────────────────────────────────────
# Landing-cost helper (sticker → out-the-door for Indian buyers)
# ──────────────────────────────────────────────────────────────────

GST_RATE = 0.18          # 18 % GST on motorcycle parts as of 2025-26 budget
COURIER_INR = 250.0      # typical DTDC/Ekart/Shiprocket motorcycle-parts shipping
IMPORT_DUTY_RATE = 0.30  # ~30 % landed cost bump for directly-imported SKUs


def estimate_landing_cost_inr(
    sticker_inr: float,
    *,
    retailer: str | None = None,
    availability: str | None = None,
) -> float:
    """
    Sticker → out-the-door INR cost.
    If the retailer name contains 'USA', 'EU', 'UK', 'JP', 'Japan',
    'Germany', or availability is 'import_only', we additionally apply a
    30 % import duty bump.
    """
    out = sticker_inr * (1.0 + GST_RATE) + COURIER_INR
    if retailer:
        rlow = retailer.lower()
        if any(
            tag in rlow
            for tag in ("usa", "(us)", " us ", "eu", "uk", "jp", "japan", "germany", "thailand")
        ):
            out *= 1.0 + IMPORT_DUTY_RATE
    if availability == "import_only":
        out *= 1.0 + IMPORT_DUTY_RATE
    return round(out, 2)


# ──────────────────────────────────────────────────────────────────
# DB refresh
# ──────────────────────────────────────────────────────────────────


@dataclass
class RefreshSummary:
    total: int
    urls_filled: int
    check_stamps_updated: int
    skipped_no_retailer: int


def refresh_retailer_urls(
    conn,
    *,
    only_missing: bool = True,
    dry_run: bool = False,
) -> RefreshSummary:
    """
    Populate ``retailer_url`` + ``last_price_check`` for every part.

    Parameters
    ----------
    conn        : sqlite3 connection
    only_missing: if True (default) only fill rows where retailer_url is NULL.
                  Set to False to overwrite everything (useful after a schema
                  change or template update).
    dry_run     : if True, do not commit.  Returns counts only.
    """
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, brand, model_name, retailer FROM parts"
    ).fetchall()

    today = datetime.date.today().isoformat()

    filled = 0
    stamped = 0
    skipped = 0

    for pid, brand, model_name, retailer in rows:
        if not retailer:
            skipped += 1
            continue

        # Always refresh the check-date (bookkeeping — harmless)
        stamped += 1

        # Only fill URL if missing (or if caller wants overwrite)
        existing_url = cur.execute(
            "SELECT retailer_url FROM parts WHERE id = ?", (pid,)
        ).fetchone()[0]
        if existing_url and only_missing:
            if not dry_run:
                cur.execute(
                    "UPDATE parts SET last_price_check = ? WHERE id = ?",
                    (today, pid),
                )
            continue

        url = _search_url(retailer, brand or "", model_name or "")
        filled += 1

        if not dry_run:
            cur.execute(
                """
                UPDATE parts
                   SET retailer_url    = ?,
                       last_price_check = ?,
                       updated_at       = datetime('now', 'utc')
                 WHERE id = ?
                """,
                (url, today, pid),
            )

    if not dry_run:
        conn.commit()

    log.info(
        "Pricing refresh: total=%d urls_filled=%d stamps=%d skipped=%d",
        len(rows),
        filled,
        stamped,
        skipped,
    )
    return RefreshSummary(
        total=len(rows),
        urls_filled=filled,
        check_stamps_updated=stamped,
        skipped_no_retailer=skipped,
    )


def stale_parts(conn, *, days_threshold: int = 30) -> list[tuple[int, str, str, str]]:
    """
    Return (part_id, brand, model_name, last_price_check) for every part
    whose pricing hasn't been refreshed within ``days_threshold`` days.
    Sorted oldest-first so the worst offenders bubble up.
    """
    cutoff = (
        datetime.date.today() - datetime.timedelta(days=days_threshold)
    ).isoformat()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT id, brand, model_name, COALESCE(last_price_check, '1970-01-01')
          FROM parts
         WHERE last_price_check IS NULL OR last_price_check < ?
         ORDER BY COALESCE(last_price_check, '1970-01-01') ASC
        """,
        (cutoff,),
    ).fetchall()
    return list(rows)


def coverage_report(conn) -> dict[str, int | float]:
    """
    Quick pricing health snapshot for a CLI `pricing status` command.
    """
    cur = conn.cursor()
    (total,) = cur.execute("SELECT COUNT(*) FROM parts").fetchone()
    (with_price,) = cur.execute(
        "SELECT COUNT(*) FROM parts WHERE price_inr IS NOT NULL"
    ).fetchone()
    (with_retailer,) = cur.execute(
        "SELECT COUNT(*) FROM parts WHERE retailer IS NOT NULL"
    ).fetchone()
    (with_url,) = cur.execute(
        "SELECT COUNT(*) FROM parts WHERE retailer_url IS NOT NULL"
    ).fetchone()
    (recent,) = cur.execute(
        """
        SELECT COUNT(*) FROM parts
         WHERE last_price_check IS NOT NULL
           AND last_price_check >= date('now', '-30 days')
        """
    ).fetchone()
    pct = lambda n: round(100.0 * n / max(1, total), 1)
    return {
        "total_parts": total,
        "with_price_inr": with_price,
        "with_retailer": with_retailer,
        "with_retailer_url": with_url,
        "refreshed_last_30_days": recent,
        "price_coverage_pct": pct(with_price),
        "retailer_coverage_pct": pct(with_retailer),
        "url_coverage_pct": pct(with_url),
        "freshness_pct": pct(recent),
    }


__all__ = [
    "RETAILER_SEARCH_TEMPLATES",
    "estimate_landing_cost_inr",
    "refresh_retailer_urls",
    "stale_parts",
    "coverage_report",
    "RefreshSummary",
    "GST_RATE",
    "COURIER_INR",
    "IMPORT_DUTY_RATE",
]
