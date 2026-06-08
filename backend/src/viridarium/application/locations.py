"""Location use cases.

A thin application service (ADR-B [TEMPLATE]: one ``XService`` per aggregate,
constructor-injected with its port) that delegates to the
:class:`~viridarium.domain.location.LocationRepository`. It returns domain types
(ARCH-007) and never translates the port's domain errors into HTTP concerns - that
mapping lives in the inbound adapter (ADR-C). Real rules (due computation, archive
exclusion) land here when later entities gain them.
"""

from __future__ import annotations

from viridarium.domain.location import (
    Location,
    LocationRepository,
    NewLocation,
)


class LocationService:
    """Use cases for managing locations, backed by a repository port."""

    def __init__(self, repository: LocationRepository) -> None:
        self._repository = repository

    def create(self, new_location: NewLocation) -> Location:
        """Persist a new location and return it."""
        return self._repository.add(new_location)

    def list(self) -> list[Location]:
        """Return all locations ordered by name."""
        return self._repository.list_all()

    def get(self, location_id: int) -> Location:
        """Return one location; propagates ``LocationNotFoundError`` if absent."""
        return self._repository.get(location_id)

    def update(self, location_id: int, name: str, notes: str | None) -> Location:
        """Full-replace a location's fields; propagates ``LocationNotFoundError``."""
        return self._repository.update(location_id, name, notes)

    def delete(self, location_id: int) -> None:
        """Delete a location; propagates ``LocationNotFoundError`` if absent."""
        self._repository.delete(location_id)
