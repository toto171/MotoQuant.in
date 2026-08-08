FROM python:3.11-slim

WORKDIR /app

# Install dependencies from the fully-pinned lockfile so two builds of the
# same git commit install identical dependency sets (requirements-api.txt is
# the human-maintained source; `make lock` regenerates the lock from it).
COPY requirements-api.lock .
RUN pip install --no-cache-dir -r requirements-api.lock

# Copy application code
COPY motoquant/ ./motoquant/
COPY motoquant.db .
COPY artifacts/surrogate/surrogate_numpy.npz ./artifacts/surrogate/surrogate_numpy.npz
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Run as an unprivileged user. /app must stay writable by it: SQLite creates
# journal/WAL sibling files next to /app/motoquant.db, so the DB's DIRECTORY
# (not just the file) needs write permission.
RUN useradd -m app && chown -R app:app /app

# Railway injects PORT at runtime
ENV PORT=8000
ENV MOTOQUANT_DB=/app/motoquant.db

USER app

# Startup
# Entrypoint seeds a persistent-disk DB on first boot, then execs uvicorn.
# No-op when MOTOQUANT_DB is the baked /app path (current free tier).
CMD ["./docker-entrypoint.sh"]
