/**
 * Parity harness: proves web/lib/surrogate.js reproduces the SERVER surrogate
 * pipeline (db_row_to_config → slider overrides → config_to_feature_vector →
 * NumpySurrogate.predict) to numerical noise.
 *
 * Run:  node web/scripts/surrogate-parity.mjs <fixture.json> [--assets web/public/surrogate]
 * The fixture is produced by tests/test_surrogate_web_export.py (Python is the
 * reference implementation). Exits 0 on pass, 1 with the worst offenders on fail.
 *
 * The real module is exercised end-to-end — loader, fingerprint check,
 * envelope, transforms, forward pass — by shimming global fetch to serve the
 * exported JSON from disk.
 */

import { readFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
if (!args.length) {
  console.error('usage: node surrogate-parity.mjs <fixture.json> [--assets DIR]');
  process.exit(2);
}
const fixturePath = resolve(args[0]);
const assetsIdx = args.indexOf('--assets');
const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const assetsDir = assetsIdx >= 0 ? resolve(args[assetsIdx + 1]) : join(webRoot, 'public', 'surrogate');

// Serve /surrogate/*.json from disk through the module's own fetch calls.
globalThis.fetch = async (url) => {
  const name = String(url).split('/').pop();
  const body = readFileSync(join(assetsDir, name), 'utf-8');
  return { ok: true, json: async () => JSON.parse(body) };
};

const { predictQuick } = await import(join(webRoot, 'lib', 'surrogate.js'));

const fixture = JSON.parse(readFileSync(fixturePath, 'utf-8'));
const TOL_S = fixture.tolerance_s ?? 1e-9;

let worst = { et: 0, trap: 0, caseIdx: -1 };
let failures = 0;
let refusals = 0;

for (let i = 0; i < fixture.cases.length; i++) {
  const c = fixture.cases[i];
  const r = await predictQuick({
    bikeId: c.bike_id,
    riderMassKg: c.rider_mass_kg,
    powerBoostPct: c.power_boost_pct,
    massDeltaKg: c.mass_delta_kg,
    venueId: c.venue_id ?? null,
  });
  if (c.expect_refusal) {
    if (r.ok) {
      console.error(`case ${i}: expected refusal (${c.expect_refusal}) but got a prediction`);
      failures++;
    } else {
      refusals++;
    }
    continue;
  }
  if (!r.ok) {
    console.error(`case ${i}: unexpected refusal '${r.reason}' (bike ${c.bike_id})`);
    failures++;
    continue;
  }
  const dEt = Math.abs(r.etS - c.expected_et_s);
  const dTrap = Math.abs(r.trapKmh - c.expected_trap_kmh);
  if (dEt > worst.et) worst = { et: dEt, trap: dTrap, caseIdx: i };
  if (dEt > TOL_S || dTrap > TOL_S * 3.6) {
    if (failures < 10) {
      console.error(
        `case ${i} (bike ${c.bike_id}): ΔET=${dEt.toExponential(3)}s ` +
          `ΔTrap=${dTrap.toExponential(3)}km/h exceeds tol ${TOL_S}`
      );
    }
    failures++;
  }
}

const n = fixture.cases.length;
console.log(
  `surrogate-parity: ${n - failures}/${n} cases within ${TOL_S}s ` +
    `(${refusals} expected refusals honoured; worst ΔET=${worst.et.toExponential(3)}s at case ${worst.caseIdx})`
);
process.exit(failures ? 1 : 0);
