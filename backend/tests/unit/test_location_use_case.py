"""Unit tests for the location use case (TEST-002: no app, no DB, no I/O).

``LocationService`` is exercised against a hand-written dict-backed fake of the
``LocationRepository`` port (TEST-003: faking the port is allowed; only the real
persistence layer must not be mocked). The frozen domain dataclasses get no unit
test of their own (TEST-004 #2: that would pass against any implementation).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from viridarium.application.locations import LocationService
from viridarium.domain.location import (
    Location,
    LocationNotFoundError,
    NewLocation,
)

pytestmark = pytest.mark.unit


class _FakeLocationRepository:
    """Dict-backed in-memory fake implementing the LocationRepository port."""

    def __init__(self) -> None:
        self._rows: dict[int, Location] = {}
        self._next_id = 1

    def add(self, new_location: NewLocation) -> Location:
        now = datetime.now(UTC)
        location = Location(
            id=self._next_id,
            name=new_location.name,
            notes=new_location.notes,
            created_at=now,
            updated_at=now,
        )
        self._rows[self._next_id] = location
        self._next_id += 1
        return location

    def list_all(self) -> list[Location]:
        return sorted(self._rows.values(), key=lambda loc: loc.name)

    def get(self, location_id: int) -> Location:
        try:
            return self._rows[location_id]
        except KeyError as exc:
            raise LocationNotFoundError(location_id) from exc

    def update(self, location_id: int, name: str, notes: str | None) -> Location:
        existing = self.get(location_id)
        updated = Location(
            id=existing.id,
            name=name,
            notes=notes,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        self._rows[location_id] = updated
        return updated

    def delete(self, location_id: int) -> None:
        if location_id not in self._rows:
            raise LocationNotFoundError(location_id)
        del self._rows[location_id]


def test_create_maps_new_location_and_returns_created() -> None:
    service = LocationService(_FakeLocationRepository())

    created = service.create(NewLocation(name="Greenhouse", notes="south"))

    assert created.id is not None
    assert created.name == "Greenhouse"
    assert created.notes == "south"


def test_list_returns_all_locations() -> None:
    service = LocationService(_FakeLocationRepository())
    service.create(NewLocation(name="Shed", notes=None))
    service.create(NewLocation(name="Attic", notes=None))

    result = service.list()

    assert [loc.name for loc in result] == ["Attic", "Shed"]


def test_list_returns_empty_when_no_locations() -> None:
    service = LocationService(_FakeLocationRepository())

    assert service.list() == []


def test_get_returns_location() -> None:
    service = LocationService(_FakeLocationRepository())
    created = service.create(NewLocation(name="Balcony", notes=None))

    assert service.get(created.id) == created


def test_get_propagates_not_found() -> None:
    service = LocationService(_FakeLocationRepository())

    with pytest.raises(LocationNotFoundError):
        service.get(999)


def test_update_returns_updated_location() -> None:
    service = LocationService(_FakeLocationRepository())
    created = service.create(NewLocation(name="Old", notes=None))

    updated = service.update(created.id, name="New", notes="renamed")

    assert updated.name == "New"
    assert updated.notes == "renamed"
    assert updated.created_at == created.created_at


def test_update_propagates_not_found() -> None:
    service = LocationService(_FakeLocationRepository())

    with pytest.raises(LocationNotFoundError):
        service.update(999, name="x", notes=None)


def test_delete_returns_none_on_success() -> None:
    service = LocationService(_FakeLocationRepository())
    created = service.create(NewLocation(name="Temp", notes=None))

    assert service.delete(created.id) is None


def test_delete_propagates_not_found() -> None:
    service = LocationService(_FakeLocationRepository())

    with pytest.raises(LocationNotFoundError):
        service.delete(999)
