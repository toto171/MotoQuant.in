# Changelog

Notable changes, newest first. This is the human-readable milestone history;
the exhaustive session-by-session log lives in `CLAUDE.md` (top entry = latest)
and `reports/`. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [PR #107] — 2026-07-10 — STAGED v4: ground-up website redesign

Operator-directed full redesign ("completely new website, full creative
freedom, simpler interface, full functionality"). New design language:
**STAGED — the digital timeslip.** Night-asphalt surfaces, one volt-green
accent (the green light), Barlow Condensed display type, mono tabular
numbers, and the printed timeslip as the signature result artifact.

### Added
- **`web/DESIGN.md`** — the v4 design authority (supersedes `REDESIGN.md`).
- **`design/staged/`** — 13 design-system preview cards (also synced to the
  owner's Claude Design project via claude.ai/design).
- New CSS vocabulary: `.timeslip`, `.chip-*`, `.delta-down/.delta-up`,
  `.centerline`; `StageDots` signature component (pre-stage · stage · GO).

### Changed
- Every page + chrome re-skinned; landing page rewritten at half its length
  around a live quick-sim hero. Tool pages unified on a two-pane workbench.
  `/r/[id]` and `/leaderboard` are now full timeslip artifacts.
- Tailwind tokens: `asphalt-*` / `accent` (volt) / `signal-*` / `mint`, with
  `ink-*`/`brand-*` kept as compatibility aliases so ~50 untouched blog
  pages re-skin automatically.
- Brand assets regenerated (volt icon set, webmanifest, OG card); the OG
  renderer in `scripts/audit_headline_stats.py` re-paletted.

### Removed
- Cockpit-era decoration: BootSequence, HudFrame, TronGrid, ManifestoScrub,
  PhysicsDial, ChristmasTree, LaunchControl, TelemetryHUD, SectionRail
  (seven-segment ScoreboardDigits survives as clean mono digits behind the
  same API).

### Unchanged (by contract)
- All functionality: job-backed sims with progress/Stop, save→leaderboard→
  share loop, auth/billing flows, chat agent UI, experiments, SEO/JSON-LD,
  `lib/api.js` polling resilience; every headline stat token byte-identical
  (audit in sync).

## [PR #100] — 2026-07-06 — Durability milestone

The 100th pull request. Focus: make the codebase keep improving across
model/human handoffs, plus a final security sweep.

### Added — durability systems (survive any contributor switch)
- **`AGENTS.md`** — the one-page, model-agnostic working contract (prime
  directive, the loop, non-negotiable rules). The canonical entry point for any
  AI tool or human.
- **`Makefile`** — the universal entry point; targets mirror CI (`make check`,
  `make test`, `make health`, `make baselines`, …).
- **`scripts/check_baselines.py`** — executable guard for the K5/R1/Hayabusa
  bit-identical invariant (exit 1 on drift). Wired into `make`, pre-commit, CI.
- **`scripts/health_check.py`** — one-command state-of-the-world (baselines,
  lint, catalog, headline drift, git, secret scan); `--secrets-only` fast mode.
- **`docs/INVARIANTS.md`** — what must never break + the gate that enforces each.
- **`docs/KNOWN_TRAPS.md`** — the recurring-bug "don't step here" map.
- **`docs/ROADMAP.md`** — honest, prioritized path to the $1M/$10M goal, tied to
  real blockers.
- **`.pre-commit-config.yaml`** — local enforcement (ruff, baseline guard on
  physics files, secret scan, large-file guard).
- **ADRs 0002–0005** — pinned baselines, no-Numba, SQLite-until-scale, desktop
  discontinued (supersedes ADR-0001). The "do not re-litigate" decisions.

### Added — CI
- **Secret-scan gate** in the Python CI job (stdlib-only, fails fast).

### Security
- Final adversarial security sweep across backend, web frontend, DB write-races,
  supply-chain/config, and a re-triage of the deferred findings. Confirmed
  low-risk fixes landed; the rest catalogued in `docs/ROADMAP.md` P1 with
  rationale. *(See the PR #100 review report in `reports/`.)*

## [PR #99] — 2026-07-06 — Security & navigability review

- **SSRF** fix in the chat agent's `web_fetch` (redirect revalidation on every
  hop + total-timeout bound + connection-leak close).
- **Rate-limit / free-quota bypass** fixed (rightmost `X-Forwarded-For` hop
  instead of the spoofable leftmost).
- **JWT default-secret** boot guard under billing enforcement.
- **Job slot-exhaustion DoS** — hung workers released past a runtime deadline.
- **API input validation** — bounded sim params; `limit=-1` table-dump on
  `/api/leaderboard` + `/api/me/runs`.
- **`docs/ARCHITECTURE.md`** — module map + data-flow diagram + docs index +
  repo-navigation guidance.
- Full suite 4324 passed; baselines bit-identical; +22 regression tests.

## Earlier

The project's full history (physics engine, 541-bike catalog, calibration
pipeline, surrogate models, agentic chat, commercial launch, the Render
migration, and dozens of accuracy/hardening passes) is recorded session-by-session
in `CLAUDE.md` and `reports/`. Highlights:

- **Agentic chat** — multi-step tool-calling agent over the whole product.
- **Taxonomy v2 accuracy retune** — full-corpus weighted sweep; per-cluster knobs.
- **Catalog** — 541 bikes / 593 parts / 254 tires / 20 venues / 221 benchmarks.
- **Surrogate models** — learned cache of the physics for the optimizer.
- **Commercial launch** — accounts, magic-link + password auth, Stripe/Razorpay,
  freemium beta, shareable timeslips.
- **Reference baselines** pinned bit-identical since the engine was validated.
