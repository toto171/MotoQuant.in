"""
MotoQuant Pro — Bulk Scrape Catalog
=====================================
Master list of every manufacturer + category + year range we want to pull
into the bike database.

Coverage target: all 600cc+ supersport / naked / sport-cruiser models
from 2000 to 2026 across the major global brands.

Each entry contains:
  manufacturer  : Display name (used for UI + DB storage)
  bikez_slug    : String used in bikez.com URLs, e.g. "suzuki" →
                  https://bikez.com/motorcycles/suzuki_motorcycles.php
  categories    : List of our internal category strings to KEEP
                  (sport / naked / cruiser / all).  "all" keeps everything.
  min_cc        : Minimum displacement to keep (cc)
  year_from     : Earliest model year to import
  year_to       : Latest model year to import (inclusive)
  priority      : 1=high (well-known in Indian drag scene), 2=standard, 3=niche
  note          : Human-readable note about quirks

Categories mapping (bikez raw → our internal):
  "Sport" / "Sport touring" / "Race" → "sport"
  "Naked bike" / "Standard" / "Streetfighter" → "naked"
  "Custom / cruiser" → "cruiser"
  "Super motard" → "naked"  (treated as naked for drag purposes)
"""

from typing import TypedDict


class ManufacturerEntry(TypedDict, total=False):
    manufacturer: str
    bikez_slug: str
    categories: list[str]
    min_cc: int
    year_from: int
    year_to: int
    priority: int
    note: str


# ── Japanese Big 4 ────────────────────────────────────────────────────────────
_JP4: list[ManufacturerEntry] = [
    {
        "manufacturer": "Suzuki",
        "bikez_slug": "suzuki",
        "categories": ["sport", "naked"],
        "min_cc": 600,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "GSX-R 600/750/1000, Hayabusa, Katana, GSX-S series",
    },
    {
        "manufacturer": "Yamaha",
        "bikez_slug": "yamaha",
        "categories": ["sport", "naked"],
        "min_cc": 600,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "R6, R1, R7, MT-07/09/10, FZ, XSR, VMAX",
    },
    {
        "manufacturer": "Honda",
        "bikez_slug": "honda",
        "categories": ["sport", "naked"],
        "min_cc": 600,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "CBR 600RR/900RR/1000RR, CB, Hornet, VTR, SP2",
    },
    {
        "manufacturer": "Kawasaki",
        "bikez_slug": "kawasaki",
        "categories": ["sport", "naked"],
        "min_cc": 600,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "ZX-6R/7R/9R/10R/12R/14R/25R, Z series, Ninja H2, ER",
    },
]

# ── European ─────────────────────────────────────────────────────────────────
_EUR: list[ManufacturerEntry] = [
    {
        "manufacturer": "Aprilia",
        "bikez_slug": "aprilia",
        "categories": ["sport", "naked"],
        "min_cc": 660,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "RSV4, RS 660, Tuono V4/660, RSV, Falco, Shiver 900",
    },
    {
        "manufacturer": "Ducati",
        "bikez_slug": "ducati",
        "categories": ["sport", "naked", "cruiser"],
        "min_cc": 748,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 1,
        "note": "Panigale, Monster, Streetfighter, Hypermotard, 749/999/1098/1198",
    },
    {
        "manufacturer": "MV Agusta",
        "bikez_slug": "mv_agusta",
        "categories": ["sport", "naked"],
        "min_cc": 675,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 2,
        "note": "F4, F3 675/800, Brutale, Dragster, Turismo Veloce",
    },
    {
        "manufacturer": "BMW",
        "bikez_slug": "bmw",
        "categories": ["sport", "naked"],
        "min_cc": 650,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 2,
        "note": "S 1000 RR/R/XR, M 1000 RR/R, F 900 R, HP4",
    },
    {
        "manufacturer": "KTM",
        "bikez_slug": "ktm",
        "categories": ["sport", "naked"],
        "min_cc": 690,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 2,
        "note": "Super Duke 990/1290/GT, RC 390/790/8C, Duke 790/890/990",
    },
    {
        "manufacturer": "Triumph",
        "bikez_slug": "triumph",
        "categories": ["sport", "naked"],
        "min_cc": 660,
        "year_from": 2000,
        "year_to": 2026,
        "priority": 2,
        "note": "Daytona 675/765, Speed Triple/RS, Street Triple, Speed Twin",
    },
    {
        "manufacturer": "Norton",
        "bikez_slug": "norton",
        "categories": ["sport", "naked", "cruiser"],
        "min_cc": 961,
        "year_from": 2010,
        "year_to": 2026,
        "priority": 3,
        "note": "Commando 961, V4CR, Atlas 650",
    },
]

# ── American ──────────────────────────────────────────────────────────────────
_AMR: list[ManufacturerEntry] = [
    {
        "manufacturer": "Harley-Davidson",
        "bikez_slug": "harley-davidson",
        "categories": ["sport", "naked", "cruiser"],
        "min_cc": 1130,
        "year_from": 2002,
        "year_to": 2026,
        "priority": 2,
        "note": "V-Rod 1130/1250 VRSC series. Standard H-D customs/touring are out-of-scope.",
    },
    {
        "manufacturer": "Indian",
        "bikez_slug": "indian",
        "categories": ["sport", "naked", "cruiser"],
        "min_cc": 1133,
        "year_from": 2015,
        "year_to": 2026,
        "priority": 2,
        "note": "FTR 1200, Scout Bobber, Challenger — high displacement sport/cruiser only",
    },
]

# ── Others relevant to Indian market ─────────────────────────────────────────
_OTHER: list[ManufacturerEntry] = [
    {
        "manufacturer": "Royal Enfield",
        "bikez_slug": "royal_enfield",
        "categories": ["sport", "naked", "cruiser"],
        "min_cc": 648,
        "year_from": 2019,
        "year_to": 2026,
        "priority": 2,
        "note": "INT 650, Interceptor 650, Super Meteor 650, Shotgun 650",
    },
    {
        "manufacturer": "Benelli",
        "bikez_slug": "benelli",
        "categories": ["sport", "naked"],
        "min_cc": 752,
        "year_from": 2016,
        "year_to": 2026,
        "priority": 3,
        "note": "752S, Leoncino 800",
    },
    {
        "manufacturer": "CFMoto",
        "bikez_slug": "cfmoto",
        "categories": ["sport", "naked"],
        "min_cc": 700,
        "year_from": 2019,
        "year_to": 2026,
        "priority": 3,
        "note": "700CL-X, 800NK, 800MT",
    },
    {
        "manufacturer": "Husqvarna",
        "bikez_slug": "husqvarna",
        "categories": ["sport", "naked"],
        "min_cc": 693,
        "year_from": 2020,
        "year_to": 2026,
        "priority": 3,
        "note": "Vitpilen 701, Norden 901 (KTM platform bikes)",
    },
]

# ── Master catalog (in priority order) ───────────────────────────────────────
SCRAPE_CATALOG: list[ManufacturerEntry] = _JP4 + _EUR + _AMR + _OTHER

# ── Convenience lookups ───────────────────────────────────────────────────────


def get_entry(manufacturer: str) -> ManufacturerEntry | None:
    """Return the catalog entry for a manufacturer (case-insensitive)."""
    key = manufacturer.lower().strip()
    for e in SCRAPE_CATALOG:
        if e["manufacturer"].lower() == key:
            return e
        # also match by bikez_slug
        if e["bikez_slug"].lower() == key:
            return e
    return None


def all_manufacturers() -> list:
    """Return all manufacturer display names in priority order."""
    return [e["manufacturer"] for e in SCRAPE_CATALOG]


def priority_manufacturers(max_priority: int = 2) -> list:
    """Return manufacturers at or above the given priority level."""
    return [e["manufacturer"] for e in SCRAPE_CATALOG if e["priority"] <= max_priority]


# ── Summary for CLI ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Total catalog entries: {len(SCRAPE_CATALOG)}")
    for e in SCRAPE_CATALOG:
        cats = "/".join(e["categories"])
        print(
            f"  [{e['priority']}] {e['manufacturer']:<20}  "
            f"{e['min_cc']}cc+  {e['year_from']}-{e['year_to']}  ({cats})"
        )
