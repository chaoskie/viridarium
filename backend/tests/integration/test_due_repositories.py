"""Integration tests for the due batch reads + DueQueryService (TEST-001 primary).

Real-DB slice (TEST-003: nothing internal mocked). Covers the two new batch reads
(``latest_event_dates`` grouped MAX, ``enabled_for_plants`` enabled filter) and the
``DueQueryService`` assembly, including the N+1 statement-count guard via a SQLAlchemy
``before_cursor_execute`` listener.

Numbered cases trace to the foundation: B-I1..B-I19.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, timedelta

import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.care_event_repository import (
    SqlAlchemyCareEventRepository,
)
from viridarium.adapters.outbound.db.care_schedule_repository import (
    SqlAlchemyCareScheduleRepository,
)
from viridarium.adapters.outbound.db.engine import (
    create_db_engine,
    create_session_factory,
)
from viridarium.adapters.outbound.db.plant_repository import SqlAlchemyPlantRepository
from viridarium.application.due import DueQueryService
from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.care_event import CareEventType, NewCareEvent
from viridarium.domain.care_schedule import CareType, Dormancy, NewCareSchedule
from viridarium.domain.due import WinterWindow
from viridarium.domain.plant import NewPlant

pytestmark = pytest.mark.integration

_TODAY = date(2026, 7, 1)  # summer: outside the Nov 1 - Mar 1 default window


@pytest.fixture
def session_factory(migrated_settings: object) -> Iterator[sessionmaker[Session]]:
    """A session factory bound to the per-test migrated SQLite file."""
    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    engine = create_db_engine(url)
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def _new_plant(name: str) -> NewPlant:
    return NewPlant(
        name=name,
        species=None,
        location_id=None,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=(),
        archived=False,
    )


def _event(care_type: CareEventType, happened_on: date) -> NewCareEvent:
    return NewCareEvent(
        type=care_type, happened_on=happened_on, note=None, photo_id=None, health=None
    )


def _schedule(
    care_type: CareType,
    interval: int,
    *,
    enabled: bool = True,
    dormancy: Dormancy = Dormancy.WINTER_INTERVAL,
    winter: int | None = None,
) -> NewCareSchedule:
    return NewCareSchedule(
        care_type=care_type,
        interval_days=interval,
        winter_interval_days=winter,
        dormancy=dormancy,
        enabled=enabled,
    )


# ============================================== 4a. latest_event_dates (R1, AC8)
def test_groups_max_happened_on_per_plant_and_type(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I1: MAX(happened_on) per (plant, type), not the latest overall."""
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    d1, d2, d3 = date(2026, 6, 1), date(2026, 6, 10), date(2026, 6, 20)
    events.add(plant.id, _event(CareEventType.WATER, d1))
    events.add(plant.id, _event(CareEventType.WATER, d2))
    events.add(plant.id, _event(CareEventType.FEED, d3))

    result = events.latest_event_dates([plant.id], {CareType.WATER, CareType.FEED})

    assert result == {(plant.id, CareType.WATER): d2, (plant.id, CareType.FEED): d3}


def test_only_the_latest_counts_independent_of_insertion_order(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I2: MAX is order-independent (inserted out of date order)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    d1, d2, d3 = date(2026, 6, 1), date(2026, 6, 10), date(2026, 6, 20)
    events.add(plant.id, _event(CareEventType.WATER, d3))
    events.add(plant.id, _event(CareEventType.WATER, d1))
    events.add(plant.id, _event(CareEventType.WATER, d2))

    result = events.latest_event_dates([plant.id], {CareType.WATER})

    assert result == {(plant.id, CareType.WATER): d3}


def test_ignores_non_water_feed_event_types(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I3: repot/observe never appear (AC8 at the source)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    events.add(plant.id, _event(CareEventType.REPOT, date(2026, 6, 1)))
    events.add(plant.id, _event(CareEventType.OBSERVE, date(2026, 6, 2)))

    result = events.latest_event_dates([plant.id], {CareType.WATER, CareType.FEED})

    assert result == {}


def test_batches_multiple_plant_ids(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I4: one call returns keys for both plants."""
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    p1 = plants.add(_new_plant("A"))
    p2 = plants.add(_new_plant("B"))
    events.add(p1.id, _event(CareEventType.WATER, date(2026, 6, 1)))
    events.add(p2.id, _event(CareEventType.WATER, date(2026, 6, 2)))

    result = events.latest_event_dates([p1.id, p2.id], {CareType.WATER})

    assert result == {
        (p1.id, CareType.WATER): date(2026, 6, 1),
        (p2.id, CareType.WATER): date(2026, 6, 2),
    }


def test_empty_plant_ids_is_safe(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I5: empty plant_ids -> {} (no crash)."""
    events = SqlAlchemyCareEventRepository(session_factory)
    assert events.latest_event_dates([], {CareType.WATER, CareType.FEED}) == {}


def test_plant_with_no_events_key_absent(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I6: a plant with zero events -> no key (service .get -> None -> due today)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    assert events.latest_event_dates([plant.id], {CareType.WATER}) == {}


# ============================================== 4c. enabled_for_plants (R2, AC6)
def test_returns_enabled_schedules_grouped_per_plant(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I9: enabled water + feed grouped under the plant."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    schedules.upsert(plant.id, _schedule(CareType.WATER, 7))
    schedules.upsert(plant.id, _schedule(CareType.FEED, 30))

    result = schedules.enabled_for_plants([plant.id])

    assert plant.id in result
    assert {s.care_type for s in result[plant.id]} == {CareType.WATER, CareType.FEED}


def test_excludes_disabled_schedules(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I10: a disabled schedule is absent (AC6)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    schedules.upsert(plant.id, _schedule(CareType.WATER, 7, enabled=True))
    schedules.upsert(plant.id, _schedule(CareType.FEED, 30, enabled=False))

    result = schedules.enabled_for_plants([plant.id])

    assert [s.care_type for s in result[plant.id]] == [CareType.WATER]


def test_enabled_batches_multiple_plant_ids(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I11: both plants' keys present from one call."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    p1 = plants.add(_new_plant("A"))
    p2 = plants.add(_new_plant("B"))
    schedules.upsert(p1.id, _schedule(CareType.WATER, 7))
    schedules.upsert(p2.id, _schedule(CareType.WATER, 7))

    result = schedules.enabled_for_plants([p1.id, p2.id])

    assert set(result) == {p1.id, p2.id}


def test_enabled_empty_plant_ids_safe(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I12: empty plant_ids -> {} (no crash)."""
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    assert schedules.enabled_for_plants([]) == {}


def test_enabled_schedule_less_plant_key_absent(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I13: a plant with no schedules -> no key."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    assert schedules.enabled_for_plants([plant.id]) == {}


# ============================================== 4d. DueQueryService assembly (Q1)
class _DefaultSettingsProvider:
    """A settings provider returning the US-3.3 spec default (seasonal on, Nov1-Mar1).

    These US-3.3 assembly tests run with ``_TODAY`` in summer (outside the default
    window) and ``seasonal_aware=True``, so behaviour is identical to US-3.3.
    """

    def current(self) -> SeasonalSettings:
        return SeasonalSettings(
            seasonal_aware=True,
            window=WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1),
        )


def _due_service(session_factory: sessionmaker[Session]) -> DueQueryService:
    return DueQueryService(
        schedule_repository=SqlAlchemyCareScheduleRepository(session_factory),
        event_repository=SqlAlchemyCareEventRepository(session_factory),
        settings_provider=_DefaultSettingsProvider(),
        today_provider=lambda: _TODAY,
    )


def test_service_assembles_per_plant_due_lists(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I14: each schedule resolves against its own last-event date."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    schedules.upsert(plant.id, _schedule(CareType.WATER, 7))
    schedules.upsert(plant.id, _schedule(CareType.FEED, 14))
    water_on = date(2026, 6, 20)
    feed_on = date(2026, 6, 1)
    events.add(plant.id, _event(CareEventType.WATER, water_on))
    events.add(plant.id, _event(CareEventType.FEED, feed_on))

    result = _due_service(session_factory).for_plants([plant.id])

    by_type = {d.care_type: d for d in result[plant.id]}
    assert by_type[CareType.WATER].next_due == water_on + timedelta(days=7)
    assert by_type[CareType.FEED].next_due == feed_on + timedelta(days=14)


def test_service_new_plant_all_due_today(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I15: a schedule with no events -> due today (AC2)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    schedules.upsert(plant.id, _schedule(CareType.WATER, 7))

    result = _due_service(session_factory).for_plants([plant.id])

    assert result[plant.id][0].next_due == _TODAY
    assert result[plant.id][0].overdue_days == 0


def test_service_schedule_less_plant_empty_list(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I16: a schedule-less plant -> present key, empty list (NOT missing)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    result = _due_service(session_factory).for_plants([plant.id])
    assert result == {plant.id: []}


def test_service_disabled_schedule_omitted(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I17: a disabled schedule does not appear in the assembled output (AC6)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    plant = plants.add(_new_plant("Fern"))
    schedules.upsert(plant.id, _schedule(CareType.WATER, 7, enabled=True))
    schedules.upsert(plant.id, _schedule(CareType.FEED, 30, enabled=False))

    result = _due_service(session_factory).for_plants([plant.id])

    assert [d.care_type for d in result[plant.id]] == [CareType.WATER]


def test_service_empty_input_empty_mapping(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I18: empty input -> {}."""
    assert _due_service(session_factory).for_plants([]) == {}


# ============================================== 4d. N+1 guard (B-I19, AC7)
@contextmanager
def _count_statements(engine: Engine) -> Iterator[list[int]]:
    """Count executed statements on ``engine`` for the duration of the block."""
    counter = [0]

    def _on_execute(*_args: object, **_kwargs: object) -> None:
        counter[0] += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)


def _seed_plants_with_schedules_and_events(
    session_factory: sessionmaker[Session], n: int
) -> list[int]:
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    ids: list[int] = []
    for i in range(n):
        plant = plants.add(_new_plant(f"P{i}"))
        schedules.upsert(plant.id, _schedule(CareType.WATER, 7))
        schedules.upsert(plant.id, _schedule(CareType.FEED, 14))
        events.add(plant.id, _event(CareEventType.WATER, date(2026, 6, 1)))
        events.add(plant.id, _event(CareEventType.FEED, date(2026, 6, 2)))
        ids.append(plant.id)
    return ids


def test_service_query_count_is_bounded_no_n_plus_one(
    session_factory: sessionmaker[Session], migrated_settings: object
) -> None:
    """B-I19: statement count constant + small across N and 2N (CRITICAL, AC7)."""
    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    n_ids = _seed_plants_with_schedules_and_events(session_factory, 5)
    two_n_ids = n_ids + _seed_plants_with_schedules_and_events(session_factory, 5)

    counting_engine = create_db_engine(url)
    try:
        counting_factory = create_session_factory(counting_engine)
        service = DueQueryService(
            schedule_repository=SqlAlchemyCareScheduleRepository(counting_factory),
            event_repository=SqlAlchemyCareEventRepository(counting_factory),
            settings_provider=_DefaultSettingsProvider(),
            today_provider=lambda: _TODAY,
        )
        with _count_statements(counting_engine) as count_n:
            service.for_plants(n_ids)
        n_count = count_n[0]
        with _count_statements(counting_engine) as count_2n:
            service.for_plants(two_n_ids)
        two_n_count = count_2n[0]
    finally:
        counting_engine.dispose()

    assert n_count <= 3  # the two grouped reads (+ at most one connection setup)
    assert two_n_count == n_count  # does NOT scale with plant count
