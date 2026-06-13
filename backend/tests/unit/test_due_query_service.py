"""Unit tests for the DueQueryService assembly (TEST-001 (b): fake ports).

The orchestration logic (group-by-plant, the ``events.get((pid, care_type))`` lookup,
empty-list for a schedule-less plant, today + window injection) is unit-testable
against a fake schedule repo + fake event repo + fake window provider (TEST-003: faking
ports is allowed). The same behaviour is re-proven end-to-end in the integration suite;
this slice de-risks the assembly branch points cheaply.

Numbered cases trace to the foundation: the assembly variants of B-I14..B-I18, plus
the US-3.5 read-once proof (B-I15) and the flag-threading proof (B-I16 unit variant).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from viridarium.application.due import DueQueryService, SeasonalSettingsProvider
from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.care_event import CareEventType
from viridarium.domain.care_schedule import CareSchedule, CareType, Dormancy
from viridarium.domain.due import WinterWindow

pytestmark = pytest.mark.unit

_TODAY = date(2026, 6, 1)  # inside the fake window below
_WINDOW = WinterWindow(start_month=4, start_day=1, end_month=9, end_day=1)


def _schedule(plant_id: int, care_type: CareType, interval: int) -> CareSchedule:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return CareSchedule(
        id=plant_id * 10 + (0 if care_type is CareType.WATER else 1),
        plant_id=plant_id,
        care_type=care_type,
        interval_days=interval,
        winter_interval_days=None,
        dormancy=Dormancy.WINTER_INTERVAL,
        enabled=True,
        created_at=now,
        updated_at=now,
    )


class _FakeScheduleRepo:
    def __init__(self, rows: dict[int, list[CareSchedule]]) -> None:
        self._rows = rows

    def enabled_for_plants(self, plant_ids: list[int]) -> dict[int, list[CareSchedule]]:
        return {pid: self._rows[pid] for pid in plant_ids if pid in self._rows}


class _FakeEventRepo:
    def __init__(self, rows: dict[tuple[int, CareType], date]) -> None:
        self._rows = rows

    def latest_event_dates(
        self, plant_ids: list[int], types: set[CareType]
    ) -> dict[tuple[int, CareType], date]:
        return {
            key: when
            for key, when in self._rows.items()
            if key[0] in plant_ids and key[1] in types
        }


class _FakeSettingsProvider:
    """A counting fake :class:`SeasonalSettingsProvider` (read-once proof, B-I15)."""

    def __init__(self, window: WinterWindow, *, seasonal_aware: bool = True) -> None:
        self._settings = SeasonalSettings(seasonal_aware=seasonal_aware, window=window)
        self.calls = 0

    def current(self) -> SeasonalSettings:
        self.calls += 1
        return self._settings


def _service(
    schedules: dict[int, list[CareSchedule]],
    events: dict[tuple[int, CareType], date],
    *,
    window: WinterWindow = _WINDOW,
    today: date = _TODAY,
    seasonal_aware: bool = True,
) -> DueQueryService:
    provider: SeasonalSettingsProvider = _FakeSettingsProvider(
        window, seasonal_aware=seasonal_aware
    )
    return DueQueryService(
        schedule_repository=_FakeScheduleRepo(schedules),
        event_repository=_FakeEventRepo(events),
        settings_provider=provider,
        today_provider=lambda: today,
    )


def test_assembles_per_plant_due_lists() -> None:
    """B-I14 (assembly): each schedule gets its own last-event date."""
    svc = _service(
        schedules={
            1: [
                _schedule(1, CareType.WATER, 7),
                _schedule(1, CareType.FEED, 14),
            ]
        },
        events={
            (1, CareType.WATER): _TODAY,
            (1, CareType.FEED): _TODAY,
        },
    )
    result = svc.for_plants([1])
    by_type = {d.care_type: d for d in result[1]}
    assert by_type[CareType.WATER].next_due == _TODAY + timedelta(days=7)
    assert by_type[CareType.FEED].next_due == _TODAY + timedelta(days=14)


def test_new_plant_no_events_due_today() -> None:
    """B-I15 (assembly): a plant with a schedule but no events -> due today."""
    svc = _service(schedules={1: [_schedule(1, CareType.WATER, 7)]}, events={})
    result = svc.for_plants([1])
    assert result[1][0].next_due == _TODAY
    assert result[1][0].overdue_days == 0


def test_schedule_less_plant_empty_list() -> None:
    """B-I16 (assembly): a plant with no schedules -> present key, empty list."""
    svc = _service(schedules={}, events={})
    result = svc.for_plants([1])
    assert result == {1: []}


def test_empty_input_empty_mapping() -> None:
    """B-I18 (assembly): empty input -> empty mapping (no crash)."""
    svc = _service(schedules={1: [_schedule(1, CareType.WATER, 7)]}, events={})
    assert svc.for_plants([]) == {}


def test_event_types_requested_are_care_types() -> None:
    """The service requests exactly the two schedule care types from the event repo."""
    captured: dict[str, set[CareType]] = {}

    class _CapturingEventRepo(_FakeEventRepo):
        def latest_event_dates(
            self, plant_ids: list[int], types: set[CareType]
        ) -> dict[tuple[int, CareType], date]:
            captured["types"] = types
            return super().latest_event_dates(plant_ids, types)

    provider: SeasonalSettingsProvider = _FakeSettingsProvider(_WINDOW)
    svc = DueQueryService(
        schedule_repository=_FakeScheduleRepo({1: [_schedule(1, CareType.WATER, 7)]}),
        event_repository=_CapturingEventRepo({}),
        settings_provider=provider,
        today_provider=lambda: _TODAY,
    )
    svc.for_plants([1])
    assert captured["types"] == {CareType.WATER, CareType.FEED}
    # CareType values must align with the event-type filter the repo applies.
    assert {t.value for t in captured["types"]} <= {
        CareEventType.WATER.value,
        CareEventType.FEED.value,
    }


def test_settings_provider_read_exactly_once_per_query() -> None:
    """B-I15 (unit): the provider is read ONCE per ``for_plants``, not per plant.

    Seeds N then 2N plants each with a schedule; the call count is 1 for both - proving
    the settings read does NOT scale with the plant count (the US-3.3 N+1 bound survives
    the settings wiring).
    """
    provider = _FakeSettingsProvider(_WINDOW)
    schedules = {pid: [_schedule(pid, CareType.WATER, 7)] for pid in range(1, 11)}
    svc = DueQueryService(
        schedule_repository=_FakeScheduleRepo(schedules),
        event_repository=_FakeEventRepo({}),
        settings_provider=provider,
        today_provider=lambda: _TODAY,
    )

    svc.for_plants(list(range(1, 11)))  # N = 10
    assert provider.calls == 1

    svc.for_plants(list(range(1, 21)))  # 2N = 20
    assert provider.calls == 2  # one more whole-query read, not per-plant


def test_seasonal_off_flag_threaded_into_compute_due() -> None:
    """B-I16 (unit): provider ``seasonal_aware=False`` flips paused-in-window to due.

    A paused schedule with a recent event, the provider returning
    ``seasonal_aware=False`` and a window that contains today -> the assembled due is
    non-null (plain interval), proving the service threaded ``False`` into
    ``compute_due``.
    """
    paused = CareSchedule(
        id=1,
        plant_id=1,
        care_type=CareType.WATER,
        interval_days=7,
        winter_interval_days=14,
        dormancy=Dormancy.PAUSED,
        enabled=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    svc = _service(
        schedules={1: [paused]},
        events={(1, CareType.WATER): _TODAY},
        seasonal_aware=False,
    )
    result = svc.for_plants([1])
    assert result[1][0].next_due == _TODAY + timedelta(days=7)
    assert result[1][0].overdue_days == 0
