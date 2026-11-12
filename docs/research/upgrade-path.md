# Research: Docker upgrade path (2026-07-06)

Status: research. Input for future specs on migration safety and on
[D-015](../decisions/D-015-update-check-and-self-update.md) part B.

## Done

**Automatic migrations on start** shipped in #68 (BUG-010): the entrypoint runs
`alembic upgrade head` before the server starts, a failed migration aborts the start,
and a fresh volume provisions itself. See the [README](../README.md). This matches what
Immich, Paperless and Grafana do.

## Not built yet

- **Opt-out and explicit mode.** `RUN_MIGRATIONS=false` to skip on start, plus a
  `migrate` subcommand that runs migrations and exits. Useful for multi-replica
  PostgreSQL: one migrate job, replicas with the opt-out.
- **PostgreSQL concurrency.** Wrap `run_migrations_online()` in `pg_advisory_lock` with a
  fixed key, PostgreSQL branch only (about ten lines; other projects hit this exact race
  with concurrent starts). Document the caveat that advisory locks do not work through
  PgBouncer transaction pooling. SQLite's single writer needs nothing, optionally a
  `busy_timeout`.
- **Pre-upgrade backup, SQLite only.** If the current revision is not head and the
  database is not empty, snapshot it with `sqlite3.Connection.backup()` (safe with WAL,
  unlike a file copy) to `/data/backups/app.db.pre-<from>-<to>.<timestamp>` and keep the
  last five. For PostgreSQL, document `pg_dump`.
- **Downgrade story (documentation).** The supported rollback is: restore the snapshot
  and run the previous image tag. `alembic downgrade` stays available but is not the
  promoted path.
- Rejected as a default: a compose init-container for migrations. It doubles the
  quickstart complexity and does nothing for plain `docker run`.

## Update tooling guidance

- **Never bundle an updater in the default compose file.** Other projects warn against
  unattended updaters, and breaking migrations before 1.0 make them a bad default.
- Documentation ladder:
  1. Read the release notes, then `docker compose pull && docker compose up -d`.
  2. Notify only: diun or WUD. Pairs with the in-app check from D-015 part A.
  3. Automatic updates, opt-in and with a warning. `containrrr/watchtower` was archived
     in December 2025; use the maintained `nicholas-fedor/watchtower` fork or WUD's
     Docker trigger.
- **Fit for D-015 part B.** Watchtower's HTTP API mode validates the sidecar direction:
  a token-protected `POST /v1/update`, polling off by default in API mode (weekly
  automatic updates via `--http-api-periodic-polls`), scoped with `--label-enable`. A
  minimal alternative is a small webhook sidecar that runs `compose pull && up -d` behind
  a token. Either way the app container stays socket-free.

## Image tags

`publish.yml` already pushes `X.Y.Z` plus rolling `X.Y`, `X` and `latest`. Still open:

- an optional `edge` tag built from `main` for soak instances,
- pinning the shipped compose example to a minor tag with a comment, and recommending
  `X.Y` over `X` before 1.0,
- a cumulative breaking-changes list in the release notes.
