"""FastAPI dependency providers bridging HTTP to the application layer.

These read collaborators wired onto ``app.state`` by the composition root
(:mod:`plant_care.infrastructure.container`), keeping the routers free of any
construction logic.
"""

from __future__ import annotations

from fastapi import Request

from plant_care.domain.health import HealthProbe


def get_health_probe(request: Request) -> HealthProbe:
    """Return the application's health probe from the composition root."""
    probe: HealthProbe = request.app.state.health_probe
    return probe
