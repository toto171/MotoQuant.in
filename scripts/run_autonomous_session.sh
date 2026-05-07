#!/usr/bin/env bash
# run_autonomous_session.sh — the cron-friendly wrapper that spawns a Claude
# Code session, feeds it the master autonomous-ops prompt, and lets it
# orchestrate one full session end-to-end.
#
# This is what your Windows Task Scheduler should invoke:
#   bash scripts/run_autonomous_session.sh
#
# Internally:
#   1. Loads ~/.motoquant-secrets/git-creds.env (so PAT is available).
#   2. cd to the repo.
#   3. Invokes `claude` (Claude Code CLI) in headless mode with a master
#      prompt that tells Claude to run START.sh, parse the dispatch plan,
#      execute each agent in parallel via the Agent tool, then run
#      postflight with the union of files-touched.
#   4. Logs Claude's stdout to logs/autonomous_<date>.log for later review.
#   5. Captures exit code; non-zero exits get echoed to OUTBOX as INCIDENT.
#
# Requires:
#   - Claude Code CLI installed (https://docs.claude.com/en/docs/claude-code)
#     or `npm install -g @anthropic-ai/claude-code`
#   - ANTHROPIC_API_KEY env var (or claude CLI is logged in via `claude login`)
#   - The autonomous-ops stack already pushed (you have it).
#
# Usage:
#   bash scripts/run_autonomous_session.sh                 # normal run
#   bash scripts/run_autonomous_session.sh --catchup       # force catchup mode
#   bash scripts/run_autonomous_session.sh --dry-run       # plan only

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LOG_DIR="${REPO_ROOT}/logs"
readonly LOG_FILE="${LOG_DIR}/autonomous_$(date +%Y-%m-%d_%H%M%S).log"

mkdir -p "${LOG_DIR}"

log() { printf "\033[1;36m[autonomous-runner]\033[0m %s\n" "$*" | tee -a "${LOG_FILE}"; }
fatal() { printf "\033[31m[autonomous-runner FATAL]\033[0m %s\n" "$*" | tee -a "${LOG_FILE}"; exit 1; }

log "════════════════════════════════════════════════════════════════"
log "Autonomous session wrapper — $(date -Iseconds)"
log "Log: ${LOG_FILE}"
log "════════════════════════════════════════════════════════════════"

# ─── Load secrets so claude inherits credentials ─────────────────────────
SECRETS_DIR="${MOTOQUANT_SECRETS_DIR:-${HOME}/.motoquant-secrets}"
SECRETS_FILE="${SECRETS_DIR}/git-creds.env"

if [[ ! -f "${SECRETS_FILE}" ]]; then
  fatal "secrets file missing at ${SECRETS_FILE}. Run: bash scripts/secrets_bootstrap.sh"
fi
# shellcheck source=/dev/null
set -a; source "${SECRETS_FILE}"; set +a
log "secrets loaded from ${SECRETS_FILE}"

# ─── Verify claude CLI is available ──────────────────────────────────────
if ! command -v claude >/dev/null 2>&1; then
  fatal "claude CLI not found in PATH. Install via 'npm install -g @anthropic-ai/claude-code' or download from https://claude.com/download"
fi
log "claude CLI: $(claude --version 2>&1 | head -1)"

# ─── Verify ANTHROPIC_API_KEY OR claude is logged in ─────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]] && ! claude config get apiKey >/dev/null 2>&1; then
  fatal "no ANTHROPIC_API_KEY and 'claude' not logged in. Run 'claude login' once."
fi

# ─── Pass-through args ───────────────────────────────────────────────────
EXTRA_ARGS="$*"

# ─── The master prompt — Claude reads this and orchestrates ──────────────
read -r -d '' MASTER_PROMPT << 'PROMPT' || true
You are running in autonomous-ops mode for the MotoQuant Pro project. Read CLAUDE.md and docs/AUTONOMOUS_OPERATIONS_PLAYBOOK.md first to understand the system you're operating.

Your job for THIS SESSION:

1. Run `bash scripts/START.sh` (no flags unless I passed --dry-run or --catchup, in which case append them).

2. Capture the dispatch plan from START.sh's output. The plan has 1-3 selected agents listed under "### Today's selected agents (in dispatch order)".

3. Source the preflight env file:
   eval "$(cat /tmp/mq-session-*/preflight.env | tail -n +1)"
   This gives you $MQ_REPO, $MQ_WORKDIR, $MQ_ACTIVE_PAT, $MQ_SESSION_ID.

4. cd to $MQ_REPO. ALL agent work happens there, NOT the FUSE / workspace folder.

5. For each agent in the dispatch plan, dispatch it as a parallel Agent tool call. Pass the agent's prompt template as the prompt (read from scripts/agents/<agent>.md). Each agent should:
   - Do its narrow, focused work per its prompt.
   - Make file edits in $MQ_REPO.
   - Return a list of files touched and a one-line commit summary.

6. After all agents complete, gather the union of files-touched (de-duplicated) and an aggregated commit message that mentions each agent's contribution.

7. Run postflight:
   bash scripts/session_postflight.sh \
        --message "<aggregated message>" \
        --files "<space-separated unique file list>"

   Postflight will: re-verify baselines, run focused tests, run anti_slop_check, stage the explicit file list, commit as Arya Desai, push to origin/main with PAT fallback, verify Railway redeploy via curl, append a SESSION block to DISPATCH_OUTBOX.md, sync the FUSE mount, release the mutex.

8. If any phase fails: do NOT push. Write a clear ## INCIDENT block to DISPATCH_OUTBOX.md describing what failed, then exit. The mutex's EXIT trap will release.

9. Print a one-line summary to stdout when done so the wrapper can log it.

Constraints:
- KAIZEN is the operating principle. Every session should produce either a committed delta OR a research artifact OR a populated dataset row. Sessions with no delta are tagged "null" in STATUS.md and freshness-weighted-up next time.
- Reference baselines (K5/R1/Hayabusa) MUST stay at +0.0000s. If baselines drift, postflight refuses to push — that's correct behaviour.
- Anti-hallucination gates are enforced. Every factual claim in marketing/competitive/benchmark output must cite a source. Anti-slop blocks AI-tell phrases pre-commit.
- Use Sonnet for routine code work, Haiku for lookups, Opus only for deep/ambiguous tasks (per the playbook routing table).
- Do NOT bypass postflight to push directly.
- Do NOT skip baseline verification.

Begin.
PROMPT

# ─── Invoke claude in headless / non-interactive mode ────────────────────
log "spawning claude (headless mode, model=default)..."
log ""

cd "${REPO_ROOT}"

# claude -p "<prompt>" runs the prompt non-interactively. The session does
# all its work, then exits. stdout streams live; we tee to log file.
#
# The append-to-prompt logic below pipes our extra args (--catchup etc.)
# down so START.sh sees them.
if [[ -n "${EXTRA_ARGS}" ]]; then
  PROMPT_FINAL="${MASTER_PROMPT}

Pass the following args to START.sh: ${EXTRA_ARGS}"
else
  PROMPT_FINAL="${MASTER_PROMPT}"
fi

# Run claude with default model (Sonnet 4.6 typically).
# --dangerously-skip-permissions: required for unattended runs since the
#   wrapper can't approve permission prompts. If you'd rather be prompted,
#   remove this flag and run interactively.
# 2>&1: merge stderr into stdout so the log captures everything.
set +e
claude --dangerously-skip-permissions -p "${PROMPT_FINAL}" </dev/null 2>&1 | tee -a "${LOG_FILE}"
CLAUDE_EXIT=${PIPESTATUS[0]}
set -e

log ""
log "claude exited with code ${CLAUDE_EXIT}"

if [[ ${CLAUDE_EXIT} -ne 0 ]]; then
  # Append an INCIDENT block to OUTBOX so the user sees it tomorrow morning
  OUTBOX="${REPO_ROOT}/DISPATCH_OUTBOX.md"
  if [[ -f "${OUTBOX}" ]]; then
    {
      echo ""
      echo "## INCIDENT — autonomous wrapper exited non-zero — $(date -Iseconds)"
      echo "claude exit code: ${CLAUDE_EXIT}"
      echo "Log: \`${LOG_FILE}\`"
      echo "First sign of trouble in the log:"
      grep -iE "(error|fatal|fail|incident)" "${LOG_FILE}" | head -10 | sed 's/^/  /'
    } >> "${OUTBOX}" 2>/dev/null || true
  fi
  fatal "session failed — see ${LOG_FILE}"
fi

log "session complete. log: ${LOG_FILE}"

# Optional cleanup: keep last 30 logs, prune older
log "pruning logs older than 30d..."
find "${LOG_DIR}" -name 'autonomous_*.log' -mtime +30 -delete 2>/dev/null || true

log "done."
