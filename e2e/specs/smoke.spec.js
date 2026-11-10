// @ts-check
'use strict';

/**
 * Landing → calculator smoke suite.
 *
 * Two checks, deliberately small and resilient:
 *   1. the landing page loads (title + hero visible, no uncaught JS errors);
 *   2. the landing calculator's happy path works end-to-end (keep the default
 *      bike, press "Calculate my time", assert the exact result renders).
 *
 * Selector strategy (verified against web/app/page.js and
 * web/components/SimulatorWidget.js, design system v6, on 2026-11-10 by
 * running this suite against a local stack):
 *   - Hero H1 reads "Know your quarter-mile time before you race."
 *   - The run button's accessible name is "Calculate my time". The same words
 *     appear in two hint sentences, so it is targeted by role=button.
 *   - "First 60 ft (launch)" and "Finish-line speed" are rows of the EXACT
 *     result only (the server simulation). The instant estimate that appears
 *     first has neither, so their appearance is the "the server answered"
 *     signal.
 *   - The result ends with a conditions line ("Conditions: …") built from the
 *     API's `environment` block: every result must say what air it is for.
 *
 * The calculator starts on a default bike, so the happy path needs no bike
 * selection.
 */

const { test, expect } = require('@playwright/test');

// Console noise we tolerate: resource/network failures (a cold or absent
// asset, favicon, a slow /api call) are not "uncaught JS errors" and must
// not flake the smoke. Genuine uncaught exceptions arrive via `pageerror`
// and are NEVER filtered.
const BENIGN_CONSOLE = [
  /favicon/i,
  /Failed to load resource/i,
  /net::ERR_/i,
  /Failed to fetch/i,
  /the server responded with a status of [45]\d\d/i,
  /manifest\.json/i,
  /Download the React DevTools/i,
];

/**
 * Attach console/page-error collectors. Returns a live array of
 * unexpected error strings that the caller can assert on at the end.
 * @param {import('@playwright/test').Page} page
 */
function collectErrors(page) {
  /** @type {string[]} */
  const errors = [];
  page.on('pageerror', (err) => {
    errors.push(`[pageerror] ${err.message}`);
  });
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (BENIGN_CONSOLE.some((re) => re.test(text))) return;
    errors.push(`[console.error] ${text}`);
  });
  return errors;
}

test.describe('MotoQuant landing smoke', () => {
  test('landing page loads with title + hero and no uncaught errors', async ({ page }) => {
    const errors = collectErrors(page);

    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // <title> comes from the root layout metadata.
    await expect(page).toHaveTitle(/MotoQuant/i);

    // The hero H1 is server-rendered, so it is in the DOM immediately.
    const hero = page.getByRole('heading', { level: 1 }).first();
    await expect(hero).toBeVisible();
    await expect(hero).toContainText(/quarter-mile time/i);

    // The calculator section is on the page.
    await expect(page.getByRole('button', { name: 'Calculate my time' })).toBeVisible();

    // Give hydration + first paint a moment to surface any runtime error.
    await page.waitForLoadState('load');

    expect(
      errors,
      `Unexpected console/page errors on landing:\n  ${errors.join('\n  ')}`,
    ).toEqual([]);
  });

  test('calculator happy path renders an exact quarter-mile result', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // The button stays disabled until the bike list has loaded.
    const runBtn = page.getByRole('button', { name: 'Calculate my time' });
    await expect(runBtn).toBeVisible();
    await expect(runBtn).toBeEnabled({ timeout: 60_000 });
    await runBtn.click();

    // Rows that only the exact (server) result has. Generous timeout: the
    // first hit may wait out an API cold start.
    // (Each label is a glossary term, rendered as a button; "Finish-line
    // speed" also occurs in page copy, so both are matched by role.)
    await expect(
      page.getByRole('button', { name: 'First 60 ft (launch)', exact: true }),
    ).toBeVisible({ timeout: 60_000 });
    await expect(
      page.getByRole('button', { name: 'Finish-line speed', exact: true }),
    ).toBeVisible();

    // A real time and a real speed, e.g. "1.90 s" and "235 km/h".
    await expect(page.getByText(/^\d+\.\d{2} s$/).first()).toBeVisible();
    await expect(page.getByText(/^\d{2,3} km\/h$/).first()).toBeVisible();

    // Every result states the conditions it was computed for.
    await expect(page.getByText(/Conditions:/).first()).toBeVisible();
  });
});
