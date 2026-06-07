"""Alembic migration environment.

Dual-engine aware (ARCH-011): the URL is resolved from application settings
(``DATABASE_URL`` env var, SQLite default), and ``render_as_batch`` is enabled for
SQLite so future ALTERs that SQLite cannot perform natively are emitted as batch
(copy-and-move) operations.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from plant_care.adapters.outbound.db.base import Base
from plant_care.adapters.outbound.db.engine import create_db_engine
from plant_care.infrastructure.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the database URL.

    Prefers a URL set programmatically on the Alembic config (used by tests and
    tooling that target a specific database); otherwise falls back to application
    settings, which read ``DATABASE_URL`` from the environment (never hardcoded;
    SEC-006).
    """
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    return get_settings().database_url


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live connection)."""
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite(url),
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live engine."""
    url = _database_url()
    engine = create_db_engine(url)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=_is_sqlite(url),
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
