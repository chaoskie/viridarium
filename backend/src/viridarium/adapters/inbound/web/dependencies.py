"""FastAPI dependency providers bridging HTTP to the application layer.

These read collaborators wired onto ``app.state`` by the composition root
(:mod:`viridarium.infrastructure.container`), keeping the routers free of any
construction logic.
"""

from __future__ import annotations

from fastapi import Request

from viridarium.application.locations import LocationService
from viridarium.domain.health import HealthProbe


def get_health_probe(request: Request) -> HealthProbe:
    """Return the application's health probe from the composition root."""
    probe: HealthProbe = request.app.state.health_probe
    return probe


def get_location_service(request: Request) -> LocationService:
    """Return the application's location service from the composition root."""
    service: LocationService = request.app.state.location_service
    return service
