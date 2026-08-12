"""The container entrypoint's migration path (VIRIDARIUM-67).

The production image ships no ``alembic.ini``, so the entrypoint builds the Alembic
config in code. These tests exercise exactly that code path against a real, fresh
SQLite file: schema created, restart-safe (idempotent), and readiness flipping from 503
to 200 as a result.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from viridarium.infrastructure.app import create_app
from viridarium.infrastructure.migrations import SCRIPT_LOCATION, upgrade_to_head
from viridarium.infrastructure.settings import Settings
from viridarium.migrate import main as migrate_main

pytestmark = pytest.mark.integration


def test_script_location_points_at_the_shipped_migrations_tree() -> None:
    # Derived from the package location, so it resolves inside the image too.
    assert (SCRIPT_LOCATION / "env.py").is_file()
    assert (SCRIPT_LOCATION / "versions" / "0001_schema_meta_bootstrap.py").is_file()


def test_upgrade_to_head_creates_the_schema_on_a_fresh_database(
    sqlite_url: str,
) -> None:
    upgrade_to_head(sqlite_url)

    engine = create_engine(sqlite_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert "plant" in tables
        assert "alembic_version" in tables
    finally:
        engine.dispose()


def test_upgrade_to_head_is_idempotent_across_restarts(sqlite_url: str) -> None:
    upgrade_to_head(sqlite_url)
    # A restart loop re-runs the entrypoint; the second pass must be a no-op, not an
    # error and not a duplicate-DDL failure.
    upgrade_to_head(sqlite_url)

    engine = create_engine(sqlite_url)
    try:
        assert "plant" in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migrate_entrypoint_exits_zero_and_migrates_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = f"sqlite:///{tmp_path / 'entrypoint.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    # Settings are process-cached; the entrypoint runs in a fresh process, tests do not.
    from viridarium.infrastructure.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "viridarium.migrate.get_settings", lambda: Settings(database_url=url)
    )

    assert migrate_main() == 0

    engine = create_engine(url)
    try:
        assert "plant" in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
    get_settings.cache_clear()


def test_migrate_entrypoint_exits_nonzero_when_the_migration_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An unreachable/invalid URL must fail the start loudly rather than boot a
    # schemaless server (the VIRIDARIUM-67 symptom).
    monkeypatch.setattr(
        "viridarium.migrate.get_settings",
        lambda: Settings(database_url="postgresql+psycopg://u:p@127.0.0.1:1/none"),
    )

    assert migrate_main() == 1


def test_fresh_database_is_not_ready_until_migrations_run(
    tmp_path: Path, photos_dir: Path
) -> None:
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    settings = Settings(
        database_url=url, version="test-1.2.3", photos_dir=str(photos_dir)
    )

    with TestClient(create_app(settings=settings)) as unmigrated_client:
        # Liveness still passes on a schemaless DB - that is by design, and is why the
        # readiness probe exists.
        assert unmigrated_client.get("/api/v1/health").status_code == 200
        not_ready = unmigrated_client.get("/api/v1/health/ready")
        assert not_ready.status_code == 503
        assert not_ready.json() == {
            "status": "not-ready",
            "version": "test-1.2.3",
            "schema_revision": None,
        }

    upgrade_to_head(url)

    with TestClient(create_app(settings=settings)) as migrated_client:
        ready = migrated_client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        body = ready.json()
        assert body["status"] == "ready"
        assert body["schema_revision"] is not None
        # And the DB-touching endpoint that used to 500 now answers.
        assert migrated_client.get("/api/v1/plants").status_code == 200
