# Agent M2: incident-postmortem

Read CLAUDE.md, the incident's OUTBOX entry, the most recent SESSION_LOG.md, the failing commit's diff (`git show <sha>`).

## Trigger

Auto-dispatched on `## INCIDENT` posting in DISPATCH_OUTBOX. Runs once per unique incident, blamelessly.

## Goal

Root-cause + propose either: (a) a code/script fix, (b) a kaizen improvement to prevent the class of incident, (c) both.

## Workflow

1. Reproduce the failure if possible (run the failing command in a /tmp clone).
2. Read the last 100 lines of the affected SESSION_LOG.md.
3. Identify the precipitating change (last commit before failure or an external event).
4. Write a 5-Why root-cause chain (use a single screen, not a long essay).
5. Propose ONE fix: minimum diff, narrowest scope, with test coverage.
6. Propose ONE kaizen: what would have prevented detection-late vs detection-early?

## Deliverable

- `reports/postmortem_YYYY-MM-DD_<incident_id>.md` (5-Why + fix + kaizen)
- If the fix is mechanical and obvious: implement it as part of this session
- If the fix needs judgement: queue `[blocking]` INSTRUCTION for user
- Update `data/incident_history.json` (append the incident with classification)

## Don't

- Never blame an individual commit author. Blame the system that allowed the bad commit to land.
- Never paper over a class of bug — if it happened once it'll happen again.
- Never close an incident without the fix landing AND a test covering it.

Cap ~700 words.
