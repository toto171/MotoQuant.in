#!/usr/bin/env bash
# resilience.sh — power-cut + internet-downtime resilience helpers.
#
# This is a library of bash functions sourced by START.sh / preflight /
# postflight / master_scheduler. NOT executed standalone (the `case` block
# at the bottom is a CLI shim for individual function tests).
#
# Three concerns:
#
#   1. CHECKPOINTING — a session writes incremental progress to
#      $MQ_WORKDIR/checkpoint.json after every major step. If the session
#      is killed (power cut, kernel OOM, sandbox eviction), the next
#      preflight detects the orphan workdir, reads its checkpoint, and
#      decides to resume vs. discard.
#
#   2. NETWORK HEALTH — every network call goes through `net_call`,
#      which probes connectivity first. If offline: queue the call to
#      $MQ_WORKDIR/network_queue.jsonl for retry on next session.
#
#   3. CATCHUP — if the system was offline / paused for N days,
#      preflight detects the gap (last STATUS.md timestamp vs now).
#      Catchup mode runs the most-stale agents in priority order, with
#      a per-session cap so we don't spam a week of work in one push.

# ─── Constants ───────────────────────────────────────────────────────────
readonly RESILIENCE_LIB_VERSION=1
readonly NET_PROBE_HOST="${NET_PROBE_HOST:-github.com}"
readonly NET_PROBE_TIMEOUT=5
readonly CATCHUP_MAX_AGENTS_PER_SESSION=4
readonly CHECKPOINT_INCOMPATIBLE_VERSION_RESET=1

resilience_log()   { printf "\033[36m[resilience]\033[0m %s\n" "$*" >&2; }
resilience_warn()  { printf "\033[33m[resilience WARN]\033[0m %s\n" "$*" >&2; }

# ─── 1. CHECKPOINTING ────────────────────────────────────────────────────
#
# Per-session checkpoint at $MQ_WORKDIR/checkpoint.txt — flat key=value
# format. Pure bash (no Python) so it works identically on Linux + Windows
# MINGW where bash and Python disagree on path separators (/tmp vs \tmp).
#
# Format:
#   version=1
#   session_id=<id>
#   started=<iso>
#   phase=<phase>
#   completed_phases=preflight,mobile_dispatch,...
#   completed_agents=catalog-expansion:ok,physics-calibration:ok,...
#   files_touched=path1 path2 ...
#   last_heartbeat=<iso>

# checkpoint_init — call from preflight after MQ_WORKDIR is set
checkpoint_init() {
  local cp="${MQ_WORKDIR}/checkpoint.txt"
  if [[ -f "${cp}" ]]; then
    resilience_warn "existing checkpoint detected at ${cp} — recovery mode"
  fi
  cat > "${cp}" <<EOF
version=${RESILIENCE_LIB_VERSION}
session_id=${MQ_SESSION_ID:-unknown}
started=$(date -Iseconds)
phase=preflight_init
completed_phases=
completed_agents=
files_touched=
last_heartbeat=$(date -Iseconds)
EOF
}

# checkpoint_advance <phase_name>
checkpoint_advance() {
  local phase="$1"
  local cp="${MQ_WORKDIR}/checkpoint.txt"
  [[ ! -f "${cp}" ]] && { resilience_warn "no checkpoint to advance"; return; }

  # Read existing completed_phases, append if not already there
  local current
  current=$(grep -E "^completed_phases=" "${cp}" 2>/dev/null | sed 's/^completed_phases=//')
  if [[ ",${current}," != *",${phase},"* ]]; then
    if [[ -z "${current}" ]]; then
      current="${phase}"
    else
      current="${current},${phase}"
    fi
  fi

  # Rewrite three keys (idempotent)
  local tmp; tmp="$(mktemp)"
  awk -v phase="${phase}" -v completed="${current}" -v hb="$(date -Iseconds)" '
    /^phase=/         { print "phase=" phase; next }
    /^completed_phases=/ { print "completed_phases=" completed; next }
    /^last_heartbeat=/   { print "last_heartbeat=" hb; next }
    { print }
  ' "${cp}" > "${tmp}" && mv -f "${tmp}" "${cp}"

  resilience_log "checkpoint advanced: ${phase}"
}

# checkpoint_record_agent <agent_name> <outcome>
checkpoint_record_agent() {
  local agent="$1" outcome="${2:-ok}"
  local cp="${MQ_WORKDIR}/checkpoint.txt"
  [[ ! -f "${cp}" ]] && return

  local current
  current=$(grep -E "^completed_agents=" "${cp}" 2>/dev/null | sed 's/^completed_agents=//')
  local entry="${agent}:${outcome}"
  if [[ -z "${current}" ]]; then
    current="${entry}"
  else
    current="${current},${entry}"
  fi

  local tmp; tmp="$(mktemp)"
  awk -v completed="${current}" -v hb="$(date -Iseconds)" '
    /^completed_agents=/ { print "completed_agents=" completed; next }
    /^last_heartbeat=/   { print "last_heartbeat=" hb; next }
    { print }
  ' "${cp}" > "${tmp}" && mv -f "${tmp}" "${cp}"
}

# checkpoint_record_files <space-separated file list>
checkpoint_record_files() {
  local files="$1"
  local cp="${MQ_WORKDIR}/checkpoint.txt"
  [[ ! -f "${cp}" ]] && return

  local current
  current=$(grep -E "^files_touched=" "${cp}" 2>/dev/null | sed 's/^files_touched=//')
  # Append new files, dedupe
  local merged
  merged=$(printf '%s %s\n' "${current}" "${files}" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
  merged="${merged% }"  # trim trailing space

  local tmp; tmp="$(mktemp)"
  awk -v files="${merged}" -v hb="$(date -Iseconds)" '
    /^files_touched=/ { print "files_touched=" files; next }
    /^last_heartbeat=/ { print "last_heartbeat=" hb; next }
    { print }
  ' "${cp}" > "${tmp}" && mv -f "${tmp}" "${cp}"
}

# checkpoint_complete — call from postflight just before mutex release
checkpoint_complete() {
  local cp="${MQ_WORKDIR}/checkpoint.txt"
  [[ ! -f "${cp}" ]] && return
  local tmp; tmp="$(mktemp)"
  awk -v at="$(date -Iseconds)" '
    /^phase=/ { print "phase=complete"; next }
    /^last_heartbeat=/ { print "last_heartbeat=" at; next }
    END { print "completed_at=" at }
    { print }
  ' "${cp}" > "${tmp}" && mv -f "${tmp}" "${cp}"
  resilience_log "checkpoint marked complete"
}

# resume_check — detect orphan workdirs from killed sessions
# Outputs: orphan workdir path (one per line) or empty
resume_check() {
  local now_epoch; now_epoch=$(date +%s)
  for d in /tmp/mq-session-*; do
    [[ -d "${d}" ]] || continue
    local cp="${d}/checkpoint.txt"
    [[ ! -f "${cp}" ]] && continue
    local phase heartbeat
    phase=$(grep -E "^phase=" "${cp}" 2>/dev/null | sed 's/^phase=//' | head -1)
    heartbeat=$(grep -E "^last_heartbeat=" "${cp}" 2>/dev/null | sed 's/^last_heartbeat=//' | head -1)
    if [[ "${phase}" == "complete" ]]; then
      continue   # not an orphan
    fi
    if [[ -n "${heartbeat}" ]]; then
      local hb_epoch; hb_epoch=$(date -d "${heartbeat}" +%s 2>/dev/null || echo 0)
      local age_min=$(( (now_epoch - hb_epoch) / 60 ))
      if [[ ${age_min} -gt 60 ]]; then
        echo "${d}"
      fi
    fi
  done
}

# ─── 2. NETWORK HEALTH ───────────────────────────────────────────────────

network_is_up() {
  curl -fsS --max-time "${NET_PROBE_TIMEOUT}" \
       -o /dev/null "https://${NET_PROBE_HOST}/" 2>/dev/null
}

# net_call <description> <command...>
# Run a network-dependent command. If offline: queue for later, return non-zero.
net_call() {
  local desc="$1"; shift
  if network_is_up; then
    "$@"
    return $?
  fi
  resilience_warn "network down — queueing: ${desc}"
  local q="${MQ_WORKDIR:-/tmp}/network_queue.jsonl"
  printf '{"queued":"%s","desc":"%s","cmd":%s}\n' \
         "$(date -Iseconds)" "${desc}" "$(printf '%s\n' "$*" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')" \
         >> "${q}"
  return 99   # signal: queued, not failed
}

# drain_network_queue — at start of each session, retry queued calls
drain_network_queue() {
  local q="${MQ_WORKDIR:-/tmp}/network_queue.jsonl"
  [[ ! -f "${q}" ]] && return
  resilience_log "draining network queue: $(wc -l < "${q}") items"
  if ! network_is_up; then
    resilience_warn "still offline — leaving queue intact"
    return 1
  fi
  # Replay each queued line. Successful = drop. Failed = re-queue.
  local tmp; tmp="$(mktemp)"
  while IFS= read -r line; do
    local cmd; cmd=$(echo "${line}" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["cmd"])')
    if eval "${cmd}"; then
      resilience_log "  drained: ${cmd:0:60}..."
    else
      echo "${line}" >> "${tmp}"
    fi
  done < "${q}"
  mv -f "${tmp}" "${q}"
}

# ─── 3. CATCHUP MODE ─────────────────────────────────────────────────────

# catchup_detect — returns "1" if last session was > 24h ago, "0" otherwise
catchup_detect() {
  # MQ_REPO may not be set yet when called pre-preflight (from START.sh).
  # Fall back to "no catchup" silently in that case.
  local repo="${MQ_REPO:-}"
  if [[ -z "${repo}" ]]; then
    # Try to find STATUS.md relative to the script
    local script_dir; script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    repo="$(cd "${script_dir}/.." && pwd)"
  fi
  local status="${repo}/STATUS.md"
  [[ ! -f "${status}" ]] && { echo 0; return; }
  local last; last=$(grep -oE 'last_run: [0-9-]+T[0-9:+]+' "${status}" 2>/dev/null | head -1 | awk '{print $2}')
  [[ -z "${last}" ]] && { echo 0; return; }
  local last_epoch now_epoch
  last_epoch=$(date -d "${last}" +%s 2>/dev/null || echo 0)
  now_epoch=$(date +%s)
  local hours_gap=$(( (now_epoch - last_epoch) / 3600 ))
  if [[ ${hours_gap} -gt 24 ]]; then
    resilience_warn "catchup mode: last session was ${hours_gap}h ago (> 24h gap)"
    echo 1
  else
    echo 0
  fi
}

# catchup_plan — when in catchup, prefer agents that haven't run in N days
# Caps at CATCHUP_MAX_AGENTS_PER_SESSION to avoid spamming a single push.
catchup_plan() {
  resilience_log "catchup plan: prioritising stalest agents (max ${CATCHUP_MAX_AGENTS_PER_SESSION} per session)"
  # The master_scheduler already prefers stale agents via freshness-weight.
  # Catchup mode just cranks the freshness multiplier and caps selection count.
  export MQ_CATCHUP_MODE=1
  export MQ_CATCHUP_MAX="${CATCHUP_MAX_AGENTS_PER_SESSION}"
}

# ─── CLI shim ────────────────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  case "${1:-}" in
    network-up)        network_is_up && echo "online" || echo "offline" ;;
    resume-check)      resume_check ;;
    catchup-detect)    catchup_detect ;;
    drain-queue)       drain_network_queue ;;
    *) cat <<USAGE
Usage: bash scripts/resilience.sh <subcommand>
  network-up        — probe network, print online/offline
  resume-check      — list orphaned workdirs from killed sessions
  catchup-detect    — print 1 if last run was > 24h ago
  drain-queue       — replay queued network calls

This script is normally SOURCED by START.sh / preflight / postflight,
not run standalone. The CLI is for manual probing only.
USAGE
       exit 0 ;;
  esac
fi
