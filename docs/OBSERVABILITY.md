# Observability — Sentry error tracking

MotoQuant ships an **env-gated** Sentry integration for the FastAPI backend.
It is wired and ready, but **does nothing until you supply a DSN** — local dev
and CI run with zero behaviour change and zero network calls.

- Code: [`motoquant/observability.py`](../motoquant/observability.py) —
  `init_sentry()` is the single entry point.
- Wiring: called once at API startup in
  [`motoquant/api.py`](../motoquant/api.py) (right after the `FastAPI(...)`
  app is constructed). It is idempotent and safe to call from multiple entry
  points.
- Dependency: `sentry-sdk[fastapi]>=2.0.0` is already in
  [`requirements-api.txt`](../requirements-api.txt). If the package is somehow
  missing, `init_sentry()` logs a warning and no-ops rather than crashing.
- Tests: [`tests/test_observability.py`](../tests/test_observability.py) pins
  the no-op-without-DSN contract.

## Behaviour matrix

| `SENTRY_DSN` | `sentry-sdk` installed | Result |
|---|---|---|
| unset / blank | yes | **No-op.** `init_sentry()` returns `False`, no init, no network. |
| set | no | Logs a warning, returns `False`. App still boots. |
| set | yes | Sentry initialised: FastAPI request instrumentation + `ERROR`-level log capture. |

## Enabling it in production

Sentry is activated by setting **one** environment variable on whichever
platform hosts the API. As of this writing the backend runs on **Render**
(`motoquant-api.onrender.com`); set it there. The frontend (Vercel) is a
separate concern — see "Frontend" below.

1. Create a project at <https://sentry.io> (the free tier is plenty at current
   traffic) and copy its **DSN** (looks like
   `https://<key>@<org>.ingest.sentry.io/<project>`).
2. In the **Render dashboard** → service `motoquant-api` → *Environment* → add:

   ```
   SENTRY_DSN = https://<key>@<org>.ingest.sentry.io/<project>
   ```

   Do **not** hardcode the DSN in `render.yaml` or any committed file — each
   environment (prod / staging / a contributor's laptop) supplies its own, and
   a committed DSN leaks to anyone who clones the repo.
3. Save → Render redeploys → the next boot calls `init_sentry()`, sees the DSN,
   and starts reporting. The log line `Sentry initialised — environment=… release=…`
   confirms it.

## Optional tuning knobs

All optional; sensible defaults apply when unset.

| Env var | Default | Notes |
|---|---|---|
| `SENTRY_ENVIRONMENT` | `production` (when DSN set) | Override with `staging`, etc. to segment events. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.05` | Fraction of requests that get full performance traces (0.0–1.0). Lower for high traffic; raise for early debugging. |
| `SENTRY_RELEASE` | `motoquant-api@<version>` | Tag events with a release for regression tracking. |
| `SENTRY_SEND_PII` | `false` | Send usernames/IPs only if explicitly `true`. Left off by default to stay on the safe side of DPDP / privacy regs. |

## Disabling / rolling back

Delete (or blank) the `SENTRY_DSN` env var and redeploy. The integration
reverts to a no-op — no code change required.

## Frontend (Vercel) — not yet wired

This integration covers the **Python API only**. The Next.js frontend on Vercel
could add browser + edge error tracking later via
[`@sentry/nextjs`](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
with its own `SENTRY_DSN` (and `NEXT_PUBLIC_SENTRY_DSN`) set in the **Vercel**
dashboard. That work lives in `web/` and is out of scope here — flagged so it is
not forgotten.

## Verifying locally

```bash
# No DSN -> silent no-op (the default):
python -c "from motoquant.observability import init_sentry; print(init_sentry())"
# -> False

# Run the contract tests:
python -m pytest tests/test_observability.py -q
```
