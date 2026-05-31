# Claude Feature Scan — 2026-05-31

**Agent:** `claude-feature-monitor` (A13)
**Scan type:** Delta scan (7 days since 2026-05-24 baseline)
**Data sources:** live WebFetch against platform.claude.com (models overview, migration guide, deprecations), anthropic.com/news, code.claude.com/docs
**Data-source limitations:** none — all 5 target URLs returned (after one expected redirect from docs.claude.com → platform.claude.com).

---

## Headline

**Claude Opus 4.8 was released 2026-05-28** (T-3 days). It is a drop-in upgrade for Opus 4.7 with no breaking API changes. The MotoQuant project's harness currently routes deep work to Opus 4.7; switching to 4.8 is opportunistic (Opus 4.7 stays Active until 2027-04-16) but zero-cost since no model IDs are pinned anywhere in the codebase.

Everything else is incremental: Anthropic raised $65B Series H, opened a Milan office, acquired Stainless (SDK tooling), and shipped a handful of new Claude Code surfaces (Dispatch, `--teleport`, WinGet install). None require action.

The June 15, 2026 dual retirement of `claude-opus-4-20250514` and `claude-sonnet-4-20250514` (T-15 days) remains zero-exposure for MotoQuant — re-verified via `grep` across `scripts/`, `docs/`, `motoquant/`, `web/`, `desktop/`. Only references are documentation/snapshot files.

---

## Deltas since 2026-05-24

### Model deltas

| Item | Delta | Action |
|---|---|---|
| **Claude Opus 4.8** | NEW — released 2026-05-28. Same $5/$25 pricing, 1M context, 128k max output, Jan 2026 cutoff. Adds mid-conversation system messages, lowers prompt-cache minimum to 1024 tokens, makes 1M context the default with no beta header. | Queue [opportunistic] INSTRUCTION (below). |
| **Claude Opus 4.7** | Moved from "primary" to "Legacy" tier in the models overview. Still Active until 2027-04-16. | No-op; migration is opportunistic. |
| **Claude Sonnet 4.6** | Unchanged. | No-op. |
| **Claude Haiku 4.5** | Unchanged. | No-op. |
| **June 15 dual retirement** | Unchanged from baseline — `claude-opus-4-20250514`, `claude-sonnet-4-20250514`. Zero MotoQuant exposure re-verified. | No action. |

### Opus 4.8 capability deep-dive

Per the migration guide and the "What's new" doc:

1. **Mid-conversation system messages** — `role: "system"` is now legal in `messages` (subject to placement rules) after a user turn. On Opus 4.7 and earlier it returns 400. Useful for the `scripts/master_scheduler.sh` → agent prompt-injection chain where today's day-of-week and market-signal context get rebuilt into the prompt every dispatch. With 4.8, those can be appended as system messages, preserving prompt-cache hits on earlier turns.
2. **Lower prompt-cache minimum (1024 tokens, was higher on 4.7)** — most agent prompts in `scripts/agents/*.md` are between 500–1500 tokens. Several that previously couldn't cache will now create cache entries on 4.8. Marginal but free win.
3. **1M context window is the default — no beta header required.** Cosmetic for our use case (we're already on 1M via the `[1m]` model variant), but simplifies any future SDK-level integration.
4. **Effort levels recalibrated:** `medium` allows somewhat more thinking, `high` somewhat less, `xhigh` substantially more. Default is `high` on all surfaces including Claude Code. **If we migrate, do not tune effort until we've re-baselined at the same level.** This is the trap to avoid.
5. **No breaking changes vs Opus 4.7.** Same constraint on `temperature`/`top_p`/`top_k` (400 error if set), same tokenizer.

### Claude Code surface deltas

| Item | New since last scan? | Relevance |
|---|---|---|
| **Dispatch** (phone → Desktop session routing) | Yes (observed for first time) | HIGH conceptual — interesting overlap with MotoQuant's `DISPATCH_INBOX.md` naming. User on 8h internship + async-only is exactly the target persona. Test before adopting; may supplement file polling. |
| **`claude --teleport`** | Yes | LOW — niche, single-environment user. |
| **WinGet installer** | Yes | LOW — install convenience. |
| **GitLab CI/CD support** | Yes | LOW — MotoQuant is on GitHub. |
| **`/claude-api migrate` skill** | Yes (first observation) | LOW until Phase 6 — auto-migrates Anthropic SDK code between model versions. Worth knowing when MotoQuant adds an Anthropic-backed `/api/chat` path. |

### Anthropic news (chronological)

- **2026-05-28** — Opus 4.8 release + $65B Series H.
- **2026-05-27** — Milan office.
- **2026-05-26** — Korea / Seoul leadership appointment.
- **2026-05-22** — Project Glasswing update (still invitation-only, still not us).
- **2026-05-19** — KPMG strategic alliance.
- **2026-05-18** — **Stainless acquisition** — they build OpenAPI-to-SDK generators. Likely improves the cadence/quality of `anthropic-sdk-python` (relevant when MotoQuant adds an Anthropic-backed chat endpoint in Phase 6).
- **2026-05-14** — PwC expanded partnership.

### Pricing / deprecation deltas

No pricing changes. No new deprecation announcements. The June 15 retirement of Opus 4 / Sonnet 4 (2025-05-14 snapshot versions) remains the only active deprecation, and MotoQuant has zero exposure.

---

## Recommendations & queued actions

### Queued to DISPATCH_INBOX.md

**One INSTRUCTION block queued (opportunistic, low effort):**

> Switch the default Opus model in the harness routing convention from `claude-opus-4-7` to `claude-opus-4-8`. Zero code edits (no IDs pinned in repo). Update `CLAUDE.md` MODEL SELECTION table to reference Opus 4.8 as the architecture/design model. If the harness is unaware of `claude-opus-4-8`, fall back to `claude-opus-4-7` (still Active until 2027-04-16). Quality-gate before promoting: run one architecture-question session on 4.8 and confirm answer quality is at-or-above the 4.7 baseline.

### Not queued (logged for next month)

- **Dispatch native primitive** — interesting overlap with MotoQuant's file-based dispatch protocol. Worth a one-off UX test from the user's phone, but not high enough ROI to queue urgently. Re-evaluate when the user explicitly asks for a phone-to-task surface.
- **`/api/chat` Anthropic migration** — Phase 6 work; gated on the auth + subscription rails landing.
- **Stainless impact on `anthropic-sdk-python`** — passive watch item; no action until we depend on the SDK.

### Not adopted (rejected per policy)

- **GitLab CI/CD support** — MotoQuant is on GitHub; no migration value.
- **`--teleport` flag** — niche.
- **WinGet install** — install convenience only.

---

## Verification notes

- `grep -r 'claude-opus-4-20250514\|claude-sonnet-4-20250514' scripts/ docs/ motoquant/ web/ desktop/` → only doc/snapshot hits.
- `grep -r 'claude-opus-4-7\|claude-opus-4-6'` → only doc/snapshot hits.
- All 5 source URLs returned successfully (one expected docs.claude.com → platform.claude.com redirect).
- Snapshot JSON validates with `python3 -c "import json; json.load(...)"`.

## Next scan

Target date: **2026-06-21** (3 weeks).
Priority checks for that scan:
1. Verify zero `claude-opus-4-20250514` / `claude-sonnet-4-20250514` references AFTER the June 15 retirement (T+6 days).
2. Check if Sonnet 4.7 or Haiku 5 announced (cadence: ~2-month minor bumps).
3. Re-evaluate Dispatch primitive vs `DISPATCH_INBOX.md` after any user feedback.
4. Confirm `/claude-api migrate` skill GA status for the Phase 6 chat path.
5. Scan for new MCP servers (Railway, Vercel, Notion).
