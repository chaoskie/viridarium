"""Integration test: boot the wired app against SQLite and hit /api/v1/health."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_health_returns_ok_and_version(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "test-1.2.3"}


def test_health_carries_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers


def test_unknown_route_is_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404


def test_openapi_docs_are_served_under_v1(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json")

    assert schema.status_code == 200
    assert "/api/v1/health" in schema.json()["paths"]
