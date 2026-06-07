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
