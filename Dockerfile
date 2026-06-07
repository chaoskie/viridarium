# syntax=docker/dockerfile:1
#
# plant-care single-container image (product-spec section 7).
#
# Multi-stage:
#   1. frontend-build - build the React SPA with Vite into /build/dist.
#   2. backend-deps    - resolve the locked backend deps into a relocatable venv with uv.
#   3. runtime         - slim, non-root Python 3.12 serving the API + the built SPA.
#
# Base images are pinned by SHA-256 digest (CI-006, SEC-012): same source + lockfiles
# => equivalent artifact, and no floating `latest` base in a shipped image.

# ---------------------------------------------------------------------------
# Stage 1: build the frontend
# ---------------------------------------------------------------------------
FROM node:20-bookworm-slim@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS frontend-build

WORKDIR /build
# The committed package-lock.json is lockfileVersion 3 produced by npm 11; node:20's
# bundled npm 10 rejects it as out-of-sync (tinyglobby/picomatch tree). Pin npm 11 so
# `npm ci` matches the lockfile that produced it (CI-006 reproducibility). The CI
# frontend job pins the same npm.
RUN npm install -g npm@11
# Install deps against the committed lockfile first for layer caching (CI-006).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Result: /build/dist (static SPA bundle).

# ---------------------------------------------------------------------------
# Stage 2: resolve backend dependencies into a venv
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58 AS backend-deps

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
# Sync only the locked runtime deps (no dev group) for a reproducible venv (CI-006).
# The project itself is installed in the runtime stage via PYTHONPATH on /app/src.
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---------------------------------------------------------------------------
# Stage 3: runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm@sha256:93ab4b7fa528b25124c97bcc755415e60eb671a86b4dbe0328df2fe2d1c1193d AS runtime

# OCI image labels. ${SOURCE_URL} stays a placeholder until the repo name is decided.
LABEL org.opencontainers.image.title="plant-care" \
      org.opencontainers.image.description="Self-hosted houseplant care tracker: inventory, watering and feeding schedules, open REST API." \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.source="https://github.com/OWNER/REPO"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    # App config (overridable env, read by pydantic-settings via field names). SQLite on
    # the /data volume by default; STATIC_DIR points at the bundled SPA so it is served
    # from the same origin. uvicorn binds 0.0.0.0 below: the trust boundary is the host
    # network / reverse proxy, not the container (SEC-003).
    DATABASE_URL=sqlite:////data/app.db \
    STATIC_DIR=/app/static

# Non-root runtime user (SEC-012).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --home /app app \
    && mkdir -p /data /app/static \
    && chown -R app:app /data /app

WORKDIR /app

# Resolved venv from stage 2.
COPY --from=backend-deps --chown=app:app /opt/venv /opt/venv
# Backend source (importable via PYTHONPATH=/app/src).
COPY --chown=app:app backend/src ./src
# Built SPA from stage 1.
COPY --from=frontend-build --chown=app:app /build/dist ./static

USER app

# SQLite lives here; future photo storage shares the volume (product-spec section 7).
VOLUME ["/data"]
EXPOSE 8000

# Liveness probe (product-spec section 7). Uses the venv Python (no curl in slim base).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status==200 else sys.exit(1)"]

# Serve the wired app. `plant_care.main:app` builds from environment settings, including
# STATIC_DIR so the SPA is served from the same origin.
CMD ["uvicorn", "plant_care.main:app", "--host", "0.0.0.0", "--port", "8000"]
