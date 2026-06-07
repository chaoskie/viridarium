"""Inbound web adapter: FastAPI routers and per-surface Pydantic schemas.

The only place HTTP exists (ARCH-002). Routers contain no business logic; they
(de)serialize and delegate to application use cases.
"""
