"""Plants router (ARCH-002: HTTP only, no business logic).

Maps the wire schemas to/from domain types and delegates to the
:class:`~viridarium.application.plants.PlantService`. The list endpoint reads the
optional query params into a :class:`~viridarium.domain.plant.PlantFilter`. Domain
errors (``PlantNotFoundError`` -> 404, ``LocationNotFoundForPlantError`` -> 422) are
not caught here: they are translated by the registered exception handlers in the app
factory (ADR-C), keeping status codes out of the router.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from viridarium.adapters.inbound.web.dependencies import (
    get_due_query_service,
    get_plant_service,
)
from viridarium.adapters.inbound.web.schemas import (
    PlantCreate,
    PlantResponse,
    PlantUpdate,
    ScheduleDueResponse,
)
from viridarium.application.due import DueQueryService
from viridarium.application.plants import PlantService
from viridarium.domain.plant import NewPlant, Plant, PlantFilter

router = APIRouter(prefix="/plants", tags=["plants"])

ServiceDep = Annotated[PlantService, Depends(get_plant_service)]
DueServiceDep = Annotated[DueQueryService, Depends(get_due_query_service)]


def _with_due(plant: Plant, due: DueQueryService) -> PlantResponse:
    """Compose a plant read with its computed ``schedules`` due field (US-3.3).

    An archived plant is excluded from due computation entirely (empty schedules); a
    non-archived plant gets one entry per enabled schedule. The field is composed here,
    not read off the domain ``Plant`` (which has no due).
    """
    response = PlantResponse.model_validate(plant)
    if plant.archived:
        return response
    due_by_plant = due.for_plants([plant.id])
    response.schedules = [
        ScheduleDueResponse.from_domain(d) for d in due_by_plant.get(plant.id, [])
    ]
    return response


def _to_new_plant(body: PlantCreate) -> NewPlant:
    return NewPlant(
        name=body.name,
        species=body.species,
        location_id=body.location_id,
        acquired_on=body.acquired_on,
        pot_size_cm=body.pot_size_cm,
        pot_material=body.pot_material,
        light_level=body.light_level,
        notes=body.notes,
        tags=tuple(body.tags),
        archived=body.archived,
    )


@router.post(
    "",
    response_model=PlantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a plant",
)
def create_plant(body: PlantCreate, service: ServiceDep) -> PlantResponse:
    """Create a new plant."""
    created = service.create(_to_new_plant(body))
    return PlantResponse.model_validate(created)


@router.get("", response_model=list[PlantResponse], summary="List plants")
def list_plants(
    service: ServiceDep,
    due: DueServiceDep,
    q: Annotated[str | None, Query()] = None,
    location_id: Annotated[int | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    species: Annotated[str | None, Query()] = None,
    homeless: Annotated[bool, Query()] = False,
    archived: Annotated[bool | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
) -> list[PlantResponse]:
    """List plants, optionally filtered (AND-combined), ordered by name.

    Defaults to active plants only; ``archived=true`` returns archived only and
    ``include_archived=true`` returns all (US-2.4).
    """
    plant_filter = PlantFilter(
        q=q,
        location_id=location_id,
        tag=tag,
        species=species,
        homeless=homeless,
        archived=archived,
        include_archived=include_archived,
    )
    plants = service.list(plant_filter)
    # One batch due read for all non-archived ids -> the list path stays flat (no N+1,
    # AC7); archived plants are excluded from the computation and get empty schedules.
    active_ids = [p.id for p in plants if not p.archived]
    due_by_plant = due.for_plants(active_ids)
    responses: list[PlantResponse] = []
    for plant in plants:
        response = PlantResponse.model_validate(plant)
        response.schedules = [
            ScheduleDueResponse.from_domain(d) for d in due_by_plant.get(plant.id, [])
        ]
        responses.append(response)
    return responses


@router.get("/{plant_id}", response_model=PlantResponse, summary="Get a plant")
def get_plant(plant_id: int, service: ServiceDep, due: DueServiceDep) -> PlantResponse:
    """Get one plant by id, with its computed ``schedules`` due field (US-3.3)."""
    return _with_due(service.get(plant_id), due)


@router.put("/{plant_id}", response_model=PlantResponse, summary="Replace a plant")
def update_plant(
    plant_id: int, body: PlantUpdate, service: ServiceDep
) -> PlantResponse:
    """Full-replace a plant's fields and tags (ADR-D)."""
    updated = service.update(plant_id, _to_new_plant(body))
    return PlantResponse.model_validate(updated)


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a plant",
)
def delete_plant(plant_id: int, service: ServiceDep) -> Response:
    """Delete a plant by id."""
    service.delete(plant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plant_id}/archive",
    response_model=PlantResponse,
    summary="Archive a plant",
)
def archive_plant(plant_id: int, service: ServiceDep) -> PlantResponse:
    """Archive a plant (idempotent state-set); 404 on an unknown id (A1)."""
    return PlantResponse.model_validate(service.archive(plant_id))


@router.post(
    "/{plant_id}/unarchive",
    response_model=PlantResponse,
    summary="Unarchive a plant",
)
def unarchive_plant(plant_id: int, service: ServiceDep) -> PlantResponse:
    """Unarchive a plant (idempotent state-set); 404 on an unknown id (A1)."""
    return PlantResponse.model_validate(service.unarchive(plant_id))
