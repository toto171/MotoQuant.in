# Security Policy

## Supported versions

MotoQuant ships continuously from `main`. The version number (2.0.0, in
`motoquant/__init__.py`) names the release line; there are no maintained
release branches. Security fixes land on **`main`** and reach the hosted
instance (<https://www.motoquant.in>) on the next deploy. If you self-host,
update to the latest `main`.

| Version | Supported |
|---|---|
| `main` (latest commit) | Yes |
| Older commits, forks, self-hosted copies that are not up to date | No. Update to `main`. |

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report it privately, by either route:

- **GitHub private reporting.** Open the repository's **Security** tab
  (<https://github.com/toto171/MotoQuant.in/security>) and choose **Report a
  vulnerability**, or go straight to
  <https://github.com/toto171/MotoQuant.in/security/advisories/new>.
- **Email** <motoquant@gmail.com> with the subject "Security report".

Describe the issue, how to reproduce it and the impact you expect. A minimal
proof of concept helps. Please do not include real user data.

What to expect:

- We will acknowledge the report within **7 days**.
- We will send an assessment and a planned fix timeline after triage.
- We will credit you in the advisory and the fix commit, unless you prefer
  not to be named.
- This is a volunteer-run, free project. There is **no bug bounty**.

Please give us reasonable time to ship a fix before you disclose publicly. We
aim for 90 days or less.

## Scope

In scope:

- The FastAPI backend in `motoquant/`, including the API routes, the chat
  agent and its tools (for example SSRF through `web_fetch` / `web_search`),
  file uploads (Dragy/dyno CSVs), rate limiting, and SQL handling.
- The Next.js web app in `web/`, including XSS, open redirects, and anything
  a crafted timeslip link can make the site display or do.
- The CLI and the MCP server (`motoquant/mcp_server.py`), where untrusted
  input is involved.
- Deployment defaults shipped in this repo (`Dockerfile`,
  `docker-entrypoint.sh`, `render.yaml`, `vercel.json`).
- Secrets committed to the repository.

Out of scope:

- Volumetric denial of service against the hosted instance. Per-IP rate
  limits are a cost fuse, not DDoS protection; edge protection belongs to
  whoever hosts a deployment.
- Findings that need a compromised device, browser or hosting account.
- Self-hosted deployments that ignore [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md)
  (for example, running publicly with several untrusted proxies in front of
  the API).
- Simulation accuracy disagreements. Those are bugs, not vulnerabilities;
  please open a normal issue with your benchmark source.
- Vulnerabilities in third-party services (Render, Vercel, LLM providers,
  OpenWeatherMap). Report those to the vendor.

## Hardening already in place

So that a report can focus on what is new: SQL is parameterized; the chat
agent's `web_fetch` re-checks the SSRF guard on every redirect hop; per-IP
rate limits trust `X-Forwarded-For` only for the configured proxy hops
(`MOTOQUANT_TRUSTED_PROXY_HOPS`); there are no accounts, and no route stores
visitor input that other visitors can see (the POST routes are a tested
allow-list). [docs/INVARIANTS.md](docs/INVARIANTS.md) lists the gates that
enforce each of these.
