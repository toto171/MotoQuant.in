#!/usr/bin/env bash
# run_cleanup_subagents.sh — Driver for the 7 Wize-AI-style cleanup subagents.
#
# Each subagent is a markdown prompt template in scripts/subagents/0N_*.md.
# This driver has two modes:
#
#   1. CLAUDE-SESSION mode (default): the script prints the prompts to stdout
#      with a "## DISPATCH N" separator. The Claude session running this script
#      then reads stdout, dispatches each prompt as an `Agent` tool call in
#      parallel (single message, multiple tool uses), waits for all to return,
#      consolidates the reports.
#
#   2. STANDALONE mode (--standalone): print prompts only, no orchestration.
#      Useful from a real terminal — paste each prompt into a Claude chat
#      manually and gather the reports yourself.
#
# In both modes, the expected output is 7 markdown reports in reports/
# named cleanup_subagent_<N>_<topic>.md, plus a consolidated summary at
# reports/cleanup_consolidated_<YYYY-MM-DD>.md.
#
# Usage:
#   bash scripts/run_cleanup_subagents.sh                 # all 7
#   bash scripts/run_cleanup_subagents.sh 1 3 7            # subset
#   bash scripts/run_cleanup_subagents.sh --standalone     # print only
#   bash scripts/run_cleanup_subagents.sh --consolidate    # only consolidate existing reports
#   bash scripts/run_cleanup_subagents.sh --help

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SUBAGENT_DIR="${SCRIPT_DIR}/subagents"
readonly REPORT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/reports"

readonly SUBAGENTS=(
  "01_deduplication.md"
  "02_type_consolidation.md"
  "03_dead_code.md"
  "04_circular_dependencies.md"
  "05_type_strengthening.md"
  "06_error_handling.md"
  "07_deprecated_and_slop.md"
)

readonly TOPICS=(
  "dedup"
  "types"
  "dead"
  "cycles"
  "types"
  "errors"
  "slop"
)

log()   { printf "\033[36m[subagents]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[subagents FATAL]\033[0m %s\n" "$*" >&2; exit 1; }

usage() {
  grep -E '^# ' "$0" | sed 's/^# \?//'
}

# ─── Arg parsing ─────────────────────────────────────────────────────────
STANDALONE=0
CONSOLIDATE_ONLY=0
SELECTED_INDICES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --standalone)  STANDALONE=1; shift ;;
    --consolidate) CONSOLIDATE_ONLY=1; shift ;;
    --help|-h)     usage; exit 0 ;;
    [1-7])         SELECTED_INDICES+=("$1"); shift ;;
    *)             fatal "unknown arg: $1" ;;
  esac
done

# Default: run all 7
if [[ ${#SELECTED_INDICES[@]} -eq 0 ]]; then
  SELECTED_INDICES=(1 2 3 4 5 6 7)
fi

mkdir -p "${REPORT_DIR}"

# ─── Consolidation step ──────────────────────────────────────────────────
consolidate() {
  local out="${REPORT_DIR}/cleanup_consolidated_$(date -I).md"
  log "consolidating reports → ${out}"

  {
    echo "# Cleanup subagent consolidated report — $(date -I)"
    echo ""
    echo "Pass kicked off via \`scripts/run_cleanup_subagents.sh\`. Each subagent ran read-only and wrote a single markdown file."
    echo ""
    echo "## Subagents that ran this pass"
    echo ""
    for i in "${SELECTED_INDICES[@]}"; do
      local topic="${TOPICS[$((i-1))]}"
      local rpt="${REPORT_DIR}/cleanup_subagent_${i}_${topic}.md"
      if [[ -f "${rpt}" ]]; then
        local lines; lines=$(wc -l < "${rpt}")
        echo "- Subagent ${i} (${topic}) — ${lines} lines — \`reports/cleanup_subagent_${i}_${topic}.md\`"
      else
        echo "- Subagent ${i} (${topic}) — **MISSING REPORT**"
      fi
    done
    echo ""
    echo "## Consolidated findings"
    echo ""
    for i in "${SELECTED_INDICES[@]}"; do
      local topic="${TOPICS[$((i-1))]}"
      local rpt="${REPORT_DIR}/cleanup_subagent_${i}_${topic}.md"
      if [[ -f "${rpt}" ]]; then
        echo ""
        echo "---"
        echo ""
        cat "${rpt}"
      fi
    done
    echo ""
    echo "---"
    echo ""
    echo "## Recommended action policy"
    echo ""
    echo "- **High-confidence findings:** apply if the change is mechanical and reversible (file deletes, dedup of test boilerplate, orphan removal). Skip if it touches physics, catalog, or tests."
    echo "- **Medium-confidence:** write an \`## INSTRUCTION\` block to \`DISPATCH_INBOX.md\` for the user to triage."
    echo "- **False positives:** ignore."
    echo ""
    echo "NEVER apply a subagent's findings blindly. They're proposals; the main session must verify against the codebase."
  } > "${out}"

  log "consolidated: ${out} ($(wc -l < "${out}") lines)"
}

if [[ ${CONSOLIDATE_ONLY} -eq 1 ]]; then
  consolidate
  exit 0
fi

# ─── Print dispatch prompts ──────────────────────────────────────────────
log "preparing ${#SELECTED_INDICES[@]} subagent prompts"
log "  mode: $([ ${STANDALONE} -eq 1 ] && echo standalone || echo claude-session)"
log "  reports → ${REPORT_DIR}"

for i in "${SELECTED_INDICES[@]}"; do
  local_topic="${TOPICS[$((i-1))]}"
  prompt_file="${SUBAGENT_DIR}/${SUBAGENTS[$((i-1))]}"

  if [[ ! -f "${prompt_file}" ]]; then
    fatal "missing subagent prompt: ${prompt_file}"
  fi

  echo ""
  echo "## DISPATCH ${i} — ${local_topic}"
  echo "**prompt-file:** ${prompt_file}"
  echo "**expected-output:** reports/cleanup_subagent_${i}_${local_topic}.md"
  echo ""
  echo "--- BEGIN PROMPT ---"
  cat "${prompt_file}"
  echo ""
  echo "--- END PROMPT ---"
  echo ""
done

if [[ ${STANDALONE} -eq 1 ]]; then
  log "standalone mode — paste each prompt into a Claude chat, save reports manually."
  log "When all reports are present, re-run with --consolidate."
else
  log ""
  log "Claude-session mode — the calling session should now:"
  log "  1. Dispatch each prompt above as an Agent() tool call (parallel, single message)."
  log "  2. Wait for all to return."
  log "  3. Re-run this script with --consolidate to merge the reports."
fi
