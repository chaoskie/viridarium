"""Care-event use cases (ADR-B [TEMPLATE]).

A thin application service over the
:class:`~viridarium.domain.care_event.CareEventRepository` port. It returns domain
types (ARCH-007) and never translates domain errors into HTTP concerns (ADR-C).

Guard order on ``create`` (test foundation §3): the **plant-exists guard** fires FIRST
(-> :class:`~viridarium.domain.care_event.PlantNotFoundForEventError`, 404,
VIRIDARIUM-48) so a missing plant is never masked by a body-reference failure; then the
**health-only-on-observe** domain rule
(-> :class:`~viridarium.domain.care_event.HealthRequiresObserveError`, 422); then the
**same-plant photo guard**
(-> :class:`~viridarium.domain.care_event.PhotoNotForPlantError`, 422 - an unknown
photo counts as not-for-plant). ``delete`` guards the plant, then lets the repo raise
:class:`~viridarium.domain.care_event.CareEventNotFoundError` (404) unchanged.
"""

from __future__ import annotations

from viridarium.domain.care_event import (
    CareEvent,
    CareEventRepository,
    CareEventType,
    HealthRequiresObserveError,
    NewCareEvent,
    PhotoNotForPlantError,
    PlantNotFoundForEventError,
)


class CareEventService:
    """Use cases for a plant's care events, backed by a repository port."""

    def __init__(self, repository: CareEventRepository) -> None:
        self._repository = repository

    def _guard_plant(self, plant_id: int) -> None:
        """Reject an unknown plant before any per-event work (404)."""
        if not self._repository.plant_exists(plant_id):
            raise PlantNotFoundForEventError(plant_id)

    def create(self, plant_id: int, new: NewCareEvent) -> CareEvent:
        """Append one event; guard plant, the health rule, then the photo link."""
        self._guard_plant(plant_id)
        if new.health is not None and new.type is not CareEventType.OBSERVE:
            raise HealthRequiresObserveError(new.type)
        if new.photo_id is not None and (
            self._repository.photo_plant_id(new.photo_id) != plant_id
        ):
            raise PhotoNotForPlantError(plant_id, new.photo_id)
        return self._repository.add(plant_id, new)

    def list(self, plant_id: int) -> list[CareEvent]:
        """Return the plant's events (newest first); raise if the plant is missing."""
        self._guard_plant(plant_id)
        return self._repository.list_for_plant(plant_id)

    def delete(self, plant_id: int, event_id: int) -> None:
        """Delete one event; raise if the plant, then the event, is missing."""
        self._guard_plant(plant_id)
        self._repository.delete(plant_id, event_id)
