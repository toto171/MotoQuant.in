# Observability: Sentry error tracking and opt-in PostHog

The FastAPI backend has a Sentry integration that does nothing until you set
a DSN in the environment. Local dev and CI run with no change in behaviour
and no network calls.

- Code: [`motoquant/observability.py`](../motoquant/observability.py).
  `init_sentry()` is the single entry point.
- Wiring: called once at API startup in
  [`motoquant/api.py`](../motoquant/api.py) (right after the `FastAPI(...)`
  app is constructed). It is idempotent and safe to call from multiple entry
  points.
- Dependency: `sentry-sdk[fastapi]>=2.0.0` is already in
  [`requirements-api.txt`](../requirements-api.txt). If the package is
  missing, `init_sentry()` logs a warning and does nothing instead of
  crashing.
- Tests: [`tests/test_observability.py`](../tests/test_observability.py) pins
  the no-op-without-DSN contract.

## Behaviour matrix

| `SENTRY_DSN` | `sentry-sdk` installed | Result |
|---|---|---|
| unset / blank | yes | **No-op.** `init_sentry()` returns `False`, no init, no network. |
| set | no | Logs a warning, returns `False`. App still boots. |
| set | yes | Sentry initialised: FastAPI request instrumentation + `ERROR`-level log capture. |

## Enabling it in production

Set one environment variable on the platform that hosts the API. The
backend runs on Render (`api.motoquant.in`), so set it there. The
frontend (Vercel) is separate; see "Frontend" below.

1. Create a project at <https://sentry.io> (the free tier is plenty at current
   traffic) and copy its DSN, which looks like
   `https://<key>@<org>.ingest.sentry.io/<project>`.
2. In the Render dashboard → service `motoquant-api` → *Environment*, add:

   ```
   SENTRY_DSN = https://<key>@<org>.ingest.sentry.io/<project>
   ```

   Do not hardcode the DSN in `render.yaml` or any committed file. Each
   environment (prod / staging / a contributor's laptop) supplies its own,
   and a committed DSN leaks to anyone who clones the repo.
3. Save. Render redeploys, and on the next boot `init_sentry()` finds the
   DSN and starts reporting. The log line
   `Sentry initialised — environment=… release=…` confirms it.

## Optional settings

Each one falls back to the default below when unset.

| Env var | Default | Notes |
|---|---|---|
| `SENTRY_ENVIRONMENT` | `production` (when DSN set) | Override with `staging`, etc. to segment events. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.05` | Fraction of requests that get full performance traces (0.0–1.0). Lower for high traffic; raise for early debugging. |
| `SENTRY_RELEASE` | `motoquant-api@<version>` | Tag events with a release for regression tracking. |
| `SENTRY_SEND_PII` | `false` | Sends usernames/IPs only when set to `true`. Off by default to stay on the safe side of DPDP and other privacy rules. |

## Disabling / rolling back

Delete (or blank) the `SENTRY_DSN` env var and redeploy. Sentry goes back
to doing nothing; no code change is needed.

## Frontend (Vercel): not wired yet

Sentry is wired into the Python API only. The Next.js frontend on Vercel
could add browser and edge error tracking later with
[`@sentry/nextjs`](https://docs.sentry.io/platforms/javascript/guides/nextjs/),
using its own `SENTRY_DSN` (and `NEXT_PUBLIC_SENTRY_DSN`) set in the Vercel
dashboard. That work belongs in `web/` and is not covered here.

## Usage telemetry: PostHog forwarding is opt-in

The web app sends anonymous usage beacons (`web/lib/telemetry.js`: an event
label, numeric/categorical props, a per-tab random session id, the path and
the user agent; no user id, email, IP correlation or free-text input) to
`POST /api/telemetry/event`. That route is rate-limited and size-capped.

| `POSTHOG_API_KEY` | Result |
|---|---|
| unset (default; every self-hosted copy) | Events are written to the API's own log (`TELEMETRY event=…`) **and sent nowhere else.** |
| set | Each event is also forwarded server-side to PostHog (`POSTHOG_HOST`, default the EU cloud), through a bounded worker pool that drops events under backpressure. The browser never talks to PostHog directly and no cookies are set. |

Whoever operates a deployment makes this choice. MotoQuant itself
collects nothing for anyone else. If you enable it on a public instance, say
so in your privacy policy.

## Verifying locally

```bash
# No DSN -> silent no-op (the default):
python -c "from motoquant.observability import init_sentry; print(init_sentry())"
# -> False

# Run the contract tests:
python -m pytest tests/test_observability.py -q
```
