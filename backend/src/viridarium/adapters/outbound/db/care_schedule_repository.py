"""SQLAlchemy care-schedule repository (outbound adapter, ADR-B [TEMPLATE]).

Session-per-call: each method opens its own session and commits its own writes. The
module-level :func:`_to_domain` is the sole ORM<->domain mapping site (ARCH-009) so no
``CareScheduleModel`` ever leaks past this adapter. A missing row raises
:class:`CareScheduleNotFoundError` (the domain error), keeping HTTP concerns out of
persistence (ADR-C).

``upsert`` is the keyed create-or-replace (CS1): it selects the row for
``(plant_id, care_type)`` and updates it in place when present, else inserts. This is
**portable** - no engine-specific ``ON CONFLICT`` (ARCH-011); the ``(plant_id,
care_type)`` unique constraint is the structural backstop. ``list_for_plant`` orders
water-first via a portable ``case()`` so the ordering does not depend on insert order.
"""

from __future__ import annotations

from sqlalchemy import case, select
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import CareScheduleModel, PlantModel
from viridarium.domain.care_schedule import (
    CareSchedule,
    CareScheduleNotFoundError,
    CareType,
    Dormancy,
    NewCareSchedule,
)

# Portable water-first ordering (CS1): a CASE over the stored string, not an enum sort.
_CARE_TYPE_ORDER = case(
    (CareScheduleModel.care_type == CareType.WATER.value, 0),
    (CareScheduleModel.care_type == CareType.FEED.value, 1),
    else_=2,
)


def _to_domain(model: CareScheduleModel) -> CareSchedule:
    """Map a persisted ``CareScheduleModel`` to the domain :class:`CareSchedule`."""
    return CareSchedule(
        id=model.id,
        plant_id=model.plant_id,
        care_type=CareType(model.care_type),
        interval_days=model.interval_days,
        winter_interval_days=model.winter_interval_days,
        dormancy=Dormancy(model.dormancy),
        enabled=model.enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyCareScheduleRepository:
    """Concrete :class:`~viridarium.domain.care_schedule.CareScheduleRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, plant_id: int, new: NewCareSchedule) -> CareSchedule:
        with self._session_factory() as session:
            model = self._load(session, plant_id, new.care_type)
            if model is None:
                model = CareScheduleModel(
                    plant_id=plant_id,
                    care_type=new.care_type.value,
                )
                session.add(model)
            model.interval_days = new.interval_days
            model.winter_interval_days = new.winter_interval_days
            model.dormancy = new.dormancy.value
            model.enabled = new.enabled
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def list_for_plant(self, plant_id: int) -> list[CareSchedule]:
        with self._session_factory() as session:
            models = session.scalars(
                select(CareScheduleModel)
                .where(CareScheduleModel.plant_id == plant_id)
                .order_by(_CARE_TYPE_ORDER)
            ).all()
            return [_to_domain(m) for m in models]

    def enabled_for_plants(self, plant_ids: list[int]) -> dict[int, list[CareSchedule]]:
        """Enabled schedules grouped per plant id (US-3.3 batch read, ARCH-011).

        One ``SELECT ... WHERE plant_id IN (:ids) AND enabled = true`` over the given
        ids; disabled rows are excluded. Empty ``plant_ids`` short-circuits to ``{}``.
        Rows are grouped into per-plant lists (water-first within a plant).
        """
        if not plant_ids:
            return {}
        with self._session_factory() as session:
            models = session.scalars(
                select(CareScheduleModel)
                .where(
                    CareScheduleModel.plant_id.in_(plant_ids),
                    CareScheduleModel.enabled.is_(True),
                )
                .order_by(_CARE_TYPE_ORDER)
            ).all()
            grouped: dict[int, list[CareSchedule]] = {}
            for model in models:
                grouped.setdefault(model.plant_id, []).append(_to_domain(model))
            return grouped

    def get(self, plant_id: int, care_type: CareType) -> CareSchedule:
        with self._session_factory() as session:
            model = self._load(session, plant_id, care_type)
            if model is None:
                raise CareScheduleNotFoundError(plant_id, care_type)
            return _to_domain(model)

    def delete(self, plant_id: int, care_type: CareType) -> None:
        with self._session_factory() as session:
            model = self._load(session, plant_id, care_type)
            if model is None:
                raise CareScheduleNotFoundError(plant_id, care_type)
            session.delete(model)
            session.commit()

    def plant_exists(self, plant_id: int) -> bool:
        with self._session_factory() as session:
            return session.get(PlantModel, plant_id) is not None

    @staticmethod
    def _load(
        session: Session, plant_id: int, care_type: CareType
    ) -> CareScheduleModel | None:
        """Load the row for ``(plant_id, care_type)`` or ``None``."""
        return session.scalars(
            select(CareScheduleModel).where(
                CareScheduleModel.plant_id == plant_id,
                CareScheduleModel.care_type == care_type.value,
            )
        ).first()
