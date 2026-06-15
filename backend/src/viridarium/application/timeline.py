"""Care-history timeline query service (US-3.4, ARCH-006: a dedicated read, no writes).

Merges a plant's care events (US-3.2) and photos (US-2.3) server-side into one
reverse-chronological, discriminated feed. A read joining two contexts -> a dedicated
query module (ARCH-006); it reuses the existing repositories' list reads and merges in
memory (no new persistence, no migration, PRIN-IX).

The feed entry is a tagged shape - :class:`TimelineEvent` | :class:`TimelinePhoto` -
kept framework-free here in the application layer; the web adapter maps it to the wire
schema. The :func:`merge_timeline` transform is pure (no I/O) so its dedup/sort logic is
unit-pinned (test-foundation §4f) without a DB round-trip.

Dedup: a photo whose id is referenced by some event's ``photo_id`` is emitted only
inline on that event entry, never as a standalone ``TimelinePhoto`` (dedup, AC2).
Sort: by ``(date, created_at)`` descending - ``date`` is ``happened_on`` for events and
``created_at.date()`` for photos, so a backdated event sorts to its ``happened_on`` slot
(AC1); the ``created_at`` timestamp breaks same-``date`` ties deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from viridarium.domain.care_event import (
    CareEvent,
    CareEventRepository,
    CareEventType,
    Health,
    PlantNotFoundForEventError,
)
from viridarium.domain.photo import Photo, PhotoRepository


@dataclass(frozen=True, slots=True)
class TimelinePhotoRef:
    """The inline/standalone photo reference carried by a timeline entry.

    Exposes only ``id`` (the wire adapter computes the bytes ``url`` from it) - the
    on-disk ``stored_filename`` security boundary never reaches this type (ARCH-007).
    """

    id: int


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """A care-event timeline entry (``kind:"event"``).

    ``date`` is the event's ``happened_on``; ``photo`` is the inline linked photo or
    ``None``. ``health`` is non-null only on observe events (the domain already enforces
    that). ``_created_at`` is the deterministic same-``date`` sort tiebreak, not a wire
    field.
    """

    event_type: CareEventType
    date: date
    note: str | None
    health: Health | None
    photo: TimelinePhotoRef | None
    _created_at: datetime


@dataclass(frozen=True, slots=True)
class TimelinePhoto:
    """A standalone (unlinked) photo timeline entry (``kind:"photo"``).

    ``date`` is the photo's ``created_at.date()``. ``_created_at`` is the deterministic
    same-``date`` sort tiebreak, not a wire field.
    """

    date: date
    photo: TimelinePhotoRef
    _created_at: datetime


TimelineEntry = TimelineEvent | TimelinePhoto


def merge_timeline(events: list[CareEvent], photos: list[Photo]) -> list[TimelineEntry]:
    """Merge events + photos into one reverse-chronological deduped feed (pure).

    1. ``linked`` = the set of photo ids referenced by some event (the dedup set).
    2. Emit one :class:`TimelineEvent` per event, carrying its inline photo when
       ``photo_id`` is set.
    3. Emit one :class:`TimelinePhoto` per photo whose id is NOT in ``linked``.
    4. Sort by ``(date, created_at)`` descending (newest-first, stable same-``date``).
    """
    # PRIN-I length note: four flat statements; the line count is multi-line dataclass
    # constructors, not branching (max depth 2). Kept inline for readability.
    linked = {event.photo_id for event in events if event.photo_id is not None}
    entries: list[TimelineEntry] = [
        TimelineEvent(
            event_type=event.type,
            date=event.happened_on,
            note=event.note,
            health=event.health,
            photo=(
                TimelinePhotoRef(id=event.photo_id)
                if event.photo_id is not None
                else None
            ),
            _created_at=event.created_at,
        )
        for event in events
    ]
    entries.extend(
        TimelinePhoto(
            date=photo.created_at.date(),
            photo=TimelinePhotoRef(id=photo.id),
            _created_at=photo.created_at,
        )
        for photo in photos
        if photo.id not in linked
    )
    entries.sort(key=lambda entry: (entry.date, entry._created_at), reverse=True)
    return entries


class TimelineQueryService:
    """Assemble a plant's care-history timeline from two list reads (US-3.4, no writes).

    Reuses :meth:`CareEventRepository.list_for_plant` and
    :meth:`PhotoRepository.list_for_plant` (both already dual-engine, ARCH-011) plus the
    plant-exists guard, then merges in memory - a bounded query count regardless of
    history size (no per-entry read).
    """

    def __init__(
        self,
        event_repository: CareEventRepository,
        photo_repository: PhotoRepository,
    ) -> None:
        self.event_repository = event_repository
        self.photo_repository = photo_repository

    def for_plant(self, plant_id: int) -> list[TimelineEntry]:
        """Return the plant's reverse-chronological deduped timeline.

        Guards plant existence FIRST (the VIRIDARIUM-48 convention) - a missing plant
        raises :class:`PlantNotFoundForEventError` (mapped to 404) before any merge.
        """
        if not self.event_repository.plant_exists(plant_id):
            raise PlantNotFoundForEventError(plant_id)
        events = self.event_repository.list_for_plant(plant_id)
        photos = self.photo_repository.list_for_plant(plant_id)
        return merge_timeline(events, photos)
