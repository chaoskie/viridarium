"""create care_schedule table

The care-schedule table (US-3.1). Portable column types and server-default timestamps
(ARCH-011 / ADR-A) so the same DDL runs on SQLite and PostgreSQL. ``plant_id`` is a
non-null FK to ``plant`` with ``ON DELETE CASCADE``: deleting a plant removes its
schedule rows (no app-level cleanup - no files this story). A surrogate ``id`` PK plus a
``(plant_id, care_type)`` unique constraint enforces one schedule per care type (the
keyed-PUT upsert is the only write path, CS1). Enums are stored as ``String`` (D3,
portable - no native DB enum types). ``enabled`` carries a server-default true.
``winter_interval_days`` is nullable (CS3). ``plant_id`` is indexed for the per-plant
list. Constraint/index names follow the metadata naming convention for SQLite Alembic
batch mode.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "care_schedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("care_type", sa.String(length=10), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("winter_interval_days", sa.Integer(), nullable=True),
        sa.Column("dormancy", sa.String(length=20), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.true(),
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
        sa.PrimaryKeyConstraint("id", name="pk_care_schedule"),
        sa.ForeignKeyConstraint(
            ["plant_id"],
            ["plant.id"],
            name="fk_care_schedule_plant_id_plant",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "plant_id", "care_type", name="uq_care_schedule_plant_id_care_type"
        ),
    )
    op.create_index("ix_care_schedule_plant_id", "care_schedule", ["plant_id"])


def downgrade() -> None:
    op.drop_index("ix_care_schedule_plant_id", table_name="care_schedule")
    op.drop_table("care_schedule")
