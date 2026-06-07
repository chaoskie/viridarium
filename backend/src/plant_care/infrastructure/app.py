"""FastAPI application factory.

Wires the composition root (:mod:`plant_care.infrastructure.container`) onto the app,
mounts the versioned API under ``/api/v1`` with OpenAPI docs at ``/api/v1/docs``, and
installs the secure-by-default middleware (SEC-003, SEC-011).
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plant_care.adapters.inbound.web.health import router as health_router
from plant_care.infrastructure.container import Container, build_container
from plant_care.infrastructure.security import security_headers_middleware
from plant_care.infrastructure.settings import Settings, get_settings
from plant_care.infrastructure.static import mount_spa

API_V1_PREFIX = "/api/v1"


def _build_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health_router)
    return api


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Accepts an optional ``settings`` override so tests can boot the app against a
    temporary database without touching process environment.
    """
    resolved = settings or get_settings()
    container: Container = build_container(resolved)

    app = FastAPI(
        title="plant-care API",
        version=resolved.version,
        docs_url=f"{API_V1_PREFIX}/docs",
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
        redoc_url=None,
    )

    # Expose wired collaborators to the inbound adapter via app.state.
    app.state.container = container
    app.state.health_probe = container.health_probe

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
