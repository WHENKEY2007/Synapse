# ==============================================================================
# Synapse Self-Healing Knowledge Base - Production Multi-Stage Dockerfile
# ==============================================================================

# --- Stage 1: Build & Dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Runtime Container ---
FROM python:3.11-slim AS runner

# Security: Non-root execution
ARG USER_NAME=synapse
ARG USER_UID=10001
ARG USER_GID=10001

RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} --create-home --shell /bin/bash ${USER_NAME}

WORKDIR /app

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /home/${USER_NAME}/.local
ENV PATH=/home/${USER_NAME}/.local/bin:${PATH}
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create persistent storage directories
RUN mkdir -p /app/data /app/backend /app/dist \
    && chown -R ${USER_NAME}:${USER_NAME} /app

# Copy application code
COPY backend/ /app/backend/
COPY dist/ /app/dist/

# Set ownership
RUN chown -R ${USER_NAME}:${USER_NAME} /app

USER ${USER_NAME}

# Environment defaults
ENV SYNAPSE_ENV=production
ENV SYNAPSE_PORT=8000
ENV SYNAPSE_DB_PATH=/app/data/synapse.db

# Health check against production status endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

EXPOSE 8000

# Start FastAPI production server with Uvicorn
CMD ["python", "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
