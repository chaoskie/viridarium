#!/bin/sh
# Container entrypoint (VIRIDARIUM-67).
#
# Applies database migrations BEFORE the server binds, so a fresh volume never serves a
# request against a schemaless database. `alembic upgrade head` is idempotent, so this
# is safe on every start, including restart loops. `set -e` means a failed migration
# aborts the start instead of leaving a "healthy" container with no tables.
#
# The CMD is exec'd afterwards, so uvicorn keeps PID 1 and receives signals directly,
# and `docker run <image> <other command>` still works.
set -e

python -m viridarium.migrate

exec "$@"
