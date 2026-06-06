"""Tests for recommended and drag_prep tire fitments."""

from motoquant.database.seed_recommended_fitments import RECOMMENDED_FITMENTS


def test_fitments_count():
    """At least 200 fitments defined."""
    assert len(RECOMMENDED_FITMENTS) >= 200


def test_fitments_distribution():
    """Check distribution by type."""
    rec = sum(1 for f in RECOMMENDED_FITMENTS if f["fitment_type"] == "recommended")
    drag = sum(1 for f in RECOMMENDED_FITMENTS if f["fitment_type"] == "drag_prep")
    assert rec >= 100, f"Need >=100 recommended, got {rec}"
    assert drag >= 50, f"Need >=50 drag_prep, got {drag}"


def test_fitment_structure():
    """All fitments have required fields."""
    for i, f in enumerate(RECOMMENDED_FITMENTS):
        assert all(
            k in f
            for k in ["bike_match", "position", "tire_match", "fitment_type", "notes"]
        ), f"Fitment {i} missing fields"
        assert f["position"] in ("front", "rear"), f"Fitment {i} bad position"
        assert f["fitment_type"] in ("recommended", "drag_prep"), (
            f"Fitment {i} bad type"
        )


if __name__ == "__main__":
    test_fitments_count()
    test_fitments_distribution()
    test_fitment_structure()
    print("All tests passed!")
