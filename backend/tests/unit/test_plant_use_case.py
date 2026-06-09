"""Unit tests for the plant use case (TEST-002: no app, no DB, no I/O).

``PlantService`` is exercised against a hand-written dict-backed fake of the
``PlantRepository`` port (TEST-003: faking the port is allowed; only the real
persistence layer must not be mocked). The fake's ``location_exists`` is backed by a
configurable set of "existing room ids".

The only economically-unit-reachable logic is the **FK-existence guard** (D1 / ADR-B):
homeless (``None``) is allowed; an existing ``location_id`` is allowed; a nonexistent
one raises ``LocationNotFoundForPlantError``. The frozen domain dataclasses and enums
get no unit test of their own (TEST-004 #2: would pass against any implementation).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from viridarium.application.plants import PlantService
from viridarium.domain.plant import (
    LightLevel,
    LocationNotFoundForPlantError,
    NewPlant,
    Plant,
    PlantFilter,
    PlantNotFoundError,
    PotMaterial,
)

pytestmark = pytest.mark.unit


def _new_plant(*, name: str = "Monstera", location_id: int | None = None) -> NewPlant:
    return NewPlant(
        name=name,
        species=None,
        location_id=location_id,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=(),
        archived=False,
    )


class _FakePlantRepository:
    """Dict-backed in-memory fake implementing the PlantRepository port."""

    def __init__(self, existing_location_ids: set[int] | None = None) -> None:
        self._rows: dict[int, Plant] = {}
        self._next_id = 1
        self._location_ids = existing_location_ids or set()

    def add(self, new_plant: NewPlant) -> Plant:
        now = datetime.now(UTC)
        plant = Plant(
            id=self._next_id,
            name=new_plant.name,
            species=new_plant.species,
            location_id=new_plant.location_id,
            acquired_on=new_plant.acquired_on,
            pot_size_cm=new_plant.pot_size_cm,
            pot_material=new_plant.pot_material,
            light_level=new_plant.light_level,
            notes=new_plant.notes,
            tags=new_plant.tags,
            archived=new_plant.archived,
            created_at=now,
            updated_at=now,
        )
        self._rows[self._next_id] = plant
        self._next_id += 1
        return plant

    def list(self, plant_filter: PlantFilter) -> list[Plant]:
        return sorted(self._rows.values(), key=lambda p: p.name)

    def get(self, plant_id: int) -> Plant:
        try:
            return self._rows[plant_id]
        except KeyError as exc:
            raise PlantNotFoundError(plant_id) from exc

    def update(self, plant_id: int, new_plant: NewPlant) -> Plant:
        existing = self.get(plant_id)
        updated = Plant(
            id=existing.id,
            name=new_plant.name,
            species=new_plant.species,
            location_id=new_plant.location_id,
            acquired_on=new_plant.acquired_on,
            pot_size_cm=new_plant.pot_size_cm,
            pot_material=new_plant.pot_material,
            light_level=new_plant.light_level,
            notes=new_plant.notes,
            tags=new_plant.tags,
            archived=new_plant.archived,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        self._rows[plant_id] = updated
        return updated

    def delete(self, plant_id: int) -> None:
        if plant_id not in self._rows:
            raise PlantNotFoundError(plant_id)
        del self._rows[plant_id]

    def archive(self, plant_id: int) -> Plant:
        existing = self.get(plant_id)
        updated = replace(existing, archived=True, updated_at=datetime.now(UTC))
        self._rows[plant_id] = updated
        return updated

    def unarchive(self, plant_id: int) -> Plant:
        existing = self.get(plant_id)
        updated = replace(existing, archived=False, updated_at=datetime.now(UTC))
        self._rows[plant_id] = updated
        return updated

    def location_exists(self, location_id: int) -> bool:
        return location_id in self._location_ids


# ----------------------------------------------------------------- FK-existence guard
def test_create_homeless_is_allowed() -> None:
    service = PlantService(_FakePlantRepository())

    created = service.create(_new_plant(location_id=None))

    assert created.location_id is None
    assert created.name == "Monstera"


def test_create_with_existing_location_is_allowed() -> None:
    service = PlantService(_FakePlantRepository(existing_location_ids={7}))

    created = service.create(_new_plant(location_id=7))

    assert created.location_id == 7


def test_create_nonexistent_location_raises() -> None:
    service = PlantService(_FakePlantRepository(existing_location_ids={1}))

    with pytest.raises(LocationNotFoundForPlantError) as exc_info:
        service.create(_new_plant(location_id=424242))

    assert exc_info.value.location_id == 424242


def test_update_nonexistent_location_raises() -> None:
    repo = _FakePlantRepository(existing_location_ids={1})
    service = PlantService(repo)
    created = service.create(_new_plant(location_id=1))

    with pytest.raises(LocationNotFoundForPlantError):
        service.update(created.id, _new_plant(location_id=424242))


# --------------------------------------------------------- plant-not-found propagation
def test_update_propagates_plant_not_found() -> None:
    service = PlantService(_FakePlantRepository())

    with pytest.raises(PlantNotFoundError):
        service.update(999, _new_plant(location_id=None))


def test_get_propagates_plant_not_found() -> None:
    service = PlantService(_FakePlantRepository())

    with pytest.raises(PlantNotFoundError):
        service.get(999)


def test_delete_propagates_plant_not_found() -> None:
    service = PlantService(_FakePlantRepository())

    with pytest.raises(PlantNotFoundError):
        service.delete(999)


# ------------------------------------------------------- archive / unarchive (US-2.4)
def test_archive_sets_flag() -> None:
    service = PlantService(_FakePlantRepository())
    created = service.create(_new_plant())

    archived = service.archive(created.id)

    assert archived.archived is True


def test_unarchive_clears_flag() -> None:
    service = PlantService(_FakePlantRepository())
    created = service.create(_new_plant())
    service.archive(created.id)

    unarchived = service.unarchive(created.id)

    assert unarchived.archived is False


def test_archive_propagates_plant_not_found() -> None:
    service = PlantService(_FakePlantRepository())

    with pytest.raises(PlantNotFoundError) as exc_info:
        service.archive(999)

    assert exc_info.value.plant_id == 999


def test_unarchive_propagates_plant_not_found() -> None:
    service = PlantService(_FakePlantRepository())

    with pytest.raises(PlantNotFoundError) as exc_info:
        service.unarchive(999)

    assert exc_info.value.plant_id == 999


# A couple of round-trip assertions that exercise the enum/date carrying paths so the
# guard's happy branch is observed with realistic values (still pure, no I/O).
def test_create_with_full_attributes_round_trips_through_fake() -> None:
    repo = _FakePlantRepository(existing_location_ids={3})
    service = PlantService(repo)

    created = service.create(
        NewPlant(
            name="Fiddle",
            species="Ficus lyrata",
            location_id=3,
            acquired_on=date(2026, 1, 15),
            pot_size_cm=14,
            pot_material=PotMaterial.TERRACOTTA,
            light_level=LightLevel.BRIGHT_INDIRECT,
            notes="north window",
            tags=("rare", "ficus"),
            archived=False,
        )
    )

    assert created.pot_material is PotMaterial.TERRACOTTA
    assert created.light_level is LightLevel.BRIGHT_INDIRECT
    assert created.tags == ("rare", "ficus")
    assert service.list(PlantFilter())[0].id == created.id
