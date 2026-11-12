# D-001: Stack and database

Status: ratified, 2026-06-07.

## Decision

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, hexagonal architecture.
- Frontend: React, TypeScript (strict), Vite, Tailwind.
- Database: SQLite by default, PostgreSQL via `DATABASE_URL`. Migrations must run on both.

## Why

Landscape research showed that the existing self-hosted plant apps draw complaints about
deploy weight (one requires MariaDB, another MySQL plus Redis plus a JVM service). The
self-hosting community norm for single-user apps is SQLite by default with optional
PostgreSQL. A lighter deploy is itself a differentiator.

## Consequences

- Users get a one-file default; anyone with an existing PostgreSQL server can point
  `DATABASE_URL` at it.
- No database-specific SQL is allowed (`ARCH-011`); CI runs the suite on both engines.
- Additions to the locked stack need an ADR, see
  [D-010](D-010-add-python-multipart.md).
