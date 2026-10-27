# ADR-0003: The RK4 hot loop stays plain Python — no Numba/JIT

**Status:** Accepted — **do not re-litigate without new measurements**.
**Superseded in part by [ADR-0007](0007-rust-physics-core.md) (2026-10-24):**
the re-open criteria below were met by a bit-identical Rust port of the loop,
which now serves production simulations. The rejection of *Numba* itself
still stands; "the loop stays plain Python" no longer does.
**Date:** 2026-07-03 (documented 2026-07-06)
**Deciders:** Hritwik Mudhai + maintaining agents

## Context

The simulation is an RK4 integrator stepping a 6-element state vector at 1 ms.
"JIT it with Numba `@njit`" is an obvious-looking speedup and gets proposed
repeatedly. It was investigated with measurements.

## Decision

**Do not JIT the physics loop with Numba.** The loop is object-access scalar
Python (it reaches into `cfg.engine`, `cfg.drivetrain`, sub-model objects,
`np.interp` on dyno curves) — not the tight numeric numpy kernel Numba
accelerates. Concretely:

- Numba would require rewriting the loop into `nopython`-compatible numeric code,
  which **voids the bit-identical baseline pin** (ADR-0002) — the single most
  expensive thing to give up.
- It adds a heavy dependency and ~60–90 MB to any packaged image.
- The measured wins that mattered came from ordinary Python refactors (dead-call
  elimination, closure removal, hoisting invariants, caching the slip-branch
  torque) — the "19% faster, bit-identical" pass — *without* changing a single
  result.

## Alternatives for speed (use these instead)

- **multiprocessing** for sweeps (already used — `mp.Pool` in the tuning/sweep
  scripts).
- **Adaptive timestep** (`run(use_adaptive_dt=True)`) where precision allows.
- **The surrogate model** (`artifacts/surrogate/`) — a learned cache of the
  physics for the optimizer's inner loop, which is the real latency win.

## Consequences

- **Positive.** Preserves the baseline pin; no new heavy dependency; the loop
  stays readable and debuggable.
- **Negative.** The pure-Python loop is slower per-sim than a JIT kernel would
  be. Accepted — parallelism + surrogate + adaptive-dt cover the real workloads.
- **Re-open criteria.** Only revisit with a prototype that demonstrates a JIT
  path producing **bit-identical** baselines AND a measured end-to-end win on a
  real workload (not a microbenchmark).

## References

- `motoquant/physics.py` (the loop) · `CLAUDE.md` (July 3 entry, the measured
  rejection) · ADR-0002.
