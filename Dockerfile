FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY motoquant/ ./motoquant/
COPY app.py .

# Railway injects PORT at runtime
ENV PORT=8000

# Startup: log the port, then launch uvicorn
CMD echo "Starting MotoQuant API on port ${PORT}..." && \
    python -c "import motoquant; print('motoquant package imported OK')" && \
    uvicorn motoquant.api:app --host 0.0.0.0 --port ${PORT}
