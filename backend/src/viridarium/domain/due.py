"""Due-computation domain logic (framework-free, pure - US-3.3).

The core read rule (proposal §3, verbatim):
``next_due = date(last matching CareEvent) + effective_interval``.

This module holds the I/O-free behaviour core: the :class:`WinterWindow` value object
(the year-agnostic, wrap-aware seasonal classifier), the :class:`ScheduleDue` result,
and the pure :func:`compute_due`. The query orchestration (batch loads, group-by-plant)
lives in :mod:`viridarium.application.due`; this layer never touches a repository, a
clock, or the framework (ARCH-006, the domain import contract).

``today`` and ``window`` are injected into :func:`compute_due` so every computation is
deterministic and testable with no clock dependence (proposal §"today"; SEC-003: no
per-user timezone in v1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from viridarium.domain.care_schedule import CareSchedule, CareType, Dormancy


@dataclass(frozen=True, slots=True)
class WinterWindow:
    """The seasonal dormancy window as year-agnostic ``(month, day)`` endpoints.

    Both endpoints are **inclusive**. The window may wrap the new year: a window whose
    start is later in the year than its end (e.g. Nov 1 - Mar 1) is in effect from the
    start through Dec 31 and from Jan 1 through the end. The default provider returns
    Nov 1 - Mar 1 until US-3.5 persists a configurable window.
    """

    start_month: int
    start_day: int
    end_month: int
    end_day: int

    def contains(self, day: date) -> bool:
        """Return whether ``day`` falls inside the window (year-agnostic, inclusive)."""
        md = (day.month, day.day)
        start = (self.start_month, self.start_day)
        end = (self.end_month, self.end_day)
        if start <= end:
            return start <= md <= end
        # Wrapping window (e.g. Nov 1 - Mar 1): in effect at/after start OR at/before
        # end.
        return md >= start or md <= end


@dataclass(frozen=True, slots=True)
class ScheduleDue:
    """The computed due state for one enabled schedule of a non-archived plant.

    ``next_due`` is ``None`` only when the schedule is paused inside the window (dormant
    this season); ``overdue_days`` is ``None`` **iff** ``next_due`` is ``None`` (the
    both-null invariant). Otherwise ``overdue_days`` is ``>= 0`` (clamped, never
    negative). The result is keyed by the **schedule's** ``care_type``, not the event's.
    """

    care_type: CareType
    next_due: date | None
    overdue_days: int | None


def _due_from(
    care_type: CareType,
    last_event_on: date | None,
    today: date,
    interval: int,
) -> ScheduleDue:
    """The shared no-event/overdue tail (US-3.5): both on-path and off-path use it.

    No matching event -> due immediately (``next_due = today``, ``overdue = 0``). Else
    ``next_due = last_event_on + interval`` and ``overdue = max(0, today - next_due)``
    (the due day itself is not overdue). Keyed by the schedule's ``care_type``.
    """
    if last_event_on is None:
        return ScheduleDue(care_type, next_due=today, overdue_days=0)
    next_due = last_event_on + timedelta(days=interval)
    overdue = max(0, (today - next_due).days)
    return ScheduleDue(care_type, next_due=next_due, overdue_days=overdue)


def compute_due(
    schedule: CareSchedule,
    last_event_on: date | None,
    today: date,
    window: WinterWindow,
    seasonal_aware: bool,
) -> ScheduleDue:
    """Compute the due state for one enabled schedule (the caller pre-filtered).

    Precondition: ``schedule.enabled`` is ``True`` and the owning plant is not archived
    (the query service / router enforce both).

    When ``seasonal_aware`` is ``False`` (US-3.5 global toggle off) the function ignores
    both the window AND ``paused`` entirely and returns the plain ``interval_days`` due
    via the shared tail (never null). When ``True`` the behaviour is exactly US-3.3:

    1. in-window + paused -> never due this window (``next_due``/``overdue_days`` null);
    2. in-window + winter_interval with ``winter_interval_days`` set -> winter cadence;
    3. otherwise -> the normal ``interval_days`` (normal season, or winter fallback when
       ``winter_interval_days`` is unset), then the shared no-event/overdue tail.
    """
    if not seasonal_aware:
        return _due_from(
            schedule.care_type, last_event_on, today, schedule.interval_days
        )
    in_window = window.contains(today)
    if in_window and schedule.dormancy is Dormancy.PAUSED:
        return ScheduleDue(schedule.care_type, next_due=None, overdue_days=None)
    if (
        in_window
        and schedule.dormancy is Dormancy.WINTER_INTERVAL
        and schedule.winter_interval_days is not None
    ):
        interval = schedule.winter_interval_days
    else:
        interval = schedule.interval_days
    return _due_from(schedule.care_type, last_event_on, today, interval)
