// Unit tests for the browser-only helpers behind saved runs, timeslips and the
// chat assistant (lib/assistant.js).
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
    'Dynojet Power Commander',
    'Rear tyre: Michelin Power Cup 2 190/55ZR17',
  ]);
  // Rider weight is a condition, not a change to the bike.
  assert.deepEqual(slip.changesFromStock({ rider_mass_kg: 90 }, {}), []);
});

const contribute = await load('../lib/contribute.js');

test('a timeslip submission opens the issue form with the numbers filled in', () => {
  const url = new URL(
    contribute.timeslipIssueUrl({ bikeName: 'KTM Duke 390', bikeId: 12, et: 13.8456, trap: 151.24, sixty: 2.1 }),
  );
  assert.equal(url.origin + url.pathname, 'https://github.com/toto171/MotoQuant.in/issues/new');
  const q = url.searchParams;
  assert.equal(q.get('template'), 'submit-timeslip.yml');
  assert.equal(q.get('title'), 'Timeslip: KTM Duke 390 13.846 s');
  assert.equal(q.get('et'), '13.846');
  assert.equal(q.get('trap'), '151.2');
  assert.equal(q.get('sixty'), '2.100');
  assert.equal(q.get('catalog'), 'https://motoquant.in/bikes/12');
  assert.equal(q.has('eighth'), false);
});

test('every prefilled field exists in the issue form', () => {
  const form = readFileSync(
    new URL('../../.github/ISSUE_TEMPLATE/submit-timeslip.yml', import.meta.url),
    'utf8',
  );
  const ids = new Set([...form.matchAll(/^\s+id:\s*(\S+)/gm)].map((m) => m[1]));
  const url = new URL(
    contribute.timeslipIssueUrl({ bikeName: 'X', bikeId: 1, et: 10, trap: 200, sixty: 1.9, eighth: 6.5 }),
  );
  for (const key of url.searchParams.keys()) {
    if (key === 'template' || key === 'title') continue;
    assert.ok(ids.has(key), `issue form has no field "${key}"`);
  }
});

// ── Assistant choice and the visitor's own key (lib/assistant.js) ───────────

const assistant = await load('../lib/assistant.js');

function memoryStore() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
    has: (k) => m.has(k),
  };
}

function brokenStore() {
  const boom = () => {
    throw new Error('SecurityError');
  };
  return { getItem: boom, setItem: boom, removeItem: boom };
}

// Built at runtime so no key-shaped literal sits in the source.
const fakeKey = (tail = 'x') => ['sk', 'ant', 'test'].join('-') + '-' + tail.repeat(24);

test('the mechanic is the default, and only known assistants are kept', () => {
  const local = memoryStore();
  assert.equal(assistant.readAssistant(local), 'mechanic');
  assert.equal(assistant.readAssistant(null), 'mechanic');
  assert.equal(assistant.saveAssistant(local, 'doctor'), true);
  assert.equal(assistant.readAssistant(local), 'doctor');
  assert.equal(local.getItem('mq.assistant.v1'), 'doctor');
  local.setItem('mq.assistant.v1', 'claude-opus-5-5');
  assert.equal(assistant.readAssistant(local), 'mechanic');
  assert.deepEqual(
    assistant.ASSISTANTS.map((a) => a.label),
    ['1. The doctor', '2. The mechanic'],
  );
});

test('a key is checked the way the server checks it', () => {
  assert.equal(assistant.looksLikeAnthropicKey(fakeKey()), true);
  assert.equal(assistant.looksLikeAnthropicKey(`  ${fakeKey()}\n`), true);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-short'), false);
  assert.equal(assistant.looksLikeAnthropicKey(fakeKey().replace('sk-ant', 'sk-xyz')), false);
  assert.equal(assistant.looksLikeAnthropicKey(fakeKey().slice(0, 12) + ' ' + fakeKey().slice(12)), false);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-' + 'a'.repeat(300)), false);
  assert.equal(assistant.looksLikeAnthropicKey(undefined), false);
  // The server takes printable ASCII only (codes 33 to 126). A zero-width
  // space from a copy, or a Latin-1 letter, would be saved and then break
  // every question, so the browser refuses them too.
  const key = fakeKey();
  const zwsp = String.fromCharCode(0x200b);
  assert.equal(assistant.looksLikeAnthropicKey(key.slice(0, 12) + zwsp + key.slice(12)), false);
  assert.equal(assistant.looksLikeAnthropicKey(key + zwsp), false);
  assert.equal(assistant.looksLikeAnthropicKey(key.slice(0, -1) + String.fromCharCode(0xe9)), false);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-' + 'a'.repeat(13)), true);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-' + 'a'.repeat(12)), false);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-' + 'a'.repeat(293)), true);
  assert.equal(assistant.looksLikeAnthropicKey('sk-ant-' + 'a'.repeat(294)), false);
  assert.equal(assistant.saveKey({ local: memoryStore(), session: memoryStore() }, key + zwsp), false);
});

test('a key is kept for the session unless "Remember on this device" is ticked', () => {
  const stores = { local: memoryStore(), session: memoryStore() };
  const key = fakeKey();
  assert.equal(assistant.saveKey(stores, key, false), true);
  assert.equal(stores.session.getItem('mq.anthropic-key.v1'), key);
  assert.equal(stores.local.has('mq.anthropic-key.v1'), false);
  assert.deepEqual(assistant.readKey(stores), { key, remember: false });

  assert.equal(assistant.saveKey(stores, key, true), true);
  assert.equal(stores.local.getItem('mq.anthropic-key.v1'), key);
  assert.equal(stores.session.has('mq.anthropic-key.v1'), false);
  assert.deepEqual(assistant.readKey(stores), { key, remember: true });

  assert.equal(assistant.saveKey(stores, key, false), true);
  assert.equal(stores.local.has('mq.anthropic-key.v1'), false);
});

test('remove key clears both places, and a bad key is never stored', () => {
  const stores = { local: memoryStore(), session: memoryStore() };
  assistant.saveKey(stores, fakeKey('a'), true);
  stores.session.setItem('mq.anthropic-key.v1', fakeKey('b'));
  assistant.removeKey(stores);
  assert.deepEqual(assistant.readKey(stores), { key: '', remember: false });
  assert.equal(assistant.saveKey(stores, 'not a key', false), false);
  assert.equal(stores.session.has('mq.anthropic-key.v1'), false);
  stores.local.setItem('mq.anthropic-key.v1', 'garbage');
  assert.deepEqual(assistant.readKey(stores), { key: '', remember: false });
});

test('blocked storage never throws', () => {
  const stores = { local: brokenStore(), session: brokenStore() };
  assert.equal(assistant.readAssistant(stores.local), 'mechanic');
  assert.equal(assistant.saveAssistant(stores.local, 'doctor'), false);
  assert.deepEqual(assistant.readKey(stores), { key: '', remember: false });
  assert.equal(assistant.saveKey(stores, fakeKey(), true), false);
  assistant.removeKey(stores);
  assert.deepEqual(assistant.readKey({}), { key: '', remember: false });
});

test('the key header is sent only for a usable key', () => {
  const key = fakeKey();
  assert.deepEqual(assistant.keyHeaders(key), { 'X-Anthropic-Key': key });
  assert.deepEqual(assistant.keyHeaders(''), {});
  assert.deepEqual(assistant.keyHeaders('sk-ant-bad key'), {});
  assert.equal(assistant.maskKey(key), 'sk-ant-…xxxx');
});

test('the assistant info from the server is read defensively', () => {
  assert.deepEqual(
    assistant.parseAssistantInfo({ free_available: false, default: 'mechanic', daily_free_limit: 200 }),
    { freeAvailable: false, defaultAssistant: 'mechanic', dailyFreeLimit: 200 },
  );
  assert.equal(
    assistant.parseAssistantInfo({ free_available: true, daily_free_limit: 0 }).dailyFreeLimit,
    null,
  );
  assert.equal(assistant.parseAssistantInfo({ detail: 'Not Found' }), null);
  assert.equal(assistant.parseAssistantInfo(null), null);
});

test('every chat error code has plain words, and key problems offer a key', () => {
  const codes = [
    'assistant_unavailable',
    'free_assistant_resting',
    'key_rejected',
    'invalid_key_format',
    'rate_limited',
    'refused',
    'agent_failed',
  ];
  for (const code of codes) {
    const copy = assistant.chatErrorCopy(code);
    assert.ok(copy && copy.text, code);
    assert.ok(!/—/.test(copy.text), `${code} has an em dash`);
  }
  for (const code of ['assistant_unavailable', 'free_assistant_resting', 'key_rejected', 'invalid_key_format']) {
    assert.equal(assistant.chatErrorCopy(code).offerKey, true, code);
  }
  assert.match(assistant.chatErrorCopy('rate_limited', { ownKey: true }).text, /your key/);
  assert.equal(assistant.chatErrorCopy('bike_not_found'), null);
});

test('a refused key only suggests the free assistant when it is on', () => {
  assert.match(assistant.chatErrorCopy('key_rejected').text, /free assistant/);
  assert.match(
    assistant.chatErrorCopy('key_rejected', { freeAvailable: true }).text,
    /remove it to use the free assistant/,
  );
  const off = assistant.chatErrorCopy('key_rejected', { freeAvailable: false });
  assert.equal(off.offerKey, true);
  assert.doesNotMatch(off.text, /free assistant/);
  assert.match(off.text, /Anthropic Console/);
});

test('a daily-limit 429 offers the visitor their own key', () => {
  const daily = Object.assign(
    new Error(JSON.stringify({ error: 'rate_limited', message: 'limit is 200 per day', retry_after_s: 40000 })),
    { status: 429 },
  );
  assert.equal(assistant.describeChatFailure(daily).offerKey, true);
  const minute = Object.assign(
    new Error(JSON.stringify({ error: 'rate_limited', message: 'limit is 20 per 60s', retry_after_s: 12 })),
    { status: 429 },
  );
  assert.deepEqual(assistant.describeChatFailure(minute), {
    text: 'Too many questions at once. Please try again in a minute.',
    offerKey: false,
  });
  assert.equal(assistant.describeChatFailure(new Error('Failed to fetch')).text, 'Failed to fetch');
  assert.equal(assistant.describeChatFailure(undefined).text, 'Request failed. Please try again.');
});
