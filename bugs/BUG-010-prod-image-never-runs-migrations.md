---
title: Production image never runs DB migrations, fresh deploy 500s on a schemaless DB
tags:
  - bug
  - deployment
  - database
  - docker
status: fixed
severity: high
evidence: reproduced
created: 2026-08-12
related-change: fix/vir-67-entrypoint-migrations
work-item: "VIRIDARIUM-67"
---

### Observed behavior
A fresh `docker compose up -d` from the quickstart (fresh volume) comes up "healthy",
the frontend shell loads, and every page 500s:

```
sqlite3.OperationalError: no such table: plant
```

`/data/app.db` is 0 bytes. Confirmed 2026-08-07 on an office Mac mini (arm64, Colima).

### Expected behavior
A fresh deploy serves a working app. The image ships Alembic and migrations 0001-0008;
the schema must exist before the server accepts its first request.

### Steps to reproduce
1. `docker volume create <fresh>` and run the image against it.
2. `GET /api/v1/health` -> 200 (container reports healthy).
3. `GET /api/v1/plants` -> 500, `no such table: plant`.

### Root cause
Two independent gaps.

1. **Nothing ever ran the migrations.** The image `CMD` went straight to uvicorn.
   Alembic and the migration tree ship in the image, but no start-time step applied
   them, so the SQLite file was created empty by the first connection.
2. **The healthcheck could not see it.** `/api/v1/health` never touches the database,
   so `HEALTHCHECK` passes on a schemaless DB and the failure only surfaces as a user
   -visible 500. Liveness answering for readiness hid gap 1.

A contributing detail: `alembic.ini` is not in the runtime image (it lives at the
backend project root, outside the copied `src` tree), so a naive
`alembic upgrade head` in the entrypoint would fail on a missing config.

### Fix
- `viridarium.infrastructure.migrations` builds the Alembic config programmatically,
  deriving `script_location` from the package's own path, so no ini file is needed and
  the same code works in the image, a checkout, and an installed wheel. The URL keeps
  resolving through `env.py` from `DATABASE_URL` (SEC-006).
- `python -m viridarium.migrate` is the entrypoint step: it upgrades to head, logs the
  outcome (never the URL, which can carry credentials), and exits non-zero on failure.
- `backend/docker-entrypoint.sh` runs it under `set -e` and then `exec "$@"`, so the
  server binds only after a successful migration and uvicorn stays PID 1.
  `alembic upgrade head` is idempotent, which makes restart loops safe.
- Readiness is now a separate, schema-gated probe: `GET /api/v1/health/ready` returns
  200 with the applied revision, or 503 while the schema is absent. `/api/v1/health`
  stays pure liveness and remains the image `HEALTHCHECK` (conservative: the existing
  probe's semantics are unchanged).

### Acceptance criteria
- [x] Fresh volume: container starts, schema present, `GET /api/v1/plants` returns 200.
- [x] Restart of a running container stays healthy and keeps its data (idempotent).
- [x] A failing migration aborts the start instead of serving a schemaless app.
- [x] Readiness answers 503 before migrations and 200 after.
- [x] Backend + frontend quality gates green.

### Dedupe check
`bugs/` searched - none. BUG-006 also touched the pipeline, but is a dependency
advisory, unrelated.

### Context
- **Environment:** Docker (reproduced on arm64/Colima, fixed and verified on amd64)
- **DB engine:** SQLite on the `/data` volume (the quickstart default)
- **Version/commit:** 3a633bc (main)
- **Surface:** container image entrypoint, health/readiness endpoints

### Notes
An interim workaround (a bind-mounted `migrate.py` run by hand) is deployed at the
office. It can be removed once this ships.
