"""Integration tests for the /api/v1/locations CRUD surface (TEST-001 primary layer).

A real-DB slice through router -> service -> repository -> SQLAlchemy -> SQLite
exercises validation, ordering, persistence round-trip, and 404/422 mapping. Nothing
internal is mocked (TEST-003); each test creates the rows it needs via the API within
its own temp-file SQLite ``client`` (TEST-006 independence).
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

_LOCATIONS = "/api/v1/locations"
_OVER_MAX_NOTES = "x" * 2001


# --------------------------------------------------------------------------- POST
def test_post_creates_location_and_round_trips(client: TestClient) -> None:
    response = client.post(_LOCATIONS, json={"name": "Greenhouse", "notes": "south"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Greenhouse"
    assert body["notes"] == "south"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body

    fetched = client.get(f"{_LOCATIONS}/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_post_creates_location_without_notes(client: TestClient) -> None:
    response = client.post(_LOCATIONS, json={"name": "Attic"})

    assert response.status_code == 201
    assert response.json()["notes"] is None


# Shared validation matrix (test-foundation §1, cells C3-C9), run for POST and PUT.
_BAD_BODIES = [
    pytest.param({"name": "ok", "notes": _OVER_MAX_NOTES}, id="notes-over-max"),
    pytest.param({"name": ""}, id="empty-name-no-notes"),
    pytest.param({"name": "", "notes": "south"}, id="empty-name-valid-notes"),
    pytest.param(
        {"name": "", "notes": _OVER_MAX_NOTES}, id="empty-name-over-max-notes"
    ),
    pytest.param({"name": "   "}, id="whitespace-name-no-notes"),
    pytest.param({"name": "   ", "notes": "south"}, id="whitespace-name-valid-notes"),
    pytest.param(
        {"name": "   ", "notes": _OVER_MAX_NOTES}, id="whitespace-name-over-max-notes"
    ),
]


@pytest.mark.parametrize("body", _BAD_BODIES)
def test_post_validation_rejects_bad_body(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post(_LOCATIONS, json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("body", _BAD_BODIES)
def test_put_validation_rejects_bad_body(
    client: TestClient, body: dict[str, object]
) -> None:
    created = client.post(_LOCATIONS, json={"name": "seed"}).json()

    response = client.put(f"{_LOCATIONS}/{created['id']}", json=body)

    assert response.status_code == 422


# --------------------------------------------------------------------------- LIST
def test_list_returns_rooms_ordered_by_name(client: TestClient) -> None:
    for name in ("Shed", "Attic", "Balcony"):
        client.post(_LOCATIONS, json={"name": name})

    response = client.get(_LOCATIONS)

    assert response.status_code == 200
    assert [room["name"] for room in response.json()] == ["Attic", "Balcony", "Shed"]


def test_list_empty_store_returns_empty_array(client: TestClient) -> None:
    response = client.get(_LOCATIONS)

    assert response.status_code == 200
    assert response.json() == []


# ------------------------------------------------------------------------- GET one
def test_get_one_returns_location(client: TestClient) -> None:
    created = client.post(_LOCATIONS, json={"name": "Office"}).json()

    response = client.get(f"{_LOCATIONS}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Office"


def test_get_unknown_id_returns_404_no_pii(client: TestClient) -> None:
    response = client.get(f"{_LOCATIONS}/424242")

    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"detail"}
    assert "424242" in body["detail"]


# ----------------------------------------------------------------------------- PUT
def test_put_updates_name_notes_and_bumps_updated_at(client: TestClient) -> None:
    created = client.post(_LOCATIONS, json={"name": "Old", "notes": "before"}).json()

    response = client.put(
        f"{_LOCATIONS}/{created['id']}", json={"name": "New", "notes": "after"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New"
    assert body["notes"] == "after"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] >= created["updated_at"]

    fetched = client.get(f"{_LOCATIONS}/{created['id']}").json()
    assert fetched["name"] == "New"
    assert fetched["notes"] == "after"


def test_put_unknown_id_returns_404(client: TestClient) -> None:
    response = client.put(f"{_LOCATIONS}/424242", json={"name": "Nope"})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


# -------------------------------------------------------------------------- DELETE
def test_delete_removes_location_then_get_404(client: TestClient) -> None:
    created = client.post(_LOCATIONS, json={"name": "Temp"}).json()

    deleted = client.delete(f"{_LOCATIONS}/{created['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"{_LOCATIONS}/{created['id']}").status_code == 404


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    response = client.delete(f"{_LOCATIONS}/424242")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


# ---------------------------------------------------------------------------- OpenAPI
def test_openapi_exposes_location_paths_and_schema(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json").json()

    assert "/api/v1/locations" in schema["paths"]
    assert "/api/v1/locations/{location_id}" in schema["paths"]
    response_schema = schema["components"]["schemas"]["LocationResponse"]
    assert set(response_schema["properties"].keys()) == {
        "id",
        "name",
        "notes",
        "created_at",
        "updated_at",
    }
