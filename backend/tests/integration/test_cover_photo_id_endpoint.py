"""Integration tests for the additive ``cover_photo_id`` on the plant reads (AC3).

Real-DB slice through router -> services -> repositories -> SQLAlchemy -> SQLite plus
the real filesystem PhotoStorage (TEST-003). Proves ``GET /plants`` and
``GET /plants/{id}`` carry the cover photo id (or null), that the field is additive
(no other shape change, OpenAPI), and that the list path's cover assembly stays bounded
regardless of plant count (no N+1), asserted via the statement-count listener.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"

# Smallest-valid magic-byte payload (mirrors test_photos_endpoint).
JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 8


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _upload(client: TestClient, plant_id: int, filename: str = "x.jpg") -> int:
    response = client.post(
        f"{_PLANTS}/{plant_id}/photos",
        files={"file": (filename, JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 201, response.text
    photo_id: int = response.json()["id"]
    return photo_id


# ====================================================== detail endpoint (AC3)
def test_detail_includes_cover_photo_id(client: TestClient) -> None:
    """GET /plants/{id} carries the plant's cover photo id."""
    plant_id = _make_plant(client)
    cover_id = _upload(client, plant_id)  # first upload becomes the cover

    body = client.get(f"{_PLANTS}/{plant_id}").json()

    assert body["cover_photo_id"] == cover_id


def test_detail_cover_photo_id_null_when_no_photos(client: TestClient) -> None:
    """GET /plants/{id} returns ``cover_photo_id: null`` when the plant has no cover."""
    plant_id = _make_plant(client)

    body = client.get(f"{_PLANTS}/{plant_id}").json()

    assert body["cover_photo_id"] is None


# ====================================================== list endpoint (AC3)
def test_list_includes_cover_photo_id_per_plant(client: TestClient) -> None:
    """GET /plants carries each plant's own cover id; null for the photo-less plant."""
    with_cover = _make_plant(client, "WithCover")
    no_photos = _make_plant(client, "NoPhotos")
    cover_id = _upload(client, with_cover)

    listed = client.get(_PLANTS).json()
    by_id = {p["id"]: p for p in listed}

    assert by_id[with_cover]["cover_photo_id"] == cover_id
    assert by_id[no_photos]["cover_photo_id"] is None


@contextmanager
def _listen(engine: Engine) -> Iterator[list[int]]:
    counter = [0]

    def _on_execute(*_args: object, **_kwargs: object) -> None:
        counter[0] += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)


def _cover_assembly_statements(client: TestClient, plant_ids: list[int]) -> int:
    """Count statements the cover batch issues for a page of plant ids.

    Exercises the wired photo repository's ``cover_ids_for_plants`` over the real engine
    (the same path GET /plants uses for the cover composition) and counts only that
    portion, which the fix pins as constant across plant counts.
    """
    engine = client.app.state.container.engine  # type: ignore[attr-defined]
    repo = client.app.state.container.photo_service._repository  # type: ignore[attr-defined]
    with _listen(engine) as counter:
        repo.cover_ids_for_plants(plant_ids)
    return counter[0]


def test_list_cover_query_count_bounded_regardless_of_plant_count(
    client: TestClient,
) -> None:
    """The list-path cover assembly does not scale with plant count (AC3, no N+1)."""
    n_ids: list[int] = []
    for i in range(5):
        pid = _make_plant(client, f"N{i}")
        _upload(client, pid)
        n_ids.append(pid)
    n_count = _cover_assembly_statements(client, n_ids)

    two_n_ids = list(n_ids)
    for i in range(5):
        pid = _make_plant(client, f"M{i}")
        _upload(client, pid)
        two_n_ids.append(pid)
    two_n_count = _cover_assembly_statements(client, two_n_ids)

    assert n_count <= 2  # the single grouped read (+ at most one connection setup)
    assert two_n_count == n_count  # flat: no per-plant cover query

    # End-to-end sanity: the list endpoint actually carries the cover ids.
    listed = client.get(_PLANTS).json()
    assert all("cover_photo_id" in p for p in listed)
    assert any(p["cover_photo_id"] is not None for p in listed)


# ====================================================== contract (AC3 additive)
def test_openapi_exposes_additive_cover_photo_id_field(client: TestClient) -> None:
    """PlantResponse.cover_photo_id is an additive nullable-integer field."""
    schema = client.get("/api/v1/openapi.json").json()
    plant_props = schema["components"]["schemas"]["PlantResponse"]["properties"]
    assert "cover_photo_id" in plant_props


def test_cover_photo_id_does_not_disturb_other_fields(client: TestClient) -> None:
    """The field is purely additive: schedules + the scalar shape are untouched."""
    plant_id = _make_plant(client)
    body = client.get(f"{_PLANTS}/{plant_id}").json()
    assert "schedules" in body  # the US-3.3 field still present
    assert body["cover_photo_id"] is None
