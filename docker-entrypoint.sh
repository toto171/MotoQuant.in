#!/bin/sh
# MotoQuant — container entrypoint.
#
# Boot logic:
#   The image ships a baked, seeded DB at /app/motoquant.db (the catalog:
#   bikes, parts, tyres, venues). When MOTOQUANT_DB points somewhere else
#   (for example a mounted volume) we seed that path ONCE from the baked copy
#   on first boot, then leave it alone. MotoQuant stores no visitor data, so
#   the default setup needs no volume: MOTOQUANT_DB defaults to the baked
#   path, the seed-path == target-path check below short-circuits, and the
#   container just starts the API.
set -e

SEED_DB="/app/motoquant.db"
TARGET_DB="${MOTOQUANT_DB:-/app/motoquant.db}"

if [ "$TARGET_DB" != "$SEED_DB" ]; then
  TARGET_DIR=$(dirname "$TARGET_DB")
  # The image runs as unprivileged user "app" (Dockerfile USER); the directory
  # holding $TARGET_DB must be writable by it.
  mkdir -p "$TARGET_DIR"
  if [ ! -f "$TARGET_DB" ]; then
    echo "[entrypoint] DB $TARGET_DB not found, seeding from image copy $SEED_DB"
    cp "$SEED_DB" "$TARGET_DB"
  else
    echo "[entrypoint] DB $TARGET_DB present, leaving it as is"
  fi
fi

exec uvicorn motoquant.api:app --host 0.0.0.0 --port "${PORT:-8000}"
