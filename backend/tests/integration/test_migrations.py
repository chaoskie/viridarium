"""Migration smoke test (ARCH-011): upgrade head then downgrade base on SQLite.

Proves the initial migration runs real DDL on the default engine and is reversible.
The PostgreSQL path is exercised by CI against a Postgres service (cicd.md); this test
guards the always-available SQLite path.
"""

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect

from tests.integration.conftest import make_alembic_config

pytestmark = pytest.mark.integration


def test_upgrade_creates_schema_meta_and_downgrade_drops_it(sqlite_url: str) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        tables_after_upgrade = set(inspect(engine).get_table_names())
        assert "schema_meta" in tables_after_upgrade

        command.downgrade(cfg, "base")
        tables_after_downgrade = set(inspect(engine).get_table_names())
        assert "schema_meta" not in tables_after_downgrade
    finally:
        engine.dispose()


def test_upgrade_creates_location_table_and_downgrade_drops_it(sqlite_url: str) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        inspector = inspect(engine)
        assert "location" in set(inspector.get_table_names())
        columns = {col["name"] for col in inspector.get_columns("location")}
        assert columns == {"id", "name", "notes", "created_at", "updated_at"}

        command.downgrade(cfg, "0001")
        tables_after_downgrade = set(inspect(engine).get_table_names())
        assert "location" not in tables_after_downgrade
        assert "schema_meta" in tables_after_downgrade
    finally:
        engine.dispose()
