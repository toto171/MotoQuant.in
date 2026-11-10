# Engineering roadmap

What to work on next, and why, ranked by what most improves accuracy or
keeps the site up. Re-rank it when the facts change. Last revised
2026-11-10, for release 2.0.0 (open source
[ADR-0006](adr/0006-open-source-pivot.md), Rust core
[ADR-0007](adr/0007-rust-physics-core.md), the accuracy epoch and the site
redesign). Finished work is recorded in [CHANGELOG.md](../CHANGELOG.md);
check it before picking up an item, because several old backlog entries
were done long before they were removed from here.

## Where the project stands

MotoQuant is free and open source under Apache-2.0. The engine is checked
against 250 published tests (263 matches to catalog bikes), the site is live at motoquant.in, and the test
suite is large. Code is no longer the main limit. In order, the limits are:

1. Data. Small bikes are the weakest class. Few instrumented timeslips exist
   for them, and many run a generic primary gear ratio because nobody has
   sourced the real one (see "Accuracy" below).
2. Contributor logistics: private security reporting, Discussions, triaged
   issue templates and CI that runs on forks.
3. One engineering blocker to scaling: the shared SQLite connection.

## P0: launch and stability

| # | Item | Owner | Why | Done when |
|---|---|---|---|---|
| P0-1 | Turn on private vulnerability reporting and Discussions, and protect `main` | Maintainer | `SECURITY.md`, `CODE_OF_CONDUCT.md` and `/contact` point at them. Branch protection with code-owner review is what keeps an outside pull request from reaching the site. | "Report a vulnerability" works; Discussions are on; `main` requires a reviewed pull request and green checks. |
| P0-2 | ~~Durability of user data on the hosted copy~~ | | Resolved on 2026-11-10 by removing accounts. The site stores no visitor data, so a redeploy loses nothing. | |
| P0-3 | Fix the shared SQLite connection before running more than one worker | Engineering | KNOWN_TRAPS T14 and ADR-0004: one `check_same_thread=False` connection is shared by request and job threads, so concurrent writes can interleave. Safe at one worker. | Two or more workers pass a concurrent read/write stress test. |
| P0-4 | Keep the secret-scan gate | Maintainer and engineering | A full-history scan before the repository went public found no live credentials. CI blocks token-shaped strings in new commits; a credential that does land must be revoked, not just deleted. | `make health` secret scan stays clean. |
| P0-5 | CI that works for forks | Engineering | A pull request from a fork must run the checks without secrets. Deploy jobs already run only on pushes to this repository's `main`. | A fork's pull request runs `ci.yml` and `web-verify.yml` green. |

## P1: accuracy

- Instrumented timeslips for small bikes and two-strokes. Their error is
  limited mostly by the benchmarks themselves: magazine tests rarely cover
  them. Real Dragy or VBOX runs from stock bikes at Aamby Valley or MMRT are
  the fix, and the "Submit a timeslip" form exists for them. This is a
  community job, not a code change.
- Sourced primary ratios for small bikes. Many fall back to a litre-bike
  primary ratio and are geared too tall. In November 2026, 32 sourced
  gearing entries covering 53 bikes were applied as an experiment. The
  weighted error went from 0.2495 s to 0.2525 s and the affected bikes got
  worse (0.411 s to 0.447 s), because the current tuning compensates for the
  wrong gearing. The data was kept and not applied
  ([reports/gearing_experiment_2026_11_10.md](../reports/gearing_experiment_2026_11_10.md)).
  Applying it needs a re-tune of the small-bike launch and drivetrain
  losses in the same change. Do not re-apply an inferred rule;
  `scripts/check_gearing_plausibility.py` keeps the flagged list from
  growing.
- The next levers from the accuracy epoch (rollout timing, combined centre
  of mass in the wheelie limit, aero pitch moment, tyre heat balance; pins
  10.0436 / 10.1092 / 10.1100). In the order of
  [reports/session_2026_11_05_handoff.md](../reports/session_2026_11_05_handoff.md):
  a launch model fitted to measured 60-ft times, per-source rollout
  evidence, the two-stroke power-curve ladder, and measured centre-of-mass
  data in place of the 52 % front and 810 mm seat-height defaults.
- Physics that would move the pins (Pacejka slip force, four-branch clutch
  dispatch, staging dead time) waits for a deliberate accuracy pass with a
  full sweep as evidence (ADR-0002).
- A wider speed-limiter annotation pass. The limiter model works; top speed
  is still weaker than ET: off by about 12.7 km/h on average and about
  6.8 km/h too fast overall (newest `reports/acc_final_*.json`).

## P1: community data

- Benchmarks. The "Submit a timeslip" form, the `/validation` page and the
  source weights (instrumented, magazine, aggregator, forum, derived) make a
  submission easy to review. Every accepted instrumented run tightens the
  sweep.
- Data from tuning shops and dyno owners. The project asks for runs and dyno
  sheets, not money; the "Dyno sheet or ECU log" form takes them.

## P2: open-source ecosystem

- A steady supply of good first issues: catalog fixes, resolver
  tokenisation, chat streaming, small interface work.
- Exact simulations in the browser. The Rust core is bit-identical to the
  Python reference and already serves every server simulation when
  installed (`motoquant/engine_select.py`). The committed wasm build passes
  the same parity checks but the interface does not call it yet
  (`web/lib/engine.js`; see [RUST_CORE.md](RUST_CORE.md)).
- Export and import of saved runs. Runs live in the browser's storage, so
  clearing it loses them; a JSON export would let people move them between
  devices.
- Observability. Sentry is wired and off unless configured. Server-side
  PostHog forwarding is off unless the operator sets `POSTHOG_API_KEY`; a
  self-hosted copy sends nothing anywhere.
- The MCP server (`motoquant/mcp_server.py`, [MCP.md](MCP.md)) and the
  `skills/motoquant/` skill shipped in August 2026 and have not been
  announced.
- Coverage. CI publishes coverage without enforcing it; a floor on the
  physics modules would catch untested changes.

## Why the project survives a change of hands

The knowledge lives in files that CI enforces, not in one person's head:
[AGENTS.md](../AGENTS.md) for the working rules,
[INVARIANTS.md](INVARIANTS.md) and `scripts/check_baselines.py` for what must
never break, [KNOWN_TRAPS.md](KNOWN_TRAPS.md) for bugs that recur, the
[ADRs](adr/) for settled decisions, and `make health` and `make check` to
learn the state of the tree and gate a change. Keep them current.
