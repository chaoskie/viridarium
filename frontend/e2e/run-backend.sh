#!/usr/bin/env bash
# Boot the FastAPI backend against a throwaway SQLite DB for the Playwright
# acceptance suite (TEST-009). Migrations run to head first so the schema is
# real. Invoked by playwright.config.ts `webServer`; cwd is frontend/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB="${ROOT}/frontend/.e2e/acceptance.db"
# Dedicated port (never 8000) so the suite never fights a dev backend.
PORT="${E2E_BACKEND_PORT:-8799}"

mkdir -p "$(dirname "${DB}")"
rm -f "${DB}"
# Absolute path -> sqlite:////home/... (four slashes); matches the CI pattern.
export DATABASE_URL="sqlite:///${DB}"

# Throwaway photo storage (the default /data/photos isn't writable in dev/CI).
# Wiped each run so uploads in the acceptance suite start clean.
PHOTOS="${ROOT}/frontend/.e2e/photos"
rm -rf "${PHOTOS}"
mkdir -p "${PHOTOS}"
export PHOTOS_DIR="${PHOTOS}"

cd "${ROOT}/backend"
uv run --frozen alembic upgrade head
exec uv run --frozen uvicorn viridarium.main:app --app-dir src --port "${PORT}"
