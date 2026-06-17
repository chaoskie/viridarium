# Design - plant-cachepot (US-2.x)

Extends the plant-crud vertical slice; [INHERITED] = the plant-crud pattern, not
re-justified. Only the cachepot additions are designed here.

## Key decisions

- **D1 - existing pot fields are the inner/nursery pot; keep their names.** The
  current `pot_material` / `pot_size_cm` already describe the real soil-holding pot,
  which is the inner/nursery pot in a cachepot setup. Renaming them
  (`inner_pot_material`, ...) would break the public REST contract (API-004) for no
  functional gain. Decision: **do not rename.** Document the semantics; clarify in the
  UI with the label "Nursery (inner) pot". Additive `outer_pot_*` fields carry the new
  information.
- **D2 - dedicated `OuterPotMaterial` enum, not reuse of `PotMaterial`.** A decorative
  outer pot has a different material space than a functional nursery pot:
  `self-watering` is an inner-pot trait and makes no sense outside; decorative
  materials (woven/basket, metal, glass) don't apply to nursery pots. Values:
  `ceramic`, `terracotta`, `plastic`, `metal`, `woven`, `glass`, `other`. `StrEnum`
  in domain, stored as `String(20)` (D3 precedent; no native DB enum, ARCH-011),
  wire form = lowercase value. Pydantic validates → 422 on bad value.
- **D3 - both new columns nullable; null = "no cachepot".** Existing rows and plants
  with a bare nursery pot read back `null` for both. No backfill. `outer_pot_size_cm`
  is optional even when `outer_pot_material` is set (you may not know the size).
- **D4 - no inner≤outer size validation in v1.** Each size is independently bounded
  (1-500). A cross-field "outer should be ≥ inner" rule is deferred (could be a soft
  warning later); enforcing it now risks rejecting legitimate odd setups.
- **D5 - descriptive only.** No change to due/schedule/timeline. The data is the
  enabler for a later bottom-watering / waterlogging-care phase (proposal "why").

## 1. REST / OpenAPI delta

Path `/api/v1/plants` (unchanged surface). Additive optional fields:

**`PlantCreate` / `PlantUpdate`** gain:
- `outer_pot_material` (opt, `OuterPotMaterial`, default null)
- `outer_pot_size_cm` (opt int, `ge=1, le=500`, default null)

**`PlantResponse`** gains the same two fields (`from_attributes=True`).

No status-code or path changes. Existing request bodies remain valid (fields default
null) → non-breaking; API-004 not triggered. The codegen/OpenAPI assertion test
(TEST-008) is extended to expect the two new properties.

## 2. Domain

`domain/plant.py`:
- Add `class OuterPotMaterial(StrEnum)` with the D2 values.
- Add `outer_pot_material: OuterPotMaterial | None = None` and
  `outer_pot_size_cm: int | None = None` to the plant entity / `NewPlant` (whatever
  the create carrier is) and thread through update. Pure domain, no I/O.

## 3. Persistence

- `models.py`: `PlantModel` gains `outer_pot_material: Mapped[str | None]`
  (`String(20)`, nullable) and `outer_pot_size_cm: Mapped[int | None]` (nullable).
  `_to_domain` maps both (string → `OuterPotMaterial` or None).
- Migration `migrations/versions/0008_add_cachepot_columns.py` (down_rev = current
  head): `op.add_column` x2, both nullable, using **batch mode** for SQLite stability
  (naming-convention aligned). Down = drop both columns. Must run up+down on SQLite
  and PostgreSQL (ARCH-011).
- Extend the migration test to cover 0008 up/down on both engines.

## 4. Frontend

- `lib/api/plants.ts`: add `outer_pot_material` + `outer_pot_size_cm` to the `Plant` /
  `PlantInput` types; export `OUTER_POT_MATERIALS` (mirrors the enum) for the select.
- `features/plants/PlantFormModal.tsx`:
  - Relabel the existing pot controls under a "Nursery (inner) pot" heading
    (label-only; state/field names unchanged).
  - Add an "Outer / decorative pot (optional)" section: an `OuterPotMaterial`
    `FieldSelect` (with "Not set" = null) + an optional `outer_pot_size_cm` number
    input (`min=1 max=500 step=1`, same integer handling as `pot_size_cm`, reusing
    `parseOptionalInt`).
  - Both submit as null when blank/"Not set".
- Display (optional, minimal): on the plant detail, if an outer pot is set, show it
  alongside the inner pot. List view unchanged to avoid clutter.
- a11y: every new control labelled (FE-011); the modal already scrolls (BUG-003 fix),
  so the extra fields don't regress reachability - the acceptance suite re-checks.

## 5. Tests (foundation summary; full matrix in test-foundation.md)

- Backend unit: enum round-trips; entity carries the new fields.
- Backend integration: POST/PUT accept valid outer material+size; bad enum → 422;
  `outer_pot_size_cm` 0/501 → 422; response echoes both; null defaults; migration
  0008 up/down on both engines. Extend the parametrized bad-body matrix.
- Frontend: form sets/clears outer material + size; submits null when unset; OpenAPI
  codegen assertion includes the new properties (TEST-008).
- Playwright (TEST-009): add-plant with an outer pot persists and reads back; the
  modal still passes the S25+ reachability + a11y checks with the extra fields.
