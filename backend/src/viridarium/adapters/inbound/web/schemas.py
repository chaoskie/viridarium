"""Response schemas for the public REST API surface (ARCH-007, ARCH-008).

Response schemas are a security boundary: only fields meant to leave the service
appear here. Use cases return domain types; this layer maps them to the wire shape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
