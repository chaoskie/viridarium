"""ASGI entry point.

``uvicorn plant_care.main:app`` serves the wired application built from environment
settings.
"""

from __future__ import annotations

from plant_care.infrastructure.app import create_app

app = create_app()
