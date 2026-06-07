# Viridarium backend

FastAPI + SQLAlchemy 2.x backend for Viridarium, laid out as a hexagonal monolith
(domain / application / adapters / infrastructure).

Walking skeleton: `GET /api/v1/health` and OpenAPI docs at `/api/v1/docs`. Domain
features (plants, schedules, care events) arrive in later stories.

## Local development

Dependencies are managed with [uv](https://docs.astral.sh/uv/). From the repo root:

```bash
make dev-backend        # run the dev server with reload
make quality-gates      # run the full backend mechanical gate
```

## Persistence

Dual-engine (SQLite default, PostgreSQL via `DATABASE_URL`). Apply migrations:

```bash
cd backend && uv run alembic upgrade head
```
