"""Unit tests for the photo use case (TEST-002: no app, no DB, no I/O).

``PhotoService`` is exercised against hand-written fakes of the ``PhotoRepository`` and
``PhotoStorage`` ports (TEST-003: faking the port is allowed). The fakes mirror the
``_FakePlantRepository`` pattern and record the ``save``/``delete`` call order so the
orchestration contract (P2 pipeline ordering, P5 cover/promotion, storage-after-repo on
delete) is observable without standing up the app.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from viridarium.application.photos import PhotoService
from viridarium.domain.photo import (
    NewPhoto,
    Photo,
    PhotoNotFoundError,
    PhotoTooLargeError,
    UnsupportedImageTypeError,
)
from viridarium.domain.plant import PlantNotFoundError

pytestmark = pytest.mark.unit

_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + b"\x00" * 8
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_GIF = b"GIF89a" + b"\x00" * 8
_TEXT = b"this is not an image at all"


class _FakePhotoStorage:
    """In-memory fake of the PhotoStorage port; records call order."""

    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}
        self.calls: list[tuple[str, str]] = []
        self._n = 0

    def save(self, data: bytes, *, suffix: str) -> str:
        self._n += 1
        name = f"fake{self._n}.{suffix}"
        self.saved[name] = data
        self.calls.append(("save", name))
        return name

    def delete(self, stored_filename: str) -> None:
        self.calls.append(("delete", stored_filename))
        self.saved.pop(stored_filename, None)


class _FakePhotoRepository:
    """Dict-backed fake of the PhotoRepository port; records call order."""

    def __init__(self, existing_plant_ids: set[int] | None = None) -> None:
        self._rows: dict[int, Photo] = {}
        self._next_id = 1
        self._plants = existing_plant_ids if existing_plant_ids is not None else {1}
        self.calls: list[tuple[str, int]] = []
        self._clock = datetime(2026, 6, 10, tzinfo=UTC)

    def _now(self) -> datetime:
        self._clock += timedelta(seconds=1)
        return self._clock

    def plant_exists(self, plant_id: int) -> bool:
        return plant_id in self._plants

    def add(self, new_photo: NewPhoto, *, make_cover: bool) -> Photo:
        if make_cover:
            for pid, row in list(self._rows.items()):
                if row.plant_id == new_photo.plant_id and row.is_cover:
                    self._rows[pid] = _replace_cover(row, is_cover=False)
        photo = Photo(
            id=self._next_id,
            plant_id=new_photo.plant_id,
            stored_filename=new_photo.stored_filename,
            content_type=new_photo.content_type,
            size_bytes=new_photo.size_bytes,
            is_cover=make_cover,
            created_at=self._now(),
        )
        self._rows[self._next_id] = photo
        self.calls.append(("add", self._next_id))
        self._next_id += 1
        return photo

    def list_for_plant(self, plant_id: int) -> list[Photo]:
        rows = [p for p in self._rows.values() if p.plant_id == plant_id]
        return sorted(rows, key=lambda p: p.created_at, reverse=True)

    def get(self, plant_id: int, photo_id: int) -> Photo:
        row = self._rows.get(photo_id)
        if row is None or row.plant_id != plant_id:
            raise PhotoNotFoundError(plant_id, photo_id)
        return row

    def set_cover(self, plant_id: int, photo_id: int) -> Photo:
        target = self.get(plant_id, photo_id)
        for pid, row in list(self._rows.items()):
            if row.plant_id == plant_id:
                self._rows[pid] = _replace_cover(row, is_cover=row.id == photo_id)
        return self._rows[target.id]

    def delete(self, plant_id: int, photo_id: int) -> Photo:
        row = self.get(plant_id, photo_id)
        del self._rows[photo_id]
        self.calls.append(("delete", photo_id))
        if row.is_cover:
            survivors = self.list_for_plant(plant_id)
            if survivors:
                newest = survivors[0]
                self._rows[newest.id] = _replace_cover(newest, is_cover=True)
        return row

    def list_filenames_for_plant(self, plant_id: int) -> list[str]:
        return [
            p.stored_filename for p in self._rows.values() if p.plant_id == plant_id
        ]


def _replace_cover(photo: Photo, *, is_cover: bool) -> Photo:
    return Photo(
        id=photo.id,
        plant_id=photo.plant_id,
        stored_filename=photo.stored_filename,
        content_type=photo.content_type,
        size_bytes=photo.size_bytes,
        is_cover=is_cover,
        created_at=photo.created_at,
    )


def _service(
    *, plant_ids: set[int] | None = None, max_bytes: int = 1_000_000
) -> tuple[PhotoService, _FakePhotoRepository, _FakePhotoStorage]:
    repo = _FakePhotoRepository(existing_plant_ids=plant_ids)
    storage = _FakePhotoStorage()
    return PhotoService(repo, storage, max_bytes=max_bytes), repo, storage


# -------------------------------------------------------------------- upload (happy)
def test_upload_happy_persists_and_returns_metadata() -> None:
    service, _repo, storage = _service()

    photo = service.upload(1, _JPEG, declared_content_type="image/jpeg")

    assert photo.plant_id == 1
    assert photo.content_type == "image/jpeg"
    assert photo.size_bytes == len(_JPEG)
    assert photo.is_cover is True  # first upload
    assert len(storage.saved) == 1
    (name,) = storage.saved
    assert name.endswith(".jpg")


def test_upload_first_photo_becomes_cover() -> None:
    service, _repo, _storage = _service()
    photo = service.upload(1, _PNG, declared_content_type="image/png")
    assert photo.is_cover is True


def test_upload_second_photo_not_cover() -> None:
    service, _repo, _storage = _service()
    service.upload(1, _JPEG, declared_content_type="image/jpeg")
    second = service.upload(1, _PNG, declared_content_type="image/png")
    assert second.is_cover is False


# ---------------------------------------------------------------------- upload (sad)
def test_upload_oversize_raises_photo_too_large() -> None:
    service, repo, storage = _service(max_bytes=4)

    with pytest.raises(PhotoTooLargeError):
        service.upload(1, _JPEG, declared_content_type="image/jpeg")

    assert storage.calls == []  # nothing hit disk
    assert repo.calls == []


def test_upload_bad_magic_raises_unsupported() -> None:
    service, _repo, storage = _service()

    with pytest.raises(UnsupportedImageTypeError):
        service.upload(1, _TEXT, declared_content_type="image/jpeg")

    assert storage.calls == []


def test_upload_gif_body_raises_unsupported() -> None:
    service, _repo, storage = _service()

    with pytest.raises(UnsupportedImageTypeError):
        service.upload(1, _GIF, declared_content_type="image/gif")

    assert storage.calls == []


def test_upload_declared_sniff_mismatch_rejected() -> None:
    service, _repo, storage = _service()

    with pytest.raises(UnsupportedImageTypeError):
        # body is jpeg, declared png -> declared/sniff cross-check rejects
        service.upload(1, _JPEG, declared_content_type="image/png")

    assert storage.calls == []


def test_upload_disallowed_declared_type_rejected() -> None:
    service, _repo, storage = _service()

    with pytest.raises(UnsupportedImageTypeError):
        service.upload(1, _JPEG, declared_content_type="application/octet-stream")

    assert storage.calls == []


def test_upload_missing_plant_raises_plant_not_found() -> None:
    service, _repo, storage = _service(plant_ids=set())

    with pytest.raises(PlantNotFoundError):
        service.upload(99, _JPEG, declared_content_type="image/jpeg")

    assert storage.calls == []  # plant-exists checked first


# ------------------------------------------------------------------------- delete
def test_delete_promotes_newest_survivor_when_cover_removed() -> None:
    service, repo, _storage = _service()
    first = service.upload(1, _JPEG, declared_content_type="image/jpeg")  # cover
    service.upload(1, _PNG, declared_content_type="image/png")
    third = service.upload(1, _JPEG, declared_content_type="image/jpeg")
    assert first.is_cover is True

    service.delete(1, first.id)

    photos = service.list(1)
    covers = [p for p in photos if p.is_cover]
    assert len(covers) == 1
    assert covers[0].id == third.id  # newest survivor promoted


def test_delete_non_cover_leaves_cover_unchanged() -> None:
    service, _repo, _storage = _service()
    cover = service.upload(1, _JPEG, declared_content_type="image/jpeg")
    other = service.upload(1, _PNG, declared_content_type="image/png")

    service.delete(1, other.id)

    photos = service.list(1)
    assert [p.id for p in photos if p.is_cover] == [cover.id]


def test_delete_last_photo_leaves_no_cover() -> None:
    service, _repo, _storage = _service()
    only = service.upload(1, _JPEG, declared_content_type="image/jpeg")

    service.delete(1, only.id)

    assert service.list(1) == []


def test_delete_calls_storage_delete_after_repo_delete() -> None:
    service, repo, storage = _service()
    photo = service.upload(1, _JPEG, declared_content_type="image/jpeg")
    repo.calls.clear()
    storage.calls.clear()

    service.delete(1, photo.id)

    order = [c[0] for c in repo.calls] + [c[0] for c in storage.calls]
    # repo.delete must precede storage.delete (DB first, P5)
    assert repo.calls[0][0] == "delete"
    assert storage.calls[-1][0] == "delete"
    assert order.index("delete") == 0


def test_delete_missing_photo_raises() -> None:
    service, _repo, _storage = _service()
    with pytest.raises(PhotoNotFoundError):
        service.delete(1, 4242)


# ------------------------------------------------------------------- get / set_cover
def test_get_missing_raises_photo_not_found() -> None:
    service, _repo, _storage = _service()
    with pytest.raises(PhotoNotFoundError):
        service.get(1, 4242)


def test_set_cover_missing_raises_photo_not_found() -> None:
    service, _repo, _storage = _service()
    with pytest.raises(PhotoNotFoundError):
        service.set_cover(1, 4242)


def test_set_cover_flips_single_cover() -> None:
    service, _repo, _storage = _service()
    first = service.upload(1, _JPEG, declared_content_type="image/jpeg")
    second = service.upload(1, _PNG, declared_content_type="image/png")

    flipped = service.set_cover(1, second.id)

    assert flipped.is_cover is True
    photos = service.list(1)
    assert [p.id for p in photos if p.is_cover] == [second.id]
    assert first.id not in [p.id for p in photos if p.is_cover]
