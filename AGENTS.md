# AGENTS.md: working agreement for every contributor, human or AI

> This is the **canonical contract** for changing this repo. It is short on
> purpose: read all of it before your first edit. It applies to every person
> and every AI coding tool. `CLAUDE.md` and `.github/copilot-instructions.md`
> only point back here.

MotoQuant is a free, open-source (Apache-2.0) first-principles physics engine
for motorcycle quarter-mile drag racing, plus the product built on it: CLI,
FastAPI backend, Next.js web app, chat agent and MCP server. The repo holds the
Python package `motoquant/` and a seeded SQLite catalog. There are no paid
tiers, quotas or license keys, and none may come back
([ADR-0006](docs/adr/0006-open-source-pivot.md)).

## 0. The prime directive

Three reference bikes are pinned **bit-identical** and gated in CI:

```
GSX-R 1000 K5 → 10.0436 s   YZF-R1 4C8 → 10.1092 s   Hayabusa Gen1 → 10.1100 s
```

A change that moves any of them by even 1e-9 s is a regression, however
correct it looks. The one exception is a *deliberate, justified* accuracy
change: it needs the full weighted sweep as evidence and a matching update of
the targets in `scripts/check_baselines.py` and `docs/INVARIANTS.md`. After
ANY edit to `physics.py`, `submodels/*`, `defaults.py`, `category_profiles.py`
or `scraper/importer.py`, run `make baselines`. The full list of invariants
is in **[docs/INVARIANTS.md](docs/INVARIANTS.md)**.

## 1. The loop

```bash
make install        # once
make health         # state of the world (baselines, lint, catalog, secrets) — do this first
# ... make your change ...
make check          # fast gate: lint + format + baselines + fast tests  (~3 min)
make test           # full suite (~25 min) — REQUIRED before opening a PR
```

`make` with no target lists everything. The make targets run what CI runs, so
green locally ≈ green in CI.

## 2. Non-negotiable working rules

Each of these was broken at least once and cost real time. The full list of
traps is **[docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md)**; read it before a big
change.

1. **Never `git add -A` or `git add .`:** stage explicit file paths. The tree
   often holds unrelated work in progress.
2. **Never commit `motoquant.db` churn** unless you *meant* to change data.
   Opening the DB through the CLI or a test rewrites it with no content
   change (even `bikes --search`; KNOWN_TRAPS T2), so run read-only commands
   against a copy (`--db /tmp/mq.db`). If `git diff` shows it modified but row
   counts are unchanged, `git checkout -- motoquant.db`.
3. **Regression tests must exercise the production path**: a DB round-trip
   for `/api/simulate?bike_id=N`, HTTP for API bugs. A test that re-implements
   the fix and checks its own math proves nothing.
4. **After `spec_to_bike_config`, physics or importer changes, re-seed:**
   `python scripts/reseed_configs_from_specs.py`. Otherwise the DB blobs go
   stale and `/api/simulate?bike_id=N` silently diverges from the sweep path.
5. **After any change to a catalog or feature count, sync the headline
   stats:** run `python scripts/audit_headline_stats.py` (or `make audit`) and
   fix every drift before pushing.
6. **When you touch `web/**`, run `make web-build`**, which is what Vercel
   runs. `useSearchParams()` must sit inside a `<Suspense>` boundary or the
   static build fails.
7. **Regenerate the physics caches in the same change that moves the
   physics:** the regression snapshot, the stock leaderboard, the
   instant-estimate model and the browser engine fixtures (see the
   regeneration list in [CONTRIBUTING.md](CONTRIBUTING.md)).
8. **Record what you measured.** A change that moves accuracy carries its
   sweep result in the pull request; a larger investigation gets a short
   write-up in `reports/`.

## 3. Where things live

- Architecture, or where X lives: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  (module map and data-flow diagram).
- First day on the project: [docs/ONBOARDING.md](docs/ONBOARDING.md).
- Development workflow: [CONTRIBUTING.md](CONTRIBUTING.md), including how
  contributions are licensed (Apache-2.0, inbound = outbound).
- Running and deploying: [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md).
- Community policy: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and
  [SECURITY.md](SECURITY.md) (report vulnerabilities privately).
- Why things are the way they are: [docs/adr/](docs/adr/), the Architecture
  Decision Records. Read them before reopening a settled decision.
- What must never break: [docs/INVARIANTS.md](docs/INVARIANTS.md).
- Bugs that keep coming back: [docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md).
- Index of all docs: [docs/README.md](docs/README.md).

## 4. Security posture (keep it)

- There are **no accounts** and **no anonymous writes that other visitors
  see**. Saved runs live in the visitor's browser; a timeslip link carries its
  setup and the page re-simulates it. Every POST route is on the allow-list in
  `tests/test_open_source_pivot.py::PUBLIC_POST_ROUTES`. Anything that would
  publish visitor input belongs in the issue tracker, not in a new route.
- Everything is free, so **per-IP rate limits are the abuse fuse**. Every
  compute-heavy public route gets a `rate_limit(...)` dependency, and the
  daily chat cap (`MOTOQUANT_CHAT_DAILY_LIMIT`) limits the LLM bill. Buckets
  key on the client IP taken from `X-Forwarded-For` only for the trusted
  proxy hops (`MOTOQUANT_TRUSTED_PROXY_HOPS`; auto = 1 on Render), never the
  leftmost hop, which the client can spoof. On Render that trusted hop is
  Render's own private proxy; the API steps over Render's private hops to
  Cloudflare's edge and takes the client from Cloudflare's
  `CF-Connecting-IP`, trusted only on Render and only when that hop is a
  Cloudflare address.
- The chat agent's `web_fetch` re-checks the SSRF guard on **every redirect
  hop**. Any server-side fetch of a URL that a user or the LLM controls must
  do the same.
- SQL is always parameterized. No secrets in tracked files (the health check
  scans for them; CI should too).

## 5. Commits and PRs

- Imperative subject ≤ 72 chars; explain the *why* in the body.
- One logical change per commit. Test each batch.
- Use your real git identity. Contributions are licensed Apache-2.0
  (inbound = outbound); there is no CLA. Never commit credentials, and never
  ask a contributor for one. Plain `git` over your own fork is all you need.
- Open PRs as **draft** and fill in the PR template. Any physics-adjacent PR
  includes the K5/R1/Hayabusa delta table.
- CI must be green (run `make test` and `make check` locally first).

## 6. Definition of done

A change is done when `make check` passes, `make test` is green, baselines are
bit-identical (or a justified sweep is attached), the headline stats are in
sync, no secret is in the diff, and the PR body explains the why. If you
deferred something, write it down in the PR or in `reports/` so the next
contributor, human or model, can pick it up.
