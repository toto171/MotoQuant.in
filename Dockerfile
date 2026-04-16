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
EXPOSE ${PORT}

CMD uvicorn motoquant.api:app --host 0.0.0.0 --port ${PORT}
