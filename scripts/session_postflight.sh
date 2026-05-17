#!/usr/bin/env bash
# session_postflight.sh — Mandatory bookend at the end of every Claude
# autonomous session against this repo.
#
# What it does:
#   1. Re-verify K5/R1/Hayabusa baselines (catch regressions before push).
#   2. Run a focused-test subset (scraper / validation / two_stroke /
#      compatibility / submodel_kaizen / power_boost_regression).
#   3. Stage explicit-list of files (NEVER `git add -A`).
#   4. Commit with the provided message + Arya Desai identity.
#   5. Push to origin/main with PRIMARY → BACKUP PAT fallback.
#   6. Verify Railway redeploy + bike_count via curl.
#   7. Append outcome to DISPATCH_OUTBOX.md (committed in the same push).
#   8. Sync the FUSE mount (cp from /tmp/mq-session/ → FUSE) so the user
#      sees the latest state from their real terminal.
#   9. Release the session mutex.
#
# Usage:
#   eval "$(/path/to/preflight.env)"   # exports MQ_WORKDIR + MQ_ACTIVE_PAT
#   cd "${MQ_REPO}"
#   ... do work, edit files, etc ...
#   bash scripts/session_postflight.sh \
#        --message "feat(catalog): add bike X" \
#        --files "motoquant/scraper/known_bikes.py tests/test_scraper.py"
#
# Exit codes:
#   0  — everything pushed, deploy verified, FUSE synced
#   1  — fatal: required env vars missing
#   2  — fatal: baseline regression broke
#   3  — fatal: focused-test subset broke
#   4  — fatal: push failed (both primary + backup PAT)
#   5  — soft: deploy verification timeout (push succeeded)
#   6  — fatal: headline-sync auto-patch gate failed

set -euo pipefail

readonly REPO_URL="https://github.com/da25mem5s02-debug/MotoQuant_v1.git"
readonly FUSE_MOUNT="/sessions/sharp-confident-cerf/mnt/Vehicle Dynamics"
readonly MUTEX_FILE="/tmp/motoquant-session.lock"
readonly RAILWAY_HEALTH="https://web-production-de6eb.up.railway.app/api/health"
readonly DEPLOY_WAIT_SECONDS=180   # max wait for Railway to redeploy
readonly DEPLOY_POLL_SECONDS=15
readonly BASELINE_TOLERANCE_S=0.005

readonly TARGET_K5=10.0334
readonly TARGET_R1=10.2859
readonly TARGET_BUSA=10.4712

log()   { printf "\033[36m[postflight]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[postflight WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[postflight FATAL]\033[0m %s\n" "$*" >&2; exit "${2:-1}"; }

# ─── Arg parsing ─────────────────────────────────────────────────────────
COMMIT_MESSAGE=""
COMMIT_FILES=""
SKIP_PUSH=0
SKIP_DEPLOY_CHECK=0
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --message)  COMMIT_MESSAGE="$2"; shift 2 ;;
    --files)    COMMIT_FILES="$2"; shift 2 ;;
    --skip-push) SKIP_PUSH=1; shift ;;
    --skip-deploy-check) SKIP_DEPLOY_CHECK=1; shift ;;
    --dry-run)  DRY_RUN=1; shift ;;
    --help|-h)
      grep -E '^# ' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) fatal "unknown arg: $1" ;;
  esac
done

# ─── Sanity: env from preflight ──────────────────────────────────────────
[[ -z "${MQ_WORKDIR:-}" ]] && fatal "MQ_WORKDIR not set — did you run preflight first?" 1
[[ -z "${MQ_ACTIVE_PAT:-}" ]] && fatal "MQ_ACTIVE_PAT not set" 1
[[ ! -d "${MQ_WORKDIR}/repo" ]] && fatal "${MQ_WORKDIR}/repo missing" 1

cd "${MQ_WORKDIR}/repo"
log "starting postflight from ${MQ_WORKDIR}/repo"
log "HEAD: $(git log -1 --format='%h %s')"

# ─── 1. Baseline regression (catch physics drift before push) ────────────
verify_baselines() {
  log "re-verifying K5/R1/Hayabusa baselines..."
  python3 -c "
import sys, motoquant
from motoquant import MotoQuantEngine
TOL = ${BASELINE_TOLERANCE_S}
fails = []
for name, cfg, target in [
    ('K5', motoquant.gsxr1000_k5(), ${TARGET_K5}),
    ('R1', motoquant.yzfr1_4c8(), ${TARGET_R1}),
    ('Busa', motoquant.hayabusa_gen1(), ${TARGET_BUSA}),
]:
    et = MotoQuantEngine(cfg).run().time_quarter
    delta = et - target
    s = 'PASS' if abs(delta) < TOL else 'FAIL'
    print(f'  {name:6s} sim={et:.4f}s target={target:.4f}s delta={delta:+.4f}s {s}')
    if s == 'FAIL': fails.append(name)
sys.exit(1 if fails else 0)
" || fatal "baseline regression FAILED — refusing to push" 2
  log "baselines: ALL PASS"
}

# ─── 2. Focused test subset ──────────────────────────────────────────────
run_focused_tests() {
  log "running focused test subset..."
  if ! PYTHONPATH=. python3 -m pytest -q --no-header --tb=line \
        tests/test_scraper.py \
        tests/test_validation.py \
        tests/test_two_stroke.py \
        tests/test_compatibility.py \
        tests/test_submodel_kaizen.py \
        tests/test_power_boost_regression.py \
        2>&1 | tail -5; then
    fatal "focused test subset FAILED — refusing to push" 3
  fi
  log "focused tests: green"
}

# ─── 2.5. Headline-sync auto-patch gate ──────────────────────────────────
# Runs `audit_headline_stats.py --fix --regen-og` AFTER agents finish but
# BEFORE staging. Auto-patches stale numbers across web/blog/docs/README and
# regenerates the OG social card if drift detected. Files modified by --fix
# are appended to COMMIT_FILES so the drift-fix rides the same commit as the
# work that caused the drift (no separate chore(headline-sync) commits).
headline_sync_gate() {
  log "running headline-sync auto-patch gate..."
  local fix_json fixed_list
  # NOTE: we pass --fix only (not --regen-og). The audit script auto-regens
  # the OG card when text drift was patched OR the cached image is older
  # than motoquant.db. Forcing --regen-og every session would create noise
  # commits even when no numbers shifted.
  if ! fix_json=$(python3 scripts/audit_headline_stats.py --fix --json 2>/dev/null); then
    _queue_alert "Postflight headline-sync gate FAILED — could not run audit_headline_stats.py --fix. Push aborted."
    fatal "headline-sync gate failed (audit script returned non-zero)" 6
  fi

  fixed_list=$(printf '%s' "$fix_json" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(' '.join(d.get('fixed_files', []) or []))
except Exception as exc:
    sys.stderr.write(f'JSON parse failed: {exc}\n')
    sys.exit(1)
" 2>/dev/null) || {
    _queue_alert "Postflight headline-sync gate: JSON parse failed on audit output. Push aborted."
    fatal "headline-sync gate JSON parse failed" 6
  }

  if [[ -z "${fixed_list}" ]]; then
    log "headline-sync: no drift detected, no patches applied"
    return 0
  fi

  log "headline-sync auto-patched: ${fixed_list}"
  # Append fixed files to COMMIT_FILES (de-duplicated). Drift-fix rides the
  # same commit as the agent work so we don't proliferate chore commits.
  for f in ${fixed_list}; do
    if [[ " ${COMMIT_FILES} " != *" ${f} "* ]]; then
      COMMIT_FILES="${COMMIT_FILES} ${f}"
    fi
  done
  log "COMMIT_FILES updated → ${COMMIT_FILES}"
}

# ─── 2.7. STATUS.md timestamp stamp (INBOX:322 — self-review M1 Sec B.2/B.3)
# Writes the current UTC ISO timestamp into STATUS.md's "_LAST_RUN_JSON._updated"
# field and the top-level "last_run:" placeholder. Auto-appends STATUS.md to
# COMMIT_FILES so the bump rides the same commit as the agent work (no
# separate chore commit). Runs even on no-op sessions — the GH-Actions
# heartbeat side-channel relies on _updated being non-null to detect dark
# windows.
stamp_status_timestamps() {
  log "stamping STATUS.md _updated + last_run (INBOX:322)..."
  if ! python3 scripts/stamp_status_timestamps.py STATUS.md 2>&1 | tail -3; then
    warn "STATUS.md stamp failed — continuing (non-fatal)"
    return 0
  fi
  if [[ " ${COMMIT_FILES} " != *" STATUS.md "* ]]; then
    COMMIT_FILES="${COMMIT_FILES} STATUS.md"
    log "STATUS.md appended to COMMIT_FILES"
  fi
}

# ─── 3. Stage explicit files (NEVER git add -A) ──────────────────────────
stage_files() {
  if [[ -z "${COMMIT_FILES}" ]]; then
    log "no --files given — checking if there's anything to stage"
    if [[ -z "$(git status --porcelain)" ]]; then
      log "working tree clean — skipping commit"
      return 1
    fi
    warn "uncommitted changes exist but no --files provided — listing for you:"
    git status --short
    fatal "refusing to use 'git add -A' — pass --files explicitly" 1
  fi

  # shellcheck disable=SC2086
  git add ${COMMIT_FILES}
  log "staged: ${COMMIT_FILES}"
  git status --short | head -20
  return 0
}

# ─── 4. Commit ───────────────────────────────────────────────────────────
do_commit() {
  if [[ -z "${COMMIT_MESSAGE}" ]]; then
    fatal "no --message given" 1
  fi
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "[dry-run] would commit with message: ${COMMIT_MESSAGE}"
    return 0
  fi
  git commit -m "${COMMIT_MESSAGE}" 2>&1 | tail -5
  local sha; sha=$(git rev-parse HEAD)
  log "committed: ${sha}"
  echo "${sha}" > /tmp/mq-last-commit.sha
}

# ─── 5. Push with primary → backup fallback ──────────────────────────────
do_push() {
  if [[ ${SKIP_PUSH} -eq 1 ]] || [[ ${DRY_RUN} -eq 1 ]]; then
    log "skip-push or dry-run — not pushing"
    return 0
  fi
  log "pushing to origin/main (PAT tier=${MQ_PAT_TIER})..."
  if git -c "credential.helper=" \
        -c "credential.helper=!f() { echo username=x-access-token; echo password=${MQ_ACTIVE_PAT}; }; f" \
        push origin main 2>&1 | tail -3; then
    log "push: ok"
    return 0
  fi

  # Push with primary failed — try backup if not already on it
  if [[ "${MQ_PAT_TIER}" == "primary" && -n "${BACKUP_PAT:-}" ]]; then
    warn "primary push failed — trying BACKUP_PAT"
    if git -c "credential.helper=" \
          -c "credential.helper=!f() { echo username=x-access-token; echo password=${BACKUP_PAT}; }; f" \
          push origin main 2>&1 | tail -3; then
      log "push via BACKUP: ok"
      _queue_alert "Postflight push fell back to BACKUP_PAT — primary failed"
      return 0
    fi
  fi

  fatal "push failed (both primary and backup)" 4
}

# ─── 6. Deploy verification ──────────────────────────────────────────────
verify_deploy() {
  if [[ ${SKIP_DEPLOY_CHECK} -eq 1 ]] || [[ ${SKIP_PUSH} -eq 1 ]] || [[ ${DRY_RUN} -eq 1 ]]; then
    log "skipping deploy verification"
    return 0
  fi
  log "waiting up to ${DEPLOY_WAIT_SECONDS}s for Railway to redeploy..."
  local elapsed=0
  while [[ ${elapsed} -lt ${DEPLOY_WAIT_SECONDS} ]]; do
    sleep ${DEPLOY_POLL_SECONDS}
    elapsed=$((elapsed + DEPLOY_POLL_SECONDS))
    local body
    body=$(curl -fsS --max-time 10 "${RAILWAY_HEALTH}" 2>/dev/null || echo "")
    if [[ "${body}" == *'"status":"ok"'* ]]; then
      log "deploy: live (${body})"
      return 0
    fi
    log "  waited ${elapsed}s — still waiting"
  done
  warn "deploy verification timeout — push landed but Railway not responding ok"
  _queue_alert "Postflight deploy check timed out after ${DEPLOY_WAIT_SECONDS}s"
  return 5
}

# ─── 7. Append DISPATCH_OUTBOX entry ─────────────────────────────────────
append_outbox() {
  local outbox="${MQ_WORKDIR}/repo/DISPATCH_OUTBOX.md"
  local sha; sha=$(git rev-parse HEAD 2>/dev/null || echo "(no commit)")

  {
    echo ""
    echo "## $(date -Iseconds) — session ${MQ_SESSION_ID:-unknown}"
    echo ""
    echo "**Commit:** \`${sha}\`"
    echo "**Files:** \`${COMMIT_FILES:-(none)}\`"
    echo ""
    if [[ -f "${MQ_SESSION_LOG:-/dev/null}" ]]; then
      tail -50 "${MQ_SESSION_LOG}" | sed 's/^/> /'
    fi
  } >> "${outbox}"
  log "outbox: appended entry"
}

_queue_alert() {
  local msg="$1"
  local outbox="${MQ_WORKDIR}/repo/DISPATCH_OUTBOX.md"
  {
    echo ""
    echo "### ALERT — $(date -Iseconds)"
    echo "${msg}"
  } >> "${outbox}" 2>/dev/null || true
}

# ─── 8. Sync FUSE-mount with origin (final state) ────────────────────────
sync_fuse() {
  if [[ ! -d "${FUSE_MOUNT}" ]]; then
    log "FUSE mount not present — skipping sync"
    return 0
  fi
  log "syncing FUSE mount with /tmp clone..."

  # Sync only the files that changed in this session, not everything.
  # Whole-tree rsync would corrupt FUSE-side artifacts.
  if [[ -n "${COMMIT_FILES}" ]]; then
    for f in ${COMMIT_FILES}; do
      local src="${MQ_WORKDIR}/repo/${f}"
      local dst="${FUSE_MOUNT}/${f}"
      if [[ -f "${src}" ]]; then
        mkdir -p "$(dirname "${dst}")" 2>/dev/null || true
        cp "${src}" "${dst}" 2>/dev/null && log "  synced: ${f}" \
          || warn "  FUSE sync failed for ${f} (FUSE permission tier?)"
      fi
    done
  fi

  # Sync the DISPATCH_OUTBOX too (so user sees the report in their workspace)
  cp "${MQ_WORKDIR}/repo/DISPATCH_OUTBOX.md" "${FUSE_MOUNT}/DISPATCH_OUTBOX.md" 2>/dev/null || true
}

# ─── 9. Cleanup ──────────────────────────────────────────────────────────
release_mutex() {
  if [[ -f "${MUTEX_FILE}" ]]; then
    rm -f "${MUTEX_FILE}" 2>/dev/null && log "released mutex" \
      || warn "could not release mutex — stale lock left behind"
  fi
}

prune_old_workdirs() {
  log "pruning /tmp/mq-session-* older than 24h..."
  find /tmp -maxdepth 1 -name 'mq-session-*' -type d -mmin +1440 -exec rm -rf {} + 2>/dev/null || true
}

# ─── Main ────────────────────────────────────────────────────────────────
main() {
  log "========================================"
  log "MotoQuant session postflight starting"
  log "========================================"
  trap 'release_mutex' EXIT

  verify_baselines
  run_focused_tests
  headline_sync_gate
  stamp_status_timestamps

  if stage_files; then
    do_commit
    do_push
    verify_deploy || warn "deploy unverified (non-fatal)"
    append_outbox
    # Re-push outbox-only commit if needed
    if [[ -n "$(git status --porcelain)" ]]; then
      git add DISPATCH_OUTBOX.md
      git commit -m "chore(dispatch): postflight outbox entry [skip ci]" || true
      git -c "credential.helper=" \
          -c "credential.helper=!f() { echo username=x-access-token; echo password=${MQ_ACTIVE_PAT}; }; f" \
          push origin main 2>&1 | tail -3 || warn "outbox-only push failed"
    fi
    sync_fuse
  else
    log "no commit needed this session"
  fi

  prune_old_workdirs
  log "========================================"
  log "POSTFLIGHT COMPLETE"
  log "========================================"
}

main
