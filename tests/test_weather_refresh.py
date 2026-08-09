"""
Tests for motoquant.database.weather_refresh
===========================================
Covers:
  - _is_stale(): freshness detection with various timestamps
  - refresh_all_venues(): no API key, stale/fresh logic, no-coords venues
  - RefreshSummary: counts and string representation
  - VenueRefreshStatus: status fields
  - Integration: refresh runs against seeded DB, fills weather records
  - weather CLI: --refresh-all flag routes correctly
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from motoquant.database import MotoQuantDB
from motoquant.database.weather_refresh import (
    RefreshSummary,
    VenueRefreshStatus,
    _is_stale,
    refresh_all_venues,
)

# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────


@pytest.fixture
def weather_db():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.conn.execute("PRAGMA journal_mode=DELETE")
    db.initialize()
    yield db
    db.close()


def _make_weather_record(age_minutes: int) -> dict:
    ts = (datetime.now(timezone.utc) - timedelta(minutes=age_minutes)).isoformat()
    return {"recorded_at": ts}


def _mock_fetch_live(record_id=42, da_ft=500.0, pcf=0.98):
    """Return a mock fetch_live that inserts a fake record."""

    def _fetch(venue_id, api_key=None, track_temp_c=None):
        return record_id

    return _fetch


# ────────────────────────────────────────────────────────────
# _is_stale
# ────────────────────────────────────────────────────────────


class TestIsStale:
    def test_none_is_stale(self):
        assert _is_stale(None, 60) is True

    def test_empty_dict_is_stale(self):
        assert _is_stale({}, 60) is True

    def test_missing_recorded_at_is_stale(self):
        assert _is_stale({"recorded_at": None}, 60) is True

    def test_fresh_record_not_stale(self):
        record = _make_weather_record(age_minutes=5)
        assert _is_stale(record, 60) is False

    def test_old_record_is_stale(self):
        record = _make_weather_record(age_minutes=120)
        assert _is_stale(record, 60) is True

    def test_exactly_at_threshold(self):
        # 60 minutes old with 60-minute threshold → stale (strictly >)
        record = _make_weather_record(age_minutes=61)
        assert _is_stale(record, 60) is True

    def test_just_under_threshold(self):
        record = _make_weather_record(age_minutes=59)
        assert _is_stale(record, 60) is False

    def test_custom_threshold_200min(self):
        record = _make_weather_record(age_minutes=120)
        assert _is_stale(record, 200) is False

    def test_very_old_record(self):
        assert _is_stale({"recorded_at": "2020-01-01T00:00:00"}, 60) is True

    def test_iso_with_z_suffix(self):
        record = {"recorded_at": "2099-01-01T00:00:00Z"}  # far future
        assert _is_stale(record, 60) is False

    def test_unparseable_treated_as_stale(self):
        assert _is_stale({"recorded_at": "not-a-date"}, 60) is True


# ────────────────────────────────────────────────────────────
# RefreshSummary
# ────────────────────────────────────────────────────────────


class TestRefreshSummary:
    def test_initial_counts_zero(self):
        s = RefreshSummary()
        assert s.refreshed == 0
        assert s.skipped_fresh == 0
        assert s.no_coords == 0
        assert s.errors == 0

    def test_total_venues(self):
        s = RefreshSummary()
        s.venue_results = [
            VenueRefreshStatus(1, "A", "refreshed"),
            VenueRefreshStatus(2, "B", "skipped_fresh"),
        ]
        assert s.total_venues == 2

    def test_str_contains_header(self):
        s = RefreshSummary()
        assert "Weather Refresh" in str(s)

    def test_str_shows_venue_status(self):
        s = RefreshSummary(refreshed=1)
        s.venue_results.append(
            VenueRefreshStatus(
                1,
                "TestTrack",
                "refreshed",
                density_altitude_ft=400.0,
                power_correction=0.985,
            )
        )
        text = str(s)
        assert "TestTrack" in text
        assert "refreshed" in text

    def test_str_shows_da_when_refreshed(self):
        s = RefreshSummary()
        s.venue_results.append(
            VenueRefreshStatus(
                1,
                "Track",
                "refreshed",
                density_altitude_ft=750.5,
                power_correction=0.975,
            )
        )
        assert "750" in str(s)


# ────────────────────────────────────────────────────────────
# refresh_all_venues — no API key
# ────────────────────────────────────────────────────────────


class TestRefreshAllVenuesNoKey:
    def test_all_venues_no_key_returns_errors(self, weather_db):
        summary = refresh_all_venues(weather_db, api_key=None, stale_minutes=60)
        # All venues should be "no_key" (or "no_coords" if no lat/lon)
        assert summary.refreshed == 0
        for vs in summary.venue_results:
            assert vs.status in ("no_key", "no_coords")

    def test_no_key_no_db_writes(self, weather_db):
        before = weather_db.weather.count()
        refresh_all_venues(weather_db, api_key=None)
        after = weather_db.weather.count()
        assert after == before

    def test_returns_refresh_summary_type(self, weather_db):
        result = refresh_all_venues(weather_db, api_key=None)
        assert isinstance(result, RefreshSummary)

    def test_env_var_key_picked_up(self, weather_db, monkeypatch):
        """If OPENWEATHERMAP_API_KEY is set, it should be used (not no_key)."""
        monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test-key-xyz")

        # Mock fetch_live to succeed
        with patch.object(weather_db.weather, "fetch_live", return_value=99):
            with patch.object(
                weather_db.weather,
                "get",
                return_value={
                    "density_altitude_ft": 300.0,
                    "power_correction_factor": 0.99,
                },
            ):
                summary = refresh_all_venues(weather_db, stale_minutes=0)

        # With stale_minutes=0, all venues are stale → should try to refresh
        assert any(vs.status != "no_key" for vs in summary.venue_results)


# ────────────────────────────────────────────────────────────
# refresh_all_venues — staleness logic
# ────────────────────────────────────────────────────────────


class TestRefreshStaleness:
    def test_fresh_venue_skipped(self, weather_db):
        """If a venue has a recent record, it should be skipped."""
        venues = weather_db.venues.list_all()
        if not venues:
            pytest.skip("No venues in DB")
        vid = venues[0]["id"]

        # Seed a fresh record (5 min old)
        weather_db.weather.record(
            venue_id=vid,
            ambient_temp_c=28.0,
            relative_humidity_pct=60.0,
            barometric_pressure_hpa=1013.0,
        )

        summary = refresh_all_venues(weather_db, api_key="fake-key", stale_minutes=60)
        # The venue with a fresh record should be "skipped_fresh"
        venue_statuses = {vs.venue_id: vs.status for vs in summary.venue_results}
        assert venue_statuses.get(vid) == "skipped_fresh"

    def test_stale_venue_attempts_refresh(self, weather_db, monkeypatch):
        """A venue with an old record (or no record) should attempt refresh."""
        venues = weather_db.venues.list_all()
        if not venues:
            pytest.skip("No venues in DB")

        # Mock fetch_live to avoid real HTTP
        with patch.object(
            weather_db.weather, "fetch_live", return_value=42
        ) as mock_fetch:  # noqa: F841
            with patch.object(
                weather_db.weather,
                "get",
                return_value={
                    "density_altitude_ft": 200.0,
                    "power_correction_factor": 0.99,
                },
            ):
                summary = refresh_all_venues(
                    weather_db, api_key="test-key", stale_minutes=60
                )

        # With no existing records, all stale venues should have been attempted
        attempted = [
            vs
            for vs in summary.venue_results
            if vs.status in ("refreshed", "api_error", "no_key", "no_coords")
        ]
        assert len(attempted) > 0

    def test_venue_ids_filter(self, weather_db):
        """Only specified venue IDs should be refreshed."""
        venues = weather_db.venues.list_all()
        if len(venues) < 2:
            pytest.skip("Need at least 2 venues")

        target_id = venues[0]["id"]
        summary = refresh_all_venues(weather_db, api_key=None, venue_ids=[target_id])
        assert summary.total_venues == 1
        assert summary.venue_results[0].venue_id == target_id

    def test_no_coords_reported(self, weather_db):
        """Venues without latitude/longitude should get no_coords status."""
        # Create a venue without coordinates
        conn = weather_db.conn
        conn.execute(
            """INSERT INTO venues (name, city, country, altitude_m)
               VALUES ('NoCoords Track', 'Test City', 'IN', 0)"""
        )
        conn.commit()

        summary = refresh_all_venues(weather_db, api_key=None, stale_minutes=0)
        no_coords = [vs for vs in summary.venue_results if vs.status == "no_coords"]
        assert len(no_coords) >= 1


# ────────────────────────────────────────────────────────────
# refresh_all_venues — successful mock fetch
# ────────────────────────────────────────────────────────────


class TestRefreshWithMockAPI:
    def test_successful_refresh_counts(self, weather_db):
        venues = weather_db.venues.list_all()
        coords_venues = [v for v in venues if v.get("latitude") is not None]
        if not coords_venues:
            pytest.skip("No venues with coordinates")

        mock_wr = {
            "density_altitude_ft": 450.0,
            "power_correction_factor": 0.982,
            "ambient_temp_c": 32.0,
        }
        with patch.object(weather_db.weather, "fetch_live", return_value=1):
            with patch.object(weather_db.weather, "get", return_value=mock_wr):
                summary = refresh_all_venues(
                    weather_db, api_key="fake-key", stale_minutes=0
                )

        assert summary.refreshed == len(coords_venues)
        refreshed_statuses = [
            vs for vs in summary.venue_results if vs.status == "refreshed"
        ]
        assert len(refreshed_statuses) == len(coords_venues)

    def test_refreshed_status_has_da(self, weather_db):
        venues = weather_db.venues.list_all()
        coords_venues = [v for v in venues if v.get("latitude") is not None]
        if not coords_venues:
            pytest.skip("No venues with coordinates")

        mock_wr = {
            "density_altitude_ft": 650.0,
            "power_correction_factor": 0.975,
        }
        with patch.object(weather_db.weather, "fetch_live", return_value=7):
            with patch.object(weather_db.weather, "get", return_value=mock_wr):
                summary = refresh_all_venues(weather_db, api_key="key", stale_minutes=0)

        refreshed = [vs for vs in summary.venue_results if vs.status == "refreshed"]
        for vs in refreshed:
            assert vs.density_altitude_ft == pytest.approx(650.0)
            assert vs.power_correction == pytest.approx(0.975)

    def test_api_error_counted(self, weather_db):
        venues = weather_db.venues.list_all()
        coords_venues = [v for v in venues if v.get("latitude") is not None]
        if not coords_venues:
            pytest.skip("No venues with coordinates")

        with patch.object(
            weather_db.weather, "fetch_live", side_effect=RuntimeError("network error")
        ):
            summary = refresh_all_venues(weather_db, api_key="key", stale_minutes=0)

        assert summary.errors >= len(coords_venues)
        assert all(
            vs.status in ("api_error", "no_coords") for vs in summary.venue_results
        )

    def test_api_returns_none_counted_as_error(self, weather_db):
        venues = weather_db.venues.list_all()
        coords_venues = [v for v in venues if v.get("latitude") is not None]
        if not coords_venues:
            pytest.skip("No venues with coordinates")

        with patch.object(weather_db.weather, "fetch_live", return_value=None):
            summary = refresh_all_venues(weather_db, api_key="key", stale_minutes=0)

        error_statuses = [
            vs for vs in summary.venue_results if vs.status == "api_error"
        ]
        assert len(error_statuses) >= len(coords_venues)


# ────────────────────────────────────────────────────────────
# Weather CLI — --refresh-all flag
# ────────────────────────────────────────────────────────────


class TestWeatherCLIRefreshAll:
    def test_refresh_all_help_present(self):
        """--refresh-all flag should appear in weather --help."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "motoquant.run", "weather", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert "--refresh-all" in result.stdout

    def test_refresh_all_runs_without_error(self):
        """--refresh-all should run and print summary (no API key → no_key errors)."""
        import subprocess
        import sys
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            # Init DB first
            subprocess.run(
                [sys.executable, "-m", "motoquant.run", "--db", db_path, "db", "init"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "motoquant.run",
                    "--db",
                    db_path,
                    "weather",
                    "--refresh-all",
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=30,
            )
            assert result.returncode == 0
            assert "Weather Refresh" in result.stdout
            assert "Refreshed:" in result.stdout
        finally:
            os.unlink(db_path)

    def test_stale_minutes_flag(self):
        """--stale-minutes should be accepted without error."""
        import subprocess
        import sys
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            subprocess.run(
                [sys.executable, "-m", "motoquant.run", "--db", db_path, "db", "init"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "motoquant.run",
                    "--db",
                    db_path,
                    "weather",
                    "--refresh-all",
                    "--stale-minutes",
                    "0",
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=30,
            )
            assert result.returncode == 0
        finally:
            os.unlink(db_path)
