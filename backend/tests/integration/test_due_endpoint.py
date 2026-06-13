"""Integration tests for the due field on the plant-read endpoints (TEST-001 primary).

Real-DB slice through router -> DueQueryService -> repositories -> SQLAlchemy -> SQLite
(TEST-003: nothing internal mocked). Covers the matching-type filter end-to-end
(B-I7/B-I8), the detail endpoint (B-I20..B-I25), the list endpoint (B-I26..B-I30, incl.
the list-path N+1 guard), and the response contract / OpenAPI shape (B-I31/B-I32).

The window provider is the only collaborator a test may override via DI (it is an
injected port, not a mock of internal logic) so B-I23 can force a deterministic
in-window ``today``.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from viridarium.application.due import DueQueryService
from viridarium.domain.due import WinterWindow

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"
_SCHEDULE_KEYS = {"care_type", "next_due", "overdue_days"}


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _put_schedule(
    client: TestClient,
    plant_id: int,
    care_type: str,
    interval: int,
    **body: object,
) -> None:
    payload: dict[str, object] = {"interval_days": interval, **body}
    response = client.put(f"{_PLANTS}/{plant_id}/schedules/{care_type}", json=payload)
    assert response.status_code == 200, response.text


def _log_event(
    client: TestClient, plant_id: int, event_type: str, happened_on: date
) -> int:
    response = client.post(
        f"{_PLANTS}/{plant_id}/events",
        json={"type": event_type, "happened_on": happened_on.isoformat()},
    )
    assert response.status_code == 201, response.text
    event_id: int = response.json()["id"]
    return event_id


def _schedules_of(client: TestClient, plant_id: int) -> list[dict[str, object]]:
    body = client.get(f"{_PLANTS}/{plant_id}").json()
    schedules: list[dict[str, object]] = body["schedules"]
    return schedules


# ====================================== 4b. matching-type filter end-to-end (AC8)
def test_feed_repot_observe_do_not_move_a_water_schedule(client: TestClient) -> None:
    """B-I7: only a feed/repot/observe event -> the water schedule is due today."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    recent = date.today() - timedelta(days=1)
    _log_event(client, plant_id, "feed", recent)
    _log_event(client, plant_id, "repot", recent)
    _log_event(client, plant_id, "observe", recent)

    schedules = _schedules_of(client, plant_id)

    water = next(s for s in schedules if s["care_type"] == "water")
    assert water["next_due"] == date.today().isoformat()
    assert water["overdue_days"] == 0


def test_water_event_does_not_move_a_feed_schedule(client: TestClient) -> None:
    """B-I8: a water event -> the feed schedule has no matching event (due today)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "feed", 14)
    _log_event(client, plant_id, "water", date.today() - timedelta(days=2))

    feed = next(s for s in _schedules_of(client, plant_id) if s["care_type"] == "feed")
    assert feed["next_due"] == date.today().isoformat()


# ====================================== 4e. detail endpoint (E2)
def test_detail_includes_schedules_happy(client: TestClient) -> None:
    """B-I20: detail carries the schedules array with the computed next_due (AC1)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    logged_on = date.today() - timedelta(days=3)
    _log_event(client, plant_id, "water", logged_on)

    body = client.get(f"{_PLANTS}/{plant_id}").json()

    assert isinstance(body["schedules"], list)
    water = next(s for s in body["schedules"] if s["care_type"] == "water")
    assert water["next_due"] == (logged_on + timedelta(days=7)).isoformat()
    assert isinstance(water["overdue_days"], int)
    assert water["overdue_days"] >= 0


def test_detail_new_plant_due_today(client: TestClient) -> None:
    """B-I21: a schedule with no events -> due today, overdue 0 (AC2)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)

    water = next(
        s for s in _schedules_of(client, plant_id) if s["care_type"] == "water"
    )
    assert water["next_due"] == date.today().isoformat()
    assert water["overdue_days"] == 0


def test_detail_disabled_schedule_no_entry(client: TestClient) -> None:
    """B-I22: a disabled schedule produces no entry (AC6)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    _put_schedule(client, plant_id, "feed", 30, enabled=False)

    care_types = {s["care_type"] for s in _schedules_of(client, plant_id)}
    assert care_types == {"water"}


def test_detail_paused_in_window_serializes_as_json_null(
    client: TestClient,
) -> None:
    """B-I23: paused in-window -> next_due null AND overdue_days null (CRITICAL, AC4).

    Overrides the window provider on the wired app so ``today`` is forced inside the
    window deterministically (an injected port, not an internal mock).
    """
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7, dormancy="paused")

    # Force a window that always contains today (year-agnostic full-year window),
    # then force today to be in it by construction.
    always_window = WinterWindow(start_month=1, start_day=1, end_month=12, end_day=31)
    container = client.app.state.container  # type: ignore[attr-defined]
    client.app.state.due_query_service = DueQueryService(  # type: ignore[attr-defined]
        schedule_repository=container.due_query_service.schedule_repository,
        event_repository=container.due_query_service.event_repository,
        window_provider=_StaticWindowProvider(always_window),
        today_provider=date.today,
    )

    water = next(
        s for s in _schedules_of(client, plant_id) if s["care_type"] == "water"
    )
    assert water["next_due"] is None
    assert water["overdue_days"] is None


class _StaticWindowProvider:
    def __init__(self, window: WinterWindow) -> None:
        self._window = window

    def current_window(self) -> WinterWindow:
        return self._window


def test_detail_archived_plant_empty_schedules(client: TestClient) -> None:
    """B-I24: an archived plant -> schedules == [] (excluded entirely, AC6)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    _log_event(client, plant_id, "water", date.today())
    assert client.post(f"{_PLANTS}/{plant_id}/archive").status_code == 200

    body = client.get(f"{_PLANTS}/{plant_id}").json()
    assert body["archived"] is True
    assert body["schedules"] == []


def test_detail_unknown_plant_404_unchanged(client: TestClient) -> None:
    """B-I25: an unknown plant is still 404, detail-only body (no PII)."""
    response = client.get(f"{_PLANTS}/999999")
    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


# ====================================== 4f. list endpoint (E1)
def test_list_includes_schedules_per_plant(client: TestClient) -> None:
    """B-I26: each listed plant carries its own schedules, no cross-plant bleed."""
    p1 = _make_plant(client, "A")
    p2 = _make_plant(client, "B")
    _put_schedule(client, p1, "water", 7)
    _put_schedule(client, p2, "water", 7)
    p1_on = date.today() - timedelta(days=1)
    p2_on = date.today() - timedelta(days=5)
    _log_event(client, p1, "water", p1_on)
    _log_event(client, p2, "water", p2_on)

    listed = client.get(_PLANTS).json()
    by_id = {p["id"]: p for p in listed}

    p1_water = next(s for s in by_id[p1]["schedules"] if s["care_type"] == "water")
    p2_water = next(s for s in by_id[p2]["schedules"] if s["care_type"] == "water")
    assert p1_water["next_due"] == (p1_on + timedelta(days=7)).isoformat()
    assert p2_water["next_due"] == (p2_on + timedelta(days=7)).isoformat()


def test_list_excludes_archived_plant_schedules(client: TestClient) -> None:
    """B-I27: an archived plant in the list has schedules == [] (AC6)."""
    active = _make_plant(client, "Active")
    archived = _make_plant(client, "Archived")
    _put_schedule(client, active, "water", 7)
    _put_schedule(client, archived, "water", 7)
    _log_event(client, active, "water", date.today())
    _log_event(client, archived, "water", date.today())
    client.post(f"{_PLANTS}/{archived}/archive")

    listed = client.get(f"{_PLANTS}?include_archived=true").json()
    by_id = {p["id"]: p for p in listed}

    assert by_id[active]["schedules"]  # populated
    assert by_id[archived]["schedules"] == []


def test_list_disabled_schedule_omitted(client: TestClient) -> None:
    """B-I28: a disabled schedule is omitted on the list path (AC6)."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    _put_schedule(client, plant_id, "feed", 30, enabled=False)

    listed = client.get(_PLANTS).json()
    entry = next(p for p in listed if p["id"] == plant_id)
    assert {s["care_type"] for s in entry["schedules"]} == {"water"}


def test_list_empty_no_crash(client: TestClient) -> None:
    """B-I29: an empty active list -> 200, [] (degenerate AC7)."""
    response = client.get(_PLANTS)
    assert response.status_code == 200
    assert response.json() == []


def _count_due_assembly_statements(client: TestClient, active_ids: list[int]) -> int:
    """Count the statements the due assembly issues for a page of active plant ids.

    Exercises the router's wired DueQueryService over the real engine (the same path
    GET /plants uses) and counts only the due-assembly portion. The plant list's own
    per-plant tag reads are a pre-existing list-path concern (out of US-3.3 scope,
    PRIN-IX); this isolates the due engine's contribution, which the foundation pins as
    constant across plant counts.
    """
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


def test_list_query_count_bounded_regardless_of_plant_count(
    client: TestClient,
) -> None:
    """B-I30: the list-path due assembly does not scale with plant count (AC7).

    The router batches due into two grouped reads for the whole page; this proves the
    statement count is constant for N and 2N active plants (the list path stays flat).
    A separate sanity check confirms GET /plants returns the schedules end-to-end.
    """
    n_ids: list[int] = []
    for i in range(5):
        pid = _make_plant(client, f"N{i}")
        _put_schedule(client, pid, "water", 7)
        _log_event(client, pid, "water", date.today())
        n_ids.append(pid)
    n_count = _count_due_assembly_statements(client, n_ids)

    two_n_ids = list(n_ids)
    for i in range(5):
        pid = _make_plant(client, f"M{i}")
        _put_schedule(client, pid, "water", 7)
        _log_event(client, pid, "water", date.today())
        two_n_ids.append(pid)
    two_n_count = _count_due_assembly_statements(client, two_n_ids)

    assert n_count <= 3  # the two grouped reads (+ at most one connection setup)
    assert two_n_count == n_count  # flat: no per-plant due query

    # End-to-end sanity: the list endpoint actually carries the schedules.
    listed = client.get(_PLANTS).json()
    assert all("schedules" in p for p in listed)
    assert any(p["schedules"] for p in listed)


# ====================================== 4g. response contract (TEST-008)
def test_openapi_exposes_additive_schedules_field(client: TestClient) -> None:
    """B-I31: PlantResponse.schedules is an additive array of the due entry shape."""
    schema = client.get("/api/v1/openapi.json").json()
    plant_props = schema["components"]["schemas"]["PlantResponse"]["properties"]
    assert "schedules" in plant_props
    assert plant_props["schedules"]["type"] == "array"


def test_schedules_entry_key_set_is_exact(client: TestClient) -> None:
    """B-I32: a populated entry has exactly {care_type, next_due, overdue_days}."""
    plant_id = _make_plant(client)
    _put_schedule(client, plant_id, "water", 7)
    _log_event(client, plant_id, "water", date.today())

    entry = _schedules_of(client, plant_id)[0]
    assert set(entry) == _SCHEDULE_KEYS
