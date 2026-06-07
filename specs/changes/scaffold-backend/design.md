# Design - scaffold-backend

## Layering (ARCH-002)

```
backend/src/plant_care/
  domain/          pure Python; entities, value objects, ports (Protocols). No FW.
  application/     use cases; depends only on domain types + ports.
  adapters/
    inbound/web/   FastAPI routers + Pydantic request/response schemas (HTTP only).
    outbound/db/   SQLAlchemy engine/session, ORM base, Alembic migrations.
  infrastructure/  settings (pydantic-settings), DI composition root, app factory.
```

Dependencies point inward only. Enforced mechanically by import-linter (ARCH-003).

## Key choices

### Health as a real use case, not just a route handler
Even though health is trivial, it is modelled as a domain value object
(`HealthStatus`) + an application use case (`GetHealthStatus`) + an inbound port.
This validates the hexagonal wiring end-to-end on the walking skeleton, so later
domain features drop into a proven shape rather than retrofitting layers.
**Alternative considered:** inline the dict in the router. Rejected: it would leave
the application/domain layers untested and the import-linter contracts unexercised,
defeating the point of a skeleton.

### Dual-engine via a single SQLAlchemy URL (ARCH-011)
`Settings.database_url` defaults to `sqlite:///data/app.db`; `DATABASE_URL` env var
overrides it (e.g. a `postgresql+psycopg://...` URL). The engine is created from this
single URL. SQLite gets `connect_args={"check_same_thread": False}` and a
`StaticPool`-free file engine; both engines share the same declarative metadata.
**Alternative considered:** separate engine factories per dialect. Rejected as
premature; the URL abstraction already isolates dialect differences, and no
engine-specific SQL exists on the critical path yet.

### Alembic batch mode for SQLite (ARCH-011)
`env.py` passes `render_as_batch=True` when the dialect is `sqlite`, so future ALTERs
that SQLite cannot do natively are emitted as batch (copy-and-move) operations. The
PostgreSQL path uses native ALTER. A SQLAlchemy naming convention is set on the
`MetaData` so constraint names are deterministic across engines (required for batch
mode to name constraints consistently).

### Initial migration: `schema_meta` bootstrap table
The first migration is "real but empty of domain": it creates a single-row
`schema_meta` table recording the bootstrap. This gives `alembic upgrade head` a
concrete operation to run on both engines (a true smoke target) without inventing any
domain tables. Later migrations add domain tables. **Alternative considered:** a
truly no-op migration. Rejected: a no-op does not prove DDL actually executes on both
engines, which is the whole risk ARCH-011 guards against.

### Settings via pydantic-settings (SEC-006)
`Settings(BaseSettings)` reads env vars (prefix-free, `PLANT_CARE_`-style not used to
keep `DATABASE_URL` standard). No secrets in code. `.env` is supported by
pydantic-settings at runtime but never read by agents and never committed.

### Security middleware (SEC-003, SEC-011)
A single middleware sets `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
`Permissions-Policy`, and a `Content-Security-Policy` with no inline script/style.
CORS is configured from explicit `cors_allow_origins` settings (empty by default; no
wildcard-with-credentials). Set centrally so every response is covered.

## mypy posture (QG-001)
`--strict` enforced on `plant_care.domain` and `plant_care.application` via per-module
overrides; adapters/infrastructure run at the default (looser) strictness because they
touch framework types (FastAPI, SQLAlchemy) whose stubs are imperfect.

## import-linter contracts (ARCH-003)
1. Layered contract: domain < application < adapters/infrastructure (inward only).
2. Forbidden contract: `domain` must not import `fastapi`, `sqlalchemy`, `pydantic`.
3. Forbidden contract: `application` must not import `fastapi`, `sqlalchemy`.

## Testing (TEST-001, TEST-012)
- Unit: `GetHealthStatus` use case in isolation (no app, no DB). `pytestmark = unit`.
- Integration: boot the wired app via FastAPI `TestClient` against a temp SQLite file,
  run migrations, hit `/api/v1/health`. `pytestmark = integration`.
- Migration smoke: `alembic upgrade head` then `downgrade base` against temp SQLite,
  asserting the `schema_meta` table appears/disappears. `pytestmark = integration`.

## Tooling choice: uv
`uv` is available on the machine, so dependencies are managed via `pyproject.toml` +
`uv.lock` (committed lockfile). The Makefile uses `uv run` so gates are reproducible.
