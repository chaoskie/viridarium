"""SQLAlchemy plant repository (outbound adapter, ADR-B [TEMPLATE]).

Session-per-call: each method opens its own session from the injected factory and
commits its own writes. The module-level :func:`_to_domain` is the sole ORM<->domain
mapping site (anti-corruption, ARCH-009) so no ``PlantModel`` ever leaks past this
adapter. Missing rows raise :class:`PlantNotFoundError` (the domain error), keeping HTTP
concerns out of the persistence layer (ADR-C).

The list query is built portably (ARCH-011, D4): ``q``/``species`` use a lowered
``LIKE`` (both sides lowered so SQLite and PostgreSQL agree on case-folding);
``location_id`` is an exact match, ``homeless`` an ``IS NULL``, and ``tag`` an
``EXISTS`` subquery over ``plant_tag`` (no engine-specific JSON SQL). Tags are
written/replaced explicitly; the DB-level CASCADE removes them on plant delete and the
FK ``SET NULL`` orphans a plant on room delete (both require the SQLite foreign-keys
pragma set in ``engine.py``).
"""

from __future__ import annotations

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import (
    LocationModel,
    PlantModel,
    PlantTagModel,
)
from viridarium.domain.plant import (
    LightLevel,
    NewPlant,
    Plant,
    PlantFilter,
    PlantNotFoundError,
    PotMaterial,
)


def _to_domain(model: PlantModel, tags: tuple[str, ...]) -> Plant:
    """Map a persisted ``PlantModel`` (+ its tags) to the domain :class:`Plant`."""
    return Plant(
        id=model.id,
        name=model.name,
        species=model.species,
        location_id=model.location_id,
        acquired_on=model.acquired_on,
        pot_size_cm=model.pot_size_cm,
        pot_material=(
            PotMaterial(model.pot_material) if model.pot_material is not None else None
        ),
        light_level=(
            LightLevel(model.light_level) if model.light_level is not None else None
        ),
        notes=model.notes,
        tags=tags,
        archived=model.archived,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _load_tags(session: Session, plant_id: int) -> tuple[str, ...]:
    """Return the persisted tags for a plant, ordered for a stable response."""
    rows = session.scalars(
        select(PlantTagModel.tag)
        .where(PlantTagModel.plant_id == plant_id)
        .order_by(PlantTagModel.tag)
    ).all()
    return tuple(rows)


def _write_tags(session: Session, plant_id: int, tags: tuple[str, ...]) -> None:
    """Insert the tag rows for a plant (deduped by the composite PK upstream)."""
    for tag in dict.fromkeys(tags):
        session.add(PlantTagModel(plant_id=plant_id, tag=tag))


class SqlAlchemyPlantRepository:
    """Concrete :class:`~viridarium.domain.plant.PlantRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, new_plant: NewPlant) -> Plant:
        with self._session_factory() as session:
            model = self._apply_fields(PlantModel(), new_plant)
            session.add(model)
            session.flush()
            _write_tags(session, model.id, new_plant.tags)
            session.commit()
            session.refresh(model)
            return _to_domain(model, _load_tags(session, model.id))

    def list(self, plant_filter: PlantFilter) -> list[Plant]:
        with self._session_factory() as session:
            stmt = select(PlantModel)
            if plant_filter.q:
                needle = f"%{plant_filter.q.lower()}%"
                stmt = stmt.where(
                    func.lower(PlantModel.name).like(needle)
                    | func.lower(func.coalesce(PlantModel.species, "")).like(needle)
                )
            if plant_filter.species:
                needle = f"%{plant_filter.species.lower()}%"
                stmt = stmt.where(
                    func.lower(func.coalesce(PlantModel.species, "")).like(needle)
                )
            if plant_filter.location_id is not None:
                stmt = stmt.where(PlantModel.location_id == plant_filter.location_id)
            if plant_filter.homeless:
                stmt = stmt.where(PlantModel.location_id.is_(None))
            if plant_filter.tag:
                stmt = stmt.where(
                    exists().where(
                        (PlantTagModel.plant_id == PlantModel.id)
                        & (PlantTagModel.tag == plant_filter.tag)
                    )
                )
            if not plant_filter.include_archived:
                stmt = stmt.where(PlantModel.archived.is_(bool(plant_filter.archived)))
            stmt = stmt.order_by(PlantModel.name)
            models = session.scalars(stmt).all()
            return [_to_domain(m, _load_tags(session, m.id)) for m in models]

    def get(self, plant_id: int) -> Plant:
        with self._session_factory() as session:
            model = session.get(PlantModel, plant_id)
            if model is None:
                raise PlantNotFoundError(plant_id)
            return _to_domain(model, _load_tags(session, plant_id))

    def update(self, plant_id: int, new_plant: NewPlant) -> Plant:
        with self._session_factory() as session:
            model = session.get(PlantModel, plant_id)
            if model is None:
                raise PlantNotFoundError(plant_id)
            self._apply_fields(model, new_plant)
            # Full-replace the tag set (ADR-D): delete all, re-insert the new set.
            session.query(PlantTagModel).filter(
                PlantTagModel.plant_id == plant_id
            ).delete()
            session.flush()
            _write_tags(session, plant_id, new_plant.tags)
            session.commit()
            session.refresh(model)
            return _to_domain(model, _load_tags(session, plant_id))

    def delete(self, plant_id: int) -> None:
        with self._session_factory() as session:
            model = session.get(PlantModel, plant_id)
            if model is None:
                raise PlantNotFoundError(plant_id)
            session.delete(model)
            session.commit()

    def archive(self, plant_id: int) -> Plant:
        return self._set_archived(plant_id, archived=True)

    def unarchive(self, plant_id: int) -> Plant:
        return self._set_archived(plant_id, archived=False)

    def _set_archived(self, plant_id: int, *, archived: bool) -> Plant:
        """Set the archived flag (idempotent) or raise ``PlantNotFoundError``.

        Tags are untouched, so the plant's history is retained; ``updated_at`` bumps
        via the model's existing ``onupdate``.
        """
        with self._session_factory() as session:
            model = session.get(PlantModel, plant_id)
            if model is None:
                raise PlantNotFoundError(plant_id)
            model.archived = archived
            session.commit()
            session.refresh(model)
            return _to_domain(model, _load_tags(session, plant_id))

    def location_exists(self, location_id: int) -> bool:
        with self._session_factory() as session:
            return session.get(LocationModel, location_id) is not None

    @staticmethod
    def _apply_fields(model: PlantModel, new_plant: NewPlant) -> PlantModel:
        """Copy the client-supplied scalar fields onto an ORM model."""
        model.name = new_plant.name
        model.species = new_plant.species
        model.location_id = new_plant.location_id
        model.acquired_on = new_plant.acquired_on
        model.pot_size_cm = new_plant.pot_size_cm
        model.pot_material = (
            new_plant.pot_material.value if new_plant.pot_material is not None else None
        )
        model.light_level = (
            new_plant.light_level.value if new_plant.light_level is not None else None
        )
        model.notes = new_plant.notes
        model.archived = new_plant.archived
        return model
