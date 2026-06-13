"""Due-computation query service (US-3.3, ARCH-006: a dedicated read module, no writes).

Orchestrates the pure :func:`viridarium.domain.due.compute_due` over a page of plant
ids. To keep the list path flat (NFR: p95 < 200 ms for 500 plants), it batch-loads in
**two grouped queries** - the enabled schedules and the latest matching-event dates for
all the ids at once - then computes in memory (no per-plant query, no N+1).

The winter window is read through the :class:`WinterWindowProvider` port, never a
constant, so US-3.5 can drop in a persisted-settings provider additively. ``today`` is
injected through a callable for the same testability reason as the domain function
(proposal §"today"); the default resolves the server-local date.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from viridarium.domain.care_event import CareEventRepository
from viridarium.domain.care_schedule import CareScheduleRepository, CareType
from viridarium.domain.due import ScheduleDue, WinterWindow, compute_due


class WinterWindowProvider(Protocol):
    """Outbound port supplying the current seasonal dormancy window (US-3.3).

    The default implementation returns the spec default (Nov 1 - Mar 1); US-3.5 replaces
    it with a persisted-settings provider without touching the due engine.
    """

    def current_window(self) -> WinterWindow:
        """Return the window currently in effect."""
        ...


class DefaultWinterWindowProvider:
    """The spec-default window provider: Nov 1 - Mar 1 (northern hemisphere).

    A constant until US-3.5 persists a configurable window; wired in the composition
    root so the rest of the engine reads the window through the port.
    """

    def current_window(self) -> WinterWindow:
        """Return the Nov 1 - Mar 1 default window."""
        return WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1)


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
        window_provider: WinterWindowProvider,
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.event_repository = event_repository
        self.window_provider = window_provider
        self.today_provider = today_provider

    def for_plants(self, plant_ids: list[int]) -> dict[int, list[ScheduleDue]]:
        """Return ``{plant_id: [ScheduleDue]}`` for the given (non-archived) ids.

        A plant with no enabled schedule gets a present key with an empty list. Empty
        input returns ``{}``.
        """
        if not plant_ids:
            return {}
        today = self.today_provider()
        window = self.window_provider.current_window()
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
                    window,
                )
                for schedule in schedules.get(plant_id, [])
            ]
        return result
