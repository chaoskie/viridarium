"""Unit tests for the pure due-computation core (TEST-002: no app, no DB, no I/O).

The behaviour core of US-3.3: ``compute_due`` (the verbatim rule
``next_due = date(last matching CareEvent) + effective_interval``) and
``WinterWindow.contains`` (the year-agnostic, wrap-aware seasonal classifier). Both are
framework-free and exhaustively branch-tested here (TEST-001 (a): genuinely complex pure
logic with a wide branch table). ``today`` and ``window`` are injected so every case is
deterministic with no clock dependence (TEST-006).

Numbered cases trace to the test foundation: B-U1..B-U14 (US-3.3) plus B-U15..B-U24
(US-3.5: the additive ``seasonal_aware`` parameter). The US-3.3 cases below now pass
``seasonal_aware=True`` - their behaviour is unchanged, which is exactly the on-path
regression guard for the additive parameter (foundation §3b).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from viridarium.domain.care_schedule import CareSchedule, CareType, Dormancy
from viridarium.domain.due import ScheduleDue, WinterWindow, compute_due

pytestmark = pytest.mark.unit

# A fixed reference date well clear of any window edge; the year is irrelevant to the
# math (intervals are added to it) but pin it for readability.
_D = date(2026, 6, 1)

# A non-wrapping test window (Apr 1 - Sep 1): _D (Jun 1) is inside it, so "in-window"
# cases use _D as today and "out-of-window" cases use a winter date.
_WINDOW = WinterWindow(start_month=4, start_day=1, end_month=9, end_day=1)
_IN_WINDOW_DAY = date(2026, 6, 1)  # Jun 1, inside Apr 1 - Sep 1
_OUT_OF_WINDOW_DAY = date(2026, 1, 15)  # Jan 15, outside Apr 1 - Sep 1


def _schedule(
    *,
    care_type: CareType = CareType.WATER,
    interval: int = 7,
    winter: int | None = None,
    dormancy: Dormancy = Dormancy.WINTER_INTERVAL,
    enabled: bool = True,
) -> CareSchedule:
    """Hand-built schedule value object; timestamps are irrelevant to due math."""
    from datetime import UTC, datetime

    now = datetime(2026, 1, 1, tzinfo=UTC)
    return CareSchedule(
        id=1,
        plant_id=1,
        care_type=care_type,
        interval_days=interval,
        winter_interval_days=winter,
        dormancy=dormancy,
        enabled=enabled,
        created_at=now,
        updated_at=now,
    )


# ===================================================================== 3a. core rule
def test_no_matching_event_due_today() -> None:
    """B-U1: no matching event -> next_due == today, overdue 0 (AC2, new plants)."""
    result = compute_due(
        _schedule(),
        last_event_on=None,
        today=_OUT_OF_WINDOW_DAY,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result == ScheduleDue(CareType.WATER, _OUT_OF_WINDOW_DAY, 0)


def test_event_present_last_plus_interval() -> None:
    """B-U2: event present -> last + interval; not yet due -> overdue 0."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_D,
        today=_D,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _D + timedelta(days=7)
    assert result.overdue_days == 0


def test_overdue_accrual_positive() -> None:
    """B-U3: interval 7, last D, today D+9 -> next_due D+7, overdue 2 (AC1)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_D,
        today=_D + timedelta(days=9),
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _D + timedelta(days=7)
    assert result.overdue_days == 2


def test_overdue_clamped_to_zero_when_future() -> None:
    """B-U4: today before next_due -> overdue clamped to 0 (max(0, negative))."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_D,
        today=_D + timedelta(days=3),
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _D + timedelta(days=7)
    assert result.overdue_days == 0


def test_overdue_zero_exactly_on_due_day() -> None:
    """B-U5: today == next_due -> overdue 0 (due today is not overdue)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_D,
        today=_D + timedelta(days=7),
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _D + timedelta(days=7)
    assert result.overdue_days == 0


def test_overdue_one_day_after_due() -> None:
    """B-U6: today == next_due + 1 -> overdue 1 (boundary above the due day)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_D,
        today=_D + timedelta(days=8),
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.overdue_days == 1


# ============================================ 3b. effective-interval matrix M1 (AC3)
@pytest.mark.parametrize(
    ("in_window", "dormancy", "winter_days", "expected_interval"),
    [
        pytest.param(True, Dormancy.WINTER_INTERVAL, 14, 14, id="in-wi-set"),
        pytest.param(True, Dormancy.WINTER_INTERVAL, None, 7, id="in-wi-none"),
        pytest.param(False, Dormancy.WINTER_INTERVAL, 14, 7, id="out-wi-set"),
        pytest.param(False, Dormancy.WINTER_INTERVAL, None, 7, id="out-wi-none"),
    ],
)
def test_effective_interval_branch_matrix(
    in_window: bool,
    dormancy: Dormancy,
    winter_days: int | None,
    expected_interval: int,
) -> None:
    """B-U7: the non-paused effective-interval branch table (CRITICAL, AC3).

    Fixes last_event_on == today == D so the only observable that moves is
    next_due == D + effective_interval.
    """
    today = _IN_WINDOW_DAY if in_window else _OUT_OF_WINDOW_DAY
    result = compute_due(
        _schedule(interval=7, winter=winter_days, dormancy=dormancy),
        last_event_on=today,
        today=today,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == today + timedelta(days=expected_interval)
    assert result.overdue_days == 0


# ========================================================= 3c. paused null-path
def test_paused_in_window_is_null_due() -> None:
    """B-U10: paused in-window -> next_due None AND overdue None (CRITICAL, AC4)."""
    result = compute_due(
        _schedule(dormancy=Dormancy.PAUSED),
        last_event_on=_IN_WINDOW_DAY,
        today=_IN_WINDOW_DAY,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due is None
    assert result.overdue_days is None


def test_paused_in_window_ignores_winter_days() -> None:
    """B-U11: paused in-window with winter_days set still null (branch order)."""
    result = compute_due(
        _schedule(dormancy=Dormancy.PAUSED, winter=14),
        last_event_on=_IN_WINDOW_DAY,
        today=_IN_WINDOW_DAY,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due is None
    assert result.overdue_days is None


def test_same_paused_schedule_out_of_window_computes_normally() -> None:
    """B-U12: the SAME paused schedule out-of-window computes normally (CRITICAL)."""
    result = compute_due(
        _schedule(dormancy=Dormancy.PAUSED, interval=7),
        last_event_on=_OUT_OF_WINDOW_DAY,
        today=_OUT_OF_WINDOW_DAY + timedelta(days=9),
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _OUT_OF_WINDOW_DAY + timedelta(days=7)
    assert result.overdue_days == 2


# ===================================================== 3d. matching-type at the seam
def test_result_carries_schedule_care_type() -> None:
    """B-U13: the result is keyed by the schedule's care_type, not the event."""
    water = compute_due(
        _schedule(care_type=CareType.WATER),
        last_event_on=_D,
        today=_D,
        window=_WINDOW,
        seasonal_aware=True,
    )
    feed = compute_due(
        _schedule(care_type=CareType.FEED),
        last_event_on=_D,
        today=_D,
        window=_WINDOW,
        seasonal_aware=True,
    )
    assert water.care_type == CareType.WATER
    assert feed.care_type == CareType.FEED


# ============================================ 3e. WinterWindow.contains M2 (AC5)
_WINDOW_A = WinterWindow(start_month=4, start_day=1, end_month=9, end_day=1)  # non-wrap
_WINDOW_B = WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1)  # wrap


@pytest.mark.parametrize(
    ("window", "test_date", "expected"),
    [
        pytest.param(_WINDOW_A, date(2026, 3, 31), False, id="A-before-start"),
        pytest.param(_WINDOW_A, date(2026, 4, 1), True, id="A-start"),
        pytest.param(_WINDOW_A, date(2026, 6, 15), True, id="A-mid"),
        pytest.param(_WINDOW_A, date(2026, 9, 1), True, id="A-end"),
        pytest.param(_WINDOW_A, date(2026, 9, 2), False, id="A-after-end"),
        pytest.param(_WINDOW_B, date(2026, 10, 31), False, id="B-before-start"),
        pytest.param(_WINDOW_B, date(2026, 11, 1), True, id="B-start"),
        pytest.param(_WINDOW_B, date(2026, 1, 15), True, id="B-january"),
        pytest.param(_WINDOW_B, date(2026, 2, 27), True, id="B-feb-late"),
        pytest.param(_WINDOW_B, date(2026, 3, 1), True, id="B-end"),
        pytest.param(_WINDOW_B, date(2026, 3, 2), False, id="B-after-end"),
        pytest.param(_WINDOW_B, date(2026, 7, 1), False, id="B-summer"),
        pytest.param(_WINDOW_B, date(1999, 1, 15), True, id="B-year-agnostic"),
    ],
)
def test_winter_window_contains(
    window: WinterWindow, test_date: date, expected: bool
) -> None:
    """B-U14: the window-edge matrix incl. the new-year wrap (CRITICAL, AC5)."""
    assert window.contains(test_date) is expected


# ================================================ US-3.5: seasonal_aware parameter
# The wrapping default (Nov 1 - Mar 1); a Jan/Dec ``today`` is inside it, a summer one
# outside. Used by the seasonal_aware=False matrix so "in-window" rows are genuinely in.
_DEFAULT_WINDOW = WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1)
_WINTER_DAY = date(2026, 1, 15)  # inside Nov 1 - Mar 1
_SUMMER_DAY = date(2026, 7, 1)  # outside Nov 1 - Mar 1


# ============================ 3a. seasonal_aware=False matrix M1 (CRITICAL, AC3)
@pytest.mark.parametrize(
    ("in_window", "dormancy", "winter_days"),
    [
        pytest.param(True, Dormancy.PAUSED, 14, id="off-in-paused-set"),
        pytest.param(True, Dormancy.PAUSED, None, id="off-in-paused-none"),
        pytest.param(True, Dormancy.WINTER_INTERVAL, 14, id="off-in-wi-set"),
        pytest.param(True, Dormancy.WINTER_INTERVAL, None, id="off-in-wi-none"),
        pytest.param(False, Dormancy.PAUSED, 14, id="off-out-paused-set"),
        pytest.param(False, Dormancy.WINTER_INTERVAL, 14, id="off-out-wi-set"),
    ],
)
def test_seasonal_off_ignores_window_and_paused(
    in_window: bool,
    dormancy: Dormancy,
    winter_days: int | None,
) -> None:
    """B-U15: toggle off -> plain interval, ignoring window AND paused (CRITICAL, AC3).

    With ``seasonal_aware=False`` the function short-circuits to the plain
    ``interval_days`` (7 here) BEFORE any window/paused/winter selection. The headline
    trio (``off-in-paused-set`` / ``off-in-paused-none`` / ``off-in-wi-set``) would
    return null or 14 under the US-3.3 body; off must return ``D + 7`` (never null,
    never 14). ``last == today == D`` isolates the interval selection from overdue math.
    """
    today = _WINTER_DAY if in_window else _SUMMER_DAY
    result = compute_due(
        _schedule(interval=7, winter=winter_days, dormancy=dormancy),
        last_event_on=today,
        today=today,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == today + timedelta(days=7)
    assert result.overdue_days == 0


def test_seasonal_off_no_event_due_today() -> None:
    """B-U16: toggle off + no matching event -> due today, overdue 0 (no-event arm)."""
    result = compute_due(
        _schedule(interval=7, dormancy=Dormancy.PAUSED),
        last_event_on=None,
        today=_WINTER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == _WINTER_DAY
    assert result.overdue_days == 0


def test_seasonal_off_overdue_accrues_normally() -> None:
    """B-U17: toggle off + paused-in-window, today=D+9 -> overdue 2 (not suppressed)."""
    result = compute_due(
        _schedule(interval=7, winter=14, dormancy=Dormancy.PAUSED),
        last_event_on=_WINTER_DAY,
        today=_WINTER_DAY + timedelta(days=9),
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == _WINTER_DAY + timedelta(days=7)
    assert result.overdue_days == 2


# ==================== 3b. seasonal_aware=True equivalence + divergence (CRITICAL)
def test_seasonal_on_paused_in_window_still_nulls() -> None:
    """B-U18: toggle on + paused-in-window -> still (None, None) (US-3.3 survives)."""
    result = compute_due(
        _schedule(dormancy=Dormancy.PAUSED),
        last_event_on=_WINTER_DAY,
        today=_WINTER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due is None
    assert result.overdue_days is None


def test_seasonal_on_in_window_winter_interval_applies() -> None:
    """B-U19: toggle on + in-window winter_interval -> winter cadence D+14 (US-3.3)."""
    result = compute_due(
        _schedule(interval=7, winter=14, dormancy=Dormancy.WINTER_INTERVAL),
        last_event_on=_WINTER_DAY,
        today=_WINTER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=True,
    )
    assert result.next_due == _WINTER_DAY + timedelta(days=14)
    assert result.overdue_days == 0


def test_seasonal_toggle_is_the_only_moving_part() -> None:
    """B-U20: ONE fixture, two flag values -> the toggle is the only diff (CRITICAL).

    A paused, winter=14, in-window schedule with ``last == today == D``: on -> (None,
    None) (US-3.3 paused null-path); off -> ``D + 7`` (plain interval). The single proof
    that the added parameter is the only moving part of the fork.
    """
    schedule = _schedule(interval=7, winter=14, dormancy=Dormancy.PAUSED)
    on_result = compute_due(
        schedule,
        last_event_on=_WINTER_DAY,
        today=_WINTER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=True,
    )
    off_result = compute_due(
        schedule,
        last_event_on=_WINTER_DAY,
        today=_WINTER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert on_result.next_due is None
    assert on_result.overdue_days is None
    assert off_result.next_due == _WINTER_DAY + timedelta(days=7)
    assert off_result.overdue_days == 0


# ============================================ 3c. _due_from shared-tail behaviour
def test_due_from_no_event_due_today() -> None:
    """B-U21: shared tail, no event -> due today, overdue 0 (off-path arm)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=None,
        today=_SUMMER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == _SUMMER_DAY
    assert result.overdue_days == 0


def test_due_from_event_present_last_plus_interval() -> None:
    """B-U22: shared tail, event present -> last + interval (off-path, interval 7)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_SUMMER_DAY,
        today=_SUMMER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == _SUMMER_DAY + timedelta(days=7)
    assert result.overdue_days == 0


@pytest.mark.parametrize(
    ("offset", "expected_overdue"),
    [
        pytest.param(7, 0, id="on-the-due-day"),
        pytest.param(8, 1, id="one-day-after"),
        pytest.param(9, 2, id="two-days-after"),
    ],
)
def test_due_from_overdue_clamp_and_boundary(
    offset: int, expected_overdue: int
) -> None:
    """B-U23: shared tail overdue clamp + due-day boundary (due day NOT overdue)."""
    result = compute_due(
        _schedule(interval=7),
        last_event_on=_SUMMER_DAY,
        today=_SUMMER_DAY + timedelta(days=offset),
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert result.next_due == _SUMMER_DAY + timedelta(days=7)
    assert result.overdue_days == expected_overdue


def test_due_from_carries_schedule_care_type() -> None:
    """B-U24: shared tail keys the result by the schedule care_type (water/feed)."""
    water = compute_due(
        _schedule(care_type=CareType.WATER),
        last_event_on=_SUMMER_DAY,
        today=_SUMMER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    feed = compute_due(
        _schedule(care_type=CareType.FEED),
        last_event_on=_SUMMER_DAY,
        today=_SUMMER_DAY,
        window=_DEFAULT_WINDOW,
        seasonal_aware=False,
    )
    assert water.care_type == CareType.WATER
    assert feed.care_type == CareType.FEED
