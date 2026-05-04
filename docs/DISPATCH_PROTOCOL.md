# Dispatch protocol

The day-to-day comms channel between you (the user) and autonomous Claude sessions running against this repo. Asynchronous, file-based, survives FUSE quirks.

## TL;DR

- **You write to me:** edit `DISPATCH_INBOX.md` at repo root. Add an `## INSTRUCTION` block. Commit.
- **I write to you:** every session appends to `DISPATCH_OUTBOX.md`. Newest at the bottom.
- **I run automatically:** scheduled tasks fire daily; each one runs `session_preflight.sh` → does work → runs `session_postflight.sh`.

## Why this exists

You work an 8-hour internship daily. You can't be the human-in-the-loop for every commit. The chat interface assumes you're online — this file-based channel doesn't. You queue work in the morning from your phone, I do it during your work day, you read the outcome at night.

## File ownership

| File | Writer | Reader | Notes |
|---|---|---|---|
| `DISPATCH_INBOX.md` | User | Claude (preflight reads at session start) | Append `## INSTRUCTION` blocks. Claude marks them `## DONE`. |
| `DISPATCH_OUTBOX.md` | Claude (postflight) | User | Read end-of-day. Look for `### ALERT` and `## INCIDENT`. |
| `~/.motoquant-secrets/git-creds.env` | User (one-time setup via `scripts/secrets_bootstrap.sh`) | Claude (preflight) | NEVER in repo. NEVER on FUSE mount. |
| `/tmp/motoquant-session.lock` | Preflight (acquire) / Postflight (release) | All sessions | File-based mutex prevents parallel-session collisions |

## Session lifecycle

```
                    ┌─────────────────────────────┐
                    │   Scheduled task fires      │
                    │   (cron / Claude scheduler) │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   session_preflight.sh      │
                    │  - acquire mutex            │
                    │  - load PRIMARY_PAT (or     │
                    │    fall back to BACKUP)     │
                    │  - check disk               │
                    │  - clone fresh to /tmp      │
                    │  - verify K5/R1/Busa        │
                    │    baselines                │
                    │  - read DISPATCH_INBOX      │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Session does work in      │
                    │   $MQ_WORKDIR/repo          │
                    │   (NEVER touches FUSE git)  │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   session_postflight.sh     │
                    │  - re-verify baselines      │
                    │  - run focused tests        │
                    │  - stage explicit files     │
                    │  - commit as Arya Desai     │
                    │  - push with PAT fallback   │
                    │  - verify Railway deploy    │
                    │  - append DISPATCH_OUTBOX   │
                    │  - sync FUSE (cp only)      │
                    │  - release mutex            │
                    └─────────────────────────────┘
```

## What happens on failure

| Failure | Severity | Outcome |
|---|---|---|
| Mutex held by live session | soft | Defer; write deferral note to INBOX; exit 2 |
| Mutex held by stale process (PID dead) | recoverable | Claim it; proceed |
| PRIMARY_PAT invalid | recoverable | Fall back to BACKUP_PAT; ALERT in OUTBOX |
| Both PATs invalid | fatal | INCIDENT in OUTBOX; exit 1 |
| `/tmp` disk full | recoverable | Auto-prune; retry; ALERT if still full |
| Baseline regression breaks | fatal | Refuse to commit; INCIDENT in OUTBOX; exit 3 |
| Focused tests break | fatal | Refuse to commit; INCIDENT in OUTBOX; exit 3 |
| Push fails | fatal | Try BACKUP_PAT; if still fails, INCIDENT; exit 4 |
| Deploy verification timeout | soft | ALERT in OUTBOX; exit 5 (push still landed) |
| FUSE sync fails | soft | Log warning; continue (commit + push already happened) |

## Writing INSTRUCTIONs to the inbox

See `DISPATCH_INBOX.md` for the full template. Quick reference:

```markdown
## INSTRUCTION — 2026-05-15 — add bike: Aprilia Tuono V4 1100 Factory 2024
[opportunistic]

Spec source: https://www.aprilia.com/en_EN/models/tuono-v4/
Key numbers: 175 hp / 121 Nm / 184 kg dry / 1077 cc V4
Drivetrain: 525 chain, 16/41 sprocket
Notes: dry clutch, semi-active suspension
```

Severity tags:
- `[urgent]` — handle in the very next session
- `[blocking]` — refuse other work until this is done
- `[opportunistic]` — fold in when convenient
- `[research]` — investigate + report back, don't act

## Reading OUTBOX entries

Each session appends one block. Format:

```markdown
## 2026-05-15T18:23:14+05:30 — session 1715789394-12345

**Commit:** `abc1234`
**Files:** `motoquant/scraper/known_bikes.py tests/test_scraper.py`

> [tail of SESSION_LOG.md, indented as a blockquote]
```

Look for:
- **`### ALERT`** — non-blocking issues (e.g. backup PAT used, deploy slow). Address within a few days.
- **`## INCIDENT`** — session aborted. Needs real-terminal action immediately.

## Operational notes

- Sessions DO NOT block on each other across days — mutex is per-running-process, not per-day.
- If two Claude sessions try to start simultaneously, the second one defers and writes a `## SESSION DEFERRED` block to INBOX. The next scheduled run picks it up.
- The mutex auto-stales after 6 hours (in case a process crashed without releasing).
- All git operations happen in `/tmp/mq-session-*` — the FUSE mount is read-only for git-state purposes during a session.
- The FUSE mount is updated at the end (postflight `sync_fuse` step) so your real-terminal `git pull` shows the latest state.

## When to bypass this protocol

You can always make commits from your real terminal directly — the protocol is for autonomous Claude sessions, not for you. If you're sitting at the keyboard and want to push a one-off fix, just `git commit && git push` normally.

If you DO push from real-terminal during a session, the next preflight will detect the divergence (clone is fresh from origin every time) and pick up your changes automatically.
