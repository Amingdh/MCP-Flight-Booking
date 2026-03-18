# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency manifest first (better layer caching)
COPY server/pyproject.toml .

# Install dependencies into an isolated virtual environment
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
    "mcp[cli]>=1.0.0" \
    "fastapi>=0.111.0" \
    "uvicorn[standard]" \
    "pydantic-settings>=2.0.0" \
    python-dotenv \
    httpx

# ── Stage 2: runtime ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Copy the pre-built virtual environment
COPY --from=builder /opt/venv /opt/venv

# Make venv binaries available
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy application source
COPY server/app ./app
COPY server/data ./data

# Copy .env (overridden by docker-compose environment: block at runtime)
COPY server/.env.example .env

EXPOSE 8000

# Use exec form for proper signal handling
# server_http.py = FastAPI REST server (for Docker / demo client)
CMD ["python", "app/server_http.py"]
