"""
MotoQuant Pro — Bulk Scrape Orchestrator
==========================================
Drives a multi-manufacturer crawl of bikez.com with:

  • Checkpoint / resume — progress is saved to a JSON file after every
    successfully imported bike.  If the run is interrupted, restart with
    --resume and it picks up where it left off.

  • Deduplication — before fetching a detail page, the DB is checked for a
    matching (manufacturer, model, year) row.  Already-imported bikes are
    skipped (unless --force-reimport is set).

  • Year and category filtering — only keeps bikes from year_from–year_to
    and in the requested categories (sport / naked / cruiser).

  • Rate-limit politeness — configurable delay between requests.

  • Per-manufacturer progress reporting — printed to stdout as it goes.

Typical use
-----------
    # Full bulk run (resumes from checkpoint if interrupted)
    python -m motoquant.run scrape --bulk

    # Dry run to see what would be scraped
    python -m motoquant.run scrape --bulk --dry-run

    # Prioritised run (only manufacturers marked priority 1 or 2)
    python -m motoquant.run scrape --bulk --priority 2

    # Resume a previous interrupted run
    python -m motoquant.run scrape --bulk --resume

    # Target a single manufacturer via bulk machinery
    python -m motoquant.run scrape --bulk --only Yamaha
"""

import json
import logging
import os
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .catalog import SCRAPE_CATALOG, get_entry
from .importer import import_spec
from .spec import BikeSpec
from .validator import score_spec, validate_spec

logger = logging.getLogger(__name__)

# Default checkpoint file (lives next to motoquant.db)
DEFAULT_CHECKPOINT = "motoquant_scrape_checkpoint.json"
DEFAULT_RATE_LIMIT_S = 1.5  # polite default
MIN_RATE_LIMIT_S = 0.8  # floor — any faster risks blocking
MAX_BATCH_PER_MFR = 300  # safety cap per manufacturer


def _utcnow_iso() -> str:
    """Naive UTC ISO timestamp.

    Python 3.12+ deprecated the implicit-UTC ``datetime.utcnow``; build a
    timezone-aware UTC value and strip the tzinfo so the serialised string
    remains a naive ISO timestamp (matches the pre-3.12 behaviour
    byte-for-byte).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


# ══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════


@dataclass
class MfrProgress:
    """Per-manufacturer scrape progress record."""

    manufacturer: str
    status: str = "pending"  # pending / in_progress / done / failed
    total_found: int = 0
    scraped: int = 0
    imported: int = 0
    skipped_dup: int = 0
    skipped_filter: int = 0
    errors: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    failed_urls: list[str] = field(default_factory=list)


@dataclass
class BulkScrapeResult:
    """Aggregate result from a completed (or interrupted) bulk run."""

    started_at: str = ""
    finished_at: str = ""
    total_imported: int = 0
    total_skipped_dup: int = 0
    total_skipped_filter: int = 0
    total_errors: int = 0
    manufacturers_done: int = 0
    manufacturers_total: int = 0
    per_manufacturer: dict[str, MfrProgress] = field(default_factory=dict)

    def summary_lines(self) -> list[str]:
        lines = [
            "  Bulk scrape summary",
            "  ─────────────────────────────────────────────",
            f"  Imported     : {self.total_imported}",
            f"  Skipped (dup): {self.total_skipped_dup}",
            f"  Skipped (flt): {self.total_skipped_filter}",
            f"  Errors       : {self.total_errors}",
            f"  Mfr done     : {self.manufacturers_done}/{self.manufacturers_total}",
        ]
        return lines


# ══════════════════════════════════════════════════════════════════
# CHECKPOINT SAVE / LOAD
# ══════════════════════════════════════════════════════════════════


def _save_checkpoint(path: str, result: BulkScrapeResult) -> None:
    """Persist BulkScrapeResult to a JSON checkpoint file."""
    try:
        data = asdict(result)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save checkpoint to {path}: {e}")


def _load_checkpoint(path: str) -> BulkScrapeResult | None:
    """Load a previously saved BulkScrapeResult from JSON. Returns None if missing."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        result = BulkScrapeResult(
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
            total_imported=data.get("total_imported", 0),
            total_skipped_dup=data.get("total_skipped_dup", 0),
            total_skipped_filter=data.get("total_skipped_filter", 0),
            total_errors=data.get("total_errors", 0),
            manufacturers_done=data.get("manufacturers_done", 0),
            manufacturers_total=data.get("manufacturers_total", 0),
        )
        for mfr, mp_data in data.get("per_manufacturer", {}).items():
            mp = MfrProgress(manufacturer=mp_data.get("manufacturer", mfr))
            for k, v in mp_data.items():
                if hasattr(mp, k):
                    setattr(mp, k, v)
            result.per_manufacturer[mfr] = mp
        return result
    except Exception as e:
        logger.warning(f"Could not load checkpoint from {path}: {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# STDLIB HTTP SESSION (no external deps)
# ══════════════════════════════════════════════════════════════════

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class _StdlibSession:
    """
    Minimal requests-compatible interface using urllib.
    Drop-in replacement so bikez.py works without the 'requests' package.
    Automatically falls back to the real requests library if available.
    """

    _requests_session = None

    def __init__(self):
        try:
            import requests

            self._requests_session = requests.Session()
            self._requests_session.headers.update(_HEADERS)
        except ImportError:
            pass

    def get(self, url: str, timeout: int = 20):
        if self._requests_session is not None:
            return self._requests_session.get(url, timeout=timeout)

        req = urllib.request.Request(url, headers=_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="replace")

                class _R:
                    status_code = resp.status

                    def raise_for_status(self):
                        pass

                r = _R()
                r.text = text
                return r
        except Exception as err:

            class _Err:
                status_code = 0
                text = ""
                error = err

                def raise_for_status(self):
                    raise OSError(str(self.error))

            return _Err()


# ══════════════════════════════════════════════════════════════════
# DEDUPLICATION
# ══════════════════════════════════════════════════════════════════


def _existing_bike_keys(db) -> set[str]:
    """
    Return a set of "manufacturer|model|year" strings for bikes already in
    the DB, so we can skip re-scraping them.
    """
    keys: set[str] = set()
    try:
        conn = db.connect()
        rows = conn.execute("""
            SELECT m.name, bm.model_name, bm.year_from
            FROM   bike_models bm
            JOIN   manufacturers m ON m.id = bm.manufacturer_id
        """).fetchall()
        for mfr, model, yr in rows:
            keys.add(f"{(mfr or '').lower()}|{(model or '').lower()}|{yr or ''}")
    except Exception as e:
        logger.warning(f"Could not fetch existing bike keys for dedup: {e}")
    return keys


def _spec_key(spec: BikeSpec) -> str:
    return (
        f"{(spec.manufacturer or '').lower()}|"
        f"{(spec.model_name or '').lower()}|"
        f"{spec.year_from or ''}"
    )


# ══════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════


def run_bulk_scrape(
    db,
    checkpoint_path: str = DEFAULT_CHECKPOINT,
    resume: bool = True,
    dry_run: bool = False,
    priority: int = 3,
    only_manufacturer: str | None = None,
    rate_limit_s: float = DEFAULT_RATE_LIMIT_S,
    per_mfr_limit: int = MAX_BATCH_PER_MFR,
    min_confidence: float = 0.30,
    verbose: bool = True,
) -> BulkScrapeResult:
    """
    Run a bulk scrape across all manufacturers in the catalog.

    Parameters
    ----------
    db               : MotoQuantDB instance
    checkpoint_path  : Path to JSON checkpoint file
    resume           : If True, skip manufacturers already marked 'done'
    dry_run          : If True, don't write to DB
    priority         : Only scrape manufacturers with priority <= this value
    only_manufacturer: If set, only scrape this one manufacturer
    rate_limit_s     : Seconds between HTTP requests
    per_mfr_limit    : Max bikes to scrape per manufacturer
    min_confidence   : Minimum overall confidence to import
    verbose          : Print progress to stdout
    """
    from .bikez import crawl_bikez

    rate_limit_s = max(MIN_RATE_LIMIT_S, rate_limit_s)
    session = _StdlibSession()

    # ── Filter catalog ────────────────────────────────────────────────────────
    catalog = [e for e in SCRAPE_CATALOG if e.get("priority", 3) <= priority]
    if only_manufacturer:
        catalog = [
            e for e in catalog if e["manufacturer"].lower() == only_manufacturer.lower()
        ]
        if not catalog:
            entry = get_entry(only_manufacturer)
            if entry:
                catalog = [entry]

    # ── Load or create BulkScrapeResult ───────────────────────────────────────
    result: BulkScrapeResult
    if resume and os.path.exists(checkpoint_path):
        result = _load_checkpoint(checkpoint_path)
        if result is None:
            result = BulkScrapeResult()
        if verbose:
            print(f"\n  Resuming from checkpoint: {checkpoint_path}")
            print(
                f"  (Previously: {result.total_imported} imported, "
                f"{result.manufacturers_done}/{len(catalog)} done)"
            )
    else:
        result = BulkScrapeResult(
            started_at=_utcnow_iso(),
            manufacturers_total=len(catalog),
        )

    result.manufacturers_total = len(catalog)

    # ── Pre-load existing bike keys for deduplication ─────────────────────────
    existing_keys = _existing_bike_keys(db)
    if verbose:
        print(f"  {len(existing_keys)} bikes already in DB (will skip duplicates)")

    # ── Iterate manufacturers ─────────────────────────────────────────────────
    for entry in catalog:
        mfr = entry["manufacturer"]
        categories = entry.get("categories", ["sport", "naked"])
        min_cc = entry.get("min_cc", 600)
        year_from = entry.get("year_from", 2000)
        year_to = entry.get("year_to", 2026)

        # Resume: skip if already done
        prev = result.per_manufacturer.get(mfr)
        if prev and prev.status == "done" and resume:
            if verbose:
                print(
                    f"\n  [{mfr}] ✓ already done ({prev.imported} imported) — skipping"
                )
            continue

        if verbose:
            print(
                f"\n  ── {mfr} ──  "
                f"({'/'.join(categories)}, ≥{min_cc}cc, {year_from}–{year_to})"
            )

        prog = MfrProgress(
            manufacturer=mfr,
            status="in_progress",
            started_at=_utcnow_iso(),
        )
        result.per_manufacturer[mfr] = prog

        try:
            specs = list(
                crawl_bikez(
                    manufacturer=mfr,
                    session=session,
                    limit=per_mfr_limit,
                    min_displacement_cc=float(min_cc),
                    rate_limit_s=rate_limit_s,
                )
            )
            if verbose and len(specs) == 0:
                print(
                    f"    ⚠  No bikes fetched for {mfr} — "
                    f"check network/bikez.com access"
                )
            for spec in specs:
                prog.total_found += 1

                # ── Year filter ───────────────────────────────────────────────
                yr = spec.year_from
                if yr is not None and not (year_from <= yr <= year_to):
                    prog.skipped_filter += 1
                    continue

                # ── Category filter ───────────────────────────────────────────
                if "all" not in categories and spec.category not in categories:
                    prog.skipped_filter += 1
                    continue

                # ── Deduplication ─────────────────────────────────────────────
                key = _spec_key(spec)
                if key in existing_keys:
                    prog.skipped_dup += 1
                    if verbose:
                        print(
                            f"    ∘ skip (dup): {spec.manufacturer} {spec.model_name} "
                            f"({spec.year_from})"
                        )
                    continue

                # ── Validate ──────────────────────────────────────────────────
                v_result = validate_spec(spec)
                conf = score_spec(spec, v_result)

                status_char = "✓" if v_result.is_valid else "?"
                if verbose:
                    warn_str = (
                        f" [{len(v_result.warnings)}W]" if v_result.warnings else ""
                    )
                    print(
                        f"    {status_char} {spec.manufacturer} {spec.model_name} "
                        f"({spec.year_from or '?'})  "
                        f"conf={conf:.2f}  "
                        f"{spec.displacement_cc or '?'}cc  "
                        f"{spec.peak_power_hp or '?'}hp"
                        f"{warn_str}"
                    )

                if not v_result.is_valid or conf < min_confidence:
                    prog.errors += 1
                    continue

                # ── Import ────────────────────────────────────────────────────
                prog.scraped += 1
                if not dry_run:
                    try:
                        import_spec(db, spec, dry_run=False)
                        existing_keys.add(key)  # update dedup set live
                        prog.imported += 1
                        result.total_imported += 1
                    except Exception as exc:
                        logger.error(f"Import failed for {spec.model_name}: {exc}")
                        prog.errors += 1
                        result.total_errors += 1
                else:
                    prog.imported += 1  # count as-if imported in dry run
                    result.total_imported += 1

        except KeyboardInterrupt:
            if verbose:
                print(f"\n  Interrupted during {mfr}. Saving checkpoint...")
            prog.status = "failed"
            _save_checkpoint(checkpoint_path, result)
            raise

        except Exception as exc:
            logger.error(f"Crawl error for {mfr}: {exc}")
            prog.status = "failed"
            prog.errors += 1
            result.total_errors += 1
        else:
            prog.status = "done"
            result.manufacturers_done += 1

        prog.finished_at = _utcnow_iso()
        result.per_manufacturer[mfr] = prog

        if verbose:
            print(
                f"  {mfr}: {prog.imported} imported, "
                f"{prog.skipped_dup} dups, "
                f"{prog.skipped_filter} filtered, "
                f"{prog.errors} errors"
            )

        # Save checkpoint after every manufacturer
        _save_checkpoint(checkpoint_path, result)

    result.finished_at = _utcnow_iso()
    _save_checkpoint(checkpoint_path, result)
    return result


# ══════════════════════════════════════════════════════════════════
# CHECKPOINT STATUS DISPLAY
# ══════════════════════════════════════════════════════════════════


def print_checkpoint_status(checkpoint_path: str = DEFAULT_CHECKPOINT) -> None:
    """Print a human-readable summary of the current checkpoint file."""
    result = _load_checkpoint(checkpoint_path)
    if result is None:
        print(f"  No checkpoint found at: {checkpoint_path}")
        return

    print(f"\n  Bulk scrape checkpoint: {checkpoint_path}")
    print(f"  Started  : {result.started_at}")
    print(
        f"  Progress : {result.manufacturers_done}/{result.manufacturers_total} manufacturers done"
    )
    print(f"  Imported : {result.total_imported}")
    print(f"  Dup skip : {result.total_skipped_dup}")
    print(f"  Filtered : {result.total_skipped_filter}")
    print(f"  Errors   : {result.total_errors}")
    print()
    print(
        f"  {'Manufacturer':<22} {'Status':<12} {'Imported':>8} {'Dups':>6} {'Errors':>7}"
    )
    print(f"  {'─' * 22} {'─' * 12} {'─' * 8} {'─' * 6} {'─' * 7}")
    for mfr, mp in result.per_manufacturer.items():
        status_sym = {"done": "✓", "failed": "✗", "in_progress": "…"}.get(
            mp.status, "?"
        )
        print(
            f"  {mfr:<22} {status_sym} {mp.status:<10} "
            f"{mp.imported:>8} {mp.skipped_dup:>6} {mp.errors:>7}"
        )
