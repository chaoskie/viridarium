"""create care_event table

The append-only care-event table (US-3.2). Portable column types and a server-default
``created_at`` (ARCH-011 / ADR-A) so the same DDL runs on SQLite and PostgreSQL. Events
are immutable (AC4), so there is no ``updated_at``. ``plant_id`` is a non-null FK to
``plant`` with ``ON DELETE CASCADE``: the history dies with the plant (like photos).
``photo_id`` is a nullable FK to ``photo`` with ``ON DELETE SET NULL``: deleting the
linked photo severs the link but preserves the event. ``type`` and ``health`` are
stored as ``String`` (D3, portable - no native DB enum types), enum-validated at the
edge. ``plant_id`` is indexed for the per-plant list. Constraint/index names follow
the metadata naming convention for SQLite Alembic batch mode.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "care_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("happened_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=10000), nullable=True),
        sa.Column("photo_id", sa.Integer(), nullable=True),
        sa.Column("health", sa.String(length=10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_care_event"),
        sa.ForeignKeyConstraint(
            ["plant_id"],
            ["plant.id"],
            name="fk_care_event_plant_id_plant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["photo_id"],
            ["photo.id"],
            name="fk_care_event_photo_id_photo",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_care_event_plant_id", "care_event", ["plant_id"])


def downgrade() -> None:
    op.drop_index("ix_care_event_plant_id", table_name="care_event")
    op.drop_table("care_event")
