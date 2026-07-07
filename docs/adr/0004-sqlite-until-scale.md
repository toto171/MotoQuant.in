# ADR-0004: SQLite is the datastore until a real scaling trigger

**Status:** Accepted
**Date:** 2026-07-06 (documenting a long-standing decision)
**Deciders:** Hritwik Mudhai + maintaining agents

## Context

"Move to PostgreSQL / Supabase" is proposed periodically. The current datastore
is a single SQLite file (`motoquant.db`, ~18 MB) that ships seeded inside the
Docker image and is read through repository classes. The API runs as a single
worker on Render's free tier.

## Decision

**Stay on SQLite until a concrete scaling trigger fires.** SQLite is the correct
tool while the app is a single-worker, read-heavy service with an
author-curated catalog. It has zero operational overhead, ships with the image,
and makes local dev and CI trivial (no DB server to stand up).

Triggers that would justify migrating to a networked DB (Postgres/Supabase):
1. Multiple API workers/replicas (SQLite's single-writer model + the shared
   in-process connection — see KNOWN_TRAPS T14 — stop being adequate).
2. User-generated write volume (accounts, saved runs, leaderboard) exceeding
   what a single writer handles comfortably.
3. A need for cross-instance consistency (horizontal scale) or managed backups.

## Consequences

- **Positive.** No infra to run; the catalog is versioned in git and shipped
  atomically; dev/CI are dependency-free.
- **Negative / known debt.** The write path shares one process-wide connection
  across request + job threads (KNOWN_TRAPS T14). This is fine single-worker but
  is the **first thing to fix before horizontal scale** — either a
  per-thread/pooled connection *or* the Postgres migration, whichever the
  scaling trigger demands.
- **Pre-work already staged.** `docker-entrypoint.sh` can seed a persistent-disk
  DB (Render disk) without code changes; `render.yaml` documents the disk block.
  Migration to Postgres would need Alembic (not yet added) for schema management.

## References

- `motoquant/database/connection.py` · `docs/KNOWN_TRAPS.md` T14 ·
  `docs/ROADMAP.md` (scaling section).
