"""Care-schedule use cases (ADR-B [TEMPLATE]).

A thin application service over the
:class:`~viridarium.domain.care_schedule.CareScheduleRepository` port. It returns domain
types (ARCH-007) and never translates domain errors into HTTP concerns (ADR-C).

The one piece of genuine application logic is the **plant-exists guard** (mirrors the
plant FK-existence guard): every operation checks ``plant_exists`` *first* and raises
:class:`~viridarium.domain.care_schedule.PlantNotFoundForScheduleError` (404) before
touching the repo, so a missing plant and a missing schedule report distinct reasons.
``get``/``delete`` on an existing plant then let the repo raise
:class:`~viridarium.domain.care_schedule.CareScheduleNotFoundError` (404) when the
schedule itself is absent (VIRIDARIUM-48).
"""

from __future__ import annotations

from viridarium.domain.care_schedule import (
    CareSchedule,
    CareScheduleRepository,
    CareType,
    NewCareSchedule,
    PlantNotFoundForScheduleError,
)


class CareScheduleService:
    """Use cases for a plant's care schedules, backed by a repository port."""

    def __init__(self, repository: CareScheduleRepository) -> None:
        self._repository = repository

    def _guard_plant(self, plant_id: int) -> None:
        """Reject an unknown plant before any per-schedule work (404)."""
        if not self._repository.plant_exists(plant_id):
            raise PlantNotFoundForScheduleError(plant_id)

    def upsert(self, plant_id: int, new: NewCareSchedule) -> CareSchedule:
        """Create-or-replace the schedule; raise if the plant is missing (CS1)."""
        self._guard_plant(plant_id)
        return self._repository.upsert(plant_id, new)

    def list(self, plant_id: int) -> list[CareSchedule]:
        """Return the plant's schedules (water-first); raise if the plant is missing."""
        self._guard_plant(plant_id)
        return self._repository.list_for_plant(plant_id)

    def get(self, plant_id: int, care_type: CareType) -> CareSchedule:
        """Return one schedule; raise if the plant, then the schedule, is missing."""
        self._guard_plant(plant_id)
        return self._repository.get(plant_id, care_type)

    def delete(self, plant_id: int, care_type: CareType) -> None:
        """Delete one schedule; raise if the plant, then the schedule, is missing."""
        self._guard_plant(plant_id)
        self._repository.delete(plant_id, care_type)
