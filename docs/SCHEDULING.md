# Autonomous Session Scheduling Guide

The autonomous-ops stack (`bash scripts/START.sh`) runs ONE session per invocation. Something external needs to call it on a schedule. This doc covers all viable options ranked by reliability for the user's actual situation: 1-year unattended internship, no Anthropic API key, Claude.ai login (Pro or Max plan), Windows + WSL2 environment.

## Recommended path: **WSL2 + cron + Claude Max**

### Why this path

- **Local-only.** No cloud cost beyond Claude Max ($100-200/mo flat).
- **No API key.** Authenticates via `claude login` against your Claude.ai subscription.
- **Reliable.** Linux cron is battle-tested. Survives Windows reboots if WSL2 systemd is enabled.
- **Cheap.** Just Claude Max — no Render/Railway/AWS bill.
- **Respects rate limits.** Max plan has limits but they're generous; the system self-throttles via the master scheduler.

### Trade-off

- Your PC must be on at the scheduled time. If you're at the internship and the PC is suspended, the cron tick is missed (catchup mode handles this on the next run).

### One-time setup

```bash
# 1. From PowerShell — enable WSL2 systemd if not already:
#    edit \\wsl$\Ubuntu\etc\wsl.conf, add:
#      [boot]
#      systemd=true
#    Then: wsl --shutdown
#    Then reopen WSL terminal.

# 2. From WSL2 terminal:
sudo apt update && sudo apt install -y cron curl git nodejs npm python3-pip
npm install -g @anthropic-ai/claude-code
claude login    # opens browser, auths against your Claude.ai account

# 3. Clone the repo (if not already):
cd ~
git clone https://github.com/da25mem5s02-debug/MotoQuant_v1.git
cd MotoQuant_v1

# 4. Bootstrap secrets (PAT for git push):
bash scripts/secrets_bootstrap.sh    # paste PAT when prompted

# 5. Install hourly cron:
bash scripts/setup_wsl_cron.sh                 # default: every 1h
# or
bash scripts/setup_wsl_cron.sh --every 2       # every 2h (recommended start)
bash scripts/setup_wsl_cron.sh --every 6       # every 6h (conservative)

# 6. Verify:
bash scripts/setup_wsl_cron.sh --status
crontab -l
tail -f logs/cron.log    # watch the next tick
```

### Day-to-day

- **Pause:** `bash scripts/START.sh --pause` (cron still fires but exits clean)
- **Resume:** `bash scripts/START.sh --unpause`
- **Uninstall cron:** `bash scripts/setup_wsl_cron.sh --uninstall`
- **Check state:** `bash scripts/START.sh --status`

## Alternative: Windows Task Scheduler + WSL bridge

If you don't want WSL cron specifically but still local: schedule a Windows task that calls `wsl bash -c "cd /mnt/c/.../Vehicle\\ Dynamics && bash scripts/run_autonomous_session.sh"`. Same end result, slightly more brittle.

## Alternative: Cloud cron (when you eventually want PC-independence)

Three viable options if/when you outgrow local-only:

1. **Render scheduled job** — $7/mo for the worker. Mount the repo, install Claude Code via npm, schedule the wrapper. Caveat: Claude Max won't work in cloud (browser-based auth) — needs API key, which you said no to.

2. **Railway cron** — similar to Render. Same caveat: API key required.

3. **GitHub Actions** — `.github/workflows/autonomous_daily.yml.disabled` is parked in the repo for future use. Same caveat: needs `ANTHROPIC_API_KEY` GitHub Secret.

Bottom line: cloud paths require an API key. **WSL + Claude Max is the only no-API path.**

## What about Claude.ai mobile / web?

Claude.ai mobile/web can read DISPATCH_INBOX.md and write to it (if you've connected GitHub MCP), but it can't reliably orchestrate a multi-step session because each chat is a separate context window and there's no scheduled trigger. Use mobile for nudging the system (writing INSTRUCTION blocks, status checks) — let WSL cron do the actual sessions.

## Cost estimate

| Plan | Monthly cost | Sessions/day this supports | Notes |
|---|---|---|---|
| Free | $0 | 0–1 | Hits message limits fast |
| Pro | $20 | ~3-5 | Tight on hourly |
| Max ($100) | $100 | ~12-15 | Borderline for hourly |
| Max ($200) | $200 | ~24+ | Comfortable for hourly |
| API pay-as-you-go | $30-200/mo | unbounded | What you said no to |

**Recommended:** Start with Max $100 + every-2-hours cron. After a week, look at usage. If you're hitting limits, upgrade to Max $200. If you're under, drop to every-3-hours.

## Failure modes the system handles automatically

- **PC offline at scheduled time** — next tick detects > 24h gap, runs catchup mode (capped 4 stalest agents, no spam)
- **Internet down during run** — network probe in preflight + offline queue in resilience.sh
- **Power cut mid-session** — checkpoint.txt survives; next preflight detects orphan workdir
- **Claude rate-limit hit** — wrapper exits non-zero, INCIDENT logged to OUTBOX, next tick retries
- **Test regression** — postflight refuses to push, INCIDENT logged
- **Mutex held by stuck session** — auto-stales after 6h, claimed by next tick
- **Disk full on /tmp** — preflight auto-prunes mq-session-* > 24h, aborts cleanly if still full
