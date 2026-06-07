# Proposal - scaffold-backend

## Summary

Scaffold the backend walking skeleton for plant-care: a Python 3.12 FastAPI service
laid out as a hexagonal monolith (domain / application / adapters / infrastructure),
with SQLAlchemy 2.x + Alembic wired for dual-engine persistence (SQLite default,
PostgreSQL via `DATABASE_URL`), a single `GET /api/v1/health` endpoint, and the full
mechanical quality-gate toolchain (ruff, mypy strict, import-linter, pytest+coverage,
pip-audit) driven from a root `Makefile`.

This is story **E1 Foundation** (backend slice) from `docs/product-spec.md` section 4.
It is a **walking skeleton only**: no plant / schedule / location domain features.
Those arrive in later stories (E2+).

## Scope (in)

- `backend/` src-layout Python package per ARCH-002 layering.
- Dual-engine SQLAlchemy 2.x setup + Alembic with batch mode for SQLite (ARCH-011).
- One real-but-empty initial migration (`schema_meta` bootstrap table) so
  `alembic upgrade head` succeeds on both SQLite and PostgreSQL.
- `GET /api/v1/health` returning `{"status": "ok", "version": ...}`; OpenAPI docs at
  `/api/v1/docs`.
- Security-by-default posture: locked-down CORS, security headers middleware
  (SEC-003, SEC-011), settings via pydantic-settings reading env vars (SEC-006).
- Quality tooling configured in `pyproject.toml`: ruff (lint+format+S), mypy strict on
  domain+application, import-linter hexagonal contracts, pytest with required layer
  markers, coverage floor 85 (QG-001, QG-002, TEST-012).
- Tests: unit test for the health use case, integration test booting the app against
  SQLite hitting `/api/v1/health`, Alembic migration smoke test.
- Root `Makefile` with one target per gate plus `dev-backend`, structured so frontend
  targets append later without conflict.
- Spec lifecycle artifacts under `specs/changes/scaffold-backend/`.

## Scope (out)

- Any plant / schedule / location / care-event domain logic (E2+).
- Frontend (separate agent), Docker image, GitHub Actions workflow (separate slices of E1).
- Species provider, webhooks, ICS, due computation.

## Stack affirmation (PRIN-V / ARCH-001)

No stack amendment. Uses the locked stack exactly: Python 3.12 + FastAPI,
SQLAlchemy 2.x, SQLite + PostgreSQL, Alembic, Pydantic v2. No new components added.

## Trust boundary (SEC-001)

`/api/v1/health` is a non-destructive read with no PII; safe on the trust boundary.
No auth in v1 by design (SEC-003). CORS locked down (no wildcard-with-credentials),
allowed origins are explicit config. Default bind is configurable and documented.

## Accepted dependency advisory (SEC-009)

- **PYSEC-2026-161** (Starlette: `request.url` reconstructed from an unvalidated
  `Host` header). Fix is Starlette 1.0.1, which the current FastAPI line
  (`<0.121`) does not yet allow, so bumping is not possible without a stack move.
  The advisory is **below the SEC-009 CVSS > 7.5 block bar** and **off our critical
  path**: v1 has a single non-destructive `/api/v1/health` endpoint, no Host-based
  URL reconstruction, no redirects, and no auth. Accepted with a `pip-audit
  --ignore-vuln` entry (justification inline in the Makefile).
  **Revisit date: 2026-09-01** (or sooner once FastAPI admits Starlette >= 1.0).

## Deviations (comply-or-explain, PRIN-X)

None. All MUSTs touched by this change are satisfied as written; the advisory above
is handled within the SEC-009 accept-and-document path, not a deviation.
