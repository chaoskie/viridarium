"""App-settings use cases (US-3.5).

A thin application service over the
:class:`~viridarium.domain.app_settings.AppSettingsRepository` port. It owns the **lazy
default**: when no row is persisted yet, :meth:`get` returns the spec default
(``seasonal_aware=True``, Nov 1 - Mar 1) so a fresh install works with no seeding
(proposal §domain). :meth:`update` persists the settings faithfully (shape/range
validation lives at the web edge, ADR-C).
"""

from __future__ import annotations

from viridarium.domain.app_settings import AppSettingsRepository, SeasonalSettings
from viridarium.domain.due import WinterWindow

# The spec default winter window: Nov 1 - Mar 1, northern hemisphere (proposal §domain).
_DEFAULT_SETTINGS = SeasonalSettings(
    seasonal_aware=True,
    window=WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1),
)


class AppSettingsService:
    """Use cases for the singleton app settings, backed by a repository port."""

    def __init__(self, repository: AppSettingsRepository) -> None:
        self._repository = repository

    def get(self) -> SeasonalSettings:
        """Return the persisted settings, or the spec default when none exist (AC1)."""
        return self._repository.get() or _DEFAULT_SETTINGS

    def update(self, settings: SeasonalSettings) -> SeasonalSettings:
        """Persist the settings (upsert the singleton) and return the stored value."""
        self._repository.put(settings)
        return settings


class ServiceSeasonalSettingsProvider:
    """A :class:`~viridarium.application.due.SeasonalSettingsProvider` backed by the
    service (US-3.5).

    Reads the current settings (the persisted row or the lazy default) on each
    ``current()`` call, so the due engine always sees the latest persisted toggle +
    window. Wired in the composition root, replacing the US-3.3 hardcoded provider.
    """

    def __init__(self, service: AppSettingsService) -> None:
        self._service = service

    def current(self) -> SeasonalSettings:
        """Return the seasonal settings currently in effect (row or lazy default)."""
        return self._service.get()
