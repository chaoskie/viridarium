"""Unit test for the health use case (TEST-002: no app, no DB, no I/O)."""

import pytest

from viridarium.application.health import GetHealthStatus, GetReadinessStatus
from viridarium.domain.health import HealthStatus, ReadinessStatus

pytestmark = pytest.mark.unit


def test_status_reports_ok_with_injected_version() -> None:
    use_case = GetHealthStatus(version="9.9.9")

    result = use_case.status()

    assert result == HealthStatus(status="ok", version="9.9.9")


class _StubInspector:
    """Schema inspector stub: returns a canned revision (TEST-002, no DB)."""

    def __init__(self, revision: str | None) -> None:
        self._revision = revision

    def current_revision(self) -> str | None:
        return self._revision


def test_readiness_is_ready_when_a_migration_revision_is_applied() -> None:
    use_case = GetReadinessStatus(_StubInspector("0008"), version="9.9.9")

    result = use_case.readiness()

    assert result == ReadinessStatus(
        status="ready", version="9.9.9", schema_revision="0008"
    )


def test_readiness_is_not_ready_when_the_schema_is_absent() -> None:
    use_case = GetReadinessStatus(_StubInspector(None), version="9.9.9")

    result = use_case.readiness()

    assert result == ReadinessStatus(
        status="not-ready", version="9.9.9", schema_revision=None
    )
