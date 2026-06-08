---
title: Test Foundation - plant-crud (US-2.1)
type: test-foundation
change: plant-crud
status: authored
date: 2026-06-08
author: test-engineer/HIGH
gates: SPEC-003 (pre-implementation), QG-002, TEST-001..TEST-014
---

# Test Foundation - plant-crud (US-2.1)

This is the SPEC-003 pre-implementation artifact that gates implementation. The two build
agents (backend / frontend) write tests **red -> green** against the surfaces, names, matrices,
and coverage targets enumerated here, and **record the failing run in the worklog before the
green** (TEST-014, §9 - mandatory per lane). The test-engineer **re-audits against this document
at story-complete** and issues the test-foundation approval as part of the DoD (QG-012, DoD §3);
nothing merges until that approval is recorded.

It refines the architect's test seed (design.md §4) into the authoritative foundation: the
explicit input-state matrix (TEST-007), happy+sad inventory per surface (TEST-005), search/filter
and cross-entity specs, per-behavior layer assignment with HoneyComb justification (TEST-001),
coverage targets (QG-002), required markers (TEST-012), and the mocking boundary (TEST-003). It
names files, test functions, and matrix cells. It is a **planning artifact** - it contains **no
test code**.

The contract under test is `design.md §1` (REST/OpenAPI delta, decisions D1-D5) and the ACs in
`proposal.md` (AC1-AC11). Plant inherits the Location vertical-slice template (US-2.2); the novel
surface here is the **optional location FK + ON DELETE SET NULL** (D1), the **normalized
`plant_tag` child + CASCADE** (D2), the **String-stored enums** (D3), and the **search/filter
query** (D4). The mirrored templates are `test-foundation.md`, `test_locations_endpoint.py`,
`test_location_use_case.py`, `test_migrations.py`, `conftest.py`, `useLocations.test.ts` from
location-crud.

---

## 0. HoneyComb strategy for this change (TEST-001)

Plant-CRUD is, like Location, thin glue over a real database - but with **more behavior that only
a real DB can honestly prove**: the FK `ON DELETE SET NULL` action, the `plant_tag` CASCADE, the
portable search/filter query (lowered-LIKE + EXISTS), and tag write/replace. Per TEST-001 the
**integration layer is primary**: a real-DB slice through router -> service -> repository ->
SQLAlchemy -> SQLite exercises validation, enum/date coercion, persistence round-trip,
search/filter, the SET-NULL orphaning, the tag CASCADE, 404/422 mapping, and OpenAPI emission in
one economical layer.

The **one piece of genuine application logic** worth isolating in a unit is the
`PlantService` **FK-existence guard** on create/update (D1 / ADR-B): "homeless is allowed; a
non-existent `location_id` raises `LocationNotFoundForPlantError`." That branch is pure decision
logic over a port and gets a surgical unit test against a hand-written fake port (TEST-003 -
faking the port is allowed). Everything else - the frozen `Plant`/`NewPlant`/`PlantFilter`
dataclasses, the enums, the error constructors - gets **no** unit test: asserting
`Plant(...).name == "..."` or `PotMaterial.TERRACOTTA == "terracotta"` would pass against any
implementation (fails TEST-004 #2) and is noise. Their behavior is observed transitively through
the integration round-trips.

E2E (Playwright) is **DEFERRED** to the frontend-infra story (proposal deviation #4, maintainer
approved) - §8. The journey is recorded as a deferred row, not built now.

The coverage floor (QG-002) is met by the **union** of unit + integration coverage (pytest
measures both together), so the integration bulk plus the targeted service unit clears the floor
without brittle implementation-mirror units.

---

## 1. Input-state matrix (TEST-007) - create / update validation

POST (`PlantCreate`) and PUT (`PlantUpdate(PlantCreate)`, full-replace per ADR-D) share the same
request validation, so the matrix is authored once and run for **both** surfaces (PUT against a
seeded existing plant so it reaches validation, not 404). Plant has **10 input dimensions**, far
exceeding the TEST-007 trigger (>= 3 dimensions OR >= 6 logical cells) - an explicit matrix with a
named branch-priority order is mandatory.

### 1a. Dimensions and their cells

Per design §1 (`PlantCreate` field rules) and D3 (enum wire values):

| Dim | Field | Cells |
|---|---|---|
| D-name | `name` (req, trimmed 1-120) | **valid** (`"Monstera"`), **empty** (`""`), **whitespace** (`"   "`), **over-120** (121 chars) |
| D-species | `species` (opt, <= 200) | **absent** (omitted/null), **valid** (`"Monstera deliciosa"`), **over-200** (201 chars) |
| D-loc | `location_id` (opt int FK, null=homeless) | **null** (homeless), **valid-existing** (a seeded room id), **nonexistent** (e.g. `424242`) |
| D-acq | `acquired_on` (opt date) | **absent**, **valid** (`"2026-01-15"`), **malformed** (`"not-a-date"` / `"2026-13-40"`) |
| D-pot-size | `pot_size_cm` (opt int, 1-500) | **absent**, **valid** (`14`), **below-min** (`0`), **above-max** (`501`), **non-int** (`"big"` / `12.5`) |
| D-pot-mat | `pot_material` (opt `PotMaterial`) | **absent**, **each valid** (every `PotMaterial` member, incl. `self-watering`), **invalid** (`"gold"`) |
| D-light | `light_level` (opt `LightLevel`) | **absent**, **each valid** (every `LightLevel` member, incl. `bright-indirect`, `full-sun`), **invalid** (`"ultraviolet"`) |
| D-tags | `tags` (list[str], default [], each trimmed non-empty <= 50, deduped, <= 50 items) | **empty** (`[]` / absent), **valid** (`["fern","rare"]`), **over-long-tag** (one tag 51 chars), **duplicate** (`["a","a"]` -> dedups to `["a"]`), **too-many** (51 items) |
| D-notes | `notes` (opt, <= 10000) | **absent**, **valid** (`"north window"`), **over-max** (10001 chars) |
| D-archived | `archived` (bool, default false) | **absent** (-> defaults false), **true**, **false** |

### 1b. Named branch-priority order: `NAME_ENUM_FK_BOUNDS_DEFAULTS`

When more than one dimension is invalid, this is the order in which the foundation reasons about
"which failure dominates" and which error loc the test asserts is present. Two distinct gates:

1. **Pydantic schema validation (request-shape gate, -> 422 before the service runs):**
   `name` (required identity, trimmed-empty -> required) -> **enum-validity** (`pot_material`,
   `light_level` against `PotMaterial`/`LightLevel`) -> field **bounds/types** (`species`/`notes`
   max-length, `pot_size_cm` range+int, `acquired_on` date parse, `tags` per-item length + item
   count) -> **optional defaults** (`tags=[]`, `archived=false`, absent optionals -> null).
   Pydantic reports all violated locs in one 422; a parametrized sad cell asserts `status == 422`
   and, where a single field is targeted, that the expected error loc is present.
2. **FK-existence guard (application gate, runs only after the body is schema-valid):** a
   schema-valid body with a **nonexistent `location_id`** reaches `PlantService`, which calls
   `location_exists` on the port and raises `LocationNotFoundForPlantError` -> mapped to **422**
   (id-only detail), **not** 404 (404 is reserved for the addressed plant). This is the **last**
   priority because it presupposes a well-formed body. Rationale for the overall order: reject
   malformed shape fast (cheap, no DB), then the one cross-aggregate reference check (one DB read).

The order is the reasoning frame; it does **not** require the implementation to short-circuit in
exactly this sequence (Pydantic aggregates). It dictates which loc each sad cell asserts.

### 1c. Cell enumeration (sad cells, parametrized for BOTH POST and PUT)

Each row below is a single parametrized case in the integration sad table, run once for POST and
once for PUT (PUT seeds a plant first). Outcome column is the HTTP verdict. Parametrize ids are
authoritative - the build agent uses these exact ids.

| # | Cell (dimension @ value) | Expected | Parametrize id |
|---|---|---|---|
| S1 | name = empty | **422** (name required) | `name-empty` |
| S2 | name = whitespace | **422** (trims to empty) | `name-whitespace` |
| S3 | name = over-120 | **422** (max_length) | `name-over-120` |
| S4 | species = over-200 | **422** | `species-over-200` |
| S5 | acquired_on = malformed | **422** (date parse) | `acquired-on-malformed` |
| S6 | pot_size_cm = below-min (0) | **422** (>= 1) | `pot-size-below-min` |
| S7 | pot_size_cm = above-max (501) | **422** (<= 500) | `pot-size-above-max` |
| S8 | pot_size_cm = non-int | **422** (int coercion) | `pot-size-non-int` |
| S9 | pot_material = invalid | **422** (enum) | `pot-material-invalid` |
| S10 | light_level = invalid | **422** (enum) | `light-level-invalid` |
| S11 | tags = over-long-tag (51-char item) | **422** (per-item <= 50) | `tag-over-long` |
| S12 | tags = too-many (51 items) | **422** (<= 50 items) | `tags-too-many` |
| S13 | notes = over-max (10001) | **422** | `notes-over-max` |
| S14 | location_id = nonexistent (valid int, no such room) | **422** id-only via `LocationNotFoundForPlantError` (**not 404**) | `location-id-nonexistent` |

S1-S13 are **schema-gate** sad cells; **S14 is the FK-existence-guard sad cell** and is the
headline 422-not-404 assertion (AC4). S14's assertion additionally checks the detail body is
`{"detail": ...}`, contains only the offending integer `location_id`, and leaks **no other
field** (SEC-001).

### 1d. Happy cells (asserted in §2, not in the sad table)

Happy cells assert **body shape + round-trip**, so they are explicit named tests, not parametrized
into the sad table:

| # | Cell | Asserts |
|---|---|---|
| H1 | full attributes: name + species + valid-existing location + acquired_on + pot_size_cm + each-valid pot_material + each-valid light_level + valid tags + notes + archived=false (absent) | 201 + full echoed body incl. `tags` list, `created_at`, `updated_at`, `archived=false`; round-trips via GET (AC1) |
| H2 | minimal homeless: name only, `location_id` absent/null, no tags | 201 + `location_id: null`, `tags: []`, `archived: false`; round-trips homeless (AC2) |
| H3 | dedup: `tags=["a","a","b"]` | 201 + persisted `tags` is the deduped set (`["a","b"]`, order per design) (AC1) |
| H4 | enum coverage: one happy per `PotMaterial` member and per `LightLevel` member | 201 + the wire value round-trips unchanged (D3) - small parametrized happy table over the valid enum members |
| H5 | archived=true explicitly | 201 + `archived: true` persisted + exposed (D5; no exclusion behavior) |

This matrix satisfies AC1, AC2, AC3, AC4.

---

## 2. Happy + sad inventory per surface (TEST-005)

Every public surface gets **>= 1 happy and >= 1 sad** test. Grouped by layer; "Test fn(s)" names
the owning function(s).

### 2a. REST endpoints (integration - primary)

File: `backend/tests/integration/test_plants_endpoint.py`
(`pytestmark = pytest.mark.integration`; reuses the existing `client` fixture from
`conftest.py` - migration `0003` now creates `plant` + `plant_tag`, so **no fixture change** is
needed). Each test seeds the rooms/plants it needs via the API within its own temp SQLite file
(TEST-006 independence; no shared seed, no global truncation).

| Endpoint | Happy | Sad | Test fn(s) |
|---|---|---|---|
| `POST /api/v1/plants` | H1 full (incl. room + tags + enums); H2 homeless; H3 dedup; H4 enum round-trip; H5 archived | S1-S13 schema matrix -> 422; **S14 nonexistent location_id -> 422 id-only (not 404)** | `test_post_creates_plant_full_and_round_trips`, `test_post_creates_homeless_plant`, `test_post_dedupes_tags`, `test_post_each_enum_value_round_trips[...]`, `test_post_archived_true_round_trips`, `test_post_validation_rejects_bad_body[<id>]`, `test_post_nonexistent_location_returns_422_not_404` |
| `GET /api/v1/plants` (list, no filter) | plants returned ordered by `name ASC`; empty store -> `[]` | (no error path; covered by empty-store + bad-param-type 422 in §2b filter table) | `test_list_returns_plants_ordered_by_name`, `test_list_empty_store_returns_empty_array` |
| `GET /api/v1/plants/{id}` | 200 with correct body incl. `tags` + `location_id` | unknown id -> 404, body `{"detail": ...}` **no PII** (only the id) | `test_get_one_returns_plant`, `test_get_unknown_id_returns_404_no_pii` |
| `PUT /api/v1/plants/{id}` | full-replace: changes scalar fields **and replaces the tag set** (old tags gone, new tags present); `updated_at` bumped (strictly >= original), `created_at` unchanged; reflected on subsequent GET | unknown plant id -> 404; invalid body -> 422 (S1-S13 matrix, PUT pass); **unknown location_id -> 422** (S14, PUT pass) | `test_put_full_replace_swaps_tags_and_bumps_updated_at`, `test_put_unknown_id_returns_404`, `test_put_validation_rejects_bad_body[<id>]`, `test_put_nonexistent_location_returns_422` |
| `DELETE /api/v1/plants/{id}` | 204 (no body); subsequent GET -> 404; **its `plant_tag` rows are gone** (CASCADE - cross-checked in §4) | unknown id -> 404 | `test_delete_removes_plant_then_get_404`, `test_delete_unknown_id_returns_404` |

Specific assertions:
- **422-not-404 (AC4):** S14 / `test_post_nonexistent_location_returns_422_not_404` asserts
  `status == 404` is **false** and `status == 422` is **true**, the detail names only the
  `location_id`, and no PII leaks. This is a critical-path (§4).
- **404 no-PII (AC6):** assert `status == 404`, `set(body.keys()) == {"detail"}`, the detail
  contains only the integer plant id, and the id used was never created.
- **Full-replace tag swap (AC6):** create with `tags=["a","b"]`, PUT with `tags=["c"]`, assert the
  GET reflects exactly `["c"]` (a is gone, b is gone, c present) - proves tag write/replace, not
  append.
- **`updated_at` bump (AC6):** capture from create, PUT a change, assert new `updated_at` >=
  original and `created_at` unchanged.

### 2b. Search / filter (integration, real DB) - AC5, D4

Same file (or a focused `test_plants_filter.py` if §2a approaches the 500-LOC hard max, QG-009).
All filter behavior is **integration-only** (the portable lowered-LIKE + EXISTS query is exactly
the kind of DB behavior that must be proven against a real engine, TEST-001). All params optional,
**AND-combined**, none -> all ordered by `name ASC`.

| Case | Setup -> assertion | Test fn |
|---|---|---|
| `q` matches name | seed plants, `?q=mons` returns those whose **name** contains it | `test_filter_q_matches_name` |
| `q` matches species | `?q=delicio` returns those whose **species** contains it | `test_filter_q_matches_species` |
| `q` case-insensitive | seed mixed-case name/species, `?q=MONS` and `?q=mons` return the same rows (lowered both sides, D4) | `test_filter_q_is_case_insensitive` |
| `location_id` exact | two rooms, `?location_id=<id>` returns only that room's plants | `test_filter_location_id_exact` |
| `homeless=true` | mix homeless + housed, `?homeless=true` returns **only null-location** plants | `test_filter_homeless_returns_only_orphans` |
| `tag` present | `?tag=rare` returns only plants having that tag (EXISTS on `plant_tag`) | `test_filter_tag_present` |
| `tag` absent (no match) | `?tag=ghost` (no plant has it) -> `[]` | `test_filter_tag_absent_returns_empty` |
| `species` substring | `?species=ficus` substring-matches species | `test_filter_species_substring` |
| **combined q + location_id + tag (AND, all-match)** | a plant matching all three is returned | `test_filter_combined_and_all_match` |
| **combined q + location_id + tag (AND, partial -> excluded)** | a plant matching only two of the three is **excluded** (proves AND, not OR) | `test_filter_combined_and_partial_excluded` |
| unknown `location_id` as **filter** | `?location_id=424242` (no such room) -> `[]`, **not an error** (D4; distinct from the create/update 422) | `test_filter_unknown_location_id_returns_empty` |
| no params -> all ordered | no query -> all plants, name ASC | (covered by `test_list_returns_plants_ordered_by_name`) |

The unknown-`location_id`-as-filter case is the deliberate contrast with S14: **as a body
reference it is 422; as a list filter it is an empty result**. Both must be present.

### 2c. The cross-entity SET-NULL test (integration, BOTH engines, ARCH-011) - AC7, D1

**The headline test of this change.** File: `test_plants_endpoint.py` (or a focused
`test_plant_location_lifecycle.py`). This proves the FK `ON DELETE SET NULL` action fires.

| Scenario | Assertion | Test fn |
|---|---|---|
| create room -> create plant in it (with tags) -> DELETE the room -> GET the plant | GET returns **200**, `location_id` is **null** (homeless), the plant **and its tags survive intact**, the plant is **NOT deleted** | `test_deleting_room_orphans_its_plants_to_homeless` |

**Dual-engine (ARCH-011, mandatory):** the SQLite path runs in the default suite via the `client`
fixture; the **PostgreSQL path runs the same assertion in CI against the Postgres service**
(cicd.md). The test is written so it executes on whichever engine the run targets - no
SQLite-only shortcut, no engine-specific SQL.

> **TEST-014 red note (D1):** on SQLite this test **fails before the `PRAGMA foreign_keys=ON`
> connect-listener fix in `engine.py`** is in place - SQLite silently ignores the FK action and
> the GET either errors or returns a stale `location_id`. That red is **useful, expected TEST-014
> evidence**: the backend lane records the failing run (this test name + the failing assertion)
> in the worklog, then adds the pragma to turn it green. See §9.

### 2d. The `plant_tag` CASCADE test (integration) - AC8, D2

Same file. Proves owned children are removed with the owner.

| Scenario | Assertion | Test fn |
|---|---|---|
| create a plant with tags -> DELETE the plant -> inspect persistence | the plant's `plant_tag` rows are **gone** (no orphans); a fresh GET-list does not surface the tags; (optionally assert via a direct inspect/count on `plant_tag` for the deleted id == 0) | `test_deleting_plant_cascades_its_tag_rows` |

The CASCADE also depends on the SQLite pragma (D1/D2); if authored before the pragma it is a
second TEST-014 red.

### 2e. OpenAPI codegen assertion (TEST-008) - integration, AC11

Same file (or `test_plants_openapi.py`); mirrors the Location OpenAPI test.

| Surface | Assertion | Test fn |
|---|---|---|
| `/api/v1/openapi.json` | `paths` contains `/api/v1/plants` and `/api/v1/plants/{plant_id}`; the **list query params** (`q`, `location_id`, `tag`, `species`, `homeless`) appear on the GET-list operation's parameters; `components.schemas` contains `PlantResponse` exposing exactly `id`, `name`, `species`, `location_id`, `acquired_on`, `pot_size_cm`, `pot_material`, `light_level`, `notes`, `tags`, `archived`, `created_at`, `updated_at` | `test_openapi_exposes_plant_paths_query_params_and_schema` |

Satisfies AC11 + TEST-008 (build-output assertion on the gitignored emitted schema).

### 2f. Migration `0003` (integration, dual-engine ARCH-011) - AC9

Extend `backend/tests/integration/test_migrations.py` (`pytestmark` already
`pytest.mark.integration`) with a **new** test fn. **Leave the existing `schema_meta` and
`location` assertions intact** - do not modify them.

| Surface | Happy | Reverse | Test fn |
|---|---|---|---|
| Migration `0003` | `upgrade head` -> `plant` table exists with the expected columns, **and** `plant_tag` exists with `(plant_id, tag)`; the FK on `plant.location_id` declares `ondelete="SET NULL"`, the `plant_tag` FK declares CASCADE | `downgrade` to `0002` -> both `plant` and `plant_tag` dropped, while `location` and `schema_meta` **remain** | `test_upgrade_creates_plant_tables_and_downgrade_drops_them` |

Use `sqlalchemy.inspect(engine)` (`get_table_names`, `get_columns("plant")`, `get_columns
("plant_tag")`, and `get_foreign_keys("plant")` / `get_foreign_keys("plant_tag")` to assert the
`ondelete` option) to verify the column set and FK actions. Cross-engine: SQLite here; Postgres in
CI (no separate Postgres-only file authored).

### 2g. Application use case (unit - sparse, TEST-004) - the FK guard

File: `backend/tests/unit/test_plant_use_case.py` (`pytestmark = pytest.mark.unit`; no app, no DB,
no I/O - TEST-002). `PlantService` is exercised against a **hand-written dict-backed fake
`PlantRepository`** implementing the port Protocol, whose `location_exists(id)` is backed by a
configurable set of "existing room ids" (allowed per TEST-003 - faking the port is not mocking the
real persistence layer).

| Behavior | Happy | Sad | Test fn |
|---|---|---|---|
| `create` with **homeless** (`location_id=None`) | passes the guard, delegates to `add`, returns the created `Plant` | - | `test_create_homeless_is_allowed` |
| `create` with **valid-existing** `location_id` | guard passes (`location_exists` true), returns created | - | `test_create_with_existing_location_is_allowed` |
| `create` with **nonexistent** `location_id` | - | raises `LocationNotFoundForPlantError` (the FK-existence guard, D1/ADR-B) | `test_create_nonexistent_location_raises` |
| `update` with nonexistent `location_id` | (existing-location update covered transitively) | raises `LocationNotFoundForPlantError` | `test_update_nonexistent_location_raises` |
| `update` / `get` / `delete` on unknown plant | - | propagates `PlantNotFoundError` from the port | `test_update_propagates_plant_not_found`, `test_get_propagates_plant_not_found`, `test_delete_propagates_plant_not_found` |

The FK-existence guard is the **only** economically-unit-reachable piece of pure logic and the
reason this unit file exists at all. **Explicitly NOT unit-tested:** the frozen `Plant` /
`NewPlant` / `PlantFilter` dataclasses, the `PotMaterial` / `LightLevel` enum members, and the
`PlantNotFoundError` / `LocationNotFoundForPlantError` constructors - asserting their attributes
would pass against any implementation (TEST-004 #2) and is noise. **No test of frozen dataclasses.**

### 2h. Repository methods (covered via integration, not separately unit-tested)

`SqlAlchemyPlantRepository.{add, list (filter), get, update, delete, location_exists}` are the
outbound adapter; per TEST-001/TEST-003 they are exercised **through the real-DB integration
slice** (2a-2f), where their happy+sad behavior (persist + tag write, portable filter query,
order-by-name, raise `PlantNotFoundError`, tag replace on update, CASCADE on delete, SET-NULL on
room delete, `location_exists`) is observed against a real database. No isolated repository unit
test is authored - it would need either a real DB (making it integration) or a mocked session
(TEST-003 forbids). Each repo method's sad path is reached through the unknown-id / nonexistent-fk
integration tests.

### 2i. Frontend API client functions (vitest) - the 5 client fns

File: `frontend/src/lib/api/plants.test.ts`, mirroring `locations.test.ts` (stub `fetch` via
`vi.stubGlobal`; `afterEach` restores). One happy + correct method/path/body + one `ApiError` sad
case per function. Each of the 5 client fns gets **>= 1 happy + >= 1 sad** (TEST-005).

| Function | Happy | Method/path/body | Sad | Test fn(s) |
|---|---|---|---|---|
| `fetchPlants(filter?)` | parses `Plant[]` on 200; **builds the query string** from `PlantFilter` (only set fields appended; `homeless=true` rendered; empty filter -> bare path) | GET `/api/v1/plants[?...]` | non-2xx -> `ApiError` | `returns parsed plants`, `builds query string from filter`, `omits unset filter fields`, `throws ApiError on non-2xx` |
| `fetchPlant(id)` | parses one `Plant` on 200 | GET `/api/v1/plants/{id}` | non-2xx -> `ApiError` (incl. 404) | `returns one plant`, `throws ApiError` |
| `createPlant(input)` | parses created `Plant` on 201 | POST `/api/v1/plants`, JSON body = `PlantInput` (incl. `tags`, enums, `location_id: null` for homeless) | non-2xx -> `ApiError` (incl. 422) | `posts and parses`, `sends correct body incl null location and tags`, `throws ApiError` |
| `updatePlant(id, input)` | parses updated `Plant` on 200 | PUT `/api/v1/plants/{id}`, JSON body | non-2xx -> `ApiError` | `puts and parses`, `throws ApiError` |
| `deletePlant(id)` | resolves `void` on 204 | DELETE `/api/v1/plants/{id}` | non-2xx -> `ApiError` | `deletes and resolves void`, `throws ApiError` |

The `fetchPlants` query-string builder is the one piece of real FE logic (D4 client side) and gets
explicit happy cases for set/unset/`homeless` fields.

### 2j. Frontend hook / page (vitest)

File: `frontend/src/features/plants/usePlants.test.ts` (mirrors `useLocations.test.ts` - tests the
hook owning `plants/loading/error` + `reload(filter)/create/update/remove`). `fetch` is stubbed
(`vi`); no real network.

| Behavior | Assertion | Test fn |
|---|---|---|
| Loads list on mount (happy, AC10) | after mount, `plants` reflects fetched rows; `error` null | `loads and exposes plants on mount` |
| Empty state (AC10) | fetch resolves `[]` -> hook exposes empty list | `exposes empty state when no plants` |
| Error state (sad, AC10) | fetch non-2xx -> hook exposes a human `error` (from `ApiError`), not a thrown exception | `surfaces error message on failed fetch` |
| Reload-with-filter contract (AC5/AC10) | `reload(filter)` re-fetches with the filter applied (assert the fetch was called with the filtered path) | `reloads the list with the active filter` |
| Mutation -> reload (AC10) | after `create`/`update`/`remove`, the hook reloads the list | `reloads the list after a create` |

(Create/edit/delete UI affordance journeys - incl. picking "No room (homeless)", enum selects,
tags input, filter controls - are the **deferred Playwright** scope, §8, not re-implemented as
jsdom interaction tests beyond the hook's mutation -> reload + reload-with-filter contract.)

---

## 3. Layer assignment per behavior (TEST-001 / TEST-002)

| Behavior | Layer | Why (HoneyComb) |
|---|---|---|
| POST happy (full / homeless / dedup / enums / archived) + round-trip | **Integration** | real persistence + tag write round-trip is the meaningful proof; primary layer |
| POST/PUT schema matrix S1-S13 | **Integration** (parametrized) | validation lives in the Pydantic schema wired into the app; exercise it through the app |
| 422-not-404 on nonexistent location_id (S14) | **Integration** + **Unit** | integration proves the wired 422 handler + id-only body; unit (2g) proves the service-level guard branch in isolation - the one pure decision worth a unit |
| List ordering + empty | **Integration** | ordering is a DB/repo concern; assert against real query result |
| Search/filter (each param + AND combos + unknown-loc -> []) | **Integration** | portable lowered-LIKE + EXISTS query is exactly real-DB behavior (D4); cannot be honestly unit-tested |
| GET-one happy + 404 no-PII | **Integration** | 404 = repo-raise + registered handler; needs the wired app |
| PUT full-replace + tag swap + updated_at bump + 404 + 422 | **Integration** | ORM `onupdate` + tag replace + handler + validation all in the slice |
| DELETE 204 + gone + 404 | **Integration** | persistence side-effect observed via real DB |
| **Room delete -> plants homeless (SET NULL)** | **Integration, BOTH engines** (ARCH-011) | the FK action only fires against a real engine; dual-engine is the whole point (D1) |
| **Plant delete -> tag rows gone (CASCADE)** | **Integration** | owned-child removal observed via real DB (D2) |
| OpenAPI paths/query-params/schema present | **Integration** (TEST-008) | asserts emitted build artifact from the real app |
| Migration `0003` up creates tables / down drops | **Integration** (ARCH-011) | real Alembic DDL on a real engine; FK ondelete inspected |
| `PlantService` FK-existence guard (homeless ok / nonexistent raises) | **Unit** (TEST-004) | the only pure decision logic worth isolating; fake-port keeps it I/O-free |
| `PlantService` plant-not-found propagation | **Unit** | propagation branch, cheap to isolate against the fake port |
| Domain dataclasses / enums / error ctors | **None** | would pass against any impl (TEST-004 #2) - noise; observed transitively |
| Repository methods | **Integration** (via 2a-2f) | real-DB is the only honest test; mocking the session is forbidden (TEST-003) |
| FE 5 API client fns + query-string builder | **vitest unit** | pure request-shaping + parse; `fetch` stubbed at the boundary |
| FE hook list/empty/error/reload-with-filter | **vitest unit** | state logic over a stubbed `fetch` |
| Full create(incl. homeless) -> filter -> edit -> delete UI journey | **Deferred E2E (Playwright)** | §8; no harness yet (deviation #4) |

---

## 4. Coverage targets (QG-002)

| Target | Floor | Scope |
|---|---|---|
| Overall coverage | **>= 85%** | union of unit + integration (pytest measures both together) |
| Diff-cover on new/changed code | **>= 80%** | all new backend + frontend files in this change (incl. the `engine.py` pragma listener) |
| Branch coverage - domain + application | **>= 95%** | `domain/plant.py`, `application/plants.py` (the FK-existence guard's both branches) |
| Branch coverage - adapters / outbound | **>= 80%** | `adapters/inbound/web/plants.py`, `adapters/outbound/db/plant_repository.py`, `models.py`, `engine.py` |
| **Critical-path 100%** | the **422 nonexistent-location guard** (S14, both POST and PUT), the **404 no-PII** path (GET/PUT/DELETE unknown plant), and the **ON DELETE SET NULL** path (room delete -> homeless) | AC4, AC6, AC7 are the trust-boundary + dual-engine-correctness behaviors. **Flagged critical:** every branch of the FK-existence guard, the not-found handler, and the SET-NULL lifecycle must be covered; the SET-NULL path additionally must run on **both engines** (the pragma branch in `engine.py` is part of this). |

The application/domain 95% branch floor is met by the §2g unit (both guard branches + plant
not-found) plus the §2a integration. The adapter floor is met by the §2a-2f integration bulk -
the portable filter query branches (each param present/absent, AND combinations) are all driven by
the §2b filter table.

**Required `pytestmark` per Python test file (TEST-012):**

| File | Marker |
|---|---|
| `backend/tests/integration/test_plants_endpoint.py` | `pytestmark = pytest.mark.integration` |
| `backend/tests/integration/test_plants_filter.py` (if split out) | `pytestmark = pytest.mark.integration` |
| `backend/tests/integration/test_plants_openapi.py` (if split out) | `pytestmark = pytest.mark.integration` |
| `backend/tests/integration/test_migrations.py` (extended) | `pytestmark = pytest.mark.integration` (already present) |
| `backend/tests/unit/test_plant_use_case.py` | `pytestmark = pytest.mark.unit` |

Frontend (`*.test.ts`) runs under **vitest**, no pytest marker (TEST-012). A Python test file
without a layer marker fails the gate - this is not optional.

**File-size watch (QG-009, 500-LOC test-file hard max):** `test_plants_endpoint.py` carries the
CRUD + matrix + lifecycle bulk and will be the largest file. If it approaches 500 LOC, split by
scenario group: `test_plants_filter.py` (the §2b search/filter table), and/or
`test_plants_openapi.py` (§2e). Keep the SET-NULL + CASCADE lifecycle tests with the CRUD core or
in a focused `test_plant_location_lifecycle.py` - do not let the headline test get buried.

---

## 5. Mocking boundary (TEST-003)

- **Integration tests:** real database (temp-file SQLite per test via the `client` fixture), real
  SQLAlchemy, real `SqlAlchemyPlantRepository`, real `PlantService`, real FastAPI app wired
  through its composition root. **Nothing internal is mocked.** No mocking of repositories, use
  cases, the session, or the persistence layer. There are no true external dependencies in this
  change (no third-party HTTP), so there is nothing legitimate to stub at all.
- **Unit test (`test_plant_use_case.py`):** the **only** fake is a hand-written dict-backed
  `PlantRepository` implementing the port Protocol, with a configurable `location_exists`. This is
  faking the **port**, not the real persistence layer - explicitly allowed by TEST-003 and the
  test seed.
- **Frontend (vitest):** the **only** stub is the global `fetch` (`vi.stubGlobal`), the true
  external boundary of the browser client. The `ApiError` parsing, the `fetchPlants` query-string
  builder, the request shaping, and the hook state logic run for real against the stubbed
  response.

Any deviation (e.g. monkeypatching a repository inside an integration test, or stubbing the FK
guard rather than driving a real nonexistent id) is a foundation violation and fails the
story-complete re-audit.

---

## 6. Search / filter + cross-entity + CASCADE - consolidated spec

(Restated here as a single checklist for the build agents; details in §2b-§2d.)

1. **Search/filter (§2b, integration, real DB):** `q`-name, `q`-species, `q`-case-insensitive,
   `location_id`-exact, `homeless=true`, `tag`-present, `tag`-absent, `species`-substring,
   combined q+location_id+tag **all-match** (returned), combined **partial** (excluded - proves
   AND), unknown `location_id`-as-filter -> `[]` (not error).
2. **Cross-entity SET-NULL (§2c, integration, BOTH engines, AC7):** create room -> create plant ->
   delete room -> plant GET 200 + `location_id` null + plant & tags intact + not deleted. **Red on
   SQLite without the `engine.py` pragma** (TEST-014 evidence, §9).
3. **`plant_tag` CASCADE (§2d, integration, AC8):** delete plant -> its tag rows gone.

---

## 7. Test count summary

| Layer | File | Approx test count |
|---|---|---|
| Integration - endpoints (CRUD) | `test_plants_endpoint.py` | ~12 explicit (5 happy POST groups + list x2 + get x2 + put x4 + delete x2) + **28 parametrized** (14 sad cells S1-S14 x POST/PUT) + the H4 enum-round-trip parametrized happy cases |
| Integration - search/filter | `test_plants_endpoint.py` (or `test_plants_filter.py`) | ~11 (the §2b table) |
| Integration - SET-NULL lifecycle (dual-engine) | (CRUD file or `test_plant_location_lifecycle.py`) | 1 (run on SQLite locally + Postgres in CI) |
| Integration - `plant_tag` CASCADE | (same) | 1 |
| Integration - OpenAPI | (same / `test_plants_openapi.py`) | 1 |
| Integration - migration `0003` | `test_migrations.py` (extended) | 1 new (existing schema_meta + location tests untouched) |
| Unit - service FK guard + propagation | `test_plant_use_case.py` | ~7 (homeless ok, existing ok, create-nonexistent raises, update-nonexistent raises, get/update/delete plant-not-found propagation) |
| vitest - API client | `plants.test.ts` | ~16 (5 fns x happy + sad, plus query-string builder set/unset/homeless + body assertions) |
| vitest - hook | `usePlants.test.ts` | ~5 (list, empty, error, reload-with-filter, mutation->reload) |
| **Deferred E2E** | (infra story) | 1 journey, recorded not built |

---

## 8. Deferred: E2E / Playwright (TEST-009 / TEST-010)

**Status: DEFERRED** to the dedicated frontend-infra story, per `proposal.md` deviation #4
(maintainer-approved at pickup), consistent with US-2.2: no Playwright harness exists yet, and
standing one up is a cross-cutting infra story, not Plant-specific. This change is covered instead
by the real-DB integration slice + targeted units + committed FE-012 breakpoint screenshots + the
orchestrator's prod-path smoke test.

**Recorded intended scenario (to be built by the infra story, not now):**

| Deferred E2E scenario | Discipline | Acceptance |
|---|---|---|
| Plants journey: open `/plants` -> Add plant **including the homeless path** (create with "No room (homeless)" selected, plus enums + tags) -> see it in the list -> **filter** (by room / tag / q) and see the list narrow -> Edit (change fields + tag set) -> see the change -> Delete (confirm dialog) -> it disappears | Drives **real UI affordances** only, never direct value injection (TEST-009); **runs against the backend-served production build** (the sprint-2 prod-path improvement - same artifact the orchestrator smoke-tests, not the dev server); **fails on any page error or error-level console output** (TEST-010); warnings ignored; any allowlisted console pattern needs an inline justification comment | The full create(incl. homeless) -> filter -> edit -> delete journey passes against the backend-served build with zero console errors |

FE-015 Audit-Spaces (axe a11y + perf budget) is deferred alongside it (same infra story).

---

## 9. TEST-014 - test-first red-run evidence (mandatory, per lane)

Test-first (PRIN-III) is **auditable from artifacts, not trusted from a claim** (TEST-014, added
this sprint). **Each build lane MUST record its failing-test run in `worklog.md` BEFORE the commit
that turns it green** - the test names plus the failing assertion/error output (the "red"). A
worklog showing no red-before-green is a PRIN-III deviation requiring comply-or-explain, and fails
the story-complete re-audit.

**Backend lane - required red entries (at minimum):**
1. The CRUD + matrix + filter tests failing against the **absent** `domain/plant.py` /
   `application/plants.py` / router / migration (import errors / 404s on the unregistered route /
   missing table) - the baseline red before the slice exists.
2. **The dual-engine SET-NULL test failing on SQLite for the FK reason** (`location_id` not
   nulled / stale) **before the `PRAGMA foreign_keys=ON` connect-listener is added to
   `engine.py`** (§2c). This specific red is the most valuable evidence in the story - it proves
   the cross-engine bug was real and the pragma fix is what closed it. Record the test name
   (`test_deleting_room_orphans_its_plants_to_homeless`) and the failing assertion (the observed
   non-null `location_id` / error) explicitly. The `plant_tag` CASCADE red (§2d) is recorded the
   same way if it precedes the pragma.
3. The FK-existence-guard unit + the 422-not-404 integration failing before `PlantService` /the
   handler exist - proving S14 was written first.

**Frontend lane - required red entries (at minimum):**
1. The `plants.test.ts` client-fn + query-string-builder tests failing against the absent
   `lib/api/plants.ts`.
2. The `usePlants.test.ts` hook tests failing against the absent `features/plants/usePlants.ts`.

Each lane's worklog entry follows the existing `TRACE-001` line format
(`time · actor · action · artifact · ref`), references TEST-014, and lists the failing test
names + the assertion/error text. The green commit comes after.

---

## 10. Re-audit / approval

This document is **authored**, not yet approved. The test-engineer **re-audits the implemented
tests against this foundation at story-complete** (DoD §3, QG-012): verifying every surface in §2
has its happy+sad, the §1 matrix is parametrized as specified (S1-S14 for both POST and PUT), the
§2b filter cases + the §2c dual-engine SET-NULL test + the §2d CASCADE test are present, the §3
layer assignments hold, the §4 coverage targets and `pytestmark` markers are met, the critical
paths (422 guard, 404 no-PII, SET-NULL) are at 100%, the §5 mocking boundary is not breached, and
**the §9 TEST-014 red-run evidence is in the worklog per lane** (notably the SQLite SET-NULL red
before the pragma). The test-foundation approval is recorded as part of the DoD gate; **no merge
occurs without it.**
