"""ASGI entry point.

``uvicorn viridarium.main:app`` serves the wired application built from environment
settings.
"""

from __future__ import annotations

from viridarium.infrastructure.app import create_app

app = create_app()
