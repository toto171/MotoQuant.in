"""
Tests for brake / suspension position-and-subtype exclusivity in the build
knapsack (roadmap A4-28).

Brakes and suspension are NOT single-slot like an exhaust: a valid brake build
runs front pads + rear pads + steel lines + a rotor together, and a valid
suspension build runs a fork mod + a rear shock together. What must be
prevented is two parts fighting for the SAME physical slot (two front-pad sets,
two rear rotors, two forks, two rear shocks).

These tests drive the group-key / selection helpers directly (no full optimize
sim needed) so they are fast and deterministic:

  * ``_brake_susp_slot``   — pure spec/name -> slot-key classifier.
  * ``_knapsack_group_key`` — the single choke point both knapsacks funnel
                              through for exclusivity.
  * ``_select_build``       — the multiple-choice knapsack, given a slot map.
"""

from motoquant.analysis.build_optimizer import _select_build
from motoquant.analysis.roi import (
    EXCLUSIVE_CATEGORIES,
    PartROIResult,
    _brake_susp_slot,
    _brake_susp_slots,
    _knapsack_group_key,
)


def _mk(pid, cat, price=5000, det=0.05, dtrap=1.0):
    """Synthetic PartROIResult (same shape as test_build_optimizer._mk)."""
    return PartROIResult(
        part_id=pid,
        part_name=f"P{pid}",
        brand="B",
        category=cat,
        category_display=cat,
        price_inr=float(price),
        price_usd=None,
        base_et_s=10.0,
        modified_et_s=10.0 - det,
        delta_et_s=float(det),
        delta_trap_ms=float(dtrap),
        roi_score=(det / max(price, 1) * 1e5),
        cost_per_tenth_inr=(price / (det * 10) if det > 0 else float("inf")),
        is_compatible=True,
        availability="in_stock",
        is_free=(price == 0),
    )


# ─────────────────────────── classifier (pure) ───────────────────────────
class TestBrakeSuspClassifier:
    def test_brake_pad_position_from_specs(self):
        assert (
            _brake_susp_slot("brakes", {"type": "brake_pads", "position": "front"}, "X")
            == "brakes:pad:front"
        )
        assert (
            _brake_susp_slot("brakes", {"type": "pad", "position": "rear"}, "X")
            == "brakes:pad:rear"
        )

    def test_brake_position_from_name_fallback(self):
        # No position in specs — must fall back to the name regex.
        slot = _brake_susp_slot(
            "brakes",
            {"type": "brake_pads"},
            "EBC HH Sintered Brake Pads Front Yamaha R15 V4 (155cc)",
        )
        assert slot == "brakes:pad:front"

    def test_brake_subtype_from_name_when_type_unknown(self):
        slot = _brake_susp_slot(
            "brakes", {"type": "mystery"}, "HEL Braided Steel Lines Rear"
        )
        assert slot == "brakes:line:rear"

    def test_brake_front_rear_is_its_own_slot(self):
        assert (
            _brake_susp_slot("brakes", {"type": "pad", "position": "front_rear"}, "X")
            == "brakes:pad:front_rear"
        )

    def test_brake_unknown_position_is_non_exclusive(self):
        # A rotor with no position in specs and no front/rear in the name can't
        # be confidently placed -> None (non-exclusive).
        assert (
            _brake_susp_slot(
                "brakes",
                {"type": "brake_rotor"},
                "Bybre Sintered Brake Rotors 330mm Suzuki Hayabusa (1299cc)",
            )
            is None
        )

    def test_brake_generic_component_is_non_exclusive(self):
        assert _brake_susp_slot("brakes", {"type": "brake_component"}, "M4 V4") is None
        assert _brake_susp_slot("brakes", {"type": "fluid"}, "DOT-4 Fluid") is None

    def test_suspension_fork_and_shock(self):
        assert (
            _brake_susp_slot("suspension", {"type": "fork"}, "X") == "suspension:fork"
        )
        assert (
            _brake_susp_slot("suspension", {"type": "fork_internals"}, "X")
            == "suspension:fork"
        )
        assert (
            _brake_susp_slot("suspension", {"type": "rear_shock"}, "X")
            == "suspension:shock"
        )
        assert (
            _brake_susp_slot("suspension", {"type": "monoshock"}, "X")
            == "suspension:shock"
        )

    def test_suspension_ambiguous_is_non_exclusive(self):
        assert _brake_susp_slot("suspension", {"type": "spring_kit"}, "X") is None
        assert _brake_susp_slot("suspension", {"type": "coilover"}, "X") is None
        assert _brake_susp_slot("suspension", {"type": "lowering_kit"}, "X") is None

    def test_non_brake_susp_category_returns_none(self):
        assert _brake_susp_slot("exhaust", {"type": "full_system"}, "X") is None

    def test_never_raises_on_junk_input(self):
        assert _brake_susp_slot(None, None, None) is None
        assert _brake_susp_slot("brakes", "not-a-dict", 12345) is None


# ─────────────────────────── group key ───────────────────────────
class TestKnapsackGroupKey:
    def test_two_front_pads_share_a_group(self):
        a, b = _mk(1, "brakes"), _mk(2, "brakes")
        slot_of = {1: "brakes:pad:front", 2: "brakes:pad:front"}
        assert _knapsack_group_key(a, slot_of=slot_of) == _knapsack_group_key(
            b, slot_of=slot_of
        )

    def test_front_and_rear_pad_are_different_groups(self):
        a, b = _mk(1, "brakes"), _mk(2, "brakes")
        slot_of = {1: "brakes:pad:front", 2: "brakes:pad:rear"}
        assert _knapsack_group_key(a, slot_of=slot_of) != _knapsack_group_key(
            b, slot_of=slot_of
        )

    def test_pad_and_rotor_same_position_are_different_groups(self):
        # front pad and front rotor are complementary (different physical part).
        a, b = _mk(1, "brakes"), _mk(2, "brakes")
        slot_of = {1: "brakes:pad:front", 2: "brakes:rotor:front"}
        assert _knapsack_group_key(a, slot_of=slot_of) != _knapsack_group_key(
            b, slot_of=slot_of
        )

    def test_two_forks_share_a_group(self):
        a, b = _mk(1, "suspension"), _mk(2, "suspension")
        slot_of = {1: "suspension:fork", 2: "suspension:fork"}
        assert _knapsack_group_key(a, slot_of=slot_of) == _knapsack_group_key(
            b, slot_of=slot_of
        )

    def test_fork_and_shock_are_different_groups(self):
        a, b = _mk(1, "suspension"), _mk(2, "suspension")
        slot_of = {1: "suspension:fork", 2: "suspension:shock"}
        assert _knapsack_group_key(a, slot_of=slot_of) != _knapsack_group_key(
            b, slot_of=slot_of
        )

    def test_unclassified_part_is_own_singleton_group(self):
        a, b = _mk(1, "brakes"), _mk(2, "brakes")
        # Neither id is in slot_of -> each gets its own solo group.
        ka = _knapsack_group_key(a, slot_of={})
        kb = _knapsack_group_key(b, slot_of={})
        assert ka != kb
        assert ka == ("__solo__", 1)
        assert kb == ("__solo__", 2)

    def test_brakes_suspension_not_in_exclusive_categories(self):
        # Guard: these must stay OUT of the blunt whole-category lock, else a
        # front + rear pad build would be wrongly forbidden.
        assert "brakes" not in EXCLUSIVE_CATEGORIES
        assert "suspension" not in EXCLUSIVE_CATEGORIES


# ─────────────────────────── selection (knapsack) ───────────────────────────
class TestSelectBuildBrakeSusp:
    def test_two_front_pads_cannot_both_be_selected(self):
        pool = [
            _mk(1, "brakes", 4000, 0.04),
            _mk(2, "brakes", 4500, 0.06),  # better ET
        ]
        slot_of = {1: "brakes:pad:front", 2: "brakes:pad:front"}
        sel = _select_build(pool, 100_000, "min_et", slot_of=slot_of)
        ids = {r.part_id for r in sel}
        assert len(ids) == 1, f"two front pads stacked: {ids}"
        assert ids == {2}, "should keep the better front pad"

    def test_front_rear_pads_coexist(self):
        pool = [
            _mk(1, "brakes", 4000, 0.04),
            _mk(2, "brakes", 4500, 0.05),
        ]
        slot_of = {1: "brakes:pad:front", 2: "brakes:pad:rear"}
        sel = _select_build(pool, 100_000, "min_et", slot_of=slot_of)
        assert {r.part_id for r in sel} == {1, 2}, "complementary pads dropped"

    def test_fork_and_shock_coexist_but_two_forks_do_not(self):
        pool = [
            _mk(1, "suspension", 30_000, 0.05),  # fork A
            _mk(2, "suspension", 32_000, 0.07),  # fork B (better)
            _mk(3, "suspension", 25_000, 0.04),  # rear shock
        ]
        slot_of = {
            1: "suspension:fork",
            2: "suspension:fork",
            3: "suspension:shock",
        }
        sel = _select_build(pool, 500_000, "min_et", slot_of=slot_of)
        ids = {r.part_id for r in sel}
        forks = [r.part_id for r in sel if slot_of[r.part_id] == "suspension:fork"]
        assert len(forks) == 1, f"two forks stacked: {forks}"
        assert forks == [2], "should keep the better fork"
        assert 3 in ids, "rear shock (complementary slot) should coexist"

    def test_unclassified_parts_are_freely_selectable(self):
        # No slot_of entries -> both are solo groups -> both selectable.
        pool = [
            _mk(1, "brakes", 3000, 0.03),
            _mk(2, "suspension", 3000, 0.03),
        ]
        sel = _select_build(pool, 100_000, "min_et", slot_of={})
        assert {r.part_id for r in sel} == {1, 2}


# ─────────────────────────── repo helper ───────────────────────────
class _FakeRepo:
    """Minimal parts_repo stub exposing .get(pid)."""

    def __init__(self, rows):
        self._rows = {r["id"]: r for r in rows}

    def get(self, pid):
        return self._rows.get(pid)


class TestBrakeSuspSlotsRepo:
    def test_repo_scan_builds_slot_map(self):
        repo = _FakeRepo(
            [
                {
                    "id": 1,
                    "category_name": "brakes",
                    "model_name": "Front pads",
                    "specifications": {"type": "brake_pads", "position": "front"},
                },
                {
                    "id": 2,
                    "category_name": "brakes",
                    "model_name": "Rear pads",
                    "specifications": '{"type": "brake_pads", "position": "rear"}',
                },
                {
                    "id": 3,
                    "category_name": "suspension",
                    "model_name": "Ohlins Fork",
                    "specifications": {"type": "fork"},
                },
                {
                    "id": 4,
                    "category_name": "brakes",
                    "model_name": "Generic component",
                    "specifications": {"type": "brake_component"},
                },
                {
                    "id": 5,
                    "category_name": "exhaust",  # ignored
                    "model_name": "Akrapovic",
                    "specifications": {"type": "full_system"},
                },
            ]
        )
        out = _brake_susp_slots(repo, [1, 2, 3, 4, 5, 999])
        assert out == {
            1: "brakes:pad:front",
            2: "brakes:pad:rear",  # parsed from a JSON string spec
            3: "suspension:fork",
        }
        assert 4 not in out  # unclassifiable -> omitted (non-exclusive)
        assert 5 not in out  # non-brake/susp category ignored

    def test_repo_without_get_returns_empty(self):
        assert _brake_susp_slots(object(), [1, 2, 3]) == {}
