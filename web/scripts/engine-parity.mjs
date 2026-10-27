/**
 * Parity harness: proves web/lib/engine.js (the Rust core compiled to
 * wasm32) reproduces the Python reference physics (motoquant/physics.py).
 *
 * Run:  node web/scripts/engine-parity.mjs [fixture.json] [--wasm PATH]
 * Defaults: fixture = rust/fixtures/engine_parity.json (written by
 * scripts/gen_engine_web.py), wasm = web/public/engine/motoquant_core.wasm.
 *
 * The REAL module is exercised end to end (fetch → instantiate → schema check
 * → alloc/simulate/dealloc → result decode) by shimming global fetch to serve
 * the wasm from disk. For every case it FAILS on:
 *   - |dET|, |dtrap| or any split / max_distance / elapsed time drifting by
 *     more than the fixture tolerance (1e-9 s),
 *   - a different sample count, loop step count or final dt (exact),
 *   - a different `finished` flag or a fixture/engine schema mismatch,
 * and it reports — without failing on — per-channel bit identity (sha256 of
 * the float64 bytes): the wasm build uses Rust's pure-Rust libm (not glibc)
 * for pow/sin, so ULP-level noise in force-type channels is possible and is
 * measured honestly here (docs/RUST_CORE.md, "wasm32 parity").
 * Exits 0 on pass, 1 on any violation.
 */

import { createHash } from 'node:crypto';
import { readFileSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = resolve(webRoot, '..');
const args = process.argv.slice(2);
const wasmIdx = args.indexOf('--wasm');
const wasmPath = wasmIdx >= 0 ? resolve(args[wasmIdx + 1]) : join(webRoot, 'public', 'engine', 'motoquant_core.wasm');
const positional = args.filter((a, i) => !a.startsWith('--') && (wasmIdx < 0 || i !== wasmIdx + 1));
const fixturePath = positional.length ? resolve(positional[0]) : join(repoRoot, 'rust', 'fixtures', 'engine_parity.json');

const fetched = [];
globalThis.fetch = async (url) => {
  if (!String(url).endsWith('.wasm')) throw new Error(`unexpected fetch ${url}`);
  fetched.push(String(url));
  const buf = readFileSync(wasmPath);
  return {
    ok: true,
    status: 200,
    headers: { get: () => 'application/octet-stream' },
    arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength),
  };
};

const { simulate, loadEngine, ENGINE_SCHEMA } = await import(join(webRoot, 'lib', 'engine.js'));

const fixture = JSON.parse(readFileSync(fixturePath, 'utf-8'));
const TOL = fixture.tolerance_s ?? 1e-9;
if (fixture.schema !== ENGINE_SCHEMA) {
  console.error(`FAIL: fixture schema ${fixture.schema} != engine.js schema ${ENGINE_SCHEMA} — run \`make wasm\``);
  process.exit(1);
}
const SPLIT_KEYS = [
  'time_60ft', 'speed_60ft', 'time_330ft', 'speed_330ft', 'time_eighth', 'speed_eighth',
  'time_1000ft', 'speed_1000ft', 'time_quarter', 'speed_quarter', 'max_distance_m', 'elapsed_time_s',
];
const CH_OUT = {
  t: 't', x: 'x', v: 'v', a: 'a', rpm: 'rpm', slip: 'slip', traction_pct: 'tractionPct',
  N_front: 'nFront', N_rear: 'nRear', F_drive: 'fDrive', F_drag: 'fDrag', F_rr: 'fRr',
  T_tire: 'tTire', T_clutch: 'tClutch', P_boost: 'pBoost', power_kw: 'powerKw', r_eff: 'rEff',
};

function sha(arr) {
  const b = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength);
  return createHash('sha256').update(b).digest('hex');
}

// Loader self-check: the engine cache is keyed by URL — concurrent loads of
// two different URLs must fetch both and return distinct engines, and a
// repeat load of the same URL must be served from cache (2026-10-24: a
// single shared promise used to hand b.wasm callers the a.wasm engine).
{
  const [a, b] = await Promise.all([loadEngine('/engine/selfcheck-a.wasm'), loadEngine('/engine/selfcheck-b.wasm')]);
  const again = await loadEngine('/engine/selfcheck-a.wasm');
  const okCache =
    a !== b && a.url === '/engine/selfcheck-a.wasm' && b.url === '/engine/selfcheck-b.wasm' && again === a &&
    fetched.filter((u) => u.includes('selfcheck-')).length === 2;
  if (!okCache) {
    console.error(`FAIL loadEngine cache: fetched=${JSON.stringify(fetched)} a=${a.url} b=${b.url}`);
    process.exit(1);
  }
}

await loadEngine();
let worstEt = 0;
let worstTrap = 0;
let worstSplit = 0;
let failures = 0;
let bitCases = 0;
let simMs = 0;
const chanMismatch = {};
for (const c of fixture.cases) {
  const r = await simulate(c.config, {
    distance: c.request.distance,
    maxTime: c.request.max_time,
    adaptive: c.request.adaptive,
    rolloutM: c.request.rollout_m,
  });
  simMs += r.elapsedMs;
  const e = c.expected;
  const dEt = Math.abs(r.splits.time_quarter - e.time_quarter);
  const dTrap = Math.abs(r.splits.speed_quarter - e.speed_quarter);
  let dSplit = 0;
  let worstSplitKey = '';
  for (const k of SPLIT_KEYS) {
    // NaN-safe: a missing/non-numeric split must count as drift, not pass.
    const d = Math.abs(r.splits[k] - e[k]);
    const dd = Number.isNaN(d) ? Infinity : d;
    if (dd > dSplit) {
      dSplit = dd;
      worstSplitKey = k;
    }
  }
  worstEt = Math.max(worstEt, dEt);
  worstTrap = Math.max(worstTrap, dTrap);
  worstSplit = Math.max(worstSplit, dSplit);
  let allBits = r.n === e.n;
  const mism = [];
  for (const [py, js] of Object.entries(CH_OUT)) {
    if (sha(r.channels[js]) !== e.channel_sha256[py]) {
      allBits = false;
      mism.push(py);
      chanMismatch[py] = (chanMismatch[py] || 0) + 1;
    }
  }
  if (sha(r.gear) !== e.channel_sha256.gear) {
    allBits = false;
    mism.push('gear');
  }
  if (allBits) bitCases++;
  const stepsOk = e.steps === undefined ? false : r.steps === e.steps;
  const bad =
    !(dEt <= TOL && dTrap <= TOL && dSplit <= TOL) ||
    r.n !== e.n ||
    !stepsOk ||
    r.dt !== e.dt ||
    r.finished !== e.finished_quarter;
  if (bad) {
    failures++;
    console.error(
      `FAIL ${c.label}: dET=${dEt.toExponential(3)} dtrap=${dTrap.toExponential(3)} ` +
        `dsplit=${dSplit.toExponential(3)}${worstSplitKey ? ` (${worstSplitKey})` : ''} n=${r.n}/${e.n} ` +
        `steps=${r.steps}/${e.steps} dt=${r.dt}/${e.dt} finished=${r.finished}/${e.finished_quarter}`,
    );
  } else if (mism.length) {
    console.log(`  note ${c.label}: channel bits differ in [${mism.join(', ')}] (dET=${dEt.toExponential(2)})`);
  }
}
const raw = statSync(wasmPath).size;
const gz = gzipSync(readFileSync(wasmPath), { level: 9 }).length;
console.log(
  `engine-parity: ${fixture.cases.length - failures}/${fixture.cases.length} cases ok | ` +
    `worst |dET| ${worstEt.toExponential(3)} s | worst |dtrap| ${worstTrap.toExponential(3)} m/s | ` +
    `worst split ${worstSplit.toExponential(3)} | channel-bit-identical ${bitCases}/${fixture.cases.length} | ` +
    `wasm ${raw} B (${gz} B gzip) | mean sim ${(simMs / fixture.cases.length).toFixed(2)} ms`,
);
if (Object.keys(chanMismatch).length) console.log('  channel mismatch counts:', JSON.stringify(chanMismatch));
process.exit(failures ? 1 : 0);
