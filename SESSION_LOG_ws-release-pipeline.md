# Session Log — ws/release-pipeline

**Date:** 2026-04-24  
**Branch:** `ws/release-pipeline`  
**Model:** claude-sonnet-4-6 (Cowork mode)

---

## What was built this session

### 1. Placeholder icons — `desktop/src-tauri/icons/`

All icon files regenerated with MotoQuant branding: orange `MQ` lettering on
carbon-black rounded rectangle, with a thin orange speed-line accent bar.
Files produced via Python / Pillow:

| File | Size | Notes |
|------|------|-------|
| `32x32.png` | 32×32 | Windows taskbar / Linux panel |
| `128x128.png` | 128×128 | Linux desktop |
| `128x128@2x.png` | **256×256** | macOS Retina (Tauri expects 256 px for @2x) |
| `icon.png` | 1024×1024 | Base / macOS App Store |
| `StoreLogo.png` | 150×150 | Windows MSIX Store listing |
| `icon.ico` | multi-res (16–256 px) | Windows installer + taskbar |
| `icon.icns` | multi-res (16–512 px) | macOS, written as binary ICNS container |

**⚠ REPLACE BEFORE 1.0 LAUNCH** — these are code-quality placeholders.
Commission a real icon from a designer (monogram "MQ", speedometer needle,
or stylized tach arc) at ≥1024×1024 and re-run Tauri's `tauri icon icon.png`
to regenerate all derivative sizes automatically.

---

### 2. Tauri updater plugin wired — `desktop/src-tauri/`

Files modified:

- **`tauri.conf.json`** — added `bundle.externalBin`, `bundle.windows`
  (code-signing stubs), `bundle.macOS` (signing stubs), and `plugins.updater`
  (Ed25519 pubkey placeholder + GitHub Releases endpoint).

- **`Cargo.toml`** — added `tauri-plugin-updater = "2"`.

- **`capabilities/default.json`** — added `updater:default`,
  `updater:allow-check`, `updater:allow-download-and-install`.

- **`src/lib.rs`** — added `.plugin(tauri_plugin_updater::Builder::new().build())`.

**⚠ ACTION REQUIRED** — the pubkey in `tauri.conf.json` is a placeholder string.
Before the first release, generate a real keypair:

```bash
cargo tauri signer generate -w ~/.tauri/motoquant-updater.key
```

Paste the printed public key into `tauri.conf.json` under `plugins.updater.pubkey`,
and add the private key to GitHub Secrets as `TAURI_SIGNING_PRIVATE_KEY`.

---

### 3. `desktop/src-tauri/bin/` directory created

Empty `bin/` directory with a self-documenting `.gitkeep` that lists the four
expected binary names. The gitignore rule `*.exe` might need a `!bin/*.exe`
exception — check before first release build.

---

### 4. `.github/workflows/release.yml` — NEW

Full four-platform release pipeline. Triggers on `v*` tags.

Per-platform matrix: `ubuntu-22.04` / `macos-14` (arm64) / `macos-13` (x64) / `windows-latest`.

Steps per runner:
1. Checkout
2. Python 3.11 + install motoquant + sidecar deps
3. Seed `motoquant.db` (so PyInstaller can bundle it)
4. PyInstaller sidecar build → smoke test → stage into `bin/`
5. Node 20 + Rust stable + swatinem rust-cache
6. Optional Windows / macOS code-signing certificate import
7. `tauri build --target <triple> --bundles <targets>`
8. `softprops/action-gh-release` upload (draft mode)

Final job `update-manifest`:
- Runs after all four platform jobs complete
- Downloads `.sig` files from the draft release
- Generates `latest.json` (Tauri updater manifest)
- Uploads to release
- Publishes draft → live

**Known limitation:** The `darwin-x86_64` signature slot in `latest.json` is
empty in the current manifest script because multiple `.dmg.sig` files land
in the release and the `gh` JQ filter is a best-effort name match. Tighten
the filter once you know the actual Tauri output filename pattern for that target.

---

### 5. `.github/workflows/ci.yml` — `sidecar-smoke` job added

Runs on every PR to `main` on `ubuntu-latest`. Prevents the PyInstaller spec
from silently rotting between releases. Steps: install deps → seed DB →
PyInstaller build → spawn binary → `curl /api/health` with 20 s timeout →
Python assertion that `status == "ok"` and `bike_count > 0`.

---

### 6. `docs/RELEASE.md` — NEW

Step-by-step tag-and-ship runbook covering:
- One-time Ed25519 keypair generation
- Version bump procedure (3 files to keep in sync)
- Tag and push workflow
- Windows EV cert acquisition (~$400/yr, Sectigo)
- macOS Developer ID + notarisation ($99/yr, Apple Developer Program)
- Rollback procedure
- Full secrets reference table
- FAQ (re-run failed job, pre-release tags, sig file quirks, binary size target)

---

### 7. `docs/INSTALL.md` — NEW

End-user install guide for all four platforms. Key sections:
- Windows: SmartScreen bypass for unsigned build, silent install (`/S` flag)
- macOS: arm64 vs x64 DMG selection, Gatekeeper right-click bypass, `xattr` one-liner
- Linux: AppImage (chmod +x, FUSE note for Ubuntu 22.04+), `.deb`
- Auto-update behaviour
- Firewall / network transparency (localhost-only backend)
- Troubleshooting: sidecar startup failure, blank screen (WebKit2GTK)

---

### 8. `README.md` — Download section added

Added CI badge, Release badge, and "Download (Desktop App)" table with platform
links. Links currently resolve to 404 until `v0.1.0` is tagged.

---

## What is manual / still pending (human follow-up)

| Item | Owner | Priority |
|------|-------|----------|
| Generate real Ed25519 keypair, paste pubkey into `tauri.conf.json`, add privkey to GitHub Secrets | Hritwik | **Before first release** |
| Commission a real icon from a designer (replace placeholder MQ icons) | Hritwik | Before 1.0 public launch |
| Acquire Windows EV code-signing cert (~$400/yr) | Hritwik | Before public Windows release |
| Acquire Apple Developer ID membership ($99/yr) for macOS signing + notarisation | Hritwik | Before public macOS release |
| Verify the `.gitignore` does not swallow `desktop/src-tauri/bin/*.exe` — add `!desktop/src-tauri/bin/` exception if needed | Hritwik | Before first release build |
| Do a local `cargo tauri dev` run to confirm sidecar handshake end-to-end | Hritwik | Before v0.1.0 |
| Actually run `desktop/sidecar/build.sh` on each target OS and confirm binary size ≤80 MB | Hritwik (or CI) | CI will do this on first tag push |
| Tighten `darwin-x86_64` `.dmg.sig` JQ filter in `release.yml` `update-manifest` job once actual Tauri output filename is known | Dev | Before updater is tested |
| `desktop/src-tauri/tauri.conf.json` `plugins.updater.pubkey` — replace placeholder string with real public key | Hritwik | **Before first release** |
| Hygiene: delete orphan Vercel project `motoquant-web`, upgrade Railway trial, rename Railway project `proactive-adventure` → `motoquant-api` | Hritwik | Soon |

---

## Files touched this session

```
desktop/src-tauri/icons/32x32.png           (regenerated)
desktop/src-tauri/icons/128x128.png         (regenerated)
desktop/src-tauri/icons/128x128@2x.png      (regenerated)
desktop/src-tauri/icons/icon.png            (regenerated)
desktop/src-tauri/icons/icon.ico            (regenerated)
desktop/src-tauri/icons/icon.icns           (regenerated)
desktop/src-tauri/icons/StoreLogo.png       (NEW)
desktop/src-tauri/bin/.gitkeep             (NEW)
desktop/src-tauri/tauri.conf.json           (modified)
desktop/src-tauri/Cargo.toml               (modified)
desktop/src-tauri/capabilities/default.json (modified)
desktop/src-tauri/src/lib.rs               (modified — +1 plugin line)
.github/workflows/release.yml              (NEW)
.github/workflows/ci.yml                   (modified — sidecar-smoke job added)
docs/RELEASE.md                            (NEW)
docs/INSTALL.md                            (NEW)
README.md                                  (modified — Download section added)
SESSION_LOG_ws-release-pipeline.md         (NEW — this file)
```

Files explicitly NOT touched (per workstream ownership rules):
- `desktop/src/**` (Stream 3)
- `motoquant/**` (Streams 1, 2, 4, 5)
- `web/**` (Streams 5, 7)
- `CLAUDE.md` (preserved; session logged in this file instead)
