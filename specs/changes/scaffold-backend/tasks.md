# Tasks - scaffold-backend

Newest work happens top-to-bottom. Checked = done.

- [x] T1 Spec artifacts (proposal, design, tasks, worklog)
- [x] T2 `backend/` package skeleton + `pyproject.toml` (deps + tool config)
- [x] T3 Domain layer: `HealthStatus` value object + inbound port
- [x] T4 Application layer: `GetHealthStatus` use case
- [x] T5 Adapters/outbound/db: declarative base + naming convention, engine/session, Alembic scaffold
- [x] T6 Initial Alembic migration: `schema_meta` bootstrap table (dual-engine, batch for SQLite)
- [x] T7 Infrastructure: settings, DI container, app factory + security middleware
- [x] T8 Adapters/inbound/web: health router + response schema, mounted under `/api/v1`
- [x] T9 import-linter contracts in pyproject
- [x] T10 Tests: unit (health use case), integration (app boot + health + CORS), migration smoke
- [x] T11 Root `Makefile` with one target per gate + `dev-backend` + `quality-gates`
- [x] T12 Create venv, install, run `make quality-gates`; iterate to green
- [x] T13 Post PASS/FAIL gate checklist; update worklog
