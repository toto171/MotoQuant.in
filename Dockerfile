FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY motoquant/ ./motoquant/
COPY app.py .
COPY motoquant.db .

# Railway injects PORT at runtime
ENV PORT=8000
ENV MOTOQUANT_DB=/app/motoquant.db

# Startup
CMD ["/bin/sh", "-c", "echo '=== MOTOQUANT STARTING ===' && echo PORT=$PORT && python -c 'print(\"Python OK\")' && python -c 'import motoquant; print(\"Import OK\")' && exec uvicorn motoquant.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
