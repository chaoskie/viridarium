"""App-settings domain types (framework-free, US-3.5).

The persisted application settings are a **singleton**: one global seasonal-aware toggle
plus the configurable winter window (reusing the US-3.3 :class:`WinterWindow` value
object verbatim). :class:`SeasonalSettings` is the immutable domain value; the
:class:`AppSettingsRepository` ``Protocol`` is the outbound port the persistence adapter
satisfies. The lazy default (Nov 1 - Mar 1, ``seasonal_aware=True``) lives in the
application service, not here - ``get()`` returns ``None`` when no row exists so the
repository never invents data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from viridarium.domain.due import WinterWindow


@dataclass(frozen=True, slots=True)
class SeasonalSettings:
    """The persisted app settings: the global toggle + the winter window.

    ``seasonal_aware`` is the global toggle (proposal §domain): when ``False`` the due
    engine ignores both the window and ``paused``, using the plain interval all year.
    ``window`` is the year-agnostic, wrap-aware :class:`WinterWindow` (US-3.3).
    """

    seasonal_aware: bool
    window: WinterWindow


class AppSettingsRepository(Protocol):
    """Outbound port for persisting the singleton app settings (US-3.5)."""

    def get(self) -> SeasonalSettings | None:
        """Return the persisted settings, or ``None`` when no row exists yet."""
        ...

    def put(self, settings: SeasonalSettings) -> None:
        """Upsert the singleton settings row (id=1; never a second row)."""
        ...
