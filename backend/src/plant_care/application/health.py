"""Health use case."""

from __future__ import annotations

from plant_care.domain.health import HealthProbe, HealthStatus


class GetHealthStatus(HealthProbe):
    """Use case: report whether the service is alive and which version it runs.

    Implements the :class:`~plant_care.domain.health.HealthProbe` inbound port. The
    version is injected at the composition root so the application layer stays free of
    packaging/runtime concerns.
    """

    def __init__(self, version: str) -> None:
        self._version = version

    def status(self) -> HealthStatus:
        return HealthStatus(status="ok", version=self._version)
