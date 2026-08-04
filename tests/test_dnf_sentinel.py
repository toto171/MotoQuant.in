"""Regression: a did-not-finish run must never rank as the fastest ET.

`SimResult.time_quarter` stays at its 0.0 default when a run never reaches the
quarter-mile (`finished_quarter` is the flag for exactly this). Every argmin /
sort consumer that read `time_quarter` raw therefore treated a DNF as an ET of
0.0 s — the global minimum — so:

  * `ecu_autotune`'s gearing + launch sweeps recommended whichever candidate
    failed to finish, reporting a nonsense `delta_et_s` (e.g. -25.691);
  * the chat agent's `compare_bikes` crowned the bike that DNF'd as `winner`;
  * `rank_bikes` sorted DNFs to the top of the "fastest" list.

All of it was reachable with fully API-legal inputs (a small-cc bike at high
altitude / heavy rider / strong headwind simply does not complete the quarter
inside the 26 s ceiling).

These tests drive the real production paths. Reverting `effective_et` (physics)
or its use in `roi._run_et` / `agent._sim_to_dict` / `agent._exec_rank_bikes`
turns them red.
"""

from __future__ import annotations

import unittest

from motoquant.analysis.roi import _run_et
from motoquant.defaults import gsxr1000_k5
from motoquant.physics import DNF_ET_SENTINEL_S, MotoQuantEngine, effective_et


def _dnf_config():
    """A config that provably cannot cover 402 m inside the sim window.

    Built by starving the engine rather than by using an exotic environment, so
    the test does not depend on venue/atmosphere tuning staying constant.
    """
    cfg = gsxr1000_k5()
    cfg.engine.peak_power_hp = 1.0
    cfg.engine.peak_torque_nm = 2.0
    if getattr(cfg.engine, "dyno_curve", None) is not None:
        cfg.engine.dyno_curve.torque_nm = [
            max(0.5, t * 0.01) for t in cfg.engine.dyno_curve.torque_nm
        ]
    cfg.chassis.dry_mass_kg += 400.0
    return cfg


class TestDnfSentinel(unittest.TestCase):
    def test_dnf_run_is_flagged_and_not_zero_et(self):
        sim = MotoQuantEngine(_dnf_config()).run()
        self.assertFalse(
            sim.finished_quarter,
            "fixture no longer produces a DNF — pick a harsher config",
        )
        # The raw field is the 0.0 sentinel; effective_et must not pass it through.
        self.assertEqual(sim.time_quarter, 0.0)
        self.assertEqual(effective_et(sim), DNF_ET_SENTINEL_S)

    def test_finished_run_passes_through_unchanged(self):
        sim = MotoQuantEngine(gsxr1000_k5()).run()
        self.assertTrue(sim.finished_quarter)
        # Bit-identical pass-through for the normal path — no rounding, no shift.
        self.assertEqual(effective_et(sim), sim.time_quarter)

    def test_dnf_sorts_slowest_not_fastest(self):
        """The actual bug: min()/sort over ET must not pick the DNF."""
        good = MotoQuantEngine(gsxr1000_k5()).run()
        bad = MotoQuantEngine(_dnf_config()).run()
        ranked = sorted([bad, good], key=effective_et)
        self.assertIs(ranked[0], good, "a did-not-finish ranked as fastest")

    def test_roi_run_et_reports_dnf_as_slow(self):
        """roi._run_et feeds ecu_autotune's gearing/launch argmin."""
        et_dnf, _ = _run_et(_dnf_config())
        et_ok, _ = _run_et(gsxr1000_k5())
        self.assertEqual(et_dnf, DNF_ET_SENTINEL_S)
        self.assertLess(et_ok, et_dnf, "finished run must beat a DNF on ET")


if __name__ == "__main__":
    unittest.main()
