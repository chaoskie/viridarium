"""SQLAlchemy app-settings repository (outbound adapter, US-3.5).

Session-per-call: each method opens its own session and commits its own writes. The
module-level :func:`_to_domain` is the sole ORM<->domain mapping site (ARCH-009) so no
``AppSettingsModel`` leaks past this adapter.

``put`` is a **portable** singleton upsert (ARCH-011): it selects the ``id = 1`` row and
updates it in place when present, else inserts it with ``id = 1`` - never an
engine-specific ``ON CONFLICT`` / ``INSERT OR REPLACE``, and never a second row. ``get``
returns ``None`` when no row exists yet (the lazy default lives in the service, not
here).
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.models import AppSettingsModel
from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.due import WinterWindow

# The fixed singleton primary key: every put targets this id, never a second row.
_SINGLETON_ID = 1


def _to_domain(model: AppSettingsModel) -> SeasonalSettings:
    """Map the persisted ``AppSettingsModel`` to a domain :class:`SeasonalSettings`."""
    return SeasonalSettings(
        seasonal_aware=model.seasonal_aware,
        window=WinterWindow(
            start_month=model.start_month,
            start_day=model.start_day,
            end_month=model.end_month,
            end_day=model.end_day,
        ),
    )


class SqlAlchemyAppSettingsRepository:
    """Concrete :class:`~viridarium.domain.app_settings.AppSettingsRepository`."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self) -> SeasonalSettings | None:
        with self._session_factory() as session:
            model = session.get(AppSettingsModel, _SINGLETON_ID)
            return None if model is None else _to_domain(model)

    def put(self, settings: SeasonalSettings) -> None:
        with self._session_factory() as session:
            model = session.get(AppSettingsModel, _SINGLETON_ID)
            if model is None:
                model = AppSettingsModel(id=_SINGLETON_ID)
                session.add(model)
            model.seasonal_aware = settings.seasonal_aware
            model.start_month = settings.window.start_month
            model.start_day = settings.window.start_day
            model.end_month = settings.window.end_month
            model.end_day = settings.window.end_day
            session.commit()
