// @ts-check
'use strict';

/**
 * MotoQuant Pro — Playwright smoke harness config
 * ================================================
 * Low-risk, version-controlled end-to-end smoke test for the landing →
 * quick-sim happy path. Intentionally minimal: one Chromium project, one
 * short spec, generous timeouts to tolerate a cold-starting API (the prod
 * backend is Render free-tier and can take 15-60s to wake).
 *
 * Run locally (see e2e/README.md for the full recipe):
 *   1. boot the API:   python3 -m uvicorn motoquant.api:app --port 8000
 *   2. build + start:  cd web && npm run build && npm start   (port 3000)
 *   3. point + run:     E2E_BASE_URL=http://localhost:3000 \
 *                       cd web && npm run e2e
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
    // Reduced motion is load-bearing here, not cosmetic:
    //   - the landing BootSequence overlay is prefers-reduced-motion-gated,
    //     so this stops a full-screen z-[100] overlay from intercepting the
    //     first clicks;
    //   - framer-motion Reveals / ManifestoScrub / TronGrid all take their
    //     static branch, which removes a large class of animation-timing
    //     flake from the smoke.
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
