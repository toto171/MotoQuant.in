# Client-Side Compute — using the rider's hardware to scale

> Written 2026-08-11 (commercial-launch readiness). Operator directive: move
> quick sims — and eventually main sims — onto the user's device so the
> 0.5-CPU Render instance stops being the scaling bottleneck.

## What runs where (the contract)

| Computation | Where | Why |
|---|---|---|
| Live/quick estimates (slider drags) | **Browser** — `web/lib/surrogate.js` | Shipped 2026-08-11. Zero server cost, ~0.01 ms, proven equal to the server surrogate to <1e-9 s |
| Exact quarter-mile (splits, timeseries) | **Server** (RK4) | The authoritative number; the Run button |
| Full sims in-browser (future) | **Browser** — Pyodide/WASM, gated on CI proof | See "Main sims" below |
| Build Optimizer / Autotune / Outlaw | **Server only, pro-gated** | The paid product — never shipped to the client |
| Leaderboard saves | **Server only** | Estimated results can never be saved (enforced in the simulator page) |

## Tier 1 — the in-browser surrogate (SHIPPED)

The shipped numpy surrogate (`artifacts/surrogate/surrogate_numpy.npz`, a
26→128→64→2 ReLU MLP) is exported to two static assets by
`scripts/gen_surrogate_web.py`:

- `web/public/surrogate/model.json` (~63 KB) — weights/norms/envelope as
  base64 float32 buffers (bit-exact transport, no decimal-string loss)
- `web/public/surrogate/bikes.json` (~272 KB) — per-bike base features from
  the SAME `db_row_to_config` path the API serves, + venue altitudes

`web/lib/surrogate.js` replicates the server inference pipeline exactly
(float64 feature math → `Math.fround` per feature, mirroring the float32 cast
in `config_to_feature_vector` → float64 MLP forward pass) and **refuses
rather than guesses** — parts/tire overrides, non-default weather, envelope
violations, and load failures all fall back to the server route.

**Proof, not hope:** `tests/test_surrogate_web_export.py` +
`web/scripts/surrogate-parity.mjs` run the real JS module (via a fetch shim)
against reference values computed by the real server pipeline —
**677/677 cases within 1e-9 s, worst ΔET 7.1e-15 s** across the full
541-bike catalog plus randomized slider perturbations, with envelope
refusals honoured.

Honesty rules baked into the UI:
- every client number is labeled **instant estimate** with the surrogate's
  documented accuracy (±0.11 s typical vs the physics — see
  `artifacts/surrogate/README.md`)
- "Save this run" is never offered on an estimated result
- the funnel event stream tags `engine: 'client-surrogate' | 'server'` so
  conversion and load-shift are both measurable

**REGEN CONTRACT (extends the standing surrogate contract):** the web export
is a cache of the surrogate, which is a cache of the physics. After ANY
reseed/retune/surrogate regen, run `python scripts/gen_surrogate_web.py` in
the same session. The two JSON files carry the npz's sha256 and the JS
refuses a mismatched pair, so a forgotten regen degrades to server-only
(slow, correct) rather than serving stale numbers.

## Tier 2 — main sims in the browser (HARNESS SHIPPED, UI GATED ON PROOF)

The full RK4 engine's import surface is numpy + stdlib only (verified by
blocking every other import and reproducing all three pinned baselines to
<5e-11 s). That makes the **unmodified Python engine** runnable in the
browser via Pyodide — no JS port, no second implementation, no baseline
drift risk from a rewrite.

Two open questions gate the UI work, and both are answered by
`e2e/pyodide-mainsim-parity.mjs` (manual-trigger workflow
`.github/workflows/pyodide-parity.yml`):

1. **Numerics.** WASM float64 arithmetic is IEEE-exact but libm
   transcendentals can differ by 1 ulp from glibc. The harness runs the three
   pinned references inside WASM and asserts the same 1e-9 s tolerance
   `scripts/check_baselines.py` uses. The Claude sandbox cannot reach the
   Pyodide CDN (numpy wasm wheel), so the proof runs on Actions where egress
   is open — trigger it from the Actions tab.
2. **Speed.** Native full sim is ~320-380 ms; interpreted-Python-on-WASM is
   expected 3-10× slower. The harness reports wall-clock per sim so the UX
   call (acceptable for an explicit "run locally" action?) is made on real
   numbers.

If the harness passes: wire a lazy-loaded "run locally" path for the FREE
full-sim action (payload ~15 MB, cached; worth it for offline + zero server).
If it drifts: record the deltas here and stop — an "exact" number that
disagrees with the server by more than the baseline tolerance must not ship.

What client full sims deliberately do NOT change:
- **Leaderboard integrity** — saved runs stay server-authoritative. (Note:
  `/api/simulate/save` currently trusts the client-supplied ET — a documented,
  rate-limited beta posture. Client-side sims neither worsen nor fix that;
  the fix is server-side recomputation at save time, tracked separately.)
- **The paid tier** — Optimizer/Autotune/Outlaw orchestrate hundreds of sims
  plus the knapsack/ROI machinery server-side and stay pro-gated. Shipping
  the engine for single free sims does not ship the analysis product.

## Rejected alternatives (do not re-litigate without new facts)

- **JS/Dart port of the RK4 engine** — a second implementation of 15
  submodels that must track the bit-identical baseline contract forever;
  every divergence is a credibility bug on the site's accuracy claims.
- **A mobile app for local compute** — reverses ADR-0005 (hosted-only)
  for a distribution bet that a PWA + this client-compute stack covers.
- **numpy-shim to run the engine on Pyodide-core without the CDN** — a
  hand-rolled mini-numpy with exact-float64 semantics is precisely the
  silent-numerical-drift risk this architecture exists to avoid.
