# ADR-0006: Monetization scrapped — MotoQuant is free and open source

**Status:** Accepted (amends [ADR-0005](0005-desktop-discontinued.md); supersedes
the "pro-gated" rows of [CLIENT_COMPUTE.md](../CLIENT_COMPUTE.md))
**Date:** 2026-10-23
**Deciders:** Hritwik Mudhai (operator decision)

## Context

From June to August 2026 MotoQuant was built as a freemium SaaS. The plan was
a free tier with a daily sim quota, "Pro" (₹499/mo) and "Studio" (₹1,999/mo)
tiers sold through Razorpay and Stripe, device-bound license keys, and a
`MOTOQUANT_BILLING_ENFORCE` switch that turned the gates on. That switch never
went to `true`, no payment was ever taken, and the payment tables shipped
empty.

Keeping the commercial machinery cost a lot relative to what it did:

- Every analysis route carried a tier gate. Every response could carry a 402
  `upgrade_url`. Chat had a "pro tools" path, and saving a run had a quota.
  Each of these needed tests in both billing modes.
- Two payment providers, webhook ledgers, refund and GST copy, KYC pages,
  and a `/pricing` page whose claims had to be audited against real
  enforcement more than once (`reports/` has the drift).
- The licence was proprietary in practice. The site's terms forbade reverse
  engineering, while the project's main credibility claim (an auditable,
  benchmark-validated physics engine) depends on people being able to read
  the code.

The operator decided to scrap monetization and release the project as free,
open-source software.

## Decision

**MotoQuant is free and open source under the Apache License 2.0.**
Everything is free. There are no tiers, quotas, plans, prices or licence keys.

### License

- Code: **Apache-2.0** (`LICENSE` at the repo root, unmodified text).
  Apache-2.0 was chosen over MIT for its explicit patent grant and its
  `NOTICE` mechanism. The `NOTICE` file carries the copyright line
  "Copyright 2026 Hritwik Mudhai and the MotoQuant contributors" and the
  attribution notes for third-party trademarks, cited benchmark figures and
  public-source catalog specs.
- Inbound contributions are accepted under the same licence (Apache-2.0 §5),
  as `CONTRIBUTING.md` states.
- Canonical source: <https://github.com/da25mem5s02-debug/MotoQuant_v1>.
- Brand: "MotoQuant Pro" → **"MotoQuant"** on every user-facing surface, doc,
  API title and CLI help. "Pro" read as a paid tier. Historical records
  (`CHANGELOG.md` entries, `reports/`, the `CLAUDE.md` history chain) are not
  rewritten.

### Removed

| Area | What went |
|---|---|
| Backend | `motoquant/payments.py`, `motoquant/subscriptions.py`, `motoquant/usage.py`, `motoquant/database/subscriptions_repo.py`; `require_tier`, `MOTOQUANT_BILLING_ENFORCE`, every 402 / `upgrade_required` / `upgrade_url` path; the `X-Sims-Remaining` header; the chat agent's "pro tools" gate; checkout and Razorpay/Stripe webhook routes; license-key routes. |
| Data | Tables `subscriptions`, `license_keys`, `payment_events`, `sim_usage` and columns `users.tier`, `users.razorpay_customer_id`, `users.stripe_customer_id`, dropped from the shipped `motoquant.db` by the idempotent `scripts/patch_2026_10_23_drop_monetization.py`. The boot-time code that re-created them is gone. Older DBs that still carry `users.tier` keep working: no code reads it, and it has a default. |
| Web | `/pricing` and `/refunds` (now permanent redirects in `web/next.config.js`), `TierBadge`/`UpgradeCTA`, tier labels, the account page's subscription / license-key / cancel sections, every "free during beta" and paid-tier claim. `/contact` was rewritten as a community page (GitHub issues and discussions, security contact). |
| Desktop | The `desktop/` tree (scrapped by ADR-0005, kept for reference until now; it called the license-key endpoints) and the retired desktop `release.yml` workflow. Its install and release docs moved to `docs/archive/`. |
| Docs | The payments runbook, commercial-launch plan, team-scaling plan, SEO growth plan and unsent B2B outreach drafts moved to `docs/archive/` with a banner. The still-relevant deployment steps (persistent disk, `JWT_SECRET`, magic-link email transport, backups) moved first into [SELF_HOSTING.md](../SELF_HOSTING.md). |

### Kept (none of this was monetization)

- **Optional accounts**: magic-link and password sign-in, sessions,
  `/api/auth/me`, the `/api/me/runs` garage, and run attribution on save.
  Signing in only attributes saved runs. Every simulation and analysis route
  works anonymously.
- The leaderboard and anonymous saves (rate-limited).
- **Per-IP rate limiting** (`motoquant/ratelimit.py`).
- Parts INR prices, `/api/pricing/*` parts routes, `budget_inr` and ROI
  cost-per-tenth. These are product features (what a build costs), not
  billing.
- The chat agent's per-turn budgets and build stages (`stage_1`..`stage_4`),
  and the fitment/scraper `tier` fields (compatibility tiers, unrelated to
  billing).
- Env-gated PostHog telemetry forwarding, now documented as **opt-in**: off
  unless the operator sets `POSTHOG_API_KEY`. Env-gated Sentry.

### Abuse fuses replace quotas

The free-tier sim quota and the paid gates also limited how much compute and
LLM spend one client could consume. Once they are gone, any route that the
quota alone had protected needs its own fuse, added in the same change:

- per-IP rate limits on `POST /api/simulate/distance`,
  `POST /api/simulate/compare` and `POST /api/jobs/compare` (the last two
  share one bucket), alongside the existing limits on simulate, top speed,
  optimizer, autotune, calibration uploads, save and telemetry;
- a per-IP **daily** chat cap, `MOTOQUANT_CHAT_DAILY_LIMIT` (default 200
  turns per rolling 24 h; `0` disables it), which caps the LLM bill for
  whoever runs a deployment;
- a fix to `ratelimit.py` eviction. Expiry used the *caller's* window, so a
  60 s-window call could evict a daily-window counter and silently reset the
  chat cap. Each key now expires on its own window.

### JWT secret policy, re-keyed off billing

The old boot guard refused to start with the public default `JWT_SECRET`
only when billing was enforced. The new policy: on a deployed host (`RENDER`,
`RENDER_EXTERNAL_URL` or `MOTOQUANT_DEPLOYED=1`) with no real `JWT_SECRET`,
the API generates an **ephemeral per-process random secret** and logs a loud
warning. Sessions reset on restart, tokens are never forgeable, and boot
never fails. Local dev keeps the documented dev default. See
[SELF_HOSTING.md §3b](../SELF_HOSTING.md) and
[INVARIANTS.md](../INVARIANTS.md) I7.

## Consequences

- **Positive.** The accuracy claims can now be audited: anyone can read the
  engine, rerun the sweep and file a benchmark. The surface area shrank by
  four backend modules, four tables, two web routes, a desktop tree and every
  dual-mode billing test. Self-hosting is now a supported use, with its own
  doc. Compute placement no longer has to protect a paid tier.
- **Negative.** There is no revenue path. Whoever hosts a deployment pays its
  costs, including the LLM key. The daily chat cap and the rate limits are
  the protection, and they are per-instance in-memory counters, not a DDoS
  defence. Edge rate limiting is still the operator's job.
- **Neutral.** Accounts stay but remain optional; their durability still
  depends on a persistent disk (`SELF_HOSTING.md §3d`). The B2B "Pro Studio"
  idea is dead. Tuning shops are now invited to contribute data (instrumented
  Dragy runs, dyno sheets) rather than buy seats.

### Effect on other records

- **ADR-0005** said "license keys survive as a product feature
  (device-bound seats)". That clause is superseded: license keys are gone.
- **CLIENT_COMPUTE.md** gave "the paid product" as the reason Build
  Optimizer / Autotune / Outlaw were server-only and pro-gated. That reason
  no longer applies. They stay server-side for now because they orchestrate
  hundreds of sims and the knapsack/ROI machinery, but they are now
  candidates for client-side execution like everything else.

## References

`LICENSE` · `NOTICE` · [SELF_HOSTING.md](../SELF_HOSTING.md) ·
`scripts/patch_2026_10_23_drop_monetization.py` ·
`tests/test_open_source_pivot.py` · `CHANGELOG.md` (2026-10-23 entry) ·
`docs/archive/` (payments runbook, commercial-launch plan).
