# LangGraph service Dockerfile (supports both development and production)
FROM python:3.11-slim AS builder

# Install uv from official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install dependencies (separate layer for better caching)
# Use only pyproject.toml to avoid requiring uv.lock
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

# Copy project source code
COPY . .

# Install project (editable for dev, non-editable for prod)
ARG INSTALL_MODE=editable
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_MODE" = "editable" ]; then \
        uv sync; \
    else \
        uv sync --no-editable; \
    fi

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage to a path outside the app mount
COPY --from=builder --chown=appuser:appuser /app/.venv /opt/venv

# Activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run LangGraph service
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000"] 