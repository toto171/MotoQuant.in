#!/usr/bin/env bash
# session_preflight.sh — Mandatory bookend at the start of every Claude
# autonomous session against this repo.
#
# Why this exists:
#   The Cowork sandbox FUSE mount is unreliable for git operations
#   (random tokens.md gating, .git/*.lock immutability, write truncation,
#   /sessions disk-full pressure). This script sidesteps all of that by:
#     1. Acquiring a file-based session mutex (no parallel-session races).
#     2. Reading credentials from a non-FUSE location (~/.motoquant-secrets/).
#     3. Cloning fresh into /tmp (where writes are atomic + cheap).
#     4. Verifying the PAT works against origin BEFORE doing any work.
#     5. Running the K5/R1/Hayabusa baseline regression to detect
#        physics drift before any commit.
#     6. Writing a SESSION_LOG.md header so the postflight has context.
#
# After this script succeeds, the session does its work in
# $MQ_WORKDIR/repo (NOT in the FUSE mount). Postflight pushes from there.
#
# Exit codes:
#   0  — preflight clean, ready to work
#   1  — fatal: credentials missing or PAT invalid
#   2  — fatal: another session holds the mutex
#   3  — fatal: baseline regression failed (physics drift)
#   4  — fatal: clone failed
#   5  — soft: disk too full, abort and write to DISPATCH_INBOX

set -euo pipefail

# ─── Constants ───────────────────────────────────────────────────────────
readonly REPO_URL="https://github.com/da25mem5s02-debug/MotoQuant_v1.git"
readonly REPO_NAME="MotoQuant_v1"
readonly FUSE_MOUNT="/sessions/sharp-confident-cerf/mnt/Vehicle Dynamics"
# SECRETS_DIR resolution order (first existing wins):
#   1. $MOTOQUANT_SECRETS_DIR  — explicit override (recommended for sandboxes)
#   2. $HOME/.motoquant-secrets — standard home location (real machines)
#   3. /tmp/.motoquant-secrets  — fallback for read-only homes / disk-full
SECRETS_DIR="${MOTOQUANT_SECRETS_DIR:-}"
if [[ -z "${SECRETS_DIR}" ]]; then
  if [[ -w "${HOME}" ]] 2>/dev/null && touch "${HOME}/.motoquant-secrets-probe" 2>/dev/null; then
    rm -f "${HOME}/.motoquant-secrets-probe"
    SECRETS_DIR="${HOME}/.motoquant-secrets"
  else
    SECRETS_DIR="/tmp/.motoquant-secrets"
  fi
fi
readonly SECRETS_DIR
readonly SECRETS_FILE="${SECRETS_DIR}/git-creds.env"
readonly MUTEX_FILE="/tmp/motoquant-session.lock"
readonly MUTEX_MAX_AGE_HOURS=6
readonly DISK_FREE_MIN_MB=300
readonly BASELINE_TOLERANCE_S=0.005

# Identity policy (CLAUDE.md standing git-auth note as of 2026-05-04)
readonly GIT_NAME="Arya Desai"
readonly GIT_EMAIL="da25mem5s02@student.nitw.ac.in"

# Reference baselines are NOT duplicated here. They live in exactly one place —
# scripts/check_baselines.py — and verify_baselines() below delegates to it.
# This script used to carry its own inline copy of the pins; that copy went
# stale at the July-13 physics epoch (10.0334/10.2859/10.4712 vs the current
# 9.9331/10.1436/10.3633) and, at ±0.005 s tolerance, hard-failed step 5 with a
# false "physics drift" on a perfectly healthy tree — aborting every autonomous
# session at exit 3. session_postflight.sh had the identical bug and was fixed
# on 2026-07-17; this twin was missed and is fixed here (2026-07-25 audit).

# ─── Logging helpers ─────────────────────────────────────────────────────
log()   { printf "\033[36m[preflight]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[preflight WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[preflight FATAL]\033[0m %s\n" "$*" >&2; exit "${2:-1}"; }

# ─── 1. Mutex ────────────────────────────────────────────────────────────
acquire_mutex() {
  if [[ -f "${MUTEX_FILE}" ]]; then
    local lock_pid lock_time lock_age_hours
    lock_pid=$(awk -F= '/^pid=/{print $2}' "${MUTEX_FILE}" 2>/dev/null || echo "")
    lock_time=$(awk -F= '/^started=/{print $2}' "${MUTEX_FILE}" 2>/dev/null || echo "")

    # Stale-lock check (age > MUTEX_MAX_AGE_HOURS or PID dead)
    if [[ -n "${lock_time}" ]]; then
      local lock_epoch now_epoch
      lock_epoch=$(date -d "${lock_time}" +%s 2>/dev/null || echo 0)
      now_epoch=$(date +%s)
      lock_age_hours=$(( (now_epoch - lock_epoch) / 3600 ))
      if [[ ${lock_age_hours} -gt ${MUTEX_MAX_AGE_HOURS} ]]; then
        warn "stale lock (age ${lock_age_hours}h > ${MUTEX_MAX_AGE_HOURS}h) — claiming"
        rm -f "${MUTEX_FILE}"
      fi
    fi

    if [[ -n "${lock_pid:-}" ]] && kill -0 "${lock_pid}" 2>/dev/null; then
      warn "active session holds mutex (pid=${lock_pid}, started=${lock_time})"
      # Append a queued-deferral marker to DISPATCH_INBOX
      _queue_deferral "${lock_pid}" "${lock_time}"
      fatal "another session is active — deferred" 2
    fi

    if [[ -f "${MUTEX_FILE}" ]]; then
      log "removing stale mutex"
      rm -f "${MUTEX_FILE}"
    fi
  fi

  cat > "${MUTEX_FILE}" <<EOF
pid=$$
started=$(date -Iseconds)
session_id=${MQ_SESSION_ID:-$(date +%s)-$$}
holder=${USER:-claude}
EOF
  chmod 600 "${MUTEX_FILE}"
  log "acquired mutex (pid=$$)"
}

_queue_deferral() {
  local active_pid="$1" started="$2"
  local inbox="${FUSE_MOUNT}/DISPATCH_INBOX.md"
  if [[ -w "${inbox}" || -w "$(dirname "${inbox}")" ]]; then
    {
      echo ""
      echo "---"
      echo "## Session deferred — $(date -Iseconds)"
      echo "Tried to start a session but pid=${active_pid} already holds the lock"
      echo "(started ${started}). Will retry next scheduled tick."
    } >> "${inbox}" 2>/dev/null || true
  fi
}

# ─── 2. Credentials ──────────────────────────────────────────────────────
load_credentials() {
  if [[ ! -f "${SECRETS_FILE}" ]]; then
    fatal "${SECRETS_FILE} not found — run scripts/secrets_bootstrap.sh first" 1
  fi

  # shellcheck source=/dev/null
  set -a; source "${SECRETS_FILE}"; set +a

  if [[ -z "${PRIMARY_PAT:-}" ]]; then
    fatal "PRIMARY_PAT not set in ${SECRETS_FILE}" 1
  fi

  # Probe PRIMARY_PAT — fall back to BACKUP_PAT if invalid
  if _probe_pat "${PRIMARY_PAT}"; then
    export MQ_ACTIVE_PAT="${PRIMARY_PAT}"
    export MQ_PAT_TIER="primary"
    log "credentials: PRIMARY_PAT verified"
  elif [[ -n "${BACKUP_PAT:-}" ]] && _probe_pat "${BACKUP_PAT}"; then
    warn "PRIMARY_PAT failed validation — falling back to BACKUP_PAT"
    export MQ_ACTIVE_PAT="${BACKUP_PAT}"
    export MQ_PAT_TIER="backup"
    log "credentials: BACKUP_PAT verified — ROTATE PRIMARY ASAP"
    # Write a high-priority alert to DISPATCH_INBOX
    _queue_alert "PRIMARY_PAT failed validation, fell back to BACKUP. Rotate primary now."
  else
    fatal "both PRIMARY_PAT and BACKUP_PAT failed validation" 1
  fi
}

_probe_pat() {
  local pat="$1"
  # Lightweight probe: fetch only the HEAD ref (does not write anywhere).
  git -c "credential.helper=" \
      -c "credential.helper=!f() { echo username=x-access-token; echo password=${pat}; }; f" \
      ls-remote --heads "${REPO_URL}" main >/dev/null 2>&1
}

_queue_alert() {
  local msg="$1"
  local outbox="${FUSE_MOUNT}/DISPATCH_OUTBOX.md"
  {
    echo ""
    echo "## ALERT — $(date -Iseconds)"
    echo "${msg}"
  } >> "${outbox}" 2>/dev/null || true
}

# ─── 3. Disk check ───────────────────────────────────────────────────────
check_disk() {
  local free_mb
  free_mb=$(df -m /tmp | awk 'NR==2 {print $4}')
  if [[ ${free_mb} -lt ${DISK_FREE_MIN_MB} ]]; then
    warn "/tmp free=${free_mb}MB < required ${DISK_FREE_MIN_MB}MB"
    log "trying to free /tmp space..."
    rm -rf /tmp/mq-clean-* /tmp/mq-arya-* /tmp/sidecar-venv 2>/dev/null || true
    free_mb=$(df -m /tmp | awk 'NR==2 {print $4}')
    if [[ ${free_mb} -lt ${DISK_FREE_MIN_MB} ]]; then
      _queue_alert "Sandbox disk pressure: /tmp free=${free_mb}MB after cleanup. Session aborted."
      fatal "/tmp still too full (${free_mb}MB) — aborting session" 5
    fi
  fi
  log "disk: /tmp free=${free_mb}MB (ok)"
}

# ─── 4. /tmp clone ───────────────────────────────────────────────────────
fresh_clone() {
  export MQ_WORKDIR="/tmp/mq-session-$(date +%s)-$$"
  mkdir -p "${MQ_WORKDIR}"
  cd "${MQ_WORKDIR}"

  log "cloning ${REPO_URL} → ${MQ_WORKDIR}/repo"
  if ! git -c "credential.helper=" \
        -c "credential.helper=!f() { echo username=x-access-token; echo password=${MQ_ACTIVE_PAT}; }; f" \
        clone --quiet "${REPO_URL}" repo 2>&1 | tail -5; then
    fatal "git clone failed" 4
  fi

  cd repo
  git config user.name  "${GIT_NAME}"
  git config user.email "${GIT_EMAIL}"
  log "identity: $(git config user.name) <$(git config user.email)>"
  log "HEAD: $(git log -1 --format='%h %s')"

  # Cache PAT for postflight (reads MQ_ACTIVE_PAT from env)
  echo "${MQ_WORKDIR}" > /tmp/mq-active-workdir.path
}

# ─── 5. Baseline regression ──────────────────────────────────────────────
verify_baselines() {
  cd "${MQ_WORKDIR}/repo"
  log "running K5/R1/Hayabusa baseline regression..."

  if ! python3 scripts/check_baselines.py --tol "${BASELINE_TOLERANCE_S}" 2>&1; then
    fatal "baseline regression FAILED — physics drift detected, aborting" 3
  fi
  log "baselines: ALL PASS (within ±${BASELINE_TOLERANCE_S}s)"
}

# ─── 6. Read DISPATCH_INBOX ──────────────────────────────────────────────
read_dispatch_inbox() {
  local inbox="${MQ_WORKDIR}/repo/DISPATCH_INBOX.md"
  if [[ ! -f "${inbox}" ]]; then
    log "no DISPATCH_INBOX.md (skipping)"
    return 0
  fi

  local instructions
  # Only match real dated entries: ## INSTRUCTION — YYYY-MM-DD — ...
  # (templates and placeholders use literal "YYYY-MM-DD" so they don't match)
  instructions=$(awk '
    /^## INSTRUCTION — [0-9]{4}-[0-9]{2}-[0-9]{2}/ { p=1; print; next }
    /^## (DONE|DEFERRED|RESPONDED)/ { p=0 }
    /^## (INSTRUCTION|INSTRUCTIONS QUEUE|DONE|How to use|Severity|Templates|---)/ { p=0; next }
    p { print }
  ' "${inbox}")

  if [[ -n "${instructions}" ]]; then
    log "DISPATCH_INBOX has unprocessed instructions:"
    echo "${instructions}" | sed 's/^/  | /'
    export MQ_INBOX_HAS_WORK=1
  else
    log "DISPATCH_INBOX clean (no pending instructions)"
  fi
}

# ─── 7. Write SESSION_LOG.md header ──────────────────────────────────────
write_session_header() {
  local logfile="${MQ_WORKDIR}/SESSION_LOG.md"
  cat > "${logfile}" <<EOF
# Session log — ${MQ_SESSION_ID:-$(date -Iseconds)}

**Started:** $(date -Iseconds)
**Workdir:** ${MQ_WORKDIR}/repo
**HEAD at start:** $(cd "${MQ_WORKDIR}/repo" && git rev-parse HEAD)
**Identity:** ${GIT_NAME} <${GIT_EMAIL}>
**PAT tier:** ${MQ_PAT_TIER}
**Baselines:** ✓ K5/R1/Hayabusa within ±${BASELINE_TOLERANCE_S}s

---

## Work performed

EOF
  export MQ_SESSION_LOG="${logfile}"
  log "session log: ${MQ_SESSION_LOG}"
}

# ─── Run all phases ──────────────────────────────────────────────────────
main() {
  log "========================================"
  log "MotoQuant session preflight starting"
  log "========================================"
  acquire_mutex
  load_credentials
  check_disk
  fresh_clone
  verify_baselines
  read_dispatch_inbox
  write_session_header
  log "========================================"
  log "PREFLIGHT GREEN — workdir=${MQ_WORKDIR}/repo"
  log "  source the env file before doing work:"
  log "    eval \"\$(${MQ_WORKDIR}/preflight.env)\""
  log "========================================"

  # Emit env vars for the parent shell to source
  cat > "${MQ_WORKDIR}/preflight.env" <<EOF
export MQ_WORKDIR="${MQ_WORKDIR}"
export MQ_REPO="${MQ_WORKDIR}/repo"
export MQ_SESSION_LOG="${MQ_SESSION_LOG}"
export MQ_ACTIVE_PAT="${MQ_ACTIVE_PAT}"
export MQ_PAT_TIER="${MQ_PAT_TIER}"
export MQ_SESSION_ID="${MQ_SESSION_ID:-$(date +%s)-$$}"
export MQ_INBOX_HAS_WORK="${MQ_INBOX_HAS_WORK:-0}"
EOF
}

main "$@"
