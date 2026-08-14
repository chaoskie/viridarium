"""Health domain types.

A deliberately tiny value object that lets the walking skeleton exercise the full
hexagonal stack (domain -> application -> adapters) without any real domain features.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

HealthState = Literal["ok"]


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Immutable snapshot of service liveness."""

    status: HealthState
    version: str


class HealthProbe(Protocol):
    """Inbound port: produce the current :class:`HealthStatus`."""

    def status(self) -> HealthStatus:
        """Return the current health status."""
        ...


ReadinessState = Literal["ready", "not-ready"]


@dataclass(frozen=True, slots=True)
class ReadinessStatus:
    """Immutable snapshot of service readiness.

    Liveness ("the process answers") and readiness ("the process can actually serve
    requests") are different questions: a container with no schema is alive but cannot
    serve a single plant read (VIRIDARIUM-67). ``schema_revision`` is the applied
    migration revision, or ``None`` when the database has never been migrated.
    """

    status: ReadinessState
    version: str
    schema_revision: str | None


class SchemaInspector(Protocol):
    """Outbound port: report the migration state of the configured database."""

    def current_revision(self) -> str | None:
        """Return the applied migration revision, or ``None`` if absent."""
        ...


class ReadinessProbe(Protocol):
    """Inbound port: produce the current :class:`ReadinessStatus`."""

    def readiness(self) -> ReadinessStatus:
        """Return the current readiness status."""
        ...
