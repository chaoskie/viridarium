"""App-settings router (ARCH-002: HTTP only, no business logic) (US-3.5).

Exposes the singleton settings under ``/settings`` and delegates to the
:class:`~viridarium.application.settings.AppSettingsService`. GET returns the persisted
settings or the lazy default; PUT validates the body (month/day ranges, month-aware day
rule -> 422 on impossible combos) and persists it, echoing the stored value. The
``id``/``updated_at`` never cross the boundary (ARCH-007); 422 bodies carry
field-locations only, no PII (settings hold no free text).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from viridarium.adapters.inbound.web.dependencies import get_app_settings_service
from viridarium.adapters.inbound.web.schemas import SettingsResponse, SettingsUpdate
from viridarium.application.settings import AppSettingsService
from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.due import WinterWindow

router = APIRouter(prefix="/settings", tags=["settings"])

ServiceDep = Annotated[AppSettingsService, Depends(get_app_settings_service)]


@router.get("", response_model=SettingsResponse, summary="Get app settings")
def get_settings(service: ServiceDep) -> SettingsResponse:
    """Return the persisted settings, or the spec default on a fresh install (AC1)."""
    return SettingsResponse.from_domain(service.get())


@router.put("", response_model=SettingsResponse, summary="Update app settings")
def update_settings(body: SettingsUpdate, service: ServiceDep) -> SettingsResponse:
    """Persist the settings and echo the stored value (422 on invalid month/day)."""
    settings = SeasonalSettings(
        seasonal_aware=body.seasonal_aware,
        window=WinterWindow(
            start_month=body.winter_window.start_month,
            start_day=body.winter_window.start_day,
            end_month=body.winter_window.end_month,
            end_day=body.winter_window.end_day,
        ),
    )
    return SettingsResponse.from_domain(service.update(settings))
