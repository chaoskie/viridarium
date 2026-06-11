"""Response schemas for the public REST API surface (ARCH-007, ARCH-008).

Response schemas are a security boundary: only fields meant to leave the service
appear here. Use cases return domain types; this layer maps them to the wire shape.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from viridarium.domain.care_event import CareEvent, CareEventType, Health
from viridarium.domain.care_schedule import CareSchedule, CareType, Dormancy
from viridarium.domain.photo import Photo
from viridarium.domain.plant import LightLevel, PotMaterial


class HealthResponse(BaseModel):
    """Public shape of GET /api/v1/health."""

    status: str
    version: str


def _trim_non_empty_name(value: str) -> str:
    """Trim ``name`` and reject whitespace-only input (422 via ValueError)."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("name must not be empty or whitespace-only")
    return trimmed


class LocationCreate(BaseModel):
    """Request body for POST /api/v1/locations.

    ``name`` is trimmed and must be non-empty (whitespace-only -> 422 via the
    ``field_validator``); ``notes`` is optional and capped at 2000 chars.
    """

    name: str = Field(min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return _trim_non_empty_name(value)


class LocationUpdate(LocationCreate):
    """Request body for PUT /api/v1/locations/{id} (full-replace, ADR-D)."""


class LocationResponse(BaseModel):
    """Public shape of a location (security boundary, ARCH-007)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


def _normalize_tags(values: list[str]) -> list[str]:
    """Trim, drop empties, dedupe (order-preserving) the tag list (design §1)."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        tag = raw.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
    return cleaned


class PlantCreate(BaseModel):
    """Request body for POST /api/v1/plants (design §1).

    ``name`` is trimmed and must be non-empty (whitespace-only -> 422); enums validate
    against the domain ``StrEnum`` wire values; ``tags`` items are trimmed, non-empty,
    capped at 50 chars, deduped, and capped at 50 items. ``location_id`` is optional
    (``null`` = homeless); a non-existent id is rejected later as 422 by the service.
    """

    name: str = Field(min_length=1, max_length=120)
    species: str | None = Field(default=None, max_length=200)
    location_id: int | None = Field(default=None)
    acquired_on: date | None = Field(default=None)
    pot_size_cm: int | None = Field(default=None, ge=1, le=500)
    pot_material: PotMaterial | None = Field(default=None)
    light_level: LightLevel | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=10000)
    tags: list[str] = Field(default_factory=list, max_length=50)
    archived: bool = Field(default=False)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return _trim_non_empty_name(value)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, values: list[str]) -> list[str]:
        for raw in values:
            if len(raw.strip()) > 50:
                raise ValueError("each tag must be at most 50 characters")
        return _normalize_tags(values)


class PlantUpdate(PlantCreate):
    """Request body for PUT /api/v1/plants/{id} (full-replace, ADR-D)."""


class PlantResponse(BaseModel):
    """Public shape of a plant (security boundary, ARCH-007)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    species: str | None
    location_id: int | None
    acquired_on: date | None
    pot_size_cm: int | None
    pot_material: PotMaterial | None
    light_level: LightLevel | None
    notes: str | None
    tags: list[str]
    archived: bool
    created_at: datetime
    updated_at: datetime


class PhotoResponse(BaseModel):
    """Public shape of a photo (security boundary, ARCH-007).

    Deliberately omits ``stored_filename`` (the on-disk name never crosses the response
    boundary). ``url`` is the computed bytes endpoint for this photo; the client fetches
    the raw image from there.
    """

    id: int
    plant_id: int
    content_type: str
    size_bytes: int
    is_cover: bool
    created_at: datetime
    url: str

    @classmethod
    def from_domain(cls, photo: Photo) -> PhotoResponse:
        """Build the wire response from a domain :class:`Photo`."""
        return cls(
            id=photo.id,
            plant_id=photo.plant_id,
            content_type=photo.content_type,
            size_bytes=photo.size_bytes,
            is_cover=photo.is_cover,
            created_at=photo.created_at,
            url=f"/api/v1/plants/{photo.plant_id}/photos/{photo.id}",
        )


class CareEventCreate(BaseModel):
    """Request body for POST /api/v1/plants/{id}/events (US-3.2, append-only).

    ``type`` validates against the closed ``CareEventType`` enum (unknown -> 422).
    ``happened_on`` defaults to today; backdating is allowed but a **future date is
    422** (the ``field_validator``). ``note`` mirrors the plant notes 10000-char cap;
    the empty string is accepted as-is (no normalization). ``photo_id`` and ``health``
    are optional - the same-plant photo rule and the health-only-on-observe rule are
    semantic (service-level), not shape rules, so they reject there.
    """

    type: CareEventType
    happened_on: date = Field(default_factory=date.today)
    note: str | None = Field(default=None, max_length=10000)
    photo_id: int | None = Field(default=None)
    health: Health | None = Field(default=None)

    @field_validator("happened_on")
    @classmethod
    def _reject_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("happened_on must not be in the future")
        return value


class CareEventResponse(BaseModel):
    """Public shape of a care event (security boundary, ARCH-007).

    Unlike CareSchedule this **does expose the surrogate ``id``**: DELETE is keyed by
    event id (proposal response shape). Events are immutable, so there is no
    ``updated_at``.
    """

    id: int
    plant_id: int
    type: CareEventType
    happened_on: date
    note: str | None
    photo_id: int | None
    health: Health | None
    created_at: datetime

    @classmethod
    def from_domain(cls, event: CareEvent) -> CareEventResponse:
        """Build the wire response from a domain :class:`CareEvent`."""
        return cls(
            id=event.id,
            plant_id=event.plant_id,
            type=event.type,
            happened_on=event.happened_on,
            note=event.note,
            photo_id=event.photo_id,
            health=event.health,
            created_at=event.created_at,
        )


class CareScheduleUpsert(BaseModel):
    """Request body for PUT /api/v1/plants/{id}/schedules/{care_type} (CS1).

    Keyed-PUT create-or-replace: ``care_type`` comes from the PATH only, never the body
    (``extra="forbid"`` rejects a stray ``care_type`` -> 422). Only ranges + enum
    membership are validated (no cross-field rule, CS3 / PO Q2): ``interval_days`` is
    required (ge=1 le=3650); ``winter_interval_days`` is optional (same range *when
    present*, default null); ``dormancy`` is optional - when omitted the router resolves
    the care-type default (feed->paused, water->winter_interval, CS2). ``enabled``
    defaults true.
    """

    model_config = ConfigDict(extra="forbid")

    interval_days: int = Field(ge=1, le=3650)
    winter_interval_days: int | None = Field(default=None, ge=1, le=3650)
    dormancy: Dormancy | None = Field(default=None)
    enabled: bool = Field(default=True)


class CareScheduleResponse(BaseModel):
    """Public shape of a care schedule (security boundary, ARCH-007).

    Keyed by ``care_type`` and deliberately **omits the surrogate ``id``** (ARCH-007):
    the resource is addressed by ``(plant_id, care_type)``, so the PK never crosses the
    wire.
    """

    plant_id: int
    care_type: CareType
    interval_days: int
    winter_interval_days: int | None
    dormancy: Dormancy
    enabled: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, schedule: CareSchedule) -> CareScheduleResponse:
        """Build the wire response from a domain :class:`CareSchedule` (no ``id``)."""
        return cls(
            plant_id=schedule.plant_id,
            care_type=schedule.care_type,
            interval_days=schedule.interval_days,
            winter_interval_days=schedule.winter_interval_days,
            dormancy=schedule.dormancy,
            enabled=schedule.enabled,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
