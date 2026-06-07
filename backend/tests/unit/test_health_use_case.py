"""Unit test for the health use case (TEST-002: no app, no DB, no I/O)."""

import pytest

from plant_care.application.health import GetHealthStatus
from plant_care.domain.health import HealthStatus

pytestmark = pytest.mark.unit


def test_status_reports_ok_with_injected_version() -> None:
    use_case = GetHealthStatus(version="9.9.9")

    result = use_case.status()

    assert result == HealthStatus(status="ok", version="9.9.9")
