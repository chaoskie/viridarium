"""Health router (ARCH-002: no business logic, HTTP only).

SEC-001: this is a non-destructive read with no PII; safe on the trust boundary.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from viridarium.adapters.inbound.web.dependencies import get_health_probe
from viridarium.adapters.inbound.web.schemas import HealthResponse
from viridarium.domain.health import HealthProbe

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health(probe: Annotated[HealthProbe, Depends(get_health_probe)]) -> HealthResponse:
    """Report service liveness and version."""
    status = probe.status()
    return HealthResponse(status=status.status, version=status.version)
