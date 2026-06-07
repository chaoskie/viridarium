"""Integration tests for the secure-by-default network posture (SEC-003)."""

import pytest
from fastapi.testclient import TestClient

from plant_care.infrastructure.app import create_app
from plant_care.infrastructure.settings import Settings

pytestmark = pytest.mark.integration


def test_cors_disabled_by_default(client: TestClient) -> None:
    # The default `client` fixture configures no origins; a cross-origin preflight
    # must not be granted an allow-origin header.
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_only_configured_origin(sqlite_url: str) -> None:
    settings = Settings(
        database_url=sqlite_url,
        cors_allow_origins=["https://app.example"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        allowed = client.get(
            "/api/v1/health", headers={"Origin": "https://app.example"}
        )
        assert allowed.headers["access-control-allow-origin"] == "https://app.example"
