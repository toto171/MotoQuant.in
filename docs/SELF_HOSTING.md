# Self-hosting MotoQuant

MotoQuant is free and open source (Apache-2.0). Everything that runs
<https://www.motoquant.in> is in this repository, and you can run your own
copy: on a laptop, on Render + Vercel the way the public instance does, or on
any host that runs Docker.

There is no billing, account or email configuration of any kind, and the
server writes nothing a visitor sends to its database (anonymous usage
events go to the server log, and to PostHog only if you set
`POSTHOG_API_KEY`; see below). Every environment variable on this page is
optional. With none of them set, the API serves the simulator, catalog,
optimizer and race-day setup; the leaderboard is a static page generated from
the physics (`scripts/gen_stock_leaderboard.py`).

The full annotated variable list is in [`.env.example`](../.env.example) at
the repo root. This page covers what each group is for and how to deploy.

---

## 1. Run it locally (five minutes)

Requirements: Python 3.10+ (CI and the Docker image use 3.11) and Node 18+ for
the web frontend.

```bash
git clone https://github.com/toto171/MotoQuant.in.git
cd MotoQuant.in

make install      # pip install -e ".[dev]": the package, runtime + dev deps
make check        # lint + format + baseline gate + fast tests (~3 min)

make api          # FastAPI backend on http://localhost:8000  (OpenAPI UI at /docs)
make web-install  # once
make web-dev      # Next.js on http://localhost:3000, pointed at the local API
```

The repo ships a seeded `motoquant.db` (bikes, parts, tires, venues,
benchmarks), so there is no database setup step. The CLI works straight
away:

```bash
python -m motoquant.run sim --bike-id 1 --venue-id 1
```

The CLI can save runs to the local database (`sim --save-run`, then
`history` and `leaderboard`). The website never writes to it: saved runs live
in each visitor's browser.

---

## 2. Architecture of a deployment

```
browser ──► web (Next.js, static + one route handler) ──/api/* rewrite──► API (FastAPI + SQLite)
```

- API: `motoquant/api.py`, served by uvicorn from the root
  [`Dockerfile`](../Dockerfile). It runs a single process
  ([`docker-entrypoint.sh`](../docker-entrypoint.sh)). Keep it that way:
  the job registry, the rate-limit counters and the weather and catalog
  caches all live in process memory.
- Database: one SQLite file, read-only in practice. The image carries the
  seeded catalog at `/app/motoquant.db`, so every deploy ships the latest
  catalog and nothing needs a persistent disk.
- Web: `web/` (Next.js App Router). The browser calls same-origin
  `/api/*`, and `web/next.config.js` rewrites those calls to the API.
  `MOTOQUANT_API_BACKEND` sets the rewrite target at build time (default
  `https://api.motoquant.in`); `NEXT_PUBLIC_API_URL` makes the browser call
  an absolute API URL directly instead (used by `make web-dev`).

---

## 3. Settings for a real host

### 3a. Chat agent (`POST /api/chat`)

The chat runs on Anthropic's Claude, and Claude is the only provider. Set
one variable on the server:

```bash
ANTHROPIC_API_KEY=<your key from https://console.anthropic.com/settings/keys>
```

Put it in your host's environment settings (on Render: the service's
**Environment** tab), never in a file in the repository. Without it, chat
answers `assistant_unavailable` unless the visitor brings their own key, and
everything else still works. The CLI's `nl` subcommand needs no key at all.

Visitors pick one of two assistants in the chat panel:

1. The doctor: Claude Opus 5.5. Slower, digs deeper.
2. The mechanic (the default): Claude Sonnet 5.5. Quick, practical
   answers.

The browser sends only `doctor` or `mechanic`; the server picks the model.

A visitor can also add their own Anthropic API key under "Use your own
key". It stays in their browser and is sent in the `X-Anthropic-Key`
header on the request that starts a chat. The server uses it for that one
request only (no fallback to your key) and never stores, logs or returns it.
Questions asked with a visitor's key are billed to the visitor's Anthropic
account.

Whoever runs a deployment pays for its own key, so chat has two fuses:

- a per-minute per-IP rate limit, for everyone (tools run simulations, so
  this protects the CPU), and
- `MOTOQUANT_CHAT_DAILY_LIMIT`: units per client IP per rolling 24 h
  (default 200), counted only when your key answers. A mechanic question
  costs 1 unit and a doctor question 2. Requests with a visitor's key skip
  this cap. Set it to `0` to turn the cap off.

If your key runs out of credit or hits its spend limit, chat answers
`free_assistant_resting` and the panel invites visitors to use their own key.

Agent web lookup is optional: `SEARCH_PROVIDER=brave|serper` plus
`SEARCH_API_KEY` upgrade the `web_search` tool from the keyless DuckDuckGo
HTML fallback. `MOTOQUANT_WEB_TOOLS=0` turns the agent's web access off.
Details: [CHAT_AGENT.md](CHAT_AGENT.md).

### 3b. Abuse fuses (on by default)

Every simulation and analysis route is free and anonymous, so each
compute-heavy route has a per-IP fixed-window rate limit (`motoquant/ratelimit.py`):
simulate, top speed, distance, compare, optimizer, autotune, calibration
uploads, place lookup, telemetry, and chat. Over the limit, a route answers
`429` with a `Retry-After` header.

The client IP comes from `X-Forwarded-For` only as far as you trust it,
set by `MOTOQUANT_TRUSTED_PROXY_HOPS`:

- Unset (auto): trust 1 hop on Render (the `RENDER` env var) or when the
  connection comes from loopback, a unix socket or a private-network peer
  (Docker bridge + nginx/Caddy); otherwise trust none and key on the socket
  peer.
- `0`: never trust the header (API exposed directly to the internet).
- `N`: you run N appending proxies; the client is the N-th hop from the
  right.

Invalid values fail closed to 0 with a warning. Trusting more hops than you
run lets clients spoof their IP and dodge the limits.

If the website proxies `/api/*` to the API (the Vercel setup in section 4),
every visitor reaches the API from Vercel's addresses and would share one
set of limits. Set the same random value of at least 16 characters as
`MOTOQUANT_PROXY_SECRET` on both the Vercel project and the API service.
The site's middleware (`web/middleware.js`) then sends each visitor's IP
with that secret, and the API keys its limits on it. The API ignores the
header from anyone without the secret. While the secret is set, one visitor
can also run at most 2 background jobs at a time.

Browsers on other sites cannot call the API: CORS allows only
`https://motoquant.in`, its `www` address and `localhost:3000`. If you
serve your own site from another origin and call the API directly from the
browser, list it in `MOTOQUANT_CORS_ORIGINS` (comma-separated).

`MOTOQUANT_RATE_LIMIT=false` disables every limit. Use it for tests, not for
a public instance. These counters are in-process; for multi-replica or
DDoS-grade protection, rate-limit at your edge as well.

### 3c. Optional extras

| Variable | Effect |
|---|---|
| `OPENWEATHERMAP_API_KEY` | Optional. Live weather when a visitor names a place comes from OpenWeatherMap when this is set, and from Open-Meteo (no key, free for non-commercial use, and it also gives the place's elevation) when it is not; `MOTOQUANT_OPEN_METEO=0` turns that fallback off. The `weather` CLI (`weather --refresh-all`) needs the key. Successful lookups are cached for ten minutes. Seeded venues use their stored seasonal data. |
| `SENTRY_DSN` (+ `SENTRY_ENVIRONMENT`, `SENTRY_RELEASE`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_SEND_PII`) | Error tracking. A no-op unless the DSN is set. See [OBSERVABILITY.md](OBSERVABILITY.md). |
| `POSTHOG_API_KEY` (+ `POSTHOG_HOST`) | Opt-in forwarding of the anonymous web telemetry beacon to PostHog. Unset, beacons are written to the server log only and nothing is sent to a third party. |
| `MOTOQUANT_KEEPWARM_URL` / `MOTOQUANT_KEEPWARM_INTERVAL_S` | In-app self-ping that keeps a sleeping free-tier host awake during the day. Starts automatically on Render (from `RENDER_EXTERNAL_URL`); off elsewhere unless you set the URL. |

---

## 4. Deploying

### 4a. Render (API) and Vercel (web), the way motoquant.in runs

For the API, [`render.yaml`](../render.yaml) is a Render Blueprint:
Docker runtime, free plan, Singapore region, health check `/api/health`, and
a `buildFilter` so pushes that only touch `web/` don't restart the API (and
kill in-flight jobs).

1. Render dashboard → **New → Blueprint** → connect your fork.
2. Apply. The first build takes a few minutes.
3. Add any secrets from section 3 under **Environment**. Never commit them.
4. Check: `curl https://<service>.onrender.com/api/health` should return
   `{"status":"ok","database":"connected","bike_count":…}`.

Free Render services sleep after 15 minutes without inbound traffic. Three
layers keep the public instance warm during the day; all are optional for
your copy:

- [`.github/workflows/keepalive.yml`](../.github/workflows/keepalive.yml):
  GitHub Actions cron. Set the `RENDER_API_URL` repository variable if your
  service URL differs.
- `web/app/api/wake/route.js` + the `crons` block in `web/vercel.json`:
  Vercel cron. It pings `MOTOQUANT_API_BACKEND` too.
- `motoquant/keepwarm.py`: in-app self-ping (section 3c).

For the web app, import the repo into Vercel with root directory `web`.
Point it at your API by setting `MOTOQUANT_API_BACKEND` in the Vercel
project; the `/api/*` rewrite in `web/next.config.js` and the wake route
both read it. Leave `NEXT_PUBLIC_API_URL` empty in production so the
browser stays same-origin, which also avoids CORS and DNS-filter problems
with PaaS domains. Before pushing anything under `web/`, run
`make web-build`, which runs the same build as Vercel.

The historical Railway → Render cutover runbook is in
[RENDER_MIGRATION.md](RENDER_MIGRATION.md).

### 4b. Any Docker host

```bash
docker build -t motoquant-api .
docker run -d --name motoquant-api -p 8000:8000 motoquant-api
curl http://localhost:8000/api/health
```

The container needs no volume: the catalog is baked into the image, and a new
image is how a catalog update ships.

Terminate TLS in a reverse proxy such as Caddy or nginx and keep exactly one
proxy hop in front of the API (see 3b). For the web frontend, run
`cd web && npm ci && npm run build && npm start` behind the same proxy with
`MOTOQUANT_API_BACKEND` pointing at the API, or deploy `web/` to any host
that supports Next.js.

---

## 5. Health checklist

- [ ] `/api/health` returns `status: ok` and the expected `bike_count`.
- [ ] `ANTHROPIC_API_KEY` set in the host's environment (not in a file), and
      `GET /api/assistant` returns `free_available: true`, if you want free
      chat.
- [ ] `MOTOQUANT_CHAT_DAILY_LIMIT` set to fit your Anthropic budget, if chat
      is enabled.
- [ ] One trusted proxy hop in front of the API, so per-IP fuses key on the
      real client.
