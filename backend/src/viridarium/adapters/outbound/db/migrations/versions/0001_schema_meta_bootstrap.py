"""schema_meta bootstrap

Creates a single bootstrap table, ``schema_meta``, so the very first migration runs
real DDL on both SQLite and PostgreSQL (ARCH-011). It carries no domain data; domain
tables arrive in later migrations. This proves ``alembic upgrade head`` actually
executes DDL on both engines, which is the risk ARCH-011 guards against.

Revision ID: 0001
Revises:
Create Date: 2026-06-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schema_meta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("key", name="key"),
    )
    op.bulk_insert(
        sa.table(
            "schema_meta",
            sa.column("id", sa.Integer),
            sa.column("key", sa.String),
            sa.column("value", sa.String),
        ),
        [{"id": 1, "key": "bootstrap", "value": "ok"}],
    )


def downgrade() -> None:
    op.drop_table("schema_meta")
