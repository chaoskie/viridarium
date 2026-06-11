"""Unit tests for the care-event use case (TEST-002: no app, no DB, no I/O).

``CareEventService`` is exercised against a hand-written dict-backed fake of the
``CareEventRepository`` port (TEST-003: faking the port is allowed; only the real
persistence layer must not be mocked). The fake's ``plant_exists`` is backed by a
configurable set of "existing plant ids" and its ``photo_plant_id`` by a configurable
``photo_id -> plant_id`` mapping (the cross-aggregate photo-ownership lookup), so the
guards are observable without the app.

Per the test foundation (care-events §3), the economically-unit-reachable logic is the
**plant-exists guard** (B-U2/B-U10), the **cross-plant-photo guard** (B-U4/B-U5), the
**health-only-on-observe** domain rule (B-U6/B-U7/B-U8), and not-found propagation on
delete (B-U12). The frozen domain dataclasses + the ``CareEventType``/``Health``
StrEnums get no pure-data unit test (TEST-004 #2). The ``happened_on`` default (B-U9)
lives at the schema edge and is proven in integration (B-I1 / matrix M1 ``omitted``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from viridarium.application.care_events import CareEventService
from viridarium.domain.care_event import (
    CareEvent,
    CareEventNotFoundError,
    CareEventType,
    Health,
    HealthRequiresObserveError,
    NewCareEvent,
    PhotoNotForPlantError,
    PlantNotFoundForEventError,
)

pytestmark = pytest.mark.unit


def _new(
    *,
    type: CareEventType = CareEventType.WATER,  # mirrors the wire field name
    happened_on: date | None = None,
    note: str | None = None,
    photo_id: int | None = None,
    health: Health | None = None,
) -> NewCareEvent:
    return NewCareEvent(
        type=type,
        happened_on=happened_on or date(2026, 6, 1),
        note=note,
        photo_id=photo_id,
        health=health,
    )


class _FakeCareEventRepository:
    """Dict-backed fake of the ``CareEventRepository`` port; records calls."""

    def __init__(
        self,
        existing_plant_ids: set[int] | None = None,
        photo_owners: dict[int, int] | None = None,
    ) -> None:
        self._rows: dict[int, CareEvent] = {}
        self._next_id = 1
        self._plant_ids = existing_plant_ids if existing_plant_ids is not None else {1}
        self._photo_owners = photo_owners or {}
        self.calls: list[tuple[str, int]] = []

    def add(self, plant_id: int, new: NewCareEvent) -> CareEvent:
        event = CareEvent(
            id=self._next_id,
            plant_id=plant_id,
            type=new.type,
            happened_on=new.happened_on,
            note=new.note,
            photo_id=new.photo_id,
            health=new.health,
            created_at=datetime.now(UTC),
        )
        self._rows[self._next_id] = event
        self.calls.append(("add", self._next_id))
        self._next_id += 1
        return event

    def list_for_plant(self, plant_id: int) -> list[CareEvent]:
        self.calls.append(("list", plant_id))
        rows = [e for e in self._rows.values() if e.plant_id == plant_id]
        return sorted(rows, key=lambda e: (e.happened_on, e.created_at), reverse=True)

    def delete(self, plant_id: int, event_id: int) -> None:
        row = self._rows.get(event_id)
        if row is None or row.plant_id != plant_id:
            raise CareEventNotFoundError(plant_id, event_id)
        del self._rows[event_id]
        self.calls.append(("delete", event_id))

    def plant_exists(self, plant_id: int) -> bool:
        return plant_id in self._plant_ids

    def photo_plant_id(self, photo_id: int) -> int | None:
        return self._photo_owners.get(photo_id)


# --------------------------------------------------------------------------- create
def test_create_with_existing_plant_persists() -> None:  # B-U1
    service = CareEventService(_FakeCareEventRepository({1}))

    result = service.create(1, _new(note="first watering"))

    assert isinstance(result, CareEvent)
    assert result.plant_id == 1
    assert result.type == CareEventType.WATER
    assert result.happened_on == date(2026, 6, 1)
    assert result.note == "first watering"


def test_create_missing_plant_raises() -> None:  # B-U2
    repo = _FakeCareEventRepository(set())
    service = CareEventService(repo)

    with pytest.raises(PlantNotFoundForEventError) as exc:
        service.create(999, _new())

    assert exc.value.plant_id == 999
    assert repo.calls == []  # repo.add not reached


def test_create_with_same_plant_photo_persists() -> None:  # B-U3
    repo = _FakeCareEventRepository({1}, photo_owners={5: 1})
    service = CareEventService(repo)

    result = service.create(1, _new(type=CareEventType.OBSERVE, photo_id=5))

    assert result.photo_id == 5


def test_create_with_cross_plant_photo_raises() -> None:  # B-U4
    repo = _FakeCareEventRepository({1, 2}, photo_owners={5: 2})
    service = CareEventService(repo)

    with pytest.raises(PhotoNotForPlantError) as exc:
        service.create(1, _new(photo_id=5))

    assert exc.value.plant_id == 1
    assert exc.value.photo_id == 5
    assert repo.calls == []  # repo.add not reached


def test_create_with_nonexistent_photo_raises() -> None:  # B-U5
    repo = _FakeCareEventRepository({1}, photo_owners={})
    service = CareEventService(repo)

    with pytest.raises(PhotoNotForPlantError):
        service.create(1, _new(photo_id=999))

    assert repo.calls == []  # repo.add not reached


def test_create_missing_plant_wins_over_cross_plant_photo() -> None:
    """Guard order (foundation §3 note): a missing plant must not be masked by a
    photo error - the plant-exists guard fires first (VIRIDARIUM-48)."""
    repo = _FakeCareEventRepository({1}, photo_owners={5: 1})
    service = CareEventService(repo)

    with pytest.raises(PlantNotFoundForEventError):
        service.create(999, _new(photo_id=5))


def test_health_on_observe_accepted() -> None:  # B-U6
    service = CareEventService(_FakeCareEventRepository({1}))

    result = service.create(1, _new(type=CareEventType.OBSERVE, health=Health.GOOD))

    assert result.health == Health.GOOD


def test_health_on_non_observe_rejected() -> None:  # B-U7
    repo = _FakeCareEventRepository({1})
    service = CareEventService(repo)

    with pytest.raises(HealthRequiresObserveError):
        service.create(1, _new(type=CareEventType.WATER, health=Health.GOOD))

    assert repo.calls == []  # repo.add not reached


def test_observe_without_health_accepted() -> None:  # B-U8
    service = CareEventService(_FakeCareEventRepository({1}))

    result = service.create(1, _new(type=CareEventType.OBSERVE))

    assert result.health is None  # health optional even on observe


# ----------------------------------------------------------------------------- list
def test_list_missing_plant_raises() -> None:  # B-U10
    repo = _FakeCareEventRepository(set())
    service = CareEventService(repo)

    with pytest.raises(PlantNotFoundForEventError) as exc:
        service.list(999)

    assert exc.value.plant_id == 999
    assert repo.calls == []  # repo.list not reached


def test_list_happy_returns_rows() -> None:  # B-U11
    repo = _FakeCareEventRepository({1})
    service = CareEventService(repo)
    service.create(1, _new())
    service.create(1, _new(type=CareEventType.FEED))

    rows = service.list(1)

    assert {e.type for e in rows} == {CareEventType.WATER, CareEventType.FEED}


# --------------------------------------------------------------------------- delete
def test_delete_propagates_not_found() -> None:  # B-U12
    service = CareEventService(_FakeCareEventRepository({1}))

    with pytest.raises(CareEventNotFoundError) as exc:
        service.delete(1, 4242)

    assert exc.value.plant_id == 1
    assert exc.value.event_id == 4242


def test_delete_missing_plant_raises_plant_not_found() -> None:
    service = CareEventService(_FakeCareEventRepository({1}))

    with pytest.raises(PlantNotFoundForEventError) as exc:
        service.delete(999, 1)

    assert exc.value.plant_id == 999


def test_delete_happy_removes_row() -> None:  # B-U13
    repo = _FakeCareEventRepository({1})
    service = CareEventService(repo)
    created = service.create(1, _new())

    service.delete(1, created.id)

    assert service.list(1) == []
    assert ("delete", created.id) in repo.calls
