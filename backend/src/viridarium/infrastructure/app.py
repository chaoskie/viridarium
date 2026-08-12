"""FastAPI application factory.

Wires the composition root (:mod:`viridarium.infrastructure.container`) onto the app,
mounts the versioned API under ``/api/v1`` with OpenAPI docs at ``/api/v1/docs``, and
installs the secure-by-default middleware (SEC-003, SEC-011).
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from viridarium.adapters.inbound.web.care_events import (
    router as care_events_router,
)
from viridarium.adapters.inbound.web.care_schedules import (
    router as care_schedules_router,
)
from viridarium.adapters.inbound.web.health import router as health_router
from viridarium.adapters.inbound.web.locations import router as locations_router
from viridarium.adapters.inbound.web.photos import router as photos_router
from viridarium.adapters.inbound.web.plants import router as plants_router
from viridarium.adapters.inbound.web.settings import router as settings_router
from viridarium.adapters.inbound.web.timeline import router as timeline_router
from viridarium.domain.care_event import (
    CareEventNotFoundError,
    HealthRequiresObserveError,
    PhotoNotForPlantError,
    PlantNotFoundForEventError,
)
from viridarium.domain.care_schedule import (
    CareScheduleNotFoundError,
    PlantNotFoundForScheduleError,
)
from viridarium.domain.location import LocationNotFoundError
from viridarium.domain.photo import (
    PhotoNotFoundError,
    PhotoTooLargeError,
    UnsupportedImageTypeError,
)
from viridarium.domain.plant import (
    LocationNotFoundForPlantError,
    PlantNotFoundError,
)
from viridarium.infrastructure.container import Container, build_container
from viridarium.infrastructure.security import security_headers_middleware
from viridarium.infrastructure.settings import Settings, get_settings
from viridarium.infrastructure.static import mount_spa

API_V1_PREFIX = "/api/v1"


def _build_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health_router)
    api.include_router(locations_router)
    api.include_router(plants_router)
    api.include_router(photos_router)
    api.include_router(care_schedules_router)
    api.include_router(care_events_router)
    api.include_router(settings_router)
    api.include_router(timeline_router)
    return api


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Accepts an optional ``settings`` override so tests can boot the app against a
    temporary database without touching process environment.
    """
    resolved = settings or get_settings()
    container: Container = build_container(resolved)

    app = FastAPI(
        title="Viridarium API",
        version=resolved.version,
        docs_url=f"{API_V1_PREFIX}/docs",
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
        redoc_url=None,
    )

    # Expose wired collaborators to the inbound adapter via app.state.
    app.state.container = container
    app.state.health_probe = container.health_probe
    app.state.readiness_probe = container.readiness_probe
    app.state.location_service = container.location_service
    app.state.plant_service = container.plant_service
    app.state.photo_service = container.photo_service
    app.state.care_schedule_service = container.care_schedule_service
    app.state.care_event_service = container.care_event_service
    app.state.app_settings_service = container.app_settings_service
    app.state.due_query_service = container.due_query_service
    app.state.timeline_query_service = container.timeline_query_service

    # Error-to-HTTP via a registered handler (ADR-C): domain raises typed errors;
    # the app factory maps each to a status. The body carries no PII (SEC-001),
    # only the id already present in the domain error message.
    @app.exception_handler(LocationNotFoundError)
    async def _location_not_found(
        _request: Request, exc: LocationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PlantNotFoundError)
    async def _plant_not_found(
        _request: Request, exc: PlantNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # A non-existent referenced location_id is a body-reference failure -> 422 (not
    # 404, which is reserved for the addressed plant). Id-only body, no PII (SEC-001).
    @app.exception_handler(LocationNotFoundForPlantError)
    async def _location_not_found_for_plant(
        _request: Request, exc: LocationNotFoundForPlantError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # Photo upload/lookup errors (US-2.3). Each body is id/int-only - never the client
    # filename or body content (SEC-001/SEC-007). The sniff/declared-cross-check failure
    # is a 415, the size-cap breach a 413, a missing/cross-plant photo a 404.
    @app.exception_handler(PhotoNotFoundError)
    async def _photo_not_found(
        _request: Request, exc: PhotoNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(UnsupportedImageTypeError)
    async def _unsupported_image_type(
        _request: Request, exc: UnsupportedImageTypeError
    ) -> JSONResponse:
        return JSONResponse(status_code=415, content={"detail": str(exc)})

    @app.exception_handler(PhotoTooLargeError)
    async def _photo_too_large(
        _request: Request, exc: PhotoTooLargeError
    ) -> JSONResponse:
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    # Care-schedule errors (US-3.1). Both 404; each body is id + care_type only - never
    # the plant name or any free text (SEC-001/SEC-007). The addressed plant missing
    # (upsert/list guard) and a missing schedule (get/delete) both surface as 404.
    @app.exception_handler(PlantNotFoundForScheduleError)
    async def _plant_not_found_for_schedule(
        _request: Request, exc: PlantNotFoundForScheduleError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CareScheduleNotFoundError)
    async def _care_schedule_not_found(
        _request: Request, exc: CareScheduleNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # Care-event errors (US-3.2). The addressed plant missing (guard first,
    # VIRIDARIUM-48) and a missing/cross-plant event are 404; the health-on-non-observe
    # rule and an unknown/cross-plant photo_id are body-reference failures -> 422. Each
    # body carries ids + closed-enum values only - never the plant name or the note
    # free text (SEC-001/SEC-007).
    @app.exception_handler(PlantNotFoundForEventError)
    async def _plant_not_found_for_event(
        _request: Request, exc: PlantNotFoundForEventError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CareEventNotFoundError)
    async def _care_event_not_found(
        _request: Request, exc: CareEventNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(HealthRequiresObserveError)
    async def _health_requires_observe(
        _request: Request, exc: HealthRequiresObserveError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(PhotoNotForPlantError)
    async def _photo_not_for_plant(
        _request: Request, exc: PhotoNotForPlantError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # Secure-by-default posture (SEC-003, SEC-011).
    app.middleware("http")(security_headers_middleware)
    if resolved.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.cors_allow_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(_build_api_router(), prefix=API_V1_PREFIX)

    # Serve the built SPA from the same origin in the single-container image. Mounted
    # last so the catch-all static route never shadows /api/v1/*. No-op when unset
    # (dev/test), so the API-only app is unchanged.
    mount_spa(app, resolved.static_dir)
    return app
