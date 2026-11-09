# Security Policy

## Supported versions

Only the current `main` branch is supported. The hosted site
([motoquant.in](https://motoquant.in)) always runs `main`; there are no
long-lived release branches.

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

1. **Preferred:** open a private security advisory on the repository:
   <https://github.com/toto171/MotoQuant.in/security/advisories/new>
2. **Or** email **support@motoquant.in** with the subject line
   `SECURITY: <short summary>`.

Include what you found, how to reproduce it (a request/response or a minimal
script is ideal), and the impact you see. You will get an acknowledgement
within a few days. Please give us reasonable time to ship a fix before any
public disclosure; we are happy to credit you in the fix unless you prefer
otherwise.

## Scope

In scope: the FastAPI backend (`motoquant/api.py` and friends), the Next.js
site in `web/`, the MCP server, and anything in the repository that handles
user input (uploads, chat tools, account endpoints).

Out of scope: findings that need a compromised device, volumetric DoS against
the free-tier hosting, and issues in third-party services we depend on (report
those upstream).

## Secrets

Never commit API keys, tokens or `.env` files. CI runs a secret scan
(`make health` runs the same check locally). If you find a leaked credential
in the repository or its history, report it as above.
