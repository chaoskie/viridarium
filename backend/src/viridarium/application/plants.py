"""Plant use cases.

A thin application service (ADR-B [TEMPLATE]) backed by the
:class:`~viridarium.domain.plant.PlantRepository` port. It returns domain types
(ARCH-007) and never translates the port's domain errors into HTTP concerns - that
mapping lives in the inbound adapter (ADR-C).

The one piece of genuine application logic here is the **FK-existence guard** (D1 /
ADR-B): on create/update, a non-null ``location_id`` that does not exist raises
:class:`~viridarium.domain.plant.LocationNotFoundForPlantError` (mapped to 422, a
body-reference failure). A homeless plant (``location_id is None``) is always allowed.
"""

from __future__ import annotations

from viridarium.domain.plant import (
    LocationNotFoundForPlantError,
    NewPlant,
    Plant,
    PlantFilter,
    PlantRepository,
)


class PlantService:
    """Use cases for managing plants, backed by a repository port."""

    def __init__(self, repository: PlantRepository) -> None:
        self._repository = repository

    def _guard_location(self, location_id: int | None) -> None:
        """Reject a non-existent referenced location (homeless = None is allowed)."""
        if location_id is not None and not self._repository.location_exists(
            location_id
        ):
            raise LocationNotFoundForPlantError(location_id)

    def create(self, new_plant: NewPlant) -> Plant:
        """Persist a new plant; raise ``LocationNotFoundForPlantError`` on a bad FK."""
        self._guard_location(new_plant.location_id)
        return self._repository.add(new_plant)

    def list(self, plant_filter: PlantFilter) -> list[Plant]:
        """Return plants matching the filter, ordered by name."""
        return self._repository.list(plant_filter)

    def get(self, plant_id: int) -> Plant:
        """Return one plant; propagates ``PlantNotFoundError`` if absent."""
        return self._repository.get(plant_id)

    def update(self, plant_id: int, new_plant: NewPlant) -> Plant:
        """Full-replace a plant; raise on a bad FK, propagate ``PlantNotFoundError``."""
        self._guard_location(new_plant.location_id)
        return self._repository.update(plant_id, new_plant)

    def delete(self, plant_id: int) -> None:
        """Delete a plant; propagates ``PlantNotFoundError`` if absent."""
        self._repository.delete(plant_id)
