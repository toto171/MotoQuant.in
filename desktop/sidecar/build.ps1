# Build the MotoQuant backend sidecar on Windows.
#
# Output: dist\motoquant-backend.exe
# Rename + move to desktop\src-tauri\bin\motoquant-backend-x86_64-pc-windows-msvc.exe
# so Tauri can pick it up as an external binary. See README.md for details.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "━━ MotoQuant backend sidecar build (Windows) ━━"

# ── venv ───────────────────────────────────────────────────────────────
if (-not (Test-Path .venv)) {
    Write-Host "→ Creating build venv at .venv\"
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip | Out-Null

Write-Host "→ Installing sidecar build deps"
pip install -q -r requirements-sidecar.txt

Write-Host "→ Installing motoquant (editable)"
pip install -q -e ..\..

# ── Pre-flight: seeded DB exists ───────────────────────────────────────
$Db = "..\..\motoquant.db"
if (-not (Test-Path $Db) -or ((Get-Item $Db).Length -eq 0)) {
    Write-Error "Seeded DB missing at $Db. Run: python -m motoquant.run db init && ... && db seed"
    exit 1
}
Write-Host "→ Seeded DB OK: $([math]::Round((Get-Item $Db).Length / 1MB, 1)) MB"

# ── Clean + build ──────────────────────────────────────────────────────
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist)  { Remove-Item -Recurse -Force dist }
if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }

pyinstaller motoquant-backend.spec --clean --noconfirm

$Bin = "dist\motoquant-backend.exe"
if (-not (Test-Path $Bin)) {
    Write-Error "Build produced no executable at $Bin"
    exit 1
}

$SizeMb = [math]::Round((Get-Item $Bin).Length / 1MB, 1)
Write-Host ""
Write-Host "✓ Built: $Bin ($SizeMb MB)"
Write-Host ""
Write-Host "Next step: rename + copy into Tauri's bin\ directory."
Write-Host "  Example:"
Write-Host "    Copy-Item $Bin ..\src-tauri\bin\motoquant-backend-x86_64-pc-windows-msvc.exe"
Write-Host "See README.md for the target-triple table."
