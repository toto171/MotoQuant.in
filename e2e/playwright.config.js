// @ts-check
'use strict';

/**
 * MotoQuant — Playwright smoke harness config
 * ============================================
 * Low-risk, version-controlled end-to-end smoke test for the landing →
 * calculator happy path. Intentionally minimal: one Chromium project, one
 * short spec, generous timeouts to tolerate a cold-starting API (the prod
 * backend is Render free-tier and can take 15-60s to wake).
 *
 * Run locally (see e2e/README.md for the full recipe):
 *   1. boot the API on a COPY of the catalog:
 *        cp motoquant.db /tmp/e2e.db
 *        MOTOQUANT_DB=/tmp/e2e.db python3 -m uvicorn motoquant.api:app --port 8000
 *   2. build + start:  cd web && NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run build
 *                      NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm start   (port 3000)
 *   3. point + run:    cd e2e && npm install && E2E_BASE_URL=http://localhost:3000 npm test
 *
 * Chromium resolution:
 *   - In THIS sandbox a browser is pre-installed at
 *     PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers with a direct symlink
 *     /opt/pw-browsers/chromium -> the chrome binary. If that path exists
 *     we point executablePath straight at it (no `playwright install`).
 *   - In CI (.github/workflows/e2e.yml) that path does NOT exist, so we
 *     fall back to Playwright's managed Chromium fetched by
 *     `npx playwright install --with-deps chromium`.
 */

const fs = require('fs');
const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';

// Pre-installed Chromium in this environment (a symlink pointing straight
// at the chrome binary). fs.existsSync follows the symlink to the target.
const PREINSTALLED_CHROMIUM = '/opt/pw-browsers/chromium';
const preinstalledChromium = fs.existsSync(PREINSTALLED_CHROMIUM)
  ? PREINSTALLED_CHROMIUM
  : null;

module.exports = defineConfig({
  testDir: './specs',
  // Fail fast if someone leaves a stray `test.only` in a committed spec.
  forbidOnly: !!process.env.CI,
  // Single worker: there's exactly one local app+API stack under test, so
  // parallelism would only create contention (and cross-talk on the
  // shared /tmp DB), not speed.
  fullyParallel: false,
  workers: 1,
  // One retry absorbs a single cold-start / animation hiccup without
  // masking a genuinely broken build.
  retries: process.env.CI ? 1 : 0,
  // Generous per-test budget — a cold Render/uvicorn boot plus the quick
  // sim can legitimately take a while on first hit.
  timeout: 90_000,
  expect: {
    // Individual assertions (e.g. "the ET result appeared") may wait out
    // a cold start; keep this comfortably above a warm response time.
    timeout: 30_000,
  },
  reporter: [
    ['list'],
    // HTML report is uploaded as a CI artifact for post-mortem.
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  use: {
    baseURL: BASE_URL,
    // Reduced motion keeps the smoke deterministic: the site's entrance
    // animations (Reveal and friends) take their static branch, which removes
    // a class of animation-timing flake.
    reducedMotion: 'reduce',
    actionTimeout: 20_000,
    navigationTimeout: 45_000,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: preinstalledChromium
          ? { executablePath: preinstalledChromium }
          : {},
      },
    },
  ],
});
