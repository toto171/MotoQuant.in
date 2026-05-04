#!/usr/bin/env bash
# mobile_dispatch_handler.sh — parse `## MOBILE — YYYY-MM-DD — HH:MM` blocks
# in DISPATCH_INBOX.md and expand the shorthand DSL into proper INSTRUCTION
# blocks (or apply directly if the verb is a system-level action).
#
# Idempotent: a MOBILE block, once processed, gets renamed to
# `## MOBILE-PROCESSED — YYYY-MM-DD — HH:MM` so it isn't re-fired.
#
# Shorthand verbs (one per line in the MOBILE block):
#   ship                                      = process inbox + commit + push
#   pause                                     = creates paused.flag
#   unpause                                   = removes paused.flag
#   rerun yesterday                           = re-execute yesterday's primary task
#   rerun <agent>                             = run <agent> immediately
#   add bike <make> <model> <year>            = queue [urgent] catalog INSTRUCTION
#   investigate <topic>                       = queue [research] INSTRUCTION
#   +1 <agent>                                = bump agent weight +10
#   -1 <agent>                                = cut agent weight -10
#   status                                    = post STATUS.md to OUTBOX
#   incident <text>                           = raise incident manually
#
# Usage:
#   bash scripts/mobile_dispatch_handler.sh
# or sourced from preflight (after inbox parse, before scheduler).

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO="${MQ_REPO:-${SCRIPT_DIR}/..}"
readonly INBOX="${REPO}/DISPATCH_INBOX.md"
readonly OUTBOX="${REPO}/DISPATCH_OUTBOX.md"
readonly WEIGHTS="${REPO}/scripts/scheduler_weights.json"
readonly PAUSE_FLAG="${MOTOQUANT_SECRETS_DIR:-/tmp/.motoquant-secrets}/paused.flag"

log()   { printf "\033[36m[mobile]\033[0m %s\n" "$*" >&2; }
warn()  { printf "\033[33m[mobile WARN]\033[0m %s\n" "$*" >&2; }

[[ ! -f "${INBOX}" ]] && { log "no INBOX present, nothing to do"; exit 0; }

# Find all unprocessed MOBILE blocks
mobile_blocks=$(awk '
  /^## MOBILE — [0-9]{4}-[0-9]{2}-[0-9]{2}/ { p=1; print NR": "$0; next }
  /^## MOBILE-PROCESSED/ { p=0 }
  /^## (INSTRUCTION|DONE|DEFERRED|RESPONDED)/ { p=0 }
  p { print NR": "$0 }
' "${INBOX}")

if [[ -z "${mobile_blocks}" ]]; then
  log "no MOBILE blocks pending"
  exit 0
fi

log "found pending MOBILE blocks"

# We do this in Python because bash regex + multi-line state machine = misery
python3 - <<'PYEOF'
import re, json, os, sys, datetime, subprocess
from pathlib import Path

def _np(p):
    """Cross-platform path normalize: MINGW /tmp/ → Windows via cygpath."""
    if not p:
        return p
    if os.name == "nt" and str(p).startswith("/"):
        try:
            out = subprocess.check_output(["cygpath", "-w", str(p)], text=True).strip()
            return out if out else str(p)
        except Exception:
            return str(p)
    return str(p)

inbox_path  = Path(_np(os.environ["INBOX"]))
outbox_path = Path(_np(os.environ["OUTBOX"]))
weights_path = Path(_np(os.environ["WEIGHTS"]))
pause_flag  = Path(_np(os.environ["PAUSE_FLAG"]))
repo = Path(_np(os.environ.get("REPO", ".")))

text = inbox_path.read_text()

# Split into blocks. We're looking for ## MOBILE — date — time blocks.
mobile_re = re.compile(
    r"^## MOBILE — (\d{4}-\d{2}-\d{2}) — (\d{2}:\d{2})\s*\n((?:(?!^## ).*\n)*)",
    re.MULTILINE
)

def queue_instruction(severity_tag: str, summary: str, body: str = "") -> str:
    """Return a properly formatted INSTRUCTION block as a string."""
    today = datetime.date.today().isoformat()
    return (
        f"\n## INSTRUCTION — {today} — {summary}\n"
        f"{severity_tag}\n\n"
        f"_(expanded from mobile dispatch)_\n\n"
        f"{body}\n"
    )

def append_outbox(line: str):
    outbox_path.write_text(outbox_path.read_text() + line)

def adjust_weight(agent: str, delta: int):
    if not weights_path.exists():
        return f"  ! weights file missing — skipped {agent} ±{delta}"
    w = json.loads(weights_path.read_text())
    if agent not in w["agents"]:
        return f"  ! unknown agent: {agent}"
    w["agents"][agent]["base"] = max(0, w["agents"][agent]["base"] + delta)
    weights_path.write_text(json.dumps(w, indent=2))
    return f"  weight: {agent} → {w['agents'][agent]['base']}"

processed = []
new_instructions = []
log_lines = []

for m in mobile_re.finditer(text):
    date_str, time_str, body = m.group(1), m.group(2), m.group(3)
    log_lines.append(f"processing MOBILE @ {date_str} {time_str}:")
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Parse verb
        if line == "ship":
            log_lines.append("  ship → no-op (postflight always pushes)")
        elif line == "pause":
            pause_flag.parent.mkdir(parents=True, exist_ok=True)
            pause_flag.write_text(f"paused at {datetime.datetime.now().isoformat()}\n")
            log_lines.append(f"  pause → flag created at {pause_flag}")
        elif line == "unpause":
            if pause_flag.exists():
                pause_flag.unlink()
                log_lines.append("  unpause → flag removed")
            else:
                log_lines.append("  unpause → no flag was set")
        elif line.startswith("rerun "):
            target = line[6:].strip()
            new_instructions.append(queue_instruction(
                "[urgent]",
                f"rerun {target}",
                f"Mobile dispatch requested re-run of `{target}`."
            ))
            log_lines.append(f"  rerun {target} → queued [urgent]")
        elif line.startswith("add bike "):
            spec = line[9:].strip()
            new_instructions.append(queue_instruction(
                "[urgent]",
                f"add bike: {spec}",
                f"Mobile dispatch requested catalog addition: `{spec}`. catalog-expansion agent should research + verify spec before adding."
            ))
            log_lines.append(f"  add bike {spec} → queued [urgent]")
        elif line.startswith("investigate "):
            topic = line[12:].strip()
            new_instructions.append(queue_instruction(
                "[research]",
                f"investigate: {topic}",
                f"Mobile dispatch requested research: `{topic}`. Investigate, write findings to outbox, do NOT act yet."
            ))
            log_lines.append(f"  investigate {topic} → queued [research]")
        elif line.startswith("+1 "):
            agent = line[3:].strip()
            log_lines.append(adjust_weight(agent, 10))
        elif line.startswith("-1 "):
            agent = line[3:].strip()
            log_lines.append(adjust_weight(agent, -10))
        elif line == "status":
            new_instructions.append(queue_instruction(
                "[urgent]",
                "post current STATUS.md to OUTBOX",
                "Mobile dispatch requested status snapshot. Echo current STATUS.md key sections into next OUTBOX entry."
            ))
            log_lines.append("  status → queued")
        elif line.startswith("incident "):
            txt = line[9:].strip()
            append_outbox(f"\n## INCIDENT — manual — {datetime.datetime.now().isoformat()}\n{txt}\n")
            log_lines.append(f"  incident → posted to OUTBOX: {txt[:60]}...")
        else:
            log_lines.append(f"  ? unknown verb: {line!r}")
    processed.append((m.start(), m.end(), date_str, time_str))

# Rewrite inbox: rename processed blocks + append new instructions
if processed:
    # Walk in reverse so indices stay valid
    new_text = text
    for start, end, d, t in reversed(processed):
        block = new_text[start:end]
        renamed = block.replace(
            f"## MOBILE — {d} — {t}",
            f"## MOBILE-PROCESSED — {d} — {t}",
            1
        )
        new_text = new_text[:start] + renamed + new_text[end:]
    # Append new INSTRUCTION blocks at the end of the QUEUE section
    queue_marker = "## INSTRUCTIONS QUEUE"
    if queue_marker in new_text and new_instructions:
        # Insert AFTER the queue header but BEFORE next ---
        idx = new_text.index(queue_marker)
        next_div = new_text.find("\n---\n", idx)
        if next_div < 0:
            next_div = len(new_text)
        new_text = new_text[:next_div] + "\n" + "\n".join(new_instructions) + new_text[next_div:]
    inbox_path.write_text(new_text)

print("\n".join(log_lines))
print(f"\n→ {len(processed)} MOBILE block(s) processed, {len(new_instructions)} INSTRUCTION(s) queued")
PYEOF

log "mobile dispatch processing complete"
