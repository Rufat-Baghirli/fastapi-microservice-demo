# Stage 1: Builder - To build and install dependencies
FROM python:3.10.11-slim AS builder
LABEL stage=builder

WORKDIR /app

# Arguments used during the build
ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000

# Install system packages required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Create an isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip itself
RUN python -m pip install --upgrade pip setuptools wheel

# Caching Optimization
# First, copy only the requirements files
COPY requirements/ ./requirements/

# Then, install dependencies. This layer will only be rebuilt if requirements files change.
RUN if [ -f requirements/base.txt ]; then python -m pip install --no-cache-dir -r requirements/base.txt; fi
RUN if [ -f requirements/dev.txt ]; then python -m pip install --no-cache-dir -r requirements/dev.txt; fi

# Stage 2: Runtime - To run the main application
FROM python:3.10.11-slim AS runtime
LABEL stage=runtime

WORKDIR /app

ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000
ARG INSTALL_PROD=false

# Install minimal system packages required for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy the prepared virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python runtime optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# === Caching Optimization ===
# First, copy only the production requirements file
COPY requirements/prod.txt ./requirements/prod.txt
# If this is a production build, install production dependencies
RUN if [ "$INSTALL_PROD" = "true" ] && [ -f requirements/prod.txt ]; then python -m pip install --no-cache-dir -r requirements/prod.txt; fi

# Create a non-root user for security
RUN groupadd -g ${APP_GID} ${APP_USER} \
  && useradd -m -u ${APP_UID} -g ${APP_GID} ${APP_USER}

# Finally, copy the entire project code. This prevents rebuilding upper layers on code changes.
COPY --chown=${APP_USER}:${APP_USER} . .

# Ensure the logs directory exists and is owned by the app user
RUN mkdir -p logs && chown -R ${APP_USER}:${APP_USER} logs

# Switch to the non-root user
USER ${APP_USER}

EXPOSE 8000

# Healthcheck to verify the container's health
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# Default command to run when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]