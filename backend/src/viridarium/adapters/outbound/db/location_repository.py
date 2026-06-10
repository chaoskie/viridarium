"""SQLAlchemy location repository (outbound adapter, ADR-B [TEMPLATE]).

Session-per-call: each method opens its own session from the injected factory and
commits its own writes. The module-level :func:`_to_domain` is the sole ORM<->domain
mapping site (anti-corruption, ARCH-009) so no ``LocationModel`` ever leaks past this
adapter. Missing rows raise :class:`LocationNotFoundError` (the domain error), keeping
HTTP concerns out of the persistence layer (ADR-C).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import LocationModel
from viridarium.domain.location import (
    Location,
    LocationNotFoundError,
    NewLocation,
)


def _to_domain(model: LocationModel) -> Location:
    """Map a persisted ``LocationModel`` to the domain :class:`Location`."""
    return Location(
        id=model.id,
        name=model.name,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLocationRepository:
    """Concrete :class:`~viridarium.domain.location.LocationRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, new_location: NewLocation) -> Location:
        with self._session_factory() as session:
            model = LocationModel(name=new_location.name, notes=new_location.notes)
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def list_all(self) -> list[Location]:
        with self._session_factory() as session:
            models = session.scalars(
                select(LocationModel).order_by(LocationModel.name)
            ).all()
            return [_to_domain(model) for model in models]

    def get(self, location_id: int) -> Location:
        with self._session_factory() as session:
            model = session.get(LocationModel, location_id)
            if model is None:
                raise LocationNotFoundError(location_id)
            return _to_domain(model)

    def update(self, location_id: int, name: str, notes: str | None) -> Location:
        with self._session_factory() as session:
            model = session.get(LocationModel, location_id)
            if model is None:
                raise LocationNotFoundError(location_id)
            model.name = name
            model.notes = notes
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def delete(self, location_id: int) -> None:
        with self._session_factory() as session:
            model = session.get(LocationModel, location_id)
            if model is None:
                raise LocationNotFoundError(location_id)
            session.delete(model)
            session.commit()
