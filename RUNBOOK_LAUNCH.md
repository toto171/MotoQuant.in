# MotoQuant Pro — Turn-Key Launch Runbook

> Copy-paste checklist to go from clean clone → live `motoquant.in` + `api.motoquant.in` in about 90 minutes.
> Assumes: GitHub repo exists, you have admin on `dhisetu@gmail.com` Vercel + Railway accounts, domain `motoquant.in` lives in a registrar you control (GoDaddy, Namecheap, Squarespace, Cloudflare, etc.).

## 0. Pre-flight (10 min)

```bash
cd "Vehicle Dynamics"

# 0.1 confirm reference baselines + all fast tests pass
python -c "import motoquant; \
  e = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5()); \
  r = e.run(); \
  assert abs(r.time_quarter - 10.034) < 0.02, r.time_quarter; \
  print(f'K5 baseline OK: {r.time_quarter:.3f}s')"

python -m pytest tests/ \
  --ignore=tests/test_api.py \
  --ignore=tests/test_surrogate.py \
  --ignore=tests/test_analysis.py \
  --ignore=tests/test_calibration.py -q
#   expect: 529 passed, 27 skipped

# 0.2 run validation sweep (takes ~2 min); fail launch if bias > +0.40s
python validation_sweep.py
#   expect: Mean |ΔET| ≤ 0.40s, Bias ≤ +0.40s, ≥ 40/53 within ±0.50s

# 0.3 verify DB is seeded end-to-end
python -m motoquant.run db stats
#   expect: bikes ≥ 270, tires ≥ 69, parts ≥ 424, venues ≥ 12

# 0.4 build a static fallback of the Next.js site (sanity check)
cd web
npm install
npm run build
cd ..
#   expect: no errors; `.next/` directory populated
```

If any of the above fails, STOP and fix before continuing.

## 1. Railway backend (20 min) — `api.motoquant.in`

Railway hosts the FastAPI service in `motoquant/api.py`.

1. **Create project**  
   Log in → https://railway.app → `+ New Project` → `Deploy from GitHub repo` → pick your `motoquant` repo.
2. **Let nixpacks auto-detect.**  
   `nixpacks.toml` is already in the repo and pins Python 3.11 + installs from `requirements-api.txt`.
3. **Environment variables** (Settings → Variables):

   | Key                     | Value                                      |
   |-------------------------|--------------------------------------------|
   | `MOTOQUANT_DB`          | `/app/motoquant.db`                        |
   | `MOTOQUANT_ALLOW_ORIGIN`| `https://motoquant.in,https://www.motoquant.in` |
   | `PORT`                  | *(Railway injects automatically — do not set)* |

4. **Upload the seeded DB.**  
   Railway doesn't persist the build-time filesystem, so commit `motoquant.db` into the repo (it's ~3 MB) or add a volume. The simpler path:  
   `git add -f motoquant.db && git commit -m "deploy: seed db snapshot"`  
   The `nixpacks.toml` copies it into the image root at `/app/motoquant.db`.
5. **Custom domain** — in Railway → Settings → Networking → Generate Domain, then add `api.motoquant.in` and copy the CNAME target Railway gives you (you will add this at your registrar in step 3).
6. **Smoke test:**
   ```bash
   curl https://<railway-url>/api/health
   #   → {"status":"ok","version":"..."}
   curl -X POST https://<railway-url>/api/simulate/quick \
     -H "Content-Type: application/json" \
     -d '{"bike_preset":"gsxr1000_k5"}'
   #   → ET ≈ 10.034
   ```

## 2. Vercel frontend (15 min) — `motoquant.in`

1. **Create Vercel project**  
   https://vercel.com → `Add New…` → `Project` → import your `motoquant` repo.
2. **Framework: Next.js**, **Root Directory: `web`**, **Build Command: `npm run build`** (Vercel auto-detects from `package.json`).
3. **Environment variables** (Project Settings → Environment Variables):

   | Key                   | Value                              | Scope         |
   |-----------------------|------------------------------------|---------------|
   | `NEXT_PUBLIC_API_URL` | `https://api.motoquant.in`         | Prod + Preview|
4. **Deploy.** Wait ~90 s for build. Grab the default `motoquant.vercel.app` URL and smoke test the simulator widget end-to-end.
5. **Add custom domain** — Domains → Add → `motoquant.in` *and* `www.motoquant.in`. Vercel prints the A/CNAME records you need.

## 3. DNS at registrar (10 min)

Add three records. Values come from Vercel (steps 2.5) and Railway (step 1.5):

| Host              | Type  | Value                              |
|-------------------|-------|------------------------------------|
| `@`  / apex       | `A`   | `76.76.21.21` *(Vercel anycast — verify in Vercel UI)* |
| `www`             | `CNAME` | `cname.vercel-dns.com`           |
| `api`             | `CNAME` | *(the CNAME target Railway gave you)* |

Then in Vercel click `Refresh` on each domain until all three turn green (SSL typically provisions in 2–10 min). In Railway do the same — the custom-domain row goes green when cert is issued.

## 4. Post-launch verification (15 min)

```bash
# 4.1 DNS resolves
dig +short motoquant.in
dig +short www.motoquant.in
dig +short api.motoquant.in

# 4.2 HTTPS + CORS
curl -I https://motoquant.in
curl -I https://api.motoquant.in/api/health
curl -H "Origin: https://motoquant.in" -I https://api.motoquant.in/api/health
#   → expect `access-control-allow-origin: https://motoquant.in`

# 4.3 end-to-end simulator works from prod
# Open https://motoquant.in → scroll to Simulator widget → pick Hayabusa → Run.
# Expect: ET ≈ 10.47 s, no console errors, request to api.motoquant.in succeeds.

# 4.4 (optional) Dragy + Dyno upload smoke tests via API
curl -X POST https://api.motoquant.in/api/calibrate/dragy \
  -F "file=@tests/fixtures/dragy_sample.csv"
```

## 5. Rollback playbook (5 min — tattoo this in your head)

- **Frontend broken:** In Vercel Deployments tab, find the last known-good deploy, click the three-dot menu → *Promote to Production*. Takes ~30 s.
- **Backend broken:** Railway keeps prior builds. Click the previous deploy → *Redeploy*. Takes ~45 s.
- **DB corrupted:** `motoquant.db` is immutable in the image. Revert the commit that changed it (`git revert <sha>`), push, Railway auto-redeploys.
- **Everything on fire:** `vercel rollback` and `railway rollback` from CLI (both tools are `npm i -g vercel` / `npm i -g @railway/cli`).

## 6. First-week monitoring

- **Vercel Analytics** (Project → Analytics) — page views, visitor geography, Core Web Vitals.
- **Railway metrics** (Project → Observability) — CPU + memory + p95 request latency. Anything > 300 ms for `/api/simulate/quick` means the engine is thrashing — check gear ratios weren't accidentally de-synced.
- **Error alerting:** add Sentry (free tier) by `npm i @sentry/nextjs` in `web/` and `pip install sentry-sdk` in API. Set `SENTRY_DSN` env var in both.
- **Uptime:** UptimeRobot (free) pinging `https://api.motoquant.in/api/health` every 5 min; alert email to `dhisetu@gmail.com`.

## 7. When to pull the subscription lever

- ≥ 100 unique simulator runs / day
- ≥ 10 users who have uploaded Dragy + dyno data
- Mean |ΔET| ≤ 0.25 s on the 53-benchmark set (currently 0.351 s)
- Desktop app closed beta running with ≥ 3 Pune/Narhe shops

## 8. Known gotchas (learned in blood)

1. **SQLite on Railway mounted filesystems** — `connection.py` already falls back from WAL → DELETE journal mode on FUSE mounts. Do not "fix" this by forcing WAL — it breaks prod.
2. **Chain-pitch inference** — the catalog's compatibility engine assumes `chain_pitch` is a string code ("428"/"520"/"525"/"530"), not an integer or mm value. `_infer_chain_pitch` in `importer.py` is authoritative.
3. **Reference baselines are non-negotiable** — `tests/test_no_silent_failures.py::TestNoSilentFailures::test_reference_baselines_preserved` hard-fails if K5 ≠ 10.034 ± 0.020 s, R1 ≠ 10.286 ± 0.030 s, or Hayabusa ≠ 10.472 ± 0.030 s. If a physics tweak moves these, the change is wrong.
4. **Parts catalog has 17 categories**, but only 7 meaningfully affect ET (exhaust, ECU, boost kit, nitrous, sprockets, clutch, tires). The remaining 10 are cosmetic / ergonomic — don't over-weight them in the ROI optimiser.
5. **The "sim slower than real" bias** is concentrated in 500-700 cc 4T parallel twins + small-cc commuters. This is real and documented; the fix is per-bike Dragy calibration (`motoquant calibrate import-dragy + calibrator.calibrate`), not more physics tuning.
