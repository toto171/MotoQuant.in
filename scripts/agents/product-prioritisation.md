# Agent A7: product-prioritisation

Read AGENTS.md, docs/ROADMAP.md and docs/adr/0006-open-source-pivot.md. MotoQuant is free and open source: rank for accuracy, contributors, self-hostability and stability, never for revenue.

## Goal

Re-rank the open items in docs/ROADMAP.md based on this week's signals (accuracy sweep, open issues, contributor activity, user suggestions, outages). Propose the top-3 next items.

## Inputs to consider

- docs/ROADMAP.md (the live backlog) and open GitHub issues
- `data/competitive_landscape.md` (what competitors just shipped)
- `bike_suggestions` table (what users keep asking for)
- `DISPATCH_OUTBOX.md` (what blockers showed up this week)

## Workflow

1. Read all 4 inputs.
2. For each open roadmap item, score on (impact × confidence) / effort.
3. Identify any new feature ideas surfaced by signals.
4. Top-3 ranking written to `reports/product_priorities_YYYY-MM-DD.md`.
5. If the top-1 changes from last week's top-1: propose the docs/ROADMAP.md re-rank in the report (the maintainer applies it).

## Deliverable

- `reports/product_priorities_YYYY-MM-DD.md` (top 3 + reasoning)
- Optional: a proposed docs/ROADMAP.md diff in the report
- Optional: queue a `[opportunistic]` INSTRUCTION for the engineering team-of-one (you / agents / user) to start the new top-1

## Escalate

- If the top-1 requires a budget or external service (hosting plan, SMTP/Resend, LLM key, etc.): queue `[blocking]` for user.
- If signals are conflicting (KPIs say A, competitors say B): write both arguments, defer to user.

## Don't

- Don't propose an item without a concrete success metric.
- Don't propose monetization (paid tiers, quotas, licence keys) — scrapped by ADR-0006.
- Don't depromote items that have customer-facing INSTRUCTION queues already.
- Don't add new phases without strong signal — this is re-ranking, not roadmap inflation.

Cap ~700 words.
