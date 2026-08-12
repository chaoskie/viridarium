"""Programmatic Alembic runner used by the container entrypoint (VIRIDARIUM-67).

The runtime image ships the migration tree and the ``alembic`` console script, but not
``alembic.ini`` (it lives at the backend project root, outside the copied ``src`` tree).
Rather than shipping the ini purely to satisfy the CLI, the config is built in code:
``script_location`` is derived from this package's own location, so it is correct in the
image (``/app/src/viridarium/...``), in a checkout, and in an installed wheel alike.

The database URL is resolved by ``env.py`` from application settings (``DATABASE_URL``),
so nothing about the deployment target is hardcoded here (SEC-006).
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

# <package>/infrastructure/migrations.py -> <package>/adapters/outbound/db/migrations
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_LOCATION = _PACKAGE_ROOT / "adapters" / "outbound" / "db" / "migrations"


def build_alembic_config(database_url: str | None = None) -> Config:
    """Build an Alembic config with no ini file on disk.

    ``database_url`` is optional: when omitted, ``env.py`` falls back to application
    settings. Percent signs are escaped because Alembic stores main options in a
    ``ConfigParser``, which would otherwise treat them as interpolation syntax.
    """
    cfg = Config()
    cfg.set_main_option("script_location", str(SCRIPT_LOCATION))
    if database_url is not None:
        cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return cfg


def upgrade_to_head(database_url: str | None = None) -> None:
    """Run ``alembic upgrade head``.

    Idempotent: on an already-current database Alembic applies nothing and returns,
    which is what makes it safe to run on every container start (restart loops).
    """
    command.upgrade(build_alembic_config(database_url), "head")
