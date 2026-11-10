"""
Revert-sensitive pin for the July-13-2026 epoch's largest physics fix:
the **fixed-point traction cap** (`motoquant/physics.py`, the
``for _ in range(2):`` refinement loop inside the ``F_drive > F_max_tire``
branch).

Background
----------
Before the epoch the traction cap was computed in a single pass:

    a_est  = (F_drive - F_aero - F_rr) / m_eff      # UNCLAMPED demand
    N_f, N_r = weight_transfer(a_est, ...)          # ...so N_r is inflated
    F_max  = tire_max_force(N_r, ...)               # ...so the cap is inflated

On a traction-limited step the bike never actually achieves ``a_est`` — the
tire is the binding constraint — so feeding the *demand* acceleration into
weight transfer overstated rear load, which overstated the cap, which
under-penalised every low-grip surface (July-10 review item 2; wet K5 measured
+488 N mean rear load ≈ 46 % of static). The fix converges the
(capped accel → weight transfer → cap) triple with two extra passes.

Why this file exists
--------------------
`tests/test_physics_epoch_2026_07_13.py::TestSurfaceGripOrdering` only asserts
``wet > dry + 0.5`` — an ordering check that passes with **zero, one, two or
three** refinement passes. Deleting the refinement loop entirely leaves it
green. The audit of 2026-07-25 (§3.4) recorded this fix as having no
revert-sensitive test; these are it.

How the pins were calibrated (measured, not guessed)
----------------------------------------------------
The refinement count was varied in a scratch copy of the package (never in
the repo tree) and the wet K5 re-simulated at each setting. Re-measured
2026-11-05 on the 2026-10/11 accuracy-epoch physics (1-ft rollout timing,
combined-CoG wheelie limit, wheelie margin) — the July-13 numbers are kept
below for history:

    passes | wet K5 ET | wet-minus-dry | mean |ΔN_rear| on clipped steps t<1 s
    -------+-----------+---------------+----------------------------------------
       0   | 11.719726 |    1.676125   |  214.71 N   (no refinement at all)
       1   | 12.535033 |    2.491432   |   70.16 N
    >> 2 <<| 12.836945 |    2.793344   |   23.53 N   <- shipped
       3   | 12.937315 |    2.893714   |    8.29 N
       4   | 12.969589 |    2.925988   |    3.28 N

    (July 13, 2026 physics: 12.791355 / 14.364537 / 14.836859 / 14.953818 /
    14.981497 s; penalties 2.956 / 4.461 / 4.904 / 5.008 s; residuals 527 /
    125 / 30.5 / 7.4 / 1.8 N.)

Every pin below is a two-sided band that admits **only** the shipped two-pass
value. The nearest neighbour to the ET pin is 0.100 s away, so the ±0.01 s
tolerance carries ~10x margin — tight enough that removing, halving or
doubling the refinement fails, loose enough to survive platform float noise
(the repo's own baselines reproduce to 1e-9, so this is generous).

The dry path is re-checked here too. Pre-epoch the fix was not dry-neutral
(dry K5 read 9.9053 at one pass, 9.9460 at three). Since the 2026-10/11 epoch
the dry K5 launch is wheelie-limited rather than traction-limited, and the
dry ET is identical (10.043601 s) at every pass count 0-4 — the wet pins
carry this fix's evidence alone.
"""

from __future__ import annotations

import unittest

import numpy as np

import motoquant
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.physics import G

# ── Measured on the shipped two-pass engine ──────────────────────────────
WET_K5_ET_S = 12.836945059344155  # re-measured 2026-11-05 (was 14.8368585008)
WET_K5_ET_TOL_S = 0.01  # nearest neighbouring pass-count is 0.100 s away

DRY_K5_ET_S = 10.043600805570911  # == scripts/check_baselines.py

# wet-minus-dry penalty band: 0/1/3-pass values are 1.676 / 2.491 / 2.894 s
# (2-pass 2.793; 2026-11-05 — July-13 band was 4.70-4.95)
WET_PENALTY_MIN_S = 2.70
WET_PENALTY_MAX_S = 2.85

# mean |weight_transfer(a_recorded) - N_rear_recorded| over traction-limited
# steps in the first second. 0/1/3/4-pass values are 215 / 70 / 8.3 / 3.3 N
# (2-pass 23.5 N; 2026-11-05 — July 13: 527 / 125 / 7.4 / 1.8 N).
RESIDUAL_MIN_N = 15.0
RESIDUAL_MAX_N = 60.0

_TRACTION_LIMITED_PCT = 99.999  # traction_pct saturates at 100 when clipped


def _wet_k5():
    cfg = gsxr1000_k5()
    cfg.environment.track_surface = "wet"
    return cfg


class TestTractionCapConverged(unittest.TestCase):
    """Runs the production engine (`MotoQuantEngine.run`) — no re-implementation
    of the cap, no monkeypatching. Every assertion reads the engine's own
    recorded channels."""

    @classmethod
    def setUpClass(cls):
        cls.eng_wet = motoquant.MotoQuantEngine(_wet_k5())
        cls.wet = cls.eng_wet.run(max_time=26.0)
        cls.dry = motoquant.MotoQuantEngine(gsxr1000_k5()).run(max_time=26.0)

    # ── 1. the headline pin ──────────────────────────────────────────────
    def test_wet_k5_et_pinned_to_converged_cap(self):
        """The wet K5 ET admits only the two-pass cap.

        Reverting the refinement loop to a single pass reads 12.5350 s (30x
        the tolerance low); deleting it entirely reads 11.7197 s (112x low);
        a third pass reads 12.9373 s (10x high). (Measured 2026-11-05.)"""
        self.assertAlmostEqual(
            self.wet.time_quarter,
            WET_K5_ET_S,
            delta=WET_K5_ET_TOL_S,
            msg=(
                f"wet K5 ET {self.wet.time_quarter:.6f} s is outside the "
                f"converged-cap pin {WET_K5_ET_S:.6f} +/- {WET_K5_ET_TOL_S} — "
                "the fixed-point traction-cap refinement has changed"
            ),
        )

    # ── 2. comparative band: the low-grip penalty ────────────────────────
    def test_wet_penalty_sits_in_the_converged_band(self):
        """Same bike, same everything but ``track_surface``.

        The single-pass cap under-penalised low grip, so the wet-minus-dry
        penalty is only 2.491 s at one pass (1.676 s with no refinement at
        all); two passes cost 2.793 s (2026-11-05 physics; July 13: 4.461 /
        2.956 / 4.904 s). This is the band the audit's '46 % of static
        rear load' finding shows up in, expressed as time."""
        penalty = self.wet.time_quarter - self.dry.time_quarter
        self.assertGreater(
            penalty,
            WET_PENALTY_MIN_S,
            f"wet costs only {penalty:.4f} s vs dry — the traction cap is "
            "under-penalising low grip again (single-pass regression)",
        )
        self.assertLess(
            penalty,
            WET_PENALTY_MAX_S,
            f"wet costs {penalty:.4f} s vs dry — more than the converged "
            "two-pass cap produces (refinement depth increased)",
        )

    # ── 3. the mechanism itself, read off the engine's own channels ──────
    def test_recorded_rear_load_is_consistent_with_the_achieved_accel(self):
        """On a traction-limited step the recorded ``N_rear`` must be the one
        weight transfer produces from the acceleration the bike *achieved*,
        not from the unclamped demand.

        This is the fix stated as an invariant: feed the run's own recorded
        acceleration back through the production ``weight_transfer`` and the
        result must land on the recorded rear load. The single-pass code
        leaves a ~70 N gap here and the no-refinement code a ~215 N gap
        (2026-11-05; July 13: ~125 / ~527 N),
        because their ``N_rear`` belongs to an acceleration the bike never
        reached. Restricted to the first second so fuel burn (8 g/s ≈ 0.08 N)
        cannot contaminate the comparison."""
        r = self.wet
        sel = (r.traction_pct >= _TRACTION_LIMITED_PCT) & (r.t < 1.0)
        self.assertGreater(
            int(sel.sum()), 100, "expected a traction-limited launch on wet asphalt"
        )

        residuals = np.array(
            [
                abs(
                    self.eng_wet.weight_transfer(
                        float(r.a[i]) * G, float(r.v[i]), float(r.t[i])
                    )[1]
                    - float(r.N_rear[i])
                )
                for i in np.where(sel)[0]
            ]
        )
        mean_residual = float(residuals.mean())

        self.assertLess(
            mean_residual,
            RESIDUAL_MAX_N,
            f"mean |N_rear - weight_transfer(a_achieved)| = {mean_residual:.2f} N "
            "— rear load is being computed from the UNCLAMPED demand "
            "acceleration again (the pre-epoch single-pass cap)",
        )
        self.assertGreater(
            mean_residual,
            RESIDUAL_MIN_N,
            f"mean |N_rear - weight_transfer(a_achieved)| = {mean_residual:.2f} N "
            "— tighter than two refinement passes converge to; the refinement "
            "depth has increased, which moves the pinned baselines",
        )

    def test_low_grip_launch_is_actually_traction_limited(self):
        """Guards the premise of the tests above: if the wet launch stopped
        clipping, none of the assertions would be exercising the cap branch
        at all and they could pass vacuously."""
        clipped = float((self.wet.traction_pct >= _TRACTION_LIMITED_PCT).mean())
        self.assertGreater(
            clipped,
            0.5,
            f"only {clipped:.1%} of wet steps are traction-limited — the cap "
            "branch is barely entered, so these pins prove nothing",
        )

    # ── 4. the dry path must not move ────────────────────────────────────
    def test_dry_baselines_bit_identical(self):
        """`scripts/check_baselines.py` mirrored in-suite. The refinement is
        not dry-neutral (one pass reads 9.9032, three reads 9.9460 on the K5),
        so the pinned dry references are part of this fix's evidence — and no
        change here may move them."""
        for factory, target in (
            (gsxr1000_k5, DRY_K5_ET_S),
            (yzfr1_4c8, 10.10920982866053),
            (hayabusa_gen1, 10.110001443831809),
        ):
            et = motoquant.MotoQuantEngine(factory()).run().time_quarter
            self.assertAlmostEqual(
                et,
                target,
                delta=1e-9,
                msg=f"{factory.__name__} drifted: {et!r} vs {target!r}",
            )


if __name__ == "__main__":
    unittest.main()
