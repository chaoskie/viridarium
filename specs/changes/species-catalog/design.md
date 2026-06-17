# Design - species-catalog (Botanicum Phase 1A)

A new read-only bounded slice. [INHERITED] = the location/plant CRUD patterns
(hexagon layering, StrEnum-as-String(20), migration naming convention), not re-justified.

## Key decisions

- **D1 - read-only over the API in 1A.** The catalog is content, not user data; v1
  exposes only `GET` list/detail. No POST/PUT/DELETE until Phase 2 (editable catalog).
  Keeps the surface small and the trust posture trivial.
- **D2 - seed shipped as repo data, loaded by a data migration.** A Python data module
  (`adapters/outbound/db/seed/species_seed.py`) holds the curated list; an Alembic
  migration's `upgrade` `bulk_insert`s it and `downgrade` deletes those rows by slug.
  This keeps the catalog identical and fully offline on both engines (ARCH-011), and
  versioned with the schema. Idempotent on re-run via stable `slug`s.
- **D3 - reuse existing enums.** `light_level` reuses `LightLevel`; `dormancy` reuses
  `Dormancy`. Stored as `String(20)` (no native DB enum, ARCH-011). Intervals are
  day-based ints (the weeks-vs-days seasonality question is a roadmap item, not v1).
- **D4 - `category` is a small `StrEnum`** (`cactus-succulent`, `foliage`, `fern`,
  `palm`, `flowering`, `other`) so broad-behaviour entries (e.g. cacti & succulents)
  are first-class; finer varieties are added as rows later.
- **D5 - no plant change here.** `species_id` on plant, the picker, and prefill are
  Phase 1B. This change must not touch the plant table, schema, or UI.
- **D6 - all default fields nullable.** A category-level or sparsely-known species may
  omit any default; the API returns null and 1B simply skips prefilling those.
- **D7 - watering = informational range + a conservative applied average.** A species
  stores `water_interval_min_days` / `water_interval_max_days` (the range we show, e.g.
  7-14) and a single `water_interval_days` (what 1B actually prefills into the
  schedule). The applied average is authored toward the **drier/longer** end of the
  range on purpose - a houseplant tolerates drought far better than overwatering, so
  erring long is the safe default. (Authoring guideline for the seed, enforced by
  review, not code.) Feeding/winter stay single intervals in v1.
- **D8 - `care_notes` free-text escape hatch.** An optional free-text field (≤2000)
  carries raw care info we have but haven't structured yet (humidity/misting, "top
  ~2 cm dry between waterings", potting-mix hints). It lets the seed hold real value
  for the Phase-3 dimensions before they get first-class fields, with zero modelling cost.

## 1. REST / OpenAPI delta

New tag `species`, path base `/api/v1/species` (API-006):
- `GET /api/v1/species` → `list[SpeciesResponse]`; optional `?category=<category>` and
  `?q=<substring over common/scientific name>` (lowered-LIKE, portable). None → all,
  ordered by `common_name ASC`.
- `GET /api/v1/species/{id}` → `SpeciesResponse`; unknown id → 404 (domain
  `SpeciesNotFoundError` → handler).

**`SpeciesResponse`** (`from_attributes=True`): `id`, `slug`, `common_name`,
`scientific_name` (nullable), `category` (nullable), `light_level` (nullable),
`water_interval_min_days` (nullable), `water_interval_max_days` (nullable),
`water_interval_days` (nullable, the applied average), `feed_interval_days` (nullable),
`winter_interval_days` (nullable), `dormancy` (nullable), `care_notes` (nullable text).
No request schema in 1A.

## 2. Domain

`domain/species.py`: `Category` + (reused) enums; `Species` value object with the
fields above; `SpeciesNotFoundError`; `SpeciesRepository` Protocol (`list(filter)`,
`get(id)`). Pure domain, no I/O.

## 3. Application

`application/species.py`: `SpeciesService` with `list_species(category?, q?)` and
`get_species(id)`. Thin read-through to the repository; raises `SpeciesNotFoundError`.

## 4. Persistence + seed

- `models.py`: `SpeciesModel` - `id` PK, `slug` unique, `common_name`,
  `scientific_name` nullable, `category` `String(20)` nullable; default columns all
  nullable: `light_level` `String(20)`, `water_interval_min_days` Integer,
  `water_interval_max_days` Integer, `water_interval_days` Integer, `feed_interval_days`
  Integer, `winter_interval_days` Integer, `dormancy` `String(20)`, `care_notes` Text.
- `seed/species_seed.py`: the curated ~25-30 entries as a typed list of dicts.
- `migrations/versions/0009_create_species_and_seed.py`: create table; `bulk_insert`
  the seed; `downgrade` drops the table. Batch mode for SQLite; naming-convention
  aligned. down_rev = current head.
- `species_repository.py`: `SqlAlchemySpeciesRepository` + `_to_domain` + portable
  filter query (lowered-LIKE for `q`, exact for `category`).
- Integration: migration 0009 up/down on **both** engines; the seeded row count + a
  spot-checked species are identical across engines.

## 5. Web wiring

- `schemas.py`: `SpeciesResponse`.
- `species.py` router: the two GET routes; list-query → repository filter.
- `dependencies.py`: `get_species_service`. `container.py` + `app.py`: construct the
  repo/service, mount the router, register the not-found handler.

## 6. Frontend (1A scope: typed client only)

- `lib/api/species.ts`: `Species` type + `listSpecies(filter?)` + `getSpecies(id)`
  typed functions + a client test (happy + ApiError sad). No UI yet (picker = 1B).

## 7. Tests (foundation summary; full matrix in test-foundation.md)

- Unit: `SpeciesService` read paths + not-found.
- Integration: `GET` list (all / by category / by `q`), `GET` detail + 404, the
  migration-seed dual-engine parity, lowered-LIKE portability.
- Frontend: `species` client round-trips list/detail; ApiError on 404.
- Codegen (TEST-008): OpenAPI includes the `species` paths + `SpeciesResponse`.
