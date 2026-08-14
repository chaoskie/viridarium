"""Migration entrypoint: ``python -m viridarium.migrate`` (VIRIDARIUM-67).

Runs before uvicorn binds in the container entrypoint, so a fresh deploy never serves
a request against a schemaless database. Exits non-zero on failure so the container
fails loudly instead of coming up "healthy" with no tables.
"""

from __future__ import annotations

import logging
import sys

from viridarium.infrastructure.migrations import upgrade_to_head
from viridarium.infrastructure.settings import get_settings

logger = logging.getLogger("viridarium.migrate")


def main() -> int:
    """Upgrade the configured database to head; return a process exit code."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s"
    )
    settings = get_settings()
    # The URL itself is never logged: it can carry credentials for the PostgreSQL
    # deployment shape (SEC-006/SEC-007).
    logger.info("Applying database migrations to head")
    try:
        upgrade_to_head(settings.database_url)
    except Exception:
        logger.exception("Database migration failed; refusing to start the server")
        return 1
    logger.info("Database schema is at head")
    return 0


if __name__ == "__main__":
    sys.exit(main())
