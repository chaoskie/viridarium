"""Health use case."""

from __future__ import annotations

from viridarium.domain.health import (
    HealthProbe,
    HealthStatus,
    ReadinessProbe,
    ReadinessStatus,
    SchemaInspector,
)


class GetHealthStatus(HealthProbe):
    """Use case: report whether the service is alive and which version it runs.

    Implements the :class:`~viridarium.domain.health.HealthProbe` inbound port. The
    version is injected at the composition root so the application layer stays free of
    packaging/runtime concerns.
    """

    def __init__(self, version: str) -> None:
        self._version = version

    def status(self) -> HealthStatus:
        return HealthStatus(status="ok", version=self._version)


class GetReadinessStatus(ReadinessProbe):
    """Use case: report whether the service can actually serve requests.

    Readiness is schema-gated (VIRIDARIUM-67): the process may be alive while the
    database has no tables, in which case every real endpoint 500s. Asking the schema
    inspector for the applied migration revision answers that in one cheap read.
    """

    def __init__(self, inspector: SchemaInspector, version: str) -> None:
        self._inspector = inspector
        self._version = version

    def readiness(self) -> ReadinessStatus:
        revision = self._inspector.current_revision()
        return ReadinessStatus(
            status="ready" if revision is not None else "not-ready",
            version=self._version,
            schema_revision=revision,
        )
