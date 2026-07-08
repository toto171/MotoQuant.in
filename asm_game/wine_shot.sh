#!/usr/bin/env bash
# Run the exe under Xvfb+Wine and screenshot it. Arg1 = output png.
export WINEPREFIX=$HOME/.wine-game WINEDEBUG=-all DISPLAY=:99
OUT="${1:-shot.png}"
pkill Xvfb 2>/dev/null; sleep 0.5
Xvfb :99 -screen 0 1200x900x24 >/dev/null 2>&1 &
sleep 2
wine raycaster.exe >/dev/null 2>&1 &
sleep "${2:-5}"
import -window root "$OUT" 2>/dev/null && echo "captured $OUT"
sleep 0.2
wineserver -k 2>/dev/null; pkill Xvfb 2>/dev/null
