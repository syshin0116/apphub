FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files and source code (needed for editable install)
COPY pyproject.toml ./
COPY uv.lock ./
COPY langgraph.json ./
COPY src ./src
COPY .env .env

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 2024

# Run with uv
CMD ["uv", "run", "langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"]
