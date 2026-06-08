"""create location table

The first domain table (US-2.2). Portable column types and server-default timestamps
(ARCH-011 / ADR-A) so the same DDL runs on SQLite and PostgreSQL. The primary key is
named ``pk_location`` (matching the metadata naming convention) so SQLite Alembic batch
mode names it consistently. ``updated_at`` carries a server default for the create case;
the per-write bump is app-side ORM ``onupdate`` (not a DB constraint), so it is not
expressed in the DDL.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "location",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.String(length=2000), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_location"),
    )


def downgrade() -> None:
    op.drop_table("location")
