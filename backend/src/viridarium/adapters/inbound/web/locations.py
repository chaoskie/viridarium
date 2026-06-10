"""Locations router (ARCH-002: HTTP only, no business logic).

Maps the wire schemas to/from domain types and delegates to the
:class:`~viridarium.application.locations.LocationService`. ``LocationNotFoundError``
is not caught here: it is translated to HTTP 404 by the registered exception handler
in the app factory (ADR-C), keeping status codes out of the router.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from viridarium.adapters.inbound.web.dependencies import get_location_service
from viridarium.adapters.inbound.web.schemas import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from viridarium.application.locations import LocationService
from viridarium.domain.location import NewLocation

router = APIRouter(prefix="/locations", tags=["locations"])

ServiceDep = Annotated[LocationService, Depends(get_location_service)]


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a location",
)
def create_location(body: LocationCreate, service: ServiceDep) -> LocationResponse:
    """Create a new room/location."""
    created = service.create(NewLocation(name=body.name, notes=body.notes))
    return LocationResponse.model_validate(created)


@router.get("", response_model=list[LocationResponse], summary="List locations")
def list_locations(service: ServiceDep) -> list[LocationResponse]:
    """List all rooms/locations ordered by name."""
    return [LocationResponse.model_validate(loc) for loc in service.list()]


@router.get("/{location_id}", response_model=LocationResponse, summary="Get a location")
def get_location(location_id: int, service: ServiceDep) -> LocationResponse:
    """Get one room/location by id."""
    return LocationResponse.model_validate(service.get(location_id))


@router.put(
    "/{location_id}", response_model=LocationResponse, summary="Replace a location"
)
def update_location(
    location_id: int, body: LocationUpdate, service: ServiceDep
) -> LocationResponse:
    """Full-replace a room/location's name and notes (ADR-D)."""
    updated = service.update(location_id, name=body.name, notes=body.notes)
    return LocationResponse.model_validate(updated)


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a location",
)
def delete_location(location_id: int, service: ServiceDep) -> Response:
    """Delete a room/location by id."""
    service.delete(location_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
