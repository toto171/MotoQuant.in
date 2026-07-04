// @ts-check
'use strict';

/**
 * Landing → quick-sim smoke suite.
 *
 * Two checks, deliberately small and resilient:
 *   1. the landing page loads (title + hero visible, no uncaught JS errors);
 *   2. the embedded Live Simulator quick-sim happy path works end-to-end
 *      (keep the default bike, click the ¼-mile run button, assert a real
 *      ET result panel renders).
 *
 * Selector strategy (verified against web/components/SimulatorWidget.js +
 * web/app/page.js on 2026-07-04):
 *   - Hero H1 text is "The physics of faster." (page.js:412).
 *   - The quick-sim run button's accessible name is "Quarter-Mile ET"
 *     (SimulatorWidget.js:592) — targeted by role=button so it can't clash
 *     with the identical result-panel LABEL text (a <p>, SimulatorWidget.js:651).
 *   - "Trap Speed" (SimulatorWidget.js:665) and "Split Timeline"
 *     (SimulatorWidget.js:681) render ONLY inside the result panel, so their
 *     appearance is a reliable "the quick sim returned" signal. Both strings
 *     are unique on the landing page (grep-verified).
 *
 * The widget defaults to Sim mode + Quarter-Mile + the first Indian-Sport
 * bike (KTM RC 390), so the happy path needs no bike selection.
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

    // Title comes from web/app/layout.js metadata.title.default.
    await expect(page).toHaveTitle(/MotoQuant/i);

    // Hero H1: "The physics of faster." (.first() defends against any
    // future stray h1 on the page).
    const hero = page.getByRole('heading', { level: 1 }).first();
    await expect(hero).toBeVisible();
    await expect(hero).toContainText(/physics/i);

    // Let mount-time fetches (e.g. the catalog fetch the widget fires on
    // mount) settle so any late console.error is captured before we assert.
    await page.waitForTimeout(1500);

    expect(
      errors,
      `Unexpected console/page errors on landing:\n  ${errors.join('\n  ')}`,
    ).toEqual([]);
  });

  test('quick-sim happy path renders an ET result', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // The run button (role=button, name "Quarter-Mile ET"). Playwright
    // auto-scrolls it into view before clicking, so no manual scroll needed.
    const runBtn = page.getByRole('button', { name: /Quarter-Mile ET/i });
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // Result-panel-only markers — their presence means the quick sim
    // returned and rendered. Generous timeout tolerates API cold start.
    await expect(page.getByText('Trap Speed')).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText('Split Timeline')).toBeVisible({ timeout: 60_000 });

    // The ¼-mile split row renders the ET to 3 decimals + an "s" suffix
    // (SimulatorWidget.js:731). Assert a real quarter-mile ET number showed
    // up rather than just chrome. The seven-segment SegEt board also renders
    // the ET, so at least one "<n>.<3dp>s" is guaranteed once the run lands.
    await expect(page.getByText('¼ mile')).toBeVisible();
    await expect(page.getByText(/\d+\.\d{3}\s*s/).first()).toBeVisible();
  });
});
