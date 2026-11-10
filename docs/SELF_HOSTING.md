# Self-hosting MotoQuant

MotoQuant is free and open source (Apache-2.0). Everything that runs
<https://www.motoquant.in> is in this repository, and you can run your own
copy: on a laptop, on Render + Vercel the way the public instance does, or on
any host that runs Docker.

There is no billing, account or email configuration of any kind, and the
server stores nothing a visitor sends. **Every environment variable on this
page is optional.** With none of them set, the API serves the simulator,
catalog, optimizer, race-day setup and leaderboard.

The full annotated variable list is in [`.env.example`](../.env.example) at
the repo root. This page explains what each group is for and how to deploy.

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

- **API**: `motoquant/api.py`, served by uvicorn from the root
  [`Dockerfile`](../Dockerfile). It runs a single process
  ([`docker-entrypoint.sh`](../docker-entrypoint.sh)). Keep it that way:
  the job registry, the rate-limit counters and the weather and catalog
  caches all live in process memory.
- **Database**: one SQLite file, read-only in practice. The image carries the
  seeded catalog at `/app/motoquant.db`, so every deploy ships the latest
  catalog and nothing needs a persistent disk.
- **Web**: `web/` (Next.js App Router). The browser calls same-origin
  `/api/*`, and `web/next.config.js` (plus the root `vercel.json` on Vercel)
  rewrites those calls to the API. `MOTOQUANT_API_BACKEND` overrides the
  rewrite target at build time; `NEXT_PUBLIC_API_URL` makes the browser call
  an absolute API URL directly instead (used by `make web-dev`).

---

## 3. Settings for a real host

### 3a. Chat agent (`POST /api/chat`)

The chat agent needs an LLM provider. Set `LLM_PROVIDER` (`groq` is the
default; also `gemini`, `anthropic`, `deepseek`, `openrouter`) and that
provider's key (`GROQ_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, …).
Without a key, chat answers `llm_not_configured` and everything else still
works. The CLI's `nl` subcommand needs no key at all.

The chat is a multi-step tool-calling agent (up to 8 tool rounds per turn),
so tool-use reliability matters more than raw speed. Free providers are fine
for a public demo; `anthropic` (Claude) gives the most reliable multi-step
tool use but is billed per token — each chat turn makes 2-8 LLM calls, so pair
it with a sensible daily cap. `ANTHROPIC_MODEL` (and `GEMINI_MODEL` /
`GROQ_MODEL`) override the default model per provider.

Whoever runs a deployment pays for its LLM key, so chat has two fuses:

- a per-minute per-IP rate limit, and
- `MOTOQUANT_CHAT_DAILY_LIMIT`: chat turns per client IP per rolling 24 h
  (default **200**). Set it to `0` to disable the cap, for example when you
  use your own key or a local model.

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

- **unset (auto):** trust 1 hop on Render (the `RENDER` env var) or when the
  connection comes from loopback, a unix socket or a private-network peer
  (Docker bridge + nginx/Caddy); otherwise trust none and key on the socket
  peer.
- **`0`:** never trust the header (API exposed directly to the internet).
- **`N`:** you run N appending proxies; the client is the N-th hop from the
  right.

Invalid values fail closed to 0 with a warning. Trusting more hops than you
actually run lets clients spoof their IP and dodge the limits.

`MOTOQUANT_RATE_LIMIT=false` disables every limit. Use it for tests, not for
a public instance. These counters are in-process; for multi-replica or
DDoS-grade protection, rate-limit at your edge as well.

### 3c. Optional extras

| Variable | Effect |
|---|---|
| `OPENWEATHERMAP_API_KEY` | Live weather when a visitor names a place, and for the `weather` CLI (`weather --refresh-all`). Successful lookups are cached for ten minutes. Without a key, a place keeps the default conditions and seeded venues use their stored seasonal data. |
| `SENTRY_DSN` (+ `SENTRY_ENVIRONMENT`, `SENTRY_RELEASE`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_SEND_PII`) | Error tracking. A no-op unless the DSN is set. See [OBSERVABILITY.md](OBSERVABILITY.md). |
| `POSTHOG_API_KEY` (+ `POSTHOG_HOST`) | **Opt-in** forwarding of the anonymous web telemetry beacon to PostHog. Unset, beacons are written to the server log only and nothing is sent to a third party. |
| `MOTOQUANT_KEEPWARM_URL` / `MOTOQUANT_KEEPWARM_INTERVAL_S` | In-app self-ping that keeps a sleeping free-tier host awake during the day. Starts automatically on Render (from `RENDER_EXTERNAL_URL`); off elsewhere unless you set the URL. |

---

## 4. Deploying

### 4a. Render (API) + Vercel (web) — how motoquant.in runs

**API on Render.** [`render.yaml`](../render.yaml) is a Render Blueprint:
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
- `web/app/api/wake/route.js` + the `crons` block in `vercel.json`: Vercel
  cron.
- `motoquant/keepwarm.py`: in-app self-ping (section 3c).

**Web on Vercel.** Import the repo with **root directory `web`**. Point the
`/api/*` rewrite at your API: edit the destination in the root
`vercel.json`, or set `MOTOQUANT_API_BACKEND` for the rewrite in
`web/next.config.js`. Leave `NEXT_PUBLIC_API_URL` empty in production so the
browser stays same-origin, which also avoids CORS and DNS-filter problems
with PaaS domains. Before pushing anything under `web/`, run
`make web-build` (it is exactly what Vercel runs).

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
- [ ] `MOTOQUANT_CHAT_DAILY_LIMIT` set to fit your LLM budget, if chat is
      enabled.
- [ ] One trusted proxy hop in front of the API, so per-IP fuses key on the
      real client.
