#!/bin/sh
# MotoQuant — container entrypoint.
#
# Account-durability boot logic (June 2026):
#   The image ships a baked, seeded DB at /app/motoquant.db (the build-time
#   catalog: bikes/parts/tires/venues). When MOTOQUANT_DB points somewhere
#   ELSE — e.g. a Render persistent disk at /data/motoquant.db — we seed that
#   path ONCE from the baked copy on first boot, then never touch it again.
#   Subsequent deploys keep the disk's DB (with its accumulated optional
#   accounts and saved runs) instead of overwriting it with the image copy.
#
#   On a free hosting plan (no disk), MOTOQUANT_DB defaults to the baked path, the
#   seed-path == target-path check below short-circuits, and behaviour is
#   byte-identical to the pre-entrypoint CMD. So this is safe to ship now and
#   "just works" the moment a disk is mounted + MOTOQUANT_DB is repointed.
set -e

SEED_DB="/app/motoquant.db"
TARGET_DB="${MOTOQUANT_DB:-/app/motoquant.db}"

if [ "$TARGET_DB" != "$SEED_DB" ]; then
  TARGET_DIR=$(dirname "$TARGET_DB")
  # The image runs as unprivileged user "app" (Dockerfile USER); the /data disk
  # mount must be writable by it — mount-point ownership is Render's to provide.
  mkdir -p "$TARGET_DIR"
  if [ ! -f "$TARGET_DB" ]; then
    echo "[entrypoint] persistent DB $TARGET_DB not found — seeding from image copy $SEED_DB"
    cp "$SEED_DB" "$TARGET_DB"
  else
    echo "[entrypoint] persistent DB $TARGET_DB present — keeping existing user data (no overwrite)"
  fi
fi

exec uvicorn motoquant.api:app --host 0.0.0.0 --port "${PORT:-8000}"
