FROM python:3.10.11-slim AS builder

WORKDIR /app

# Build args
ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install base dependencies into venv
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Install dev dependencies (builder only) if dev.txt present
COPY requirements/dev.txt .
RUN if [ -f dev.txt ]; then pip install --no-cache-dir -r dev.txt; fi

# ----------------------------------------------------------------
# Runtime stage (smaller image)
FROM python:3.10.11-slim AS runtime

WORKDIR /app

ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000
# New arg to conditionally install prod dependencies
ARG INSTALL_PROD=false

# Minimal runtime packages (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy venv from builder (contains base + dev if installed there)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy prod requirements and install them only if requested
COPY requirements/prod.txt .
RUN if [ "$INSTALL_PROD" = "true" ] && [ -f prod.txt ]; then /opt/venv/bin/pip install --no-cache-dir -r prod.txt; fi

# Create non-root user and set ownership
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -m -u ${APP_UID} -g ${APP_GID} ${APP_USER} && \
    chown -R ${APP_USER}:${APP_USER} /app

# Switch to non-root user
USER ${APP_USER}

# Copy application code (as non-root)
COPY --chown=${APP_USER}:${APP_USER} . .

# Create logs dir with correct perms
RUN mkdir -p logs && chown ${APP_USER}:${APP_USER} logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Default command for dev/local (prod will override in compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]