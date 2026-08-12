"""Schema-state adapter backing the readiness probe (VIRIDARIUM-67).

Reads the Alembic bookkeeping table rather than probing a business table: it is the
single source of truth for "were migrations applied", it stays correct as the schema
grows, and it costs one indexed row read.
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from viridarium.domain.health import SchemaInspector


class SqlAlchemySchemaInspector(SchemaInspector):
    """Report the applied migration revision for the configured database."""

    _ALEMBIC_VERSION_TABLE = "alembic_version"

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def current_revision(self) -> str | None:
        """Return the applied revision, or ``None`` when unmigrated or unreachable.

        A missing table, an empty version table and an unreachable database are all the
        same answer for a readiness probe: not ready. They are deliberately not
        distinguished in the response body (SEC-001: no internal detail on the trust
        boundary); the exception detail stays in the server logs.
        """
        try:
            with self._engine.connect() as connection:
                if not self._engine.dialect.has_table(
                    connection, self._ALEMBIC_VERSION_TABLE
                ):
                    return None
                revision = connection.execute(
                    text(f"SELECT version_num FROM {self._ALEMBIC_VERSION_TABLE}")  # noqa: S608
                ).scalar()
        except SQLAlchemyError:
            return None
        return str(revision) if revision is not None else None
