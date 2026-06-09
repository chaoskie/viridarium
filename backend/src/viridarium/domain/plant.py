"""Plant domain types (framework-free).

The second persisted aggregate (US-2.1), mirroring the Location [TEMPLATE] (ADR-B):
a persisted ``Plant`` + ``NewPlant`` pair, typed ``XNotFoundError`` carrying no PII
(only the id), and a ``PlantRepository`` ``Protocol`` whose ``get``/``update``/
``delete`` raise the domain error on a missing row and never return framework types.

Novel here (vs Location): the optional ``location_id`` reference (homeless = ``None``,
D-009 / D1), the ``tags`` tuple persisted to a normalized child table (D2), the two
``StrEnum`` attribute types stored as strings (D3), the ``PlantFilter`` value object
that drives the portable search/filter query (D4), and the cross-aggregate
``LocationNotFoundForPlantError`` (a body-reference failure -> 422, distinct from the
404 of the addressed plant) plus the ``location_exists`` port read backing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol


class PotMaterial(StrEnum):
    """Pot material, stored as a string (D3). Values are the spec wire form."""

    TERRACOTTA = "terracotta"
    PLASTIC = "plastic"
    CERAMIC = "ceramic"
    SELF_WATERING = "self-watering"
    OTHER = "other"


class LightLevel(StrEnum):
    """Light level, stored as a string (D3). Values are the spec wire form."""

    DARK = "dark"
    INDIRECT = "indirect"
    BRIGHT_INDIRECT = "bright-indirect"
    FULL_SUN = "full-sun"


@dataclass(frozen=True, slots=True)
class Plant:
    """A persisted plant.

    ``location_id`` is optional: ``None`` means the plant is homeless (D-009).
    ``created_at``/``updated_at`` are server-set infrastructural metadata (ADR-A),
    absent from :class:`NewPlant`. ``tags`` is an immutable tuple persisted to the
    normalized ``plant_tag`` child table (D2).
    """

    id: int
    name: str
    species: str | None
    location_id: int | None
    acquired_on: date | None
    pot_size_cm: int | None
    pot_material: PotMaterial | None
    light_level: LightLevel | None
    notes: str | None
    tags: tuple[str, ...]
    archived: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewPlant:
    """A plant to create: the client-supplied fields only (no server-set fields)."""

    name: str
    species: str | None
    location_id: int | None
    acquired_on: date | None
    pot_size_cm: int | None
    pot_material: PotMaterial | None
    light_level: LightLevel | None
    notes: str | None
    tags: tuple[str, ...]
    archived: bool


@dataclass(frozen=True, slots=True)
class PlantFilter:
    """Optional, AND-combined search/filter criteria for the plant list (D4).

    The default (all-``None``/false) is **active only**: archived plants are excluded
    unless ``archived`` or ``include_archived`` says otherwise (US-2.4 / A2). ``q`` is a
    substring over name|species; ``species`` a substring over species; ``location_id``
    an exact match; ``tag`` an EXISTS over ``plant_tag``; ``homeless`` restricts to
    null-location plants. ``archived`` (``None``/``False`` -> active only; ``True`` ->
    archived only) and ``include_archived`` (``True`` -> no archived clause, return all)
    drive the archived filter. Portable across SQLite/PostgreSQL (lowered-LIKE + EXISTS,
    ARCH-011).
    """

    q: str | None = None
    location_id: int | None = None
    tag: str | None = None
    species: str | None = None
    homeless: bool = False
    archived: bool | None = None
    include_archived: bool = False


class PlantNotFoundError(Exception):
    """Raised when no plant exists for the given id.

    Carries only the integer id (SEC-001/PRIN-II: no PII in the message or any
    derived error body).
    """

    def __init__(self, plant_id: int) -> None:
        self.plant_id = plant_id
        super().__init__(f"Plant {plant_id} not found")


class LocationNotFoundForPlantError(Exception):
    """Raised when a plant references a ``location_id`` that does not exist.

    A body-reference validation failure (mapped to 422, not 404 - 404 is reserved for
    the addressed plant). Carries only the integer location id (SEC-001: no PII).
    """

    def __init__(self, location_id: int) -> None:
        self.location_id = location_id
        super().__init__(f"Location {location_id} not found")


class PlantRepository(Protocol):
    """Outbound port for persisting and querying :class:`Plant` aggregates."""

    def add(self, new_plant: NewPlant) -> Plant:
        """Persist a new plant (and its tags) and return it with server-set fields."""
        ...

    def list(self, plant_filter: PlantFilter) -> list[Plant]:
        """Return plants matching the filter, ordered by ``name`` ascending."""
        ...

    def get(self, plant_id: int) -> Plant:
        """Return the plant or raise :class:`PlantNotFoundError`."""
        ...

    def update(self, plant_id: int, new_plant: NewPlant) -> Plant:
        """Full-replace the plant's fields and tags (ADR-D) or raise not-found."""
        ...

    def delete(self, plant_id: int) -> None:
        """Delete the plant (and cascade its tags) or raise the not-found error."""
        ...

    def archive(self, plant_id: int) -> Plant:
        """Set ``archived`` true (idempotent) or raise :class:`PlantNotFoundError`."""
        ...

    def unarchive(self, plant_id: int) -> Plant:
        """Set ``archived`` false (idempotent) or raise :class:`PlantNotFoundError`."""
        ...

    def location_exists(self, location_id: int) -> bool:
        """Return whether a location with the given id exists (cross-aggregate read)."""
        ...
