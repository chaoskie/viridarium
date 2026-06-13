"""Integration tests for app settings: repo, service, web API, due wiring (US-3.5).

Real-DB slice through the singleton repository, the :class:`AppSettingsService` lazy
default, the GET/PUT ``/api/v1/settings`` endpoints, and the end-to-end toggle through
the due path (TEST-003: nothing internal mocked). The settings table is a SINGLETON
(one shared id=1 row), so every mutating test owns a full read-after-write and never
assumes a pristine table (foundation §4 independence caveat).

Numbered cases trace to the foundation: B-I1..B-I6 (repo + service), B-I7 (migration,
in test_migrations.py), B-I9..B-I14 (web API + restart), B-I16/B-I18 (due wiring).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from viridarium.adapters.outbound.db.app_settings_repository import (
    SqlAlchemyAppSettingsRepository,
)
from viridarium.adapters.outbound.db.engine import create_session_factory
from viridarium.adapters.outbound.db.models import AppSettingsModel
from viridarium.application.settings import AppSettingsService
from viridarium.domain.app_settings import SeasonalSettings
from viridarium.domain.due import WinterWindow
from viridarium.infrastructure.app import create_app
from viridarium.infrastructure.settings import Settings

pytestmark = pytest.mark.integration

_SETTINGS = "/api/v1/settings"
_DEFAULT_BODY = {
    "seasonal_aware": True,
    "winter_window": {
        "start_month": 11,
        "start_day": 1,
        "end_month": 3,
        "end_day": 1,
    },
}


@pytest.fixture
def session_factory(migrated_settings: Settings) -> Iterator[sessionmaker[Session]]:
    """A session factory over the migrated per-test SQLite DB."""
    engine = create_engine(migrated_settings.database_url)
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def _row_count(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(AppSettingsModel)) or 0


def _reset_settings(client: TestClient) -> None:
    """PUT the spec default back, for independence on the shared singleton."""
    assert client.put(_SETTINGS, json=_DEFAULT_BODY).status_code == 200


# ============================================== 4a. singleton repo + lazy default
def test_repo_get_none_when_no_row(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I1: repo get() returns None when no row (lazy default lives above the repo)."""
    repo = SqlAlchemyAppSettingsRepository(session_factory)
    assert repo.get() is None


def test_service_get_lazy_default_when_no_row(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I2: service get() returns the spec default when no row (AC1, no seeding)."""
    service = AppSettingsService(SqlAlchemyAppSettingsRepository(session_factory))
    result = service.get()
    assert result.seasonal_aware is True
    assert result.window == WinterWindow(
        start_month=11, start_day=1, end_month=3, end_day=1
    )


def test_repo_put_then_get_round_trip(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I3: put a non-default value, then get() round-trips it exactly (AC2)."""
    repo = SqlAlchemyAppSettingsRepository(session_factory)
    stored = SeasonalSettings(
        seasonal_aware=False,
        window=WinterWindow(start_month=5, start_day=1, end_month=9, end_day=1),
    )
    repo.put(stored)
    assert repo.get() == stored

    service = AppSettingsService(SqlAlchemyAppSettingsRepository(session_factory))
    assert service.get() == stored  # not the default


def test_persistence_across_fresh_repository(
    session_factory: sessionmaker[Session], migrated_settings: Settings
) -> None:
    """B-I4: a non-default value survives a fresh repo/session (restart proxy, AC2)."""
    stored = SeasonalSettings(
        seasonal_aware=False,
        window=WinterWindow(start_month=5, start_day=1, end_month=9, end_day=1),
    )
    SqlAlchemyAppSettingsRepository(session_factory).put(stored)

    # A brand-new engine/session bound to the same DB - a durable-row, not in-memory.
    fresh_engine = create_engine(migrated_settings.database_url)
    try:
        fresh_repo = SqlAlchemyAppSettingsRepository(
            create_session_factory(fresh_engine)
        )
        assert fresh_repo.get() == stored
    finally:
        fresh_engine.dispose()


def test_portable_upsert_updates_same_row_never_inserts_second(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I5: put twice -> exactly ONE row; 2nd put UPDATEs id=1 (CRITICAL, AC2)."""
    repo = SqlAlchemyAppSettingsRepository(session_factory)
    a = SeasonalSettings(
        seasonal_aware=False,
        window=WinterWindow(start_month=5, start_day=1, end_month=9, end_day=1),
    )
    b = SeasonalSettings(
        seasonal_aware=True,
        window=WinterWindow(start_month=10, start_day=15, end_month=4, end_day=15),
    )
    repo.put(a)
    repo.put(b)

    assert _row_count(session_factory) == 1  # the singleton invariant
    assert repo.get() == b  # the last write wins


def test_upsert_first_put_inserts_then_get(
    session_factory: sessionmaker[Session],
) -> None:
    """B-I6: the happy upsert path on the local engine (first put inserts id=1)."""
    repo = SqlAlchemyAppSettingsRepository(session_factory)
    assert _row_count(session_factory) == 0
    value = SeasonalSettings(
        seasonal_aware=True,
        window=WinterWindow(start_month=11, start_day=1, end_month=3, end_day=1),
    )
    repo.put(value)
    assert _row_count(session_factory) == 1
    assert repo.get() == value


# ===================================================== 4c-i. GET lazy-default shape
def test_get_fresh_install_lazy_default(client: TestClient) -> None:
    """B-I9: GET on a fresh install returns the lazy default + exact shape (AC1)."""
    response = client.get(_SETTINGS)
    assert response.status_code == 200
    body = response.json()
    assert body == _DEFAULT_BODY
    assert set(body) == {"seasonal_aware", "winter_window"}
    assert set(body["winter_window"]) == {
        "start_month",
        "start_day",
        "end_month",
        "end_day",
    }


# ===================================================== 4c-ii. PUT round-trip echo
def test_put_persists_and_echoes_then_get(client: TestClient) -> None:
    """B-I10: PUT echoes the stored value; a follow-up GET returns it (AC2)."""
    body = {
        "seasonal_aware": False,
        "winter_window": {
            "start_month": 5,
            "start_day": 1,
            "end_month": 9,
            "end_day": 1,
        },
    }
    put = client.put(_SETTINGS, json=body)
    assert put.status_code == 200, put.text
    assert put.json() == body
    assert client.get(_SETTINGS).json() == body


def test_put_toggle_only_keeps_window(client: TestClient) -> None:
    """B-I11: the toggle and window are independent fields."""
    body = {"seasonal_aware": False, "winter_window": _DEFAULT_BODY["winter_window"]}
    assert client.put(_SETTINGS, json=body).status_code == 200
    got = client.get(_SETTINGS).json()
    assert got["seasonal_aware"] is False
    assert got["winter_window"] == _DEFAULT_BODY["winter_window"]


def test_put_southern_hemisphere_window_persists(client: TestClient) -> None:
    """B-I12: a southern (non-wrapping) window persists and round-trips (AC4)."""
    body = {
        "seasonal_aware": True,
        "winter_window": {
            "start_month": 5,
            "start_day": 1,
            "end_month": 9,
            "end_day": 1,
        },
    }
    assert client.put(_SETTINGS, json=body).status_code == 200
    assert client.get(_SETTINGS).json()["winter_window"] == body["winter_window"]


# ===================================================== 4c-iii. validation matrix M2
def _window(start_month: int, start_day: int, end_month: int, end_day: int) -> dict:
    return {
        "start_month": start_month,
        "start_day": start_day,
        "end_month": end_month,
        "end_day": end_day,
    }


@pytest.mark.parametrize(
    ("seasonal_aware", "window", "expected"),
    [
        pytest.param(True, _window(11, 1, 3, 1), 200, id="valid-default"),
        pytest.param(True, _window(2, 29, 3, 1), 200, id="valid-feb-29"),
        pytest.param(True, _window(0, 1, 3, 1), 422, id="start-month-0"),
        pytest.param(True, _window(13, 1, 3, 1), 422, id="start-month-13"),
        pytest.param(True, _window(11, 1, 13, 1), 422, id="end-month-13"),
        pytest.param(True, _window(11, 0, 3, 1), 422, id="start-day-0"),
        pytest.param(True, _window(11, 32, 3, 1), 422, id="start-day-32"),
        pytest.param(True, _window(2, 30, 3, 1), 422, id="feb-30"),
        pytest.param(True, _window(4, 31, 3, 1), 422, id="apr-31"),
        pytest.param(True, _window(11, 1, 9, 31), 422, id="sep-31"),
        pytest.param(True, _window(11, 1, 2, 30), 422, id="feb-30-end"),
        pytest.param("yes", _window(11, 1, 3, 1), 422, id="seasonal-not-bool"),
    ],
)
def test_settings_validation_matrix(
    client: TestClient,
    seasonal_aware: object,
    window: dict,
    expected: int,
) -> None:
    """B-I13: the month/day validation matrix; 422 bodies detail-only, no PII (AC5)."""
    response = client.put(
        _SETTINGS, json={"seasonal_aware": seasonal_aware, "winter_window": window}
    )
    assert response.status_code == expected, response.text
    if expected == 200:
        _reset_settings(client)
    else:
        # 422 body is the Pydantic detail envelope only - no free-text / PII.
        assert set(response.json()) == {"detail"}


@pytest.mark.parametrize(
    "extra_field",
    [
        pytest.param({"id": 999}, id="inject-id"),
        pytest.param({"updated_at": "2020-01-01T00:00:00"}, id="inject-updated-at"),
        pytest.param({"unexpected": True}, id="inject-unknown"),
    ],
)
def test_put_rejects_injected_extra_fields(
    client: TestClient, extra_field: dict
) -> None:
    """Mass-assignment guard: extra='forbid' rejects client-set server fields (422)."""
    response = client.put(_SETTINGS, json={**_DEFAULT_BODY, **extra_field})
    assert response.status_code == 422, response.text
    assert set(response.json()) == {"detail"}


# ===================================================== 4c-iv. API restart persistence
def test_put_then_get_on_fresh_app_instance(
    client: TestClient, migrated_settings: Settings
) -> None:
    """B-I14: PUT a value, then GET on a 2nd app over the same DB returns it (AC2)."""
    body = {
        "seasonal_aware": False,
        "winter_window": {
            "start_month": 5,
            "start_day": 1,
            "end_month": 9,
            "end_day": 1,
        },
    }
    assert client.put(_SETTINGS, json=body).status_code == 200

    fresh_app = create_app(settings=migrated_settings)
    with TestClient(fresh_app) as fresh_client:
        assert fresh_client.get(_SETTINGS).json() == body


# ===================================================== 4e. toggle drives compute_due
def test_toggle_flips_paused_in_window_schedule(
    client: TestClient, migrated_settings: Settings
) -> None:
    """B-I18: the persisted toggle drives compute_due both directions (CRITICAL, AC3).

    A paused schedule + a recent event, today forced inside the window: toggle OFF ->
    next_due is non-null (due normally); toggle ON -> next_due is JSON null again. The
    full path PUT settings -> persisted row -> provider -> service -> compute_due.
    """
    from datetime import date

    plants = "/api/v1/plants"
    plant_id = client.post(plants, json={"name": "Cactus"}).json()["id"]
    assert (
        client.put(
            f"{plants}/{plant_id}/schedules/water",
            json={"interval_days": 7, "dormancy": "paused"},
        ).status_code
        == 200
    )
    client.post(
        f"{plants}/{plant_id}/events",
        json={"type": "water", "happened_on": date.today().isoformat()},
    )

    # Force today inside the window deterministically (an injected port, not a mock).
    full_year = WinterWindow(start_month=1, start_day=1, end_month=12, end_day=31)
    container = client.app.state.container  # type: ignore[attr-defined]

    class _StaticProvider:
        def __init__(self) -> None:
            self._service = container.app_settings_service

        def current(self) -> SeasonalSettings:
            stored = self._service.get()
            return SeasonalSettings(
                seasonal_aware=stored.seasonal_aware, window=full_year
            )

    from viridarium.application.due import DueQueryService

    client.app.state.due_query_service = DueQueryService(  # type: ignore[attr-defined]
        schedule_repository=container.due_query_service.schedule_repository,
        event_repository=container.due_query_service.event_repository,
        settings_provider=_StaticProvider(),
        today_provider=date.today,
    )

    # toggle OFF -> due normally (non-null)
    off = client.put(_SETTINGS, json={**_DEFAULT_BODY, "seasonal_aware": False})
    assert off.status_code == 200
    water_off = next(
        s
        for s in client.get(f"{plants}/{plant_id}").json()["schedules"]
        if s["care_type"] == "water"
    )
    assert water_off["next_due"] is not None

    # toggle ON -> paused-in-window null again
    on = client.put(_SETTINGS, json={**_DEFAULT_BODY, "seasonal_aware": True})
    assert on.status_code == 200
    water_on = next(
        s
        for s in client.get(f"{plants}/{plant_id}").json()["schedules"]
        if s["care_type"] == "water"
    )
    assert water_on["next_due"] is None
    assert water_on["overdue_days"] is None


def _count_due_assembly_statements(client: TestClient, active_ids: list[int]) -> int:
    """Count statements the due assembly issues over a page of plant ids (B-I17)."""
    from sqlalchemy import event

    engine = client.app.state.container.engine  # type: ignore[attr-defined]
    due = client.app.state.due_query_service  # type: ignore[attr-defined]
    counter = [0]

    def _on_execute(*_args: object, **_kwargs: object) -> None:
        counter[0] += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        due.for_plants(active_ids)
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)
    return counter[0]


def test_due_statement_count_bounded_with_settings(client: TestClient) -> None:
    """B-I17: the settings read adds NO per-plant query; count stays flat across N/2N.

    Seeds a persisted settings row, then N then 2N plants with water+feed schedules +
    events; the due-assembly statement count is constant (the US-3.3 bound plus at most
    one settings select), proving the settings wiring did not regress the N+1 bound.
    """
    from datetime import date

    _reset_settings(client)  # ensure a persisted row exists (not the lazy default)
    plants = "/api/v1/plants"

    def _seed(n: int) -> list[int]:
        ids: list[int] = []
        for i in range(n):
            pid = client.post(plants, json={"name": f"P{len(ids)}-{i}"}).json()["id"]
            for care in ("water", "feed"):
                client.put(
                    f"{plants}/{pid}/schedules/{care}", json={"interval_days": 7}
                )
                client.post(
                    f"{plants}/{pid}/events",
                    json={"type": care, "happened_on": date.today().isoformat()},
                )
            ids.append(pid)
        return ids

    n_ids = _seed(5)
    count_n = _count_due_assembly_statements(client, n_ids)

    two_n_ids = n_ids + _seed(5)
    count_2n = _count_due_assembly_statements(client, two_n_ids)

    assert count_n == count_2n  # constant: no per-plant query, settings read once
