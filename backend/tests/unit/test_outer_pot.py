"""Unit tests for the cachepot (outer-pot) domain additions (TEST-002: no I/O).

Two targeted units the integration slice does not already pin (test-foundation §0, §10):
the new ``OuterPotMaterial`` ``StrEnum`` members + wire values (D2), and the ``Plant`` /
``NewPlant`` entities carrying + threading the two new optional fields. The existing
frozen dataclasses otherwise get no unit test (TEST-004 #2); these assert the *new*
members/fields that did not exist before, so they are genuinely red-first.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from viridarium.domain.plant import NewPlant, OuterPotMaterial, Plant

pytestmark = pytest.mark.unit


def test_outer_pot_material_members_and_wire_values() -> None:
    # D2: exactly these seven decorative materials, lowercase wire values, no
    # ``self-watering`` (an inner-pot trait deliberately excluded).
    assert [m.value for m in OuterPotMaterial] == [
        "ceramic",
        "terracotta",
        "plastic",
        "metal",
        "woven",
        "glass",
        "other",
    ]
    assert OuterPotMaterial("woven") is OuterPotMaterial.WOVEN
    assert "self-watering" not in {m.value for m in OuterPotMaterial}


def test_new_plant_carries_outer_pot_fields() -> None:
    new_plant = NewPlant(
        name="Monstera",
        species=None,
        location_id=None,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=(),
        archived=False,
        outer_pot_material=OuterPotMaterial.CERAMIC,
        outer_pot_size_cm=22,
    )

    assert new_plant.outer_pot_material is OuterPotMaterial.CERAMIC
    assert new_plant.outer_pot_size_cm == 22


def test_outer_pot_fields_default_to_none() -> None:
    # A bare nursery-pot plant carries null/null for both (D3).
    new_plant = NewPlant(
        name="Pothos",
        species=None,
        location_id=None,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=(),
        archived=False,
    )

    assert new_plant.outer_pot_material is None
    assert new_plant.outer_pot_size_cm is None


def test_plant_entity_threads_outer_pot_fields() -> None:
    plant = Plant(
        id=1,
        name="Fern",
        species=None,
        location_id=None,
        acquired_on=None,
        pot_size_cm=None,
        pot_material=None,
        light_level=None,
        notes=None,
        tags=(),
        archived=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        outer_pot_material=OuterPotMaterial.WOVEN,
        outer_pot_size_cm=18,
    )

    # The frozen entity threads the values; ``replace`` rebuilds with a new outer pot.
    rehomed = replace(plant, outer_pot_material=OuterPotMaterial.GLASS)
    assert plant.outer_pot_material is OuterPotMaterial.WOVEN
    assert plant.outer_pot_size_cm == 18
    assert rehomed.outer_pot_material is OuterPotMaterial.GLASS
