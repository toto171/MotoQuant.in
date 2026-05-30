# Benchmark Import — 2026-05-30 (Saturday, second pass)

**Agent:** benchmark-import
**Session:** `/tmp/mq-session-1780165842-649/repo`
**Source file edited:** none
**Outcome:** no new benchmarks added — defensible null

## Summary

No new benchmarks added this pass. The current sandbox has no web access
(WebSearch / WebFetch not available in this session's tool catalog), and
the project's instrumented-only source bar requires verifiable, citable
publications (Cycle World / Sport Rider / MCN / MotoStatz with explicit
Dragy device naming). Per CLAUDE.md hygiene `honest > apparent accuracy`
and the agent spec's hard rule "Never inflate matched-N with low-quality
benchmarks. Without web access, prefer 'no additions + clear research
escalation' over making things up", this pass returns a defensible null.

Reference baselines verified unchanged:
- K5 **10.0334s** (Δ +0.0000)
- R1 **10.2859s** (Δ +0.0000)
- Hayabusa **10.4712s** (Δ +0.0000)

No files touched. Sweep not re-run (would consume budget for no delta).

## Context

The earlier 2026-05-30 session (`1780158642-983`) had web access and
already landed two benchmarks today (Kawasaki Ninja ZX-6R 636 @ 10.74s
and Yamaha YZF-R6 4th-gen @ 10.89s, both MotoStatz Dragy instrumented).
Those entries are committed on `main` at `df7fd5e`. The current second
pass would be additive on top — but the sandbox environment changed
between sessions, and WebSearch/WebFetch are gone.

The honest options were:
1. Add nothing and escalate cleanly (chosen).
2. Fabricate a "MotoStatz says X" citation from prior-knowledge guesses
   (rejected — every prior benchmark-import pass that added an entry
   verified the source article with WebFetch and the comments cite the
   exact URL; the audit trail is load-bearing).
3. Add a DERIVED 0-100 × 1.6 estimate (rejected — the project has been
   actively moving AWAY from DERIVED benchmarks; 2 open `[research]`
   inbox items already exist proposing to REMOVE existing DERIVED rows
   from the entry_150_200 and entry_200_300 clusters).

## Inbox state — no new escalation filed

Checked `DISPATCH_INBOX.md` for existing benchmark-research requests:

- `INSTRUCTION — 2026-05-20 — research: verify entry_150_200 DERIVED
  benchmarks` — open, covers Apache RTR 200 4V + MT-15 V2 + RTR 200 etc.
- `INSTRUCTION — 2026-05-20 — research: verify entry_200_300 DERIVED
  benchmarks` — open, covers Pulsar N250, FZ25, Gixxer 250 etc.
- `INSTRUCTION — 2026-05-25 — [urgent] fix BENCHMARKS matcher
  specificity bug` — this is the matcher-spec bug that was already
  resolved by the `_best_benchmark_match` score-and-pick refactor visible
  in `validation_sweep.py:1078-1104`. Inbox heading should be flipped to
  `## DONE` by the next session that touches inbox housekeeping, but
  that's not this agent's scope.

No new `[research]` item filed by this pass — adding a third "find more
benchmark sources" inbox request would duplicate the two existing ones
without adding signal. The two open items already cover the highest-
priority candidates (entry-class DERIVED rows that should be replaced
with instrumented data).

## Where the user can productively help (when next at a keyboard)

These bikes are in the catalog, currently missing benchmarks (or have a
DERIVED-only benchmark), and would be high-impact instrumented additions
if the user can source measured runs from Indian or SE-Asia community
timeslips. None requires web access from Claude — the user supplies the
data, Claude adds the entry.

Highest-priority candidates (DERIVED today, would benefit most from real
data — same list the open `[research]` items reference):

- **Bajaj Pulsar N250** — currently `15.45s` DERIVED, would benefit from
  a Dragy timeslip from any Pune/Bangalore community user.
- **Yamaha FZ25** — currently `16.00s` DERIVED, same situation.
- **TVS Apache RTR 200 4V** — currently `15.90s` DERIVED.
- **Yamaha MT-15** — currently `15.80s` DERIVED.
- **Bajaj Pulsar RS 200** — currently `15.70s` DERIVED.
- **Bajaj Pulsar NS400Z** — currently `14.10s` DERIVED.

Lower-priority (catalog has bike but no benchmark exists at all):

- **Honda CBR1100XX Super Blackbird** — flagged in the
  `benchmark_import_2026-05-25_seventh_pass.md` report as having
  verified MotoStatz data (10.38s @ 137.8 mph, Dragy named) but
  NOT in catalog. Adding the catalog spec unblocks the benchmark too.
- **Suzuki Katana 1000** (the modern one, not the GSX-S1000 variant
  already benchmarked) — `topspeed.com` quote of 10.86s seen but
  unsourced; needs primary citation.
- **Triumph Speed Triple 1200 RS** — flagged repeatedly across passes
  4 / 5 / 6 as not-locatable in honest search.

## Commit / no-commit

This pass commits no source changes. The report file itself
(`reports/benchmark_import_2026-05-30_second_pass.md`) is documentation
of why no source edits were made. Postflight may choose to commit it as
a noop dispatch entry, or skip the commit entirely — either is correct.

## Files touched

None.

## Conventional-commit message (if postflight commits this report only)

`docs(benchmarks): no-web defensible null for 2026-05-30 second pass`
