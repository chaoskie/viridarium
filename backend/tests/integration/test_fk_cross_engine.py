"""Cross-engine FK on-delete *runtime* behaviour (ARCH-011, design D1, AC7/AC8).

The other integration tests pin a per-test SQLite file for isolation, so they never
exercise FK actions on PostgreSQL. This test instead resolves its engine from
``DATABASE_URL``: the CI ``postgres`` leg runs the real SET NULL / CASCADE behaviour
against PostgreSQL, while locally / the ``sqlite`` leg it runs against SQLite (where the
engine's ``PRAGMA foreign_keys=ON`` makes the actions fire). This is the dual-engine
test mandated by design D1 / AC7 — proving the behaviour on *both* engines, not just
that the DDL applies.

It is self-contained (builds its own engine, migrates to head, cleans up its own rows)
so it adds no cross-test state on the shared PostgreSQL database.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from tests.integration.conftest import make_alembic_config
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
from viridarium.adapters.outbound.db.location_repository import (
    SqlAlchemyLocationRepository,
)
from viridarium.adapters.outbound.db.models import (
    CareEventModel,
    CareScheduleModel,
    PhotoModel,
    PlantTagModel,
)
from viridarium.adapters.outbound.db.photo_repository import (
    SqlAlchemyPhotoRepository,
)
from viridarium.adapters.outbound.db.plant_repository import SqlAlchemyPlantRepository
from viridarium.domain.care_event import CareEventType, NewCareEvent
from viridarium.domain.care_schedule import CareType, Dormancy, NewCareSchedule
from viridarium.domain.location import NewLocation
from viridarium.domain.photo import NewPhoto
from viridarium.domain.plant import NewPlant, PlantNotFoundError

pytestmark = pytest.mark.integration


def _new_plant(name: str, location_id: int | None, tags: tuple[str, ...]) -> NewPlant:
    return NewPlant(
        name=name,
        species=None,
        location_id=location_id,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=tags,
        archived=False,
    )


@pytest.fixture
def fk_engine(tmp_path: Path) -> Iterator[Engine]:
    """Engine under test: ``DATABASE_URL`` when it points at a non-SQLite engine
    (the CI postgres leg), otherwise a fresh per-test SQLite file. Migrated to head;
    idempotent if the CI step already upgraded the shared database."""
    url = os.environ.get("DATABASE_URL", "")
    if not url or url.startswith("sqlite"):
        url = f"sqlite:///{tmp_path / 'fk.db'}"
    command.upgrade(make_alembic_config(url), "head")
    engine = create_db_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()


def _count_tag_rows(session_factory: sessionmaker[Session], plant_id: int) -> int:
    with session_factory() as session:
        return (
            session.scalar(
                select(func.count())
                .select_from(PlantTagModel)
                .where(PlantTagModel.plant_id == plant_id)
            )
            or 0
        )


def _count_photo_rows(session_factory: sessionmaker[Session], plant_id: int) -> int:
    with session_factory() as session:
        return (
            session.scalar(
                select(func.count())
                .select_from(PhotoModel)
                .where(PhotoModel.plant_id == plant_id)
            )
            or 0
        )


def _count_care_schedule_rows(
    session_factory: sessionmaker[Session], plant_id: int
) -> int:
    with session_factory() as session:
        return (
            session.scalar(
                select(func.count())
                .select_from(CareScheduleModel)
                .where(CareScheduleModel.plant_id == plant_id)
            )
            or 0
        )


def _count_care_event_rows(
    session_factory: sessionmaker[Session], plant_id: int
) -> int:
    with session_factory() as session:
        return (
            session.scalar(
                select(func.count())
                .select_from(CareEventModel)
                .where(CareEventModel.plant_id == plant_id)
            )
            or 0
        )


def _new_event(photo_id: int | None = None) -> NewCareEvent:
    return NewCareEvent(
        type=CareEventType.OBSERVE if photo_id else CareEventType.WATER,
        happened_on=date(2026, 6, 1),
        note=None,
        photo_id=photo_id,
        health=None,
    )


def test_deleting_a_room_orphans_its_plants_to_homeless(fk_engine: Engine) -> None:
    """SET NULL on the real engine: delete a room -> its plant goes homeless and
    survives with history/tags intact (D-009 option C baseline, AC7)."""
    session_factory = create_session_factory(fk_engine)
    locations = SqlAlchemyLocationRepository(session_factory)
    plants = SqlAlchemyPlantRepository(session_factory)

    room = locations.add(NewLocation(name="FK cross-engine room", notes=None))
    plant = plants.add(_new_plant("FK cross-engine plant", room.id, ("alpha", "beta")))
    try:
        locations.delete(room.id)

        orphaned = plants.get(plant.id)
        assert orphaned.location_id is None  # SET NULL fired (homeless)
        assert orphaned.name == "FK cross-engine plant"  # not deleted
        assert orphaned.tags == ("alpha", "beta")  # history intact
    finally:
        plants.delete(plant.id)


def test_deleting_a_plant_cascades_its_tag_rows(fk_engine: Engine) -> None:
    """CASCADE on the real engine: deleting a plant removes its plant_tag rows (AC8)."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)

    plant = plants.add(_new_plant("FK cascade plant", None, ("gamma", "delta")))
    assert _count_tag_rows(session_factory, plant.id) == 2

    plants.delete(plant.id)

    assert _count_tag_rows(session_factory, plant.id) == 0  # CASCADE removed the rows
    with pytest.raises(PlantNotFoundError):
        plants.get(plant.id)


def test_deleting_a_plant_cascades_its_photo_rows(fk_engine: Engine) -> None:
    """CASCADE on the real engine: deleting a plant removes its photo rows (AC8).

    Proves the DB-row CASCADE on both engines; the file-cleanup half is app-level and
    covered once in the SQLite endpoint suite (test_plant_delete_cleans_photo_files)."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)
    photos = SqlAlchemyPhotoRepository(session_factory)

    plant = plants.add(_new_plant("FK photo cascade plant", None, ()))
    photos.add(
        NewPhoto(
            plant_id=plant.id,
            stored_filename="fk-a.jpg",
            content_type="image/jpeg",
            size_bytes=10,
        ),
        make_cover=True,
    )
    photos.add(
        NewPhoto(
            plant_id=plant.id,
            stored_filename="fk-b.png",
            content_type="image/png",
            size_bytes=10,
        ),
        make_cover=False,
    )
    assert _count_photo_rows(session_factory, plant.id) == 2

    plants.delete(plant.id)

    assert _count_photo_rows(session_factory, plant.id) == 0  # CASCADE fired


def test_deleting_a_plant_cascades_its_care_schedule_rows(fk_engine: Engine) -> None:
    """CASCADE on the real engine: a plant delete removes its care_schedule rows (AC7).

    Proves the DB-row CASCADE on both engines (SQLite local, Postgres CI leg). No
    app-level cleanup this story (no files), so this is the sole cascade proof."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)

    plant = plants.add(_new_plant("FK schedule cascade plant", None, ()))
    schedules.upsert(
        plant.id,
        NewCareSchedule(
            care_type=CareType.WATER,
            interval_days=7,
            winter_interval_days=None,
            dormancy=Dormancy.WINTER_INTERVAL,
            enabled=True,
        ),
    )
    schedules.upsert(
        plant.id,
        NewCareSchedule(
            care_type=CareType.FEED,
            interval_days=30,
            winter_interval_days=None,
            dormancy=Dormancy.PAUSED,
            enabled=True,
        ),
    )
    assert _count_care_schedule_rows(session_factory, plant.id) == 2

    plants.delete(plant.id)

    assert _count_care_schedule_rows(session_factory, plant.id) == 0  # CASCADE fired


def test_deleting_a_plant_cascades_its_care_event_rows(fk_engine: Engine) -> None:
    """CASCADE on the real engine: a plant delete removes its care_event rows
    (B-I35, AC5): the history dies with the plant, on both engines."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)

    plant = plants.add(_new_plant("FK event cascade plant", None, ()))
    events.add(plant.id, _new_event())
    events.add(plant.id, _new_event())
    assert _count_care_event_rows(session_factory, plant.id) == 2

    plants.delete(plant.id)

    assert _count_care_event_rows(session_factory, plant.id) == 0  # CASCADE fired


def test_deleting_a_photo_nulls_event_photo_id(fk_engine: Engine) -> None:
    """SET NULL on the real engine: deleting the linked photo severs the event's
    ``photo_id`` but preserves the event row (B-I36, ARCH-011). Self-cleans."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)
    photos = SqlAlchemyPhotoRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)

    plant = plants.add(_new_plant("FK photo set-null plant", None, ()))
    try:
        photo = photos.add(
            NewPhoto(
                plant_id=plant.id,
                stored_filename="fk-event-link.jpg",
                content_type="image/jpeg",
                size_bytes=10,
            ),
            make_cover=True,
        )
        event = events.add(plant.id, _new_event(photo_id=photo.id))
        assert event.photo_id == photo.id

        photos.delete(plant.id, photo.id)

        reloaded = events.list_for_plant(plant.id)
        assert [e.id for e in reloaded] == [event.id]  # event preserved
        assert reloaded[0].photo_id is None  # SET NULL fired
    finally:
        plants.delete(plant.id)


def test_latest_event_dates_grouped_max_runs_on_both_engines(
    fk_engine: Engine,
) -> None:
    """B-I33 (US-3.3, ARCH-011): the grouped MAX(happened_on) GROUP BY plant_id, type
    and the enabled = true filter run identically on the engine resolved from
    ``DATABASE_URL`` (SQLite local, PostgreSQL CI leg). Self-cleans its own rows."""
    session_factory = create_session_factory(fk_engine)
    plants = SqlAlchemyPlantRepository(session_factory)
    events = SqlAlchemyCareEventRepository(session_factory)
    schedules = SqlAlchemyCareScheduleRepository(session_factory)

    plant = plants.add(_new_plant("FK due grouped-MAX plant", None, ()))
    try:
        d1, d2, d3 = date(2026, 6, 1), date(2026, 6, 10), date(2026, 6, 20)
        events.add(
            plant.id,
            NewCareEvent(
                type=CareEventType.WATER,
                happened_on=d1,
                note=None,
                photo_id=None,
                health=None,
            ),
        )
        events.add(
            plant.id,
            NewCareEvent(
                type=CareEventType.WATER,
                happened_on=d2,
                note=None,
                photo_id=None,
                health=None,
            ),
        )
        events.add(
            plant.id,
            NewCareEvent(
                type=CareEventType.FEED,
                happened_on=d3,
                note=None,
                photo_id=None,
                health=None,
            ),
        )

        latest = events.latest_event_dates([plant.id], {CareType.WATER, CareType.FEED})
        assert latest == {
            (plant.id, CareType.WATER): d2,
            (plant.id, CareType.FEED): d3,
        }

        # The enabled = true filter shares the IN (:ids) + boolean shape that differs
        # most between engines (SQLite has no native boolean).
        schedules.upsert(
            plant.id,
            NewCareSchedule(
                care_type=CareType.WATER,
                interval_days=7,
                winter_interval_days=None,
                dormancy=Dormancy.WINTER_INTERVAL,
                enabled=True,
            ),
        )
        schedules.upsert(
            plant.id,
            NewCareSchedule(
                care_type=CareType.FEED,
                interval_days=30,
                winter_interval_days=None,
                dormancy=Dormancy.PAUSED,
                enabled=False,
            ),
        )
        enabled = schedules.enabled_for_plants([plant.id])
        assert [s.care_type for s in enabled[plant.id]] == [CareType.WATER]
    finally:
        plants.delete(plant.id)
