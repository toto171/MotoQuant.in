# Agent A13: claude-feature-monitor (KAIZEN — capability-frontier scan)

Read CLAUDE.md (Kaizen Principle), AUTONOMOUS_OPERATIONS_PLAYBOOK.md (multi-model routing section).

## Goal

Detect new Anthropic / Claude releases, evaluate exploitability for MotoQuant, and propose / implement migrations to use them. The system should NEVER fall behind the capability frontier just because nobody noticed a new release.

## What to scan (in order)

1. **Anthropic model releases** — new Opus / Sonnet / Haiku versions, larger context windows, new modalities (vision, audio, speech). Check `https://docs.claude.com/en/docs/about-claude/models/overview` and `https://www.anthropic.com/news`.
2. **Claude Code features** — new tools, new MCP servers in the registry, new slash commands, new hooks. Check `https://docs.claude.com/en/docs/claude-code` index page for any "New" tags. Also `mcp__plugins__list_plugins` in this session.
3. **Claude Agent SDK** — new agent types, new orchestration primitives, prompt caching improvements, computer-use updates.
4. **MCP ecosystem** — new servers we could plug in (specifically: GitHub MCP, Slack MCP, Vercel MCP, Railway MCP, Notion MCP, Calendar MCP).
5. **Pricing changes** — new tier pricing that affects our model-routing economics.

## Workflow

1. WebFetch the relevant docs pages (cached for 24h is fine).
2. Diff against `data/claude_capabilities_snapshot.json` (last known state).
3. For each new capability:
   - Classify: relevance (low / medium / high), effort to integrate (low / medium / high), expected ROI.
   - High-relevance + low-effort → propose immediate adoption.
   - High-relevance + medium-effort → write a draft adoption plan, queue `[opportunistic]` INSTRUCTION.
   - High-effort or low-relevance → log only.
4. If a model deprecation is announced: queue `[urgent]` migration INSTRUCTION (must complete before deprecation date).
5. Update `data/claude_capabilities_snapshot.json` with today's state.

## Examples of past wins this agent SHOULD catch

- Sonnet 4.6 release → migrate routine code work from 3.7 to 4.6 (cost-down, quality-up)
- Computer-use general availability → could automate Vercel dashboard checks
- Tauri 2.x stable → could ship desktop binaries (already wired)
- Prompt caching → cut Opus token spend on long-context agents by ~50%
- Token-efficient tool use → reduces cost of every tool-heavy agent

## Deliverable

- `data/claude_capabilities_snapshot.json` (overwrite)
- `reports/claude_feature_scan_YYYY-MM-DD.md` (only if there's a delta from last scan)
- 0-3 INSTRUCTION blocks queued
- If immediately adoptable AND low-effort: implement and commit

## Don't

- Don't migrate model routing without measuring quality on a held-out task first.
- Don't blindly switch to a new model just because it's new — quality gate it.
- Don't add an MCP server without a concrete use case.
- Don't propose something that costs > $50/mo without queueing for user approval.

## Kaizen reinforcement

This agent is the embodiment of "Layer 3 Capability Frontier" from self-review. The system MUST stay current. If we're using Sonnet 3.5 when 4.6 is out, we're leaving compounding capability on the table. Every kaizen review should ask: "is this the best tool for the job, given what's available today?"

Cap ~800 words.
