# Commercial Launch Plan — MotoQuant Pro

> Written 2026-07-02 (audit-release session). Grounded in a full code audit of the
> auth/payments/subscriptions surface, the API route inventory, and the web/desktop
> clients. Supersedes the "flip the env var" framing in PAYMENTS_SETUP.md — that doc
> covers the *mechanics* of enabling billing; this one covers what must be true for
> billing to be worth enabling.

## The one-paragraph verdict

The plumbing is done; the product isn't. Auth, unified Razorpay+Stripe payments,
license keys, and the garage all exist and work. But the paid tier barely exists:
the entire tier-gated surface is three routes (save-run @ pro, Dragy import @ studio,
dyno import @ studio) while the crown jewels — Build Optimizer, ECU Autotune,
unlimited sims, AI chat — are ungated public routes. Flipping
`MOTOQUANT_BILLING_ENFORCE=true` today would gate almost nothing worth paying for.
Fix what's free-vs-paid first; the payment keys come last.

## Launch blockers (ordered)

| # | Blocker | State | Action |
|---|---------|-------|--------|
| B1 | **Account durability** — accounts/runs/subscriptions wiped on every deploy (free tier, no disk) | Mechanism shipped (`docker-entrypoint.sh`), disk block ready-but-commented in `render.yaml` | Operator: Render paid plan (~$7/mo) + uncomment disk block + `MOTOQUANT_DB=/data/motoquant.db` |
| B2 | **No paid product** — only 3 routes tier-gated | Gates exist (`require_tier`) but unused on the valuable routes | Gate Build Optimizer + ECU Autotune @ pro; keep calibration @ studio; meter free sims (B3) |
| B3 | **Free-tier metering** | ✅ Shipped this session: `motoquant/usage.py` + `sim_usage` table + quota dependency on `/api/simulate*` (records always; blocks only when billing enforced) | Tune `MOTOQUANT_FREE_DAILY_SIMS` (default 30) |
| B4 | **Abuse/cost protection** — `/api/chat` spends LLM tokens, optimizer pins the 0.5-CPU instance, zero rate limiting | ✅ Shipped this session: in-memory per-IP rate limiter on chat/optimize/autotune | Tune limits after observing real traffic |
| B5 | **Secrets** — dev-insecure `JWT_SECRET` default, SMTP unset | Env vars documented in PAYMENTS_SETUP.md | Operator: set before real accounts |
| B6 | **End-to-end billing test** in provider test mode | Untested against live providers (tests use mocks) | Operator: PAYMENTS_SETUP Step 4 flow |
| B7 | **Backups** — no backup job even with a disk | Missing | Cron `sqlite3 .backup` to object storage; do with B1 |
| B8 | **GST invoice promise** — terms/pricing promise invoices; no generator exists | Missing | Use provider-native invoicing (Razorpay/Stripe both emit) or soften copy |

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
