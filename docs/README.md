# docs/ — index

Start here if you're new: **[../AGENTS.md](../AGENTS.md)** (the working
contract) → **[ONBOARDING.md](ONBOARDING.md)** → **[ARCHITECTURE.md](ARCHITECTURE.md)**
→ [../CONTRIBUTING.md](../CONTRIBUTING.md). One-command tour: `make health`.

MotoQuant is free and open source under the Apache License 2.0
([../LICENSE](../LICENSE), [../NOTICE](../NOTICE)).

## Orientation (read first)
| Doc | What it covers |
|---|---|
| [../AGENTS.md](../AGENTS.md) | The working contract for any contributor (human or AI): the prime directive, the loop (`make check`/`make test`), the non-negotiable rules. |
| [ONBOARDING.md](ONBOARDING.md) | Day-one brief: what MotoQuant is, current state, read order, good first issues. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map, data-flow diagram, and "where do I change X?" |
| [INVARIANTS.md](INVARIANTS.md) | What must never break, and the automated gate that enforces each. |
| [KNOWN_TRAPS.md](KNOWN_TRAPS.md) | Bugs and gotchas that keep coming back. Read before a big change. |
| [ROADMAP.md](ROADMAP.md) | Prioritized engineering roadmap: open-source launch, accuracy, scaling blockers. |
| [FAQ.md](FAQ.md) | Common questions. |

## Community
| Doc | What it covers |
|---|---|
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Setup, testing, code style, PR workflow; how contributions are licensed. |
| [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Contributor Covenant 2.1. |
| [../SECURITY.md](../SECURITY.md) | Reporting vulnerabilities privately; scope. |

## Subsystems
| Doc | What it covers |
|---|---|
| [CHAT_AGENT.md](CHAT_AGENT.md) | The agentic chat: tool-calling loop, tools, budgets, per-IP fuses. |
| [MCP.md](MCP.md) | Stdio MCP server: use MotoQuant sims from Claude Code / Desktop or any MCP client. |
| [RUST_CORE.md](RUST_CORE.md) | Optional Rust physics core (PyO3 + wasm32), bit-identical to the Python reference. |
| [CLIENT_COMPUTE.md](CLIENT_COMPUTE.md) | What runs in the browser vs on the server, and the parity proofs. |
| [MOTOQUANT_LLM_PLAN.md](MOTOQUANT_LLM_PLAN.md) | LLM provider abstraction + roadmap. |
| [OBSERVABILITY.md](OBSERVABILITY.md) | Sentry wiring (env-gated) and opt-in PostHog forwarding. |
| [SCRAPING.md](SCRAPING.md) | Scrapling toolkit (dev-side): polite fetch tiers → validator gate. |
| [PARAMETER_AUDIT.txt](PARAMETER_AUDIT.txt) | Physics parameter inventory. |
| [adr/](adr/) | Architecture Decision Records (settled decisions; read before relitigating). |
| [papers/](papers/) | Reference papers, project plans, validation reports. |

## Deploy & ops
| Doc | What it covers |
|---|---|
| [SELF_HOSTING.md](SELF_HOSTING.md) | Run the API + web locally, on Render/Vercel or any Docker host; every environment variable. |
| [RENDER_MIGRATION.md](RENDER_MIGRATION.md) | Historical Railway → Render cutover + rollback runbook. |
| [RUFF_SETUP.md](RUFF_SETUP.md) | Lint/format config. |

## Planning notes and history
| Doc | What it covers |
|---|---|
| [TASKS_MASTER_LIST.md](TASKS_MASTER_LIST.md) · [phase_plan.md](phase_plan.md) · [motoquant_toolkit.md](motoquant_toolkit.md) | Older planning / tooling notes (dated; trust the dates). |
| [AUTONOMOUS_OPERATIONS_PLAYBOOK.md](AUTONOMOUS_OPERATIONS_PLAYBOOK.md) | Internal maintainer workflow: the (paused) unattended-session system. Not needed for development. |
| [changelog/](changelog/) | Release notes + fix summaries. |
| [mockups/](mockups/) | Design mockups. |
| [archive/](archive/) | Retired documents: the old commercial plans and payments runbook, desktop install/release docs, internal dispatch/scheduling notes. |
