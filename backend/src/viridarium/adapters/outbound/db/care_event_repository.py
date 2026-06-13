"""SQLAlchemy care-event repository (outbound adapter, ADR-B [TEMPLATE]).

Session-per-call: each method opens its own session and commits its own writes. The
module-level :func:`_to_domain` is the sole ORM<->domain mapping site (ARCH-009) so no
``CareEventModel`` ever leaks past this adapter. A missing or cross-plant row raises
:class:`CareEventNotFoundError` (the domain error), keeping HTTP concerns out of
persistence (ADR-C).

``list_for_plant`` implements the ordering contract: ``happened_on`` desc, then
``created_at`` desc, with the surrogate ``id`` desc as a final stable tiebreak (the
server-default ``created_at`` is second-granular on SQLite, so same-second appends
would otherwise tie; ``id`` desc preserves the created-at-desc intent).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import (
    CareEventModel,
    PhotoModel,
    PlantModel,
)
from viridarium.domain.care_event import (
    CareEvent,
    CareEventNotFoundError,
    CareEventType,
    Health,
    NewCareEvent,
)
from viridarium.domain.care_schedule import CareType


def _to_domain(model: CareEventModel) -> CareEvent:
    """Map a persisted ``CareEventModel`` to the domain :class:`CareEvent`."""
    return CareEvent(
        id=model.id,
        plant_id=model.plant_id,
        type=CareEventType(model.type),
        happened_on=model.happened_on,
        note=model.note,
        photo_id=model.photo_id,
        health=Health(model.health) if model.health is not None else None,
        created_at=model.created_at,
    )


class SqlAlchemyCareEventRepository:
    """Concrete :class:`~viridarium.domain.care_event.CareEventRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, plant_id: int, new: NewCareEvent) -> CareEvent:
        with self._session_factory() as session:
            model = CareEventModel(
                plant_id=plant_id,
                type=new.type.value,
                happened_on=new.happened_on,
                note=new.note,
                photo_id=new.photo_id,
                health=new.health.value if new.health is not None else None,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def list_for_plant(self, plant_id: int) -> list[CareEvent]:
        with self._session_factory() as session:
            models = session.scalars(
                select(CareEventModel)
                .where(CareEventModel.plant_id == plant_id)
                .order_by(
                    CareEventModel.happened_on.desc(),
                    CareEventModel.created_at.desc(),
                    CareEventModel.id.desc(),
                )
            ).all()
            return [_to_domain(m) for m in models]

    def latest_event_dates(
        self, plant_ids: list[int], types: set[CareType]
    ) -> dict[tuple[int, CareType], date]:
        """Grouped ``MAX(happened_on)`` per ``(plant_id, type)`` (US-3.3, ARCH-011).

        One standard ``SELECT ... GROUP BY plant_id, type`` over the given ids and the
        wire values of ``types``; portable across SQLite and PostgreSQL. Empty
        ``plant_ids`` short-circuits to ``{}`` without touching the DB.
        """
        if not plant_ids:
            return {}
        type_values = {t.value for t in types}
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    CareEventModel.plant_id,
                    CareEventModel.type,
                    func.max(CareEventModel.happened_on),
                )
                .where(
                    CareEventModel.plant_id.in_(plant_ids),
                    CareEventModel.type.in_(type_values),
                )
                .group_by(CareEventModel.plant_id, CareEventModel.type)
            ).all()
            return {
                (plant_id, CareType(type_value)): happened_on
                for plant_id, type_value, happened_on in rows
            }

    def delete(self, plant_id: int, event_id: int) -> None:
        with self._session_factory() as session:
            model = session.get(CareEventModel, event_id)
            if model is None or model.plant_id != plant_id:
                raise CareEventNotFoundError(plant_id, event_id)
            session.delete(model)
            session.commit()

    def plant_exists(self, plant_id: int) -> bool:
        with self._session_factory() as session:
            return session.get(PlantModel, plant_id) is not None

    def photo_plant_id(self, photo_id: int) -> int | None:
        with self._session_factory() as session:
            photo = session.get(PhotoModel, photo_id)
            return photo.plant_id if photo is not None else None
