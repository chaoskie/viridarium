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


def test_upgrade_creates_plant_tables_and_downgrade_drops_them(
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "plant" in tables
        assert "plant_tag" in tables

        plant_cols = {col["name"] for col in inspector.get_columns("plant")}
        assert plant_cols == {
            "id",
            "name",
            "species",
            "location_id",
            "acquired_on",
            "pot_size_cm",
            "pot_material",
            "light_level",
            "notes",
            "archived",
            "created_at",
            "updated_at",
        }
        tag_cols = {col["name"] for col in inspector.get_columns("plant_tag")}
        assert tag_cols == {"plant_id", "tag"}

        plant_fks = inspector.get_foreign_keys("plant")
        loc_fk = next(fk for fk in plant_fks if fk["referred_table"] == "location")
        assert loc_fk["options"].get("ondelete") == "SET NULL"

        tag_fks = inspector.get_foreign_keys("plant_tag")
        plant_fk = next(fk for fk in tag_fks if fk["referred_table"] == "plant")
        assert plant_fk["options"].get("ondelete") == "CASCADE"

        command.downgrade(cfg, "0002")
        after = set(inspect(engine).get_table_names())
        assert "plant" not in after
        assert "plant_tag" not in after
        assert "location" in after
        assert "schema_meta" in after
    finally:
        engine.dispose()
