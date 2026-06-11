"""Dependency-injection composition root.

The single place where concrete implementations are constructed and wired to the
ports they satisfy. Keeping construction here means routers and use cases never know
how their collaborators are built (ARCH-002).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

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
from viridarium.adapters.outbound.db.photo_repository import (
    SqlAlchemyPhotoRepository,
)
from viridarium.adapters.outbound.db.photo_storage import FilesystemPhotoStorage
from viridarium.adapters.outbound.db.plant_repository import (
    SqlAlchemyPlantRepository,
)
from viridarium.application.care_events import CareEventService
from viridarium.application.care_schedules import CareScheduleService
from viridarium.application.health import GetHealthStatus
from viridarium.application.locations import LocationService
from viridarium.application.photos import PhotoService
from viridarium.application.plants import PlantService
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
    plant_service: PlantService
    photo_service: PhotoService
    care_schedule_service: CareScheduleService
    care_event_service: CareEventService


def build_container(settings: Settings) -> Container:
    """Construct and wire all application dependencies from settings."""
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    health_probe = GetHealthStatus(version=settings.version)
    location_service = LocationService(SqlAlchemyLocationRepository(session_factory))

    photo_repository = SqlAlchemyPhotoRepository(session_factory)
    photo_storage = FilesystemPhotoStorage(settings.photos_dir)
    photo_service = PhotoService(
        photo_repository, photo_storage, max_bytes=settings.photos_max_bytes
    )
    # Inject the photo repo + storage into the plant service for P6 file cleanup:
    # deleting a plant cascades its photo rows (DB) AND unlinks the files (app-level).
    plant_service = PlantService(
        SqlAlchemyPlantRepository(session_factory),
        photo_repository=photo_repository,
        photo_storage=photo_storage,
    )
    care_schedule_service = CareScheduleService(
        SqlAlchemyCareScheduleRepository(session_factory)
    )
    care_event_service = CareEventService(
        SqlAlchemyCareEventRepository(session_factory)
    )
    return Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        health_probe=health_probe,
        location_service=location_service,
        plant_service=plant_service,
        photo_service=photo_service,
        care_schedule_service=care_schedule_service,
        care_event_service=care_event_service,
    )
