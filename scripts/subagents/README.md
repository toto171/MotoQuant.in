# Cleanup subagents

Seven specialized read-only subagents that scan the codebase for specific classes of cruft. Adapted from the "Wize AI" multi-subagent pattern, tuned for the MotoQuant codebase (Python physics core + Next.js web + optional Rust core).

## What's here

| File | Subagent | Looking for |
|---|---|---|
| `01_deduplication.md` | DEDUPLICATION | Repeated logic, copy-pasted functions, redundant abstractions |
| `02_type_consolidation.md` | TYPE CONSOLIDATION | Type definitions scattered across files; cross-language drift |
| `03_dead_code.md` | DEAD CODE REMOVAL | Unused exports, unreferenced functions, orphaned files |
| `04_circular_dependencies.md` | CIRCULAR DEPENDENCIES | Import cycles, layer violations |
| `05_type_strengthening.md` | TYPE STRENGTHENING | `Any` / `dict[str, Any]` / TS `any` / weak signatures |
| `06_error_handling.md` | ERROR HANDLING CLEANUP | Silent swallows, bare excepts, defaults masking real values |
| `07_deprecated_and_slop.md` | DEPRECATED CODE & AI SLOP | Legacy paths, stubs, narrative-edit-history comments |

## Why they exist

Two things motivate this:

1. **The Kaizen Principle in CLAUDE.md** explicitly enumerates the same anti-patterns these subagents hunt for ("silent failure modes", "dead fields", "bypass paths", etc.). Running these passes is the operational form of that principle.
2. **AI-assisted codebases drift in predictable ways.** Splitting the cleanup work across specialized agents (vs one general "review the code" pass) gets significantly more signal — each agent is focused on a single failure class and has the prompt/context budget to do it justice.

## How to run them

### One-off (manual, this session only)

```bash
bash scripts/run_cleanup_subagents.sh           # all 7 in parallel
bash scripts/run_cleanup_subagents.sh 1 3 7      # subset by number
```

The driver dispatches each subagent prompt as an `Agent` tool call (when run inside a Claude session) or prints them to stdout for manual paste (when run from a real terminal).

### Routine (autonomous, monthly)

Wired into the weekly schedule in CLAUDE.md as the **last Sunday of every month**. Preflight reads the calendar; if today is "monthly cleanup day", the post-INBOX-handling work is replaced by a full subagent sweep with results consolidated into `reports/cleanup_consolidated_<YYYY-MM>.md` and a `## SESSION` block in `DISPATCH_OUTBOX.md`.

## Output convention

Each subagent writes a single markdown report to `reports/cleanup_subagent_<N>_<topic>.md`. Format is enforced by the prompt template:

```
# Subagent N — <topic> report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## High-confidence findings (apply these)
## Medium-confidence (verify before acting)
## False positives / leave alone
## Numerical summary
```

The driver concatenates all 7 into `reports/cleanup_consolidated_<YYYY-MM-DD>.md` after the run completes.

## What the human (or main session) does next

Reading the consolidated report, the main session decides which findings to action. Default policy:

- **High-confidence** → apply if mechanical and reversible (file deletes, dedup of test boilerplate, orphan removal). Skip if it touches physics / catalog / tests.
- **Medium-confidence** → write a `## INSTRUCTION` block to `DISPATCH_INBOX.md` for the user to triage.
- **False positives** → ignore.

NEVER apply a subagent's findings blindly. They're proposals; main session must verify against the codebase.

## What NOT to do

- Don't run subagents on every commit. They're meta-passes, not pre-commit hooks. Monthly is right.
- Don't extend the prompts to also "fix" things. Read-only is the contract — keeps the surface area small and the parallel runs safe.
- Don't add an 8th subagent without thinking hard. Seven is already a lot of context budget per pass.
