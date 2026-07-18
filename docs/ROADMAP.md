# Engineering roadmap — the path to a durable business

> Honest, prioritized, and tied to real blockers. This is the "what to do next
> and why" for whoever is at the keyboard — a model, a human, or the operator.
> Re-rank it as reality changes; don't let it rot. Last substantive revision:
> 2026-07-06 (PR #100).

## North star

- **$1M valuation by 2026-12-31, $10M by 2027-12-31**, via **B2C freemium**
  (basic sim + gear tools free) + **B2B Pro Studio** (full optimization + AI
  calibration for tuning shops / teams), with acquisition optionality. All three
  share the same prerequisites: *more validated benchmarks, more content &
  visibility, and a product that stays up and correct under real load.*

## The honest reality

The **code is not the bottleneck.** The engine is validated, the product is live
(`motoquant.in` on Vercel, API on Render), and the test suite is deep. The
things standing between here and revenue are, in order:

1. **Operator actions** — payment-provider config, prod DB durability. No code
   ships revenue until these are done.
2. **Data** — small-cc accuracy is *data-limited, not model-limited*; it needs
   real instrumented Dragy timeslips, which is an outreach/partnership problem.
3. **One real engineering scaling blocker** — the shared SQLite connection.

Everything below is ranked by *what unblocks revenue or prevents an outage*, not
by what's fun to build.

## P0 — Do before scaling or charging money

| # | Item | Owner | Why | Success metric |
|---|---|---|---|---|
| P0-1 | **Payment providers live** (Razorpay + Stripe keys, plans, `MOTOQUANT_BILLING_ENFORCE=1`) | Operator | No revenue path exists until this is flipped. Code is complete (`docs/PAYMENTS_SETUP.md`). | First successful paid checkout in prod. |
| P0-2 | **Prod DB durability** (Render persistent disk, ~$7/mo; `docker-entrypoint.sh` already seeds it) | Operator | Every deploy currently wipes user accounts/runs. Cannot retain paying users on an ephemeral DB. | Accounts survive a deploy. |
| P0-3 | **Fix the shared SQLite connection before multi-worker** (per-thread / pooled conn, or the Postgres migration) | Engineering | KNOWN_TRAPS T14 / ADR-0004: one `check_same_thread=False` connection is shared across request + job threads; concurrent writes can interleave. Fine at 1 worker, corrupts under scale. | 2+ workers pass a concurrent read/write stress test with no interleave/errors. |
| P0-4 | **Rotate any exposed credentials + wire the secret-scan gate** (done in CI as of PR #100) | Operator + Eng | Tokens have historically been pasted into chats/docs. CI now blocks token-shaped strings; operator must rotate anything already leaked. | `make health` secret scan clean; PATs/keys rotated. |

## P1 — Correctness & hardening

**Fixed in PR #100** (was deferred): magic-link token echo in prod (account
takeover), `consume_magic_link` double-consume race, `get_or_create_user` race,
`simulate_distance` empty-array 500, `ratelimit` overflow now evicts oldest-first
(no longer wipes everyone), a `busy_timeout` on the DB connection, the chat
citation XSS, the login `?next=` backslash open-redirect, and least-privilege
`permissions` on the read-only CI workflows.

**Still deferred** (verified real; each needs a focused/coordinated pass — see the
PR #100 review report in `reports/`):

- **License-key device binding is bypassable by omitting `device_id`** — but the
  no-device path is *test-pinned* for legacy clients (`test_subscriptions.py`).
  Now that the desktop client is scrapped (ADR-0005), make the policy call: drop
  legacy tolerance, update the pinned test, and decide whether the unauthenticated
  `/license-key/validate` route should be rate-limited. Do before charging money.
- **Razorpay webhook has no idempotency ledger** (the Stripe path does) — mirror
  `record_payment_event` in the Razorpay handler. Payments are beta-inert, so
  land it alongside the payment-provider go-live (P0-1).
- **`python-jose` is effectively unmaintained** (known CVEs) — migrate JWT to
  `PyJWT` (or `authlib`). A dependency swap with its own test pass.
- **Dockerfile runs as root** — add a non-root `USER`; verify the Render build
  still works (small deploy risk, hence its own change).
- **`bike_repo`/`venue_repo` `lastrowid==0` misread** — prefer
  `rowcount==0`; import-path only, guarded by idempotency tests (change carefully).
  *(`tire_repo` was already fixed July 6 — the earlier mention of it here was
  stale; bike/venue repos are in scope for the 2026-07-17 orchestrated run.)*
- **Dead `CategoryProfile` knobs** — either wire (with a liveness test) or delete.
- *Already resolved — do NOT re-implement:* the license-key **revoke route** and
  the auth **timing-safe compare + bounded fail-tracker** hardening (July-3
  inventory items A1-5/A1-6) landed long ago; sessions keep re-scoping them from
  the stale `reports/ROADMAP_2026_07_03.md` inventory. Verified done in the
  2026-07-17 scope pass (`reports/SCOPE_2026_07_17_next_orchestrated_run.md` §5).

## P1 — Accuracy (data-limited)

- **Small-cc / 2-stroke ET floor** is limited by benchmark *data quality*, not
  the model. The lever is **instrumented Dragy/VBox timeslips** from real Indian
  / SE-Asia stock bikes (Aamby Valley, MMRT). This is a community/partnership
  play, not a code change. Every added instrumented benchmark tightens the
  weighted sweep and the public accuracy story.
- **Epoch-gated physics** (Pacejka slip, 4-branch clutch dispatch, staging
  rollout/dead-time) — do NOT wire casually; they move the pinned baselines
  (ADR-0002). Only behind a deliberate, sweep-justified accuracy pass.
  *(July 13, 2026: the first such epoch landed — locked-clutch deceleration,
  converged weight-transfer→traction cap, slip-phase ram-air+parasitic,
  front-wheel inertia radius, per-cluster `mu_peak_scale` recalibration.
  New pins 9.9331 / 10.1436 / 10.3633; see
  `reports/session_2026_07_13_epoch_data_hardening.md`.)*
- **Factory speed-limiter model** — the +20–40 km/h litre top-speed
  overshoot is NOT the decel clamp (A/B-disproven July 13): sims run to
  their aero-limited 320–340 km/h against 299-limited published figures.
  Add a `speed_limiter_kmh` spec field consumed by `run_top_speed` (many
  top-speed benchmark rows already carry "factory-limited"). Would collapse
  the top-speed sweep's +28.5 km/h bias.

## P2 — Growth & moat

- **Observability**: Sentry is wired (env-gated). Add product analytics
  (GA4/PostHog) so every user-facing KPI stops being "TBD". Then instrument the
  funnel (sim → save → share → signup → upgrade).
- **Content & SEO**: the accuracy/validation story is the differentiator. More
  blog posts, the `/validation` explorer, and honest benchmark tables compound
  into organic traffic (see `docs/SEO_STRATEGY.md`).
- **Distribution channels**: an **MCP server** wrapping the existing `/api/*`
  surface ("ask your AI what 16/45 does to your 60-foot") and a **MotoQuant
  skill** — cheap given the OpenAPI surface already exists; both are demos that
  market themselves.
- **Test-coverage signal → gate**: CI already emits coverage XML (non-blocking).
  Once the funnel is stable, ratchet a floor on the physics/critical modules.

## The durability thesis (why this repo can be handed off)

This project is maintained largely by AI sessions with occasional human input.
It survives model/contributor switches because the knowledge is **externalized
and enforced**, not held in one head:

- **AGENTS.md** — the contract every contributor reads first.
- **docs/INVARIANTS.md** + `scripts/check_baselines.py` + CI — what must never
  break, enforced automatically.
- **docs/KNOWN_TRAPS.md** — the "don't step here" map of recurring bugs.
- **docs/adr/** — why settled decisions are settled (don't relitigate).
- **`make health` / `make check`** — one command to know the state / to gate a PR.

Keep these current and the codebase keeps improving no matter who — or what — is
at the keyboard. That is the actual moat behind the physics.
