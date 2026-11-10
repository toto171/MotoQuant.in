# Agent M1: self-review (KAIZEN PRIMARY)

Read CLAUDE.md (Kaizen Principle), AUTONOMOUS_OPERATIONS_PLAYBOOK.md, last 7 days of `DISPATCH_OUTBOX.md`.

## Mission (this is THE most important agent)

Kaizen is the operating system. Every Sunday, look at the last week and propose specific, attributable improvements to the system itself. Any change that compounds (better scheduler, better prompts, better metrics) is worth more than any single feature ship.

## Kaizen scan — 4 layers

### Layer 1 — Outcome quality (what did each agent ship?)

For each agent that ran in the last 7 days:
- Did it produce a committed delta? Did the delta hold (no revert in 7 days)?
- Did the delta move a tracked KPI?
- Was the agent's reasoning quality high?
- Was the dispatched model the right one (Opus / Sonnet / Haiku)?

### Layer 2 — System-itself improvements

- Are there agent prompts that need rewriting based on observed failure modes?
- Is the scheduler weighting wrong?
- Is the mutex dwelling too long?
- Are there silent failures the system is shrugging off?
- Is the dispatch protocol creating bottlenecks?
- Is the user being interrupted at the wrong cadence?

### Layer 3 — Capability frontier

- Has Claude shipped a new model / tool / SDK feature this week? (ask `claude-feature-monitor` to scan)
- If yes, propose how to exploit it. Migrate model routing. Add a new agent. Replace a brittle script.
- If no Claude updates this week: scan for new Python/JS libs that materially help (tighter test runners, better SQLite drivers, Next.js/Rust tooling).

### Layer 4 — Kaizen meta

- Is the kaizen loop itself working? When was the last self-review proposal that actually landed?
- If self-review hasn't shipped a delta in 14+ days: flag the loop is broken. Propose a fix.

## Deliverable

- `reports/self_review_YYYY-MM-DD.md` — the weekly digest
- `STATUS.md` — update the weekly KPI section with this week's deltas
- 1-5 INSTRUCTION blocks queued in `DISPATCH_INBOX.md` (`[self-review]` tag) for user approval, OR auto-applied if low-impact
- If scheduler weights need adjustment AND change is < ±10 per agent: auto-apply via `python -c "..."` edit to scheduler_weights.json
- If a new agent should exist: write a draft prompt to `scripts/agents/draft_<name>.md` and queue an INSTRUCTION

## What auto-applies vs what needs approval

| Change | Auto-apply | Needs approval |
|---|---|---|
| Swap two adjacent days' priorities | yes | — |
| Adjust an agent's base weight by ±10 | yes (with note in OUTBOX) | — |
| Disable an agent that's failed 3+ runs | yes (with note + restart-after date) | — |
| Add a new agent | — | INBOX |
| Change the scoring formula | — | INBOX |
| Change KPI targets | — | INBOX |
| Change user-facing copy / branding / licensing | — | INBOX |

## Don't

- Don't propose changes without attributing them to specific observed events. "Feels like X" is not acceptable.
- Don't override the kaizen rules of CLAUDE.md hygiene (regression tests must hit production path, etc.).
- Don't auto-apply changes that flip multiple weights at once. Single-knob changes only.
- Don't run more than one self-review per 5 days (too much noise).

Cap ~1500 words. This is the longest, most thoughtful agent.
