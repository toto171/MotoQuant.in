# Security policy

## Reporting a vulnerability

Email **motoquant@gmail.com** with the subject line `SECURITY:` followed by a
short description. Include steps to reproduce and, if you have one, a
suggested fix. Please do not open a public issue for anything that could be
exploited on the hosted service at motoquant.in before it is fixed.

You will get an acknowledgement within 72 hours. This is a volunteer-run
project; fixes for the hosted service are prioritised over fixes that only
affect self-hosted installs.

## Scope

- The hosted API (`motoquant-api.onrender.com`) and site (`motoquant.in`).
- The Python package (`motoquant/`), the MCP server (`motoquant/mcp_server.py`)
  and the CLI.

Out of scope: the discontinued desktop scaffold under `desktop/`, and
denial-of-service against the free-tier hosting.

## What is already in place

Signature-verified, fail-closed payment webhooks; scrypt password hashing;
JWT session tokens with a boot guard against the default secret when billing
is enforced; per-IP and per-client rate limits on the expensive routes; a
pinned dependency lockfile; a non-root Docker image; and a CI secret-scan
gate (`scripts/health_check.py --secrets-only`).
