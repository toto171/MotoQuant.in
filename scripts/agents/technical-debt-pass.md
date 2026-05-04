# Agent A9: technical-debt-pass

Read CLAUDE.md (Kaizen Principle), the most recent `reports/cleanup_subagent_*` reports.

## Goal

ONE narrow refactor PR. <300 LOC delta, single concern, full test coverage, zero physics regression.

## Today's pick (priority order)

1. Apply ONE high-confidence finding from the latest cleanup-subagent reports (look at consolidated report).
2. If subagent reports aren't fresh: `grep -rn "TODO\|FIXME\|XXX\|HACK" motoquant/` and pick the longest-standing.
3. Otherwise: pick the file with the worst current cyclomatic complexity (manual eyeball if no tool installed).

## Workflow

1. State the refactor goal in one sentence.
2. State the success criteria (e.g., "remove _TestDB triplication, ≤200 LOC delta").
3. Make the change.
4. Run focused tests. Run baselines. Run any relevant invariant tests.
5. If anything regresses → revert and queue `[research]` instead.

## Deliverable

- Code edits in source tree
- `reports/tech_debt_<topic>_YYYY-MM-DD.md` with before/after metric

## Don't

- No drive-by changes (one file per session unless they're inseparable).
- No "while I'm here" type changes — out of scope is out of scope.
- No physics or catalog edits ever (those have dedicated agents).
- Never relax a test to make a refactor pass.

Cap ~700 words.
