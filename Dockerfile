FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY motoquant/ ./motoquant/
COPY motoquant.db .
COPY artifacts/surrogate/surrogate_numpy.npz ./artifacts/surrogate/surrogate_numpy.npz
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Railway injects PORT at runtime
ENV PORT=8000
ENV MOTOQUANT_DB=/app/motoquant.db

# Startup
# Entrypoint seeds a persistent-disk DB on first boot, then execs uvicorn.
# No-op when MOTOQUANT_DB is the baked /app path (current free tier).
CMD ["./docker-entrypoint.sh"]
