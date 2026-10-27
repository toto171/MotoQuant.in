# Migrate MotoQuant API: Railway → Render (free tier)

> **Historical runbook (May 2026).** The cutover is done; production runs on
> Render. For how to deploy or self-host MotoQuant today, including every
> environment variable, see [SELF_HOSTING.md](SELF_HOSTING.md). Some steps
> below mention files and services that no longer exist (Railway, the
> desktop app).

**Goal:** drop hosting cost to $0/mo for the 3-4 month runway while MotoQuant
gets users. Keep the Vercel frontend on `motoquant.in` untouched; only swap the
backend that serves `/api/*`.

**Trade-off accepted:** Render's free tier sleeps after 15 minutes of no
inbound traffic. A GitHub Actions cron (`.github/workflows/keepalive.yml`,
already in this repo) pings `/api/health` every 14 minutes to keep it warm
during active hours. Cold-start budget if the cron ever fails: ~30-60s on the
next request.

**Rollback plan:** keep Railway running for 48 hours after Render goes live.
If anything breaks, revert `vercel.json` to point back at Railway and
redeploy Vercel. Total downtime in the worst case: one Vercel build (~2 min).

---

## Files added in this migration

| File | Purpose |
|---|---|
| `render.yaml` | Render Blueprint — tells Render to build the existing `Dockerfile` on the free plan, healthcheck `/api/health`, auto-deploy on every push to `main`. |
| `.github/workflows/keepalive.yml` | GH Actions cron pinging `/api/health` every 14 min. Stops the free-tier 15-min sleep. |
| `docs/RENDER_MIGRATION.md` | This file. |

Files **not** modified:

- `Dockerfile` — already honors `$PORT` (Render injects 10000) and defaults
  `MOTOQUANT_DB` to `/app/motoquant.db`. Works as-is.
- `motoquant.db` — still tracked in git, still ships in the image. Same DB
  on Render as on Railway.
- `requirements-api.txt`, `motoquant/api.py`, anything in `web/`,
  `desktop/`, or the Phase 5 release pipeline — untouched.

---

## Step 1 — Deploy to Render (no CLI install needed)

Render is dashboard-driven. There is nothing to install on your machine.

1. Push this branch to GitHub on `main`. Render watches `main` for changes.
2. Open https://dashboard.render.com → sign up with the **same GitHub
   account** that owns `da25mem5s02-debug/MotoQuant_v1`.
3. **New +** → **Blueprint** → **Connect a repository** →
   pick `da25mem5s02-debug/MotoQuant_v1`.
4. Render reads `render.yaml`, shows a one-screen summary
   (`motoquant-api`, Docker, Free plan, Singapore region, healthcheck
   `/api/health`). Click **Apply**.
5. First build runs. Expect 4-7 minutes — Render is building the same
   Dockerfile Railway builds, just on a cold cache.
6. When the dashboard shows **Live**, note the URL. It will look like
   `https://motoquant-api.onrender.com` (Render auto-derives it from the
   service name in `render.yaml`).

### Setting optional secrets

If/when you want chat (`GEMINI_API_KEY`, `GROQ_API_KEY`), error tracking
(`SENTRY_DSN`), or optional accounts (`JWT_SECRET`, plus an email transport;
see [SELF_HOSTING.md](SELF_HOSTING.md)), add them in the Render dashboard:

`motoquant-api` → **Environment** → **Add Environment Variable**

None of these are required for the basic simulator + catalog endpoints.
`motoquant.in` worked on Railway without any of them.

---

## Step 2 — Verify Render is healthy

From your terminal:

```bash
curl https://motoquant-api.onrender.com/api/health
# expect: {"status":"ok","database":"connected","bike_count":336}

curl "https://motoquant-api.onrender.com/api/bikes?limit=3"
# expect: 3 bike rows with the latest catalog (Aprilia / KTM / etc.)

curl -X POST https://motoquant-api.onrender.com/api/simulate/quick \
  -H "Content-Type: application/json" \
  -d '{"bike_id": 1, "rider_mass_kg": 80}'
# expect: {"time_quarter": 10.0xx, "trap_speed_kmh": 23x.x, ...}
```

If any of those fail, check the **Logs** tab in the Render dashboard
and look for the uvicorn startup line + the first request handler. Most
common failure: missing dependency in `requirements-api.txt` (shouldn't
happen since Railway is building from the same file, but worth checking).

---

## Step 3 — Soft cutover (flip Vercel rewrite)

This is the only line in the repo that needs to change to redirect
production traffic:

In `vercel.json`, change:

```json
"destination": "https://web-production-de6eb.up.railway.app/api/:path*"
```

to:

```json
"destination": "https://motoquant-api.onrender.com/api/:path*"
```

Commit + push. Vercel auto-redeploys in ~90 seconds. Then test
`motoquant.in` end-to-end:

```bash
curl https://www.motoquant.in/api/health
# Vercel will now route this through Render. Expect the same JSON.
```

Walk through the live simulator widget on the landing page and confirm a
`/api/simulate/quick` call comes back in <500 ms (after warm-up).

---

## Step 4 — Enable the keep-alive cron

The workflow file `.github/workflows/keepalive.yml` will start running
automatically as soon as it lands on `main` — GitHub picks up new cron
schedules on push. Default URL is `https://motoquant-api.onrender.com`.

**If your Render service URL is different** (e.g. you picked a custom
service name), override it in the repo:

GitHub repo → **Settings** → **Secrets and variables** → **Actions** →
**Variables tab** → **New repository variable** → name `RENDER_API_URL`,
value `https://<your-service>.onrender.com`.

Verify by triggering manually:
GitHub → **Actions** → **Render keep-alive** → **Run workflow**.
Should succeed within 60 seconds.

---

## Step 5 — 48-hour soak, then suspend Railway

For 48 hours, leave Railway running with the same Dockerfile / same DB so
you have an instant-flip fallback if Render misbehaves. Monitor:

- Render dashboard → **Metrics** tab → response times, error rate
- GitHub Actions tab → Render keep-alive should be 100% green
- `motoquant.in` simulator widget — click around, run a few sims

After 48 hours of clean operation:

1. Railway dashboard (https://railway.app) → `proactive-adventure` project →
   `web` service → **Settings** → **Suspend service**. Don't delete yet —
   keeps the project recoverable for another 30 days. Suspended services
   don't accrue charges.
2. Update `motoquant/CLAUDE.md` (Phase 3 hygiene section) — strike the
   "upgrade Railway trial" and "rename Railway project" lines, add a
   "Migrated to Render free tier — see `docs/RENDER_MIGRATION.md`" note
   in the dated session entry.

After 30 more days (90 days total), if Render is still working, delete the
Railway project entirely.

---

## Rollback (if Render breaks within the soak window)

1. Revert the single-line change to `vercel.json` (point back at the Railway
   URL `https://web-production-de6eb.up.railway.app/api/:path*`).
2. Commit + push. Vercel redeploys in ~90s.
3. `motoquant.in` is back on Railway.
4. Investigate Render logs at your own pace.

---

## What I traded away to save $5/mo

| Property | Railway ($5/mo) | Render Free |
|---|---|---|
| First-request latency | <300 ms always | <300 ms when warm, 30-60s cold-start if cron fails |
| Uptime SLA | best-effort, no formal SLA on hobby | best-effort, same |
| Build minutes | unlimited | 500 free build min/mo (we use ~5/build, ~5 builds/wk = ~100 min/mo) |
| Outbound bandwidth | unlimited (within reason) | 100 GB/mo free (we use <1 GB) |
| Persistent disk | ephemeral (rebuilds wipe) | ephemeral (rebuilds wipe) — same |
| Region | `us-west2` | `singapore` (closer to India — actually a win) |
| Cost | $5/mo | $0/mo |

The cold-start risk is the only real downside, and the keep-alive cron
mitigates it for the URLs that visitors actually hit (`/api/health` warms
the worker, `/api/bikes` and `/api/simulate/*` share that warm worker).

---

## If/when you outgrow Render free

In order of effort (low → high):

1. **Render Starter ($7/mo)** — same dashboard, no sleep, persistent disk.
   One-click upgrade from the free plan once usage justifies it.
2. **Fly.io pay-as-you-go (~$1.50-2/mo)** — slightly cheaper than Render
   Starter, no sleep, requires Docker (already have one) + `flyctl` install.
3. **Oracle Cloud Always Free** — 4× ARM Ampere cores + 24 GB RAM forever
   free. Strictly better resources than any paid tier on this list. Costs
   1-2 hours of setup time (provision VM, install Docker, set up Caddy for
   TLS, point DNS). Worth doing once real usage makes cold starts and the
   ephemeral DB unacceptable.

The migration path from Render to any of these is identical to this one:
deploy to the new platform, flip `vercel.json`, suspend the old one. The
`render.yaml` file can stay in the repo as a fallback or be deleted at
that point.
