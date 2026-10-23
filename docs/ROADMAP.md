# Engineering roadmap

> Honest, prioritized, and tied to real blockers. This is the "what to do next
> and why" for whoever is at the keyboard, whether that is a model, a human
> contributor or the maintainer. Re-rank it as reality changes; don't let it
> rot. Last substantive revision: 2026-10-23 (open-source pivot,
> [ADR-0006](adr/0006-open-source-pivot.md)).

## North star

MotoQuant is **free and open source** (Apache-2.0). Success means:

- **Accuracy you can audit.** A growing, source-labelled corpus of
  *instrumented* benchmarks (Dragy/VBOX/Racelogic runs, magazine timing
  gear), a weighted sweep anyone can rerun, and residuals published on
  `/validation`.
- **Contributors.** Riders, tuners and developers can add a bike, a
  benchmark, a dyno sheet or a fix without asking permission, because the
  contract (AGENTS.md), the gates (`make check`) and the invariants are
  written down and enforced.
- **Self-hostable.** Anyone can run the whole stack from this repo
  ([SELF_HOSTING.md](SELF_HOSTING.md)), and the hosted instance at
  motoquant.in stays up and correct under real load.

## The honest reality

The **code is not the bottleneck.** The engine is validated, the product is
live (`motoquant.in` on Vercel, API on Render), and the test suite is deep.
What limits MotoQuant now, in order:

1. **Data.** Small-cc accuracy is *data-limited, not model-limited*. It needs
   real instrumented timeslips, which means community contributions and data
   partnerships with tuning shops and dyno owners.
2. **Openness logistics.** The repo has to be public and easy to contribute
   to: visibility flipped, private security reporting on, issue templates
   triaged, CI working for forks.
3. **One real engineering scaling blocker**: the shared SQLite connection.

Everything below is ranked by *what unblocks contributors and accuracy or
prevents an outage*, not by what's fun to build.

## P0 — Open-source launch and stability

| # | Item | Owner | Why | Success metric |
|---|---|---|---|---|
| P0-1 | **Flip the repository public** and turn on GitHub private vulnerability reporting + Discussions | Maintainer | `SECURITY.md`, `CODE_OF_CONDUCT.md` and the `/contact` page point at them. | Repo public; "Report a vulnerability" works; Discussions enabled. |
| P0-2 | **User-data durability on the hosted instance** (Render persistent disk; `docker-entrypoint.sh` already seeds it; `scripts/backup_db.py` scheduled) | Maintainer | Every deploy currently wipes optional accounts and saved runs. See [SELF_HOSTING.md §3d–3e](SELF_HOSTING.md). | An account and its garage survive a deploy; daily off-box backups. |
| P0-3 | **Fix the shared SQLite connection before multi-worker** (per-thread / pooled conn, or the Postgres migration) | Engineering | KNOWN_TRAPS T14 / ADR-0004: one `check_same_thread=False` connection is shared across request + job threads; concurrent writes can interleave. Fine at 1 worker, corrupts under scale. | 2+ workers pass a concurrent read/write stress test with no interleave/errors. |
| P0-4 | **Rotate any credentials that ever touched the history before going public**, and keep the secret-scan gate | Maintainer + Eng | Tokens have historically been pasted into chats and notes. A public repo exposes its entire history. CI blocks token-shaped strings in new commits; anything already in history must be rotated or the history scrubbed. | `make health` secret scan clean; every historical PAT/API key revoked. |
| P0-5 | **Fork-friendly CI** | Engineering | Workflows must pass on PRs from forks without secrets (deploy jobs are already gated). | A PR from a fork runs `ci.yml` and `web-verify.yml` green. |

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

- ~~`python-jose` unmaintained~~ — migrated to `PyJWT`; algorithms pinned, no
  alg-confusion path, and the unsigned `dev.` branch stays gated on the
  library-absent case.
- ~~Dockerfile runs as root~~ — non-root `USER app`, verified against a real
  Docker build.
- ~~`bike_repo`/`venue_repo` `lastrowid==0` misread~~ — both use `rowcount`.
- ~~Dead `CategoryProfile` knobs~~ — the six inert knobs were deleted and the
  live-knob inventory is pinned as an exact set in `tests/test_profile_knobs.py`.
  *(Caveat found 2026-07-25: `parasitic_mult` was listed as live but bypassed
  for the whole catalog. RESOLVED 2026-08-08: synthetic catalog curves now
  declare crank semantics, so the parasitic + chain-efficiency paths — and
  the 29 previously-inert priced SKUs behind them — are live; see
  reports/session_2026_08_08_full_night_run.md.)*
- *Also already resolved — do NOT re-implement:* the auth **timing-safe
  compare + bounded fail-tracker** hardening (July-3 inventory item A1-6).
  Sessions kept re-scoping it from the stale `reports/ROADMAP_2026_07_03.md`
  inventory; treat that file as history only. (The license-key and Razorpay
  hardening that used to be listed here was deleted with monetization on
  2026-10-23; see ADR-0006.)

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

## P1 — Community data

- **Benchmark contributions.** Make it trivial to submit an instrumented run:
  the `calibration_data` issue template, the `/validation` page CTA, and a
  documented source-labelling rule (instrumented / magazine / aggregator /
  forum / DERIVED weights). Every accepted instrumented row tightens the
  weighted sweep.
- **Data partnerships, not sales.** Tuning shops and dyno owners in
  Pune/Narhe, Bangalore and Hyderabad are asked for runs and dyno sheets, not
  sold seats (`scripts/agents/partnership-outreach.md`; the old B2B pitches
  are in `docs/archive/outreach/`).

## P2 — Open-source ecosystem

- **Good-first-issue pipeline.** Label scoped issues (catalog passes,
  resolver tokenization, chat streaming, small UI polish) so new
  contributors have an obvious entry point.
- **Rust core adoption** (optional accelerator, bit-identical to the Python
  reference): server adoption behind `native.available()`, exact
  client-side full sims in the browser, and faster sweeps. See
  [RUST_CORE.md](RUST_CORE.md). Python stays the reference.
- **Observability.** Sentry is wired (env-gated). Server-side PostHog
  forwarding is opt-in and off unless the operator sets `POSTHOG_API_KEY`.
  Funnel events (sim → save → share → signup) help the hosted instance, but a
  self-hosted copy sends nothing anywhere.
- **Content.** The accuracy/validation story is the differentiator: blog
  posts, the `/validation` explorer and honest benchmark tables.
- **Distribution channels**: ~~an **MCP server** wrapping the existing `/api/*`
  surface ("ask your AI what 16/45 does to your 60-foot") and a **MotoQuant
  skill**~~ — **SHIPPED 2026-08-08**: `motoquant/mcp_server.py` (stdlib-only
  stdio MCP, 9 tools, HTTP + local backends, `docs/MCP.md`) and
  `skills/motoquant/`. Remaining: announce it (blog post, a 30-second demo
  clip of the sprocket what-if).
- **Test-coverage signal → gate**: CI already emits coverage XML
  (non-blocking). Ratchet a floor on the physics and other critical modules.

## The durability thesis (why this repo can be handed off)

This project has been maintained largely by AI sessions with occasional human
input, and is now open to every contributor. It survives model/contributor
switches because the knowledge is **externalized and enforced**, not held in
one head:

- **AGENTS.md** — the contract every contributor reads first.
- **docs/INVARIANTS.md** + `scripts/check_baselines.py` + CI — what must never
  break, enforced automatically.
- **docs/KNOWN_TRAPS.md** — the "don't step here" map of recurring bugs.
- **docs/adr/** — why settled decisions are settled (don't relitigate).
- **`make health` / `make check`** — one command to know the state / to gate a PR.

Keep these current and the codebase keeps improving no matter who — or what — is
at the keyboard. That is the actual moat behind the physics.
