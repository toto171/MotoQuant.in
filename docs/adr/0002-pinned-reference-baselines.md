# ADR-0002: Reference baselines are pinned bit-identical

**Status:** Accepted
**Date:** 2026-07-06 (documenting a policy in force since the engine was validated)
**Deciders:** Hritwik Mudhai + maintaining agents

## Context

The physics engine's credibility rests on three hand-curated, human-validated
configs — GSX-R 1000 K5, YZF-R1 4C8, Hayabusa Gen1 — whose quarter-mile ETs were
tuned against real magazine/instrumented data. Everything else in the catalog is
derived from specs through `spec_to_bike_config`; these three are the fixed point
the model is trusted against.

The recurring risk: a "harmless" refactor (loop hoisting, closure elimination,
reordering) subtly changes a floating-point result, moving a baseline by
milliseconds. That is indistinguishable from a real physics regression and
erodes the one thing the model is validated against.

## Decision

**The three baselines are pinned bit-identical (Δ = 0.0000).** Any change that
perturbs them by even 1e-9 s is rejected as a regression — *unless* it is a
deliberate, evidence-backed accuracy improvement, in which case it must:
1. Ship the full weighted benchmark sweep (`scripts/phys_weighted_sweep.py`) as
   justification, and
2. Update the pinned values in `scripts/check_baselines.py`, `docs/INVARIANTS.md`,
   `AGENTS.md`, `CONTRIBUTING.md`, and the PR template — in the same PR.

Performance work must prove bit-identity (the "19% faster, bit-identical" pass is
the model: measure, refactor, prove Δ = 0.0000 on all three).

## Consequences

- **Positive.** Refactors are safe and reviewable — the guard is objective and
  automated (`make baselines`, CI job, `test_regression_snapshot.py`). A whole
  class of silent-drift bugs cannot merge.
- **Negative.** Some legitimate micro-optimisations that would change the last
  ULP are off-limits unless re-justified. This is an accepted cost — correctness
  of the validated reference outweighs a sub-millisecond speed gain.
- **Neutral.** Accuracy *is* allowed to improve; the pin is a change-control
  mechanism, not a freeze. It just forces the evidence to be on the table.

## References

- `scripts/check_baselines.py` (the executable guard)
- `docs/INVARIANTS.md` I1
- `.github/workflows/ci.yml` → "Physics baselines — bit-identical gate"
