# Minimal, secure Python container for FastAPI + Uvicorn
# Final image ~80MB, no build tools
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=3000

# System deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for docker layer caching
COPY requirements.txt ./
RUN python -m venv .venv && . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Cloud Run respects $PORT env)
EXPOSE 8080

# Health variables defaults; adjust in Cloud Run env
ENV AUSTLII_POLL_INTERVAL=120 \
    AUSTLII_HEALTH_TIMEOUT=6 \
    AUSTLII_TIMEOUT=8 \
    AUSTLII_RETRIES=2 \
    AUSTLII_BACKOFF=0.5

# Start the server (Cloud Run injects $PORT, default 8080)
CMD ["/app/.venv/bin/python", "run.py"]
