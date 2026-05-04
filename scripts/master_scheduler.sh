#!/usr/bin/env bash
# master_scheduler.sh — picks today's autonomous work and emits a dispatch plan.
#
# Reads:
#   - $MQ_REPO/STATUS.md          (recent outcomes, KPIs, weekly review)
#   - $MQ_REPO/DISPATCH_INBOX.md  (queued user instructions)
#   - $MQ_REPO/scripts/agents/    (12 agent prompt templates)
#   - data/market_signals.json    (refreshed by competitive-intel agent)
#   - $MQ_REPO/scripts/scheduler_weights.json (default + self-tuned weights)
#   - day-of-week (date +%u: 1=Mon..7=Sun)
#
# Writes (to stdout for the calling Claude session to act on):
#   - DISPATCH PLAN — N lines describing which agents to dispatch, in what order,
#     with what model preference, and what files they're allowed to touch.
#
# Usage:
#   bash scripts/master_scheduler.sh             # emit today's plan
#   bash scripts/master_scheduler.sh --dry-run   # show scoring detail
#   bash scripts/master_scheduler.sh --inbox-only  # process only queued instructions
#   bash scripts/master_scheduler.sh --reset     # reset scheduler weights to defaults
#
# Designed to be called by START.sh AFTER session_preflight.sh has succeeded.
# MQ_WORKDIR / MQ_REPO must already be set in the environment.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO="${MQ_REPO:-${SCRIPT_DIR}/..}"
readonly AGENTS_DIR="${REPO}/scripts/agents"
readonly STATUS_FILE="${REPO}/STATUS.md"
readonly INBOX_FILE="${REPO}/DISPATCH_INBOX.md"
readonly SIGNALS_FILE="${REPO}/data/market_signals.json"
readonly WEIGHTS_FILE="${REPO}/scripts/scheduler_weights.json"

log()   { printf "\033[36m[scheduler]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[scheduler FATAL]\033[0m %s\n" "$*" >&2; exit 1; }

# ─── Arg parsing ─────────────────────────────────────────────────────────
DRY_RUN=0
INBOX_ONLY=0
RESET=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=1; shift ;;
    --inbox-only) INBOX_ONLY=1; shift ;;
    --reset)      RESET=1; shift ;;
    --help|-h)    grep -E '^# ' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)            fatal "unknown arg: $1" ;;
  esac
done

# ─── Default scheduler weights ───────────────────────────────────────────
write_default_weights() {
  cat > "${WEIGHTS_FILE}" <<'JSON'
{
  "_meta": {
    "schema": 1,
    "last_self_review": null,
    "comment": "agents are scored each morning. Higher = more likely to run today. Self-review can adjust ±10 per cycle. Manual override via mobile dispatch."
  },
  "agents": {
    "catalog-expansion":      { "base": 50, "best_dow": [1] },
    "physics-calibration":    { "base": 40, "best_dow": [3] },
    "benchmark-import":       { "base": 40, "best_dow": [2] },
    "marketing-content":      { "base": 35, "best_dow": [1, 5] },
    "seo-keyword":            { "base": 30, "best_dow": [1] },
    "competitive-intel":      { "base": 25, "best_dow": [2] },
    "product-prioritisation": { "base": 20, "best_dow": [4] },
    "customer-support":       { "base": 30, "best_dow": [4] },
    "technical-debt-pass":    { "base": 25, "best_dow": [3, 6] },
    "performance-monitor":    { "base": 20, "best_dow": [7] },
    "growth-experiments":     { "base": 30, "best_dow": [5] },
    "partnership-outreach":   { "base": 25, "best_dow": [5] },
    "self-review":            { "base": 50, "best_dow": [7] }
  }
}
JSON
  log "default weights written to ${WEIGHTS_FILE}"
}

if [[ ${RESET} -eq 1 ]]; then
  mkdir -p "$(dirname "${WEIGHTS_FILE}")"
  write_default_weights
  exit 0
fi

[[ ! -f "${WEIGHTS_FILE}" ]] && write_default_weights

# ─── Inbox parsing ───────────────────────────────────────────────────────
parse_inbox_urgent() {
  [[ ! -f "${INBOX_FILE}" ]] && { echo ""; return; }
  awk '
    /^## INSTRUCTION — [0-9]{4}-[0-9]{2}-[0-9]{2}/ { p=1; t=$0; next }
    /^## (DONE|DEFERRED|RESPONDED)/ { p=0 }
    p && /\[(urgent|blocking)\]/ { print t; p=0 }
  ' "${INBOX_FILE}" 2>/dev/null
}

count_inbox_pending() {
  [[ ! -f "${INBOX_FILE}" ]] && { echo 0; return; }
  awk '/^## INSTRUCTION — [0-9]{4}-[0-9]{2}-[0-9]{2}/ {n++} END {print n+0}' "${INBOX_FILE}"
}

# ─── Pause-flag check ────────────────────────────────────────────────────
PAUSE_FLAG="${MOTOQUANT_SECRETS_DIR:-/tmp/.motoquant-secrets}/paused.flag"
if [[ -f "${PAUSE_FLAG}" ]]; then
  log "PAUSED (flag at ${PAUSE_FLAG} — remove to resume)"
  echo "## DISPATCH PLAN — $(date -Iseconds) — PAUSED"
  echo "(no work scheduled; remove ${PAUSE_FLAG} to resume)"
  exit 0
fi

# ─── Day of week ─────────────────────────────────────────────────────────
DOW=$(date +%u)   # 1 (Mon) .. 7 (Sun)
DOW_NAME=$(date +%A)
TODAY=$(date -I)
log "scheduling for ${DOW_NAME} (dow=${DOW}), date=${TODAY}"

# ─── Score each agent ────────────────────────────────────────────────────
# We use a simple Python helper to compute scores from the JSON weights file.
score_agents() {
  python3 - <<PYEOF
import json, sys, os, subprocess

def _np(p):
    """Cross-platform path normalize: MINGW /tmp/ → Windows via cygpath."""
    if not p:
        return p
    if os.name == "nt" and p.startswith("/"):
        try:
            out = subprocess.check_output(["cygpath", "-w", p], text=True).strip()
            return out if out else p
        except Exception:
            return p
    return p

weights_file = _np("${WEIGHTS_FILE}")
inbox_file   = _np("${INBOX_FILE}")
status_file  = _np("${STATUS_FILE}")
signals_file = _np("${SIGNALS_FILE}")
dow          = int("${DOW}")
agents_dir   = _np("${AGENTS_DIR}")

with open(weights_file) as f:
    weights = json.load(f)

# Last-run tracking from STATUS.md (a JSON block at the bottom)
last_run = {}
if os.path.isfile(status_file):
    with open(status_file) as f:
        text = f.read()
    if "<!-- LAST_RUN_JSON" in text:
        block = text.split("<!-- LAST_RUN_JSON", 1)[1].split("-->", 1)[0]
        try:
            last_run = json.loads(block.strip())
        except Exception:
            pass

# Market signals (lightweight; absent = empty)
signals = {}
if os.path.isfile(signals_file):
    try:
        with open(signals_file) as f:
            signals = json.load(f)
    except Exception:
        pass

# INBOX queued count (per-agent if tagged)
inbox_count_per_agent = {}
if os.path.isfile(inbox_file):
    with open(inbox_file) as f:
        for line in f:
            for agent in weights["agents"]:
                if f"@{agent}" in line:
                    inbox_count_per_agent[agent] = inbox_count_per_agent.get(agent, 0) + 1

import datetime
def days_since(iso):
    if not iso: return 99
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(iso[:10])).days
    except Exception:
        return 99

scores = []
for agent, w in weights["agents"].items():
    base = w["base"]
    best_dow = w.get("best_dow", [])
    dow_bonus = 30 if dow in best_dow else 0
    queue_bonus = 50 * inbox_count_per_agent.get(agent, 0)
    last = last_run.get(agent, {})
    days = days_since(last.get("date"))
    freshness = max(0, min(20, days * 3))      # bigger if stale
    if last.get("outcome") == "fail":
        freshness += 20                         # retry boost
    if last.get("consecutive_fails", 0) >= 3:
        freshness = -100                        # circuit-break this agent
    sig = signals.get(agent, {}).get("opportunity_boost", 0)
    score = base + dow_bonus + queue_bonus + freshness + sig
    scores.append({
        "agent": agent,
        "score": score,
        "base": base,
        "dow_bonus": dow_bonus,
        "queue_bonus": queue_bonus,
        "freshness": freshness,
        "signal_bonus": sig,
        "days_since_last_run": days,
        "last_outcome": last.get("outcome", "unknown"),
    })

scores.sort(key=lambda s: -s["score"])

# Pick top 3 (primary + 2 fills) above floor
floor = 30
picks = [s for s in scores if s["score"] >= floor][:3]

# Always include self-review on Sunday regardless
if dow == 7 and not any(p["agent"] == "self-review" for p in picks):
    sr = next(s for s in scores if s["agent"] == "self-review")
    picks.append(sr)

print(json.dumps({
    "all_scored": scores,
    "selected": picks,
    "dow": dow,
    "date": "${TODAY}",
}, indent=2))
PYEOF
}

# ─── Emit dispatch plan ──────────────────────────────────────────────────
emit_plan() {
  local plan_json
  plan_json=$(score_agents)

  if [[ ${DRY_RUN} -eq 1 ]]; then
    echo "${plan_json}"
    return
  fi

  echo "## DISPATCH PLAN — ${TODAY} (${DOW_NAME})"
  echo ""
  echo "_Generated by master_scheduler. The calling Claude session should dispatch each agent below in order, then run postflight._"
  echo ""

  # urgent inbox items first
  local urgent_count
  urgent_count=$(parse_inbox_urgent | wc -l)
  if [[ ${urgent_count} -gt 0 ]]; then
    echo "### URGENT inbox items (process FIRST, then continue)"
    parse_inbox_urgent | sed 's/^/- /'
    echo ""
  fi

  # selected agents
  echo "### Today's selected agents (in dispatch order)"
  echo ""
  echo "${plan_json}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for i, p in enumerate(data['selected'], 1):
    print(f'**Agent {i}: {p[\"agent\"]}** (score={p[\"score\"]})')
    print(f'  - prompt: scripts/agents/{p[\"agent\"]}.md')
    print(f'  - days since last run: {p[\"days_since_last_run\"]}')
    print(f'  - last outcome: {p[\"last_outcome\"]}')
    print()
"

  echo "### Total inbox queue depth: $(count_inbox_pending) pending"
  echo ""
  echo "### Pause flag: $([ -f \"${PAUSE_FLAG}\" ] && echo 'PRESENT' || echo 'absent')"
  echo ""
  echo "---"
  echo ""
  echo "After agent execution, postflight will be invoked with the union of files-touched and a generated commit message. STATUS.md will be updated with today's outcome."
}

if [[ ${INBOX_ONLY} -eq 1 ]]; then
  echo "## INBOX-ONLY MODE — ${TODAY}"
  echo ""
  parse_inbox_urgent
  exit 0
fi

emit_plan
