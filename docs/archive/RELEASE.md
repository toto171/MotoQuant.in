> **Archived 2026-10-23: desktop app deleted** — the `desktop/` tree and its `release.yml` workflow were removed (ADR-0005, ADR-0006). Historical record only.

> **DISCONTINUED (July 2026).** The native desktop app was scrapped — the
> hosted web app at motoquant.in is the product. This document is retained
> for historical reference only; no desktop releases will be cut.

# MotoQuant Pro — Release Runbook

> This document is for developers cutting a release. For end-user install
> instructions see [INSTALL.md](INSTALL.md).

---

## Prerequisites

You need these tools installed locally **once**:

```bash
# Rust + Tauri CLI
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install tauri-cli --version "^2"

# Node 20 (use nvm or https://nodejs.org)
node --version   # should be 20.x

# Python 3.11
python3 --version

# GitHub CLI (for release management)
gh --version
```

---

## One-time setup: generate the Ed25519 updater keypair

Run this **once** per repository. The private key stays secret; the public key
goes in the codebase.

```bash
cargo tauri signer generate -w ~/.tauri/motoquant-updater.key
```

This prints two things:

```
Private key written to ~/.tauri/motoquant-updater.key
Public key: <base64 string>
```

**Step 1 — store the private key in GitHub Secrets:**

```
Settings → Secrets and variables → Actions → New repository secret

  TAURI_SIGNING_PRIVATE_KEY         ← content of ~/.tauri/motoquant-updater.key
  TAURI_SIGNING_PRIVATE_KEY_PASSWORD ← passphrase you chose (empty string if none)
```

**Step 2 — paste the public key into `tauri.conf.json`:**

```json
// desktop/src-tauri/tauri.conf.json
"plugins": {
  "updater": {
    "pubkey": "<PASTE PUBLIC KEY HERE>",
    ...
  }
}
```

Commit and push. The public key is safe to commit; it only verifies, not signs.

---

## Ship a release (tag and push)

```bash
# 1. Make sure main is green
gh run list --branch main --limit 5

# 2. Bump the version in both files (keep them in sync)
#    desktop/package.json  →  "version": "0.2.0"
#    desktop/src-tauri/Cargo.toml  →  version = "0.2.0"
#    desktop/src-tauri/tauri.conf.json  →  "version": "0.2.0"
#    (or use bump-my-version / cargo-release to automate)

# 3. Commit the bump
git add desktop/package.json desktop/src-tauri/Cargo.toml desktop/src-tauri/tauri.conf.json
git commit -m "chore: bump to v0.2.0"
git push origin main

# 4. Tag and push — this triggers the Release workflow
git tag v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

GitHub Actions (`.github/workflows/release.yml`) will then:

1. Build the PyInstaller sidecar on all 4 platforms (Linux x64, macOS arm64, macOS x64, Windows x64).
2. Run a smoke test against `/api/health` on each platform.
3. Run `tauri build` for each platform, producing installers + `.sig` files.
4. Upload all artifacts to a **draft** GitHub Release.
5. Generate `latest.json` (the Tauri updater manifest) and upload it.
6. Publish the draft (remove the draft flag) automatically.

Wait for the workflow to finish (~30–40 min). You can watch it at:

```
https://github.com/da25mem5s02-debug/MotoQuant_v1/actions
```

---

## Code-signing (optional but strongly recommended)

Without signing, users on Windows see a SmartScreen warning and macOS users
must right-click → Open. Signing eliminates those warnings.

### Windows — EV Code Signing Certificate

**Cost:** ~$400/year (Sectigo, DigiCert, or Certum are common choices).
EV (Extended Validation) certs suppress SmartScreen immediately; OV certs
require building up reputation over ~30 days.

**Steps:**

1. Purchase an EV cert from Sectigo (https://sectigo.com/ssl-certificates-tls/code-signing).
2. Complete identity verification (~3–5 business days).
3. Export the cert as a `.pfx` file (contains private key, requires password).
4. Base64-encode it:

   ```bash
   base64 -i motoquant_cert.pfx | tr -d '\n' > cert_b64.txt
   ```

5. Add two GitHub Secrets:

   ```
   WINDOWS_CERTIFICATE          ← content of cert_b64.txt
   WINDOWS_CERTIFICATE_PASSWORD ← pfx export password
   ```

6. The `release.yml` `Import Windows certificate` step picks these up automatically.

**Without a cert:** the release workflow still produces unsigned installers.
Document the SmartScreen caveat in INSTALL.md (already done).

### macOS — Apple Developer ID

**Cost:** $99/year (Apple Developer Program: https://developer.apple.com/programs/).

**Steps:**

1. Enroll in the Apple Developer Program.
2. In Xcode / Keychain, generate a **Developer ID Application** certificate.
3. Export as `.p12` (private key included) with a password.
4. Base64-encode it:

   ```bash
   base64 -i motoquant_dev_id.p12 | tr -d '\n' > cert_b64.txt
   ```

5. Generate an app-specific password at https://appleid.apple.com for notarisation.

6. Add GitHub Secrets:

   ```
   APPLE_CERTIFICATE          ← base64 .p12
   APPLE_CERTIFICATE_PASSWORD ← .p12 export password
   APPLE_ID                   ← your Apple ID email
   APPLE_ID_PASSWORD          ← app-specific password (NOT your Apple ID password)
   APPLE_TEAM_ID              ← 10-character team ID (from developer.apple.com/account)
   ```

7. The `release.yml` `Import macOS certificate` step picks these up.
   Tauri's build step uses them for `codesign` and `xcrun notarytool`.

**Without a cert:** macOS users must right-click → Open on first launch.
Document this in INSTALL.md (already done).

---

## Rollback

If a release has a critical bug:

```bash
# 1. Delete the release (keeps the tag, removes the artifacts)
gh release delete v0.2.0 --yes

# 2. Delete the tag (forces clients to stay on the previous version)
git push origin :v0.2.0
git tag -d v0.2.0

# 3. Re-tag a known-good commit and re-release
git tag v0.2.1 <good-sha> -m "Hotfix: <description>"
git push origin v0.2.1
```

If the release is already installed by users, the updater will serve them the
last valid `latest.json` pointing to the previous version, so no action is
needed on the client side.

---

## Secrets reference

| Secret | Required | Purpose |
|--------|----------|---------|
| `TAURI_SIGNING_PRIVATE_KEY` | **Yes** (updater) | Ed25519 private key for updater `.sig` files |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | **Yes** (updater) | Passphrase for the private key (empty string OK) |
| `WINDOWS_CERTIFICATE` | No | Base64 PFX for Windows code-signing |
| `WINDOWS_CERTIFICATE_PASSWORD` | No | PFX password |
| `APPLE_CERTIFICATE` | No | Base64 .p12 for macOS Developer ID |
| `APPLE_CERTIFICATE_PASSWORD` | No | .p12 password |
| `APPLE_ID` | No | Apple ID email for notarisation |
| `APPLE_ID_PASSWORD` | No | App-specific password for notarisation |
| `APPLE_TEAM_ID` | No | 10-char Apple team ID |
| `VERCEL_TOKEN` | Yes (deploy.yml) | Vercel deploy token (web frontend) |
| `VERCEL_ORG_ID` | Yes (deploy.yml) | Vercel org ID |
| `VERCEL_PROJECT_ID` | Yes (deploy.yml) | Vercel project ID |

---

## FAQ

**Q: The release workflow failed on the macOS arm64 runner — can I re-run just that job?**

Yes. Go to the failed workflow run → click the three-dot menu on the failing
job → Re-run failed jobs. The other platform artifacts are preserved from the
first run.

**Q: How do I ship a pre-release / RC?**

Tag with a pre-release suffix: `v1.0.0-rc.1`. GitHub Actions will create a
pre-release (GitHub automatically detects the `-` in the version). The Tauri
updater will only offer it to users if their `tauri.conf.json` allows
pre-releases (currently set to stable-only).

**Q: The `latest.json` signature for darwin-x86_64 is empty.**

The CI currently generates the x64 dmg signature only when the sig file is
present in the release. If the macOS-13 runner produced a `.dmg.sig` file,
re-run the `update-manifest` job after verifying all assets are uploaded.

**Q: Binary size target?**

The spec's `excludes` list (torch, sklearn, SALib, matplotlib) targets a
sidecar binary under 80 MB. Actual sizes observed in CI:
- Linux: ~65 MB
- macOS: ~70 MB
- Windows: ~75 MB

If the binary exceeds 80 MB, check `pyinstaller --debug all` output for
unexpectedly included packages.
