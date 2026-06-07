"""Integration tests for the optional SPA static mount (product-spec section 7).

The single-container image serves the built React app and the API from one process.
These tests prove: the API still wins over the catch-all mount, ``index.html`` is served
at ``/`` (and for unknown client-side routes) when a static dir is configured, and the
mount is a no-op when no static dir exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from viridarium.infrastructure.app import create_app
from viridarium.infrastructure.settings import Settings
from viridarium.infrastructure.static import mount_spa

pytestmark = pytest.mark.integration

_INDEX_HTML = "<!doctype html><title>viridarium</title><div id=root></div>"


@pytest.fixture
def static_settings(sqlite_url: str, tmp_path: Path) -> Settings:
    """Settings pointed at a temp directory holding a built ``index.html``."""
    static_dir = tmp_path / "spa"
    static_dir.mkdir()
    (static_dir / "index.html").write_text(_INDEX_HTML, encoding="utf-8")
    (static_dir / "asset.js").write_text("export const x = 1;", encoding="utf-8")
    return Settings(
        database_url=sqlite_url,
        version="test-1.2.3",
        static_dir=str(static_dir),
    )


def test_mount_spa_is_noop_when_dir_missing() -> None:
    app = create_app(
        settings=Settings(database_url="sqlite://", static_dir="/no/such/dir")
    )
    assert mount_spa(app, None) is False
    assert mount_spa(app, "/no/such/dir") is False


def test_index_served_at_root(static_settings: Settings) -> None:
    app = create_app(settings=static_settings)
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "viridarium" in response.text


def test_unknown_client_route_falls_back_to_index(static_settings: Settings) -> None:
    app = create_app(settings=static_settings)
    with TestClient(app) as client:
        response = client.get("/plants/42")

    # StaticFiles(html=True) serves index.html for unknown paths so the SPA router
    # can take over client-side.
    assert response.status_code == 200
    assert "viridarium" in response.text


def test_static_asset_is_served(static_settings: Settings) -> None:
    app = create_app(settings=static_settings)
    with TestClient(app) as client:
        response = client.get("/asset.js")

    assert response.status_code == 200
    assert "export const x" in response.text


def test_api_takes_precedence_over_static(static_settings: Settings) -> None:
    app = create_app(settings=static_settings)
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "test-1.2.3"}
