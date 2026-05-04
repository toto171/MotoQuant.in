# Agent A8: customer-support

Read CLAUDE.md first.

## Goal

Triage `bike_suggestions` table entries (user-submitted bike requests). For each: validate, classify, respond/queue.

## Workflow

1. `SELECT * FROM bike_suggestions WHERE status='pending' ORDER BY created_at DESC LIMIT 20`
2. For each: lookup if bike already in catalog (typo? rename?), check spec plausibility, decide:
   - **Add now:** queue `[opportunistic]` for catalog-expansion
   - **Need more info:** mark status='needs_info' with question
   - **Out of scope:** mark status='rejected' with reason
   - **Duplicate:** mark status='duplicate' with reference
3. If `bike_suggestions` is empty: scan DISPATCH_OUTBOX for the last 30d of `### ALERT` entries. Group by category, propose top-3 systemic fixes.

## Deliverable

- DB updates to `bike_suggestions.status` + `response`
- `reports/support_triage_YYYY-MM-DD.md`
- Optional: 1-3 INSTRUCTION queue entries

## Don't

- Never auto-add a suggested bike without spec verification (catalog-expansion handles that).
- Never reject with "out of scope" for any bike legitimately ridden in India.
- Never close a suggestion without a recorded response.

Cap ~500 words.
