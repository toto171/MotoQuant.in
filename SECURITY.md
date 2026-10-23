# Security Policy

## Supported versions

MotoQuant ships continuously from `main`; there are no versioned releases or
maintained branches. Security fixes land on **`main`** and reach the hosted
instance (<https://www.motoquant.in>) on the next deploy. If you self-host,
update to the latest `main`.

| Version | Supported |
|---|---|
| `main` (latest commit) | Yes |
| Older commits, forks, self-hosted copies that are not up to date | No. Update to `main`. |

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report it privately with **GitHub Security Advisories**:

1. Go to the repository's **Security** tab:
   <https://github.com/da25mem5s02-debug/MotoQuant_v1/security>
2. Choose **Report a vulnerability** (or open
   <https://github.com/da25mem5s02-debug/MotoQuant_v1/security/advisories/new>).
3. Describe the issue, how to reproduce it, and the impact you expect. A
   minimal proof of concept helps. Please do not include real user data.

If private reporting is unavailable (for example while the repository is
still private), open a GitHub issue that says only *"security report — please
contact me"*, with no details, and a maintainer will arrange a private
channel.

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

- The FastAPI backend in `motoquant/`, including the API routes, optional
  accounts (magic link, password, JWT sessions), the chat agent and its tools
  (for example SSRF through `web_fetch` / `web_search`), file uploads
  (Dragy/dyno CSVs), rate limiting, and SQL handling.
- The Next.js web app in `web/`, including XSS, open redirects, and leaks of
  tokens or user data.
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
  (for example, running publicly without `MOTOQUANT_DEPLOYED`/`JWT_SECRET` on
  a non-Render host, or with several untrusted proxies in front of the API).
- Simulation accuracy disagreements. Those are bugs, not vulnerabilities;
  please open a normal issue with your benchmark source.
- Vulnerabilities in third-party services (Render, Vercel, LLM providers,
  Resend). Report those to the vendor.

## Hardening already in place

So that a report can focus on what is new: SQL is parameterized; the chat
agent's `web_fetch` re-checks the SSRF guard on every redirect hop; per-IP
rate limits key on the rightmost `X-Forwarded-For` hop; magic-link tokens are
never echoed in responses on a deployed host; a deployed host never signs
sessions with the public development JWT secret (it uses an ephemeral secret
if none is configured). [docs/INVARIANTS.md](docs/INVARIANTS.md) lists the
gates that enforce each of these.
