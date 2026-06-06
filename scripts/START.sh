#!/usr/bin/env bash
# START.sh — single entry-point for an autonomous MotoQuant session.
#
# This script is what your scheduled task runs (or you run manually with no
# arguments). It orchestrates the full session lifecycle from preflight
# through agent dispatch through postflight.
#
# Lifecycle:
#   1. Source resilience.sh (network probes, checkpointing, catchup)
#   2. Detect catchup mode (last run > 24h ago)
#   3. Detect orphan workdirs (killed sessions)
#   4. Run session_preflight.sh (mutex, creds, baselines, clone)
#   5. Run mobile_dispatch_handler.sh (expand mobile-shorthand inbox)
#   6. Run master_scheduler.sh — emits the day's dispatch plan
#   7. The CALLING CLAUDE SESSION reads the plan and dispatches Agent
#      tool calls in parallel. (When run from a real terminal without
#      Claude, the plan is printed for human reference.)
#   8. Postflight stages explicit files, runs anti_slop_check, source-verifier,
#      tests, baselines, pushes with PAT fallback, verifies deploy, syncs FUSE.
#   9. Mark checkpoint complete, release mutex.
#
# Usage:
#   bash scripts/START.sh                 # Normal session
#   bash scripts/START.sh --reset         # Reset scheduler weights to defaults
#   bash scripts/START.sh --catchup       # Force catchup mode
#   bash scripts/START.sh --inbox-only    # Process queued instructions only
#   bash scripts/START.sh --dry-run       # Print plan, do nothing else
#   bash scripts/START.sh --pause         # Pause autonomous ops
#   bash scripts/START.sh --unpause       # Resume autonomous ops
#   bash scripts/START.sh --status        # Print current STATUS.md
#
# Environment variables (override defaults):
#   MOTOQUANT_SECRETS_DIR   Path to git-creds.env (default: ~/.motoquant-secrets/)
#   MQ_SESSION_ID           Override session id (default: timestamp+pid)
#   MQ_DRY_RUN              Set to 1 to skip all writes
#   NET_PROBE_HOST          Host for network probe (default: github.com)

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Source the resilience library
# shellcheck source=./resilience.sh
. "${SCRIPT_DIR}/resilience.sh"

# ─── Logging ─────────────────────────────────────────────────────────────
log()   { printf "\033[1;36m[START]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[START WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[START FATAL]\033[0m %s\n" "$*" >&2; exit 1; }

# ─── Arg parsing ─────────────────────────────────────────────────────────
RESET=0
CATCHUP=0
INBOX_ONLY=0
DRY_RUN=0
PAUSE=0
UNPAUSE=0
STATUS_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset)        RESET=1; shift ;;
    --catchup)      CATCHUP=1; shift ;;
    --inbox-only)   INBOX_ONLY=1; shift ;;
    --dry-run)      DRY_RUN=1; shift ;;
    --pause)        PAUSE=1; shift ;;
    --unpause)      UNPAUSE=1; shift ;;
    --status)       STATUS_ONLY=1; shift ;;
    --help|-h)      grep -E '^# ' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)              fatal "unknown arg: $1" ;;
  esac
done

# ─── Quick non-session commands ──────────────────────────────────────────
PAUSE_FLAG_DIR="${MOTOQUANT_SECRETS_DIR:-/tmp/.motoquant-secrets}"
PAUSE_FLAG="${PAUSE_FLAG_DIR}/paused.flag"

if [[ ${PAUSE} -eq 1 ]]; then
  mkdir -p "${PAUSE_FLAG_DIR}"
  echo "paused at $(date -Iseconds)" > "${PAUSE_FLAG}"
  log "autonomous ops PAUSED (flag: ${PAUSE_FLAG})"
  exit 0
fi

if [[ ${UNPAUSE} -eq 1 ]]; then
  if [[ -f "${PAUSE_FLAG}" ]]; then
    rm -f "${PAUSE_FLAG}"
    log "autonomous ops RESUMED"
  else
    log "(was not paused)"
  fi
  exit 0
fi

if [[ ${STATUS_ONLY} -eq 1 ]]; then
  cat "${REPO_ROOT}/STATUS.md"
  exit 0
fi

if [[ ${RESET} -eq 1 ]]; then
  bash "${SCRIPT_DIR}/master_scheduler.sh" --reset
  log "scheduler weights reset to defaults"
  exit 0
fi

# ─── Pause-flag check (skip session if paused) ───────────────────────────
if [[ -f "${PAUSE_FLAG}" ]]; then
  log "session SKIPPED — autonomous ops paused (flag at ${PAUSE_FLAG})"
  log "   resume with: bash scripts/START.sh --unpause"
  exit 0
fi

# Repo-local pause flag (durable across WSL restarts, unlike the /tmp flag
# above). Added 2026-06-06 after stale WSL cron entries kept firing sessions.
if [[ -f "${REPO_ROOT}/AUTONOMOUS_PAUSED" ]]; then
  log "session SKIPPED — AUTONOMOUS_PAUSED flag present at repo root"
  log "   re-enable with: rm '${REPO_ROOT}/AUTONOMOUS_PAUSED'"
  exit 0
fi

log "════════════════════════════════════════════════════════════════"
log "MotoQuant autonomous session — $(date -Iseconds)"
log "════════════════════════════════════════════════════════════════"

# ─── Resilience: orphan-workdir detection ────────────────────────────────
ORPHANS=$(resume_check)
if [[ -n "${ORPHANS}" ]]; then
  warn "found orphan workdirs from killed sessions:"
  echo "${ORPHANS}" | while read -r d; do warn "  ${d}"; done
  warn "(left intact — incident-postmortem agent will inspect)"
fi

# ─── Resilience: network probe ───────────────────────────────────────────
if network_is_up; then
  log "network: ONLINE"
else
  warn "network: OFFLINE — preflight will fail at PAT validation; aborting."
  warn "queue any in-progress writes; system will retry on next scheduled run."
  # Append to OUTBOX for visibility
  if [[ -f "${REPO_ROOT}/DISPATCH_OUTBOX.md" ]]; then
    {
      echo ""
      echo "### ALERT — network offline at session start — $(date -Iseconds)"
      echo "Aborted before preflight. Will auto-retry on next scheduled tick."
    } >> "${REPO_ROOT}/DISPATCH_OUTBOX.md"
  fi
  exit 0   # exit clean so the scheduled task doesn't mark this as a failure
fi

# ─── Resilience: drain network queue from prior offline session ──────────
drain_network_queue || warn "network queue partial drain (some items left)"

# ─── Resilience: catchup-mode detection ──────────────────────────────────
if [[ ${CATCHUP} -eq 1 ]] || [[ "$(catchup_detect)" == "1" ]]; then
  catchup_plan
  log "CATCHUP MODE active (will prefer stale agents, capped at ${MQ_CATCHUP_MAX:-4} per session)"
fi

# ─── Phase 1: PREFLIGHT ──────────────────────────────────────────────────
log ""
log "PHASE 1 / 4 — preflight"
log "─────────────────────────"
if ! bash "${SCRIPT_DIR}/session_preflight.sh"; then
  fatal "preflight failed — see above. exiting without postflight."
fi

# Source the env file the preflight wrote
LATEST_WORKDIR=$(ls -d /tmp/mq-session-* 2>/dev/null | tail -1)
if [[ -z "${LATEST_WORKDIR}" || ! -f "${LATEST_WORKDIR}/preflight.env" ]]; then
  fatal "preflight succeeded but env file missing"
fi
# shellcheck source=/dev/null
. "${LATEST_WORKDIR}/preflight.env"
checkpoint_init
checkpoint_advance preflight

# ─── Phase 2: MOBILE DISPATCH HANDLER ────────────────────────────────────
log ""
log "PHASE 2 / 4 — mobile dispatch expansion"
log "─────────────────────────────────────────"
INBOX="${MQ_REPO}/DISPATCH_INBOX.md" \
OUTBOX="${MQ_REPO}/DISPATCH_OUTBOX.md" \
WEIGHTS="${MQ_REPO}/scripts/scheduler_weights.json" \
PAUSE_FLAG="${PAUSE_FLAG}" \
REPO="${MQ_REPO}" \
  bash "${MQ_REPO}/scripts/mobile_dispatch_handler.sh" || warn "mobile dispatch had issues (continuing)"
checkpoint_advance mobile_dispatch

# ─── Phase 3: SCHEDULER + AGENT DISPATCH ─────────────────────────────────
log ""
log "PHASE 3 / 4 — master scheduler"
log "────────────────────────────────"
PLAN_FILE="${MQ_WORKDIR}/dispatch_plan.md"
bash "${MQ_REPO}/scripts/master_scheduler.sh" $([[ ${INBOX_ONLY} -eq 1 ]] && echo "--inbox-only") > "${PLAN_FILE}"
checkpoint_advance scheduler

log ""
log "─── Today's dispatch plan ─────────────────────────────────"
cat "${PLAN_FILE}"
log "──────────────────────────────────────────────────────────"
log ""

if [[ ${DRY_RUN} -eq 1 ]]; then
  log "DRY RUN — exiting before agent dispatch + postflight"
  exit 0
fi

# When this script runs INSIDE a Claude Code session, the calling LLM
# reads ${PLAN_FILE} from stdout and dispatches the agents listed.
#
# When run from a real terminal (no LLM in the loop), we emit a notice
# and let the user dispatch them manually via Claude mobile dispatch.

if [[ -z "${CLAUDE_AGENT_SDK:-}${ANTHROPIC_API_KEY:-}" ]]; then
  log ""
  log "ℹ︎  Plan above written to ${PLAN_FILE}"
  log "ℹ︎  Standalone-terminal mode: a human (or Claude session) needs to"
  log "ℹ︎  dispatch the agents listed. Then re-run:"
  log "ℹ︎    bash ${SCRIPT_DIR}/session_postflight.sh --message '...' --files '...'"
  exit 0
fi

# Inside a Claude session, the next phase is invoked by the calling LLM.
# We print a marker the LLM can grep for to know it should now dispatch.
echo ""
echo "═════════════ AGENT DISPATCH HANDOFF ═════════════"
echo "PLAN_FILE=${PLAN_FILE}"
echo "WORKDIR=${MQ_WORKDIR}"
echo "REPO=${MQ_REPO}"
echo "SESSION_ID=${MQ_SESSION_ID}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Calling Claude session: read ${PLAN_FILE}, dispatch each agent in"
echo "parallel via Agent tool calls. After all agents complete, gather"
echo "the union of files-touched, then run:"
echo ""
echo "  bash ${SCRIPT_DIR}/session_postflight.sh \\"
echo "       --message '<aggregated commit message>' \\"
echo "       --files '<space-separated file list>'"
echo ""
echo "Postflight will run anti_slop_check, source-verifier, tests, baselines,"
echo "push with PAT fallback, verify deploy, sync FUSE, release mutex."
