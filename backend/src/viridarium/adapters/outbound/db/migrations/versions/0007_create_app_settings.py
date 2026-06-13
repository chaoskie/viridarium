"""create app_settings table

The singleton app-settings table (US-3.5). One row (``id = 1``) holds the global
``seasonal_aware`` toggle plus the configurable winter window (month/day endpoints).
Portable column types only (ARCH-011) so the same DDL runs on SQLite and PostgreSQL:
``seasonal_aware`` is Boolean (SQLite has no native boolean), the month/day columns are
SmallInteger, and ``updated_at`` is a server-default timestamp (ADR-A). **No row is
seeded** - the lazy default (Nov 1 - Mar 1, ``seasonal_aware=True``) lives in the
service, avoiding cross-engine seed quirks. The down-migration drops the table. The PK
constraint name follows the metadata naming convention for SQLite Alembic batch mode.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("seasonal_aware", sa.Boolean(), nullable=False),
        sa.Column("start_month", sa.SmallInteger(), nullable=False),
        sa.Column("start_day", sa.SmallInteger(), nullable=False),
        sa.Column("end_month", sa.SmallInteger(), nullable=False),
        sa.Column("end_day", sa.SmallInteger(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_settings"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
