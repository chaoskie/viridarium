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

from viridarium.domain.photo import PhotoRepository, PhotoStorage
from viridarium.domain.plant import (
    LocationNotFoundForPlantError,
    NewPlant,
    Plant,
    PlantFilter,
    PlantRepository,
)


class PlantService:
    """Use cases for managing plants, backed by a repository port.

    Optionally wired with the photo repository + storage so :meth:`delete` can clean up
    a deleted plant's photo files (P6): the DB CASCADE removes the photo rows, but the
    raw bytes on disk must be unlinked app-level (engine-agnostic). The photo ports are
    optional so the pure plant use cases can be unit-tested without them.
    """

    def __init__(
        self,
        repository: PlantRepository,
        *,
        photo_repository: PhotoRepository | None = None,
        photo_storage: PhotoStorage | None = None,
    ) -> None:
        self._repository = repository
        self._photo_repository = photo_repository
        self._photo_storage = photo_storage

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
        """Delete a plant and clean up its photo files (P6).

        Enumerate the plant's photo filenames *before* the delete (the rows still
        exist), delete the plant (the DB CASCADE removes the photo rows), then unlink
        the files *after* (idempotent). Propagates ``PlantNotFoundError`` if absent;
        the enumerate step is skipped when no photo ports are wired (pure unit tests).
        """
        filenames: list[str] = []
        if self._photo_repository is not None and self._photo_storage is not None:
            filenames = self._photo_repository.list_filenames_for_plant(plant_id)
        self._repository.delete(plant_id)
        if self._photo_storage is not None:
            for filename in filenames:
                self._photo_storage.delete(filename)

    def archive(self, plant_id: int) -> Plant:
        """Archive a plant (idempotent); propagates ``PlantNotFoundError`` if absent.

        A pass-through to the port: archiving never touches the location, so there is
        no FK guard (unlike create/update).
        """
        return self._repository.archive(plant_id)

    def unarchive(self, plant_id: int) -> Plant:
        """Unarchive a plant (idempotent); propagates ``PlantNotFoundError``."""
        return self._repository.unarchive(plant_id)
