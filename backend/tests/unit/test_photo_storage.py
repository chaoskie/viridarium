"""Unit tests for the filesystem photo storage adapter (traversal guard, P1/SEC).

These exercise the security-critical paths of the ``FilesystemPhotoStorage`` adapter
directly against a real ``tmp_path`` (no app, no DB): server-side UUID naming, the
resolve-within-root traversal guard (the belt-and-suspenders check on top of the UUID
naming), and the idempotent delete. The endpoint suite proves the same naming behaviour
end-to-end; this pins the guard branch that a tainted name would trip.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from viridarium.adapters.outbound.db.photo_storage import FilesystemPhotoStorage

pytestmark = pytest.mark.unit


def test_save_generates_uuid_name_and_writes_bytes(tmp_path: Path) -> None:
    storage = FilesystemPhotoStorage(tmp_path / "photos")

    name = storage.save(b"\xff\xd8\xff data", suffix="jpg")

    assert name.endswith(".jpg")
    assert ".." not in name
    written = (tmp_path / "photos" / name).read_bytes()
    assert written == b"\xff\xd8\xff data"


def test_open_path_rejects_traversal_escape(tmp_path: Path) -> None:
    storage = FilesystemPhotoStorage(tmp_path / "photos")

    with pytest.raises(ValueError, match="escapes"):
        storage.open_path("../../etc/passwd")


def test_delete_is_idempotent(tmp_path: Path) -> None:
    storage = FilesystemPhotoStorage(tmp_path / "photos")
    name = storage.save(b"\x89PNG\r\n\x1a\n", suffix="png")

    storage.delete(name)
    storage.delete(name)  # second delete is a no-op, not an error

    assert not (tmp_path / "photos" / name).exists()
