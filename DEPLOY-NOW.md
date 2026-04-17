# MotoQuant Pro — Deploy Guide

Follow these four steps in order. The whole thing should take ~30 minutes.

---

## Step 1 — Push everything to GitHub (from YOUR terminal)

Open a terminal on your own machine, `cd` into the `Vehicle Dynamics` folder, and run:

```bash
# 1. Clear any stale git lock left over from the sandbox
rm -f .git/index.lock

# 2. Stage everything
git add -A

# 3. Sanity check — you should see ~70 files, including:
#    new:   Procfile, nixpacks.toml, DEPLOY-NOW.md
#    modified:  web/app/page.js, web/components/SimulatorWidget.js, web/vercel.json
#    modified:  lots of motoquant/* Python files (Phase 3/4 work)
git status

# 4. Commit
git commit -m "Phase 3/4 + web launch: cinematic landing + mobile polish + deploy configs

- Landing page: Next.js 14 + framer-motion, cinematic dark hero, glass cards
- Mobile: hamburger nav, stacked simulator sliders, responsive padding
- SimulatorWidget: animated counters, glowing timeline, orange brand palette
- Deploy: Procfile, nixpacks.toml (Railway), vercel.json (Next framework + caching)
- Phase 3 calibration: Dragy/Dyno/ECU import, overlay, auto-calibrator
- Phase 3 API: FastAPI endpoints (health, bikes, tires, sim, compare, uploads)
- Phase 4 analysis: ROI knapsack, Sobol, Bayesian opt, XGBoost + DNN surrogates
- Phase 4 recommendations: synergies, compatibility, upgrade paths, NLP queries
- Tests: 583+ passing across 13 files"

# 5. Push
git push origin main
```

If the `.git/index.lock` file won't delete (Cowork mount permission issue shows
`Operation not permitted`), close this Cowork session first so the mount is
released, then retry `rm -f .git/index.lock` from your local terminal.

---

## Step 2 — Railway (backend API)

1. Go to https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Authorise GitHub if needed, then pick **da25mem5s02-debug/MotoQuant_v1**
3. Railway auto-detects `nixpacks.toml` and starts building
4. While it builds, go to **Variables** and set:
   - `MOTOQUANT_DB` = `/app/motoquant.db`
   - `PYTHON_VERSION` = `3.11`
5. Go to **Settings → Networking** → **Generate Domain**. You'll get something like
   `motoquant-v1-production.up.railway.app`. **Copy this URL — you need it in Step 3.**
6. Upload the seeded DB:
   - In Railway, install the Railway CLI: `npm install -g @railway/cli`
   - `railway login` (opens browser)
   - `railway link` → pick your project
   - `railway run bash` → from inside the container, `cd /app && ls` to confirm
     you're in the app dir. Your deployed repo already contains `motoquant.db`
     because it's committed to git — so no upload needed. ✓
7. Test: `curl https://<your-railway-url>/api/health` → should return `{"status":"ok"}`

If the DB isn't found, double-check `MOTOQUANT_DB` points to where the file is.
The repo's `motoquant.db` lands at `/app/motoquant.db` by default.

---

## Step 3 — Vercel (frontend)

1. Go to https://vercel.com → **Add New → Project** → Import the same GitHub repo
2. **Important:** Set **Root Directory** to `web` (click "Edit" next to Root
   Directory and type `web`)
3. Framework preset: **Next.js** (auto-detected)
4. Build command, output dir, install command — leave defaults
5. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_URL` = `https://<your-railway-url>` (from Step 2.5,
     NO trailing slash)
6. Click **Deploy**. First build takes ~2 minutes.
7. Vercel gives you a preview URL like `motoquant-v1.vercel.app`. Test the
   simulator — it should hit your Railway API and return ET.

---

## Step 4 — DNS (motoquant.in)

Wherever your domain registrar is (GoDaddy / Namecheap / Cloudflare / whoever
issued the GitHub Education domain — usually Namecheap):

1. **Root domain `motoquant.in` → Vercel**
   - Add an **A record**: `@` → `76.76.21.21` (Vercel's anycast IP)
   - OR if your registrar supports ALIAS/ANAME: `@` → `cname.vercel-dns.com`
2. **www subdomain → Vercel**
   - Add a **CNAME**: `www` → `cname.vercel-dns.com`
3. **API subdomain `api.motoquant.in` → Railway**
   - Add a **CNAME**: `api` → `<your-railway-url without https://>`
     (e.g. `motoquant-v1-production.up.railway.app`)
4. In Vercel project → Settings → Domains → **Add Domain** `motoquant.in` and
   `www.motoquant.in`. Vercel will verify the DNS records.
5. In Railway project → Settings → Networking → **Custom Domain** →
   `api.motoquant.in`. Railway will verify.
6. Once DNS propagates (5 minutes to 2 hours), update Vercel env var
   `NEXT_PUBLIC_API_URL` to `https://api.motoquant.in` and redeploy.

DNS propagation can take a few hours globally but usually works within 5 min
for the nameserver you're querying.

---

## Step 5 — Optional polish (later)

- Drop a 1080p MP4 at `web/public/hero/reel.mp4` for the cinematic video hero
  (see `web/public/hero/README.md` for recommended clips)
- Set up GitHub Actions CI to run `pytest` on every push
- Configure Railway health check path to `/api/health`
- Enable Vercel Analytics for mobile-device traffic breakdown

---

## Troubleshooting

**Railway build fails on `pip install`**: check that `requirements-api.txt`
didn't get broken. Should have `fastapi`, `uvicorn[standard]`, `pydantic`,
`numpy`, `scipy`, `python-multipart`.

**Vercel build fails with "Cannot find module 'styled-jsx'"**: that was a
sandbox-only issue with the mounted FS. Vercel does a fresh `npm install`, so
it won't hit this. If it does somehow, delete `web/node_modules` and
`web/package-lock.json` locally, run `npm install` in `web/`, commit the new
lockfile, push.

**API returns 500 from Vercel but works when you curl Railway directly**:
check CORS. `motoquant/api.py` is open CORS by default, so this shouldn't
happen — but if it does, make sure `NEXT_PUBLIC_API_URL` has the correct
`https://` prefix and no trailing slash.

**Simulator on the page never loads**: open browser devtools → Network tab →
click Run Simulation. The request should go to `<NEXT_PUBLIC_API_URL>/api/simulate/quick`.
If it's going to the wrong URL, redeploy Vercel after fixing the env var.
