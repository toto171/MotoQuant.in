"""
MotoQuant Pro — Weather Scheduled Refresh
==========================================
Polls OpenWeatherMap for all active venues and stores fresh weather records.

Usage (standalone):
    python -m motoquant.database.weather_refresh --db motoquant.db --interval 60

Usage (CLI via run.py):
    python -m motoquant.run weather --refresh-all [--stale-minutes 60]

Design:
  - Only re-fetches a venue if its most recent record is older than
    `stale_minutes` (default: 60 min) to avoid unnecessary API calls.
  - API key read from OPENWEATHERMAP_API_KEY env var or --api-key flag.
  - Results logged and also stored as weather_records in DB.
  - Returns a RefreshSummary with per-venue status.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


@dataclass
class VenueRefreshStatus:
    venue_id: int
    venue_name: str
    status: str  # "refreshed" | "skipped_fresh" | "no_coords" | "api_error" | "no_key"
    record_id: int | None = None
    density_altitude_ft: float | None = None
    power_correction: float | None = None
    message: str = ""


@dataclass
class RefreshSummary:
    refreshed: int = 0
    skipped_fresh: int = 0
    no_coords: int = 0
    errors: int = 0
    venue_results: list[VenueRefreshStatus] = field(default_factory=list)
    run_at: str = ""

    def __post_init__(self):
        if not self.run_at:
            self.run_at = datetime.now(timezone.utc).isoformat()

    @property
    def total_venues(self) -> int:
        return len(self.venue_results)

    def __str__(self):
        lines = [
            f"Weather Refresh  [{self.run_at[:19]}]",
            f"  Refreshed:     {self.refreshed}",
            f"  Skipped fresh: {self.skipped_fresh}",
            f"  No coords:     {self.no_coords}",
            f"  API errors:    {self.errors}",
        ]
        for v in self.venue_results:
            icon = {
                "refreshed": "✓",
                "skipped_fresh": "—",
                "no_coords": "?",
                "api_error": "✗",
                "no_key": "✗",
            }.get(v.status, "·")
            detail = ""
            if v.density_altitude_ft is not None:
                detail = (
                    f"  DA={v.density_altitude_ft:.0f}ft  PCF={v.power_correction:.4f}"
                )
            lines.append(f"  {icon} [{v.venue_id}] {v.venue_name}: {v.status}{detail}")
        return "\n".join(lines)


def _is_stale(latest_record: dict | None, stale_minutes: int) -> bool:
    """Return True if the record is older than stale_minutes (or missing)."""
    if latest_record is None:
        return True
    try:
        recorded_str = latest_record.get("recorded_at", "")
        if not recorded_str:
            return True
        # Parse ISO 8601; handle both +00:00 and Z suffixes
        recorded_str = recorded_str.replace("Z", "+00:00")
        try:
            recorded_at = datetime.fromisoformat(recorded_str)
        except ValueError:
            # Fallback: strip timezone for naive comparison
            recorded_at = datetime.fromisoformat(recorded_str[:19])
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age = now - recorded_at.astimezone(timezone.utc)
        return age > timedelta(minutes=stale_minutes)
    except Exception:
        return True  # conservative: treat unparseable records as stale


def refresh_all_venues(
    db,
    api_key: str = None,
    stale_minutes: int = 60,
    venue_ids: list[int] = None,
) -> RefreshSummary:
    """
    Poll OpenWeatherMap for all active venues and store fresh weather records.

    Args:
        db:             MotoQuantDB instance (must be connected + initialized)
        api_key:        OpenWeatherMap API key (falls back to env var)
        stale_minutes:  Skip venues whose last record is newer than this (default: 60)
        venue_ids:      If provided, only refresh these specific venue IDs

    Returns:
        RefreshSummary with per-venue status and aggregate counts.
    """
    if api_key is None:
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")

    summary = RefreshSummary()

    # Fetch all venues (or specific subset)
    if venue_ids:
        venues = [db.venues.get(vid) for vid in venue_ids]
        venues = [v for v in venues if v is not None]
    else:
        venues = db.venues.list_all()

    if not venues:
        logger.warning("No venues found — nothing to refresh")
        return summary

    for venue in venues:
        vid = venue["id"]
        vname = venue.get("name", f"venue_{vid}")
        lat = venue.get("latitude")
        lon = venue.get("longitude")

        # Skip venues without coordinates
        if lat is None or lon is None:
            logger.debug(f"Venue {vname}: no coordinates, skipping")
            status = VenueRefreshStatus(
                venue_id=vid,
                venue_name=vname,
                status="no_coords",
                message="No latitude/longitude configured",
            )
            summary.venue_results.append(status)
            summary.no_coords += 1
            continue

        # Check staleness
        latest = db.weather.latest(vid)
        if not _is_stale(latest, stale_minutes):
            age_min = 0
            if latest and latest.get("recorded_at"):
                try:
                    recorded_str = latest["recorded_at"].replace("Z", "+00:00")
                    try:
                        recorded_at = datetime.fromisoformat(recorded_str)
                    except ValueError:
                        recorded_at = datetime.fromisoformat(recorded_str[:19])
                        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
                    age_min = int(
                        (
                            datetime.now(timezone.utc)
                            - recorded_at.astimezone(timezone.utc)
                        ).total_seconds()
                        / 60
                    )
                except Exception:
                    pass
            logger.debug(f"Venue {vname}: data fresh ({age_min}min old), skipping")
            status = VenueRefreshStatus(
                venue_id=vid,
                venue_name=vname,
                status="skipped_fresh",
                message=f"Last record {age_min}min ago (< {stale_minutes}min threshold)",
            )
            summary.venue_results.append(status)
            summary.skipped_fresh += 1
            continue

        # No API key — can't fetch
        if not api_key:
            logger.warning(f"Venue {vname}: no API key, skipping")
            status = VenueRefreshStatus(
                venue_id=vid,
                venue_name=vname,
                status="no_key",
                message="OPENWEATHERMAP_API_KEY not set",
            )
            summary.venue_results.append(status)
            summary.errors += 1
            continue

        # Fetch from OWM
        logger.info(f"Refreshing weather for {vname} (lat={lat:.3f}, lon={lon:.3f})")
        try:
            record_id = db.weather.fetch_live(
                venue_id=vid,
                api_key=api_key,
            )
            if record_id is not None:
                wr = db.weather.get(record_id)
                status = VenueRefreshStatus(
                    venue_id=vid,
                    venue_name=vname,
                    status="refreshed",
                    record_id=record_id,
                    density_altitude_ft=wr.get("density_altitude_ft"),
                    power_correction=wr.get("power_correction_factor"),
                    message=f"DA={wr.get('density_altitude_ft', 0):.0f}ft",
                )
                summary.venue_results.append(status)
                summary.refreshed += 1
                logger.info(
                    f"  {vname}: DA={wr.get('density_altitude_ft', 0):.0f}ft, "
                    f"PCF={wr.get('power_correction_factor', 1):.4f}"
                )
            else:
                raise RuntimeError("fetch_live returned None")
        except Exception as e:
            logger.error(f"  {vname}: fetch failed — {e}")
            status = VenueRefreshStatus(
                venue_id=vid,
                venue_name=vname,
                status="api_error",
                message=str(e),
            )
            summary.venue_results.append(status)
            summary.errors += 1

    return summary


# ────────────────────────────────────────────────────────────────────
# Standalone entry point  (python -m motoquant.database.weather_refresh)
# ────────────────────────────────────────────────────────────────────


def _main():
    import argparse

    from ..database import MotoQuantDB

    parser = argparse.ArgumentParser(
        prog="weather_refresh",
        description="Poll OpenWeatherMap for all MotoQuant venues and store results.",
    )
    parser.add_argument(
        "--db",
        default="motoquant.db",
        help="Path to MotoQuant DB (default: motoquant.db)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenWeatherMap API key (or set OPENWEATHERMAP_API_KEY env var)",
    )
    parser.add_argument(
        "--stale-minutes",
        type=int,
        default=60,
        help="Skip venues with data newer than N minutes (default: 60)",
    )
    parser.add_argument(
        "--venue-ids", type=int, nargs="+", help="Only refresh specific venue IDs"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s  %(message)s",
    )

    db = MotoQuantDB(args.db)
    db.initialize()

    summary = refresh_all_venues(
        db=db,
        api_key=args.api_key,
        stale_minutes=args.stale_minutes,
        venue_ids=args.venue_ids,
    )
    print(str(summary))
    db.close()


if __name__ == "__main__":
    _main()
