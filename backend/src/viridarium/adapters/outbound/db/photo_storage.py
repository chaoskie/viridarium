"""Filesystem photo storage (outbound adapter for the PhotoStorage port, ARCH-009).

Stores raw photo bytes under ``PHOTOS_DIR``. ``save`` generates a server-side name
(``uuid4().hex`` + the sniffed suffix) so the client filename never reaches disk -
path-traversal-proof by construction. ``open_path`` additionally resolves the candidate
and asserts it stays within the storage root (belt-and-suspenders, P1/SEC). ``delete``
is idempotent (``missing_ok=True``) so deleting a row whose file is already gone is not
an error.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class FilesystemPhotoStorage:
    """Concrete :class:`~viridarium.domain.photo.PhotoStorage` over a directory."""

    def __init__(self, photos_dir: str | Path) -> None:
        self._root = Path(photos_dir).resolve()

    def save(self, data: bytes, *, suffix: str) -> str:
        """Write ``data`` to a fresh UUID-named file and return the name."""
        self._root.mkdir(parents=True, exist_ok=True)
        name = f"{uuid4().hex}.{suffix}"
        (self._root / name).write_bytes(data)
        return name

    def open_path(self, stored_filename: str) -> Path:
        """Resolve the stored file's path for serving, asserting it stays within the
        root AND that the file exists.

        Raises ``FileNotFoundError`` (carrying only the stored name, never the absolute
        path) when the row's backing file is gone, so the serve path answers 404 not a
        500 on a row/file desync (crash mid-delete, backup/restore, external loss)."""
        candidate = self._resolve(stored_filename)
        if not candidate.is_file():
            raise FileNotFoundError(stored_filename)
        return candidate

    def delete(self, stored_filename: str) -> None:
        """Unlink the stored file; a missing file is not an error (idempotent)."""
        self._resolve(stored_filename).unlink(missing_ok=True)

    def _resolve(self, stored_filename: str) -> Path:
        """Resolve within-root (traversal guard) WITHOUT asserting existence.

        The name is server-generated (UUID), but the resolve-within-root check guards
        against any future caller passing a tainted name."""
        candidate = (self._root / stored_filename).resolve()
        if self._root not in candidate.parents and candidate != self._root:
            raise ValueError("resolved path escapes the photos directory")
        return candidate
