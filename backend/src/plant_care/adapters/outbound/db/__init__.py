"""Outbound persistence adapter: SQLAlchemy + Alembic.

The only place persistence exists (ARCH-002). Engine-specific behaviour is isolated
here so the rest of the app stays engine-portable (ARCH-011).
"""
