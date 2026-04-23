# MotoQuant backend sidecar — build + packaging

This folder produces the Python FastAPI backend as a single standalone executable that Tauri spawns as a sidecar when the desktop app starts.

## Why a sidecar?

The MotoQuant physics engine + full 15-submodel simulation stack is pure Python (numpy/scipy). Porting it to Rust/WASM would be weeks of work for zero user-visible benefit. The Tauri-native approach is: keep the backend in Python, freeze it to a native binary with PyInstaller, and have Tauri boot it on app launch. See [`desktop/src-tauri/src/lib.rs`](../src-tauri/src/lib.rs) for the Rust side of the handshake (`pick_free_port` → spawn → health-check loop).

## How to build

### Linux / macOS

```bash
cd desktop/sidecar
./build.sh
```

### Windows

```powershell
cd desktop\sidecar
.\build.ps1
```

Both scripts:
1. Create a venv at `desktop/sidecar/.venv/`.
2. `pip install -r requirements-sidecar.txt` (runtime deps + PyInstaller).
3. `pip install -e ../..` so the frozen binary contains the `motoquant` package.
4. Run PyInstaller with `motoquant-backend.spec`.
5. Sanity-check the output by starting it on an ephemeral port and pinging `/api/health` (Unix only; Windows skips the smoke test).

Build artifact: `dist/motoquant-backend` (or `.exe` on Windows).

## Tauri target-triple naming

Tauri's `externalBin` mechanism expects **the binary's filename to include the host's Rust target triple**, otherwise the bundler can't find it per-platform. After building, rename the output before dropping it into `../src-tauri/bin/`:

| Platform              | Rust target triple                  | Final filename                                              |
|-----------------------|-------------------------------------|-------------------------------------------------------------|
| Windows (x64)         | `x86_64-pc-windows-msvc`            | `motoquant-backend-x86_64-pc-windows-msvc.exe`              |
| Linux (x64 glibc)     | `x86_64-unknown-linux-gnu`          | `motoquant-backend-x86_64-unknown-linux-gnu`                |
| macOS (Intel)         | `x86_64-apple-darwin`               | `motoquant-backend-x86_64-apple-darwin`                     |
| macOS (Apple Silicon) | `aarch64-apple-darwin`              | `motoquant-backend-aarch64-apple-darwin`                    |

```bash
# Example: Linux x64
cp dist/motoquant-backend \
   ../src-tauri/bin/motoquant-backend-x86_64-unknown-linux-gnu

# Example: Windows
Copy-Item dist\motoquant-backend.exe `
          ..\src-tauri\bin\motoquant-backend-x86_64-pc-windows-msvc.exe
```

You can discover your host's triple with `rustc -vV | grep host`.

## Wiring the sidecar back into `tauri.conf.json`

The Tauri config currently **does not** declare `externalBin` or `resources`, because those paths are validated at build time and we didn't want `npx tauri dev` to fail on a fresh clone before anyone has built a sidecar. Once you've produced `desktop/src-tauri/bin/motoquant-backend-<TRIPLE>[.exe]` and copied the seeded DB to `desktop/src-tauri/resources/motoquant.db`, add these two keys back under `"bundle"` in `desktop/src-tauri/tauri.conf.json`:

```json
"externalBin": ["bin/motoquant-backend"],
"resources": ["resources/motoquant.db"]
```

Tauri resolves `externalBin` paths per-target: the `bin/motoquant-backend` prefix + your host's target triple (e.g. `motoquant-backend-x86_64-pc-windows-msvc.exe` on Windows). After re-adding, `npx tauri build` produces an installer that bundles both.

## Database bundling

The seeded `motoquant.db` (~5 MB, 270 bikes / 424 parts / 159 tires / 20 venues) is bundled **inside** the PyInstaller binary via `datas` in the spec file. `sidecar_entry.py` resolves `sys._MEIPASS/motoquant.db` at startup and sets `MOTOQUANT_DB` so `motoquant/api.py:92` finds it.

Trade-off: catalog updates require rebuilding the sidecar. For dev flow where you'd rather not rebuild on every `db seed`, set `MOTOQUANT_DB` before launching the desktop app and the sidecar will respect the override.

Alternative (not yet wired): Tauri already lists `motoquant.db` under `bundle.resources` in [`tauri.conf.json`](../src-tauri/tauri.conf.json). To decouple DB from binary, the Rust side in `lib.rs` could resolve that resource path and pass it via env var to the sidecar (`cmd.env("MOTOQUANT_DB", resource_path)`). Tracking as a follow-up.

## Dev-mode override

When iterating on both the React frontend and the Python backend, you don't want Tauri auto-spawning a stale binary. Set:

```bash
export MOTOQUANT_DEV_BACKEND_URL=http://127.0.0.1:8000
```

Then in another terminal run `uvicorn motoquant.api:app --reload`. Tauri's `setup()` hook respects this env var and skips the sidecar spawn entirely (see `lib.rs` around line 115).

## Troubleshooting

| Symptom                                       | Cause / fix                                                                                                         |
|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `ModuleNotFoundError: uvicorn.loops.asyncio`  | PyInstaller missed a hidden import. Add to `hiddenimports` list in the spec.                                        |
| Binary is 400+ MB                             | Likely pulled in torch/sklearn/matplotlib. Check `excludes` in the spec; add the offender.                          |
| `/api/health` returns `database: error`       | Bundled DB wasn't found. Either the `datas` path is wrong, or `sidecar_entry.py` `_resolve_bundled_db()` logic failed. |
| Windows console window flashes on spawn       | Known PyInstaller behavior with `console=True`. Switch to `console=False` if console logs aren't needed.            |
| Tauri complains "external binary not found"   | Filename doesn't include the target triple suffix. See table above.                                                 |

## CI integration

This spec is designed to be CI-buildable. A `sidecar` job added to [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) would run on a matrix of `{ubuntu-latest, windows-latest, macos-l