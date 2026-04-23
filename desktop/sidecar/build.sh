#!/usr/bin/env bash
# Build the MotoQuant backend sidecar on Linux or macOS.
#
# Output: dist/motoquant-backend  (plain name)
# After building, rename to match Tauri's expected target-triple suffix and
# move it into desktop/src-tauri/bin/. See README.md for the exact suffix
# per platform.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━ MotoQuant backend sidecar build ━━"
echo "Working dir: $SCRIPT_DIR"

# ── venv ──────────────────────────────────────────────────────────────────
if [ ! -d .venv ]; then
  echo "→ Creating build venv at .venv/"
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install --upgrade pip

echo "→ Installing sidecar build deps"
pip install -q -r requirements-sidecar.txt

echo "→ Installing motoquant (editable)"
pip install -q -e ../..

# ── Pre-flight: seeded DB exists ──────────────────────────────────────────
DB="../../motoquant.db"
if [ ! -s "$DB" ]; then
  echo "❌ Seeded DB missing at $DB — run:"
  echo "     python -m motoquant.run db init"
  echo "     python -m motoquant.run import --known-bikes"
  echo "     python -m motoquant.run db seed"
  exit 1
fi
echo "→ Seeded DB OK: $(du -h "$DB" | cut -f1)"

# ── Clean + build ─────────────────────────────────────────────────────────
rm -rf build dist __pycache__
pyinstaller motoquant-backend.spec --clean --noconfirm

BIN="dist/motoquant-backend"
if [ ! -x "$BIN" ]; then
  echo "❌ Build produced no executable at $BIN"
  exit 1
fi

echo
echo "✓ Built: $BIN ($(du -h "$BIN" | cut -f1))"
echo
echo "Smoke test — starting on an ephemeral port, pinging /api/health:"

# Pick a free port, boot the sidecar, curl /api/health, kill.
PORT=$(python - <<'PY'
import socket
s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()
PY
)

"$BIN" --host 127.0.0.1 --port "$PORT" --log-level warning &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
  sleep 0.5
  if curl -fsS "http://127.0.0.1:$PORT/api/health" >/tmp/mq-health.json 2>/dev/null; then
    echo "✓ Health OK: $(cat /tmp/mq-health.json)"
    break
  fi
done

kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true

echo
echo "Next step: rename + move into Tauri's bin/ directory."
echo "  Example (Linux x86_64):"
echo "    cp dist/motoquant-backend ../src-tauri/bin/motoquant-backend-x86_64-unknown-linux-gnu"
echo "See README.md for the target-triple table."
