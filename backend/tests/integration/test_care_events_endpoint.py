"""Integration tests for the /api/v1/plants/{id}/events surface (TEST-001 primary).

A real-DB slice through router -> CareEventService -> SqlAlchemyCareEventRepository ->
SQLAlchemy -> SQLite (TEST-003: nothing internal mocked). Per the care-events test
foundation §4 this is the primary layer: the create happy inventory, the field matrices
(M1 happened_on, M2 type x health, M3 note, M4 photo_id), the ordering contract
(``happened_on`` desc then ``created_at`` desc), delete, the 404 plant-reason + no-PII
discipline, the append-only invariant (no update route, OpenAPI cross-check), and the
photo-deletion-nulls-link behaviour. Each test seeds its own plant (and photo where
needed) via the API (TEST-006). Case ids (B-In) cite the foundation.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from tests.integration.test_photos_endpoint import JPEG_BYTES

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"

_EXPECTED_RESPONSE_KEYS = {
    "id",  # unlike CareSchedule, exposed: DELETE is keyed by event id
    "plant_id",
    "type",
    "happened_on",
    "note",
    "photo_id",
    "health",
    "created_at",
}


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _events_url(plant_id: int) -> str:
    return f"{_PLANTS}/{plant_id}/events"


def _upload_photo(client: TestClient, plant_id: int) -> int:
    response = client.post(
        f"{_PLANTS}/{plant_id}/photos",
        files={"file": ("x.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 201
    photo_id: int = response.json()["id"]
    return photo_id


# ------------------------------------------------------- create happy (§4a, AC1/AC2)
def test_create_water_returns_201_and_body(client: TestClient) -> None:  # B-I1
    plant_id = _make_plant(client)

    response = client.post(_events_url(plant_id), json={"type": "water"})

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == _EXPECTED_RESPONSE_KEYS
    assert body["plant_id"] == plant_id
    assert body["type"] == "water"
    assert body["happened_on"] == date.today().isoformat()  # default (M1 omitted)
    assert body["note"] is None
    assert body["photo_id"] is None
    assert body["health"] is None
    assert body["created_at"] is not None


@pytest.mark.parametrize("event_type", ["feed", "repot"])
def test_create_other_types(client: TestClient, event_type: str) -> None:  # B-I2/B-I3
    plant_id = _make_plant(client)

    response = client.post(_events_url(plant_id), json={"type": event_type})

    assert response.status_code == 201
    assert response.json()["type"] == event_type


def test_create_observe_without_health(client: TestClient) -> None:  # B-I4
    plant_id = _make_plant(client)

    response = client.post(_events_url(plant_id), json={"type": "observe"})

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "observe"
    assert body["health"] is None


def test_create_observe_with_health(client: TestClient) -> None:  # B-I5
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "observe", "health": "good"}
    )

    assert response.status_code == 201
    assert response.json()["health"] == "good"


def test_create_with_past_happened_on(client: TestClient) -> None:  # B-I6
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "water", "happened_on": "2026-01-01"}
    )

    assert response.status_code == 201
    assert response.json()["happened_on"] == "2026-01-01"  # backdating allowed


def test_create_with_today_happened_on(client: TestClient) -> None:  # B-I7
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id),
        json={"type": "water", "happened_on": date.today().isoformat()},
    )

    assert response.status_code == 201  # today is the boundary, allowed


def test_create_with_note(client: TestClient) -> None:  # B-I8
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "observe", "note": "leaf drop"}
    )

    assert response.status_code == 201
    assert response.json()["note"] == "leaf drop"


def test_create_with_max_length_note(client: TestClient) -> None:  # B-I9
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "water", "note": "x" * 10000}
    )

    assert response.status_code == 201  # boundary inclusive


def test_create_with_same_plant_photo(client: TestClient) -> None:  # B-I10
    plant_id = _make_plant(client)
    photo_id = _upload_photo(client, plant_id)

    response = client.post(
        _events_url(plant_id), json={"type": "observe", "photo_id": photo_id}
    )

    assert response.status_code == 201
    assert response.json()["photo_id"] == photo_id


# ----------------------------------------------- matrix M1: happened_on (§4b, AC3)
@pytest.mark.parametrize(
    "days_ahead",
    [pytest.param(1, id="future"), pytest.param(365, id="far-future")],
)
def test_future_happened_on_returns_422(  # B-I11 / B-I12
    client: TestClient, days_ahead: int
) -> None:
    plant_id = _make_plant(client)
    future = (date.today() + timedelta(days=days_ahead)).isoformat()

    response = client.post(
        _events_url(plant_id), json={"type": "water", "happened_on": future}
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}


def test_malformed_happened_on_returns_422(client: TestClient) -> None:  # B-I13
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "water", "happened_on": "not-a-date"}
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}


# -------------------------------------- matrix M2: type x health (§4c, AC3 CRITICAL)
@pytest.mark.parametrize(
    ("event_type", "health", "expected_status"),
    [
        pytest.param("water", None, 201, id="water-no-health"),
        pytest.param("feed", None, 201, id="feed-no-health"),
        pytest.param("repot", None, 201, id="repot-no-health"),
        pytest.param("observe", None, 201, id="observe-no-health"),
        pytest.param("observe", "good", 201, id="observe-good"),
        pytest.param("observe", "fair", 201, id="observe-fair"),
        pytest.param("observe", "bad", 201, id="observe-bad"),
        pytest.param("observe", "meh", 422, id="observe-invalid-health"),
        pytest.param("water", "good", 422, id="water-with-health"),
        pytest.param("feed", "good", 422, id="feed-with-health"),
        pytest.param("repot", "good", 422, id="repot-with-health"),
        pytest.param("prune", None, 422, id="unknown-type"),
    ],
)
def test_type_health_matrix(  # B-I14
    client: TestClient, event_type: str, health: str | None, expected_status: int
) -> None:
    plant_id = _make_plant(client)
    body: dict[str, object] = {"type": event_type}
    if health is not None:
        body["health"] = health

    response = client.post(_events_url(plant_id), json=body)

    assert response.status_code == expected_status
    if expected_status == 201:
        stored = response.json()
        assert stored["type"] == event_type
        assert stored["health"] == health
    else:
        assert set(response.json().keys()) == {"detail"}


# --------------------------------------------------------- matrix M3: note (§4d)
def test_create_with_empty_note(client: TestClient) -> None:  # B-I15
    plant_id = _make_plant(client)

    response = client.post(_events_url(plant_id), json={"type": "water", "note": ""})

    assert response.status_code == 201
    assert response.json()["note"] == ""  # empty accepted as-is (no normalization)


def test_create_with_over_max_note_returns_422(client: TestClient) -> None:  # B-I16
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "water", "note": "x" * 10001}
    )

    assert response.status_code == 422


# ------------------------------------------- matrix M4: photo_id (§4e, AC3 CRITICAL)
def test_cross_plant_photo_returns_422(client: TestClient) -> None:  # B-I17
    plant_a = _make_plant(client, name="Plant Alpha")
    plant_b = _make_plant(client, name="Plant Beta")
    photo_of_b = _upload_photo(client, plant_b)

    response = client.post(
        _events_url(plant_a), json={"type": "observe", "photo_id": photo_of_b}
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}
    assert "Plant Alpha" not in response.text  # neither plant's name leaks
    assert "Plant Beta" not in response.text


def test_nonexistent_photo_returns_422(client: TestClient) -> None:  # B-I18
    plant_id = _make_plant(client)

    response = client.post(
        _events_url(plant_id), json={"type": "observe", "photo_id": 999999}
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}


# ------------------------------------------------- list + ordering (§4f, AC4)
def test_list_empty_when_none(client: TestClient) -> None:  # B-I19
    plant_id = _make_plant(client)

    response = client.get(_events_url(plant_id))

    assert response.status_code == 200
    assert response.json() == []


def test_list_newest_first_by_created_at(client: TestClient) -> None:  # B-I20
    plant_id = _make_plant(client)
    for note in ("first", "second", "third"):
        client.post(_events_url(plant_id), json={"type": "water", "note": note})

    listed = client.get(_events_url(plant_id)).json()

    # Same happened_on (today): created_at desc tiebreak -> reverse insertion order.
    assert [e["note"] for e in listed] == ["third", "second", "first"]


def test_list_orders_happened_on_desc(client: TestClient) -> None:  # B-I21
    plant_id = _make_plant(client)
    client.post(_events_url(plant_id), json={"type": "water", "note": "today"})
    client.post(
        _events_url(plant_id),
        json={"type": "water", "happened_on": "2026-01-01", "note": "past"},
    )

    listed = client.get(_events_url(plant_id)).json()

    # happened_on desc dominates created_at: today first despite older created_at.
    assert [e["note"] for e in listed] == ["today", "past"]


def test_backdated_entries_sort_by_full_tuple(client: TestClient) -> None:  # B-I22
    """ORDERING CONTRACT headline: insertion order is wrong under either single key;
    only ``(happened_on desc, created_at desc)`` yields the asserted order."""
    plant_id = _make_plant(client)
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    client.post(_events_url(plant_id), json={"type": "water", "note": "A-today"})
    client.post(
        _events_url(plant_id),
        json={"type": "water", "happened_on": "2026-01-01", "note": "B-far-past"},
    )
    client.post(
        _events_url(plant_id),
        json={"type": "water", "happened_on": yesterday, "note": "C-yesterday"},
    )
    client.post(_events_url(plant_id), json={"type": "water", "note": "D-today"})

    listed = client.get(_events_url(plant_id)).json()

    # happened_on desc groups (today, yesterday, far past); created_at desc within.
    assert [e["note"] for e in listed] == [
        "D-today",
        "A-today",
        "C-yesterday",
        "B-far-past",
    ]


# ------------------------------------------------------------- delete (§4g, AC4)
def test_delete_then_list_excludes_it(client: TestClient) -> None:  # B-I23
    plant_id = _make_plant(client)
    event_id = client.post(_events_url(plant_id), json={"type": "water"}).json()["id"]

    deleted = client.delete(f"{_events_url(plant_id)}/{event_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(_events_url(plant_id)).json() == []


def test_delete_leaves_siblings(client: TestClient) -> None:  # B-I24
    plant_id = _make_plant(client)
    first = client.post(_events_url(plant_id), json={"type": "water"}).json()["id"]
    second = client.post(_events_url(plant_id), json={"type": "feed"}).json()["id"]

    assert client.delete(f"{_events_url(plant_id)}/{first}").status_code == 204

    listed = client.get(_events_url(plant_id)).json()
    assert [e["id"] for e in listed] == [second]


def test_delete_missing_event_returns_404(client: TestClient) -> None:  # B-I25
    plant_id = _make_plant(client)

    response = client.delete(f"{_events_url(plant_id)}/4242")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


def test_delete_cross_plant_event_returns_404(client: TestClient) -> None:  # B-I26
    plant_a = _make_plant(client, name="Plant A")
    plant_b = _make_plant(client, name="Plant B")
    a_event = client.post(_events_url(plant_a), json={"type": "water"}).json()["id"]

    response = client.delete(f"{_events_url(plant_b)}/{a_event}")

    assert response.status_code == 404  # cross-plant isolation
    assert [e["id"] for e in client.get(_events_url(plant_a)).json()] == [a_event]


# ------------------------------- 404 plant-reason + no-PII (§4h, AC3 CRITICAL)
def test_create_unknown_plant_returns_404_plant_reason(  # B-I27
    client: TestClient,
) -> None:
    response = client.post(f"{_PLANTS}/999999/events", json={"type": "water"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Plant 999999 not found"  # VIRIDARIUM-48


def test_list_unknown_plant_returns_404_plant_reason(client: TestClient) -> None:
    response = client.get(f"{_PLANTS}/999999/events")  # B-I28

    assert response.status_code == 404
    assert response.json()["detail"] == "Plant 999999 not found"


def test_delete_unknown_plant_returns_404_plant_reason(client: TestClient) -> None:
    response = client.delete(f"{_PLANTS}/999999/events/1")  # B-I29

    assert response.status_code == 404
    # the plant guard precedes the missing-event check
    assert response.json()["detail"] == "Plant 999999 not found"


def test_reject_leaks_neither_plant_name_nor_note(client: TestClient) -> None:
    plant_id = _make_plant(client, name="Secret Orchid")  # B-I30

    response = client.post(
        _events_url(plant_id),
        json={"type": "water", "health": "good", "note": "distinctive-note-xyzzy"},
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}
    assert "Secret Orchid" not in response.text  # SEC-007
    assert "distinctive-note-xyzzy" not in response.text


def test_missing_event_404_no_pii(client: TestClient) -> None:  # B-I31
    plant_id = _make_plant(client, name="Secret Orchid")

    response = client.delete(f"{_events_url(plant_id)}/4242")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}
    assert "Secret Orchid" not in response.text


# --------------------------------------- append-only invariant (§4i, AC4 CRITICAL)
def test_no_update_route_exists(client: TestClient) -> None:  # B-I32
    plant_id = _make_plant(client)
    event_id = client.post(_events_url(plant_id), json={"type": "water"}).json()["id"]

    put = client.put(f"{_events_url(plant_id)}/{event_id}", json={"type": "feed"})
    patch = client.patch(f"{_events_url(plant_id)}/{event_id}", json={"type": "feed"})

    assert put.status_code in (404, 405)  # events are immutable
    assert patch.status_code in (404, 405)


def test_openapi_exposes_only_append_only_surface(client: TestClient) -> None:
    spec = client.get("/api/v1/openapi.json").json()  # B-I33

    paths = spec["paths"]
    collection = "/api/v1/plants/{plant_id}/events"
    keyed = "/api/v1/plants/{plant_id}/events/{event_id}"
    assert collection in paths
    assert keyed in paths
    assert {"post", "get"} <= set(paths[collection].keys())
    assert "delete" in paths[keyed]
    assert not {"put", "patch"} & set(paths[collection].keys())
    assert not {"put", "patch"} & set(paths[keyed].keys())

    props = spec["components"]["schemas"]["CareEventResponse"]["properties"]
    assert set(props.keys()) == _EXPECTED_RESPONSE_KEYS  # includes id/photo_id/health


# ----------------------------------- photo deletion nulls the link (§4j)
def test_deleting_linked_photo_nulls_event_photo_id(client: TestClient) -> None:
    plant_id = _make_plant(client)  # B-I34
    photo_id = _upload_photo(client, plant_id)
    event_id = client.post(
        _events_url(plant_id), json={"type": "observe", "photo_id": photo_id}
    ).json()["id"]

    deleted = client.delete(f"{_PLANTS}/{plant_id}/photos/{photo_id}")
    assert deleted.status_code == 204

    listed = client.get(_events_url(plant_id)).json()
    assert [e["id"] for e in listed] == [event_id]  # history preserved
    assert listed[0]["photo_id"] is None  # link severed (SET NULL)
