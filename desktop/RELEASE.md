# MotoQuant Pro Desktop — Release & Code-Signing Runbook

> Goal: produce **signed, notarized, integrity-verifiable** installers and a
> **signed auto-update channel**. Every step that needs the operator's
> certificates / accounts / private keys is marked **[OPERATOR]** — those cannot
> be done in CI or in a sandbox.

This is a Tauri 2 app. The frontend is built with Vite; the installers are built
by `tauri build`. There is **no Python sidecar** to bundle (hosted-only client).

---

## 0. Prerequisites (one-time, [OPERATOR])

- Rust stable toolchain (`rustup`), Node 22 / npm 10.
- Platform toolchains: Windows → MSVC + WiX/NSIS (Tauri pulls these); macOS →
  Xcode CLT; Linux → standard build-essential + webkit2gtk dev packages.
- `cargo install cargo-audit` (for the dependency advisory gate, step 5).

---

## 1. Generate the updater signing keypair  **[OPERATOR]**

The auto-updater verifies update manifests with an **Ed25519** signature.

```bash
# Generates a private key (keep SECRET) + prints the public key.
npx @tauri-apps/cli signer generate -w ~/.tauri/motoquant-updater.key
```

- Paste the printed **public** key into `src-tauri/tauri.conf.json` →
  `plugins.updater.pubkey`, replacing the `PLACEHOLDER_DO_NOT_SHIP…` value.
- The **private** key + its password go into CI secrets only:
  - `TAURI_SIGNING_PRIVATE_KEY` (the key file contents)
  - `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- **Never** commit the private key. It signs every update your users install.

---

## 2. Windows code-signing (Authenticode)  **[OPERATOR]**

Use an **EV** (or OV) code-signing certificate. EV avoids SmartScreen warnings.

In `src-tauri/tauri.conf.json → bundle.windows`:

```jsonc
"windows": {
  "certificateThumbprint": "<SHA1 THUMBPRINT OF YOUR CERT IN THE WINDOWS STORE>",
  "digestAlgorithm": "sha256",
  "timestampUrl": "http://timestamp.digicert.com"
}
```

- `certificateThumbprint` is currently `null` — fill it from your cert.
- For an HSM/token-backed EV cert, configure `signtool` per your CA's
  instructions; Tauri shells out to `signtool` using the thumbprint.
- Timestamping (already set) keeps signatures valid after the cert expires.

---

## 3. macOS code-signing + notarization  **[OPERATOR]**

Requires an Apple Developer account ($99/yr) and a **Developer ID Application**
certificate.

In `src-tauri/tauri.conf.json → bundle.macOS`:

```jsonc
"macOS": {
  "signingIdentity": "Developer ID Application: Your Name (TEAMID)",
  "providerShortName": "<YOUR_PROVIDER_SHORT_NAME>",
  "entitlements": "src-tauri/entitlements.plist"   // if you add hardened-runtime entitlements
}
```

Notarization env (set in CI secrets, consumed by `tauri build`):

```bash
export APPLE_ID="you@apple.example"
export APPLE_PASSWORD="<app-specific-password>"   # appleid.apple.com → App-Specific Passwords
export APPLE_TEAM_ID="<TEAMID>"
# tauri build will sign, submit to notarytool, and staple the ticket.
```

---

## 4. Build the installers

```bash
cd desktop
npm ci
# Point the build at the production API (optional; default is already hosted):
export MOTOQUANT_API_URL="https://motoquant-api.onrender.com"
npm run tauri:build      # → src-tauri/target/release/bundle/{msi,nsis,dmg,appimage,deb}
```

With the signing config + env from steps 1–3 in place, the produced bundles are
signed (Windows + macOS) and notarized (macOS). The updater artifacts (`*.sig`)
are produced when the updater plugin + signing key are configured.

---

## 5. Dependency advisory gate  **[OPERATOR — needs cargo]**

JS side is already clean (`npm audit` → 0 vulnerabilities, pinned). Run the Rust
gate before tagging:

```bash
cd desktop/src-tauri
cargo update          # prune crates removed in the hosted-only rewrite
                      # (tokio + anyhow are no longer dependencies)
cargo audit           # fail the release on any RUSTSEC advisory
cargo check           # confirms the hosted-only lib.rs/Cargo.toml compile
cargo tauri build     # full build (only on the target OS)
```

Known item to verify with `cargo audit`: the GTK stack on Linux pulls
`glib 0.18.5` transitively (RUSTSEC-2024-0429, low severity, Linux-only). Bump
the GTK/`glib` line if `cargo audit` flags it and a compatible patch exists;
otherwise document it as a non-reachable transitive in the release notes.

---

## 6. Release-integrity checksums

Publish a **signed** SHA-256 checksum file alongside the installers so users can
verify authenticity independently of the OS signature.

```bash
cd src-tauri/target/release/bundle
# Generate checksums for every shipped artifact:
find . -type f \( -name '*.msi' -o -name '*.exe' -o -name '*.dmg' \
  -o -name '*.AppImage' -o -name '*.deb' \) -exec sha256sum {} \; \
  | sed 's#\./##' > SHA256SUMS.txt

# [OPERATOR] sign the checksum file (GPG detached signature):
gpg --armor --detach-sign --output SHA256SUMS.txt.asc SHA256SUMS.txt
```

Upload `SHA256SUMS.txt` + `SHA256SUMS.txt.asc` to the GitHub Release. Document
the operator's GPG public key fingerprint on `motoquant.in` so users can verify:

```bash
gpg --verify SHA256SUMS.txt.asc SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt
```

---

## 7. Updater manifest

The updater endpoint in `tauri.conf.json` is:

```
https://motoquant.in/desktop/updates/{{target}}/{{arch}}/{{current_version}}
```

For each release, publish a `latest.json` per the Tauri updater schema, with the
per-platform download URLs and the **Ed25519 signatures** emitted by step 4. The
client verifies each signature against the embedded public key before applying.

---

## Pre-tag checklist

- [ ] `npm audit` → 0 vulnerabilities (`cd desktop`).
- [ ] `cargo audit` → clean (or documented non-reachable transitives).
- [ ] `cargo check` + `cargo tauri build` succeed on each target OS.
- [ ] Secrets scan clean (see `SECURITY.md`) — ships no secret.
- [ ] `tauri.conf.json` updater `pubkey` is the REAL key (not the placeholder).
- [ ] Windows `certificateThumbprint` + macOS `signingIdentity` filled in.
- [ ] Real designer icons in `src-tauri/icons/` (placeholders flagged at v0.x).
- [ ] `SHA256SUMS.txt` + `.asc` signature published with the release.
