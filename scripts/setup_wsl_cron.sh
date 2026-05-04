#!/usr/bin/env bash
# setup_wsl_cron.sh — one-shot installer for the autonomous-ops cron under WSL2.
#
# Run this ONCE from inside WSL2 (Ubuntu/Debian) to:
#   1. Verify Claude Code is installed + logged in
#   2. Verify the secrets file exists
#   3. Install a crontab entry that runs run_autonomous_session.sh hourly
#   4. Set up systemd-cron-replacement so cron survives WSL restarts
#   5. Print the schedule + how to monitor logs
#
# WSL gotcha: cron doesn't auto-start in WSL2. We use either:
#   - `service cron start` (manual, dies on WSL shutdown)
#   - systemd (WSL2's modern path; survives restarts)
#
# Prereqs (run these once before this script):
#   sudo apt update && sudo apt install -y cron curl git
#   curl -fsSL https://nodejs.org/install.sh | bash    # or your preferred node
#   npm install -g @anthropic-ai/claude-code
#   claude login    # opens browser, auths against Claude.ai (Pro/Max)
#
# Usage:
#   bash scripts/setup_wsl_cron.sh                 # install hourly
#   bash scripts/setup_wsl_cron.sh --every 2       # every 2 hours
#   bash scripts/setup_wsl_cron.sh --every 6       # every 6 hours
#   bash scripts/setup_wsl_cron.sh --uninstall     # remove the cron entry
#   bash scripts/setup_wsl_cron.sh --status        # show current state

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly WRAPPER="${SCRIPT_DIR}/run_autonomous_session.sh"
readonly LOG_DIR="${REPO_ROOT}/logs"
readonly CRON_TAG="# motoquant-autonomous-session"

log()   { printf "\033[1;36m[wsl-cron]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[wsl-cron WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[wsl-cron FATAL]\033[0m %s\n" "$*" >&2; exit 1; }

# ─── Arg parsing ─────────────────────────────────────────────────────────
EVERY_HOURS=1
UNINSTALL=0
STATUS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --every)      EVERY_HOURS="$2"; shift 2 ;;
    --uninstall)  UNINSTALL=1; shift ;;
    --status)     STATUS=1; shift ;;
    --help|-h)    grep -E '^# ' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)            fatal "unknown arg: $1" ;;
  esac
done

# ─── Status mode ─────────────────────────────────────────────────────────
if [[ ${STATUS} -eq 1 ]]; then
  log "current crontab entries for autonomous session:"
  crontab -l 2>/dev/null | grep -A 0 -B 0 "${CRON_TAG}" || echo "  (none installed)"
  echo ""
  log "cron service status:"
  service cron status 2>&1 | head -5 || echo "  (cron not running)"
  echo ""
  log "recent logs (last 3):"
  ls -lt "${LOG_DIR}"/autonomous_*.log 2>/dev/null | head -3 || echo "  (no logs yet)"
  exit 0
fi

# ─── Uninstall mode ──────────────────────────────────────────────────────
if [[ ${UNINSTALL} -eq 1 ]]; then
  log "removing autonomous cron entry..."
  current=$(crontab -l 2>/dev/null || true)
  cleaned=$(echo "${current}" | grep -v "${CRON_TAG}" | grep -v "${WRAPPER}")
  if [[ -z "${cleaned}" ]]; then
    crontab -r 2>/dev/null || true
  else
    echo "${cleaned}" | crontab -
  fi
  log "removed. autonomous sessions will no longer fire from cron."
  exit 0
fi

# ─── Validate prereqs ────────────────────────────────────────────────────
log "checking prerequisites..."

# 1. WSL?
if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  warn "this doesn't look like WSL. Script will still work on plain Linux."
fi

# 2. cron installed?
if ! command -v crontab >/dev/null 2>&1; then
  fatal "crontab not installed. Run: sudo apt install cron"
fi

# 3. claude CLI?
if ! command -v claude >/dev/null 2>&1; then
  fatal "claude CLI not found. Install: npm install -g @anthropic-ai/claude-code"
fi
log "claude CLI: $(claude --version 2>&1 | head -1)"

# 4. claude logged in?
# Test with a no-op `claude config get` — fails if not logged in.
if ! claude --help >/dev/null 2>&1; then
  fatal "claude CLI broken. Try: claude --version"
fi
log "claude CLI looks ok (login state checked at runtime by wrapper)"

# 5. secrets file?
SECRETS_DIR="${MOTOQUANT_SECRETS_DIR:-${HOME}/.motoquant-secrets}"
SECRETS_FILE="${SECRETS_DIR}/git-creds.env"
if [[ ! -f "${SECRETS_FILE}" ]]; then
  fatal "secrets file missing: ${SECRETS_FILE}. Run: bash scripts/secrets_bootstrap.sh"
fi
log "secrets: ${SECRETS_FILE} (mode $(stat -c '%a' "${SECRETS_FILE}"))"

# 6. cron running?
if ! pgrep -x cron >/dev/null 2>&1; then
  warn "cron daemon not running. Starting it (one-time)..."
  if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    sudo systemctl enable cron
    sudo systemctl start cron
  else
    sudo service cron start
    warn "  (cron started via service — won't survive WSL shutdown)"
    warn "  enable WSL2 systemd: edit /etc/wsl.conf, add [boot]\\nsystemd=true, then 'wsl --shutdown' from PowerShell"
  fi
fi

# ─── Build the crontab line ──────────────────────────────────────────────
mkdir -p "${LOG_DIR}"

# Cron expression: every N hours at :00
if [[ ${EVERY_HOURS} -eq 1 ]]; then
  CRON_EXPR="0 * * * *"
elif [[ ${EVERY_HOURS} -le 23 ]]; then
  CRON_EXPR="0 */${EVERY_HOURS} * * *"
else
  CRON_EXPR="0 0 * * *"   # default daily if invalid
fi

# Cron line: bash wrapper, redirect stdout+stderr to dated log
CRON_LINE="${CRON_EXPR} cd ${REPO_ROOT} && bash ${WRAPPER} >> ${LOG_DIR}/cron.log 2>&1 ${CRON_TAG}"

log "installing cron entry:"
log "  schedule: every ${EVERY_HOURS}h"
log "  command:  bash ${WRAPPER}"
log "  log:      ${LOG_DIR}/cron.log + per-session ${LOG_DIR}/autonomous_*.log"

# ─── Install (idempotent: replace existing entry if present) ─────────────
current=$(crontab -l 2>/dev/null || true)
cleaned=$(echo "${current}" | grep -v "${CRON_TAG}" | grep -v "${WRAPPER}")
new_crontab=$(printf "%s\n%s\n" "${cleaned}" "${CRON_LINE}" | grep -v '^$')
echo "${new_crontab}" | crontab -

log ""
log "✓ installed. Verify with: crontab -l"
log ""
log "monitor with:"
log "  tail -f ${LOG_DIR}/cron.log              # live cron output"
log "  ls -lt ${LOG_DIR}/autonomous_*.log        # per-session detail"
log "  bash scripts/setup_wsl_cron.sh --status   # show this script's view"
log ""
log "control with:"
log "  bash scripts/START.sh --pause             # pause without removing cron"
log "  bash scripts/START.sh --unpause           # resume"
log "  bash scripts/setup_wsl_cron.sh --uninstall  # remove cron entry"
log ""
log "the first session will fire at the next ${CRON_EXPR/0 / } mark."
