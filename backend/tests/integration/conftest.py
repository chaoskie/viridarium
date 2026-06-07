"""Integration test fixtures: a wired app and migrated DB on a temp SQLite file.

Uses a real database and the real composition root (TEST-003): nothing internal is
mocked. Each test gets its own temp DB file so the suite is parallel-safe (TEST-006).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from plant_care.infrastructure.app import create_app
from plant_care.infrastructure.settings import Settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def make_alembic_config(database_url: str) -> Config:
    """Build an Alembic config pointed at ``database_url``."""
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option(
        "script_location",
        str(_BACKEND_ROOT / "src/plant_care/adapters/outbound/db/migrations"),
    )
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


@pytest.fixture
def sqlite_url(tmp_path: Path) -> str:
    """A file-backed SQLite URL unique to this test."""
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def migrated_settings(sqlite_url: str, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Settings whose database has migrations applied to head."""
    # env.py resolves the URL from settings via DATABASE_URL.
    monkeypatch.setenv("DATABASE_URL", sqlite_url)
    settings = Settings(database_url=sqlite_url, version="test-1.2.3")
    command.upgrade(make_alembic_config(sqlite_url), "head")
    return settings


@pytest.fixture
def client(migrated_settings: Settings) -> Iterator[TestClient]:
    """A TestClient backed by the wired app and a migrated database."""
    app = create_app(settings=migrated_settings)
    with TestClient(app) as test_client:
        yield test_client
