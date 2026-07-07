# PR #100 — Durability milestone + final security sweep (2026-07-06)

**Model:** claude-fable-5 (final Fable 5 session, operator-directed).
**Branch:** `claude/motoquant-review-optimize-tf4w0e` (restarted from `main`
after #99 merged). **Theme:** make the codebase keep improving across
model/human handoffs, plus a final adversarial security sweep.

Reference baselines held **bit-identical** throughout (K5 10.0334 / R1 10.2859 /
Hayabusa 10.4712).

## Durability systems (the "keep improving after I switch models" ask)

The enforcement layer already existed (CI gates baselines + ruff + pytest). What
was missing was the **contributor-facing, model-agnostic** layer. Added:

- **`AGENTS.md`** — the one-page working contract every AI tool / human reads
  first (prime directive, the loop, non-negotiable rules). `.github/copilot-instructions.md`
  redirects Copilot to it too, so every tool converges on one contract.
- **`Makefile`** — universal entry point; targets mirror CI (`make check`,
  `make test`, `make health`, `make baselines`, …).
- **`scripts/check_baselines.py`** — executable guard for the bit-identical
  invariant (exit 1 on drift). Reused by make / pre-commit / CI.
- **`scripts/health_check.py`** — one-command state-of-the-world (baselines,
  lint, catalog, headline drift, git, secret scan); `--secrets-only` fast mode.
- **`docs/INVARIANTS.md`** — what must never break + the gate enforcing each.
- **`docs/KNOWN_TRAPS.md`** — the recurring-bug "don't step here" map (git add -A,
  DB churn, reseed drift, the ROI seam, xdist flakes, lastrowid, shared conn…).
- **`docs/ROADMAP.md`** — honest, prioritized path to $1M/$10M tied to real
  blockers (payments, DB durability, the shared-connection scaling fix).
- **ADRs 0002–0005** — pinned baselines, no-Numba, SQLite-until-scale, desktop
  discontinued (supersedes 0001). The "do not re-litigate" decisions.
- **`.pre-commit-config.yaml`** — local enforcement (ruff, baseline guard on
  physics files, secret scan, large-file guard).
- **`CHANGELOG.md`** — human-readable milestone history (relieves the CLAUDE.md wall).
- **CI secret-scan gate** (stdlib-only, fails fast).

## Security sweep — fixed in this PR

A 5-surface adversarial review (backend, web frontend, DB races, supply-chain,
deferred-recheck), 27 findings → adversarially verified. Landed the confirmed,
low-risk ones:

- **Magic-link token leak → account takeover (HIGH).** `request_magic_link`
  echoed the token in the HTTP response whenever SMTP was unset (the beta state).
  Now gated to a genuine local dev run (`EMAIL_BACKEND==stdout` AND not a Render
  deploy) — closes the leak without failing-closed on the live beta or breaking
  the test flow. *(The auto-verifier flagged this fix_now=false assuming a naive
  503 fix; the shipped fix is the safer "explicit-stdout + deployed-env guard"
  it actually recommended.)*
- **`consume_magic_link` double-consume race** → atomic `UPDATE … WHERE
  consumed=0` + rowcount (one link can't mint two JWT pairs).
- **`get_or_create_user` race** → catch `IntegrityError`, re-select.
- **DB `busy_timeout=5000`** → concurrent writers wait for the lock instead of
  erroring (mitigates the shared-connection pain; not a substitute for P0-3).
- **Chat citation XSS** → validate URL scheme before rendering as an href
  (`javascript:`/`data:` blocked; render inert text instead).
- **`simulate_distance` empty-array 500** → clean 422 guard.
- **Login `?next=` open-redirect** via backslash → tightened same-origin check.
- **`ratelimit` overflow** → oldest-first eviction instead of `clear()`.
- **`subscriptions_repo` migration** → narrowed the `OperationalError` swallow.
- **Least-privilege `permissions: contents: read`** on the 4 read-only CI
  workflows.

New regression tests: `test_auth.py` (no-dev-token-in-deployed + single-use
consume) and the existing suites cover the DB fixes. 209 + 186 affected tests
green; full suite verified before push.

## Security sweep — deferred (documented, not lost)

Real but needing a focused/coordinated pass — tracked in `docs/ROADMAP.md` P1:
license device-binding policy call (test-pinned), Razorpay webhook idempotency
ledger (beta-inert, land with payments go-live), `python-jose` → PyJWT migration,
Dockerfile non-root, `lastrowid==0` misread, dead `CategoryProfile` knobs, and
the shared-SQLite-connection redesign (P0-3, the #1 pre-scale fix).

## Verification

`make health` green; full pytest suite green (serial); ruff check + format clean;
baselines bit-identical; web build verified (`web-verify`/Vercel). No physics,
seed, or DB-data files changed.
