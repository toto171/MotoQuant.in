#!/usr/bin/env bash
# anti_slop_check.sh — fast pre-commit scan for AI-tell phrases and
# unverified-claim markers in staged content. Called by postflight as a
# hard gate before push.
#
# Exit codes:
#   0 — clean, push allowed
#   1 — slop or unverified claims found, push blocked
#   2 — usage error

set -euo pipefail

# Files to scan (staged in this commit)
SCAN_FILES="${MQ_FILES_TOUCHED:-}"
# Or pass them as args
[[ -z "${SCAN_FILES}" && $# -gt 0 ]] && SCAN_FILES="$*"

if [[ -z "${SCAN_FILES}" ]]; then
  echo "anti_slop_check: no files to scan (skipping)"
  exit 0
fi

# Only scan content-y files. Skip code (.py, .ts, .js source) and JSON / locks.
filter_content_files() {
  for f in $1; do
    case "${f}" in
      *.md|*.mdx|*.txt|*.html|*/page.js|*/about/page.js|*/blog/**/page.js)
        echo "${f}" ;;
    esac
  done
}

CONTENT_FILES=$(filter_content_files "${SCAN_FILES}")

if [[ -z "${CONTENT_FILES}" ]]; then
  echo "anti_slop_check: no content files in scan set (skipping)"
  exit 0
fi

# AI-slop phrase library — case-insensitive grep
AI_SLOP_PATTERNS=(
  "delve into"
  "navigating the complex"
  "navigate the complex"
  "in today's fast-paced"
  "in this ever-evolving"
  "ever-evolving landscape"
  "robust solution"
  "leverage"
  "synergy"
  "synergize"
  "paradigm shift"
  "it's worth noting that"
  "it goes without saying"
  "tapestry"
  "kaleidoscope of"
  "symphony of"
  "embark on a journey"
  "elevate your"
  "unleash the"
  "unleash your"
  "harness the power"
  "in the realm of"
  "the world of"
  "stands as a testament"
  "a beacon of"
  "comprehensive approach"
  "holistic approach"
  "rich tapestry"
  "stands at the forefront"
  "play a pivotal role"
  "navigate the world"
  "navigate the realm"
  "play a crucial role"
  "play a key role"
  "underscore the importance"
  "noteworthy"
  "transformative"
)

VIOLATIONS=()

for f in ${CONTENT_FILES}; do
  if [[ ! -f "${f}" ]]; then
    continue
  fi
  for pat in "${AI_SLOP_PATTERNS[@]}"; do
    # Use grep -in for case-insensitive line-numbered matches
    while IFS=: read -r linenum line; do
      [[ -z "${linenum}" ]] && continue
      VIOLATIONS+=("${f}:${linenum}: '${pat}' → ${line:0:80}")
    done < <(grep -in "${pat}" "${f}" 2>/dev/null || true)
  done

  # Em-dash overuse: count em-dashes (— and --) in the file
  if [[ "${f}" == *.md || "${f}" == *.mdx ]]; then
    em_count=$(grep -oE '—|--' "${f}" 2>/dev/null | wc -l || echo 0)
    word_count=$(wc -w < "${f}" || echo 1)
    # > 1 em-dash per 100 words is excessive
    if [[ ${word_count} -gt 200 && $((em_count * 100 / word_count)) -gt 1 ]]; then
      VIOLATIONS+=("${f}: em-dash overuse (${em_count} em-dashes / ${word_count} words)")
    fi
  fi
done

if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
  echo "anti_slop_check: clean (${CONTENT_FILES} scanned)"
  exit 0
fi

echo "═══════════════════════════════════════════════════════════════"
echo "anti_slop_check: ${#VIOLATIONS[@]} violation(s) found"
echo "═══════════════════════════════════════════════════════════════"
for v in "${VIOLATIONS[@]}"; do
  echo "  ${v}"
done
echo
echo "Push BLOCKED. Rewrite the flagged lines without AI-slop tells."
echo "If a flagged phrase is genuinely the right word in context (rare),"
echo "add a one-line comment explaining why and re-run."

# Write to OUTBOX for visibility
if [[ -n "${MQ_REPO:-}" ]]; then
  outbox="${MQ_REPO}/DISPATCH_OUTBOX.md"
  {
    echo ""
    echo "### ALERT — anti-slop check blocked push — $(date -Iseconds)"
    echo "${#VIOLATIONS[@]} violations:"
    for v in "${VIOLATIONS[@]}"; do
      echo "- \`${v}\`"
    done
  } >> "${outbox}" 2>/dev/null || true
fi

exit 1
