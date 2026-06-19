# ── AI Service Dockerfile ─────────────────────────────────────────────────────
FROM python:3.11-slim

# Build args
ARG APP_ENV=production

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create directories for model artifacts (will be mounted as volumes in prod)
RUN mkdir -p models vectorstore

# Pre-download sentence-transformer model to cache it in the image
# (avoids download on first request)
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2')" || echo "Model download skipped"

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Entrypoint
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8006", \
     "--workers", "1", \
     "--log-level", "info"]
