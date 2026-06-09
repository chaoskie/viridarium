"""Integration tests for the /api/v1/plants/{id}/photos surface (TEST-001 primary).

A real-DB slice through router -> PhotoService -> SqlAlchemyPhotoRepository ->
SQLAlchemy -> SQLite, PLUS the real filesystem PhotoStorage adapter writing into a
``tmp_path`` (TEST-003: nothing internal mocked). This is the headline security-bearing
layer: the upload-validation rejects (413/415x3), cross-plant 404, traversal-safe
naming, cover semantics, and the plant-delete file cleanup are all proven end-to-end
against a real filesystem. Each test seeds its own plant via the API (TEST-006).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"

# Smallest-valid magic-byte payloads (no committed binaries, no PII).
JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 8
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
WEBP_BYTES = b"RIFF" + (24).to_bytes(4, "little") + b"WEBPVP8 " + b"\x00" * 8
GIF_BYTES = b"GIF89a" + b"\x00" * 8
TEXT_BYTES = b"this is definitely not an image"

_EXPECTED_RESPONSE_KEYS = {
    "id",
    "plant_id",
    "content_type",
    "size_bytes",
    "is_cover",
    "created_at",
    "url",
}


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _photos_url(plant_id: int) -> str:
    return f"{_PLANTS}/{plant_id}/photos"


def _upload(
    client: TestClient,
    plant_id: int,
    *,
    data: bytes = JPEG_BYTES,
    filename: str = "x.jpg",
    content_type: str = "image/jpeg",
) -> object:
    return client.post(
        _photos_url(plant_id),
        files={"file": (filename, data, content_type)},
    )


# --------------------------------------------------------------------- happy upload
def test_upload_jpeg_returns_201_and_metadata(client: TestClient) -> None:
    plant_id = _make_plant(client)

    response = _upload(client, plant_id)

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == _EXPECTED_RESPONSE_KEYS
    assert "stored_filename" not in body  # security boundary (ARCH-007/AC11)
    assert body["plant_id"] == plant_id
    assert body["content_type"] == "image/jpeg"
    assert body["size_bytes"] == len(JPEG_BYTES)
    assert body["is_cover"] is True
    assert body["url"] == f"{_photos_url(plant_id)}/{body['id']}"


def test_upload_png_and_webp_round_trip(client: TestClient) -> None:
    plant_id = _make_plant(client)

    png = _upload(
        client, plant_id, data=PNG_BYTES, filename="a.png", content_type="image/png"
    )
    webp = _upload(
        client, plant_id, data=WEBP_BYTES, filename="a.webp", content_type="image/webp"
    )

    assert png.status_code == 201
    assert png.json()["content_type"] == "image/png"
    assert webp.status_code == 201
    assert webp.json()["content_type"] == "image/webp"


def test_get_bytes_round_trips(client: TestClient) -> None:
    plant_id = _make_plant(client)
    photo_id = _upload(client, plant_id).json()["id"]

    response = client.get(f"{_photos_url(plant_id)}/{photo_id}")

    assert response.status_code == 200
    assert response.content == JPEG_BYTES
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == ("private, max-age=31536000, immutable")


def test_list_newest_first(client: TestClient) -> None:
    plant_id = _make_plant(client)
    ids = [_upload(client, plant_id).json()["id"] for _ in range(3)]

    listed = client.get(_photos_url(plant_id))

    assert listed.status_code == 200
    assert [p["id"] for p in listed.json()] == list(reversed(ids))


def test_first_upload_is_cover(client: TestClient) -> None:
    plant_id = _make_plant(client)
    body = _upload(client, plant_id).json()
    assert body["is_cover"] is True


def test_set_cover_flips_exactly_one(client: TestClient) -> None:
    plant_id = _make_plant(client)
    first = _upload(client, plant_id).json()["id"]
    second = _upload(client, plant_id).json()["id"]

    flip = client.post(f"{_photos_url(plant_id)}/{second}/cover")

    assert flip.status_code == 200
    listed = client.get(_photos_url(plant_id)).json()
    covers = [p["id"] for p in listed if p["is_cover"]]
    assert covers == [second]
    assert first not in covers


def test_delete_then_get_404_and_file_gone(
    client: TestClient, photos_dir: Path
) -> None:
    plant_id = _make_plant(client)
    photo_id = _upload(client, plant_id).json()["id"]
    files_before = list(photos_dir.iterdir())
    assert len(files_before) == 1

    deleted = client.delete(f"{_photos_url(plant_id)}/{photo_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"{_photos_url(plant_id)}/{photo_id}").status_code == 404
    assert list(photos_dir.iterdir()) == []  # file unlinked


def test_cover_promotion_on_delete(client: TestClient) -> None:
    plant_id = _make_plant(client)
    cover = _upload(client, plant_id).json()["id"]
    _upload(client, plant_id)
    newest = _upload(client, plant_id).json()["id"]

    client.delete(f"{_photos_url(plant_id)}/{cover}")

    listed = client.get(_photos_url(plant_id)).json()
    assert [p["id"] for p in listed if p["is_cover"]] == [newest]


# ------------------------------------------------------------- security / sad rejects
def test_upload_oversize_returns_413(client: TestClient) -> None:
    plant_id = _make_plant(client)
    oversize = JPEG_BYTES + b"\x00" * 4096  # > photos_max_bytes (small in conftest)

    response = _upload(client, plant_id, data=oversize)

    assert response.status_code == 413
    assert set(response.json().keys()) == {"detail"}


def test_upload_declared_text_plain_returns_415(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = _upload(
        client,
        plant_id,
        data=TEXT_BYTES,
        filename="x.txt",
        content_type="text/plain",
    )
    assert response.status_code == 415
    assert "x.txt" not in response.text  # no PII / filename echo (SEC-007)


def test_upload_wrong_magic_text_body_returns_415(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = _upload(client, plant_id, data=TEXT_BYTES)  # declared jpeg, body text
    assert response.status_code == 415


def test_upload_wrong_magic_gif_body_returns_415(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = _upload(client, plant_id, data=GIF_BYTES)  # declared jpeg, body gif
    assert response.status_code == 415


def test_upload_declared_sniff_mismatch_returns_415(client: TestClient) -> None:
    plant_id = _make_plant(client)
    # body is jpeg, declared png -> declared/sniff cross-check
    response = _upload(
        client,
        plant_id,
        data=JPEG_BYTES,
        filename="x.png",
        content_type="image/png",
    )
    assert response.status_code == 415


def test_upload_missing_plant_returns_404(client: TestClient) -> None:
    response = _upload(client, 999999)
    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


def test_upload_no_file_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.post(_photos_url(plant_id))
    assert response.status_code == 422


def test_get_missing_photo_returns_404(client: TestClient) -> None:
    plant_id = _make_plant(client)
    assert client.get(f"{_photos_url(plant_id)}/4242").status_code == 404


def test_cover_missing_photo_returns_404(client: TestClient) -> None:
    plant_id = _make_plant(client)
    assert client.post(f"{_photos_url(plant_id)}/4242/cover").status_code == 404


def test_delete_missing_photo_returns_404(client: TestClient) -> None:
    plant_id = _make_plant(client)
    assert client.delete(f"{_photos_url(plant_id)}/4242").status_code == 404


def test_get_cross_plant_photo_returns_404(client: TestClient) -> None:
    plant_a = _make_plant(client, "A")
    plant_b = _make_plant(client, "B")
    photo_id = _upload(client, plant_a).json()["id"]

    response = client.get(f"{_photos_url(plant_b)}/{photo_id}")

    assert response.status_code == 404  # cross-plant isolation (no ownership -> 404)


def test_cover_cross_plant_returns_404(client: TestClient) -> None:
    plant_a = _make_plant(client, "A")
    plant_b = _make_plant(client, "B")
    photo_id = _upload(client, plant_a).json()["id"]

    assert client.post(f"{_photos_url(plant_b)}/{photo_id}/cover").status_code == 404


def test_delete_cross_plant_returns_404(client: TestClient) -> None:
    plant_a = _make_plant(client, "A")
    plant_b = _make_plant(client, "B")
    photo_id = _upload(client, plant_a).json()["id"]

    assert client.delete(f"{_photos_url(plant_b)}/{photo_id}").status_code == 404


def test_path_traversal_safe_naming(client: TestClient, photos_dir: Path) -> None:
    plant_id = _make_plant(client)

    response = _upload(client, plant_id, filename="../../etc/evil.jpg")

    assert response.status_code == 201
    files = list(photos_dir.iterdir())
    assert len(files) == 1
    stored = files[0]
    assert stored.suffix == ".jpg"
    assert ".." not in stored.name
    assert "evil" not in stored.name
    # no file escaped the photos dir, no traversal entry anywhere under it
    for entry in photos_dir.rglob("*"):
        assert "evil" not in entry.name
        assert ".." not in entry.name
    # the malicious string never reaches the response either
    assert "evil" not in response.text


# ------------------------------------------------------------- plant-delete cleanup
def test_plant_delete_cleans_photo_files(client: TestClient, photos_dir: Path) -> None:
    plant_id = _make_plant(client)
    for _ in range(3):
        _upload(client, plant_id)
    assert len(list(photos_dir.iterdir())) == 3

    deleted = client.delete(f"{_PLANTS}/{plant_id}")

    assert deleted.status_code == 204
    # rows gone (CASCADE): a fresh list is empty, and the files are unlinked
    assert client.get(_photos_url(plant_id)).json() == []
    assert list(photos_dir.iterdir()) == []  # files unlinked, not orphaned


# --------------------------------------------------------------------------- OpenAPI
def test_openapi_exposes_photo_paths_and_schema_omits_stored_filename(
    client: TestClient,
) -> None:
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/plants/{plant_id}/photos" in paths
    assert "/api/v1/plants/{plant_id}/photos/{photo_id}" in paths
    assert "/api/v1/plants/{plant_id}/photos/{photo_id}/cover" in paths

    props = schema["components"]["schemas"]["PhotoResponse"]["properties"]
    assert set(props.keys()) == _EXPECTED_RESPONSE_KEYS
    assert "stored_filename" not in props
