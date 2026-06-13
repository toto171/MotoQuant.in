# MotoQuant Pro Desktop — Security Model

> Last hardened: 2026-06-13 (hosted-only re-architecture + dependency pin + Tauri lockdown).

## The one true security property

MotoQuant Pro desktop is a **thin, licensed client of the hosted MotoQuant API.**
All of the valuable intellectual property — the physics engine, the build
optimizer, the surrogate models, and the bike/part/tire catalog — lives
**server-side** and is **never bundled into the desktop binary**. The client
ships UI code and an HTTP client; it ships no engine, no catalog, and no secret.

**What this protects:** a copied, decompiled, or patched client is *worthless*
without a valid authenticated, licensed session against the operator's server,
because every simulation, optimization, and catalog read happens on the server
behind authentication. There is no offline mode that reveals the IP.

**What this does NOT claim — and never will:** this software is **not
"uncrackable"** and has **no "zero vulnerabilities" guarantee in the absolute.**
Those claims are false for any software. A determined attacker can always
inspect, modify, or replay the client. The honest, defensible properties we ship
are:

- **Zero KNOWN CVEs** in the dependency tree at release time (`npm audit` clean;
  `cargo audit` to be run by the operator — see `RELEASE.md`).
- **Least-privilege** Tauri capabilities + a locked-down Content Security Policy.
- **Signed + notarized** release binaries with a signed update channel.
- **Server-authoritative licensing** — the client cannot forge entitlement.

## Residual risk (read this)

A hosted-only licensed client does **not** protect against:

- **Client tampering / replay.** An authenticated user can capture their own
  bearer token and replay API calls outside the app. This is mitigated by
  short-lived access tokens, server-side rate limiting, and tier/quota
  enforcement — all of which live on the server, not here.
- **Credential phishing or shared accounts.** Account sharing is a business
  problem; device binding + revocation (server-side) limit but don't eliminate
  it.
- **Token theft via XSS-equivalent in the WebView.** The refresh token now
  lives in the **OS keychain** (macOS Keychain / Windows Credential Manager /
  Linux Secret Service) via the Rust `keychain_get/set/delete` commands
  (`src-tauri/src/lib.rs`) and `src/lib/secureStore.ts`, so it is no longer
  readable from WebView-accessible storage. The access token lives only in
  memory. We further reduce the surface with a strict CSP (`script-src 'self'`,
  no `unsafe-eval`) and no third-party script origins. Fallback: when no
  keychain backend is present (dev/browser, or a headless Linux box without a
  Secret Service provider) the refresh token degrades to `sessionStorage`
  (cleared on app close) so the session never hard-fails.
- **A compromised server.** All trust flows from the hosted API; its security
  (JWT secret hygiene, DB access, payment-webhook signature verification) is out
  of scope for this client and is the server's responsibility.

## Token storage (honest trade-off)

| Token | Storage | Survives app restart? | Rationale |
|---|---|---|---|
| Access token | React memory (a `useRef`) | No | Short-lived; never persisted to disk. |
| Refresh token | **OS keychain** (Keychain / Credential Manager / Secret Service) | Yes (encrypted by the OS) | Not WebView-readable. Falls back to `sessionStorage` only when no keychain backend is available. **Never** `localStorage` (plaintext on disk). |

The client performs a single silent refresh on a `401`; if refresh fails the
app drops to the login screen. The client **never** computes or caches any
license verdict locally — it only presents credentials and reacts to the
server's response (`401` → re-login, `402`/`403` → upgrade prompt).

## Secrets-in-bundle scan

The desktop tree ships **no secret of any kind.** The app authenticates at
runtime; there is no API key, token, password, or private key embedded in the
source or the built bundle. Verified at 2026-06-13:

```
grep -rniE 'api[_-]?key|secret|token=|bearer [a-z0-9]|ghp_|github_pat|sk-|
  jwt[_-]?secret|private[_-]?key|client[_-]?secret|-----BEGIN' \
  src/ src-tauri/ --include='*.ts' --include='*.tsx' --include='*.json' \
  --include='*.rs' --include='*.toml'
# → only type names, variable names, comments, and UI copy. No values.

grep -rnE 'ghp_…|github_pat_…|sk_(live|test)_…|AKIA…|-----BEGIN' src/ src-tauri/
# → empty.

grep -rnE 'ghp_…|sk_…|-----BEGIN|jwt[_-]?secret' dist/    # built bundle
# → empty.
```

The only `ANTHROPIC_API_KEY` reference (in `ChatBox.tsx`) is **UI copy** that
tells the *operator* to set that key **server-side** — it is not a value and is
never read by the client.

Re-run this scan before every release; it is the gate for "ships no secret."

## Tauri capability set (least privilege)

`src-tauri/capabilities/default.json` grants only:

| Permission | Why it's needed |
|---|---|
| `core:default` | Baseline IPC for the single `get_backend_url` command + window lifecycle. |
| `core:window:allow-start-dragging` | Custom title-bar drag region. |
| `shell:allow-open` | Open the billing/upgrade page (`motoquant.in/pricing`) in the user's default browser. **Not** `shell:default`, which also grants `allow-execute`/`allow-spawn`. |
| `updater:default` | Apply Ed25519-signed self-updates from the signed update channel. |

Removed in this pass: the broad **`shell:default`** grant (execute/spawn
capability the app never used). The hosted-only client spawns no processes.

## Content Security Policy

`tauri.conf.json → app.security.csp`:

```
default-src 'self' data: blob:;
script-src 'self';                         ← no 'unsafe-eval'
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
connect-src 'self' ipc: http://ipc.localhost https://motoquant-api.onrender.com;
img-src 'self' data: blob: https:;
```

- `connect-src` is locked to the Tauri IPC origins **and the hosted API only.**
  There is **no** `http://localhost:*` / `http://127.0.0.1:*` allowance in the
  production CSP (those existed only for the removed local sidecar).
- `'unsafe-eval'` was dropped from `script-src`.
- `withGlobalTauri` is `false` (the global `__TAURI__` object is not injected).
- Devtools are disabled in release builds (`windows_subsystem = "windows"` +
  Tauri's default release config); the WebView inspector is dev-only.

## Update channel integrity

Self-updates use the Tauri updater plugin with **Ed25519-signed** manifests.
The public key is embedded in `tauri.conf.json`; the **private key never enters
the repo** and is held by the operator. See `RELEASE.md` for keygen + signing.

> ⚠️ The `pubkey` currently in `tauri.conf.json` is a clearly-marked
> **PLACEHOLDER** (`PLACEHOLDER_DO_NOT_SHIP…`). A real key MUST be generated and
> pasted before any public release, or the updater will reject every manifest.
