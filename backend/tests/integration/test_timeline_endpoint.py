"""Integration tests for GET /api/v1/plants/{id}/timeline (TEST-001 primary).

Real-DB slice through router -> TimelineQueryService -> CareEventRepository +
PhotoRepository -> SQLAlchemy -> SQLite (TEST-003: nothing internal mocked). Covers the
merge order incl. backdated-by-``happened_on`` (B-I1/B-I2), the standalone-photo
interleave (B-I3, residual assumption CONFIRMED = interleave), the same-day
``created_at`` tiebreak (B-I4), empty history (B-I5), the dedup invariant
(B-I6/B-I7/B-I8), the all-four-types + field pass-through (B-I9/B-I10), the
missing-plant 404 + no-PII guard-first (B-I11/B-I12), the bounded count (B-I13), the
discriminated-union key-set contract (B-I14/B-I15), and the additive OpenAPI shape
(B-I16). Each test seeds its own plant/event/photo via the real API (TEST-006). Case ids
(B-In) cite the test-foundation §4.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from tests.integration.test_photos_endpoint import JPEG_BYTES

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"

_EVENT_KEYS = {"kind", "date", "event_type", "note", "health", "photo"}
_PHOTO_ENTRY_KEYS = {"kind", "date", "photo"}
_NESTED_PHOTO_KEYS = {"id", "url"}


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _upload_photo(client: TestClient, plant_id: int) -> int:
    response = client.post(
        f"{_PLANTS}/{plant_id}/photos",
        files={"file": ("x.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 201, response.text
    photo_id: int = response.json()["id"]
    return photo_id


def _log_event(
    client: TestClient,
    plant_id: int,
    event_type: str = "water",
    happened_on: date | None = None,
    note: str | None = None,
    health: str | None = None,
    photo_id: int | None = None,
) -> int:
    body: dict[str, object] = {"type": event_type}
    if happened_on is not None:
        body["happened_on"] = happened_on.isoformat()
    if note is not None:
        body["note"] = note
    if health is not None:
        body["health"] = health
    if photo_id is not None:
        body["photo_id"] = photo_id
    response = client.post(f"{_PLANTS}/{plant_id}/events", json=body)
    assert response.status_code == 201, response.text
    event_id: int = response.json()["id"]
    return event_id


def _timeline(client: TestClient, plant_id: int) -> tuple[int, object]:
    response = client.get(f"{_PLANTS}/{plant_id}/timeline")
    return response.status_code, response.json()


# ====================================================== 4a. merge order + sort (AC1)
def test_newest_first_merge_of_events_and_photos(client: TestClient) -> None:  # B-I1
    """Events on D1<D2 + a standalone photo dated D3 -> [photo, event, event] desc."""
    plant_id = _make_plant(client)
    d1 = date.today() - timedelta(days=4)
    d2 = date.today() - timedelta(days=2)
    _log_event(client, plant_id, "water", happened_on=d1)
    _log_event(client, plant_id, "feed", happened_on=d2)
    # The standalone photo's date is its created_at (today), the newest of the three.
    _upload_photo(client, plant_id)

    status_code, body = _timeline(client, plant_id)

    assert status_code == 200
    assert isinstance(body, list)
    kinds = [entry["kind"] for entry in body]
    dates = [entry["date"] for entry in body]
    assert kinds == ["photo", "event", "event"]
    assert dates == [date.today().isoformat(), d2.isoformat(), d1.isoformat()]


def test_backdated_event_sorts_by_happened_on(client: TestClient) -> None:  # B-I2
    """CRITICAL: a backdated event sorts to its ``happened_on`` slot, not the top.

    A is logged first with the LATER ``happened_on`` (D2); B is logged second (so B's
    ``created_at`` is later) with the EARLIER ``happened_on`` (D1). A naive created_at
    sort would put B first; sorting on ``happened_on`` puts A (D2) before B (D1).
    """
    plant_id = _make_plant(client)
    d1 = date.today() - timedelta(days=7)
    d2 = date.today() - timedelta(days=2)
    _log_event(client, plant_id, "water", happened_on=d2, note="A")
    _log_event(client, plant_id, "feed", happened_on=d1, note="B")

    _, body = _timeline(client, plant_id)

    assert [entry["date"] for entry in body] == [d2.isoformat(), d1.isoformat()]
    assert [entry["note"] for entry in body] == ["A", "B"]


def test_standalone_photo_emits_as_kind_photo(client: TestClient) -> None:  # B-I3
    """Residual default (CONFIRMED = interleave): a standalone photo is a kind:photo.

    A photo with no event referencing it appears as a ``kind:photo`` entry dated at its
    ``created_at.date()``.
    """
    plant_id = _make_plant(client)
    _log_event(client, plant_id, "water", happened_on=date.today() - timedelta(days=1))
    photo_id = _upload_photo(client, plant_id)

    _, body = _timeline(client, plant_id)

    photo_entries = [entry for entry in body if entry["kind"] == "photo"]
    assert len(photo_entries) == 1
    entry = photo_entries[0]
    assert entry["date"] == date.today().isoformat()
    assert entry["photo"]["id"] == photo_id
    assert entry["photo"]["url"] == f"/api/v1/plants/{plant_id}/photos/{photo_id}"


def test_same_day_items_have_stable_deterministic_order(  # B-I4
    client: TestClient,
) -> None:
    """Same-date items return a STABLE, deterministic order across repeated calls.

    Integration ``created_at`` is second-granular, so two items created in the same
    second cannot be separated by the desc ``created_at`` tiebreak; their order falls
    back to the merge's emission order (events before photos) and must be stable (no
    flapping). The tiebreak KEY itself (sub-second ``created_at`` desc) is pinned at the
    unit layer with exact datetimes (B-U5), where granularity is controllable; this
    integration case only guarantees determinism.
    """
    plant_id = _make_plant(client)
    _log_event(client, plant_id, "observe", happened_on=date.today())
    _upload_photo(client, plant_id)

    _, first = _timeline(client, plant_id)
    _, second = _timeline(client, plant_id)

    assert first == second  # deterministic, no flapping across calls
    assert [entry["kind"] for entry in first] == ["event", "photo"]  # stable emission


def test_empty_history_returns_empty_list(client: TestClient) -> None:  # B-I5
    """A freshly-created plant with no events and no photos -> 200, exactly []."""
    plant_id = _make_plant(client)

    status_code, body = _timeline(client, plant_id)

    assert status_code == 200
    assert body == []


# ====================================================== 4b. dedup invariant (AC2)
def test_linked_photo_emits_one_event_entry_inline(client: TestClient) -> None:  # B-I6
    """CRITICAL: an event's linked photo is inline once, NEVER a kind:photo entry."""
    plant_id = _make_plant(client)
    photo_id = _upload_photo(client, plant_id)
    _log_event(client, plant_id, "observe", health="good", photo_id=photo_id)

    _, body = _timeline(client, plant_id)

    assert len(body) == 1  # the single event, not two entries
    entry = body[0]
    assert entry["kind"] == "event"
    assert entry["photo"] == {
        "id": photo_id,
        "url": f"/api/v1/plants/{plant_id}/photos/{photo_id}",
    }
    assert not any(e["kind"] == "photo" and e["photo"]["id"] == photo_id for e in body)


def test_linked_plus_standalone_photo_mix(client: TestClient) -> None:  # B-I7
    """A linked photo P (inline) + a standalone photo Q (kind:photo); never crossed."""
    plant_id = _make_plant(client)
    p = _upload_photo(client, plant_id)
    _log_event(client, plant_id, "observe", health="fair", photo_id=p)
    q = _upload_photo(client, plant_id)

    _, body = _timeline(client, plant_id)

    event_entries = [e for e in body if e["kind"] == "event"]
    photo_entries = [e for e in body if e["kind"] == "photo"]
    assert len(event_entries) == 1
    assert event_entries[0]["photo"]["id"] == p
    assert [e["photo"]["id"] for e in photo_entries] == [q]
    # P never a kind:photo; Q never inline on an event.
    assert all(e["photo"]["id"] != p for e in photo_entries)


def test_two_events_share_one_photo_id(client: TestClient) -> None:  # B-I8
    """Edge: two events referencing the SAME photo id -> P still never a kind:photo.

    P renders inline on each referencing event; its id is in ``linked`` so it is never
    emitted as a standalone ``kind:photo`` entry (the ``linked``-is-a-set semantics).
    """
    plant_id = _make_plant(client)
    photo_id = _upload_photo(client, plant_id)
    _log_event(client, plant_id, "observe", photo_id=photo_id)
    _log_event(client, plant_id, "observe", photo_id=photo_id)

    _, body = _timeline(client, plant_id)

    event_entries = [e for e in body if e["kind"] == "event"]
    assert len(event_entries) == 2
    assert all(e["photo"]["id"] == photo_id for e in event_entries)
    assert not any(e["kind"] == "photo" for e in body)


# ====================================================== 4c. event-type pass-through
def test_all_four_event_types_carry_through(client: TestClient) -> None:  # B-I9
    """All four types carried; observe carries health, the others null."""
    plant_id = _make_plant(client)
    base = date.today() - timedelta(days=10)
    _log_event(client, plant_id, "water", happened_on=base, note="w")
    _log_event(client, plant_id, "feed", happened_on=base + timedelta(days=1), note="f")
    _log_event(
        client, plant_id, "repot", happened_on=base + timedelta(days=2), note="r"
    )
    _log_event(
        client,
        plant_id,
        "observe",
        happened_on=base + timedelta(days=3),
        note="o",
        health="good",
    )

    _, body = _timeline(client, plant_id)

    by_type = {e["event_type"]: e for e in body}
    assert set(by_type) == {"water", "feed", "repot", "observe"}
    assert by_type["observe"]["health"] == "good"
    assert by_type["water"]["health"] is None
    assert by_type["feed"]["health"] is None
    assert by_type["repot"]["health"] is None
    assert {e["note"] for e in body} == {"w", "f", "r", "o"}


def test_event_without_photo_has_null_photo(client: TestClient) -> None:  # B-I10
    """An event with a note but no photo -> ``photo`` is JSON null (present, null)."""
    plant_id = _make_plant(client)
    _log_event(client, plant_id, "water", note="dry soil")

    _, body = _timeline(client, plant_id)

    assert body[0]["photo"] is None
    assert "photo" in body[0]  # the slot is present, not absent


# ====================================================== 4d. missing plant + privacy
def test_unknown_plant_returns_404_plant_reason_no_pii(  # B-I11
    client: TestClient,
) -> None:
    """CRITICAL: an unknown plant -> 404, {"detail"}-only, plant-reason, no PII."""
    response = client.get(f"{_PLANTS}/999999/timeline")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"detail"}
    assert "999999" in body["detail"]  # the integer id, the only datum
    assert "plant" in body["detail"].lower()


def test_guard_fires_first_no_sibling_data_leak(client: TestClient) -> None:  # B-I12
    """The plant-exists guard fires before any merge: a missing id leaks no feed."""
    plant_a = _make_plant(client, "A")
    _log_event(client, plant_a, "water")
    missing_id = plant_a + 100000

    response = client.get(f"{_PLANTS}/{missing_id}/timeline")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


# ====================================================== 4e. bounded count + contract
def _count_timeline_statements(client: TestClient, plant_id: int) -> int:
    """Count the statements the timeline query service issues for one plant.

    Exercises the router's wired TimelineQueryService over the real engine (the same
    path GET .../timeline uses) and counts the merged read's statements. The foundation
    pins this constant across history size (the two list reads + the plant-exists guard,
    no per-entry query).
    """
    engine = client.app.state.container.engine  # type: ignore[attr-defined]
    service = client.app.state.timeline_query_service  # type: ignore[attr-defined]
    counter = [0]

    def _on_execute(*_args: object, **_kwargs: object) -> None:
        counter[0] += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        service.for_plant(plant_id)
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)
    return counter[0]


def test_query_count_bounded_regardless_of_history(client: TestClient) -> None:  # B-I13
    """CRITICAL (NFR): the statement count does not scale with history size.

    Seed N events + N photos, count; then add to 2N events + 2N photos, count again.
    The count is a small constant and equal across N/2N (no per-entry query).
    """
    plant_id = _make_plant(client)
    for i in range(4):
        _log_event(
            client, plant_id, "water", happened_on=date.today() - timedelta(days=i)
        )
        _upload_photo(client, plant_id)
    n_count = _count_timeline_statements(client, plant_id)

    for i in range(4, 8):
        _log_event(
            client, plant_id, "water", happened_on=date.today() - timedelta(days=i)
        )
        _upload_photo(client, plant_id)
    two_n_count = _count_timeline_statements(client, plant_id)

    assert n_count <= 4  # plant-exists guard + the two list reads (+ connection setup)
    assert two_n_count == n_count  # flat: no per-entry query


def test_event_entry_key_set_is_exact(client: TestClient) -> None:  # B-I14
    """A kind:event entry has exactly the §7 keys; the inline photo is {id,url} only."""
    plant_id = _make_plant(client)
    photo_id = _upload_photo(client, plant_id)
    _log_event(
        client, plant_id, "observe", health="good", note="leaf", photo_id=photo_id
    )

    _, body = _timeline(client, plant_id)

    entry = body[0]
    assert set(entry) == _EVENT_KEYS
    assert entry["kind"] == "event"
    assert set(entry["photo"]) == _NESTED_PHOTO_KEYS  # no stored_filename / created_at
    assert entry["photo"]["url"] == f"/api/v1/plants/{plant_id}/photos/{photo_id}"


def test_photo_entry_key_set_is_exact(client: TestClient) -> None:  # B-I15
    """A kind:photo entry has exactly {kind,date,photo}; nested photo is {id,url}."""
    plant_id = _make_plant(client)
    _upload_photo(client, plant_id)

    _, body = _timeline(client, plant_id)

    entry = next(e for e in body if e["kind"] == "photo")
    assert set(entry) == _PHOTO_ENTRY_KEYS
    assert set(entry["photo"]) == _NESTED_PHOTO_KEYS
    assert "event_type" not in entry
    assert "health" not in entry
    assert "note" not in entry


def test_openapi_exposes_timeline_path_additively(client: TestClient) -> None:  # B-I16
    """OpenAPI carries GET .../timeline as an array response (additive)."""
    schema = client.get("/api/v1/openapi.json").json()

    path = schema["paths"]["/api/v1/plants/{plant_id}/timeline"]
    assert "get" in path
    response_schema = path["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert response_schema.get("type") == "array"
    # The existing plant-read shape is unchanged (additive only, API-004).
    assert "/api/v1/plants/{plant_id}" in schema["paths"]
