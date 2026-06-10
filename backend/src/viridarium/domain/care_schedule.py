"""Care-schedule domain types (framework-free).

The first E3 aggregate (US-3.1): a ``CareSchedule`` owned child of ``Plant`` mirroring
the Photo [TEMPLATE] (ADR-B). A persisted ``CareSchedule`` + ``NewCareSchedule`` pair,
typed errors carrying no PII (only the integer plant id + the closed-enum care_type,
SEC-001/SEC-007), and a ``CareScheduleRepository`` ``Protocol`` whose ``get``/``delete``
raise the domain error on a missing row.

The two ``StrEnum`` attribute types use the spec wire vocabulary verbatim (SPEC-001):
``CareType`` is ``water``/``feed``; ``Dormancy`` is ``paused``/``winter_interval``.
``dormancy`` is stored and user-editable (CS2 / PO Q1) - the due engine (US-3.3) reads
this one field and never branches on care_type. ``winter_interval_days`` may be ``None``
even with ``winter_interval`` dormancy (CS3 / PO Q2): there is no cross-field rule here;
in winter the due engine falls back to the normal interval when it is unset.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class CareType(StrEnum):
    """The kind of care a schedule governs (spec vocab verbatim, SPEC-001)."""

    WATER = "water"
    FEED = "feed"


class Dormancy(StrEnum):
    """How the schedule behaves in dormancy (spec vocab verbatim, SPEC-001).

    ``paused`` stops the cadence for the dormant season; ``winter_interval`` switches to
    the (optional) winter cadence. Stored + user-editable (CS2 / PO Q1).
    """

    PAUSED = "paused"
    WINTER_INTERVAL = "winter_interval"


@dataclass(frozen=True, slots=True)
class CareSchedule:
    """A persisted care schedule for one ``(plant, care_type)`` pair.

    The surrogate ``id`` is the DB PK; it never crosses the response boundary
    (ARCH-007). ``created_at``/``updated_at`` are server-set (ADR-A).
    ``winter_interval_days`` is optional (``None`` = no distinct winter cadence; CS3).
    """

    id: int
    plant_id: int
    care_type: CareType
    interval_days: int
    winter_interval_days: int | None
    dormancy: Dormancy
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewCareSchedule:
    """A care schedule to upsert: the resolved client-supplied fields (no server id).

    ``dormancy`` is already resolved (the care-type default applied at the HTTP boundary
    when the body omitted it, CS2); the persistence layer stores it faithfully.
    """

    care_type: CareType
    interval_days: int
    winter_interval_days: int | None
    dormancy: Dormancy
    enabled: bool


class CareScheduleNotFoundError(Exception):
    """Raised when no schedule exists for the given ``(plant_id, care_type)``.

    Mapped to 404 at the boundary. Carries only the integer plant id + the closed-enum
    care_type (both non-PII identifiers) - never the plant name or any free text
    (SEC-001/SEC-007).
    """

    def __init__(self, plant_id: int, care_type: CareType) -> None:
        self.plant_id = plant_id
        self.care_type = care_type
        super().__init__(f"No {care_type} schedule for plant {plant_id}")


class PlantNotFoundForScheduleError(Exception):
    """Raised when the addressed plant does not exist (upsert/list guard).

    Mapped to 404 at the boundary. Carries only the integer plant id (no PII, SEC-001).
    """

    def __init__(self, plant_id: int) -> None:
        self.plant_id = plant_id
        super().__init__(f"Plant {plant_id} not found")


class CareScheduleRepository(Protocol):
    """Outbound port for persisting and querying :class:`CareSchedule` rows."""

    def upsert(self, plant_id: int, new: NewCareSchedule) -> CareSchedule:
        """Create-or-replace the row for ``(plant_id, new.care_type)`` (CS1)."""
        ...

    def list_for_plant(self, plant_id: int) -> list[CareSchedule]:
        """Return the plant's schedules ordered water-first (0-2 rows)."""
        ...

    def get(self, plant_id: int, care_type: CareType) -> CareSchedule:
        """Return the row or raise :class:`CareScheduleNotFoundError`."""
        ...

    def delete(self, plant_id: int, care_type: CareType) -> None:
        """Delete the row or raise :class:`CareScheduleNotFoundError`."""
        ...

    def plant_exists(self, plant_id: int) -> bool:
        """Return whether a plant with the given id exists (cross-aggregate read)."""
        ...
