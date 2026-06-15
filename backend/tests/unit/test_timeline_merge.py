"""Unit tests for the pure timeline merge/dedup/sort (test-foundation §4f).

The one genuinely non-trivial pure transform in US-3.4 (TEST-001 (a)): the dedup set
membership, the ``happened_on``-vs-``created_at.date()`` sort-key selection, and the
``(date, created_at)`` desc tiebreak. Framework-free, no app, no DB - hand-built
``CareEvent`` / ``Photo`` value objects with explicit dates (no real clock). Pins
matrix M-TL's sort/dedup table (B-U1..B-U5).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from viridarium.application.timeline import (
    TimelineEvent,
    TimelinePhoto,
    merge_timeline,
)
from viridarium.domain.care_event import CareEvent, CareEventType, Health
from viridarium.domain.photo import Photo

pytestmark = pytest.mark.unit


def _event(
    event_id: int,
    happened_on: date,
    created_at: datetime,
    *,
    photo_id: int | None = None,
    event_type: CareEventType = CareEventType.WATER,
    health: Health | None = None,
    note: str | None = None,
) -> CareEvent:
    return CareEvent(
        id=event_id,
        plant_id=1,
        type=event_type,
        happened_on=happened_on,
        note=note,
        photo_id=photo_id,
        health=health,
        created_at=created_at,
    )


def _photo(photo_id: int, created_at: datetime) -> Photo:
    return Photo(
        id=photo_id,
        plant_id=1,
        stored_filename=f"{photo_id}.jpg",
        content_type="image/jpeg",
        size_bytes=10,
        is_cover=False,
        created_at=created_at,
    )


def test_linked_photo_not_emitted_as_photo_entry() -> None:  # B-U1
    """A linked photo id is inline on its event, never a kind:photo entry."""
    p = _photo(5, datetime(2026, 6, 1, 9, 0))
    e = _event(1, date(2026, 6, 1), datetime(2026, 6, 1, 10, 0), photo_id=5)

    entries = merge_timeline([e], [p])

    assert len(entries) == 1
    only = entries[0]
    assert isinstance(only, TimelineEvent)
    assert only.photo is not None
    assert only.photo.id == 5
    assert not any(isinstance(entry, TimelinePhoto) for entry in entries)


def test_standalone_photo_emitted_at_created_at_date() -> None:  # B-U2
    """An unlinked photo emits as a TimelinePhoto dated its created_at.date()."""
    q = _photo(7, datetime(2026, 6, 9, 14, 30))

    entries = merge_timeline([], [q])

    assert len(entries) == 1
    only = entries[0]
    assert isinstance(only, TimelinePhoto)
    assert only.photo.id == 7
    assert only.date == date(2026, 6, 9)


def test_interleave_default_standalone_photo_present() -> None:  # B-U3
    """Interleave (CONFIRMED default): a standalone photo on D3 precedes event on D2."""
    e = _event(1, date(2026, 6, 2), datetime(2026, 6, 2, 10, 0))
    q = _photo(7, datetime(2026, 6, 3, 8, 0))  # standalone, later date

    entries = merge_timeline([e], [q])

    assert [type(entry).__name__ for entry in entries] == [
        "TimelinePhoto",
        "TimelineEvent",
    ]
    assert [entry.date for entry in entries] == [date(2026, 6, 3), date(2026, 6, 2)]


def test_backdated_event_sorts_by_happened_on() -> None:  # B-U4
    """A is happened_on D2 created_at t1; B is happened_on D1 created_at t2>t1.

    Sorted by ``happened_on``: A (D2) precedes B (D1), regardless of created_at order.
    """
    a = _event(1, date(2026, 6, 2), datetime(2026, 6, 10, 9, 0))
    b = _event(2, date(2026, 6, 1), datetime(2026, 6, 10, 12, 0))

    entries = merge_timeline([a, b], [])

    assert [entry.date for entry in entries] == [date(2026, 6, 2), date(2026, 6, 1)]


def test_same_date_tiebreak_by_created_at_desc() -> None:  # B-U5
    """Same date D: ordered strictly by ``created_at`` desc, NOT by input order.

    The event (created_at 08:00, the EARLIEST) is built first and the standalone photo
    (created_at 12:00, the LATEST) second: a date-only sort would keep that input order
    (event, photo) and pass falsely, so the photo deliberately carries the LATER
    ``created_at``. The explicit ``created_at`` desc tiebreak must reorder to
    [photo (12:00), event (08:00)] - dropping the secondary key leaves the wrong order
    and this assertion goes red.
    """
    e = _event(1, date(2026, 6, 5), datetime(2026, 6, 5, 8, 0))
    q = _photo(7, datetime(2026, 6, 5, 12, 0))

    entries = merge_timeline([e], [q])

    assert [type(entry).__name__ for entry in entries] == [
        "TimelinePhoto",
        "TimelineEvent",
    ]
    assert [entry._created_at for entry in entries] == [
        datetime(2026, 6, 5, 12, 0),
        datetime(2026, 6, 5, 8, 0),
    ]
