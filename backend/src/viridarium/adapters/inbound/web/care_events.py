"""Care-events router (ARCH-002: HTTP only, no business logic).

Exposes the append-only care-event sub-resource under ``/plants/{plant_id}/events``
and delegates to the :class:`~viridarium.application.care_events.CareEventService`.
Deliberately POST/GET/DELETE only - **no PUT/PATCH route exists** (AC4, append-only);
events are immutable and a mistake is deleted, not edited.

Shape rules live on :class:`~viridarium.adapters.inbound.web.schemas.CareEventCreate`
(enum membership, the today default + future-date 422, the note cap). Domain errors
(``PlantNotFoundForEventError``/``CareEventNotFoundError`` -> 404,
``HealthRequiresObserveError``/``PhotoNotForPlantError`` -> 422) are mapped by the
registered exception handlers in the app factory (ADR-C). Reject bodies carry ids +
enum values only - never the plant name or the note free text (SEC-007).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from viridarium.adapters.inbound.web.dependencies import get_care_event_service
from viridarium.adapters.inbound.web.schemas import (
    CareEventCreate,
    CareEventResponse,
)
from viridarium.application.care_events import CareEventService
from viridarium.domain.care_event import NewCareEvent

router = APIRouter(prefix="/plants/{plant_id}/events", tags=["care-events"])

ServiceDep = Annotated[CareEventService, Depends(get_care_event_service)]


@router.post(
    "",
    response_model=CareEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a care event",
)
def create_event(
    plant_id: int, body: CareEventCreate, service: ServiceDep
) -> CareEventResponse:
    """Append one care event; 404 if the plant is missing (guard first)."""
    event = service.create(
        plant_id,
        NewCareEvent(
            type=body.type,
            happened_on=body.happened_on,
            note=body.note,
            photo_id=body.photo_id,
            health=body.health,
        ),
    )
    return CareEventResponse.from_domain(event)


@router.get("", response_model=list[CareEventResponse], summary="List care events")
def list_events(plant_id: int, service: ServiceDep) -> list[CareEventResponse]:
    """List the plant's events newest-first (happened_on desc, created_at desc)."""
    return [CareEventResponse.from_domain(e) for e in service.list(plant_id)]


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a care event",
)
def delete_event(plant_id: int, event_id: int, service: ServiceDep) -> Response:
    """Delete one event; 404 if the plant, then the event, is missing."""
    service.delete(plant_id, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
