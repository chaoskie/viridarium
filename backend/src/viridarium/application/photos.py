"""Photo use cases (ADR-B [TEMPLATE]).

A thin application service over the :class:`~viridarium.domain.photo.PhotoRepository`
and :class:`~viridarium.domain.photo.PhotoStorage` ports. It returns domain types
(ARCH-007) and never translates domain errors into HTTP concerns (ADR-C).

The genuine application logic is the **upload validation pipeline** (P2, the core of
this security-sensitive story), ordered so no bytes hit disk until every check passes:

1. ``plant-exists`` -> ``PlantNotFoundError`` (404) if the addressed plant is missing.
2. ``size`` -> ``PhotoTooLargeError`` (413) if the body exceeds the server cap.
3. ``sniff`` -> ``UnsupportedImageTypeError`` (415) if the magic bytes are not an
   allowlisted image (the sniff is authoritative).
4. ``declared/sniff cross-check`` -> 415 if the client-declared content-type is not in
   the allowlist or disagrees with the sniffed type.
5. ``storage.save`` then ``repo.add`` (make_cover when it is the plant's first photo).

On delete the row is removed first, then the file (DB-first, P5), so a failed file
unlink never leaves a dangling row.
"""

from __future__ import annotations

from pathlib import Path

from viridarium.domain.photo import (
    ALLOWED_CONTENT_TYPES,
    NewPhoto,
    Photo,
    PhotoNotFoundError,
    PhotoRepository,
    PhotoStorage,
    PhotoTooLargeError,
    UnsupportedImageTypeError,
    sniff_image_type,
)
from viridarium.domain.plant import PlantNotFoundError


class PhotoService:
    """Use cases for managing a plant's photos, backed by the two ports."""

    def __init__(
        self, repository: PhotoRepository, storage: PhotoStorage, *, max_bytes: int
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._max_bytes = max_bytes

    @property
    def max_bytes(self) -> int:
        """The server-side upload size cap (for the router's capped read)."""
        return self._max_bytes

    def upload(
        self, plant_id: int, data: bytes, *, declared_content_type: str | None
    ) -> Photo:
        """Validate then persist an upload (pipeline in the module docstring)."""
        if not self._repository.plant_exists(plant_id):
            raise PlantNotFoundError(plant_id)
        if len(data) > self._max_bytes:
            raise PhotoTooLargeError(self._max_bytes)

        sniffed = sniff_image_type(data)
        if sniffed is None:
            raise UnsupportedImageTypeError()
        content_type, ext = sniffed

        # The declared type must be allowlisted AND agree with the authoritative sniff.
        declared = (declared_content_type or "").split(";")[0].strip().lower()
        if declared not in ALLOWED_CONTENT_TYPES or declared != content_type:
            raise UnsupportedImageTypeError()

        stored_filename = self._storage.save(data, suffix=ext)
        make_cover = not self._repository.list_for_plant(plant_id)
        return self._repository.add(
            NewPhoto(
                plant_id=plant_id,
                stored_filename=stored_filename,
                content_type=content_type,
                size_bytes=len(data),
            ),
            make_cover=make_cover,
        )

    def list(self, plant_id: int) -> list[Photo]:
        """Return the plant's photos, newest-first."""
        return self._repository.list_for_plant(plant_id)

    def get(self, plant_id: int, photo_id: int) -> Photo:
        """Return one photo; raises ``PhotoNotFoundError`` (incl. cross-plant)."""
        return self._repository.get(plant_id, photo_id)

    def set_cover(self, plant_id: int, photo_id: int) -> Photo:
        """Make one photo the cover (single-cover invariant in-tx)."""
        return self._repository.set_cover(plant_id, photo_id)

    def storage_path(self, plant_id: int, photo_id: int) -> tuple[Path, str]:
        """Return the on-disk path + content-type for serving (after a cross-plant
        existence check). The path is traversal-guarded by the storage adapter. A
        missing backing file (row/file desync) maps to PhotoNotFoundError -> 404, not a
        500, and leaks no path (SEC-007)."""
        photo = self._repository.get(plant_id, photo_id)
        try:
            path = self._storage.open_path(photo.stored_filename)
        except FileNotFoundError as exc:
            raise PhotoNotFoundError(plant_id, photo_id) from exc
        return path, photo.content_type

    def delete(self, plant_id: int, photo_id: int) -> None:
        """Delete a photo: remove the row first, then unlink the file (DB-first, P5)."""
        removed = self._repository.delete(plant_id, photo_id)
        self._storage.delete(removed.stored_filename)
