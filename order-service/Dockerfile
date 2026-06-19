# ──────────────────────────────────────────────────────────────────────────────
# Dockerfile – order-service (Django 5 + Gunicorn)
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Build args
ARG SERVICE_PORT=8003
ENV SERVICE_PORT=${SERVICE_PORT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies (cached layer) ───────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Collect static files ──────────────────────────────────────────────────────
RUN python manage.py collectstatic --noinput || true

# ── Non-root user for security ────────────────────────────────────────────────
RUN addgroup --system app && adduser --system --ingroup app app
RUN chown -R app:app /app
USER app

EXPOSE ${SERVICE_PORT}

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT}/api/health/ || exit 1

# ── Entrypoint: migrate + start gunicorn ─────────────────────────────────────
CMD ["sh", "-c", "python manage.py migrate --noinput && \
    gunicorn core.wsgi:application \
    --bind 0.0.0.0:${SERVICE_PORT} \
    --workers 3 \
    --worker-class sync \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -"]

