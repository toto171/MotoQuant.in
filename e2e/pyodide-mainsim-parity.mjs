/**
 * Pyodide main-sim parity harness — the go/no-go proof for running the REAL
 * RK4 physics engine (unmodified Python) in the browser via WebAssembly.
 * ======================================================================
 * Boots the Pyodide runtime from node_modules, loads the numpy wasm wheel
 * (Pyodide CDN — reachable from GitHub Actions; NOT from the Claude sandbox,
 * which is why this lives behind a manual-trigger workflow instead of being
 * asserted locally), mounts the repo's motoquant/ package unmodified, and
 * runs the three pinned reference bikes.
 *
 * PASS = all three ETs within 1e-9 s of the pinned baselines (the same
 * tolerance scripts/check_baselines.py enforces). WASM float64 arithmetic is
 * IEEE-exact, but libm transcendentals (exp/sin/atan) may differ from glibc
 * by 1 ulp — if that accumulates past 1e-9 across ~10k RK4 steps, this
 * harness reports the actual deltas and the client-full-sim decision gets
 * made on real numbers instead of hope.
 *
 * Also reports wall-clock per sim — the second go/no-go input (native is
 * ~320 ms; interpreted-Python-on-WASM is expected 3-10× slower, which still
 * beats a Render cold start).
 *
 * Run (CI or any machine with open egress):
 *     cd e2e && npm i pyodide && node pyodide-mainsim-parity.mjs
 */

import { loadPyodide } from 'pyodide';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');

// Pinned references — keep in lockstep with scripts/check_baselines.py.
// (Deliberately restated here rather than parsed out of the Python: this
// harness must fail loudly if either side moves without the other.)
const BASELINES = [
  ['gsxr1000_k5', 9.9330563825],
  ['yzfr1_4c8', 10.1435897157],
  ['hayabusa_gen1', 10.3633450813],
];
const TOL_S = 1e-9;

console.log('[pyodide-parity] booting Pyodide runtime …');
const t0 = Date.now();
const pyodide = await loadPyodide();
console.log(`[pyodide-parity] runtime up in ${Date.now() - t0} ms (${pyodide.version})`);

console.log('[pyodide-parity] loading numpy wasm wheel …');
const t1 = Date.now();
await pyodide.loadPackage('numpy');
console.log(`[pyodide-parity] numpy loaded in ${Date.now() - t1} ms`);

// Mount the real repo tree read-only inside the WASM FS — the engine source
// is used byte-identical, no copies, no build step.
pyodide.FS.mkdir('/repo');
pyodide.FS.mount(pyodide.FS.filesystems.NODEFS, { root: REPO }, '/repo');

const results = await pyodide.runPythonAsync(`
import json, sys, time
sys.path.insert(0, "/repo")

# Import the physics core directly — motoquant/__init__ may pull optional
# server-side deps; defaults+physics need only numpy + stdlib (verified by
# the import-graph audit of 2026-08-11).
from motoquant import defaults
from motoquant.physics import MotoQuantEngine

out = []
for preset in ${JSON.stringify(BASELINES.map(([name]) => name))}:
    cfg = getattr(defaults, preset)()
    t = time.time()
    sim = MotoQuantEngine(cfg).run()
    out.append({
        "preset": preset,
        "et_s": float(sim.time_quarter),
        "wall_ms": round((time.time() - t) * 1000),
    })
json.dumps(out)
`);

let failures = 0;
for (const r of JSON.parse(results)) {
  const [, pinned] = BASELINES.find(([n]) => n === r.preset);
  const delta = Math.abs(r.et_s - pinned);
  const ok = delta <= TOL_S;
  if (!ok) failures++;
  console.log(
    `[pyodide-parity] ${r.preset.padEnd(14)} wasm=${r.et_s.toFixed(10)} ` +
      `pinned=${pinned.toFixed(10)} Δ=${delta.toExponential(2)} ` +
      `(${r.wall_ms} ms) ${ok ? 'OK' : 'DRIFT'}`
  );
}

if (failures) {
  console.error(
    `[pyodide-parity] ${failures}/3 baselines drifted beyond ${TOL_S}s — ` +
      'client-side full sims would NOT be numerically interchangeable with ' +
      'the server. Do not wire the UI path; record the deltas above in the ' +
      'client-compute decision doc.'
  );
  process.exit(1);
}
console.log(
  '[pyodide-parity] PASS — the unmodified engine is numerically ' +
    'interchangeable with the server inside WASM. Client-side full sims are GO.'
);
