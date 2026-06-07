"""Engine and session factory, derived from a single SQLAlchemy URL.

The single-URL abstraction isolates dialect differences (ARCH-011): SQLite needs
``check_same_thread=False`` so the file engine can be shared across the threadpool
FastAPI uses for sync routes; PostgreSQL needs no special connect args here.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(database_url: str) -> Engine:
    """Create an :class:`~sqlalchemy.Engine` for the given URL.

    Applies SQLite-only connect args; other dialects use defaults.
    """
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to ``engine``."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
