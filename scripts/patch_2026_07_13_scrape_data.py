#!/usr/bin/env python3
"""
MotoQuant — web-scrape data application patch (2026-07-13).

Applies the July-10, 2026 full-catalog web-scrape findings
(``reports/scrape_2026_07_10/{parts,tires}_web_data.json`` — a 51-agent
fan-out that was READ-ONLY at collection time per its own SCRAPE_REPORT.md;
nothing in the DB, seed sources, or physics was touched until now) to the
parts and tires catalogs. Six independent, idempotent actions:

  1. INR reprice — every part with a confirmed India-retail INR price and a
     live http(s) source_url (and found != false) gets price_inr stamped
     from the web value, plus retailer / retailer_url refreshed from the
     JSON's retailer / source_url, plus last_price_check = 2026-07-13.
     (~72 rows, per SCRAPE_REPORT.md "72 INR India-retail".)

  2. USD-only reprice — parts priced only in USD (price_inr null) get
     converted through the project's own landed-cost helper,
     motoquant.database.pricing_refresh.estimate_landing_cost_inr (GST 18%
     + courier ₹250 + a 30% import-duty bump where the retailer string or
     availability implies an overseas source). That helper expects an INR
     *sticker* price, not USD, so USD is first converted at the documented
     approximate USD_TO_INR_RATE (see constant below) — this is an offline
     patch with no live FX feed, so the rate is a fixed, commented
     approximation, not a live quote. price_inr + price_usd +
     last_price_check are stamped the same way as action 1.
     (~210 of the 217 "USD-only" rows per SCRAPE_REPORT.md — 7 are
     hard-excluded, see EXCLUDE_USD_REPRICE_IDS.)

  3. Discontinued parts — 6 Bazzaz / AEM engine-management SKUs the
     manufacturers pulled from sale (Jan 2022 / May 2023, per the scrape
     notes) get availability = 'discontinued'. That is an EXISTING,
     documented value in the parts.availability column comment
     ("in_stock / order / import_only / discontinued") — not a new word.

  4. Fictional-brand honesty renames — ClutchCo / Regina Pro / Sprocket
     Specialists are not real motorcycle-parts brands (every SKU under
     them carries sku_exists='low' in the scrape; SCRAPE_REPORT.md flags
     all three by name as "fully fictional brands"). Per the July-6
     P183/P194/P195/P501 precedent in
     scripts/patch_2026_07_06_catalog_integrity.py, rename to honest,
     descriptive class names. UNLIKE that precedent (real brands — Leo
     Vince / S&S / Two Brothers / JT Sprockets — where only a
     bike-specific model_name was misleading), these three brands are
     themselves fictional, so brand is rewritten to 'Generic' too.
     fitment_rules / param_overrides / param_deltas / param_multipliers
     are left completely untouched — only the label was fictional, not the
     compatibility rule or the physics delta. KNOWN TRADE-OFF (deliberately
     not fixed here, out of scope): each part's fitment_rules.description
     JSON string still says e.g. "ClutchCo Kevlar Pro clutch kit for..." —
     cosmetic staleness in a field this patch is instructed not to touch.
     The mapping table is hardcoded (not generated at runtime) so it is
     reviewable in a diff and trivially idempotent.

  5. Tire family status — families the scrape marked 'discontinued' or
     'not_found' (24 families / 48 rows) get available_india = 0 and an
     audit-trail suffix appended to data_source. Rows are NEVER deleted or
     renamed — historical bike_tire_fitments rows reference them.

  6. Tire prices — conservative price_inr application from each family's
     scraped 'prices' list. A price point only applies to a specific row
     when the mapping is unambiguous: either the family has exactly one
     tire_ids row, or the price's 'size' field — run through the SAME
     TireRepository.normalize_size_designation used by the July-6
     tire-dedup fix — matches exactly one row in a multi-row family. On
     top of that row-mapping test, if more than one price point maps to
     the same row and they DISAGREE on the number, that is treated as
     ambiguous too (multiple retailers quoting different prices for one
     tire is not something this patch resolves by picking one arbitrarily)
     and the row is skipped. Reports applied vs skipped counts, split by
     skip reason.

Idempotent: every change is expressed as target state; a second run
reports 0 changes. Run from repo root:

    python3 scripts/patch_2026_07_13_scrape_data.py
    MOTOQUANT_DB=/path/to.db python3 scripts/patch_2026_07_13_scrape_data.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motoquant.database.pricing_refresh import estimate_landing_cost_inr  # noqa: E402
from motoquant.database.tire_repo import TireRepository  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PARTS_JSON = REPO_ROOT / "reports" / "scrape_2026_07_10" / "parts_web_data.json"
TIRES_JSON = REPO_ROOT / "reports" / "scrape_2026_07_10" / "tires_web_data.json"

PATCH_DATE = "2026-07-13"

# Documented approximate USD->INR rate for the landed-cost conversion (see
# action 2 in the module docstring). This is the same order-of-magnitude
# rate CLAUDE.md's April-30-2026 pricing-refresh entry documents ("USD x
# 84"), and is corroborated by the scrape's own USD-vs-INR notes (e.g. part
# 178's notes quote "$77-94 USD (~Rs6,400-7,800)", an implied ~83 rate).
# Not a live FX quote — this patch has no network access at run time.
USD_TO_INR_RATE = 84.0

# ────────────────────────────────────────────────────────────────────
# Action 2 hard exclusions. All 7 already fail the `found is not False` /
# http-source_url gates as of the 2026-07-10 scrape data, so this list is
# currently redundant with those gates — it is kept explicit anyway as
# defense-in-depth documentation: if a future re-scrape flips `found` back
# to true or fills in a source_url for one of these unconfirmed-SKU rows,
# the exclusion still holds until a human re-verifies the specific match.
# ────────────────────────────────────────────────────────────────────
EXCLUDE_USD_REPRICE_IDS = {
    140,  # Kraftwerks C-1 Supercharger Kit — no "C-1" SKU found (found=false)
    262,  # K-Tech 25IDS Cartridge Kit Indian 200-400 — quoted price is for
    #      an unrelated western fitment, not this Indian-market SKU (found=false)
    309,  # SC-Project CR-M Full System Norden 901 — price is for the real
    #      "Rally Raid" line, not a confirmed "CR-M" product (found=false)
    470,  # SC-Project CR-M Full Yamaha YZF-R1 — no "CR-M" R1 variant found
    #      in SC-Project's real lineup (CR-T / SC1-R) (found=false)
    477,  # S&S Cycle Slip-On Low Rider ST — no exact-SKU match; price is a
    #      generic Softail slip-on, not the Low Rider ST fitment (found=false)
    506,  # Aracer RC Mini ECU Remap YZF-R1 — the "RC Mini" line only exists
    #      for small-displacement bikes, not the R1 (found=false)
    368,  # Galfer DF Wave Rotor Front Pair — no source_url at all (found=true
    #      but source_url is null, so it also fails the http-source gate)
}

# ────────────────────────────────────────────────────────────────────
# Action 3: parts the manufacturer has discontinued (per scrape notes).
# ────────────────────────────────────────────────────────────────────
DISCONTINUED_PART_IDS = [51, 95, 116, 146, 407, 504]

# ────────────────────────────────────────────────────────────────────
# Action 4: fictional-brand -> honest-class-name mapping (deterministic,
# reviewable, NOT generated at runtime). Displacement bands for the
# ClutchCo kits are lifted verbatim from each row's own fitment_rules
# (banded by the July-6 patch); sprocket pitch/tooth-count/position come
# from the existing model_name. fitment_rules are NOT touched.
# ────────────────────────────────────────────────────────────────────
FICTIONAL_BRAND_RENAMES: list[dict] = [
    # ClutchCo (8 SKUs, sku_exists='low' on every row; fitment_rules bands
    # were already fixed by scripts/patch_2026_07_06_catalog_integrity.py —
    # this patch only relabels the fictional brand/name, bands are unchanged)
    {
        "id": 129,
        "old_brand": "ClutchCo",
        "old_name": "Kevlar Pro Kit",
        "new_brand": "Generic",
        "new_name": "Kevlar Pro Clutch Kit (750-1100cc)",
    },
    {
        "id": 130,
        "old_brand": "ClutchCo",
        "old_name": "Carbon Race Kit",
        "new_brand": "Generic",
        "new_name": "Carbon Race Clutch Kit (1100cc+)",
    },
    {
        "id": 131,
        "old_brand": "ClutchCo",
        "old_name": "Organic Street Kit",
        "new_brand": "Generic",
        "new_name": "Organic Street Clutch Kit (250-500cc)",
    },
    {
        "id": 132,
        "old_brand": "ClutchCo",
        "old_name": "Sintered Sport Kit",
        "new_brand": "Generic",
        "new_name": "Sintered Sport Clutch Kit (500-750cc)",
    },
    {
        "id": 133,
        "old_brand": "ClutchCo",
        "old_name": "Heavy Duty Steel Kit",
        "new_brand": "Generic",
        "new_name": "Heavy Duty Steel Clutch Kit (500-750cc)",
    },
    {
        "id": 134,
        "old_brand": "ClutchCo",
        "old_name": "Race Ceramic Kit",
        "new_brand": "Generic",
        "new_name": "Race Ceramic Clutch Kit (1100cc+)",
    },
    {
        "id": 135,
        "old_brand": "ClutchCo",
        "old_name": "Premium Organic Kit",
        "new_brand": "Generic",
        "new_name": "Premium Organic Clutch Kit (250-500cc)",
    },
    {
        "id": 136,
        "old_brand": "ClutchCo",
        "old_name": "Ultra Slippery Kit",
        "new_brand": "Generic",
        "new_name": "Ultra Slippery Clutch Kit (750-1100cc)",
    },
    # Regina Pro (9 SKUs) — the "Pro" suffix was the fictional-prestige
    # flourish; pitch + position + tooth-count (the actual spec info) is
    # preserved verbatim.
    {
        "id": 266,
        "old_brand": "Regina Pro",
        "old_name": "520 Front Sprocket 13T Pro",
        "new_brand": "Generic",
        "new_name": "520 Front Sprocket 13T",
    },
    {
        "id": 267,
        "old_brand": "Regina Pro",
        "old_name": "525 Front Sprocket 13T Pro",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 13T",
    },
    {
        "id": 268,
        "old_brand": "Regina Pro",
        "old_name": "530 Front Sprocket 13T Pro",
        "new_brand": "Generic",
        "new_name": "530 Front Sprocket 13T",
    },
    {
        "id": 269,
        "old_brand": "Regina Pro",
        "old_name": "520 Front Sprocket 14T Pro",
        "new_brand": "Generic",
        "new_name": "520 Front Sprocket 14T",
    },
    {
        "id": 270,
        "old_brand": "Regina Pro",
        "old_name": "525 Front Sprocket 14T Pro",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 14T",
    },
    {
        "id": 271,
        "old_brand": "Regina Pro",
        "old_name": "530 Front Sprocket 14T Pro",
        "new_brand": "Generic",
        "new_name": "530 Front Sprocket 14T",
    },
    {
        "id": 272,
        "old_brand": "Regina Pro",
        "old_name": "520 Front Sprocket 15T Pro",
        "new_brand": "Generic",
        "new_name": "520 Front Sprocket 15T",
    },
    {
        "id": 273,
        "old_brand": "Regina Pro",
        "old_name": "525 Front Sprocket 15T Pro",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 15T",
    },
    {
        "id": 274,
        "old_brand": "Regina Pro",
        "old_name": "530 Front Sprocket 15T Pro",
        "new_brand": "Generic",
        "new_name": "530 Front Sprocket 15T",
    },
    # Sprocket Specialists (8 SKUs) — the model_name was already a plain
    # descriptive spec string with no fictional flourish; only the brand
    # changes.
    {
        "id": 5,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Front Sprocket 16T",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 16T",
    },
    {
        "id": 6,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Front Sprocket 17T",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 17T",
    },
    {
        "id": 7,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Front Sprocket 18T",
        "new_brand": "Generic",
        "new_name": "525 Front Sprocket 18T",
    },
    {
        "id": 20,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Rear Sprocket 42T",
        "new_brand": "Generic",
        "new_name": "525 Rear Sprocket 42T",
    },
    {
        "id": 21,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Rear Sprocket 44T",
        "new_brand": "Generic",
        "new_name": "525 Rear Sprocket 44T",
    },
    {
        "id": 22,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Rear Sprocket 46T",
        "new_brand": "Generic",
        "new_name": "525 Rear Sprocket 46T",
    },
    {
        "id": 23,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Rear Sprocket 48T",
        "new_brand": "Generic",
        "new_name": "525 Rear Sprocket 48T",
    },
    {
        "id": 24,
        "old_brand": "Sprocket Specialists",
        "old_name": "525 Rear Sprocket 50T",
        "new_brand": "Generic",
        "new_name": "525 Rear Sprocket 50T",
    },
]

_DISCONTINUED_TAG_FMT = "; scrape 2026-07-10: discontinued, successor: {successor}"
_NOT_FOUND_TAG = "; scrape 2026-07-10: not found as named"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_http(url) -> bool:
    return isinstance(url, str) and url.startswith("http")


# ────────────────────────────────────────────────────────────────────
# Action 1 — INR reprice
# ────────────────────────────────────────────────────────────────────
def _apply_inr_reprice(conn: sqlite3.Connection, parts: list[dict]) -> dict:
    changed = 0
    noop = 0
    problems: list[str] = []
    for p in parts:
        if p.get("price_inr") is None or not _is_http(p.get("source_url")):
            continue
        if p.get("found") is False:
            continue

        row = conn.execute(
            "SELECT id, price_inr, retailer, retailer_url, last_price_check "
            "FROM parts WHERE id = ?",
            (p["id"],),
        ).fetchone()
        if row is None:
            problems.append(f"part {p['id']}: not found in DB — skipped")
            continue

        target_price = round(float(p["price_inr"]), 2)
        target_retailer = p.get("retailer") or row["retailer"]
        target_retailer_url = p["source_url"]

        updates: dict[str, object] = {}
        if (
            row["price_inr"] is None
            or round(float(row["price_inr"]), 2) != target_price
        ):
            updates["price_inr"] = target_price
        if target_retailer and row["retailer"] != target_retailer:
            updates["retailer"] = target_retailer
        if row["retailer_url"] != target_retailer_url:
            updates["retailer_url"] = target_retailer_url
        if row["last_price_check"] != PATCH_DATE:
            updates["last_price_check"] = PATCH_DATE

        if not updates:
            noop += 1
            continue

        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE parts SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*updates.values(), p["id"]),
        )
        changed += 1
    return {"changed": changed, "noop": noop, "problems": problems}


# ────────────────────────────────────────────────────────────────────
# Action 2 — USD-only reprice via the landed-cost helper
# ────────────────────────────────────────────────────────────────────
def _apply_usd_reprice(conn: sqlite3.Connection, parts: list[dict]) -> dict:
    changed = 0
    noop = 0
    problems: list[str] = []
    for p in parts:
        if p["id"] in EXCLUDE_USD_REPRICE_IDS:
            continue
        if p.get("price_usd") is None or p.get("price_inr") is not None:
            continue
        if not _is_http(p.get("source_url")):
            continue
        if p.get("found") is False:
            continue

        row = conn.execute(
            "SELECT id, price_inr, price_usd, last_price_check FROM parts WHERE id = ?",
            (p["id"],),
        ).fetchone()
        if row is None:
            problems.append(f"part {p['id']}: not found in DB — skipped")
            continue

        sticker_inr = float(p["price_usd"]) * USD_TO_INR_RATE
        target_price = estimate_landing_cost_inr(
            sticker_inr,
            retailer=p.get("retailer"),
            availability=p.get("availability"),
        )
        target_usd = round(float(p["price_usd"]), 2)

        updates: dict[str, object] = {}
        if row["price_inr"] is None or round(float(row["price_inr"]), 2) != round(
            target_price, 2
        ):
            updates["price_inr"] = target_price
        if row["price_usd"] is None or round(float(row["price_usd"]), 2) != target_usd:
            updates["price_usd"] = target_usd
        if row["last_price_check"] != PATCH_DATE:
            updates["last_price_check"] = PATCH_DATE

        if not updates:
            noop += 1
            continue

        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE parts SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*updates.values(), p["id"]),
        )
        changed += 1
    return {"changed": changed, "noop": noop, "problems": problems}


# ────────────────────────────────────────────────────────────────────
# Action 3 — discontinued parts
# ────────────────────────────────────────────────────────────────────
def _apply_discontinued(conn: sqlite3.Connection) -> dict:
    changed = 0
    noop = 0
    problems: list[str] = []
    for pid in DISCONTINUED_PART_IDS:
        row = conn.execute(
            "SELECT id, availability FROM parts WHERE id = ?", (pid,)
        ).fetchone()
        if row is None:
            problems.append(f"part {pid}: not found in DB — skipped")
            continue
        if row["availability"] == "discontinued":
            noop += 1
            continue
        conn.execute(
            "UPDATE parts SET availability = 'discontinued', "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (pid,),
        )
        changed += 1
    return {"changed": changed, "noop": noop, "problems": problems}


# ────────────────────────────────────────────────────────────────────
# Action 4 — fictional-brand honesty renames
# ────────────────────────────────────────────────────────────────────
def _apply_fictional_brand_renames(conn: sqlite3.Connection) -> dict:
    changed = 0
    noop = 0
    problems: list[str] = []
    for fix in FICTIONAL_BRAND_RENAMES:
        row = conn.execute(
            "SELECT id, brand, model_name FROM parts WHERE id = ?", (fix["id"],)
        ).fetchone()
        if row is None:
            problems.append(f"part {fix['id']}: not found in DB — skipped")
            continue
        if row["brand"] == fix["new_brand"] and row["model_name"] == fix["new_name"]:
            noop += 1
            continue
        if row["brand"] != fix["old_brand"] or row["model_name"] != fix["old_name"]:
            problems.append(
                f"part {fix['id']}: brand/name is {row['brand']!r}/{row['model_name']!r} "
                f"(expected {fix['old_brand']!r}/{fix['old_name']!r} or already-renamed "
                f"{fix['new_brand']!r}/{fix['new_name']!r}) — skipped"
            )
            continue
        conn.execute(
            "UPDATE parts SET brand = ?, model_name = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (fix["new_brand"], fix["new_name"], fix["id"]),
        )
        changed += 1
    return {"changed": changed, "noop": noop, "problems": problems}


# ────────────────────────────────────────────────────────────────────
# Action 5 — tire family status (discontinued / not_found)
# ────────────────────────────────────────────────────────────────────
def _apply_tire_family_status(conn: sqlite3.Connection, families: list[dict]) -> dict:
    changed = 0
    noop = 0
    problems: list[str] = []
    for fam in families:
        status = fam.get("status")
        if status not in ("discontinued", "not_found"):
            continue
        if status == "discontinued":
            successor = fam.get("successor") or "none specified"
            tag = _DISCONTINUED_TAG_FMT.format(successor=successor)
        else:
            tag = _NOT_FOUND_TAG

        for tid in fam.get("tire_ids") or []:
            row = conn.execute(
                "SELECT id, available_india, data_source FROM tire_models WHERE id = ?",
                (tid,),
            ).fetchone()
            if row is None:
                problems.append(
                    f"tire {tid} ({fam.get('manufacturer')} {fam.get('model')}): "
                    "not found in DB — skipped"
                )
                continue
            existing_source = row["data_source"] or ""
            needs_avail = row["available_india"] != 0
            needs_tag = tag not in existing_source

            if not needs_avail and not needs_tag:
                noop += 1
                continue

            new_source = existing_source + tag if needs_tag else existing_source
            conn.execute(
                "UPDATE tire_models SET available_india = 0, data_source = ?, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_source, tid),
            )
            changed += 1
    return {"changed": changed, "noop": noop, "problems": problems}


# ────────────────────────────────────────────────────────────────────
# Action 6 — tire prices (conservative, unambiguous mapping only)
# ────────────────────────────────────────────────────────────────────
def _collect_tire_price_targets(
    conn: sqlite3.Connection, families: list[dict]
) -> tuple[dict[int, list[tuple[float, str]]], int]:
    """Map each family's scraped price points onto a single tire_models row
    where the mapping is unambiguous. Returns (tire_id -> [(price_inr,
    provenance), ...], count of price points with no unique row match)."""
    norm = TireRepository.normalize_size_designation
    targets: dict[int, list[tuple[float, str]]] = {}
    no_unique_match = 0

    for fam in families:
        ids = fam.get("tire_ids") or []
        if not ids:
            continue
        row_sizes: dict[int, str] = {}
        if len(ids) > 1:
            for tid in ids:
                r = conn.execute(
                    "SELECT size_designation FROM tire_models WHERE id = ?", (tid,)
                ).fetchone()
                if r is not None:
                    row_sizes[tid] = norm(r["size_designation"])

        for pr in fam.get("prices") or []:
            price_inr = pr.get("price_inr")
            if price_inr is None:
                continue
            if len(ids) == 1:
                target = ids[0]
            else:
                nsize = norm(pr.get("size") or "")
                matches = [tid for tid, s in row_sizes.items() if s == nsize]
                if len(matches) != 1:
                    no_unique_match += 1
                    continue
                target = matches[0]
            label = (
                f"{fam.get('manufacturer')} {fam.get('model')} ({pr.get('retailer')})"
            )
            targets.setdefault(target, []).append((float(price_inr), label))

    return targets, no_unique_match


def _apply_tire_prices(conn: sqlite3.Connection, families: list[dict]) -> dict:
    targets, no_unique_match = _collect_tire_price_targets(conn, families)
    changed = 0
    noop = 0
    conflict = 0
    problems: list[str] = []

    for tire_id, candidates in sorted(targets.items()):
        distinct = sorted({round(v, 2) for v, _ in candidates})
        if len(distinct) != 1:
            conflict += 1
            problems.append(
                f"tire {tire_id}: {len(candidates)} conflicting price points "
                f"{distinct} — skipped ({candidates[0][1]})"
            )
            continue
        target_price = distinct[0]

        row = conn.execute(
            "SELECT id, price_inr FROM tire_models WHERE id = ?", (tire_id,)
        ).fetchone()
        if row is None:
            problems.append(f"tire {tire_id}: not found in DB — skipped")
            continue

        current = row["price_inr"]
        if current is not None and round(float(current), 2) == target_price:
            noop += 1
            continue

        conn.execute(
            "UPDATE tire_models SET price_inr = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (target_price, tire_id),
        )
        changed += 1

    return {
        "changed": changed,
        "noop": noop,
        "conflict_skipped": conflict,
        "no_unique_row_match_skipped": no_unique_match,
        "problems": problems,
    }


# ────────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────────
_ACTION_ORDER = (
    "inr_reprice",
    "usd_reprice",
    "discontinued",
    "fictional_brand_renames",
    "tire_family_status",
    "tire_prices",
)


def main(db_path: str | None = None) -> dict:
    if db_path is None:
        db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")

    if not os.path.exists(db_path):
        return {"db_path": db_path, "error": f"DB not found at {db_path}"}

    parts_data = _load_json(PARTS_JSON)["parts"]
    tire_families = _load_json(TIRES_JSON)["tire_families"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    summary: dict = {"db_path": db_path}
    summary["inr_reprice"] = _apply_inr_reprice(conn, parts_data)
    summary["usd_reprice"] = _apply_usd_reprice(conn, parts_data)
    summary["discontinued"] = _apply_discontinued(conn)
    summary["fictional_brand_renames"] = _apply_fictional_brand_renames(conn)
    summary["tire_family_status"] = _apply_tire_family_status(conn, tire_families)
    summary["tire_prices"] = _apply_tire_prices(conn, tire_families)

    conn.commit()

    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        summary["foreign_key_violations"] = len(fk)

    conn.close()

    summary["total_changed"] = sum(summary[k]["changed"] for k in _ACTION_ORDER)
    return summary


def _print_summary(summary: dict) -> None:
    if "error" in summary:
        print(f"ERROR: {summary['error']}", file=sys.stderr)
        return

    print(f"web-scrape data patch — {summary['db_path']}")
    for key in _ACTION_ORDER:
        s = summary[key]
        extra = ""
        if "conflict_skipped" in s:
            extra = (
                f", conflict_skipped={s['conflict_skipped']}, "
                f"no_unique_row_match_skipped={s['no_unique_row_match_skipped']}"
            )
        print(
            f"  [{key}] changed={s['changed']} noop={s['noop']}{extra} "
            f"problems={len(s['problems'])}"
        )
        for prob in s["problems"]:
            print(f"    WARN: {prob}")

    if summary.get("foreign_key_violations"):
        print(
            f"ERROR: foreign_key_check reported "
            f"{summary['foreign_key_violations']} violations",
            file=sys.stderr,
        )

    print(f"Done. {summary['total_changed']} total changes.")


if __name__ == "__main__":
    result = main()
    _print_summary(result)
    if result.get("error") or result.get("foreign_key_violations"):
        sys.exit(1)
    sys.exit(0)
