"""Engine and session factory, derived from a single SQLAlchemy URL.

The single-URL abstraction isolates dialect differences (ARCH-011): SQLite needs
``check_same_thread=False`` so the file engine can be shared across the threadpool
FastAPI uses for sync routes; PostgreSQL needs no special connect args here.

SQLite also disables foreign-key enforcement by default - ``ON DELETE SET NULL`` and
``ON DELETE CASCADE`` silently no-op unless ``PRAGMA foreign_keys=ON`` is issued per
connection (D1). A ``connect`` event listener applies it for SQLite engines only
(engine-isolated, harmless to PostgreSQL which enforces FKs natively). Without it the
``plant.location_id`` SET NULL and ``plant_tag`` CASCADE actions diverge between
engines - a cross-engine correctness bug (ARCH-011).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    """Issue ``PRAGMA foreign_keys=ON`` on each new SQLite connection (D1)."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def create_db_engine(database_url: str) -> Engine:
    """Create an :class:`~sqlalchemy.Engine` for the given URL.

    Applies SQLite-only connect args and the SQLite-only foreign-key pragma listener;
    other dialects use defaults.
    """
    connect_args: dict[str, object] = {}
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    if is_sqlite:
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to ``engine``."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
