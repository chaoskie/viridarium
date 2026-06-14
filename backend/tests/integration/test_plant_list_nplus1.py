"""Integration tests for the plant-list N+1 fix (tech-debt plant-list-nplus1).

Real-DB slice (TEST-003: nothing internal mocked) over the two new batch reads:

* ``SqlAlchemyPlantRepository._load_tags_batch`` -> ``list``/``list_archived`` issue a
  bounded query count (no per-row tag query) while returning tags identically to the
  per-row ``_load_tags`` (AC1).
* ``SqlAlchemyPhotoRepository.cover_ids_for_plants`` -> one grouped read returning the
  ``is_cover`` photo id per plant, omitting no-cover plants, empty-ids safe (AC2).

The statement-count guard reuses the ``before_cursor_execute`` listener pattern of the
due tests. The dual-engine cover read is proven in ``test_fk_cross_engine.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.engine import (
    create_db_engine,
    create_session_factory,
)
from viridarium.adapters.outbound.db.photo_repository import (
    SqlAlchemyPhotoRepository,
)
from viridarium.adapters.outbound.db.plant_repository import SqlAlchemyPlantRepository
from viridarium.domain.photo import NewPhoto
from viridarium.domain.plant import NewPlant, PlantFilter

pytestmark = pytest.mark.integration


@pytest.fixture
def session_factory(migrated_settings: object) -> Iterator[sessionmaker[Session]]:
    """A session factory bound to the per-test migrated SQLite file."""
    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    engine = create_db_engine(url)
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def _new_plant(name: str, tags: tuple[str, ...] = ()) -> NewPlant:
    return NewPlant(
        name=name,
        species=None,
        location_id=None,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=tags,
        archived=False,
    )


def _new_photo(plant_id: int, name: str) -> NewPhoto:
    return NewPhoto(
        plant_id=plant_id,
        stored_filename=name,
        content_type="image/jpeg",
        size_bytes=10,
    )


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


# ====================================================== AC1: tag batch correctness
def test_list_returns_tags_identically_to_per_row_read(
    session_factory: sessionmaker[Session],
) -> None:
    """Tags per plant are unchanged: same content + ordering as the single-row read."""
    plants = SqlAlchemyPlantRepository(session_factory)
    p1 = plants.add(_new_plant("A", ("zebra", "alpha", "mango")))
    p2 = plants.add(_new_plant("B", ()))
    p3 = plants.add(_new_plant("C", ("solo",)))

    listed = {p.id: p for p in plants.list(PlantFilter())}

    # list tags equal the get() (single-row _load_tags) tags, per plant.
    assert listed[p1.id].tags == plants.get(p1.id).tags == ("alpha", "mango", "zebra")
    assert listed[p2.id].tags == plants.get(p2.id).tags == ()
    assert listed[p3.id].tags == plants.get(p3.id).tags == ("solo",)


def test_list_archived_returns_tags_correctly(
    session_factory: sessionmaker[Session],
) -> None:
    """``list`` with ``archived=True`` carries each archived plant's own tags."""
    plants = SqlAlchemyPlantRepository(session_factory)
    active = plants.add(_new_plant("Active", ("keep",)))
    archived = plants.add(_new_plant("Archived", ("beta", "alpha")))
    plants.archive(archived.id)

    listed = {p.id: p for p in plants.list(PlantFilter(archived=True))}

    assert set(listed) == {archived.id}
    assert listed[archived.id].tags == ("alpha", "beta")
    # the active plant's tags are untouched on its own (active) read
    assert plants.get(active.id).tags == ("keep",)


def test_list_no_cross_plant_tag_bleed(
    session_factory: sessionmaker[Session],
) -> None:
    """The batch read keys tags to the right plant (no bleed across plants)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    p1 = plants.add(_new_plant("A", ("a1", "a2")))
    p2 = plants.add(_new_plant("B", ("b1",)))

    listed = {p.id: p for p in plants.list(PlantFilter())}

    assert listed[p1.id].tags == ("a1", "a2")
    assert listed[p2.id].tags == ("b1",)


# ====================================================== AC1: bounded query count
def test_list_tag_query_count_bounded_regardless_of_plant_count(
    session_factory: sessionmaker[Session], migrated_settings: object
) -> None:
    """``list`` issues no per-row tag query: constant statements over N and 2N."""
    plants = SqlAlchemyPlantRepository(session_factory)
    for i in range(5):
        plants.add(_new_plant(f"N{i}", (f"t{i}a", f"t{i}b")))

    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    counting_engine = create_db_engine(url)
    try:
        counting_factory = create_session_factory(counting_engine)
        counting_repo = SqlAlchemyPlantRepository(counting_factory)
        with _count_statements(counting_engine) as count_n:
            counting_repo.list(PlantFilter())
        n_count = count_n[0]

        for i in range(5):
            plants.add(_new_plant(f"M{i}", (f"m{i}a", f"m{i}b")))
        with _count_statements(counting_engine) as count_2n:
            counting_repo.list(PlantFilter())
        two_n_count = count_2n[0]
    finally:
        counting_engine.dispose()

    # the plant scan + one grouped tag read (+ at most one connection setup)
    assert n_count <= 3
    assert two_n_count == n_count  # flat: no per-plant tag query


# ====================================================== AC2: cover_ids_for_plants
def test_cover_ids_returns_cover_id_per_plant(
    session_factory: sessionmaker[Session],
) -> None:
    """Returns the ``is_cover`` photo id keyed by plant id."""
    plants = SqlAlchemyPlantRepository(session_factory)
    photos = SqlAlchemyPhotoRepository(session_factory)
    p1 = plants.add(_new_plant("A"))
    p2 = plants.add(_new_plant("B"))
    cover1 = photos.add(_new_photo(p1.id, "a-cover.jpg"), make_cover=True)
    photos.add(_new_photo(p1.id, "a-extra.jpg"), make_cover=False)
    cover2 = photos.add(_new_photo(p2.id, "b-cover.jpg"), make_cover=True)

    result = photos.cover_ids_for_plants([p1.id, p2.id])

    assert result == {p1.id: cover1.id, p2.id: cover2.id}


def test_cover_ids_omits_plants_without_a_cover(
    session_factory: sessionmaker[Session],
) -> None:
    """A plant with no photos (or no cover) gets no key (not a null entry)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    photos = SqlAlchemyPhotoRepository(session_factory)
    with_cover = plants.add(_new_plant("WithCover"))
    no_photos = plants.add(_new_plant("NoPhotos"))
    cover = photos.add(_new_photo(with_cover.id, "c.jpg"), make_cover=True)

    result = photos.cover_ids_for_plants([with_cover.id, no_photos.id])

    assert result == {with_cover.id: cover.id}
    assert no_photos.id not in result


def test_cover_ids_empty_plant_ids_is_safe(
    migrated_settings: object,
) -> None:
    """Empty plant_ids -> {} without touching the DB (no query issued)."""
    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    counting_engine = create_db_engine(url)
    try:
        counting_factory = create_session_factory(counting_engine)
        photos = SqlAlchemyPhotoRepository(counting_factory)
        with _count_statements(counting_engine) as count:
            result = photos.cover_ids_for_plants([])
    finally:
        counting_engine.dispose()

    assert result == {}
    assert count[0] == 0  # short-circuits, no query issued


def test_cover_ids_query_count_bounded(
    session_factory: sessionmaker[Session], migrated_settings: object
) -> None:
    """``cover_ids_for_plants`` is one query regardless of plant count (AC2)."""
    plants = SqlAlchemyPlantRepository(session_factory)
    photos = SqlAlchemyPhotoRepository(session_factory)
    ids: list[int] = []
    for i in range(5):
        p = plants.add(_new_plant(f"P{i}"))
        photos.add(_new_photo(p.id, f"cover-{i}.jpg"), make_cover=True)
        ids.append(p.id)

    url: str = migrated_settings.database_url  # type: ignore[attr-defined]
    counting_engine = create_db_engine(url)
    try:
        counting_factory = create_session_factory(counting_engine)
        counting_repo = SqlAlchemyPhotoRepository(counting_factory)
        with _count_statements(counting_engine) as count:
            counting_repo.cover_ids_for_plants(ids)
    finally:
        counting_engine.dispose()

    assert count[0] <= 2  # the single grouped read (+ at most one connection setup)
