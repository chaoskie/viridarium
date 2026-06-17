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
            # additive cachepot columns from 0008 (plant-cachepot); the head column set.
            "outer_pot_material",
            "outer_pot_size_cm",
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


def test_upgrade_creates_photo_table_and_downgrade_drops_it(
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        inspector = inspect(engine)
        assert "photo" in set(inspector.get_table_names())

        cols = {col["name"] for col in inspector.get_columns("photo")}
        assert cols == {
            "id",
            "plant_id",
            "stored_filename",
            "content_type",
            "size_bytes",
            "is_cover",
            "created_at",
        }
        assert "updated_at" not in cols  # photos immutable

        photo_fks = inspector.get_foreign_keys("photo")
        plant_fk = next(fk for fk in photo_fks if fk["referred_table"] == "plant")
        assert plant_fk["options"].get("ondelete") == "CASCADE"

        indexes = inspector.get_indexes("photo")
        index_cols = [idx["column_names"] for idx in indexes]
        assert ["plant_id"] in index_cols  # ix_photo_plant_id

        uniques = {
            tuple(uc["column_names"])
            for uc in inspector.get_unique_constraints("photo")
        }
        unique_indexes = {
            tuple(idx["column_names"]) for idx in indexes if idx["unique"]
        }
        assert ("stored_filename",) in (uniques | unique_indexes)

        command.downgrade(cfg, "0003")
        after = set(inspect(engine).get_table_names())
        assert "photo" not in after
        assert "plant" in after
        assert "plant_tag" in after
    finally:
        engine.dispose()


def test_upgrade_creates_care_schedule_table_and_downgrade_drops_it(
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        inspector = inspect(engine)
        assert "care_schedule" in set(inspector.get_table_names())

        cols = {col["name"] for col in inspector.get_columns("care_schedule")}
        assert cols == {
            "id",
            "plant_id",
            "care_type",
            "interval_days",
            "winter_interval_days",
            "dormancy",
            "enabled",
            "created_at",
            "updated_at",
        }

        fks = inspector.get_foreign_keys("care_schedule")
        plant_fk = next(fk for fk in fks if fk["referred_table"] == "plant")
        assert plant_fk["options"].get("ondelete") == "CASCADE"

        indexes = inspector.get_indexes("care_schedule")
        index_cols = [idx["column_names"] for idx in indexes]
        assert ["plant_id"] in index_cols  # ix_care_schedule_plant_id

        uniques = {
            tuple(uc["column_names"])
            for uc in inspector.get_unique_constraints("care_schedule")
        }
        unique_indexes = {
            tuple(idx["column_names"]) for idx in indexes if idx["unique"]
        }
        # the structural half of the AC2 uniqueness headline
        assert ("plant_id", "care_type") in (uniques | unique_indexes)

        command.downgrade(cfg, "0004")
        after = set(inspect(engine).get_table_names())
        assert "care_schedule" not in after
        assert "photo" in after
        assert "plant" in after
    finally:
        engine.dispose()


def test_upgrade_creates_care_event_table_and_downgrade_drops_it(  # B-I37
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        inspector = inspect(engine)
        assert "care_event" in set(inspector.get_table_names())

        cols = {col["name"] for col in inspector.get_columns("care_event")}
        assert cols == {
            "id",
            "plant_id",
            "type",
            "happened_on",
            "note",
            "photo_id",
            "health",
            "created_at",
        }
        assert "updated_at" not in cols  # events immutable (append-only)

        fks = inspector.get_foreign_keys("care_event")
        plant_fk = next(fk for fk in fks if fk["referred_table"] == "plant")
        assert plant_fk["options"].get("ondelete") == "CASCADE"
        photo_fk = next(fk for fk in fks if fk["referred_table"] == "photo")
        assert photo_fk["options"].get("ondelete") == "SET NULL"

        indexes = inspector.get_indexes("care_event")
        index_cols = [idx["column_names"] for idx in indexes]
        assert ["plant_id"] in index_cols  # ix_care_event_plant_id

        command.downgrade(cfg, "0005")
        after = set(inspect(engine).get_table_names())
        assert "care_event" not in after
        assert "care_schedule" in after
        assert "photo" in after
        assert "plant" in after
        assert "plant_tag" in after
    finally:
        engine.dispose()


def test_upgrade_creates_app_settings_table_and_downgrade_drops_it(  # B-I7
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        from sqlalchemy import text

        inspector = inspect(engine)
        assert "app_settings" in set(inspector.get_table_names())

        cols = {col["name"] for col in inspector.get_columns("app_settings")}
        assert cols == {
            "id",
            "seasonal_aware",
            "start_month",
            "start_day",
            "end_month",
            "end_day",
            "updated_at",
        }

        pk = inspector.get_pk_constraint("app_settings")
        assert pk["constrained_columns"] == ["id"]

        # No row is seeded - the lazy default lives in the service (proposal).
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM app_settings")).scalar()
        assert count == 0

        command.downgrade(cfg, "0006")
        after = set(inspect(engine).get_table_names())
        assert "app_settings" not in after
        assert "care_event" in after
        assert "care_schedule" in after
        assert "photo" in after
        assert "plant" in after
        assert "plant_tag" in after
    finally:
        engine.dispose()


# ---------------------------------- cachepot columns (0008, plant-cachepot, AC3) -----
# The pre-0008 plant column set (the 0003 columns); 0008 adds exactly the two new ones.
_PRE_0008_PLANT_COLS = {
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
_CACHEPOT_COLS = {"outer_pot_material", "outer_pot_size_cm"}


def test_upgrade_adds_cachepot_columns_and_downgrade_drops_them(  # M1 + M2
    sqlite_url: str,
) -> None:
    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    command.upgrade(cfg, "head")
    try:
        # M1: head adds exactly the two nullable cachepot columns to ``plant``.
        cols = {col["name"]: col for col in inspect(engine).get_columns("plant")}
        assert set(cols) == _PRE_0008_PLANT_COLS | _CACHEPOT_COLS
        assert cols["outer_pot_material"]["nullable"] is True
        assert cols["outer_pot_size_cm"]["nullable"] is True

        # M2: downgrade to 0007 drops exactly the two columns (batch-mode reversible);
        # the table and all 0003 columns survive.
        command.downgrade(cfg, "0007")
        after = {col["name"] for col in inspect(engine).get_columns("plant")}
        assert after == _PRE_0008_PLANT_COLS
        assert "plant" in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_existing_plant_row_gets_null_cachepot_columns_on_upgrade(  # M3
    sqlite_url: str,
) -> None:
    from sqlalchemy import text

    cfg = make_alembic_config(sqlite_url)
    engine = create_engine(sqlite_url)

    # Seed a plant row at 0007 (before the cachepot columns exist), then upgrade.
    command.upgrade(cfg, "0007")
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO plant (name, archived) VALUES ('Legacy', 0)")
            )

        command.upgrade(cfg, "head")

        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT outer_pot_material, outer_pot_size_cm "
                    "FROM plant WHERE name = 'Legacy'"
                )
            ).one()
        # No backfill, no default (D3): the existing row reads back null/null.
        assert row.outer_pot_material is None
        assert row.outer_pot_size_cm is None
    finally:
        engine.dispose()
