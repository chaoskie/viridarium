"""Due-computation query service (US-3.3, ARCH-006: a dedicated read module, no writes).

Orchestrates the pure :func:`viridarium.domain.due.compute_due` over a page of plant
ids. To keep the list path flat (NFR: p95 < 200 ms for 500 plants), it batch-loads in
**two grouped queries** - the enabled schedules and the latest matching-event dates for
all the ids at once - then computes in memory (no per-plant query, no N+1).

The window AND the global seasonal-aware flag are read through the
:class:`SeasonalSettingsProvider` port (US-3.5), never a constant, so the persisted
settings drive the engine. ``today`` is injected through a callable for the same
testability reason as the domain function (proposal §"today"); the default resolves the
server-local date.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.care_event import CareEventRepository
from viridarium.domain.care_schedule import CareScheduleRepository, CareType
from viridarium.domain.due import ScheduleDue, compute_due


class SeasonalSettingsProvider(Protocol):
    """Outbound port supplying the current seasonal settings (US-3.5).

    Yields both the winter window AND the global ``seasonal_aware`` flag in one read, so
    the due engine reads settings once per query (the US-3.3 N+1 bound survives).
    """

    def current(self) -> SeasonalSettings:
        """Return the seasonal settings currently in effect."""
        ...


class DueQueryService:
    """Assemble per-plant due lists from batch reads (US-3.3, no writes).

    Two grouped queries regardless of plant count: the enabled schedules and the latest
    matching-event dates. The caller passes only **non-archived** plant ids (the router
    filters archived plants out, which therefore get an empty due list).
    """

    def __init__(
        self,
        schedule_repository: CareScheduleRepository,
        event_repository: CareEventRepository,
        settings_provider: SeasonalSettingsProvider,
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.event_repository = event_repository
        self.settings_provider = settings_provider
        self.today_provider = today_provider

    def for_plants(self, plant_ids: list[int]) -> dict[int, list[ScheduleDue]]:
        """Return ``{plant_id: [ScheduleDue]}`` for the given (non-archived) ids.

        Reads the seasonal settings ONCE per query (the window + the global flag), then
        passes both into every :func:`compute_due` - no per-plant settings read, so the
        US-3.3 N+1 bound survives. A plant with no enabled schedule gets a present key
        with an empty list. Empty input returns ``{}``.
        """
        if not plant_ids:
            return {}
        today = self.today_provider()
        settings = self.settings_provider.current()
        schedules = self.schedule_repository.enabled_for_plants(plant_ids)
        events = self.event_repository.latest_event_dates(
            plant_ids, {CareType.WATER, CareType.FEED}
        )
        result: dict[int, list[ScheduleDue]] = {}
        for plant_id in plant_ids:
            result[plant_id] = [
                compute_due(
                    schedule,
                    events.get((plant_id, schedule.care_type)),
                    today,
                    settings.window,
                    settings.seasonal_aware,
                )
                for schedule in schedules.get(plant_id, [])
            ]
        return result
