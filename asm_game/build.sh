#!/usr/bin/env bash
# Cross-build the Win64 .exe from Linux (nasm + mingw-w64).
#   sudo apt-get install nasm mingw-w64
set -euo pipefail
cd "$(dirname "$0")"

nasm -f win64 raycaster.asm -o raycaster.obj

# gcc as the linker driver finds the mingw import libs automatically.
# -nostdlib: no C runtime.  -e start: our entry point.  windows subsystem: no console.
x86_64-w64-mingw32-gcc -nostdlib -o raycaster.exe raycaster.obj \
    -luser32 -lgdi32 -lkernel32 \
    -Wl,--subsystem,windows -Wl,-e,start

echo "Built raycaster.exe"
