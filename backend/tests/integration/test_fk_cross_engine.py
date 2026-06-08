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
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from tests.integration.conftest import make_alembic_config
from viridarium.adapters.outbound.db.engine import (
    create_db_engine,
    create_session_factory,
)
from viridarium.adapters.outbound.db.location_repository import (
    SqlAlchemyLocationRepository,
)
from viridarium.adapters.outbound.db.models import PlantTagModel
from viridarium.adapters.outbound.db.plant_repository import SqlAlchemyPlantRepository
from viridarium.domain.location import NewLocation
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
