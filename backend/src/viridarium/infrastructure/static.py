"""Single-page-app static file serving (infrastructure layer).

The production container ships the built React SPA alongside the API and serves both
from one process (product-spec section 7). This mount is optional: when ``static_dir``
is unset or missing (the dev/test default), the app stays API-only and nothing changes.

Living in ``infrastructure`` keeps the hexagonal inward-only contract intact (ARCH-003):
this is app wiring, not a domain or application concern, and imports no inner layer.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class _SpaStaticFiles(StaticFiles):
    """StaticFiles that falls back to ``index.html`` for unmatched paths.

    The stock ``StaticFiles(html=True)`` serves ``index.html`` only for the directory
    root; a deep client-side route like ``/plants/42`` would 404. A single-page app
    needs every unknown non-asset path to return ``index.html`` so the in-browser
    router can take over. We map a 404 (and only a 404) to the SPA shell, leaving every
    other status untouched.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def mount_spa(app: FastAPI, static_dir: str | None) -> bool:
    """Mount the built SPA at ``/`` with an ``index.html`` fallback.

    Returns ``True`` when a static mount was installed, ``False`` when skipped (no
    directory configured or it does not exist on disk). The API router is mounted before
    this call, so ``/api/v1/*`` always takes precedence over the catch-all static mount.

    Real asset paths are served from disk; any unmatched path falls back to
    ``index.html`` so client-side routing works on full-page loads / refreshes.
    """
    if not static_dir:
        return False
    resolved = Path(static_dir)
    if not resolved.is_dir():
        return False
    app.mount("/", _SpaStaticFiles(directory=str(resolved), html=True), name="spa")
    return True
