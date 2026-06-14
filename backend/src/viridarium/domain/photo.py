"""Photo domain types (framework-free).

The security-sensitive aggregate of US-2.3 (SPEC-004), mirroring the Plant/Location
[TEMPLATE]: a persisted ``Photo`` + ``NewPhoto`` pair, typed errors carrying no PII
(ids/ints only, SEC-001/SEC-007), and two outbound ``Protocol`` ports - a
``PhotoRepository`` for metadata and a ``PhotoStorage`` for the raw bytes (ARCH-009:
filesystem I/O stays at the adapter boundary).

The pure :func:`sniff_image_type` is the security primitive: it inspects only the
leading bytes (never the declared content-type or the client filename) and is the
**authoritative** source for the stored content-type and extension. The allowlist is
jpeg/png/webp; anything else (GIF, junk, empty, truncated, RIFF-but-not-WEBP) -> None.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

# Allowlist of accepted declared content-types (P2). The sniff result is the
# authoritative content-type; the declared value is only cross-checked against it.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)


def sniff_image_type(head: bytes) -> tuple[str, str] | None:
    """Return ``(content_type, ext)`` for an allowlisted image, else ``None``.

    Authoritative magic-byte sniff (P2): inspects only ``head`` (the leading bytes of
    the payload) in a fixed priority - JPEG, then PNG, then WEBP - and returns the first
    match. Disallowed/unknown/empty/truncated content falls through to ``None`` (the
    security default). Never consults any declared type or filename.
    """
    if head[:3] == b"\xff\xd8\xff":
        return ("image/jpeg", "jpg")
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return ("image/png", "png")
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ("image/webp", "webp")
    return None


@dataclass(frozen=True, slots=True)
class Photo:
    """A persisted photo's metadata.

    ``stored_filename`` is the server-generated on-disk name (UUID + sniffed ext); it
    is a security boundary and never crosses the response layer (ARCH-007). Photos are
    immutable, so there is no ``updated_at`` (only ``created_at``, server-set, ADR-A).
    """

    id: int
    plant_id: int
    stored_filename: str
    content_type: str
    size_bytes: int
    is_cover: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewPhoto:
    """A photo to persist: the server-validated metadata (no server-set id/timestamp).

    All fields are server-derived: ``content_type``/``stored_filename`` come from the
    authoritative sniff, never from the client headers or filename.
    """

    plant_id: int
    stored_filename: str
    content_type: str
    size_bytes: int


class PhotoNotFoundError(Exception):
    """Raised when no photo exists for the given (plant_id, photo_id).

    Covers both a genuinely-missing photo and a cross-plant reference (a photo that
    exists but belongs to a different plant -> 404, no ownership model in v1, SEC-002).
    Carries only the integer ids (SEC-001: no PII).
    """

    def __init__(self, plant_id: int, photo_id: int) -> None:
        self.plant_id = plant_id
        self.photo_id = photo_id
        super().__init__(f"Photo {photo_id} not found for plant {plant_id}")


class UnsupportedImageTypeError(Exception):
    """Raised when the upload is not an allowlisted image (mapped to 415).

    Triggered when the declared content-type is not in the allowlist, the magic-byte
    sniff fails (not a jpeg/png/webp), or the declared type and the sniffed type
    disagree. Carries no client-supplied data (no filename, no body) - SEC-007.
    """

    def __init__(self) -> None:
        super().__init__("Unsupported image type")


class PhotoTooLargeError(Exception):
    """Raised when the upload exceeds the server-side size cap (mapped to 413).

    Carries only the integer limit (no PII). Enforced via a capped read so an oversize
    body is rejected before it is fully buffered or written to disk.
    """

    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        super().__init__(f"Photo exceeds the {max_bytes} byte limit")


class PhotoRepository(Protocol):
    """Outbound port for persisting and querying :class:`Photo` metadata."""

    def add(self, new_photo: NewPhoto, *, make_cover: bool) -> Photo:
        """Persist a photo row; if ``make_cover`` clear other covers in the same tx."""
        ...

    def list_for_plant(self, plant_id: int) -> list[Photo]:
        """Return the plant's photos, newest-first (``created_at`` descending)."""
        ...

    def get(self, plant_id: int, photo_id: int) -> Photo:
        """Return the photo or raise :class:`PhotoNotFoundError` (incl. cross-plant)."""
        ...

    def cover_ids_for_plants(self, plant_ids: list[int]) -> dict[int, int]:
        """Return the cover photo id per plant, one grouped read (no-cover omitted)."""
        ...

    def set_cover(self, plant_id: int, photo_id: int) -> Photo:
        """Make exactly one photo the cover (clears others in-tx) or raise not-found."""
        ...

    def delete(self, plant_id: int, photo_id: int) -> Photo:
        """Delete the row (promoting a survivor if the cover went) and return it."""
        ...

    def plant_exists(self, plant_id: int) -> bool:
        """Return whether a plant with the given id exists (cross-aggregate read)."""
        ...

    def list_filenames_for_plant(self, plant_id: int) -> list[str]:
        """Return the stored filenames for a plant (for plant-delete cleanup, P6)."""
        ...


class PhotoStorage(Protocol):
    """Outbound port for the raw photo bytes (filesystem in v1, ARCH-009)."""

    def save(self, data: bytes, *, suffix: str) -> str:
        """Write ``data`` under a server-generated name and return that name."""
        ...

    def open_path(self, stored_filename: str) -> Path:
        """Resolve ``stored_filename`` to an absolute path within the storage root.

        Implementations MUST assert the resolved path stays inside the storage dir
        (traversal guard, belt-and-suspenders on top of the UUID naming)."""
        ...

    def delete(self, stored_filename: str) -> None:
        """Remove the stored file (idempotent: a missing file is not an error)."""
        ...
