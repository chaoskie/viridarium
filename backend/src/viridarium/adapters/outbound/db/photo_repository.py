"""SQLAlchemy photo repository (outbound adapter, ADR-B [TEMPLATE]).

Session-per-call: each method opens its own session and commits its own writes. The
module-level :func:`_to_domain` is the sole ORM<->domain mapping site (ARCH-009) so no
``PhotoModel`` ever leaks past this adapter. Missing/cross-plant rows raise
:class:`PhotoNotFoundError` (the domain error), keeping HTTP concerns out of persistence
(ADR-C). Lists are ordered ``created_at`` descending (newest-first, P5).

The single-cover invariant lives here, in-transaction: ``add(make_cover=True)`` and
``set_cover`` clear every other cover for the plant before setting the new one;
``delete`` promotes the newest survivor when the removed row was the cover. The
``id``-tiebreaker on the ordering keeps the result deterministic when two rows share a
``created_at`` (sub-second test inserts on SQLite).
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import PhotoModel, PlantModel
from viridarium.domain.photo import (
    NewPhoto,
    Photo,
    PhotoNotFoundError,
)


def _to_domain(model: PhotoModel) -> Photo:
    """Map a persisted ``PhotoModel`` to the domain :class:`Photo`."""
    return Photo(
        id=model.id,
        plant_id=model.plant_id,
        stored_filename=model.stored_filename,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        is_cover=model.is_cover,
        created_at=model.created_at,
    )


def _clear_covers(session: Session, plant_id: int) -> None:
    """Unset ``is_cover`` for every photo of a plant (single-cover invariant)."""
    session.execute(
        update(PhotoModel)
        .where(PhotoModel.plant_id == plant_id, PhotoModel.is_cover.is_(True))
        .values(is_cover=False)
    )


class SqlAlchemyPhotoRepository:
    """Concrete :class:`~viridarium.domain.photo.PhotoRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, new_photo: NewPhoto, *, make_cover: bool) -> Photo:
        with self._session_factory() as session:
            if make_cover:
                _clear_covers(session, new_photo.plant_id)
            model = PhotoModel(
                plant_id=new_photo.plant_id,
                stored_filename=new_photo.stored_filename,
                content_type=new_photo.content_type,
                size_bytes=new_photo.size_bytes,
                is_cover=make_cover,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def list_for_plant(self, plant_id: int) -> list[Photo]:
        with self._session_factory() as session:
            models = session.scalars(
                select(PhotoModel)
                .where(PhotoModel.plant_id == plant_id)
                .order_by(PhotoModel.created_at.desc(), PhotoModel.id.desc())
            ).all()
            return [_to_domain(m) for m in models]

    def get(self, plant_id: int, photo_id: int) -> Photo:
        with self._session_factory() as session:
            model = self._require(session, plant_id, photo_id)
            return _to_domain(model)

    def set_cover(self, plant_id: int, photo_id: int) -> Photo:
        with self._session_factory() as session:
            model = self._require(session, plant_id, photo_id)
            _clear_covers(session, plant_id)
            model.is_cover = True
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def delete(self, plant_id: int, photo_id: int) -> Photo:
        with self._session_factory() as session:
            model = self._require(session, plant_id, photo_id)
            was_cover = model.is_cover
            removed = _to_domain(model)
            session.delete(model)
            session.flush()
            if was_cover:
                survivor = session.scalars(
                    select(PhotoModel)
                    .where(PhotoModel.plant_id == plant_id)
                    .order_by(PhotoModel.created_at.desc(), PhotoModel.id.desc())
                ).first()
                if survivor is not None:
                    survivor.is_cover = True
            session.commit()
            return removed

    def plant_exists(self, plant_id: int) -> bool:
        with self._session_factory() as session:
            return session.get(PlantModel, plant_id) is not None

    def list_filenames_for_plant(self, plant_id: int) -> list[str]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(PhotoModel.stored_filename).where(
                    PhotoModel.plant_id == plant_id
                )
            ).all()
            return list(rows)

    @staticmethod
    def _require(session: Session, plant_id: int, photo_id: int) -> PhotoModel:
        """Load a photo scoped to its plant or raise (covers cross-plant -> 404)."""
        model = session.get(PhotoModel, photo_id)
        if model is None or model.plant_id != plant_id:
            raise PhotoNotFoundError(plant_id, photo_id)
        return model
