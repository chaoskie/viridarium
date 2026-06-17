"""add cachepot (outer pot) columns to plant

Additive, non-breaking (plant-cachepot, AC3). Adds two nullable columns to the ``plant``
table for the decorative outer pot (cachepot): ``outer_pot_material`` (``String(20)``,
the enum stored as a string per D3) and ``outer_pot_size_cm`` (``Integer``). Both are
nullable with no default - null = "no cachepot" (D3); existing rows read back null/null,
no backfill. ``op.batch_alter_table`` is used so the change is SQLite-safe (batch mode
rebuilds the table portably) as well as PostgreSQL-safe (ARCH-011). The downgrade drops
both columns. Portable column types only, same DDL on both engines.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("plant") as batch_op:
        batch_op.add_column(
            sa.Column("outer_pot_material", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(sa.Column("outer_pot_size_cm", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("plant") as batch_op:
        batch_op.drop_column("outer_pot_size_cm")
        batch_op.drop_column("outer_pot_material")
