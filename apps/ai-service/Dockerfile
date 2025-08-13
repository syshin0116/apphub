# LangGraph service Dockerfile (supports both development and production)
FROM python:3.11-slim AS builder

# Install uv from official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install dependencies (separate layer for better caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project

# Copy project source code
COPY . .

# Install project (editable for dev, non-editable for prod)
ARG INSTALL_MODE=editable
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_MODE" = "editable" ]; then \
        uv sync --locked; \
    else \
        uv sync --locked --no-editable; \
    fi

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Activate virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run LangGraph service
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000"] 