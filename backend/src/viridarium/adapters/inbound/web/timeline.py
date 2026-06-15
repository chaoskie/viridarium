"""Timeline router (ARCH-002: HTTP only, no business logic).

Exposes the read-only care-history feed under ``/plants/{plant_id}/timeline`` and
delegates to the :class:`~viridarium.application.timeline.TimelineQueryService`. The
service merges the plant's events + photos server-side (US-3.4); this layer maps each
domain entry to its discriminated wire arm. The plant-exists guard lives in the service
and raises :class:`PlantNotFoundForEventError`, mapped to 404 by the registered handler
in the app factory (ADR-C) - the router never sets a status for it. The 404 body carries
the integer id only, no PII (SEC-001/SEC-007).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from viridarium.adapters.inbound.web.dependencies import get_timeline_query_service
from viridarium.adapters.inbound.web.schemas import (
    TimelineEntryResponse,
    timeline_entry_to_response,
)
from viridarium.application.timeline import TimelineQueryService

router = APIRouter(prefix="/plants/{plant_id}/timeline", tags=["timeline"])

ServiceDep = Annotated[TimelineQueryService, Depends(get_timeline_query_service)]


@router.get(
    "",
    response_model=list[TimelineEntryResponse],
    summary="Get a plant's care-history timeline",
)
def get_timeline(plant_id: int, service: ServiceDep) -> list[TimelineEntryResponse]:
    """Return the plant's events + photos merged, newest-first (404 if absent)."""
    return [
        timeline_entry_to_response(plant_id, entry)
        for entry in service.for_plant(plant_id)
    ]
