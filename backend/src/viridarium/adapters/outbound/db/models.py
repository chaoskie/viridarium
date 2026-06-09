"""SQLAlchemy ORM models (ADR-A/ADR-B [TEMPLATE]: all ORM models live here).

Portable column types only (ARCH-011) so the same DDL runs on SQLite and PostgreSQL.
Timestamps are server-set (ADR-A): ``created_at`` defaults to ``func.now()`` and
``updated_at`` carries an app-side ``onupdate`` so a row's modification time bumps on
write. The named primary key (``pk_location`` via the shared naming convention) keeps
constraint names stable for SQLite Alembic batch mode.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from viridarium.adapters.outbound.db.base import Base


class LocationModel(Base):
    """A room/location row."""

    __tablename__ = "location"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
