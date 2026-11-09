# docs/ — index

MotoQuant is open source under the [MIT license](../LICENSE) — see also [../CONTRIBUTING.md](../CONTRIBUTING.md), [../SECURITY.md](../SECURITY.md) and [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md).

Start here if you're new: **[../AGENTS.md](../AGENTS.md)** (the working
contract) → **[ONBOARDING.md](ONBOARDING.md)** → **[ARCHITECTURE.md](ARCHITECTURE.md)**
→ [../CONTRIBUTING.md](../CONTRIBUTING.md). One-command tour: `make health`.

## Orientation (read first)
| Doc | What it covers |
|---|---|
| [../AGENTS.md](../AGENTS.md) | The working contract for any contributor (human or AI): the prime directive, the loop (`make check`/`make test`), the non-negotiable rules. |
| [ONBOARDING.md](ONBOARDING.md) | Day-one brief: what MotoQuant is, current state, read order. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map + data-flow diagram + "where do I change X?" |
| [INVARIANTS.md](INVARIANTS.md) | What must never break, and the automated gate that enforces each. |
| [KNOWN_TRAPS.md](KNOWN_TRAPS.md) | Bugs & gotchas that keep coming back — read before a big change. |
| [ROADMAP.md](ROADMAP.md) | Prioritized engineering roadmap and open work. |
| [FAQ.md](FAQ.md) | Common questions. |

## Subsystems
| Doc | What it covers |
|---|---|
| [CLIENT_COMPUTE.md](CLIENT_COMPUTE.md) | Running sims on the user's device: in-browser surrogate, Pyodide plan. |
| [CHAT_AGENT.md](CHAT_AGENT.md) | The agentic chat: tool-calling loop, tools, budgets. |
| [MCP.md](MCP.md) | Stdio MCP server: wire MotoQuant sims into Claude Code / Desktop. |
| [MOTOQUANT_LLM_PLAN.md](MOTOQUANT_LLM_PLAN.md) | LLM provider abstraction + roadmap. |
| [OBSERVABILITY.md](OBSERVABILITY.md) | Sentry wiring (env-gated). |
| [SCRAPING.md](SCRAPING.md) | Scrapling toolkit (dev-side): polite fetch tiers → validator gate. |
| [PARAMETER_AUDIT.txt](PARAMETER_AUDIT.txt) | Physics parameter inventory. |
| [adr/](adr/) | Architecture Decision Records (incl. [ADR-0006: open source under MIT](adr/0006-open-source-mit.md)). |
| [papers/](papers/) | Reference papers, project plans, validation reports. |

## Deploy & ops
| Doc | What it covers |
|---|---|
| [RENDER_MIGRATION.md](RENDER_MIGRATION.md) | API cutover to Render + rollback runbook. |
| [RELEASE.md](RELEASE.md) | Release process (desktop parts deprecated). |
| [INSTALL.md](INSTALL.md) | Install notes (desktop parts deprecated). |
| [RUFF_SETUP.md](RUFF_SETUP.md) | Lint/format config. |

## Automation & process (autonomous-ops — not needed for product dev)
| Doc | What it covers |
|---|---|
| [AUTONOMOUS_OPERATIONS_PLAYBOOK.md](AUTONOMOUS_OPERATIONS_PLAYBOOK.md) | The unattended-session orchestration system. |
| [DISPATCH_PROTOCOL.md](DISPATCH_PROTOCOL.md) | The `DISPATCH_INBOX/OUTBOX.md` async message queue. |
| [SCHEDULING.md](SCHEDULING.md) | Cron/scheduler layout. |
| [TASKS_MASTER_LIST.md](TASKS_MASTER_LIST.md) · [TEAM_SCALING.md](TEAM_SCALING.md) · [SEO_STRATEGY.md](SEO_STRATEGY.md) · [phase_plan.md](phase_plan.md) · [motoquant_toolkit.md](motoquant_toolkit.md) | Planning / strategy notes. |
| [changelog/](changelog/) | Release notes + fix summaries. |
| [mockups/](mockups/) | Design mockups. |
