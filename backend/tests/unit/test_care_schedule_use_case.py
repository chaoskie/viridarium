"""Unit tests for the care-schedule use case (TEST-002: no app, no DB, no I/O).

``CareScheduleService`` is exercised against a hand-written dict-backed fake of the
``CareScheduleRepository`` port (TEST-003: faking the port is allowed; only the real
persistence layer must not be mocked). The fake is keyed by ``(plant_id, care_type)``
so even at the fake level a second upsert overwrites rather than adds a second row, and
its ``plant_exists`` is backed by a configurable set of "existing plant ids".

The only economically-unit-reachable logic is the **plant-exists guard** (all four
operations -> ``PlantNotFoundForScheduleError``) and the **not-found propagation**
(get/delete on an existing plant -> ``CareScheduleNotFoundError``).
The frozen domain dataclasses + the ``CareType``/
``Dormancy`` StrEnums get no unit test of their own (TEST-004 #2: would pass against any
implementation); the dormancy-default-by-care-type logic lives in the router and is
proven through the integration matrix.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from viridarium.application.care_schedules import CareScheduleService
from viridarium.domain.care_schedule import (
    CareSchedule,
    CareScheduleNotFoundError,
    CareType,
    Dormancy,
    NewCareSchedule,
    PlantNotFoundForScheduleError,
)

pytestmark = pytest.mark.unit


def _new(
    *,
    care_type: CareType = CareType.WATER,
    interval_days: int = 7,
    winter_interval_days: int | None = None,
    dormancy: Dormancy = Dormancy.WINTER_INTERVAL,
    enabled: bool = True,
) -> NewCareSchedule:
    return NewCareSchedule(
        care_type=care_type,
        interval_days=interval_days,
        winter_interval_days=winter_interval_days,
        dormancy=dormancy,
        enabled=enabled,
    )


class _FakeCareScheduleRepository:
    """Dict-backed fake keyed by ``(plant_id, care_type)`` (mirrors the real port)."""

    def __init__(self, existing_plant_ids: set[int] | None = None) -> None:
        self._rows: dict[tuple[int, CareType], CareSchedule] = {}
        self._next_id = 1
        self._plant_ids = existing_plant_ids if existing_plant_ids is not None else {1}

    def upsert(self, plant_id: int, new: NewCareSchedule) -> CareSchedule:
        now = datetime.now(UTC)
        key = (plant_id, new.care_type)
        existing = self._rows.get(key)
        schedule = CareSchedule(
            id=existing.id if existing else self._next_id,
            plant_id=plant_id,
            care_type=new.care_type,
            interval_days=new.interval_days,
            winter_interval_days=new.winter_interval_days,
            dormancy=new.dormancy,
            enabled=new.enabled,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        if existing is None:
            self._next_id += 1
        self._rows[key] = schedule
        return schedule

    def list_for_plant(self, plant_id: int) -> list[CareSchedule]:
        rows = [s for (pid, _ct), s in self._rows.items() if pid == plant_id]
        order = {CareType.WATER: 0, CareType.FEED: 1}
        return sorted(rows, key=lambda s: order[s.care_type])

    def get(self, plant_id: int, care_type: CareType) -> CareSchedule:
        schedule = self._rows.get((plant_id, care_type))
        if schedule is None:
            raise CareScheduleNotFoundError(plant_id, care_type)
        return schedule

    def delete(self, plant_id: int, care_type: CareType) -> None:
        if (plant_id, care_type) not in self._rows:
            raise CareScheduleNotFoundError(plant_id, care_type)
        del self._rows[(plant_id, care_type)]

    def plant_exists(self, plant_id: int) -> bool:
        return plant_id in self._plant_ids


def test_upsert_with_existing_plant_persists() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))

    result = service.upsert(1, _new(interval_days=10))

    assert isinstance(result, CareSchedule)
    assert result.plant_id == 1
    assert result.care_type == CareType.WATER
    assert result.interval_days == 10


def test_upsert_replaces_same_key_in_fake() -> None:
    repo = _FakeCareScheduleRepository({1})
    service = CareScheduleService(repo)

    service.upsert(1, _new(interval_days=7))
    service.upsert(1, _new(interval_days=14))

    rows = service.list(1)
    assert len(rows) == 1
    assert rows[0].interval_days == 14  # the second value won; never a second row


def test_upsert_missing_plant_raises() -> None:
    repo = _FakeCareScheduleRepository(set())
    service = CareScheduleService(repo)

    with pytest.raises(PlantNotFoundForScheduleError) as exc:
        service.upsert(999, _new())

    assert exc.value.plant_id == 999
    assert repo.list_for_plant(999) == []  # repo.upsert not reached


def test_list_with_existing_plant_returns_rows() -> None:
    repo = _FakeCareScheduleRepository({1})
    service = CareScheduleService(repo)
    service.upsert(1, _new(care_type=CareType.FEED, dormancy=Dormancy.PAUSED))
    service.upsert(1, _new(care_type=CareType.WATER))

    rows = service.list(1)

    assert [s.care_type for s in rows] == [CareType.WATER, CareType.FEED]


def test_list_missing_plant_raises() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository(set()))

    with pytest.raises(PlantNotFoundForScheduleError) as exc:
        service.list(999)

    assert exc.value.plant_id == 999


def test_get_propagates_care_schedule_not_found() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))

    with pytest.raises(CareScheduleNotFoundError) as exc:
        service.get(1, CareType.FEED)

    assert exc.value.plant_id == 1
    assert exc.value.care_type == CareType.FEED


def test_get_missing_plant_raises_plant_not_found() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))

    with pytest.raises(PlantNotFoundForScheduleError) as exc:
        service.get(999, CareType.WATER)

    assert exc.value.plant_id == 999


def test_get_happy_returns_row() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))
    service.upsert(1, _new())

    result = service.get(1, CareType.WATER)

    assert result.care_type == CareType.WATER


def test_delete_propagates_care_schedule_not_found() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))

    with pytest.raises(CareScheduleNotFoundError):
        service.delete(1, CareType.WATER)


def test_delete_missing_plant_raises_plant_not_found() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))

    with pytest.raises(PlantNotFoundForScheduleError) as exc:
        service.delete(999, CareType.WATER)

    assert exc.value.plant_id == 999


def test_delete_happy_removes_row() -> None:
    service = CareScheduleService(_FakeCareScheduleRepository({1}))
    service.upsert(1, _new())

    service.delete(1, CareType.WATER)

    assert service.list(1) == []
