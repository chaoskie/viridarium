"""Dependency-injection composition root.

The single place where concrete implementations are constructed and wired to the
ports they satisfy. Keeping construction here means routers and use cases never know
how their collaborators are built (ARCH-002).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.engine import (
    create_db_engine,
    create_session_factory,
)
from viridarium.adapters.outbound.db.location_repository import (
    SqlAlchemyLocationRepository,
)
from viridarium.application.health import GetHealthStatus
from viridarium.application.locations import LocationService
from viridarium.domain.health import HealthProbe
from viridarium.infrastructure.settings import Settings


@dataclass(frozen=True, slots=True)
class Container:
    """Assembled application dependencies."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    health_probe: HealthProbe
    location_service: LocationService


def build_container(settings: Settings) -> Container:
    """Construct and wire all application dependencies from settings."""
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    health_probe = GetHealthStatus(version=settings.version)
    location_service = LocationService(SqlAlchemyLocationRepository(session_factory))
    return Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        health_probe=health_probe,
        location_service=location_service,
    )
