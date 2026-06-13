"""Unit tests for the DueQueryService assembly (TEST-001 (b): fake ports).

The orchestration logic (group-by-plant, the ``events.get((pid, care_type))`` lookup,
empty-list for a schedule-less plant, today + window injection) is unit-testable
against a fake schedule repo + fake event repo + fake window provider (TEST-003: faking
ports is allowed). The same behaviour is re-proven end-to-end in the integration suite;
this slice de-risks the assembly branch points cheaply.

Numbered cases trace to the foundation: the assembly variants of B-I14..B-I18.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from viridarium.application.due import DueQueryService, WinterWindowProvider
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


class _FakeWindowProvider:
    def __init__(self, window: WinterWindow) -> None:
        self._window = window

    def current_window(self) -> WinterWindow:
        return self._window


def _service(
    schedules: dict[int, list[CareSchedule]],
    events: dict[tuple[int, CareType], date],
    *,
    window: WinterWindow = _WINDOW,
    today: date = _TODAY,
) -> DueQueryService:
    provider: WinterWindowProvider = _FakeWindowProvider(window)
    return DueQueryService(
        schedule_repository=_FakeScheduleRepo(schedules),
        event_repository=_FakeEventRepo(events),
        window_provider=provider,
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

    provider: WinterWindowProvider = _FakeWindowProvider(_WINDOW)
    svc = DueQueryService(
        schedule_repository=_FakeScheduleRepo({1: [_schedule(1, CareType.WATER, 7)]}),
        event_repository=_CapturingEventRepo({}),
        window_provider=provider,
        today_provider=lambda: _TODAY,
    )
    svc.for_plants([1])
    assert captured["types"] == {CareType.WATER, CareType.FEED}
    # CareType values must align with the event-type filter the repo applies.
    assert {t.value for t in captured["types"]} <= {
        CareEventType.WATER.value,
        CareEventType.FEED.value,
    }
