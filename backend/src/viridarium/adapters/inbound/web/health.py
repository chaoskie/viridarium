"""Health router (ARCH-002: no business logic, HTTP only).

SEC-001: this is a non-destructive read with no PII; safe on the trust boundary.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from viridarium.adapters.inbound.web.dependencies import (
    get_health_probe,
    get_readiness_probe,
)
from viridarium.adapters.inbound.web.schemas import HealthResponse, ReadinessResponse
from viridarium.domain.health import HealthProbe, ReadinessProbe

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health(probe: Annotated[HealthProbe, Depends(get_health_probe)]) -> HealthResponse:
    """Report service liveness and version."""
    status = probe.status()
    return HealthResponse(status=status.status, version=status.version)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe (schema-gated)",
    responses={503: {"model": ReadinessResponse}},
)
def readiness(
    response: Response,
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
) -> ReadinessResponse:
    """Report whether the service can serve requests.

    Split from ``/health`` deliberately (VIRIDARIUM-67): the container HEALTHCHECK
    stays a pure liveness probe, while orchestrators that gate traffic can point at
    this one. A database without an applied migration answers 503, which is what the
    schemaless fresh deploy did not do before.
    """
    status = probe.readiness()
    if status.status != "ready":
        response.status_code = 503
    return ReadinessResponse(
        status=status.status,
        version=status.version,
        schema_revision=status.schema_revision,
    )
