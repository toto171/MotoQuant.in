# AGENTS.md — working agreement for any contributor (human or AI)

> This is the **canonical, model-agnostic contract** for changing this repo.
> It is short on purpose. Read it fully before your first edit. It applies to
> every AI coding tool (Claude, Cursor, Copilot, Gemini, …) and every human.
> `CLAUDE.md` is a *different* thing — a long session changelog; skim only its
> top entry. Start here, not there.

MotoQuant is a free, open-source (Apache-2.0) first-principles physics engine
for motorcycle quarter-mile drag racing, plus the product built on it (CLI,
FastAPI backend, Next.js web app, agentic chat, MCP server). Python package
`motoquant/` + a seeded SQLite catalog. There are no paid tiers, quotas or
license keys, and none may be reintroduced
([ADR-0006](docs/adr/0006-open-source-pivot.md)).

## 0. The prime directive (never violate)

Three reference bikes are pinned **bit-identical** and CI-gated:

```
GSX-R 1000 K5 → 9.9331 s   YZF-R1 4C8 → 10.1436 s   Hayabusa Gen1 → 10.3633 s
```

Any change that moves them by even 1e-9 s is a regression — no matter how
correct it looks — unless it is a *deliberate, justified* accuracy change (then
it needs the full weighted sweep as evidence and a coordinated update of the
targets in `scripts/check_baselines.py` + `docs/INVARIANTS.md`). After ANY edit
to `physics.py`, `submodels/*`, `defaults.py`, `category_profiles.py`, or
`scraper/importer.py`, run `make baselines`. The complete list of invariants is
in **[docs/INVARIANTS.md](docs/INVARIANTS.md)**.

## 1. The loop

```bash
make install        # once
make health         # state of the world (baselines, lint, catalog, secrets) — do this first
# ... make your change ...
make check          # fast gate: lint + format + baselines + fast tests  (~3 min)
make test           # full suite (~25 min) — REQUIRED before opening a PR
```

`make` (no target) lists everything. The make targets mirror CI exactly, so
green locally ≈ green in CI.

## 2. Non-negotiable working rules

These exist because each was broken at least once and cost real time. The full
catalogue of traps is **[docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md)** — read it
before a big change.

1. **Never `git add -A` / `git add .`** — stage explicit file paths. The tree
   routinely holds unrelated WIP.
2. **Never commit `motoquant.db` churn** unless you *intended* a data change.
   Opening the DB in a test rewrites SQLite pages with no content change; if
   `git diff` shows it modified but row counts are unchanged, `git checkout --
   motoquant.db`.
3. **Regression tests must exercise the production path** (DB round-trip for
   `/api/simulate?bike_id=N`, HTTP for API bugs). A test that re-implements the
   fix and asserts its own math is worthless.
4. **After `spec_to_bike_config` / physics / importer changes, re-seed:**
   `python scripts/reseed_configs_from_specs.py` — otherwise the DB blobs go
   stale and `/api/simulate?bike_id=N` silently diverges from the sweep path.
5. **After any catalog/feature count change, sync the headline stats:**
   `python scripts/audit_headline_stats.py` (or `make audit`) and patch every
   drift before pushing.
6. **When you touch `web/**`, run `make web-build`** (that's what Vercel runs).
   `useSearchParams()` must sit inside a `<Suspense>` boundary or the static
   build fails.
7. **Don't rewrite `CLAUDE.md`** — it's a fragile single-paragraph changelog;
   prepend one line at most. Put substantive write-ups in `reports/`.
8. **Verify file length after a large Write** (`wc -l`) — write tools can
   truncate; a suspiciously short file lost its tail.

## 3. Where things live

- **Architecture / "where does X live?"** → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  (module map + data-flow diagram).
- **Day-one orientation** → [docs/ONBOARDING.md](docs/ONBOARDING.md).
- **Dev workflow detail** → [CONTRIBUTING.md](CONTRIBUTING.md) (incl. how
  contributions are licensed: Apache-2.0, inbound = outbound).
- **Running / deploying it** → [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md).
- **Community policy** → [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
  [SECURITY.md](SECURITY.md) (report vulnerabilities privately).
- **Why things are the way they are** → [docs/adr/](docs/adr/) (Architecture
  Decision Records — read before relitigating a settled decision).
- **What must never break** → [docs/INVARIANTS.md](docs/INVARIANTS.md).
- **Bugs that keep coming back** → [docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md).
- **Docs index** → [docs/README.md](docs/README.md).

## 4. Security posture (keep it)

- Accounts are **optional**: magic-link + password (scrypt), JWT sessions.
  Every sim/analysis route must keep working anonymously. A deployed host
  (`RENDER` / `RENDER_EXTERNAL_URL` / `MOTOQUANT_DEPLOYED=1`) never signs
  with the public dev JWT secret: with no `JWT_SECRET` it uses an ephemeral
  per-process secret and warns. Don't reintroduce the `dev.` unsigned-token
  path outside the JWT-library-absent branch.
- Everything is free, so **per-IP rate limits are the abuse fuse**. Every
  compute-heavy public route gets a `rate_limit(...)` dependency, plus the
  daily chat cap (`MOTOQUANT_CHAT_DAILY_LIMIT`) for the LLM bill. Buckets
  key on the client IP derived from `X-Forwarded-For` only for the trusted
  proxy hops (`MOTOQUANT_TRUSTED_PROXY_HOPS`; auto = 1 on Render), never the
  client-spoofable leftmost hop.
- The chat agent's `web_fetch` re-checks the SSRF guard on **every redirect
  hop**. Any server-side fetch of a user/LLM-controlled URL must do the same.
- SQL is always parameterized. No secrets in tracked files (the health check
  scans for them; CI should too).

## 5. Commits & PRs

- Imperative subject ≤ 72 chars; explain the *why* in the body.
- One logical change per commit (atomic). Test each batch.
- Use your real git identity. Contributions are licensed Apache-2.0
  (inbound = outbound); no CLA. Never commit credentials, and never ask a
  contributor for one. Normal `git` over your own fork is all you need.
- Open PRs as **draft**; fill the PR template; put the K5/R1/Hayabusa delta
  table in any physics-adjacent PR.
- CI must be green (`make test` + `make check` locally first).

## 6. Definition of done

A change is done when: `make check` passes, `make test` is green, baselines are
bit-identical (or a justified sweep is attached), the headline stats are in
sync, no secret is in the diff, and the PR body explains the why. If you
deferred something, write it down (in the PR or `reports/`) so the next
contributor — model or human — can pick it up.
