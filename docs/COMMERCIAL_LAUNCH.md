# Commercial Launch Plan — MotoQuant Pro

> Written 2026-07-02 (audit-release session). Grounded in a full code audit of the
> auth/payments/subscriptions surface, the API route inventory, and the web/desktop
> clients. Supersedes the "flip the env var" framing in PAYMENTS_SETUP.md — that doc
> covers the *mechanics* of enabling billing; this one covers what must be true for
> billing to be worth enabling.

## The one-paragraph verdict

> **Status refreshed 2026-08-10.** The July-2 verdict below is superseded on its
> central point: the paid tier now exists. Build Optimizer, ECU Autotune and the
> Outlaw pipeline (direct **and** job variants), save-run, and the chat agent's
> pro tools are all `require_tier("pro")`; Dragy and dyno import are
> `require_tier("studio")`. What remains is almost entirely operator/account
> work — one purchase (Render Starter + disk) plus env vars — with the code-side
> gaps closed on 2026-08-10.

*(July 2, retained for the record:)* The plumbing is done; the product isn't.
Auth, unified Razorpay+Stripe payments, license keys, and the garage all exist
and work. But the paid tier barely exists: the entire tier-gated surface is
three routes… Flipping `MOTOQUANT_BILLING_ENFORCE=true` today would gate almost
nothing worth paying for.

## Launch blockers (ordered)

| # | Blocker | State | Action |
|---|---------|-------|--------|
| B1 | **Account durability** — accounts/runs/subscriptions wiped on every deploy (free tier, no disk) | ❌ **OPEN — the one hard blocker.** Mechanism shipped (`docker-entrypoint.sh`), disk block ready-but-commented in `render.yaml` | Operator: Render paid plan (~$7/mo) + uncomment disk block + `MOTOQUANT_DB=/data/motoquant.db`. Also fixes free-tier cold starts for paying users. |
| B2 | **No paid product** — only 3 routes tier-gated | ✅ **CLOSED 2026-08-08.** Optimizer / Autotune / Outlaw (+job variants) @ pro, save-run @ pro, calibration @ studio, chat pro tools return typed `upgrade_required` | Pricing-ladder tuning only |
| B3 | **Free-tier metering** | ✅ Shipped: `motoquant/usage.py` + `sim_usage` table | Tune `MOTOQUANT_FREE_DAILY_SIMS` (default 30) |
| B4 | **Abuse/cost protection** | ✅ Shipped: per-IP rate limiter on chat/optimize/autotune | Tune after observing real traffic |
| B5 | **Secrets** — dev-insecure `JWT_SECRET` default, email unset | ❌ OPEN (operator env). Boot now *hard-fails* on the default JWT secret when billing is enforced | Operator: PAYMENTS_SETUP Step 1 |
| B6 | **End-to-end billing test** in provider test mode | ❌ OPEN — untested against live providers (tests use mocks) | Operator: PAYMENTS_SETUP Step 4 flow |
| B7 | **Backups** | ✅ **CLOSED 2026-08-10:** `scripts/backup_db.py` — hot online-backup, integrity-verified, gzipped, rotated, optional off-box upload hook | Operator: schedule as a Render Cron Job once the disk exists |
| B8 | **GST invoice promise** — terms/pricing promised 18% GST + provider-issued tax invoices | ✅ **CLOSED 2026-08-10:** operator confirmed unregistered sole proprietorship below the ₹20 L services threshold → no GSTIN, cannot collect GST. All copy corrected to "no GST charged" with a forward clause for crossing the threshold | Revisit at ₹20 L turnover |
| B9 | **Payment-provider website checklist** — no contact page, no address/phone, refund policy buried in ToS §5 and not footer-linked | ✅ **CLOSED 2026-08-10:** standalone `/refunds` + `/contact`, both footer-linked, sitemapped and crawlable | Operator: fill `BUSINESS` in `web/app/contact/page.js` with the exact KYC address/phone |
| B10 | **Magic-link sign-in was silently dead in prod** — backend defaulted to `stdout` and short-circuited the send guard, so configuring SMTP per the runbook sent nothing while the API answered "Sign-in link sent"; Resend was documented in 3 places with zero implementation | ✅ **CLOSED 2026-08-10:** transport derived from configured env vars, Resend implemented (stdlib urllib), deployed-without-transport returns 503 instead of lying, boot warning added, 18 regression tests | — |

## Operator env checklist (July 2 functional audit — features that work, waiting only on keys)

> Every flow below is code-complete and verified end-to-end (36/36 functional
> checks); each lights up with ZERO code changes the moment its env vars land
> on Render (Dashboard → motoquant-api → Environment). Operator confirmed
> July 2 they will set these up.

| Feature | Current behavior (unset) | Env vars to set |
|---|---|---|
| **Magic-link EMAILS** | Deployed + unconfigured now returns a clear 503 (was: silently sent nothing while reporting success). Password sign-in unaffected | `RESEND_API_KEY` + `SMTP_FROM` (recommended — verify the sending domain first) or `SMTP_HOST/PORT/USER/PASS/FROM`. Transport is auto-detected; no enable flag |
| **AI chat** | Honest "LLM not configured" banner in the UI | `GROQ_API_KEY` + `LLM_PROVIDER=groq` (or `ANTHROPIC_API_KEY`) |
| **Live weather for un-seeded cities** | Seeded 20 venues resolve fine; unknown cities → clean 503 | `OPENWEATHERMAP_API_KEY` |
| **Real checkout** | Beta CTA routes to free signup; `/api/payments/checkout` → friendly 503 | Razorpay keys + plan IDs, Stripe keys + price IDs per `PAYMENTS_SETUP.md`, then `MOTOQUANT_BILLING_ENFORCE=true` |
| **Session security hardening** | Dev-default JWT secret | `JWT_SECRET` (32-byte random) — set BEFORE real accounts (B5) |
| **Account durability** | Accounts/runs wiped on redeploy (no disk) | Render paid disk + `MOTOQUANT_DB=/data/motoquant.db` (B1) |
| **Error tracking** | Sentry wired, no-op | `SENTRY_DSN` |
| **Product analytics** | PostHog forwarding wired, no-op | `POSTHOG_API_KEY` (+ `NEXT_PUBLIC_POSTHOG_KEY` on Vercel) |

## Feature ladder (revenue-impact ÷ effort)

1. **Free-sim quota + Pro-gating the Optimizer/Autotune** — the conversion lever. *(metering shipped this session; gating decision is the operator's pricing call)*
2. **Public shareable run pages + OG cards** — viral loop, WhatsApp-first market. *(shipped this session: `GET /api/runs/{id}` + `/r/[id]` timeslip page)*
3. **Per-venue leaderboards on the web** — competition = retention. *(shipped this session: `venue_id` filter + `/leaderboard` page)*
4. **PDF timeslip/build report (Pro)** — port desktop's jsPDF export to web.
5. **Dragy-upload → calibrated-garage-bike wizard (Studio)** — the calibration moat; API exists, needs a web wizard.
6. **Referral codes** — cheapest growth channel; provider coupons + a code table.
7. **B2B tuning-shop dashboard / API keys** — defer until the first shop conversation.

## Explicitly NOT yet

- No `BILLING_ENFORCE=true` until B1–B3 are all live in prod.
- No SQLite→Postgres migration (persistent disk covers launch scale).
- No PayPal (Razorpay UPI + Stripe cover the market).
- No more physics-accuracy work as a *launch gate* (data-limited, already credible).
- No desktop binaries as a launch dependency (hosted web is the funnel).
- No PINN / 3D viz / MCP server until there are paying users.

## Analytics

Telemetry events already flow from `web/lib/telemetry.js` → `POST /api/telemetry/event`.
As of this session the route forwards to PostHog (EU) when `POSTHOG_API_KEY` is set
(project "Motoquant", id 213355) — stdout logging is kept as the fallback so the
behavior without the key is unchanged. Server-side capture, no cookies — stays inside
the privacy page's consent promise.
