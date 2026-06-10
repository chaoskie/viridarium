"""Care-schedules router (ARCH-002: HTTP only, no business logic).

Exposes the care-schedule sub-resource under ``/plants/{plant_id}/schedules`` and
delegates to the :class:`~viridarium.application.care_schedules.CareScheduleService`.
The ``care_type`` is a path parameter typed as the ``CareType`` enum, so an unknown
value (e.g. ``banana``) is auto-rejected as 422 by FastAPI before the handler runs.

The only HTTP-layer logic is :func:`_to_new_schedule`, which resolves the **dormancy
default** by care type (CS2 / PO Q1): when the body omits ``dormancy``, feed ->
``paused`` and water -> ``winter_interval``; an explicit body value always wins. There
is no cross-field validation (CS3 / PO Q2): a ``winter_interval`` dormancy with a null
``winter_interval_days`` is accepted.

Domain errors (``PlantNotFoundForScheduleError`` -> 404,
``CareScheduleNotFoundError`` -> 404) are mapped by the registered exception handlers in
the app factory (ADR-C). Reject bodies carry ids + the care_type only - never the plant
name (SEC-007).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from viridarium.adapters.inbound.web.dependencies import get_care_schedule_service
from viridarium.adapters.inbound.web.schemas import (
    CareScheduleResponse,
    CareScheduleUpsert,
)
from viridarium.application.care_schedules import CareScheduleService
from viridarium.domain.care_schedule import CareType, Dormancy, NewCareSchedule

router = APIRouter(prefix="/plants/{plant_id}/schedules", tags=["care-schedules"])

ServiceDep = Annotated[CareScheduleService, Depends(get_care_schedule_service)]

# Care-type dormancy defaults applied when the body omits ``dormancy`` (CS2 / PO Q1).
_DORMANCY_DEFAULTS: dict[CareType, Dormancy] = {
    CareType.FEED: Dormancy.PAUSED,
    CareType.WATER: Dormancy.WINTER_INTERVAL,
}


def _to_new_schedule(care_type: CareType, body: CareScheduleUpsert) -> NewCareSchedule:
    """Resolve the dormancy default by care type when the body omits it (CS2)."""
    dormancy = body.dormancy or _DORMANCY_DEFAULTS[care_type]
    return NewCareSchedule(
        care_type=care_type,
        interval_days=body.interval_days,
        winter_interval_days=body.winter_interval_days,
        dormancy=dormancy,
        enabled=body.enabled,
    )


@router.get("", response_model=list[CareScheduleResponse], summary="List schedules")
def list_schedules(plant_id: int, service: ServiceDep) -> list[CareScheduleResponse]:
    """List the plant's care schedules (0-2, water-first)."""
    return [CareScheduleResponse.from_domain(s) for s in service.list(plant_id)]


@router.put(
    "/{care_type}",
    response_model=CareScheduleResponse,
    summary="Create or replace a schedule",
)
def upsert_schedule(
    plant_id: int,
    care_type: CareType,
    body: CareScheduleUpsert,
    service: ServiceDep,
) -> CareScheduleResponse:
    """Create-or-replace the schedule for this ``care_type`` (idempotent, CS1)."""
    schedule = service.upsert(plant_id, _to_new_schedule(care_type, body))
    return CareScheduleResponse.from_domain(schedule)


@router.get(
    "/{care_type}",
    response_model=CareScheduleResponse,
    summary="Get a schedule",
)
def get_schedule(
    plant_id: int, care_type: CareType, service: ServiceDep
) -> CareScheduleResponse:
    """Return one schedule; 404 if the plant or schedule is missing."""
    return CareScheduleResponse.from_domain(service.get(plant_id, care_type))


@router.delete(
    "/{care_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a schedule",
)
def delete_schedule(
    plant_id: int, care_type: CareType, service: ServiceDep
) -> Response:
    """Delete one schedule; 404 if it does not exist."""
    service.delete(plant_id, care_type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
