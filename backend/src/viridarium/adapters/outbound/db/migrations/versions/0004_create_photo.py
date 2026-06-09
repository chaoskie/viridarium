"""create photo table

The photo metadata table (US-2.3). Portable column types and a server-default
``created_at`` (ARCH-011 / ADR-A) so the same DDL runs on SQLite and PostgreSQL. Photos
are immutable, so there is no ``updated_at``. ``plant_id`` is a non-null FK to ``plant``
with ``ON DELETE CASCADE`` (P1): deleting a plant removes its photo rows (the files are
unlinked app-level, P6). ``stored_filename`` is unique (the server-generated on-disk
name) and ``plant_id`` is indexed for the per-plant list. Constraint/index names follow
the metadata naming convention for SQLite Alembic batch mode.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "photo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "is_cover",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_photo"),
        sa.ForeignKeyConstraint(
            ["plant_id"],
            ["plant.id"],
            name="fk_photo_plant_id_plant",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("stored_filename", name="uq_photo_stored_filename"),
    )
    op.create_index("ix_photo_plant_id", "photo", ["plant_id"])


def downgrade() -> None:
    op.drop_index("ix_photo_plant_id", table_name="photo")
    op.drop_table("photo")
