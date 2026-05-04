# Agent A7: product-prioritisation

Read CLAUDE.md (Phase 5/6/7 sections), AUTONOMOUS_OPERATIONS_PLAYBOOK.md (KPI section).

## Goal

Re-rank the open Phase 6 / Phase 7 carry-forward items based on this week's signals (KPIs, market intel, customer support volume, competitor moves). Update CLAUDE.md ranking + propose top-3 next features.

## Inputs to consider

- STATUS.md weekly KPIs (which goals are off-track)
- `data/competitive_landscape.md` (what competitors just shipped)
- `bike_suggestions` table (what users keep asking for)
- `DISPATCH_OUTBOX.md` (what blockers showed up this week)

## Workflow

1. Read all 4 inputs.
2. For each open Phase 6/7 item, score on (impact × confidence) / effort.
3. Identify any new feature ideas surfaced by signals.
4. Top-3 ranking written to `reports/product_priorities_YYYY-MM-DD.md`.
5. If the top-1 changes from last week's top-1: update CLAUDE.md "Standing priorities" section.

## Deliverable

- `reports/product_priorities_YYYY-MM-DD.md` (top 3 + reasoning)
- Optional: small CLAUDE.md edit to the standing priorities note
- Optional: queue a `[opportunistic]` INSTRUCTION for the engineering team-of-one (you / agents / user) to start the new top-1

## Escalate

- If the top-1 requires a budget or external service (SMTP, Razorpay, etc.): queue `[blocking]` for user.
- If signals are conflicting (KPIs say A, competitors say B): write both arguments, defer to user.

## Don't

- Don't propose a phase-6 item without a concrete success metric.
- Don't depromote items that have customer-facing INSTRUCTION queues already.
- Don't add new phases without strong signal — this is re-ranking, not roadmap inflation.

Cap ~700 words.
