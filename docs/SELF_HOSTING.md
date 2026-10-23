# Self-hosting MotoQuant

MotoQuant is free and open source (Apache-2.0). Everything that runs
<https://www.motoquant.in> is in this repository, and you can run your own
copy: on a laptop, on Render + Vercel the way the public instance does, or on
any host that runs Docker.

There is no billing, licence-key or payment-provider configuration of any
kind. **Every environment variable on this page is optional.** With none of
them set, the API serves the simulator, catalog, optimizer, autotune,
leaderboard and optional accounts.

The full annotated variable list is in [`.env.example`](../.env.example) at
the repo root. This page explains what each group is for and how to deploy.

---

## 1. Run it locally (five minutes)

Requirements: Python 3.10+ (CI and the Docker image use 3.11) and Node 18+ for
the web frontend.

```bash
git clone https://github.com/da25mem5s02-debug/MotoQuant_v1.git
cd MotoQuant_v1

make install      # runtime + dev deps, editable motoquant package
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

Locally, sign-in links are printed to the API's stdout instead of being
emailed, and sessions are signed with the public development JWT secret.
That is fine on your own machine and wrong anywhere else; section 3 covers
what to set on a real host.

---

## 2. Architecture of a deployment

```
browser ──► web (Next.js, static + one route handler) ──/api/* rewrite──► API (FastAPI + SQLite)
```

- **API**: `motoquant/api.py`, served by uvicorn from the root
  [`Dockerfile`](../Dockerfile). It runs a single process
  ([`docker-entrypoint.sh`](../docker-entrypoint.sh)). Keep it that way:
  the job registry, rate-limit counters and (when no `JWT_SECRET` is set) the
  ephemeral signing secret all live in process memory.
- **Database**: one SQLite file. The image carries the seeded copy at
  `/app/motoquant.db`.
- **Web**: `web/` (Next.js App Router). The browser calls same-origin
  `/api/*`, and `web/next.config.js` (plus the root `vercel.json` on Vercel)
  rewrites those calls to the API. `MOTOQUANT_API_BACKEND` overrides the
  rewrite target at build time; `NEXT_PUBLIC_API_URL` makes the browser call
  an absolute API URL directly instead (used by `make web-dev`).

---

## 3. Settings for a real host

### 3a. Tell the API it is deployed

Render sets `RENDER` and `RENDER_EXTERNAL_URL` automatically. **On any other
host, set `MOTOQUANT_DEPLOYED=1`.** A deployed API:

- never echoes magic-link tokens in HTTP responses (the dev convenience that
  makes local sign-in work without email), and
- never signs sessions with the public development JWT secret.

### 3b. `JWT_SECRET` — keeps optional sign-ins alive across restarts

| Situation | What the API signs sessions with |
|---|---|
| `JWT_SECRET` set (32+ random bytes) | Your secret. Sessions survive restarts and redeploys. |
| Deployed host, `JWT_SECRET` unset (or left at the public default) | An **ephemeral, per-process random secret**, plus a loud boot warning. Tokens cannot be forged, but every sign-in resets whenever the process restarts. The API never refuses to boot over this; accounts are optional and must not take the simulator down. |
| Local / tests | The documented public dev default, with a warning. |

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"   # or: openssl rand -hex 32
```

### 3c. Magic-link email transport

Password sign-in works with no email configured. Magic links (passwordless
sign-in) need a transport, chosen from whatever you set:

| Set | Transport |
|---|---|
| `RESEND_API_KEY` + `SMTP_FROM` | [Resend](https://resend.com) HTTP API (highest precedence). Verify the sending domain in the Resend dashboard first, or Resend answers 403. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` | Plain SMTP (STARTTLS). |
| neither | Dev mode: the link is printed to stdout. |

Precedence is `MOTOQUANT_EMAIL_BACKEND` (an explicit `resend` / `smtp` /
`stdout` override) → Resend → SMTP → stdout. `SMTP_FROM` is the From address
for both transports. Set `MOTOQUANT_BASE_URL` to your web origin so the links
point at your site rather than motoquant.in.

On a deployed host with no transport, `POST /api/auth/magic-link` answers
**503** instead of claiming that an email was sent, and the API logs a
warning at boot.

> History: before 2026-08-10, `MOTOQUANT_EMAIL_BACKEND` defaulted to `stdout`
> and short-circuited the send guard, so a correctly configured SMTP host
> still sent nothing while the API reported success. The transport is now
> derived from what you configure. If magic links "send" but never arrive on
> an older checkout, that bug is why.

### 3d. Durable storage — persistent disk for accounts and saved runs

The catalog is read-only, but optional accounts, sessions and saved runs (the
leaderboard and each user's garage) are written to the same SQLite file. In
the image that file lives at `/app/motoquant.db` and **is replaced on every
deploy**. On a free hosting plan with no disk, that is the trade: accounts and
saved runs reset whenever you deploy.

To keep them, put the DB on a persistent volume:

1. Mount a volume (Render: a paid instance plus a disk; any Docker host: a
   named volume or bind mount) at, say, `/data`. It must be writable by the
   image's unprivileged `app` user.
2. Set `MOTOQUANT_DB=/data/motoquant.db`.

`docker-entrypoint.sh` copies the seeded catalog onto the volume on first
boot and leaves it alone on every boot after that. When `MOTOQUANT_DB` is the
baked `/app` path it does nothing, so the same image works with or without a
disk.

For Render, both edits are already in [`render.yaml`](../render.yaml) as
comments: uncomment the `disk:` block and switch `MOTOQUANT_DB` to
`/data/motoquant.db`. To verify, register a test account, deploy, and check
that the account is still there. `/api/health` should report the same
`bike_count` as before.

> **Catalog updates on a persistent disk.** Because the entrypoint never
> overwrites an existing DB, a deploy that ships a newer catalog in
> `motoquant.db` does not reach a disk-backed instance automatically. Apply
> catalog changes to the live file with the repo's idempotent
> `scripts/patch_*.py` scripts, or re-seed from the image deliberately after
> taking a backup.

### 3e. Backups — set these up with the disk

[`scripts/backup_db.py`](../scripts/backup_db.py) takes a hot,
integrity-checked, gzipped snapshot with SQLite's online-backup API, which is
safe to run against concurrent writers including WAL mode, and prunes old
snapshots down to the newest N.

```bash
python scripts/backup_db.py --db /data/motoquant.db --keep 14
```

Snapshots go to `<db-dir>/backups` by default. That protects against a bad
migration or an errant `DELETE`, but not against losing the disk. Set
`MOTOQUANT_BACKUP_UPLOAD_CMD` to copy each snapshot off the box; `{path}` is
replaced with the snapshot's path:

```bash
MOTOQUANT_BACKUP_UPLOAD_CMD='rclone copy {path} r2:motoquant-backups/'
```

Exit codes: `0` ok · `1` backup failed · `2` snapshot ok but upload failed.
Run it daily (a Render Cron Job, systemd timer or plain cron).

### 3f. Chat agent (`POST /api/chat`)

The chat agent needs an LLM provider. Set `LLM_PROVIDER` (`groq` is the
default; also `gemini`, `anthropic`, `deepseek`, `openrouter`) and that
provider's key (`GROQ_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, …).
Without a key, chat answers `llm_not_configured` and everything else still
works. The CLI's `nl` subcommand needs no key at all.

Whoever runs a deployment pays for its LLM key, so chat has two fuses:

- a per-minute per-IP rate limit, and
- `MOTOQUANT_CHAT_DAILY_LIMIT`: chat turns per client IP per rolling 24 h
  (default **200**). Set it to `0` to disable the cap, for example when you
  use your own key or a local model.

Agent web lookup is optional: `SEARCH_PROVIDER=brave|serper` plus
`SEARCH_API_KEY` upgrade the `web_search` tool from the keyless DuckDuckGo
HTML fallback. `MOTOQUANT_WEB_TOOLS=0` turns the agent's web access off.
Details: [CHAT_AGENT.md](CHAT_AGENT.md).

### 3g. Abuse fuses (on by default)

Every simulation and analysis route is free and anonymous, so each
compute-heavy route has a per-IP fixed-window rate limit (`motoquant/ratelimit.py`):
simulate, top speed, distance, compare, optimizer, autotune, calibration
uploads, saving a run, telemetry, and chat. Over the limit, a route answers
`429` with a `Retry-After` header. The client IP is the **rightmost**
`X-Forwarded-For` hop, which assumes exactly one trusted proxy in front of
the API (Render's edge). If you put more proxies in front, adjust
`client_ip()` accordingly.

`MOTOQUANT_RATE_LIMIT=false` disables every limit. Use it for tests, not for
a public instance. These counters are in-process; for multi-replica or
DDoS-grade protection, rate-limit at your edge as well.

### 3h. Optional extras

| Variable | Effect |
|---|---|
| `OPENWEATHERMAP_API_KEY` | Live venue weather for the `weather` CLI (`weather --refresh-all`). Without it, venues use their stored seasonal data. |
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
- `motoquant/keepwarm.py`: in-app self-ping (section 3h).

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
docker volume create motoquant-data
docker run -d --name motoquant-api -p 8000:8000 \
  -e MOTOQUANT_DEPLOYED=1 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e MOTOQUANT_DB=/data/motoquant.db \
  -v motoquant-data:/data \
  motoquant-api
curl http://localhost:8000/api/health
```

Generate `JWT_SECRET` once and store it (in a secrets manager or a `.env`
file passed with `--env-file`) rather than regenerating it on every run, or
sessions will reset. If the volume's mount point is owned by root, make it
writable by the container's `app` user (uid 1000 in the stock image).

Terminate TLS in a reverse proxy such as Caddy or nginx and keep exactly one
proxy hop in front of the API (see 3g). For the web frontend, run
`cd web && npm ci && npm run build && npm start` behind the same proxy with
`MOTOQUANT_API_BACKEND` pointing at the API, or deploy `web/` to any host
that supports Next.js.

---

## 5. Health checklist

- [ ] `/api/health` returns `status: ok` and the expected `bike_count`.
- [ ] `MOTOQUANT_DEPLOYED=1` (non-Render hosts) and a stored `JWT_SECRET`.
- [ ] Persistent disk mounted and `MOTOQUANT_DB` points at it (if you want
      accounts and saved runs to survive deploys).
- [ ] `scripts/backup_db.py` scheduled, with an off-box upload command.
- [ ] An email transport configured, or you accept password-only sign-in.
- [ ] `MOTOQUANT_CHAT_DAILY_LIMIT` set to fit your LLM budget, if chat is
      enabled.
- [ ] One trusted proxy hop in front of the API, so per-IP fuses key on the
      real client.
