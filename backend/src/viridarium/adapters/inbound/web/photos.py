"""Photos router (ARCH-002: HTTP only, no business logic).

Exposes the photo sub-resource under ``/plants/{plant_id}/photos`` and delegates to the
:class:`~viridarium.application.photos.PhotoService`. The upload reads the body with a
**cap** (``max_bytes + 1``) so an oversize payload is rejected (413) without buffering
the whole thing; the magic-byte sniff + declared/sniff cross-check (415) and the
plant-existence check (404) all live in the service. The bytes are served via
``FileResponse`` (not a static mount, P4) with a long private immutable cache header.

Domain errors (``PhotoNotFoundError`` -> 404, ``UnsupportedImageTypeError`` -> 415,
``PhotoTooLargeError`` -> 413, ``PlantNotFoundError`` -> 404) are mapped by the
registered exception handlers in the app factory (ADR-C); the router never sets a status
for them. Reject bodies carry ids/ints only - never the client filename (SEC-007).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse

from viridarium.adapters.inbound.web.dependencies import get_photo_service
from viridarium.adapters.inbound.web.schemas import PhotoResponse
from viridarium.application.photos import PhotoService
from viridarium.domain.photo import PhotoTooLargeError

router = APIRouter(prefix="/plants/{plant_id}/photos", tags=["photos"])

ServiceDep = Annotated[PhotoService, Depends(get_photo_service)]

_CACHE_CONTROL = "private, max-age=31536000, immutable"


@router.post(
    "",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo",
)
async def upload_photo(
    plant_id: int,
    service: ServiceDep,
    file: Annotated[UploadFile, File()],
) -> PhotoResponse:
    """Upload a photo for a plant (multipart ``file``); validated server-side."""
    cap = service.max_bytes
    data = await file.read(cap + 1)
    if len(data) > cap:
        # Oversize: reject before any sniff/disk write. Id/int-only body (no filename).
        raise PhotoTooLargeError(cap)
    created = service.upload(plant_id, data, declared_content_type=file.content_type)
    return PhotoResponse.from_domain(created)


@router.get("", response_model=list[PhotoResponse], summary="List a plant's photos")
def list_photos(plant_id: int, service: ServiceDep) -> list[PhotoResponse]:
    """List the plant's photos, newest-first."""
    return [PhotoResponse.from_domain(p) for p in service.list(plant_id)]


@router.get("/{photo_id}", summary="Get a photo's bytes")
def get_photo_bytes(plant_id: int, photo_id: int, service: ServiceDep) -> FileResponse:
    """Serve the raw photo bytes via ``FileResponse`` (P4), not a static mount."""
    path, content_type = service.storage_path(plant_id, photo_id)
    return FileResponse(
        path,
        media_type=content_type,
        headers={"Cache-Control": _CACHE_CONTROL},
    )


@router.post(
    "/{photo_id}/cover",
    response_model=PhotoResponse,
    summary="Set a photo as the cover",
)
def set_cover_photo(plant_id: int, photo_id: int, service: ServiceDep) -> PhotoResponse:
    """Make this photo the plant's cover (single-cover invariant)."""
    return PhotoResponse.from_domain(service.set_cover(plant_id, photo_id))


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo",
)
def delete_photo(plant_id: int, photo_id: int, service: ServiceDep) -> Response:
    """Delete a photo (row + file); promotes a survivor if the cover went."""
    service.delete(plant_id, photo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
