# MotoQuant E2E — Playwright smoke harness

A tiny, durable Playwright smoke suite for the **landing → calculator happy
path**. It exists so that "the homepage loads and the calculator returns an
exact quarter-mile time" is version-controlled and runnable, instead of living
only in a throwaway session scratchpad.

- `playwright.config.js` — one Chromium project, `testDir: ./specs`,
  `baseURL` from `E2E_BASE_URL` (default `http://localhost:3000`), reduced
  motion on, generous timeouts for API cold starts.
- `specs/smoke.spec.js` — two checks:
  1. landing page loads (title + hero visible, no uncaught JS errors);
  2. calculator happy path (keep the default bike, press **Calculate my
     time**, assert the exact result renders: the **First 60 ft (launch)** and
     **Finish-line speed** rows, a time, a speed, and the **Conditions:** line
     that says what air the result is for).

## Running it locally

The tests drive a **real** running stack (Next.js frontend + FastAPI
backend). Nothing is mocked. From the repo root:

```bash
# 1. Boot the API on :8000 against a COPY of the shipped catalog (the API
#    writes to the file it opens; never point it at the tracked motoquant.db).
cp motoquant.db /tmp/e2e.db
MOTOQUANT_DB=/tmp/e2e.db python3 -m uvicorn motoquant.api:app --host 127.0.0.1 --port 8000
#    (`pip install -e .` installs the package and its runtime dependencies.)

# 2. In a second shell, build + start the web app on :3000, pointed at the API.
cd web
npm install                                   # first time only
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run build
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm start

# 3. In a third shell, install the test runner + browser (from e2e/), then run.
cd e2e
npm install                                   # installs @playwright/test (self-contained)
npx playwright install --with-deps chromium   # skip if a browser is already present
E2E_BASE_URL=http://localhost:3000 npm test
```

The harness is **self-contained under `e2e/`** — it has its own
`package.json`, so it never perturbs `web/package.json` or the web lockfile.
`npm test` (in `e2e/`) runs `playwright test`, which auto-loads
`e2e/playwright.config.js`.

### Pre-installed Chromium (this sandbox / matching CI images)

If a browser already lives at `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`
(with `/opt/pw-browsers/chromium` symlinked to the chrome binary), the config
points `executablePath` straight at it — **do not** run
`playwright install` (and `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` is honored).
Everywhere else the config falls back to Playwright's managed Chromium
fetched by `npx playwright install --with-deps chromium`.

## CI

`.github/workflows/e2e.yml` runs the same flow, but it is **manual-trigger
only** (`workflow_dispatch`) — never auto-on-PR — so a flaky run can never
red a pull request while the harness is stabilizing. The job boots uvicorn +
`next start`, waits for both, runs the suite, and uploads the Playwright HTML
report as an artifact.

## Notes

- `@playwright/test` is declared in `e2e/package.json` and is **not** vendored
  into the repo — `npm install` (locally or in CI) fetches it. The web app's
  `package.json`/lockfile are left completely untouched.
- Selectors intentionally prefer role + visible text over brittle CSS. If the
  app later grows `data-testid`s, prefer those. See the header comment in
  `specs/smoke.spec.js` for exactly which source lines each selector maps to.
