"""Integration tests for the /api/v1/plants CRUD surface (TEST-001 primary layer).

A real-DB slice through router -> service -> repository -> SQLAlchemy -> SQLite
exercises validation, enum/date coercion, persistence round-trip, search/filter, the
ON DELETE SET NULL orphaning, the plant_tag CASCADE, and 404/422 mapping. Nothing
internal is mocked (TEST-003); each test seeds the rooms/plants it needs via the API
within its own temp-file SQLite ``client`` (TEST-006 independence). Migration ``0003``
creates ``plant`` + ``plant_tag``, so no fixture change is needed.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from viridarium.domain.plant import LightLevel, OuterPotMaterial, PotMaterial

pytestmark = pytest.mark.integration

_PLANTS = "/api/v1/plants"
_LOCATIONS = "/api/v1/locations"


def _make_room(client: TestClient, name: str = "Greenhouse") -> int:
    room_id: int = client.post(_LOCATIONS, json={"name": name}).json()["id"]
    return room_id


# --------------------------------------------------------------------------- POST
def test_post_creates_plant_full_and_round_trips(client: TestClient) -> None:
    room_id = _make_room(client)
    payload = {
        "name": "Monstera",
        "species": "Monstera deliciosa",
        "location_id": room_id,
        "acquired_on": "2026-01-15",
        "pot_size_cm": 14,
        "pot_material": "terracotta",
        "light_level": "bright-indirect",
        "notes": "north window",
        "tags": ["fern", "rare"],
    }

    response = client.post(_PLANTS, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Monstera"
    assert body["species"] == "Monstera deliciosa"
    assert body["location_id"] == room_id
    assert body["acquired_on"] == "2026-01-15"
    assert body["pot_size_cm"] == 14
    assert body["pot_material"] == "terracotta"
    assert body["light_level"] == "bright-indirect"
    assert body["notes"] == "north window"
    assert sorted(body["tags"]) == ["fern", "rare"]
    assert body["archived"] is False
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body

    fetched = client.get(f"{_PLANTS}/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_post_creates_homeless_plant(client: TestClient) -> None:
    response = client.post(_PLANTS, json={"name": "Pothos"})

    assert response.status_code == 201
    body = response.json()
    assert body["location_id"] is None
    assert body["tags"] == []
    assert body["archived"] is False


def test_post_dedupes_tags(client: TestClient) -> None:
    response = client.post(_PLANTS, json={"name": "Fern", "tags": ["a", "a", "b"]})

    assert response.status_code == 201
    assert sorted(response.json()["tags"]) == ["a", "b"]


@pytest.mark.parametrize("pot_material", list(PotMaterial))
def test_post_each_pot_material_round_trips(
    client: TestClient, pot_material: PotMaterial
) -> None:
    response = client.post(
        _PLANTS, json={"name": "P", "pot_material": pot_material.value}
    )

    assert response.status_code == 201
    assert response.json()["pot_material"] == pot_material.value


@pytest.mark.parametrize("light_level", list(LightLevel))
def test_post_each_light_level_round_trips(
    client: TestClient, light_level: LightLevel
) -> None:
    response = client.post(
        _PLANTS, json={"name": "P", "light_level": light_level.value}
    )

    assert response.status_code == 201
    assert response.json()["light_level"] == light_level.value


def test_post_archived_true_round_trips(client: TestClient) -> None:
    response = client.post(_PLANTS, json={"name": "Old", "archived": True})

    assert response.status_code == 201
    assert response.json()["archived"] is True


# ------------------------------------------- cachepot / outer pot (plant-cachepot)
@pytest.mark.parametrize("outer_pot_material", list(OuterPotMaterial))
def test_post_each_outer_pot_material_round_trips(  # B1
    client: TestClient, outer_pot_material: OuterPotMaterial
) -> None:
    response = client.post(
        _PLANTS, json={"name": "P", "outer_pot_material": outer_pot_material.value}
    )

    assert response.status_code == 201
    assert response.json()["outer_pot_material"] == outer_pot_material.value


@pytest.mark.parametrize("size", [1, 500])
def test_post_outer_pot_size_boundaries_round_trip(  # B3
    client: TestClient, size: int
) -> None:
    response = client.post(_PLANTS, json={"name": "P", "outer_pot_size_cm": size})

    assert response.status_code == 201
    assert response.json()["outer_pot_size_cm"] == size


# B6: each independent-optionality pairing accepted + echoed.
@pytest.mark.parametrize(
    ("material", "size"),
    [
        ("ceramic", None),
        (None, 30),
        ("woven", 22),
        (None, None),
    ],
)
def test_outer_pot_fields_independently_optional(
    client: TestClient, material: str | None, size: int | None
) -> None:
    body: dict[str, Any] = {"name": "P"}
    if material is not None:
        body["outer_pot_material"] = material
    if size is not None:
        body["outer_pot_size_cm"] = size

    response = client.post(_PLANTS, json=body)

    assert response.status_code == 201
    echoed = response.json()
    assert echoed["outer_pot_material"] == material
    assert echoed["outer_pot_size_cm"] == size


def test_post_outer_pot_null_when_unset_round_trips(client: TestClient) -> None:  # B7
    # A bare nursery-pot plant reads back null/null and re-fetches identically.
    created = client.post(_PLANTS, json={"name": "Bare"})

    assert created.status_code == 201
    body = created.json()
    assert body["outer_pot_material"] is None
    assert body["outer_pot_size_cm"] is None

    fetched = client.get(f"{_PLANTS}/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_inner_and_outer_pot_coexist_and_round_trip(client: TestClient) -> None:
    # Setting the outer pot leaves the inner (nursery) pot untouched; all four fields
    # round-trip independently (D1).
    payload = {
        "name": "Calathea",
        "pot_size_cm": 12,
        "pot_material": "plastic",
        "outer_pot_size_cm": 16,
        "outer_pot_material": "woven",
    }

    response = client.post(_PLANTS, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["pot_size_cm"] == 12
    assert body["pot_material"] == "plastic"
    assert body["outer_pot_size_cm"] == 16
    assert body["outer_pot_material"] == "woven"


# Shared validation matrix (test-foundation §1c, S1-S13), run for POST and PUT.
_BAD_BODIES = [
    pytest.param({"name": ""}, id="name-empty"),
    pytest.param({"name": "   "}, id="name-whitespace"),
    pytest.param({"name": "x" * 121}, id="name-over-120"),
    pytest.param({"name": "ok", "species": "x" * 201}, id="species-over-200"),
    pytest.param(
        {"name": "ok", "acquired_on": "not-a-date"}, id="acquired-on-malformed"
    ),
    pytest.param({"name": "ok", "pot_size_cm": 0}, id="pot-size-below-min"),
    pytest.param({"name": "ok", "pot_size_cm": 501}, id="pot-size-above-max"),
    pytest.param({"name": "ok", "pot_size_cm": "big"}, id="pot-size-non-int"),
    # a float must be a 422, never silently truncated to int (VIRIDARIUM-47)
    pytest.param({"name": "ok", "pot_size_cm": 3.7}, id="pot-size-float-not-coerced"),
    pytest.param({"name": "ok", "pot_material": "gold"}, id="pot-material-invalid"),
    pytest.param(
        {"name": "ok", "light_level": "ultraviolet"}, id="light-level-invalid"
    ),
    pytest.param({"name": "ok", "tags": ["x" * 51]}, id="tag-over-long"),
    pytest.param(
        {"name": "ok", "tags": [str(i) for i in range(51)]}, id="tags-too-many"
    ),
    pytest.param({"name": "ok", "notes": "x" * 10001}, id="notes-over-max"),
    # cachepot / outer pot (plant-cachepot): B2 / B4 / B5, run for POST and PUT.
    pytest.param(
        {"name": "ok", "outer_pot_material": "gold"}, id="outer-pot-material-invalid"
    ),
    # self-watering is an inner-pot trait, deliberately NOT a valid outer value (D2).
    pytest.param(
        {"name": "ok", "outer_pot_material": "self-watering"},
        id="outer-pot-material-self-watering-rejected",
    ),
    pytest.param({"name": "ok", "outer_pot_size_cm": 0}, id="outer-pot-size-below-min"),
    pytest.param(
        {"name": "ok", "outer_pot_size_cm": 501}, id="outer-pot-size-above-max"
    ),
    pytest.param(
        {"name": "ok", "outer_pot_size_cm": "big"}, id="outer-pot-size-non-int"
    ),
    # a float must be a 422, never silently truncated to int (VIRIDARIUM-47 guard).
    pytest.param(
        {"name": "ok", "outer_pot_size_cm": 3.7}, id="outer-pot-size-float-not-coerced"
    ),
]


@pytest.mark.parametrize("body", _BAD_BODIES)
def test_post_validation_rejects_bad_body(
    client: TestClient, body: dict[str, Any]
) -> None:
    response = client.post(_PLANTS, json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("body", _BAD_BODIES)
def test_put_validation_rejects_bad_body(
    client: TestClient, body: dict[str, Any]
) -> None:
    created = client.post(_PLANTS, json={"name": "seed"}).json()

    response = client.put(f"{_PLANTS}/{created['id']}", json=body)

    assert response.status_code == 422


# S14: nonexistent location_id -> 422 id-only (NOT 404). The headline AC4 assertion.
def test_post_nonexistent_location_returns_422_not_404(client: TestClient) -> None:
    response = client.post(_PLANTS, json={"name": "Orphan", "location_id": 424242})

    assert response.status_code != 404
    assert response.status_code == 422
    body = response.json()
    assert set(body.keys()) == {"detail"}
    assert "424242" in body["detail"]


def test_put_nonexistent_location_returns_422(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "seed"}).json()

    response = client.put(
        f"{_PLANTS}/{created['id']}", json={"name": "seed", "location_id": 424242}
    )

    assert response.status_code != 404
    assert response.status_code == 422
    assert "424242" in response.json()["detail"]


# --------------------------------------------------------------------------- LIST
def test_list_returns_plants_ordered_by_name(client: TestClient) -> None:
    for name in ("Snake", "Aloe", "Mint"):
        client.post(_PLANTS, json={"name": name})

    response = client.get(_PLANTS)

    assert response.status_code == 200
    assert [p["name"] for p in response.json()] == ["Aloe", "Mint", "Snake"]


def test_list_empty_store_returns_empty_array(client: TestClient) -> None:
    response = client.get(_PLANTS)

    assert response.status_code == 200
    assert response.json() == []


# ------------------------------------------------------------------------- GET one
def test_get_one_returns_plant(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Cactus", "tags": ["spiky"]}).json()

    response = client.get(f"{_PLANTS}/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Cactus"
    assert body["tags"] == ["spiky"]
    assert body["location_id"] is None


def test_get_unknown_id_returns_404_no_pii(client: TestClient) -> None:
    response = client.get(f"{_PLANTS}/424242")

    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"detail"}
    assert "424242" in body["detail"]


# ----------------------------------------------------------------------------- PUT
def test_put_full_replace_swaps_tags_and_bumps_updated_at(client: TestClient) -> None:
    created = client.post(
        _PLANTS, json={"name": "Old", "species": "before", "tags": ["a", "b"]}
    ).json()

    response = client.put(
        f"{_PLANTS}/{created['id']}",
        json={"name": "New", "species": "after", "tags": ["c"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New"
    assert body["species"] == "after"
    assert body["tags"] == ["c"]
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] >= created["updated_at"]

    fetched = client.get(f"{_PLANTS}/{created['id']}").json()
    assert fetched["name"] == "New"
    assert fetched["tags"] == ["c"]


def test_put_unknown_id_returns_404(client: TestClient) -> None:
    response = client.put(f"{_PLANTS}/424242", json={"name": "Nope"})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}
    assert "424242" in response.json()["detail"]


# -------------------------------------------------------------------------- DELETE
def test_delete_removes_plant_then_get_404(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Temp"}).json()

    deleted = client.delete(f"{_PLANTS}/{created['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"{_PLANTS}/{created['id']}").status_code == 404


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    response = client.delete(f"{_PLANTS}/424242")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}


# --------------------------------------------------------- search / filter (§2b, D4)
def test_filter_q_matches_name(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Monstera"})
    client.post(_PLANTS, json={"name": "Aloe"})

    names = [p["name"] for p in client.get(f"{_PLANTS}?q=mons").json()]

    assert names == ["Monstera"]


def test_filter_q_matches_species(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "A", "species": "Monstera deliciosa"})
    client.post(_PLANTS, json={"name": "B", "species": "Aloe vera"})

    names = [p["name"] for p in client.get(f"{_PLANTS}?q=delicio").json()]

    assert names == ["A"]


def test_filter_q_is_case_insensitive(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Monstera"})

    lower = [p["name"] for p in client.get(f"{_PLANTS}?q=mons").json()]
    upper = [p["name"] for p in client.get(f"{_PLANTS}?q=MONS").json()]

    assert lower == upper == ["Monstera"]


def test_filter_location_id_exact(client: TestClient) -> None:
    room_a = _make_room(client, "A")
    room_b = _make_room(client, "B")
    client.post(_PLANTS, json={"name": "InA", "location_id": room_a})
    client.post(_PLANTS, json={"name": "InB", "location_id": room_b})

    names = [p["name"] for p in client.get(f"{_PLANTS}?location_id={room_a}").json()]

    assert names == ["InA"]


def test_filter_homeless_returns_only_orphans(client: TestClient) -> None:
    room = _make_room(client)
    client.post(_PLANTS, json={"name": "Housed", "location_id": room})
    client.post(_PLANTS, json={"name": "Homeless"})

    names = [p["name"] for p in client.get(f"{_PLANTS}?homeless=true").json()]

    assert names == ["Homeless"]


def test_filter_tag_present(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Rare", "tags": ["rare"]})
    client.post(_PLANTS, json={"name": "Common", "tags": ["common"]})

    names = [p["name"] for p in client.get(f"{_PLANTS}?tag=rare").json()]

    assert names == ["Rare"]


def test_filter_tag_absent_returns_empty(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Rare", "tags": ["rare"]})

    assert client.get(f"{_PLANTS}?tag=ghost").json() == []


def test_filter_species_substring(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "A", "species": "Ficus lyrata"})
    client.post(_PLANTS, json={"name": "B", "species": "Aloe vera"})

    names = [p["name"] for p in client.get(f"{_PLANTS}?species=ficus").json()]

    assert names == ["A"]


def test_filter_combined_and_all_match(client: TestClient) -> None:
    room = _make_room(client)
    client.post(
        _PLANTS,
        json={
            "name": "Monstera",
            "species": "Monstera deliciosa",
            "location_id": room,
            "tags": ["rare"],
        },
    )

    url = f"{_PLANTS}?q=mons&location_id={room}&tag=rare"
    names = [p["name"] for p in client.get(url).json()]

    assert names == ["Monstera"]


def test_filter_combined_and_partial_excluded(client: TestClient) -> None:
    room = _make_room(client)
    other = _make_room(client, "Other")
    # Matches q + tag but is in the *other* room -> excluded by AND on location_id.
    client.post(
        _PLANTS,
        json={"name": "Monstera", "location_id": other, "tags": ["rare"]},
    )

    url = f"{_PLANTS}?q=mons&location_id={room}&tag=rare"

    assert client.get(url).json() == []


def test_filter_unknown_location_id_returns_empty(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Homeless"})

    # As a *filter*, unknown location_id is an empty result, NOT an error (vs S14).
    response = client.get(f"{_PLANTS}?location_id=424242")

    assert response.status_code == 200
    assert response.json() == []


# ----------------------------- cross-entity SET-NULL (§2c, AC7, D1) - headline test
def test_deleting_room_orphans_its_plants_to_homeless(client: TestClient) -> None:
    room_id = _make_room(client)
    created = client.post(
        _PLANTS,
        json={"name": "Monstera", "location_id": room_id, "tags": ["rare"]},
    ).json()

    delete_room = client.delete(f"{_LOCATIONS}/{room_id}")
    assert delete_room.status_code == 204

    fetched = client.get(f"{_PLANTS}/{created['id']}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["location_id"] is None  # SET NULL fired: plant is now homeless
    assert body["name"] == "Monstera"  # plant survives
    assert body["tags"] == ["rare"]  # its tags survive intact


# ------------------------------------ plant_tag CASCADE (§2d, AC8) -----------------
def test_deleting_plant_cascades_its_tag_rows(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Tagged", "tags": ["x", "y"]}).json()

    assert client.delete(f"{_PLANTS}/{created['id']}").status_code == 204

    # The plant is gone; recreating with the same tags and listing by tag must not
    # surface any orphaned rows from the deleted plant (a single match only).
    again = client.post(_PLANTS, json={"name": "Fresh", "tags": ["x"]}).json()
    by_tag = client.get(f"{_PLANTS}?tag=x").json()
    assert [p["id"] for p in by_tag] == [again["id"]]


# ----------------------------------------------------------------- OpenAPI (§2e, AC11)
def test_openapi_exposes_plant_paths_query_params_and_schema(
    client: TestClient,
) -> None:
    schema = client.get("/api/v1/openapi.json").json()

    assert "/api/v1/plants" in schema["paths"]
    assert "/api/v1/plants/{plant_id}" in schema["paths"]

    list_op = schema["paths"]["/api/v1/plants"]["get"]
    param_names = {p["name"] for p in list_op.get("parameters", [])}
    assert {"q", "location_id", "tag", "species", "homeless"} <= param_names

    assert "/api/v1/plants/{plant_id}/archive" in schema["paths"]
    assert "/api/v1/plants/{plant_id}/unarchive" in schema["paths"]
    assert {"archived", "include_archived"} <= param_names

    response_schema = schema["components"]["schemas"]["PlantResponse"]
    # C1 / C5: exact key-set (the rename-or-removal guard) - inner pot names unchanged,
    # the two additive cachepot fields present.
    assert set(response_schema["properties"].keys()) == {
        "id",
        "name",
        "species",
        "location_id",
        "acquired_on",
        "pot_size_cm",
        "pot_material",
        "light_level",
        "notes",
        "tags",
        "archived",
        "created_at",
        "updated_at",
        "schedules",  # additive US-3.3 due field (proposal §API, non-breaking)
        "cover_photo_id",  # additive plant-list-nplus1 cover id (non-breaking)
        "outer_pot_material",  # additive plant-cachepot field (non-breaking)
        "outer_pot_size_cm",  # additive plant-cachepot field (non-breaking)
    }

    schemas = schema["components"]["schemas"]
    # C2: both request schemas gain the two additive properties.
    for schema_name in ("PlantCreate", "PlantUpdate"):
        props = schemas[schema_name]["properties"]
        assert "outer_pot_material" in props
        assert "outer_pot_size_cm" in props

    create_props = schemas["PlantCreate"]["properties"]
    # C3: outer size carries the contract bounds and is nullable (same shape as the
    # inner ``pot_size_cm``: anyOf integer(min/max)|null).
    size_arms = create_props["outer_pot_size_cm"]["anyOf"]
    int_arm = next(a for a in size_arms if a.get("type") == "integer")
    assert int_arm["minimum"] == 1
    assert int_arm["maximum"] == 500
    assert any(a.get("type") == "null" for a in size_arms)

    # C4: outer material enum lists exactly the 7 wire values and is nullable.
    mat_arms = create_props["outer_pot_material"]["anyOf"]
    enum_ref = next(a for a in mat_arms if "$ref" in a)
    enum_name = enum_ref["$ref"].rsplit("/", 1)[-1]
    assert schemas[enum_name]["enum"] == [m.value for m in OuterPotMaterial]
    assert any(a.get("type") == "null" for a in mat_arms)


# ------------------------------------------ archive / unarchive (US-2.4, §3, AC1-AC6)
def test_archive_sets_flag_and_persists(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Dead"}).json()

    response = client.post(f"{_PLANTS}/{created['id']}/archive")

    assert response.status_code == 200
    assert response.json()["archived"] is True
    assert client.get(f"{_PLANTS}/{created['id']}").json()["archived"] is True


def test_unarchive_clears_flag_and_persists(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Back", "archived": True}).json()

    response = client.post(f"{_PLANTS}/{created['id']}/unarchive")

    assert response.status_code == 200
    assert response.json()["archived"] is False
    assert client.get(f"{_PLANTS}/{created['id']}").json()["archived"] is False


def test_archive_unknown_id_returns_404_no_pii(client: TestClient) -> None:
    response = client.post(f"{_PLANTS}/424242/archive")

    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"detail"}
    assert "424242" in body["detail"]


def test_unarchive_unknown_id_returns_404_no_pii(client: TestClient) -> None:
    response = client.post(f"{_PLANTS}/424242/unarchive")

    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"detail"}
    assert "424242" in body["detail"]


def test_archive_is_idempotent(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Twice"}).json()

    first = client.post(f"{_PLANTS}/{created['id']}/archive")
    second = client.post(f"{_PLANTS}/{created['id']}/archive")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["archived"] is True
    assert second.json()["archived"] is True


def test_unarchive_is_idempotent(client: TestClient) -> None:
    created = client.post(_PLANTS, json={"name": "Active"}).json()

    first = client.post(f"{_PLANTS}/{created['id']}/unarchive")
    second = client.post(f"{_PLANTS}/{created['id']}/unarchive")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["archived"] is False
    assert second.json()["archived"] is False


def test_list_excludes_archived_by_default(client: TestClient) -> None:
    # Intended US-2.1 contract change (design D5 / proposal deviation 2): the default
    # list switches from "all" to "active only". This is the US-2.4 deliverable US-2.1
    # explicitly deferred, NOT a regression.
    client.post(_PLANTS, json={"name": "Active"})
    archived = client.post(_PLANTS, json={"name": "Archived"}).json()
    client.post(f"{_PLANTS}/{archived['id']}/archive")

    names = [p["name"] for p in client.get(_PLANTS).json()]

    assert names == ["Active"]


def test_list_archived_true_returns_archived_only(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Active"})
    archived = client.post(_PLANTS, json={"name": "Archived"}).json()
    client.post(f"{_PLANTS}/{archived['id']}/archive")

    names = [p["name"] for p in client.get(f"{_PLANTS}?archived=true").json()]

    assert names == ["Archived"]


def test_list_include_archived_returns_all(client: TestClient) -> None:
    client.post(_PLANTS, json={"name": "Active"})
    archived = client.post(_PLANTS, json={"name": "Archived"}).json()
    client.post(f"{_PLANTS}/{archived['id']}/archive")

    names = [p["name"] for p in client.get(f"{_PLANTS}?include_archived=true").json()]

    assert names == ["Active", "Archived"]


def test_list_archived_and_tag_composes_and(client: TestClient) -> None:
    # (a) archived + rare -> the only match for ?archived=true&tag=rare.
    a = client.post(_PLANTS, json={"name": "ArchivedRare", "tags": ["rare"]}).json()
    client.post(f"{_PLANTS}/{a['id']}/archive")
    # (b) active + rare -> excluded (wrong archived state).
    client.post(_PLANTS, json={"name": "ActiveRare", "tags": ["rare"]})
    # (c) archived + common -> excluded (wrong tag).
    c = client.post(_PLANTS, json={"name": "ArchivedCommon", "tags": ["common"]}).json()
    client.post(f"{_PLANTS}/{c['id']}/archive")

    names = [p["name"] for p in client.get(f"{_PLANTS}?archived=true&tag=rare").json()]

    assert names == ["ArchivedRare"]


def test_lifecycle_archive_unarchive_keeps_history(client: TestClient) -> None:
    created = client.post(
        _PLANTS, json={"name": "Lifecycle", "tags": ["rare", "fern"]}
    ).json()

    # Present in the default (active) list.
    assert "Lifecycle" in [p["name"] for p in client.get(_PLANTS).json()]

    # Archive -> absent from the default list.
    assert client.post(f"{_PLANTS}/{created['id']}/archive").status_code == 200
    assert "Lifecycle" not in [p["name"] for p in client.get(_PLANTS).json()]

    # Unarchive -> present again, history (tags, created_at) intact throughout.
    unarchived = client.post(f"{_PLANTS}/{created['id']}/unarchive").json()
    assert "Lifecycle" in [p["name"] for p in client.get(_PLANTS).json()]
    assert sorted(unarchived["tags"]) == ["fern", "rare"]
    assert unarchived["created_at"] == created["created_at"]
