"""
Tests for tire fitment expansion (April 2026 — 267 bikes)
Verify that every bike in the catalog has OEM tire fitments.
"""

import json
import tempfile

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.database.seed import seed_all


class TestTireFitments:
    """Tire fitment tests."""

    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary test database."""
        path = tempfile.mktemp(suffix=".db")
        db = MotoQuantDB(path)
        db.initialize()
        seed_all(db)
        yield db
        # Cleanup
        import os

        if os.path.exists(path):
            os.remove(path)

    def test_tire_library_expansion(self, temp_db):
        """Verify that tire library has expanded to cover all new sizes."""
        cursor = temp_db._conn.execute("SELECT COUNT(*) FROM tire_models")
        total_tires = cursor.fetchone()[0]
        # Should have original ~31 + 63 new missing sizes = ~94 unique tires
        assert total_tires >= 90, f"Expected >=90 tires, got {total_tires}"

    def test_every_bike_has_front_fitments(self, temp_db):
        """Each seeded bike should have at least one front tire fitment."""
        cursor = temp_db._conn.execute(
            """
            SELECT COUNT(DISTINCT bm.id) as bikes_without_front
            FROM bike_models bm
            WHERE NOT EXISTS (
                SELECT 1 FROM bike_tire_fitments btf
                WHERE btf.bike_model_id = bm.id AND btf.position = 'front'
            )
            """
        )
        bikes_without = cursor.fetchone()[0]
        # Should be zero — all seeded bikes have front fitments
        assert bikes_without == 0, f"{bikes_without} bikes missing front fitments"

    def test_every_bike_has_rear_fitments(self, temp_db):
        """Each seeded bike should have at least one rear tire fitment."""
        cursor = temp_db._conn.execute(
            """
            SELECT COUNT(DISTINCT bm.id) as bikes_without_rear
            FROM bike_models bm
            WHERE NOT EXISTS (
                SELECT 1 FROM bike_tire_fitments btf
                WHERE btf.bike_model_id = bm.id AND btf.position = 'rear'
            )
            """
        )
        bikes_without = cursor.fetchone()[0]
        assert bikes_without == 0, f"{bikes_without} bikes missing rear fitments"

    def test_fitment_count_minimum(self, temp_db):
        """Verify we have fitments for all seeded bikes."""
        cursor = temp_db._conn.execute("SELECT COUNT(*) FROM bike_tire_fitments")
        total_fitments = cursor.fetchone()[0]
        # The default seed has 3 reference bikes = 6 fitments minimum (front+rear each)
        assert total_fitments >= 6, f"Expected >=6 fitments, got {total_fitments}"

    def test_fitment_oem_defaults(self, temp_db):
        """Every OEM fitment must be marked as the default tyre (is_default=1)
        so the simulator always has a sensible stock tyre to fall back on.

        The old assertion required OEM defaults to be >30% of *all* fitments.
        That proxy went stale once ``seed_all`` began calling
        ``seed_recommended_fitments`` (April 2026): the seed now adds
        recommended + drag_prep fitments, which are legitimately non-default,
        diluting the ratio below 30% even though every OEM fitment is still a
        default. This checks the real invariant instead of a brittle ratio."""
        oem_total = temp_db._conn.execute(
            "SELECT COUNT(*) FROM bike_tire_fitments WHERE fitment_type = 'oem'"
        ).fetchone()[0]
        oem_defaults = temp_db._conn.execute(
            "SELECT COUNT(*) FROM bike_tire_fitments "
            "WHERE fitment_type = 'oem' AND is_default = 1"
        ).fetchone()[0]
        assert oem_total > 0, "seed produced no OEM fitments"
        assert oem_defaults == oem_total, (
            f"{oem_total - oem_defaults} OEM fitment(s) not marked is_default=1"
        )

    def test_no_orphaned_fitments(self, temp_db):
        """Verify all fitments reference valid bikes and tires."""
        # Check bike references
        cursor = temp_db._conn.execute(
            """
            SELECT COUNT(*) FROM bike_tire_fitments btf
            WHERE NOT EXISTS (
                SELECT 1 FROM bike_models bm WHERE bm.id = btf.bike_model_id
            )
            """
        )
        orphaned_bikes = cursor.fetchone()[0]
        assert orphaned_bikes == 0, (
            f"{orphaned_bikes} fitments with invalid bike_model_id"
        )

        # Check tire references
        cursor = temp_db._conn.execute(
            """
            SELECT COUNT(*) FROM bike_tire_fitments btf
            WHERE NOT EXISTS (
                SELECT 1 FROM tire_models t WHERE t.id = btf.tire_model_id
            )
            """
        )
        orphaned_tires = cursor.fetchone()[0]
        assert orphaned_tires == 0, (
            f"{orphaned_tires} fitments with invalid tire_model_id"
        )

    def test_rim_sizes_covered(self, temp_db):
        """Verify tires are available for all rim sizes used in the catalog."""
        # Get all unique rim sizes from bike configs
        cursor = temp_db._conn.execute(
            """
            SELECT DISTINCT bc.tire_params FROM bike_configs bc
            WHERE bc.is_current = 1
            """
        )

        missing_rims = set()
        for row in cursor.fetchall():
            tire_params = json.loads(row[0])
            front_size = tire_params.get("front_size")
            rear_size = tire_params.get("rear_size")

            for size in [front_size, rear_size]:
                if not size:
                    continue
                # Extract rim diameter
                s = size.replace("ZR", "/").replace("R", "/").split("/")
                if len(s) >= 3:
                    try:
                        rim = int(s[2].split("-")[-1])
                    except (ValueError, IndexError):
                        continue
                else:
                    continue

                # Check if tire with this rim exists
                check = temp_db._conn.execute(
                    "SELECT COUNT(*) FROM tire_models WHERE rim_diameter_inch = ?",
                    (rim,),
                ).fetchone()[0]
                if check == 0:
                    missing_rims.add(f'{size} (rim {rim}")')

        assert len(missing_rims) == 0, f"Missing tires for rim sizes: {missing_rims}"

    def test_fitment_completeness_summary(self, temp_db):
        """Print a summary of fitment coverage."""
        # Count by position
        cursor = temp_db._conn.execute(
            "SELECT position, COUNT(*) FROM bike_tire_fitments GROUP BY position"
        )
        by_position = dict(cursor.fetchall())

        # Count by fitment type
        cursor = temp_db._conn.execute(
            "SELECT fitment_type, COUNT(*) FROM bike_tire_fitments GROUP BY fitment_type"
        )
        by_type = dict(cursor.fetchall())

        print("\nFitment summary:")
        print(f"  By position: {by_position}")
        print(f"  By type: {by_type}")

        total_bikes = temp_db._conn.execute(
            "SELECT COUNT(*) FROM bike_models"
        ).fetchone()[0]
        total_fitments = sum(by_position.values())
        print(f"  Total bikes: {total_bikes}")
        print(f"  Total fitments: {total_fitments}")
        print(f"  Average fitments/bike: {total_fitments / total_bikes:.1f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
