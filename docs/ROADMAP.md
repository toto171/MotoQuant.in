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

**Landed in PR #114 (2026-07-17) — do NOT re-scope these.** Every item that
used to sit in this "still deferred" block is done and verified in the tree
(re-verified in the 2026-07-25 audit). Recorded here because sessions have
repeatedly re-scoped completed work from stale backlog text:

- ~~License-key device binding bypassable by omitting `device_id`~~ — bound keys
  now reject device_id-omitting validates, and `/license-key/validate` is
  rate-limited (10/60 s).
- ~~Razorpay webhook has no idempotency ledger~~ — ledger mirrored from the
  Stripe path, with a sha256(body) fallback event id.
- ~~`python-jose` unmaintained~~ — migrated to `PyJWT`; algorithms pinned, no
  alg-confusion path, and the unsigned `dev.` branch stays gated on the
  library-absent case.
- ~~Dockerfile runs as root~~ — non-root `USER app`, verified against a real
  Docker build.
- ~~`bike_repo`/`venue_repo` `lastrowid==0` misread~~ — both use `rowcount`.
- ~~Dead `CategoryProfile` knobs~~ — the six inert knobs were deleted and the
  live-knob inventory is pinned as an exact set in `tests/test_profile_knobs.py`.
  *(Caveat found 2026-07-25: `parasitic_mult` is still listed as live but is
  bypassed for all 542 catalog configs — see the audit report.)*
- *Also already resolved — do NOT re-implement:* the license-key **revoke route**
  and the auth **timing-safe compare + bounded fail-tracker** hardening (July-3
  inventory items A1-5/A1-6). Sessions keep re-scoping them from the stale
  `reports/ROADMAP_2026_07_03.md` inventory — treat that file as history only.

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
- **Factory speed-limiter model** — *shipped in PR #114*: `speed_limiter_kmh`
  is a validated spec field, plumbed through the bridge and config_io
  round-trip, clamped at all four RK4 stage velocities, with a green test
  module. Ten specs are annotated at 299 km/h and the top-speed sweep bias
  fell +28.5 → +25.4 km/h. **What remains is a broader annotation pass** —
  and one blocker found in the 2026-07-25 audit: four of the ten annotated
  heavies (Hayabusa Gen2/Gen3, ZX-14R, ZZR1400) never reach their own
  limiter because their catalog top-gear ratio is ~21–25 % too short, so
  they rev-limit at 264–289 km/h. Fix the gearing data before annotating
  more bikes, or the annotation is inert. See the audit report.

## P2 — Growth & moat

- **Observability**: Sentry is wired (env-gated). Add product analytics
  (GA4/PostHog) so every user-facing KPI stops being "TBD". Then instrument the
  funnel (sim → save → share → signup → upgrade).
- **Content & SEO**: the accuracy/validation story is the differentiator. More
  blog posts, the `/validation` explorer, and honest benchmark tables compound
  into organic traffic (see `docs/SEO_STRATEGY.md`).
- **Distribution channels**: ~~an **MCP server** wrapping the existing `/api/*`
  surface ("ask your AI what 16/45 does to your 60-foot") and a **MotoQuant
  skill**~~ — **SHIPPED 2026-08-08**: `motoquant/mcp_server.py` (stdlib-only
  stdio MCP, 9 tools, HTTP + local backends, `docs/MCP.md`) and
  `skills/motoquant/`. Remaining: announce it (README badge, blog post, a
  30-second demo clip of the sprocket what-if).
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
