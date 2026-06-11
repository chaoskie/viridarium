"""Care-event domain types (framework-free).

The append-only care history of US-3.2: a ``CareEvent`` owned child of ``Plant``
mirroring the CareSchedule [TEMPLATE] (ADR-B). A persisted ``CareEvent`` +
``NewCareEvent`` pair, typed errors carrying no PII (only integer ids + closed-enum
values, SEC-001/SEC-007), and a ``CareEventRepository`` ``Protocol`` whose ``delete``
raises the domain error on a missing/cross-plant row.

The two ``StrEnum`` attribute types use the spec wire vocabulary verbatim (SPEC-001):
``CareEventType`` is ``water``/``feed``/``repot``/``observe`` (NOT the schedule
``CareType`` - neither enum widens the other); ``Health`` is ``good``/``fair``/``bad``,
a journal input valid only on ``observe`` events (never aggregated). Events are never
updated (append-only, AC4); delete is allowed for mistakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol


class CareEventType(StrEnum):
    """The kind of care an event records (spec vocab verbatim, SPEC-001)."""

    WATER = "water"
    FEED = "feed"
    REPOT = "repot"
    OBSERVE = "observe"


class Health(StrEnum):
    """The observed plant health (spec vocab verbatim, SPEC-001).

    A journal input, only valid when the event type is ``observe``; never aggregated.
    """

    GOOD = "good"
    FAIR = "fair"
    BAD = "bad"


@dataclass(frozen=True, slots=True)
class CareEvent:
    """A persisted care event for one plant (append-only).

    Unlike CareSchedule the surrogate ``id`` DOES cross the response boundary: DELETE
    is keyed by event id. ``created_at`` is server-set (ADR-A); there is no
    ``updated_at`` because events are immutable (AC4). ``photo_id`` is an optional link
    to a photo of the same plant; photo deletion severs the link (SET NULL).
    """

    id: int
    plant_id: int
    type: CareEventType
    happened_on: date
    note: str | None
    photo_id: int | None
    health: Health | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewCareEvent:
    """A care event to append: the resolved client-supplied fields (no server id).

    ``happened_on`` is already resolved (the today default applied at the HTTP boundary
    when the body omitted it); the persistence layer stores it faithfully.
    """

    type: CareEventType
    happened_on: date
    note: str | None
    photo_id: int | None
    health: Health | None


class CareEventNotFoundError(Exception):
    """Raised when no event exists for the given ``(plant_id, event_id)``.

    Covers both a genuinely-missing event and a cross-plant reference (an event that
    exists but belongs to a different plant -> 404). Carries only the integer ids
    (SEC-001: no PII).
    """

    def __init__(self, plant_id: int, event_id: int) -> None:
        self.plant_id = plant_id
        self.event_id = event_id
        super().__init__(f"Care event {event_id} not found for plant {plant_id}")


class PlantNotFoundForEventError(Exception):
    """Raised when the addressed plant does not exist (create/list/delete guard).

    Mapped to 404 at the boundary. Carries only the integer plant id (no PII, SEC-001).
    """

    def __init__(self, plant_id: int) -> None:
        self.plant_id = plant_id
        super().__init__(f"Plant {plant_id} not found")


class PhotoNotForPlantError(Exception):
    """Raised when ``photo_id`` is unknown or belongs to a different plant.

    A body-reference failure mapped to 422 at the boundary (404 is reserved for the
    addressed plant/event). Carries only the integer ids (SEC-001: no PII).
    """

    def __init__(self, plant_id: int, photo_id: int) -> None:
        self.plant_id = plant_id
        self.photo_id = photo_id
        super().__init__(f"Photo {photo_id} does not belong to plant {plant_id}")


class HealthRequiresObserveError(Exception):
    """Raised when ``health`` is supplied on a non-``observe`` event type.

    The conditional domain rule (AC3) mapped to 422 at the boundary. Carries only the
    closed-enum type value (no PII, no free text - SEC-007).
    """

    def __init__(self, event_type: CareEventType) -> None:
        self.event_type = event_type
        super().__init__(f"health is only valid on observe events, not {event_type}")


class CareEventRepository(Protocol):
    """Outbound port for persisting and querying :class:`CareEvent` rows."""

    def add(self, plant_id: int, new: NewCareEvent) -> CareEvent:
        """Append the event row and return the persisted :class:`CareEvent`."""
        ...

    def list_for_plant(self, plant_id: int) -> list[CareEvent]:
        """Return the plant's events: ``happened_on`` desc, ``created_at`` desc."""
        ...

    def delete(self, plant_id: int, event_id: int) -> None:
        """Delete the row or raise :class:`CareEventNotFoundError` (cross-plant too)."""
        ...

    def plant_exists(self, plant_id: int) -> bool:
        """Return whether a plant with the given id exists (cross-aggregate read)."""
        ...

    def photo_plant_id(self, photo_id: int) -> int | None:
        """Return the owning plant id of a photo, or ``None`` for an unknown photo."""
        ...
