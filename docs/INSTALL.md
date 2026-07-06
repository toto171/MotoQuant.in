> **DISCONTINUED (July 2026).** The native desktop app was scrapped — the
> hosted web app at motoquant.in is the product. This document is retained
> for historical reference only; no desktop releases will be cut.

# MotoQuant Pro — Installation Guide

> **Current version:** see [Releases](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest)

MotoQuant Pro is a self-contained desktop application. It bundles a Python physics
engine inside the app — no Python installation required on your machine.

---

## System requirements

| Platform | Minimum |
|----------|---------|
| Windows | Windows 10 64-bit (build 1903+) |
| macOS | macOS 11 Big Sur (Apple Silicon or Intel) |
| Linux | Ubuntu 20.04+ / Fedora 36+ / any glibc 2.31+ distro |
| RAM | 512 MB free |
| Disk | 250 MB |

---

## Windows

### Download

Go to the [latest release](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest)
and download **`MotoQuant-Pro_x.y.z_x64-setup.exe`** (NSIS installer, recommended)
or **`MotoQuant-Pro_x.y.z_x64_en-US.msi`** (MSI, for enterprise/group-policy deployment).

### Install

1. Run the downloaded installer.
2. **SmartScreen warning:** The current release is unsigned. If you see
   *"Windows protected your PC"*, click **More info → Run anyway**.
   This warning disappears once the app accumulates enough usage data, or
   when a code-signing certificate is added in a future release.
3. Follow the installer prompts (defaults are fine).
4. Launch **MotoQuant Pro** from the Start menu.

### First run

On first launch the app starts a local Python backend (you may see a Windows
Firewall dialog — click **Allow access** to let the app talk to itself on
`127.0.0.1`). The backend is not accessible from other devices on your network.

### Silent install (IT / MDM)

```bat
MotoQuant-Pro_x.y.z_x64-setup.exe /S
```

Or for the MSI:

```bat
msiexec /i MotoQuant-Pro_x.y.z_x64_en-US.msi /quiet /norestart
```

### Uninstall

*Control Panel → Programs → MotoQuant Pro → Uninstall*, or via the NSIS
uninstaller at `C:\Program Files\MotoQuant Pro\Uninstall MotoQuant Pro.exe`.

---

## macOS

### Download

Go to the [latest release](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest)
and download the correct `.dmg` for your machine:

| File | Architecture |
|------|-------------|
| `MotoQuant-Pro_x.y.z_aarch64.dmg` | Apple Silicon (M1/M2/M3/M4) |
| `MotoQuant-Pro_x.y.z_x64.dmg` | Intel Mac |

Not sure which you have? Apple menu → About This Mac. "Apple M…" = arm64;
"Intel Core" = x64.

### Install

1. Open the downloaded `.dmg`.
2. Drag **MotoQuant Pro** into the **Applications** folder.
3. Eject the disk image.

### First launch — Gatekeeper warning

The current release is unsigned. macOS will block the first open with
*"MotoQuant Pro cannot be opened because the developer cannot be verified."*

**To bypass:**

1. Right-click (or Control-click) the app in Finder.
2. Select **Open** from the context menu.
3. In the dialog, click **Open** again.

You only need to do this once; subsequent launches open normally.

Alternatively, run once in Terminal:

```bash
xattr -dr com.apple.quarantine "/Applications/MotoQuant Pro.app"
```

### First run

The app starts a local Python sidecar on a random port on `127.0.0.1`.
If macOS prompts about incoming connections, click **Allow** (the backend is
localhost-only and does not accept remote connections).

### Uninstall

Drag **MotoQuant Pro** from `Applications` to Trash, then empty Trash.
App data is stored in `~/Library/Application Support/in.motoquant.desktop/`.
Delete that folder too for a clean uninstall.

---

## Linux

### Download options

Go to the [latest release](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest)
and choose your preferred package:

| File | Type | Notes |
|------|------|-------|
| `motoquant-pro_x.y.z_amd64.AppImage` | AppImage | Universal, no install needed |
| `motoquant-pro_x.y.z_amd64.deb` | Debian package | Ubuntu, Debian, Linux Mint |

### AppImage (recommended — works on any distro)

```bash
# 1. Download (replace x.y.z with the actual version)
wget https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/\
motoquant-pro_x.y.z_amd64.AppImage

# 2. Make it executable
chmod +x motoquant-pro_x.y.z_amd64.AppImage

# 3. Run
./motoquant-pro_x.y.z_amd64.AppImage
```

To integrate with your desktop launcher, use
[AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher) or place
the file in `~/.local/bin/` and create a `.desktop` file.

### Debian / Ubuntu (.deb)

```bash
# Download
wget https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/\
motoquant-pro_x.y.z_amd64.deb

# Install
sudo dpkg -i motoquant-pro_x.y.z_amd64.deb

# Launch
motoquant-pro
# or open "MotoQuant Pro" from your application menu
```

To uninstall: `sudo dpkg -r motoquant-pro`

### FUSE requirement (AppImage on Ubuntu 22.04+)

AppImages need FUSE 2. On Ubuntu 22.04+ it may not be installed by default:

```bash
sudo apt install libfuse2
```

---

## Auto-updates

MotoQuant Pro checks for updates automatically on startup (requires internet
access). When an update is available, a dialog will prompt you to install it.
Updates are signed with an Ed25519 key — only official builds are accepted.

To disable auto-update checks, set the environment variable
`MOTOQUANT_DISABLE_UPDATER=1` before launching.

---

## Firewall / network notes

MotoQuant Pro is a **local-only** application. The embedded Python backend
binds exclusively to `127.0.0.1` (localhost) and never accepts connections
from other machines. The only outbound network traffic is:

- Checking for updates at startup (one HTTPS GET to GitHub Releases).
- Optional: fetching live weather data for race venues (OWM API, configurable in Settings).

---

## Troubleshooting

### "Python sidecar did not start within 8 s"

The embedded Python backend failed to boot. Common causes:

1. **Antivirus false positive** — add an exception for the MotoQuant Pro install directory.
2. **Port conflict** — another process is blocking ephemeral ports. Restart your machine.
3. **Corrupted install** — uninstall, reboot, reinstall.

### App opens but shows a blank screen

Usually a WebView issue. On Linux, WebKit2GTK must be installed:

```bash
sudo apt install libwebkit2gtk-4.1-0   # Ubuntu 22.04+
```

On Windows, update the WebView2 runtime:
[Download WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)

### Reporting bugs

Open an issue at:
https://github.com/da25mem5s02-debug/MotoQuant_v1/issues

Include: OS version, MotoQuant Pro version (Settings → About), and a
description of what you did / what you expected / what happened.
