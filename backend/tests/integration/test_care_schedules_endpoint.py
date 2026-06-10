"""Integration tests for the /api/v1/plants/{id}/schedules surface (TEST-001 primary).

A real-DB slice through router -> CareScheduleService ->
SqlAlchemyCareScheduleRepository -> SQLAlchemy -> SQLite (TEST-003: nothing internal
mocked). This is the primary layer: the ``(plant, care_type)``
uniqueness/idempotent-replace headline (AC1/AC2), the list ordering, the dormancy
default+override matrix (AC4), the allow-null winter-interval case (AC5), the
``enabled`` default, all 404/422 rejects with the no-PII discipline (AC6), and the
OpenAPI shape (AC10) are all proven end-to-end. Each test seeds its own plant via the
API (TEST-006).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"

_EXPECTED_RESPONSE_KEYS = {
    "plant_id",
    "care_type",
    "interval_days",
    "winter_interval_days",
    "dormancy",
    "enabled",
    "created_at",
    "updated_at",
}  # note: NO "id" (ARCH-007, AC10)


def _make_plant(client: TestClient, name: str = "Fern") -> int:
    plant_id: int = client.post(_PLANTS, json={"name": name}).json()["id"]
    return plant_id


def _schedules_url(plant_id: int) -> str:
    return f"{_PLANTS}/{plant_id}/schedules"


# ----------------------------------------------------------- HEADLINE: uniqueness (AC2)
def test_put_water_twice_replaces_never_adds_a_second_row(client: TestClient) -> None:
    """The story headline: a second PUT replaces, never adds a second row (AC1/AC2)."""
    plant_id = _make_plant(client)

    first = client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})
    second = client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 14})
    assert first.status_code == 200
    assert second.status_code == 200

    listed = client.get(_schedules_url(plant_id)).json()
    assert len(listed) == 1  # exactly one water row
    assert listed[0]["interval_days"] == 14  # the second value won


# --------------------------------------------------------------- PUT / GET happy (AC1)
def test_put_water_creates_and_returns_body(client: TestClient) -> None:
    plant_id = _make_plant(client)

    response = client.put(
        f"{_schedules_url(plant_id)}/water", json={"interval_days": 7}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == _EXPECTED_RESPONSE_KEYS  # no "id"
    assert body["plant_id"] == plant_id
    assert body["care_type"] == "water"
    assert body["interval_days"] == 7
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_put_feed_creates_second_schedule(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})

    response = client.put(
        f"{_schedules_url(plant_id)}/feed", json={"interval_days": 30}
    )

    assert response.status_code == 200
    assert len(client.get(_schedules_url(plant_id)).json()) == 2


def test_get_list_empty_when_none(client: TestClient) -> None:
    plant_id = _make_plant(client)

    response = client.get(_schedules_url(plant_id))

    assert response.status_code == 200
    assert response.json() == []


def test_get_list_orders_water_then_feed(client: TestClient) -> None:
    plant_id = _make_plant(client)
    # Insert feed first, then water: ordering must not follow insert order.
    client.put(f"{_schedules_url(plant_id)}/feed", json={"interval_days": 30})
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})

    listed = client.get(_schedules_url(plant_id)).json()

    assert [s["care_type"] for s in listed] == ["water", "feed"]


def test_get_single_returns_one(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})

    response = client.get(f"{_schedules_url(plant_id)}/water")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)  # a single object, not a list
    assert set(body.keys()) == _EXPECTED_RESPONSE_KEYS


def test_put_replace_updates_value(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 21})

    body = client.get(f"{_schedules_url(plant_id)}/water").json()

    assert body["interval_days"] == 21
    assert body["updated_at"] >= body["created_at"]


def test_enabled_defaults_true(client: TestClient) -> None:
    plant_id = _make_plant(client)

    body = client.put(
        f"{_schedules_url(plant_id)}/water", json={"interval_days": 7}
    ).json()

    assert body["enabled"] is True


def test_enabled_explicit_false_persists(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(
        f"{_schedules_url(plant_id)}/water",
        json={"interval_days": 7, "enabled": False},
    )

    body = client.get(f"{_schedules_url(plant_id)}/water").json()

    assert body["enabled"] is False


# ------------------------------------------------------------------------ DELETE (AC6)
def test_delete_then_get_404(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})

    deleted = client.delete(f"{_schedules_url(plant_id)}/water")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"{_schedules_url(plant_id)}/water").status_code == 404


def test_delete_leaves_sibling(client: TestClient) -> None:
    plant_id = _make_plant(client)
    client.put(f"{_schedules_url(plant_id)}/water", json={"interval_days": 7})
    client.put(f"{_schedules_url(plant_id)}/feed", json={"interval_days": 30})

    assert client.delete(f"{_schedules_url(plant_id)}/water").status_code == 204

    listed = client.get(_schedules_url(plant_id)).json()
    assert [s["care_type"] for s in listed] == ["feed"]


# ----------------------------------------------------- dormancy default+override (AC4)
@pytest.mark.parametrize(
    ("care_type", "dormancy_in", "expected"),
    [
        pytest.param("feed", None, "paused", id="omitted-feed"),
        pytest.param("water", None, "winter_interval", id="omitted-water"),
        pytest.param(
            "feed", "winter_interval", "winter_interval", id="explicit-feed-winter"
        ),
        pytest.param("water", "paused", "paused", id="explicit-water-paused"),
        pytest.param("feed", "paused", "paused", id="explicit-feed-paused"),
        pytest.param(
            "water", "winter_interval", "winter_interval", id="explicit-water-winter"
        ),
    ],
)
def test_dormancy_default_and_override_matrix(
    client: TestClient, care_type: str, dormancy_in: str | None, expected: str
) -> None:
    """Body dormancy wins; otherwise the care-type default (feed->paused,
    water->winter_interval). Asserted on the *stored* value via a follow-up GET."""
    plant_id = _make_plant(client)
    body: dict[str, object] = {"interval_days": 7}
    if dormancy_in is not None:
        body["dormancy"] = dormancy_in

    client.put(f"{_schedules_url(plant_id)}/{care_type}", json=body)

    stored = client.get(f"{_schedules_url(plant_id)}/{care_type}").json()
    assert stored["dormancy"] == expected


# ----------------------------------------------- allow-null-winter-interval (AC5, Q2)
def test_winter_interval_dormancy_with_null_days_is_accepted(
    client: TestClient,
) -> None:
    plant_id = _make_plant(client)

    response = client.put(
        f"{_schedules_url(plant_id)}/water",
        json={
            "interval_days": 7,
            "dormancy": "winter_interval",
            "winter_interval_days": None,
        },
    )

    assert response.status_code == 200  # NOT 422; no cross-field validation
    body = response.json()
    assert body["winter_interval_days"] is None
    assert body["dormancy"] == "winter_interval"


def test_winter_interval_dormancy_with_days_persists(client: TestClient) -> None:
    plant_id = _make_plant(client)

    body = client.put(
        f"{_schedules_url(plant_id)}/water",
        json={
            "interval_days": 7,
            "dormancy": "winter_interval",
            "winter_interval_days": 21,
        },
    ).json()

    assert body["winter_interval_days"] == 21


# ----------------------------------------------------------- validation / 422 (AC3)
def test_put_bad_care_type_path_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)

    response = client.put(
        f"{_schedules_url(plant_id)}/banana", json={"interval_days": 7}
    )

    assert response.status_code == 422
    assert set(response.json().keys()) == {"detail"}


def test_get_bad_care_type_path_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    assert client.get(f"{_schedules_url(plant_id)}/banana").status_code == 422


def test_delete_bad_care_type_path_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    assert client.delete(f"{_schedules_url(plant_id)}/banana").status_code == 422


def test_interval_days_zero_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water", json={"interval_days": 0}
    )
    assert response.status_code == 422


def test_interval_days_negative_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water", json={"interval_days": -1}
    )
    assert response.status_code == 422


def test_interval_days_over_max_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water", json={"interval_days": 3651}
    )
    assert response.status_code == 422


def test_winter_interval_days_out_of_range_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water",
        json={"interval_days": 7, "winter_interval_days": 3651},
    )
    assert response.status_code == 422


def test_bad_dormancy_value_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water",
        json={"interval_days": 7, "dormancy": "hibernate"},
    )
    assert response.status_code == 422


def test_care_type_in_body_returns_422(client: TestClient) -> None:
    plant_id = _make_plant(client)
    response = client.put(
        f"{_schedules_url(plant_id)}/water",
        json={"interval_days": 7, "care_type": "feed"},
    )
    assert response.status_code == 422  # extra="forbid"; care_type is path-only


# --------------------------------------------------- 404 inventory + no-PII (AC6 CRIT)
def test_put_unknown_plant_returns_404(client: TestClient) -> None:
    response = client.put(
        f"{_PLANTS}/999999/schedules/water", json={"interval_days": 7}
    )
    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


def test_get_list_unknown_plant_returns_404(client: TestClient) -> None:
    response = client.get(f"{_PLANTS}/999999/schedules")
    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


def test_get_single_unknown_plant_returns_404(client: TestClient) -> None:
    response = client.get(f"{_PLANTS}/999999/schedules/water")
    assert response.status_code == 404


def test_delete_unknown_plant_returns_404(client: TestClient) -> None:
    response = client.delete(f"{_PLANTS}/999999/schedules/water")
    assert response.status_code == 404


def test_get_unknown_schedule_returns_404_no_pii(client: TestClient) -> None:
    plant_id = _make_plant(client, name="Secret Orchid")

    response = client.get(f"{_schedules_url(plant_id)}/feed")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}
    assert "Secret Orchid" not in response.text  # plant name must not leak (SEC-007)


def test_delete_unknown_schedule_returns_404_no_pii(client: TestClient) -> None:
    plant_id = _make_plant(client, name="Secret Orchid")

    response = client.delete(f"{_schedules_url(plant_id)}/water")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}
    assert "Secret Orchid" not in response.text


# -------------------------------------------------------------------- OpenAPI (AC10)
def test_openapi_exposes_schedule_paths_and_schema_omits_id(
    client: TestClient,
) -> None:
    spec = client.get("/api/v1/openapi.json").json()

    paths = spec["paths"]
    list_path = "/api/v1/plants/{plant_id}/schedules"
    keyed_path = "/api/v1/plants/{plant_id}/schedules/{care_type}"
    assert list_path in paths
    assert keyed_path in paths
    assert {"get"} <= set(paths[list_path].keys())
    assert {"get", "put", "delete"} <= set(paths[keyed_path].keys())

    props = spec["components"]["schemas"]["CareScheduleResponse"]["properties"]
    assert set(props.keys()) == _EXPECTED_RESPONSE_KEYS
    assert "id" not in props  # ARCH-007 / AC10
