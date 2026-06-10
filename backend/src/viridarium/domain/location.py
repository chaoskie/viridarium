"""Location domain types (framework-free).

The first persisted aggregate. It establishes the reusable [TEMPLATE] every later
entity copies (ADR-B): a persisted ``Entity`` + ``NewEntity`` pair, a typed
``XNotFoundError`` carrying no PII (only the id), and an ``XRepository`` ``Protocol``
whose ``get``/``update``/``delete`` raise the domain error on a missing row and never
return framework types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Location:
    """A persisted room/location where plants live.

    ``created_at``/``updated_at`` are server-set infrastructural metadata (ADR-A),
    not client-controllable; they are absent from :class:`NewLocation`.
    """

    id: int
    name: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewLocation:
    """A location to create: the client-supplied fields only (no server-set fields)."""

    name: str
    notes: str | None


class LocationNotFoundError(Exception):
    """Raised when no location exists for the given id.

    Carries only the integer id (SEC-001/PRIN-II: no PII in the message or any
    derived error body).
    """

    def __init__(self, location_id: int) -> None:
        self.location_id = location_id
        super().__init__(f"Location {location_id} not found")


class LocationRepository(Protocol):
    """Outbound port for persisting and querying :class:`Location` aggregates."""

    def add(self, new_location: NewLocation) -> Location:
        """Persist a new location and return it with its server-set fields."""
        ...

    def list_all(self) -> list[Location]:
        """Return all locations ordered by ``name`` ascending."""
        ...

    def get(self, location_id: int) -> Location:
        """Return the location or raise :class:`LocationNotFoundError`."""
        ...

    def update(self, location_id: int, name: str, notes: str | None) -> Location:
        """Full-replace ``name``/``notes`` (ADR-D) or raise the not-found error."""
        ...

    def delete(self, location_id: int) -> None:
        """Delete the location or raise :class:`LocationNotFoundError`."""
        ...
