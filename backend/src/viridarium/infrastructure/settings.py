"""Application settings, loaded from environment variables (SEC-006).

No secrets are hardcoded. ``DATABASE_URL`` follows the standard SQLAlchemy URL form so
PostgreSQL can be selected at deploy time without code changes (ARCH-001, ARCH-011).
The secure-by-default posture (SEC-003) lives here: CORS is empty by default (no
wildcard) and the bind address is configurable.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistence. SQLite by default for zero-config self-hosting (ARCH-001).
    database_url: str = Field(default="sqlite:///data/app.db")

    # Service metadata surfaced by /api/v1/health.
    version: str = Field(default="0.1.0")

    # Network posture (SEC-003). Defaults are safe for trusted-network deployment.
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # CORS (SEC-003): explicit allow-list, empty by default. No wildcard-with-creds.
    cors_allow_origins: list[str] = Field(default_factory=list)

    # Built SPA directory served at "/" by the single-container image (product-spec
    # section 7). Unset by default so dev/test runs stay API-only.
    static_dir: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
