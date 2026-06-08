---
title: Test Foundation - location-crud (US-2.2)
type: test-foundation
change: location-crud
status: authored
date: 2026-06-08
author: test-engineer/HIGH
gates: SPEC-003 (pre-implementation), QG-002, TEST-001..TEST-013
---

# Test Foundation - location-crud (US-2.2)

This is the SPEC-003 pre-implementation artifact that gates implementation. The two build
agents (backend / frontend) write tests **red -> green** against the surfaces, names,
matrices, and coverage targets enumerated here. The test-engineer **re-audits against this
document at story-complete** and issues the test-foundation approval as part of the DoD
(QG-012, DoD §3); nothing merges until that approval is recorded.

It refines the architect's test plan seed into the authoritative foundation: explicit
input-state matrix (TEST-007), happy+sad inventory per surface (TEST-005), per-behavior layer
assignment with HoneyComb justification (TEST-001), coverage targets (QG-002), and the mocking
boundary (TEST-003). It names files, test functions, and matrix cells. It is a **planning
artifact** - it contains no test code.

The contract under test is `design.md §1` (REST/OpenAPI delta) and the ACs in `proposal.md`.

---

## 0. HoneyComb strategy for this change (TEST-001)

Location-CRUD is thin glue over a real database: the domain entities are frozen dataclasses,
the service methods are one-line port delegations, and the router maps domain types to Pydantic
responses. There is almost no pure logic. Per TEST-001 the **integration layer is primary** here:
a real-DB slice through router -> service -> repository -> SQLAlchemy -> SQLite exercises the
overwhelming majority of behavior (validation, ordering, persistence round-trip, 404/422
mapping, OpenAPI emission) in one economical layer.

Units are **sparse and surgical** (TEST-004): only the `LocationService` error-propagation and
mapping behavior gets a unit test, driven against a hand-written **fake of the port** (allowed -
this is not mocking the real persistence layer). The frozen domain dataclasses get **no** unit
test: a test asserting `Location(...).name == "..."` would pass against any implementation
(fails the meaningful-test bar TEST-004 #2) and is pure noise.

E2E (Playwright) is **deferred** (see §6) per the proposal's maintainer-approved deviation #2;
the journey is recorded as a deferred row, not built now.

The coverage floor (QG-002) is met by the **union** of unit + integration coverage (pytest
measures both together), so the integration bulk plus the targeted service unit clears the floor
without brittle implementation-mirror units.

---

## 1. Input-state matrix (TEST-007) - create / update validation

POST and PUT share the same request validation (`LocationCreate` / `LocationUpdate`, design §1:
`name` trimmed `min_length=1 max_length=120`, whitespace-only -> 422 via `field_validator`;
`notes` optional `max_length=2000`). This is **2 dimensions x 9 logical cells** -> qualifies for
an explicit matrix under TEST-007 (>= 6 logical cells).

**Dimensions:**
- `name` in { **empty** (`""`), **whitespace-only** (`"   "`), **valid** (`"Greenhouse"`) }
- `notes` in { **none** (omitted / `null`), **valid** (`"south-facing"`), **over-max** (2001 chars) }

**Named branch-priority order: `NAME_BEFORE_NOTES_FAIL_FAST`.**
`name` is the required field; its validation is evaluated/asserted **before** `notes`. When both
are invalid, the test asserts a 422 (Pydantic reports both error locs in one 422; the assertion
checks the response is 422 and that the `name` error loc is present). Rationale: name is the
required identity of the entity - fail fast on it; notes is optional decoration.

**Cell enumeration** (outcome = the validation verdict; the persisted/echoed result on success
is asserted separately per §2):

| # | name | notes | Expected | Note |
|---|---|---|---|---|
| C1 | valid | none | **2xx** (POST 201 / PUT 200) | baseline happy |
| C2 | valid | valid | **2xx** | happy with notes |
| C3 | valid | over-max | **422** | notes too long |
| C4 | empty | none | **422** | name required |
| C5 | empty | valid | **422** | name dominates |
| C6 | empty | over-max | **422** | name asserted first (fail-fast order) |
| C7 | whitespace | none | **422** | trims to empty -> required |
| C8 | whitespace | valid | **422** | trims to empty |
| C9 | whitespace | over-max | **422** | name asserted first |

**Parametrization:**
- The **sad** cells (C3-C9, seven cells) are driven by a single `pytest.mark.parametrize`
  table in the integration file, run **once for POST and once for PUT** (PUT runs against a
  seeded existing row so it reaches validation, not 404). Parametrize ids: `notes-over-max`,
  `empty-name-no-notes`, `empty-name-valid-notes`, `empty-name-over-max-notes`,
  `whitespace-name-no-notes`, `whitespace-name-valid-notes`, `whitespace-name-over-max-notes`.
- The **happy** cells C1/C2 are the explicit happy-path tests in §2 (not parametrized into the
  sad table - they assert body shape, not just status).

This matrix satisfies AC2 ("empty or whitespace-only name -> 422; notes over max -> 422").

---

## 2. Happy + sad inventory per surface (TEST-005)

Every public surface gets **>= 1 happy and >= 1 sad** test. Surfaces below are grouped by layer;
the "Where" column names the test file and the assertion's owning test function.

### 2a. REST endpoints (integration - primary)

File: `backend/tests/integration/test_locations_endpoint.py`
(`pytestmark = pytest.mark.integration`; reuses the existing `client` fixture - migration `0002`
now creates the `location` table, so no fixture change is needed).

| Endpoint | Happy | Sad | Test fn(s) |
|---|---|---|---|
| `POST /api/v1/locations` | C1/C2: 201 + body has `id`, `name`, `notes`, `created_at`, `updated_at`; round-trips via `GET /{id}` | C3-C9 via §1 matrix -> 422 | `test_post_creates_location_and_round_trips`, `test_post_validation_rejects_bad_body[<id>]` |
| `GET /api/v1/locations` (list) | rooms returned ordered by `name ASC`; empty store -> `[]` | (no error path for list; covered by empty-store edge) | `test_list_returns_rooms_ordered_by_name`, `test_list_empty_store_returns_empty_array` |
| `GET /api/v1/locations/{id}` | 200 with correct body for a seeded row | unknown id -> 404, body is `{"detail": ...}` with **no PII** (only the id) | `test_get_one_returns_location`, `test_get_unknown_id_returns_404_no_pii` |
| `PUT /api/v1/locations/{id}` | updates `name` + `notes`; `updated_at` changes (strictly greater than the original); reflected on subsequent `GET` | unknown id -> 404; invalid body -> 422 (§1 matrix, PUT pass) | `test_put_updates_name_notes_and_bumps_updated_at`, `test_put_unknown_id_returns_404`, `test_put_validation_rejects_bad_body[<id>]` |
| `DELETE /api/v1/locations/{id}` | 204 (no body); subsequent `GET /{id}` -> 404 | unknown id -> 404 | `test_delete_removes_location_then_get_404`, `test_delete_unknown_id_returns_404` |

Notes on specific assertions:
- **404 no-PII (AC4, SEC-001/PRIN-II):** assert `status_code == 404`, `response.json()` has key
  `detail`, and the detail string contains only the integer id - assert it does **not** leak any
  other field. Mirror the no-PII discipline; the unknown id used is one that was never created.
- **Ordering (AC3):** seed rooms out of alphabetical order (e.g. "Shed", "Attic", "Balcony")
  then assert the returned `name` sequence is sorted ascending. Do not rely on insertion order.
- **`updated_at` bump (AC5):** capture `updated_at` from the create response, PUT a change,
  assert the new `updated_at` differs from (is later than) the original. `created_at` must be
  unchanged.
- **Independence (TEST-006):** every test creates the rows it needs via the API within its own
  `client` (own temp SQLite file per test); no shared seed, no global truncation.

### 2b. OpenAPI codegen assertion (TEST-008) - integration

Same file (or a focused `test_locations_openapi.py`); `pytestmark = pytest.mark.integration`.
Mirrors `test_health_endpoint.py::test_openapi_docs_are_served_under_v1`.

| Surface | Assertion | Test fn |
|---|---|---|
| `/api/v1/openapi.json` | `paths` contains `/api/v1/locations` and `/api/v1/locations/{id}`; `components.schemas` contains `LocationResponse` (and that `LocationResponse` exposes `id`/`name`/`notes`/`created_at`/`updated_at`) | `test_openapi_exposes_location_paths_and_schema` |

Satisfies AC9 + TEST-008 (build-output assertion on the gitignored emitted schema).

### 2c. Migration (integration, dual-engine ARCH-011) - AC8

File: extend `backend/tests/integration/test_migrations.py` (`pytestmark` already
`pytest.mark.integration`) with a new test fn (do not modify the existing `schema_meta` test).

| Surface | Happy | Sad / reverse | Test fn |
|---|---|---|---|
| Migration `0002` | `upgrade head` -> `location` table exists with expected columns (`id`, `name`, `notes`, `created_at`, `updated_at`) | `downgrade base` (or downgrade to `0001`) -> `location` table dropped | `test_upgrade_creates_location_table_and_downgrade_drops_it` |

Use `sqlalchemy.inspect(engine).get_table_names()` and `get_columns("location")` to assert the
column set. **Cross-engine:** this guards the always-available SQLite path; the PostgreSQL path
runs the same migration in CI against the Postgres service (cicd.md / ARCH-011) - no separate
Postgres-only test file is authored here.

### 2d. Application use case (unit - sparse, TEST-004)

File: `backend/tests/unit/test_location_use_case.py` (`pytestmark = pytest.mark.unit`; no app,
no DB, no I/O - TEST-002). `LocationService` is exercised against a **hand-written dict-backed
fake `LocationRepository`** implementing the port Protocol (allowed per TEST-003 - faking the
port is not mocking the real persistence layer).

| Method | Happy | Sad | Test fn |
|---|---|---|---|
| `create` | maps `NewLocation(name, notes)` to the port `add` and returns the created `Location` | (validation lives in the schema layer, covered by integration; no service-level sad path) | `test_create_maps_new_location_and_returns_created` |
| `list` | returns the port's `list_all()` result unchanged | empty -> `[]` | `test_list_returns_all_locations` (incl. empty case) |
| `get` | returns the located `Location` | unknown id -> propagates `LocationNotFoundError` | `test_get_propagates_not_found` (+ happy in `test_get_returns_location`) |
| `update` | returns the updated `Location` | unknown id -> propagates `LocationNotFoundError` | `test_update_propagates_not_found` |
| `delete` | returns `None` on success | unknown id -> propagates `LocationNotFoundError` | `test_delete_propagates_not_found` |

The fake's `get`/`update`/`delete` raise `LocationNotFoundError(id)` for absent ids so the unit
test proves the **service propagates** the domain error without translation (the router/handler's
mapping to HTTP 404 is proven in 2a). This is the only economically-unit-reachable behavior;
everything else is covered more meaningfully in integration.

**Explicitly NOT unit-tested:** `Location` / `NewLocation` frozen dataclasses and the
`LocationNotFoundError` constructor - asserting their attributes would pass against any
implementation (TEST-004 #2) and is noise. Their behavior is observed transitively through the
integration round-trips.

### 2e. Repository methods (covered via integration, not separately unit-tested)

`SqlAlchemyLocationRepository.{add,list_all,get,update,delete}` are the outbound adapter; per
TEST-001/TEST-003 they are exercised **through the real-DB integration slice** (2a), which is
where their happy+sad behavior (persist, order-by-name, raise `LocationNotFoundError`, commit)
is observed against a real database. No isolated repository unit test is authored (it would
require either a real DB - making it an integration test - or a mocked session, which TEST-003
forbids). The 404 sad path per repository method is reached through the GET/PUT/DELETE
unknown-id integration tests.

### 2f. Frontend API functions (vitest)

File: `frontend/src/lib/api/locations.test.ts`, mirroring `health.test.ts` (stub `fetch` via
`vi.stubGlobal`; `afterEach` restores). One happy + correct method/path/body + one `ApiError`
sad case per function.

| Function | Happy | Method/path/body | Sad | Test fn(s) |
|---|---|---|---|---|
| `fetchLocations` | parses `Location[]` on 200 | GET `/api/v1/locations`, `Accept: application/json` | non-2xx -> `ApiError` | `returns parsed locations`, `calls GET locations`, `throws ApiError on non-2xx` |
| `fetchLocation` | parses one `Location` on 200 | GET `/api/v1/locations/{id}` | non-2xx -> `ApiError` | `returns one location`, `throws ApiError` |
| `createLocation` | parses created `Location` on 201 | POST `/api/v1/locations`, JSON body = `LocationInput` | non-2xx -> `ApiError` | `posts and parses`, `sends correct body`, `throws ApiError` |
| `updateLocation` | parses updated `Location` on 200 | PUT `/api/v1/locations/{id}`, JSON body | non-2xx -> `ApiError` | `puts and parses`, `throws ApiError` |
| `deleteLocation` | resolves `void` on 204 | DELETE `/api/v1/locations/{id}` | non-2xx -> `ApiError` | `deletes and resolves void`, `throws ApiError` |

### 2g. Frontend hook / page (vitest)

File: `frontend/src/features/rooms/useLocations.test.ts` (preferred - tests the hook owning
`locations/loading/error` + `reload/create/update/remove`). If a hook-level test is awkward to
mount, a `RoomsPage` component test is the accepted alternative. `fetch` is stubbed (`vi`); no
real network.

| Behavior | Assertion | Test fn |
|---|---|---|
| Renders / loads list (happy, AC7) | after mount load resolves, `locations` reflects the fetched rows | `loads and exposes locations on mount` |
| Empty state (AC7) | fetch resolves `[]` -> hook exposes empty list / page shows empty state | `exposes empty state when no rooms` |
| Error state (sad, AC7) | fetch rejects / non-2xx -> hook exposes a human `error` message (from `ApiError`), not a thrown exception | `surfaces error message on failed fetch` |

(Create/edit/delete UI affordance journeys are the **deferred Playwright** scope - §6 - not
re-implemented here as jsdom interaction tests beyond the hook's mutation -> reload contract,
which the `createLocation`/`updateLocation`/`deleteLocation` + `reload` calls cover.)

---

## 3. Layer assignment per behavior (TEST-001 / TEST-002)

| Behavior | Layer | Why (HoneyComb) |
|---|---|---|
| POST happy + body shape + round-trip | **Integration** | real persistence round-trip is the meaningful proof; primary layer |
| POST/PUT validation matrix (§1) | **Integration** (parametrized) | validation is in the Pydantic schema wired into the app; exercise it through the app |
| List ordering + empty | **Integration** | ordering is a DB/repository concern; assert against real query result |
| GET-one happy + 404 | **Integration** | 404 = repo-raise + registered handler mapping; needs the wired app |
| PUT happy + `updated_at` bump + 404 + 422 | **Integration** | ORM `onupdate` + handler + validation all in the slice |
| DELETE 204 + gone + 404 | **Integration** | persistence side-effect observed via real DB |
| OpenAPI paths/schema present | **Integration** (TEST-008) | asserts emitted build artifact from the real app |
| Migration up creates table / down drops | **Integration** (ARCH-011) | real Alembic DDL on a real engine |
| `LocationService` error propagation + create mapping | **Unit** (TEST-004) | the only pure logic worth isolating; fake-port keeps it I/O-free |
| Domain dataclasses / error ctor | **None** | would pass against any impl (TEST-004 #2) - noise |
| Repository methods | **Integration** (via 2a) | real-DB is the only honest test; mocking the session is forbidden (TEST-003) |
| FE API client functions | **vitest unit** | pure request-shaping + parse; `fetch` stubbed at the boundary |
| FE hook list/empty/error states | **vitest unit** | state logic over a stubbed `fetch` |
| Full create->list->edit->delete UI journey | **Deferred E2E (Playwright)** | §6; no harness yet (deviation #2) |

---

## 4. Coverage targets (QG-002)

| Target | Floor | Scope |
|---|---|---|
| Overall coverage | **>= 85%** | union of unit + integration (pytest measures both together) |
| Diff-cover on new/changed code | **>= 80%** | all new backend + frontend files in this change |
| Branch coverage - domain + application | **>= 95%** | `domain/location.py`, `application/locations.py` |
| Branch coverage - adapters / outbound | **>= 80%** | `adapters/inbound/web/*`, `adapters/outbound/db/*` |
| Critical-path 100% | the **404 no-PII** path and the **422 validation** path | AC4 + AC2 are trust-boundary behaviors (SEC-001/PRIN-II); every branch of the not-found handler and the name `field_validator` must be covered. Flagged here as the only 100% requirement. |

The application/domain branch floor (95%) is comfortably met by the §2d unit + §2a integration
combination: every service method's success and not-found branch is hit, and the schema
validator's empty/whitespace/over-max branches are all driven by the §1 matrix.

**Required `pytestmark` per Python test file (TEST-012):**

| File | Marker |
|---|---|
| `backend/tests/integration/test_locations_endpoint.py` | `pytestmark = pytest.mark.integration` |
| `backend/tests/integration/test_migrations.py` (extended) | `pytestmark = pytest.mark.integration` (already present) |
| `backend/tests/unit/test_location_use_case.py` | `pytestmark = pytest.mark.unit` |

Frontend (`*.test.ts`) runs under **vitest**, no pytest marker (TEST-012). A Python test file
without a layer marker fails the gate - this is not optional.

File-size watch (QG-009): `test_locations_endpoint.py` carries the bulk; if it approaches the
**500 LOC test-file hard max**, split by endpoint group (e.g. a separate `test_locations_validation.py`
for the parametrized matrix). Keep an eye on it but a single file is acceptable at the projected size.

---

## 5. Mocking boundary (TEST-003)

- **Integration tests:** real database (temp-file SQLite per test via the `client` fixture),
  real SQLAlchemy, real repository, real `LocationService`, real FastAPI app wired through its
  composition root. **Nothing internal is mocked.** No mocking of repositories, use cases, the
  session, or the persistence layer. There are no true external dependencies in this change
  (no third-party HTTP), so there is nothing legitimate to stub at all.
- **Unit test (`test_location_use_case.py`):** the **only** fake is a hand-written dict-backed
  `LocationRepository` implementing the port Protocol. This is faking the **port**, not the real
  persistence layer - explicitly allowed by TEST-003 and the test plan seed.
- **Frontend (vitest):** the **only** stub is the global `fetch` (`vi.stubGlobal`), the true
  external boundary of the browser client. The `ApiError` parsing, request shaping, and hook
  state logic run for real against the stubbed response.

Any deviation from this boundary (e.g. monkeypatching a repository inside an integration test)
is a foundation violation and fails the story-complete re-audit.

---

## 6. Deferred: E2E / Playwright (TEST-009 / TEST-010)

**Status: DEFERRED** to the dedicated frontend-infra story, per `proposal.md` deviation #2
(maintainer-approved at pickup): no Playwright harness exists yet, and standing one up is a
cross-cutting infra story, not Location-specific. This change is covered instead by the real-DB
integration slice + targeted units + committed FE-012 breakpoint screenshots.

**Recorded intended scenario (to be built by the infra story, not now):**

| Deferred E2E scenario | Discipline | Acceptance |
|---|---|---|
| Rooms journey: open `/rooms` -> Add room (create) -> see it in the list -> Edit (rename + notes) -> see the change -> Delete (confirm dialog) -> it disappears | Drives **real UI affordances** only, never direct value injection (TEST-009); **fails on any page error or error-level console output** (TEST-010); warnings ignored; any allowlisted console pattern needs an inline justification comment | The full create->list->edit->delete journey passes against a running app + real backend, with zero console errors |

FE-015 Audit-Spaces (axe a11y + perf budget) is deferred alongside it (same infra story).

---

## 7. Test count summary

| Layer | File | Approx test count |
|---|---|---|
| Integration - endpoints | `test_locations_endpoint.py` | ~11 explicit tests + 14 parametrized matrix cases (7 sad cells x POST/PUT) |
| Integration - OpenAPI | (same / `test_locations_openapi.py`) | 1 |
| Integration - migration | `test_migrations.py` (extended) | 1 |
| Unit - service | `test_location_use_case.py` | ~6 (create-map, list incl. empty, get happy+sad, update sad, delete sad) |
| vitest - API client | `locations.test.ts` | ~13 (5 functions x happy + sad, plus body/method assertions) |
| vitest - hook/page | `useLocations.test.ts` | 3 (list, empty, error) |
| **Deferred E2E** | (infra story) | 1 journey, recorded not built |

---

## 8. Re-audit / approval

This document is **authored**, not yet approved. The test-engineer **re-audits the implemented
tests against this foundation at story-complete** (DoD §3, QG-012): verifying every surface in
§2 has its happy+sad, the §1 matrix is parametrized as specified, the §3 layer assignments hold,
the §4 coverage targets and `pytestmark` markers are met, and the §5 mocking boundary is not
breached. The test-foundation approval is recorded as part of the DoD gate; no merge occurs
without it.
