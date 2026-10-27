# ADR-0007: Rust physics core — Python resolves, Rust integrates

**Status:** Accepted. Supersedes [ADR-0003](0003-no-numba-jit.md) in part
(the "loop stays plain Python" conclusion; the Numba rejection stands) and the
Pyodide plan for in-browser full simulations in
[CLIENT_COMPUTE.md](../CLIENT_COMPUTE.md).
**Date:** 2026-10-24 (core built 2026-10-23; wired into production paths
2026-10-24)
**Deciders:** Hritwik Mudhai + maintaining agents

## Context

One quarter-mile run of `MotoQuantEngine.run()` costs 430–650 ms of pure
Python, depending on how busy the host is. Every product surface multiplies
that:

- The API runs on a 0.5-CPU free-tier instance.
- The build optimizer, autotune and outlaw pipeline each orchestrate hundreds
  of runs.
- The tuning and benchmark sweeps (`phys_weighted_sweep`, `tune_cluster_knobs`,
  surrogate regeneration) run thousands, and the planned accuracy epoch needs
  many such sweeps.

Two earlier decisions blocked the obvious fixes:

- **ADR-0003** rejected JIT-compiling the loop. Rewriting it for Numba would
  void the bit-identical baseline pin
  ([ADR-0002](0002-pinned-reference-baselines.md)). Its re-open criterion is
  "a prototype that demonstrates a JIT path producing bit-identical baselines
  AND a measured end-to-end win on a real workload".
- **CLIENT_COMPUTE.md** rejected a JS port of the engine: a second
  implementation would have to track the baseline forever. For browser full
  sims it planned Pyodide instead (the unmodified Python engine on WebAssembly,
  about 15 MB, expected 3–10× slower than native Python). The go/no-go harness
  for that plan never ran.

## Decision

**The integration loop also exists as one Rust crate (`rust/motoquant-core`),
compiled to two targets. It is used for every production simulation when it
is installed, current and bit-exact on the host.** `motoquant/physics.py`
remains the reference implementation.

- **Python resolves, Rust integrates.** `motoquant/native.py::resolve_engine`
  builds a real `MotoQuantEngine` and serialises every value the loop reads
  *after* category dispatch, environment corrections, tire-grip scaling, gear
  ratios, shift points and effective-mass terms. The result is a plain JSON
  config, schema-versioned on both sides. Rust ports only the loop and the
  per-step sub-model math. Policy (profiles, defaults, parts, venues, knobs)
  never needs a Rust change.
- **Two targets from one source.**
  - A PyO3 abi3 extension (`motoquant_core`, built with `make native` and
    compiled into the Docker image).
  - A raw-C-ABI wasm32 module (`web/public/engine/motoquant_core.wasm`, about
    94 KB gzip), loaded by `web/lib/engine.js`.
- **One selector.** `motoquant/engine_select.py` is the only place that
  decides which engine runs. `MOTOQUANT_ENGINE` takes three values:
  - `auto` (the default): native when the extension imports, its schema
    matches, it is not stale and the host math probe is exact; otherwise
    Python.
  - `python`: the kill switch, no rebuild needed.
  - `native`: require the Rust core, and raise if it is missing or stale.
  - Any other value falls back to `python` with a one-time warning;
    `/api/health` reports `mode: "invalid"` and the error.

  Every API simulation route uses it (simulate, quick incl. its stock
  baseline, top speed, distance, compare, the Dragy overlay), as do the
  jobs, the chat agent, the NL runner and the MCP local backend.
  `NativeEngine` subclasses `MotoQuantEngine` and overrides only `run()`, so
  `run_top_speed()` / `run_distance()` post-processing stays Python's own
  code. `/api/health` reports the live engine and, when `auto` fell back,
  why.

## Evidence

- **Parity:** `scripts/check_native_parity.py`, the full default sweep,
  2026-10-24, schema 2. It passed 1,894/1,894 cases with worst |ΔET| = 0 s.
  Every SimResult channel was compared element by element, along with sample
  counts, the final `dt` and every split. The cases were:
  - every catalog bike (541) with fixed dt;
  - every catalog bike with adaptive dt;
  - every catalog bike in top-speed mode;
  - the three references in each mode;
  - 262 stress variants: forced induction, every clutch type, every
    surface, wind, gradient, limiters, every category profile, dt
    variants, configs edited after construction, reused engines, and every
    error path.

  The only channel differences were the 9 cases where both engines raise
  (they have no channels to compare).
- **Browser:** the committed wasm reproduces ET, trap, every split, the
  sample count, the loop step count and the final `dt` exactly on all 53
  fixture cases (`node web/scripts/engine-parity.mjs`) and on all 1,082
  catalog runs (`scripts/gen_engine_web.py --full-catalog`, 2026-10-24).
  Force-type channels can carry 1-ULP noise because wasm uses Rust's libm,
  not glibc. That noise never reached a reported time.
- **Speed** (same sweep, serial, 23 bikes): Python takes 652 ms per sim.
  Native takes 13.6 ms end to end (resolve, run, numpy conversion), which is
  48× faster; the loop alone takes 8.5 ms, 77× faster. The earlier,
  less-loaded run measured 429 ms vs 8.9 / 5.1 ms (48× / 83×). Wasm under
  node: about 5–16 ms per sim depending on the host.
- **Deployment:** the multi-stage Docker build was run for real on
  2026-10-24 (both with and without the wheel). It compiles the wheel in a
  `python:3.11-slim-bookworm` builder, installs it in the runtime image and
  boots. `/api/health` then reports `"engine": "native"`. The pure-Python
  variant (`--build-arg MOTOQUANT_NATIVE=0`) boots with
  `"fallback_reason": "unavailable"` and identical numbers.

## Dual-implementation discipline

Two implementations of the same loop are only safe if any drift is caught
mechanically, before review. These gates enforce that:

1. **CI gate.** `.github/workflows/native.yml` is path-filtered on the Rust
   sources, `physics.py`, `submodels/`, `models.py`, `defaults.py`,
   `category_profiles.py`, `native.py`, `engine_select.py`, the browser engine
   and the parity tooling. It runs:
   - `cargo test` (native Rust vs the committed Python-reference fixtures);
   - a `maturin --locked` wheel build;
   - the pytest native gate with `MOTOQUANT_REQUIRE_NATIVE=1`, so a missing or
     stale build fails instead of skipping;
   - the quick parity sweep;
   - the node wasm parity.
2. **Schema version on both sides.** It is defined in
   `native.SCHEMA_VERSION` and `config.rs::SCHEMA_VERSION`, with
   `deny_unknown_fields` everywhere. A shape change that is not mirrored
   fails to deserialise; it never silently ignores a knob. The wasm exports
   `schema_version()`, and the tests read it from the binary itself.
3. **Source fingerprint.** `build.rs` stamps an FNV-1a hash of the crate's
   sources into both builds. `native.is_stale()` compares it with the
   checkout, and `auto` refuses a stale extension. The freshness test fails if
   the committed wasm was built from other sources.
4. **Fixture freshness.** `tests/test_native_engine.py` always runs, even
   without the extension. It fails when the committed fixtures no longer
   match today's Python ETs or `resolve_config` output.
5. **Same exception classes.** For the same input, native raises what Python
   raises (`ValueError` / `OverflowError` / `ZeroDivisionError` /
   `MemoryError`). (Until the 2026-10 epoch `distance <= 0` was the one
   documented difference: Python hit an accidental `UnboundLocalError`. Python
   now raises the same `ValueError`.)

**Rule for contributors:** a change to `MotoQuantEngine.run()` or to any
sub-model method it calls must port the same change to `engine.rs` in the
same PR. Then run `make native native-test wasm`, and `make native-parity`
for anything non-trivial. The regen contract table in
[RUST_CORE.md](../RUST_CORE.md) lists every case.

## Consequences

- **Positive.**
  - About 50× more simulations per CPU-second on the same instance.
  - Sweeps and tuning runs that took tens of minutes finish in seconds.
  - Exact full sims are possible in the browser at about 94 KB.
  - The bit-identical pin (ADR-0002) is preserved, not traded away.
- **Negative.**
  - Every physics-loop change costs a second port. This includes the planned
    accuracy epoch (dropping the phantom slip inertia, the 1-ft rollout, and
    so on).
  - Contributors touching the loop need a Rust toolchain.
  - The Docker build gains about 1–2 minutes (rustup plus a cargo LTO build).
  - Bit parity is *host-relative*: the native core reproduces the local
    Python bit for bit by calling the same libm and probing NumPy's `exp`
    dispatch. Two different machines can still differ from each other at
    the ULP level, exactly as two Python hosts already do.
- **Still rejected:**
  - **Numba.** It is a heavy dependency, and it cannot express the
    call-for-call libm/SVML semantics that parity needs.
  - **A hand-written JS port.** It would be a second policy implementation,
    not a single source compiled twice.
  - **Pyodide for full sims.** It costs about 15 MB and runs seconds per
    sim, against about 94 KB and milliseconds for the Rust engine. Its
    harness and manual workflow were deleted.

## Re-open criteria

Turn the Rust core off (`MOTOQUANT_ENGINE=python`) and reconsider this ADR in
either case:

- parity can no longer be kept on the CI host;
- maintaining the port blocks a needed accuracy epoch.

Python stays the reference throughout, so deleting `rust/` remains a
one-commit rollback.

## References

- `motoquant/native.py`, `motoquant/engine_select.py`, `rust/motoquant-core/`.
- [RUST_CORE.md](../RUST_CORE.md) (architecture, parity method, regen
  contract, limitations).
- `scripts/check_native_parity.py`, `.github/workflows/native.yml`.
- ADR-0002, ADR-0003, [CLIENT_COMPUTE.md](../CLIENT_COMPUTE.md).
