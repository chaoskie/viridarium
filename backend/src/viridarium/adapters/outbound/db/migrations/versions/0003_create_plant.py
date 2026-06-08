"""create plant and plant_tag tables

The second domain entity (US-2.1). Portable column types and server-default timestamps
(ARCH-011 / ADR-A) so the same DDL runs on SQLite and PostgreSQL. ``plant.location_id``
is a nullable FK to ``location`` with ``ON DELETE SET NULL`` (D1): deleting a room
orphans its plants to homeless. ``plant_tag`` is the normalized tags child (D2) with a
composite PK ``(plant_id, tag)`` and an ``ON DELETE CASCADE`` FK to ``plant``. Enums are
stored as ``String(20)`` (D3). Constraint names follow the metadata naming convention so
SQLite Alembic batch mode names them consistently. The per-write ``updated_at`` bump is
app-side ORM ``onupdate`` (not a DB constraint), so it is not expressed in the DDL.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("species", sa.String(length=200), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("acquired_on", sa.Date(), nullable=True),
        sa.Column("pot_size_cm", sa.Integer(), nullable=True),
        sa.Column("pot_material", sa.String(length=20), nullable=True),
        sa.Column("light_level", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.String(length=10000), nullable=True),
        sa.Column(
            "archived",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_plant"),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["location.id"],
            name="fk_plant_location_id_location",
            ondelete="SET NULL",
        ),
    )
    op.create_table(
        "plant_tag",
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("plant_id", "tag", name="pk_plant_tag"),
        sa.ForeignKeyConstraint(
            ["plant_id"],
            ["plant.id"],
            name="fk_plant_tag_plant_id_plant",
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    # Drop the child table first so the FK to ``plant`` does not block the drop.
    op.drop_table("plant_tag")
    op.drop_table("plant")
