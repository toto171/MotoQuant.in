// Unit tests for the browser-only helpers behind saved runs and timeslips.
// Run (from web/): node --test scripts/*.test.mjs   (CI: .github/workflows/web-verify.yml)
//
// The modules use ES `export` syntax in .js files that Node would read as
// CommonJS, so each is loaded from its source text through a data: URL. They
// import nothing, which is what makes that possible; keep it that way.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

async function load(rel) {
  const src = readFileSync(new URL(rel, import.meta.url), 'utf8');
  return import('data:text/javascript;base64,' + Buffer.from(src).toString('base64'));
}

const runs = await load('../lib/runs.js');
const slip = await load('../lib/timeslip.js');

const ENV = {
  name: 'Aamby Valley Airstrip (TVR)',
  source: 'venue',
  altitude_m: 679,
  ambient_temp_c: 22.123456,
  track_temp_c: 30,
  humidity_pct: 40,
  pressure_hpa: 1013.25,
  headwind_kmh: 0,
  track_surface: 'asphalt',
};

test('a saved setup round-trips into the request that re-runs it', () => {
  const q = runs.timeslipQuery({
    bikeId: 3,
    venueId: 1,
    riderKg: 80,
    powerBoost: 10,
    massChange: -5,
    partIds: [48, 354],
    frontTireId: 2,
    rearTireId: 1,
    environment: ENV,
  });
  const body = runs.timeslipRequest(new URLSearchParams(q));
  assert.deepEqual(body, {
    bike_id: 3,
    venue_id: 1,
    front_tire_id: 2,
    rear_tire_id: 1,
    rider_mass_kg: 80,
    power_boost_pct: 10,
    mass_delta_kg: -5,
    altitude_m: 679,
    ambient_temp_c: 22.123456,
    track_temp_c: 30,
    humidity_pct: 40,
    pressure_hpa: 1013.25,
    part_ids: [48, 354],
  });
});

test('timeslip keys are the simulator share keys, so one query opens both', () => {
  const q = new URLSearchParams(
    runs.timeslipQuery({ bikeId: 7, riderKg: 75, environment: ENV }),
  );
  for (const key of ['bike', 'rider', 'temp', 'track', 'hum']) assert.ok(q.has(key), key);
});

test('a link without a valid bike gives no request', () => {
  assert.equal(runs.timeslipRequest(new URLSearchParams('')), null);
  assert.equal(runs.timeslipRequest(new URLSearchParams('bike=0')), null);
  assert.equal(runs.timeslipRequest(new URLSearchParams('bike=-3')), null);
  assert.equal(runs.timeslipRequest(new URLSearchParams('bike=1e3')), null);
});

test('values outside what the API accepts are dropped, not clamped', () => {
  const body = runs.timeslipRequest(
    new URLSearchParams('bike=3&boost=900&temp=-80&hum=101&pres=10&alt=abc&rider=75'),
  );
  assert.deepEqual(body, { bike_id: 3, rider_mass_kg: 75 });
});

test('part lists are de-duplicated, positive and capped at 30', () => {
  const ids = Array.from({ length: 40 }, (_, i) => i + 1);
  const body = runs.timeslipRequest(
    new URLSearchParams(`bike=3&parts=5,5,-1,x,${ids.join(',')}`),
  );
  assert.equal(body.part_ids.length, 30);
  assert.equal(body.part_ids[0], 5);
  assert.equal(new Set(body.part_ids).size, 30);
});

test('conditions read as one plain line', () => {
  assert.equal(
    slip.conditionsSummary(ENV),
    'Aamby Valley Airstrip (TVR) · 679 m · 22 °C air · 30 °C track · 40 % humidity',
  );
  assert.equal(
    slip.conditionsSummary({ ...ENV, source: 'manual', headwind_kmh: -12, track_surface: 'dry_lake_bed' }),
    '679 m · 22 °C air · 30 °C track · 40 % humidity · 12 km/h tailwind · dry lake bed',
  );
});

test('every change from stock is listed on the slip', () => {
  const lines = slip.changesFromStock(
    { power_boost_pct: 25, mass_delta_kg: -4, rider_mass_kg: 90 },
    {
      parts_applied: [{ id: 48, brand: 'Dynojet', name: 'Power Commander' }],
      tyres: [{ position: 'rear', id: 1, name: 'Michelin Power Cup 2 190/55ZR17' }],
    },
  );
  assert.deepEqual(lines, [
    'Engine power +25 %',
    'Bike weight −4 kg',
    'Rider 90 kg',
    'Dynojet Power Commander',
    'Rear tyre: Michelin Power Cup 2 190/55ZR17',
  ]);
  assert.deepEqual(slip.changesFromStock({ rider_mass_kg: 75 }, {}), []);
});
