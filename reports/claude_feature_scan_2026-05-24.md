# Claude Feature Scan — 2026-05-24 (bootstrap baseline)

**Agent:** claude-feature-monitor (A13)
**Run type:** First run since agent inception. No prior `data/claude_capabilities_snapshot.json` existed; this run establishes the baseline.
**Scan method:** Live WebFetch against Anthropic-operated docs (platform.claude.com, code.claude.com, anthropic.com/news). All fetches succeeded; no egress blocking observed.

---

## Bottom line

**MotoQuant's production model routing is on the current capability frontier.** No urgent migration required. The previously-feared June 15, 2026 retirement of `claude-opus-4-20250514` / `claude-sonnet-4-20250514` does NOT affect MotoQuant — production routing uses `claude-opus-4-7` and `claude-sonnet-4-6`, both active with retirement not sooner than 2027.

Five adoptable opportunities identified, ranked by ROI:

1. **Skills system** (`/en/skills`) — package `motoquant.skill` as native (already on toolkit shortlist).
2. **Routines** (`/en/routines`) — Anthropic-managed cron could replace `scripts/master_scheduler.sh` if host availability becomes a problem.
3. **Sub-agents primitive** (`/en/sub-agents`) — native equivalent of the cleanup-rotation 7-agent pattern.
4. **Background agents** (`/en/agent-view`) — native equivalent of the April-24 7-stream parallel-Cowork pattern.
5. **Sonnet 4.6's 1M context window** — was 200k when playbook was written; now matches Opus 4.7. The "long-context summarisation → Sonnet 200k" routing rule in the playbook is now obsolete (Sonnet handles 1M natively).

---

## Frontier state vs MotoQuant's routing

| Slot | MotoQuant uses | Frontier model | Status |
|---|---|---|---|
| Deep work | `claude-opus-4-7` | `claude-opus-4-7` | ✓ current; retirement not before 2027-04-16 |
| Code | `claude-sonnet-4-6` | `claude-sonnet-4-6` | ✓ current; retirement not before 2027-02-17 |
| Fast lookup | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | ✓ current; retirement not before 2026-10-15 |
| User /api/chat | gemini-flash-2.5 | (non-Anthropic) | unchanged |

**Pricing (per million tokens):** Opus 4.7 $5 in / $25 out · Sonnet 4.6 $3 in / $15 out · Haiku 4.5 $1 in / $5 out. Identical to the playbook's assumed pricing.

**Notable model-level deltas since the playbook was authored:**
- Sonnet 4.6 context window 200k → **1M tokens** (matches Opus 4.7). Sonnet 4.6 + extended thinking now covers the "long-context summarisation" tier that the playbook routes to a non-existent "Sonnet 200k".
- Opus 4.7 uses a new tokenizer (~555k words per 1M tokens vs ~750k words for Sonnet's tokenizer). Cost-per-equivalent-doc differs slightly between Opus and Sonnet; not large enough to retune routing.
- Batch API supports up to **300k output tokens** via the `output-300k-2026-03-24` beta header on Opus 4.7 / 4.6 / Sonnet 4.6. Useful if MotoQuant ever generates full bike-spec catalog docs in one shot.

---

## Capability-frontier delta (what's new in Claude Code since playbook)

### High-relevance, low-effort (adopt)

**Skills (`/en/skills`)** — Already on the toolkit shortlist as "MotoQuant skill for Claude — teach Claude bike spec schema + glossary." Native Skills system makes this a packaging task vs custom prompt engineering. **Recommendation:** queue as one [opportunistic] INSTRUCTION (see below).

**Sub-agents primitive (`/en/sub-agents`)** — `scripts/run_cleanup_subagents.sh` dispatches 7 cleanup subagents in parallel via shell. Native sub-agents could replace this with a single agent invocation and cleaner result merging. **Recommendation:** evaluate at next monthly cleanup-rotation Sunday (last Sunday of June 2026).

**Background agents (`/en/agent-view`)** — direct replacement for the April-24 7-stream parallel orchestration via /tmp clones documented in CLAUDE.md. Cleaner primitive. **Recommendation:** evaluate next time a multi-stream session is needed.

### High-relevance, medium-effort (track, don't act yet)

**Routines (`/en/routines`)** — Anthropic-managed scheduled agent runs. Survives local power-off. Triggerable from web/Desktop/CLI/GitHub events. Could replace `scripts/master_scheduler.sh` local cron entirely. **Trade-off:** loses access to local files; would need API surface for everything currently filesystem-based. **Recommendation:** monitor resilience.sh real-world failures over the next month before deciding.

**Channels (`/en/channels`)** — Telegram / Discord / iMessage / webhook events → session. DISPATCH_INBOX.md is currently file-polling; Channels would give true async push from phone during the user's 8h internship. **Recommendation:** worth a spike but not urgent; the file-polling pattern works.

### Low-relevance / not yet

**Agent SDK (`/en/agent-sdk/overview`)** — full control over orchestration, tool access. Could underpin the 12 production agents in `scripts/agents/*`. Current prompt-template approach works; re-evaluate when agent count crosses 25.

**Code review native (`/en/code-review`)** — automatic PR review. Free quality gate. Worth adopting after pytest-regressions baseline (toolkit shortlist #1) is in place so reviewer has a firm contract to enforce.

**Slack (`@Claude` in Slack)** — user is solo + on Indian internship, no team Slack. Logged only.

**Claude Design** — Anthropic Labs product for visual work. Relevance to MotoQuant: pitch decks, marketing one-pagers. Effort: low. Track for Phase 6 launch prep.

**Claude Mythos Preview (Project Glasswing)** — invitation-only defensive cybersecurity research. Not relevant.

---

## Deprecation alert (June 15, 2026 — 22 days out)

`claude-opus-4-20250514` and `claude-sonnet-4-20250514` retire June 15, 2026. **MotoQuant has zero exposure** — production routing uses `claude-opus-4-7` and `claude-sonnet-4-6`. Grep verifies no references to the dated model IDs anywhere in `scripts/`, `docs/`, or `motoquant/`. No action required.

If the next scan finds any reference creep, this becomes an `[urgent]` migration INSTRUCTION. For now it doesn't.

---

## Recent Anthropic announcements summary (Feb–May 2026)

| Date | Item | MotoQuant relevance |
|---|---|---|
| Feb 4 2026 | Claude remains ad-free | Brand alignment note; no action |
| Apr 7 2026 | Project Glasswing | Invitation-only security research; not relevant |
| Apr 14 2026 | Sonnet 4 / Opus 4 deprecation announced | Zero exposure (verified) |
| Apr 16 2026 | Claude Opus 4.7 | Already adopted |
| Apr 17 2026 | Claude Design (Labs) | Track for Phase 6 marketing decks |
| May 6 2026 | Higher usage limits + SpaceX compute partnership | May enable wider concurrency in 7-subagent cleanup-rotation |
| May 13 2026 | Claude for Small Business | Track for Phase 6 commercial launch if MotoQuant scales |

---

## INSTRUCTION queued

Per the prompt's "0–3 INSTRUCTIONs; only one if truly high-impact + low-effort" gate, queuing exactly **one** opportunistic block to DISPATCH_INBOX.md. The toolkit-shortlist `motoquant.skill` line item is the natural fit — already on the priority list, already classified as low-effort, native primitive now formally documented.

(Not queued: any model-migration block, because MotoQuant has no exposure; any Routines / Channels / Background agents block, because they need a spike + measurement before being worth committing.)

---

## Next scan

**Target:** 2026-06-21 (4-week cadence).
**Priority checks for next run:**
1. Verify zero references to retired `claude-opus-4-20250514` / `claude-sonnet-4-20250514` post June 15 retirement.
2. Check if Sonnet 4.7 / Opus 4.8 are announced (rough cadence: ~2-month minor bumps observed since Opus 4.5 → 4.6 → 4.7).
3. Re-scan Claude Design GA status.
4. Re-evaluate Routines vs `scripts/master_scheduler.sh` after resilience.sh real-world track record.
5. Scan for new MCP servers relevant to Railway / Vercel / Notion product-priorities flow.

---

*Snapshot file: `data/claude_capabilities_snapshot.json` (overwritten as 2026-05-24 baseline).*
