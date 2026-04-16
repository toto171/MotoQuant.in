"""
MotoQuant Pro — Bikez.com Scraper
=================================
Scrapes motorcycle specifications from bikez.com.

Bikez.com structure (2024):
  Listing: https://bikez.com/motorcycles/{manufacturer}_motorcycles.php
  Detail:  https://bikez.com/motorcycles/{manufacturer}_{model}_{year}.php
  Also:    https://bikez.com/motorcycles/compare_insurance.php?id={id}

The spec table on detail pages follows:
  <table class="zebra-table">
    <tr><td>Displacement</td><td>999 ccm (60.96 cubic inches)</td></tr>
    ...

Rate limiting: 1.5 seconds between requests (polite scraping).
Uses a persistent requests.Session with realistic browser headers.
"""

import logging
import re
import time
import urllib.parse
from collections.abc import Iterator
from typing import Any

from .spec import BikeSpec

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────
# HTTP helpers
# ────────────────────────────────────────────────────────

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BASE_URL = "https://bikez.com"
RATE_LIMIT_S = 1.5  # seconds between requests
REQUEST_TIMEOUT = 20  # seconds


def _make_session():
    """Create a requests.Session with browser-like headers."""
    try:
        import requests
    except ImportError:
        raise RuntimeError(
            "requests library not found. Install with: pip install requests --break-system-packages"
        )
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def _fetch(session, url: str, retries: int = 3, backoff: float = 2.0) -> str | None:
    """
    Fetch a URL with retry and exponential backoff.
    Returns HTML text or None on failure.
    """
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            wait = backoff**attempt
            logger.warning(
                f"Fetch failed (attempt {attempt + 1}/{retries}): {url} — {exc}. "
                f"Retrying in {wait:.1f}s..."
            )
            if attempt < retries - 1:
                time.sleep(wait)
    logger.error(f"Failed to fetch after {retries} attempts: {url}")
    return None


# ────────────────────────────────────────────────────────
# HTML parsers (no external BS4 dependency - pure stdlib)
# ────────────────────────────────────────────────────────


def _strip_tags(html: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", html)


def _html_decode(s: str) -> str:
    """Decode basic HTML entities."""
    entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&nbsp;": " ",
        "&quot;": '"',
        "&#39;": "'",
        "&rsquo;": "'",
        "&lsquo;": "'",
        "&mdash;": "—",
    }
    for ent, char in entities.items():
        s = s.replace(ent, char)
    # Numeric entities
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
    return s


def _parse_table_rows(html: str) -> dict[str, str]:
    """
    Extract key→value pairs from a simple HTML table.
    Returns {cleaned_header: cleaned_value} dict.
    """
    rows = {}
    # Match <tr>...</tr> blocks
    for tr_match in re.finditer(
        r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE
    ):
        tr = tr_match.group(1)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL | re.IGNORECASE)
        if len(tds) >= 2:
            key = _html_decode(_strip_tags(tds[0])).strip()
            val = _html_decode(_strip_tags(tds[1])).strip()
            if key:
                rows[key] = val
    return rows


def _find_links_matching(
    html: str, pattern: str, base_url: str = BASE_URL
) -> list[str]:
    """Find all href links matching a regex pattern."""
    links = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        href = m.group(1)
        if re.search(pattern, href, re.IGNORECASE):
            if href.startswith("http"):
                links.append(href)
            elif href.startswith("/"):
                links.append(base_url + href)
            else:
                links.append(base_url + "/" + href)
    return list(dict.fromkeys(links))  # dedup, preserve order


# ────────────────────────────────────────────────────────
# Value parsers — extract numeric values from raw strings
# ────────────────────────────────────────────────────────


def _parse_float(s: str) -> float | None:
    """Extract first float from a string like '999 ccm (60.96 cubic inches)'."""
    m = re.search(r"[\d,]+\.?\d*", s.replace(",", ""))
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return None


def _parse_int(s: str) -> int | None:
    f = _parse_float(s)
    return int(f) if f is not None else None


def _parse_power(s: str) -> tuple[float | None, int | None]:
    """
    Parse power string like '178 HP @ 12000 RPM' or '132.0 kW / 13500 rpm'.
    Returns (hp, rpm).
    """
    hp, rpm = None, None

    # kW → HP conversion
    kw_match = re.search(r"([\d.]+)\s*kW", s, re.IGNORECASE)
    if kw_match:
        hp = float(kw_match.group(1)) * 1.341

    # HP directly
    hp_match = re.search(r"([\d.]+)\s*(?:HP|PS|bhp|cv|ch)", s, re.IGNORECASE)
    if hp_match and hp is None:
        hp = float(hp_match.group(1))

    # RPM
    rpm_match = re.search(r"@?\s*([\d,]+)\s*[Rr][Pp][Mm]", s)
    if rpm_match:
        try:
            rpm = int(rpm_match.group(1).replace(",", ""))
        except ValueError:
            pass

    return hp, rpm


def _parse_torque(s: str) -> tuple[float | None, int | None]:
    """
    Parse torque string like '113 Nm @ 9000 RPM' or '79.5 ft-lbs @ 9500 rpm'.
    Returns (nm, rpm).
    """
    nm, rpm = None, None

    ftlb_match = re.search(r"([\d.]+)\s*(?:ft[-.]?lbs?|lb[-.]?ft)", s, re.IGNORECASE)
    if ftlb_match:
        nm = float(ftlb_match.group(1)) * 1.356

    nm_match = re.search(r"([\d.]+)\s*(?:Nm|N\.m)", s, re.IGNORECASE)
    if nm_match and nm is None:
        nm = float(nm_match.group(1))

    rpm_match = re.search(r"@?\s*([\d,]+)\s*[Rr][Pp][Mm]", s)
    if rpm_match:
        try:
            rpm = int(rpm_match.group(1).replace(",", ""))
        except ValueError:
            pass

    return nm, rpm


def _parse_mass(s: str) -> float | None:
    """Parse mass, convert lbs to kg if needed."""
    # Try kg first
    kg_match = re.search(r"([\d.]+)\s*kg", s, re.IGNORECASE)
    if kg_match:
        return float(kg_match.group(1))
    # Try lbs
    lb_match = re.search(r"([\d.]+)\s*(?:lbs?|pounds?)", s, re.IGNORECASE)
    if lb_match:
        return float(lb_match.group(1)) * 0.4536
    # Fallback: bare number < 500 → kg, > 500 → likely lbs
    f = _parse_float(s)
    if f is not None:
        return f * 0.4536 if f > 500 else f
    return None


def _parse_tire(s: str) -> str | None:
    """Extract tire size string like '120/70ZR17'."""
    m = re.search(r"\d{2,3}[/\\]\d{2,3}\s*[ZR]?R?\s*\d{2}", s, re.IGNORECASE)
    if m:
        return re.sub(r"\s+", "", m.group())
    return None


def _classify_category(s: str) -> str:
    """Map Bikez category string to our internal category."""
    s = s.lower()
    if any(x in s for x in ["sport", "super", "race", "track"]):
        return "sport"
    if any(x in s for x in ["naked", "standard", "streetfighter", "muscle"]):
        return "naked"
    if any(x in s for x in ["cruiser", "chopper", "custom", "bobber"]):
        return "cruiser"
    if any(x in s for x in ["adventure", "dual", "enduro", "offroad", "off-road"]):
        return "adventure"
    if any(x in s for x in ["touring", "gt ", "grand", "bagger"]):
        return "touring"
    return "sport"  # default


# ────────────────────────────────────────────────────────
# Core: parse a bikez detail page into BikeSpec
# ────────────────────────────────────────────────────────

# Bikez field name → our field name + parser
FIELD_MAP = {
    # Engine
    "Displacement": ("displacement_cc", _parse_float),
    "Bore x Stroke": ("bore_x_stroke_raw", lambda s: s),
    "Compression": ("compression_ratio", _parse_float),
    "Power": ("power_raw", lambda s: s),
    "Torque": ("torque_raw", lambda s: s),
    "Fuel System": ("fuel_system", lambda s: s.split()[0].lower()),
    "Cooling System": ("cooling", lambda s: s.split()[0].lower()),
    "Valves Per Cylinder": ("valves_per_cyl_raw", _parse_int),
    "Number of Cylinders": ("cylinders", _parse_int),
    "Engine Type": ("engine_type_raw", lambda s: s.lower()),
    # Drivetrain
    "Number of Gears": ("gears", _parse_int),
    "Drive": ("final_drive", lambda s: s.lower().split()[0]),
    # Chassis
    "Dry weight": ("dry_mass_kg", _parse_mass),
    "Wet weight": ("wet_mass_kg", _parse_mass),
    "Wheelbase": (
        "wheelbase_mm",
        lambda s: (
            _parse_float(s) * 1000
            if re.search(r"\d\.\d{2,3}\s*m", s, re.I)
            else _parse_float(s)
        ),
    ),
    "Seat Height": (
        "seat_height_mm",
        lambda s: (
            _parse_float(s) * 1000
            if re.search(r"\d\.\d{2,3}\s*m", s, re.I)
            else _parse_float(s)
        ),
    ),
    "Fuel Capacity": ("fuel_capacity_l", _parse_float),
    # Tires
    "Front Tires": ("front_tire_size", _parse_tire),
    "Rear Tires": ("rear_tire_size", _parse_tire),
    # Category
    "Category": ("category_raw", lambda s: s),
    "Year": ("year_raw", lambda s: s),
}


def _parse_bikez_spec_table(
    html: str, url: str, manufacturer: str = "", model_name: str = ""
) -> BikeSpec:
    """
    Parse a Bikez.com detail page HTML into a BikeSpec.
    """
    rows = _parse_table_rows(html)
    spec = BikeSpec(
        manufacturer=manufacturer,
        model_name=model_name,
        source_name="bikez",
        source_url=url,
    )
    raw_data = {}

    for bz_field, (our_field, parser) in FIELD_MAP.items():
        val_str = rows.get(bz_field)
        if val_str is None:
            # Try partial match
            for k, v in rows.items():
                if bz_field.lower() in k.lower():
                    val_str = v
                    break
        if val_str:
            raw_data[bz_field] = val_str
            try:
                parsed = parser(val_str)
                if parsed is not None:
                    setattr(spec, our_field, parsed)
            except Exception as e:
                logger.debug(f"  parse error for {bz_field}='{val_str}': {e}")

    spec.raw_data = raw_data

    # ── Post-process compound fields ────────────────────────────────────
    # Bore × stroke: "73.4 x 59.0 mm" → bore_mm, stroke_mm
    bore_raw = raw_data.get("Bore x Stroke", "")
    if bore_raw:
        nums = re.findall(r"[\d.]+", bore_raw)
        if len(nums) >= 2:
            spec.bore_mm = float(nums[0])
            spec.stroke_mm = float(nums[1])

    # Power: "178.0 HP (130.0 kW)) @ 12,000 RPM"
    power_raw = raw_data.get("Power", "")
    if power_raw:
        hp, rpm = _parse_power(power_raw)
        if hp:
            spec.peak_power_hp = hp
        if rpm:
            spec.peak_power_rpm = rpm

    # Torque: "113 Nm (11.5 kgf-m or 83.3 ft.lbs) @ 9,000 RPM"
    torque_raw = raw_data.get("Torque", "")
    if torque_raw:
        nm, rpm = _parse_torque(torque_raw)
        if nm:
            spec.peak_torque_nm = nm
        if rpm:
            spec.peak_torque_rpm = rpm

    # Category
    cat_raw = getattr(spec, "category_raw", None)
    if cat_raw:
        spec.category = _classify_category(cat_raw)
        del spec.__dict__["category_raw"]

    # Year from model page (usually in URL or page title)
    year_raw = getattr(spec, "year_raw", None)
    if year_raw:
        years = re.findall(r"\b(19[7-9]\d|20[0-3]\d)\b", year_raw)
        if years:
            spec.year_from = int(years[0])
            if len(years) > 1:
                spec.year_to = int(years[-1])
        try:
            del spec.__dict__["year_raw"]
        except KeyError:
            pass

    # Engine type → valve config (DOHC / SOHC)
    eng_raw = getattr(spec, "engine_type_raw", None)
    if eng_raw:
        if "dohc" in eng_raw:
            spec.valve_config = "dohc"
        elif "sohc" in eng_raw:
            spec.valve_config = "sohc"
        try:
            del spec.__dict__["engine_type_raw"]
        except KeyError:
            pass

    # bore_x_stroke_raw cleanup
    if hasattr(spec, "bore_x_stroke_raw"):
        try:
            del spec.__dict__["bore_x_stroke_raw"]
        except KeyError:
            pass

    # valves_per_cyl_raw cleanup
    if hasattr(spec, "valves_per_cyl_raw"):
        try:
            del spec.__dict__["valves_per_cyl_raw"]
        except KeyError:
            pass

    # Set per-field confidence to "bikez" level
    for field_name in [
        "displacement_cc",
        "bore_mm",
        "stroke_mm",
        "compression_ratio",
        "peak_power_hp",
        "peak_power_rpm",
        "peak_torque_nm",
        "peak_torque_rpm",
        "dry_mass_kg",
        "wet_mass_kg",
        "gears",
        "wheelbase_mm",
        "front_tire_size",
        "rear_tire_size",
    ]:
        if getattr(spec, field_name, None) is not None:
            spec.field_confidence[field_name] = 0.58

    return spec


# ────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────


def scrape_bikez(url: str, session=None) -> BikeSpec | None:
    """
    Scrape a single Bikez.com detail page.

    Args:
        url: Full URL of the bikez.com motorcycle detail page.
        session: Optional requests.Session (reused for connection pooling).

    Returns:
        BikeSpec or None if the page could not be fetched/parsed.

    Example:
        spec = scrape_bikez(
            "https://bikez.com/motorcycles/suzuki_gsx-r_1000_2005.php"
        )
    """
    if session is None:
        session = _make_session()

    html = _fetch(session, url)
    if html is None:
        return None

    # Extract manufacturer and model from URL
    url_path = urllib.parse.urlparse(url).path
    # e.g. /motorcycles/suzuki_gsx-r_1000_2005.php
    fn = url_path.split("/")[-1].replace(".php", "")
    parts = fn.split("_")

    manufacturer = parts[0].replace("-", " ").title() if parts else ""
    year_from_url = None
    model_parts = []
    for p in parts[1:]:
        if re.match(r"^\d{4}$", p):
            year_from_url = int(p)
            break
        model_parts.append(p)
    model_name = " ".join(p.replace("-", " ").upper() for p in model_parts)

    spec = _parse_bikez_spec_table(html, url, manufacturer, model_name)

    if year_from_url and spec.year_from is None:
        spec.year_from = year_from_url

    return spec


def crawl_bikez(
    manufacturer: str,
    session=None,
    limit: int = 100,
    category_filter: str | None = None,
    min_displacement_cc: float = 400.0,
    rate_limit_s: float = RATE_LIMIT_S,
) -> Iterator[BikeSpec]:
    """
    Crawl Bikez.com for all motorcycles from a given manufacturer.

    Yields BikeSpec objects as they are parsed (generator).
    Respects rate limiting between requests.

    Args:
        manufacturer: Manufacturer name (e.g. "Suzuki", "Yamaha")
        session:      Optional requests.Session
        limit:        Maximum number of bikes to scrape (safety cap)
        category_filter: If set, only yield bikes in this category
        min_displacement_cc: Skip bikes below this displacement
        rate_limit_s: Seconds to wait between requests

    Yields:
        BikeSpec instances

    Example:
        for spec in crawl_bikez("Suzuki", limit=50, min_displacement_cc=600):
            db_spec, result = validate_spec(spec)
            if result.is_valid:
                import_spec(db, spec)
    """
    if session is None:
        session = _make_session()

    mfr_slug = manufacturer.lower().replace(" ", "_")
    listing_url = f"{BASE_URL}/motorcycles/{mfr_slug}_motorcycles.php"

    logger.info(f"Crawling {manufacturer}: {listing_url}")
    html = _fetch(session, listing_url)
    if html is None:
        logger.error(f"Could not fetch manufacturer listing: {listing_url}")
        return

    # Find links to detail pages
    detail_links = _find_links_matching(
        html,
        r"/motorcycles/" + mfr_slug + r"[_-].+\.php",
        BASE_URL,
    )

    # Deduplicate and filter out listing pages
    detail_links = [
        lnk
        for lnk in detail_links
        if re.search(r"\d{4}\.php$", lnk)  # year at end means detail page
    ]

    logger.info(f"  Found {len(detail_links)} detail page candidates")

    count = 0
    for url in detail_links:
        if count >= limit:
            break

        time.sleep(rate_limit_s)  # polite rate limiting

        spec = scrape_bikez(url, session=session)
        if spec is None:
            continue

        spec.manufacturer = manufacturer

        # Apply filters
        if min_displacement_cc and spec.displacement_cc:
            if spec.displacement_cc < min_displacement_cc:
                logger.debug(
                    f"  Skipping {spec.model_name} ({spec.displacement_cc:.0f}cc "
                    f"< {min_displacement_cc:.0f}cc)"
                )
                continue

        if category_filter and spec.category != category_filter:
            continue

        logger.info(
            f"  Scraped: {spec.manufacturer} {spec.model_name} "
            f"({spec.year_from or '?'}) — "
            f"{spec.displacement_cc or '?'}cc {spec.peak_power_hp or '?'}HP"
        )
        count += 1
        yield spec

    logger.info(f"Crawl complete: {count} bikes scraped from {manufacturer}")


# ────────────────────────────────────────────────────────
# Manual data entry helper (no network needed)
# ────────────────────────────────────────────────────────


def spec_from_dict(data: dict[str, Any], source_name: str = "spec_sheet") -> BikeSpec:
    """
    Create a BikeSpec from a manually curated dict.
    Useful for known-good data that doesn't need scraping.

    Example:
        spec = spec_from_dict({
            "manufacturer": "Honda",
            "model_name": "CBR 1000RR Fireblade",
            "year_from": 2004, "year_to": 2007,
            "displacement_cc": 998,
            "peak_power_hp": 172,
            "peak_power_rpm": 11250,
            "dry_mass_kg": 179,
            "gear_ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.241],
            "front_sprocket": 16, "rear_sprocket": 43,
        })
    """
    spec = BikeSpec(source_name=source_name)
    for k, v in data.items():
        if hasattr(spec, k):
            setattr(spec, k, v)
    # Set high confidence for manually entered data
    for f in data:
        if hasattr(spec, f) and f not in ("manufacturer", "model_name", "source_name"):
            spec.field_confidence[f] = 0.88
    return spec
