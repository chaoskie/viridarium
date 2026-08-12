# Worklog - BUG-010 production image never runs DB migrations

Per-fix trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.

## Gate-check (QG-004, 2026-08-12)

Mechanical gates (discovered from `Makefile` + `.github/workflows/quality-gates.yml`):

- `make lint` - **PASS**
- `make format-check` - **PASS** (98 files)
- `make typecheck` - **PASS** (65 source files)
- `make imports` - **PASS** (3 contracts kept, 0 broken)
- `make test-coverage` - **PASS** (500 passed, 99.41% vs an 85% floor)
- `make audit` - **PASS** (no known vulnerabilities; the first run reported msgpack
  1.1.2 from a stale venv, green after `make backend-install` re-synced the lockfile)
- `make fe-lint` / `fe-format-check` / `fe-typecheck` / `fe-test` - **PASS** (279 tests)

Docker verification (the thing the unit suite structurally cannot prove):

- Built the production image locally, ran it against a **fresh** volume: migrations
  0001-0008 applied in the entrypoint before uvicorn bound, `/api/v1/health` 200,
  `/api/v1/health/ready` 200 `{"schema_revision":"0008"}`, `/api/v1/plants` 200 `[]`,
  `/data/app.db` 81920 bytes (was 0 before the fix).
- Created a plant, `docker restart`, re-probed: container `healthy`, second migration
  pass a no-op, the plant still there, readiness still 200. Restart loop is safe.
- `uvicorn` remains PID 1 (the entrypoint `exec`s the CMD), so signal handling is
  unchanged.

DoD gate (QG-004):

1. Reproduction is a failing test that now passes (`PRIN-III`/`TEST-014`) - **WATCH**
   (see below)
2. Tests green - **PASS**
3. Boundaries clean (`ARCH-003`) - **PASS** (import-linter contracts kept; the readiness
   port lives in the domain, its adapter in `adapters/outbound/db`)
4. Dual-engine (`ARCH-011`) - **PASS by construction**, SQLite verified end-to-end. The
   runner adds no dialect-specific code: it reuses `env.py`'s URL resolution, and the
   schema inspector reads `alembic_version` through the SQLAlchemy dialect. PostgreSQL
   is not exercised locally (CI runs the Postgres service job).
5. Scope unchanged (`SPEC-001`) - **PASS** (entrypoint + readiness only; the readiness
   probe is the ticket's explicitly-invited companion fix)
6. Minimal change (PRIN-IX) - **PASS** (no refactors; `/api/v1/health` semantics and the
   image HEALTHCHECK deliberately untouched)

**Verdict: PASS with 1 WATCH.**

WATCH (carry to the next retro): the fix was written before its regression tests, so no
red-run is recorded ahead of the green (`TEST-014`). The reproduction is nonetheless
encoded as a test -
`test_fresh_database_is_not_ready_until_migrations_run` asserts the exact bug shape
(alive but 503 / unmigrated, then ready and 200 after the upgrade), and the original
failure was reproduced manually in Docker before the change.

## Decisions

- **Programmatic Alembic config over shipping `alembic.ini`.** Deriving
  `script_location` from the package path keeps one code path correct in the image, a
  checkout and a wheel, and avoids shipping a config whose `script_location` is relative
  to a backend root that does not exist in the image.
- **A separate readiness endpoint, not a schema check inside `/health`.** The
  conservative half of the ticket's "your call": the image HEALTHCHECK and any existing
  monitor keep their current liveness semantics, and traffic-gating callers get a probe
  that actually answers "can this serve a request". Making `/health` schema-dependent
  would have flipped an existing contract and could crash-loop a container whose DB is
  briefly unreachable.
- **Readiness reads `alembic_version`, not a business table.** It is the source of truth
  for "migrations applied", stays correct as the schema grows, and exposes the revision,
  which is the one detail that makes a 503 actionable.
- **Migration failure exits non-zero.** Failing the start loudly is strictly better than
  the reported symptom: a "healthy" container serving 500s.

## Entries

- `18:20 · claude/OPUS · GATE: full mechanical gate green (backend lint/format/type/imports/coverage/audit + frontend lint/format/type/test); docker fresh-volume and restart verification green · Makefile targets · QG-004`
- `18:15 · claude/OPUS · docs: README quickstart documents start-time migrations + the two probes; docker-compose.yml comments mark the healthcheck as liveness-only · README.md, docker-compose.yml · -`
- `18:05 · claude/OPUS · VERIFY: built the production image, ran it on a fresh volume (schema created before bind, /api/v1/plants 200, db 81920 bytes), then created a plant and restarted (idempotent no-op, data intact, healthy) · Dockerfile · VIRIDARIUM-67`
- `17:55 · claude/OPUS · GREEN: readiness probe added end-to-end (domain SchemaInspector/ReadinessProbe ports, GetReadinessStatus use case, SqlAlchemySchemaInspector, GET /api/v1/health/ready 200/503) + 2 unit and 6 integration tests · domain/health.py, application/health.py, adapters/outbound/db/schema_inspector.py, adapters/inbound/web/health.py · PRIN-III`
- `17:45 · claude/OPUS · GREEN: entrypoint applies migrations before uvicorn binds (programmatic Alembic config, python -m viridarium.migrate, docker-entrypoint.sh exec'ing the CMD) · infrastructure/migrations.py, migrate.py, backend/docker-entrypoint.sh, Dockerfile · VIRIDARIUM-67`
- `17:40 · claude/OPUS · root cause confirmed: image CMD went straight to uvicorn so migrations never ran, and /api/v1/health never touches the DB so HEALTHCHECK passed on a schemaless database; alembic.ini is absent from the runtime image, ruling out a plain CLI call · Dockerfile · -`
- `17:35 · claude/OPUS · intake: filed BUG-010 from the office Mac mini report; verified against git log that no fix exists on main (3a633bc) · bugs/BUG-010-prod-image-never-runs-migrations.md · VIRIDARIUM-67`
