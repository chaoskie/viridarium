"""SQLAlchemy ORM models (ADR-A/ADR-B [TEMPLATE]: all ORM models live here).

Portable column types only (ARCH-011) so the same DDL runs on SQLite and PostgreSQL.
Timestamps are server-set (ADR-A): ``created_at`` defaults to ``func.now()`` and
``updated_at`` carries an app-side ``onupdate`` so a row's modification time bumps on
write. The named primary key (``pk_location`` via the shared naming convention) keeps
constraint names stable for SQLite Alembic batch mode.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
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


class PlantModel(Base):
    """A plant row (US-2.1).

    ``location_id`` is a nullable FK with ``ON DELETE SET NULL`` (D1): deleting a room
    orphans its plants to homeless rather than cascading a delete. Enums are stored as
    ``String(20)`` (D3, no native DB enum types - portable). ``archived`` carries a
    DB-level ``server_default`` false. Timestamps are server-set (ADR-A), mirroring
    ``LocationModel``. The FK action only fires on SQLite with the ``foreign_keys``
    pragma (set in ``engine.py``).
    """

    __tablename__ = "plant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("location.id", ondelete="SET NULL"),
        nullable=True,
    )
    acquired_on: Mapped[date | None] = mapped_column(Date(), nullable=True)
    pot_size_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pot_material: Mapped[str | None] = mapped_column(String(20), nullable=True)
    light_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(10000), nullable=True)
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=func.false()
    )
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


class PlantTagModel(Base):
    """A normalized plant tag row (D2): composite PK ``(plant_id, tag)``.

    Owned child of ``plant`` with ``ON DELETE CASCADE`` so tags are removed with their
    plant. A child table (not a JSON column) keeps the ``?tag=`` filter portable via a
    SQL ``EXISTS`` subquery (ARCH-011).
    """

    __tablename__ = "plant_tag"

    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plant.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(50), primary_key=True)


class PhotoModel(Base):
    """A plant photo's metadata row (US-2.3).

    Owned child of ``plant`` with ``ON DELETE CASCADE`` so a plant delete removes the
    rows (the files are unlinked app-level, P6). ``stored_filename`` is the
    server-generated on-disk name (UUID + sniffed ext) and is unique. ``plant_id`` is
    indexed for the per-plant list. Photos are immutable, so there is no ``updated_at``
    (only the server-set ``created_at``, ADR-A). ``is_cover`` carries a DB-level
    ``server_default`` false; the single-cover invariant is enforced in the repository.
    """

    __tablename__ = "photo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_cover: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=func.false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CareScheduleModel(Base):
    """A plant's care schedule row (US-3.1).

    Owned child of ``plant`` with ``ON DELETE CASCADE`` so a plant delete removes its
    schedule rows. A surrogate ``id`` PK plus a ``(plant_id, care_type)`` unique
    constraint enforces one schedule per care type (the keyed-PUT upsert is the only
    write path, CS1). Enums are stored as ``String`` (D3, portable - no native DB enum
    types, ARCH-011). ``enabled`` carries a DB-level ``server_default`` true.
    ``winter_interval_days`` is nullable (CS3). ``plant_id`` is indexed for the
    per-plant list. Timestamps are server-set (ADR-A), mirroring ``PlantModel``.
    """

    __tablename__ = "care_schedule"
    __table_args__ = (
        UniqueConstraint(
            "plant_id", "care_type", name="uq_care_schedule_plant_id_care_type"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    care_type: Mapped[str] = mapped_column(String(10), nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    winter_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dormancy: Mapped[str] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=func.true()
    )
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
