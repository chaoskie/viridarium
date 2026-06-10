---
title: Test Foundation - care-schedules (US-3.1)
type: test-foundation
change: care-schedules
status: authored
date: 2026-06-10
---

# Test Foundation - care-schedules (US-3.1)

Pre-implementation test foundation for the `CareSchedule` owned-child aggregate of Plant
(SPEC-003 artifact gating). First E3 story, config only - the schedule is *stored and
user-editable*; due computation (US-3.3), event logging (US-3.2), and snooze/skip (US-3.6)
are out of scope. Authored by `test-engineer/HIGH` against `design.md` (decisions CS1-CS5,
the REST delta, the file plan) and `proposal.md` (scope, AC1-AC10, the two PO decisions).

This document is **prescriptive** (input matrices, named cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. The build agents (backend
lane, frontend lane) implement against it and record the TEST-014 red per lane before
turning it green. The story-complete pass re-audits the implementation against this
foundation and issues the approval (DoD §3).

Two **critical** lanes for this story (flagged 100% in §11):
1. The `(plant, care_type)` **uniqueness invariant** - the headline (AC2); a second PUT
   must replace, never add a second row.
2. The **404 no-PII** discipline - every 404/422 reject body carries `{"detail"}` keyed by
   id + care_type only, never the plant name or any free-text PII (AC6, DoR item 6).

---

## 1. Surface inventory (what gets a happy + a sad, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test. The four endpoints and
the four service methods are the behaviour-bearing surfaces.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| E1 | `PUT /plants/{id}/schedules/{care_type}` (upsert) | endpoint | 200 create-or-replace + body | 404-plant / 422 enum / 422 range / 422 extra-field |
| E2 | `GET /plants/{id}/schedules` (list 0-2) | endpoint | 200 ordered water-then-feed | 404-plant |
| E3 | `GET /plants/{id}/schedules/{care_type}` | endpoint | 200 one schedule | 404-plant / 404 no-schedule / 422 enum |
| E4 | `DELETE /plants/{id}/schedules/{care_type}` | endpoint | 204 | 404-plant / 404 no-schedule / 422 enum |
| S1 | `CareScheduleService.upsert` | use case | persist (returns domain) | `PlantNotFoundForScheduleError` (plant-exists guard) |
| S2 | `CareScheduleService.list` | use case | rows for plant | `PlantNotFoundForScheduleError` (plant-exists guard) |
| S3 | `CareScheduleService.get` | use case | returns row | `CareScheduleNotFoundError` propagates |
| S4 | `CareScheduleService.delete` | use case | row gone | `CareScheduleNotFoundError` propagates |
| F1 | `fetchSchedules / upsertSchedule / deleteSchedule` | FE client | PUT path/body, GET, DELETE | `ApiError` on non-2xx |
| F2 | `useCareSchedules` hook | FE hook | reload / upsert→reload / remove→reload | error propagation |
| F3 | `CareScheduleModal` no-winter-interval hint | FE component | hint shows + dismisses | (component assertion; Playwright deferred §10) |

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Integration is the primary layer** (TEST-001). The real-DB slice through
  router → `CareScheduleService` → `SqlAlchemyCareScheduleRepository` → SQLAlchemy →
  SQLite carries the bulk of coverage: every endpoint, the **uniqueness/idempotent-replace
  headline**, the list ordering, the dormancy default+override matrix, the allow-null
  winter-interval case, the `enabled` default, all 404/422 rejects, and the OpenAPI shape.
  No filesystem this story (unlike photos) - the slice is router→service→repo→DB only.
- **Unit only where integration cannot economically reach** (TEST-001 (b)):
  - `CareScheduleService` orchestration against a **fake `CareScheduleRepository`** - the
    `plant_exists` guard (upsert/list → `PlantNotFoundForScheduleError`) and the
    not-found propagation (get/delete → `CareScheduleNotFoundError`). These pin the
    error-type mapping cheaply without standing up the app. The same behaviour is re-proven
    end-to-end as 404s in integration.
  - The frozen domain dataclasses + the `CareType`/`Dormancy` StrEnums get **no unit test
    of their own** (TEST-004 #2: a pure-data assertion would pass against any
    implementation). The *dormancy-default-by-care-type* logic lives in the router
    (`_to_new_schedule`) and is observed through the integration matrix §5e, not a unit.
- **Dual-engine** (`test_fk_cross_engine.py`): the care_schedule-row CASCADE on the
  **real engine** resolved from `DATABASE_URL` (the CI postgres leg proves CASCADE on both
  engines), mirroring the existing tag/photo cascade tests.
- **Migration** (`test_migrations.py`): `0005` up/down DDL on the always-available SQLite
  path; CI runs the postgres leg.
- **Acceptance (Playwright, TEST-009): DEFERRED** to the infra story (proposal deviation
  #2), covered here by integration + the prod-path smoke + FE-012 screenshots. The
  intended journey is recorded in §10 but **not built**. The no-winter-interval hint is
  asserted as a component-level test (§8c) in the interim.

---

## 3. Backend unit: `test_care_schedule_use_case.py` (`unit`)

`pytestmark = pytest.mark.unit`. `CareScheduleService.upsert/list/get/delete` against a
hand-written **fake `CareScheduleRepository`** (TEST-003: faking the port is allowed; only
the real persistence layer must not be mocked in *integration*). The fake mirrors the
`_FakePlantRepository` pattern: dict-backed by `(plant_id, care_type)`, a configurable set
of "existing plant ids" backing `plant_exists`, and `upsert` overwriting any existing row
for the same key (so even at the fake level a second upsert never adds a row).

The only economically-unit-reachable logic is the **plant-exists guard** and the
**not-found propagation** (mirrors `test_plant_use_case.py`'s FK-guard + propagation).

| test | setup | expectation |
|---|---|---|
| `test_upsert_with_existing_plant_persists` | `plant_exists` → True | returns a `CareSchedule` carrying the upserted values (happy guard branch) |
| `test_upsert_replaces_same_key_in_fake` | upsert water twice, different `interval_days` | `list` returns exactly **one** water row with the **second** value (the invariant holds even in the fake; documents the contract) |
| `test_upsert_missing_plant_raises` | `plant_exists` → False | raises `PlantNotFoundForScheduleError`; `.plant_id` carries the queried id; repo.upsert **not** reached |
| `test_list_with_existing_plant_returns_rows` | `plant_exists` → True, two rows | returns water-then-feed (service pass-through; ordering is the repo's job, asserted in integration) |
| `test_list_missing_plant_raises` | `plant_exists` → False | raises `PlantNotFoundForScheduleError`; repo.list **not** reached |
| `test_get_propagates_care_schedule_not_found` | repo.get raises `CareScheduleNotFoundError` | the error propagates unchanged (service does not swallow/remap); `.plant_id` + `.care_type` carried |
| `test_get_happy_returns_row` | row present | returns the domain `CareSchedule` |
| `test_delete_propagates_care_schedule_not_found` | repo.delete raises `CareScheduleNotFoundError` | propagates unchanged |
| `test_delete_happy_removes_row` | row present | repo.delete called; no error |

**Guard-order note** (design `application/care_schedules.py`): `upsert`/`list` check
`plant_exists` **first** → `PlantNotFoundForScheduleError`; only then do they touch the
repo. `get`/`delete` do **not** pre-check the plant - they let the repo raise
`CareScheduleNotFoundError` (a missing schedule and a missing plant both surface as 404 at
the boundary; §5d covers both at the endpoint).

---

## 4. Backend integration: `test_care_schedules_endpoint.py` (`integration`)

`pytestmark = pytest.mark.integration`. Real DB, nothing internal mocked (TEST-003). Each
test seeds its own plant via the API (`POST /api/v1/plants {"name": ...}`) for TEST-006
independence. JSON bodies via the TestClient (`client.put(url, json={...})`).

### 4a. Fixtures / helpers (call out for the build agent)

No fixture change needed beyond the existing `client` (no filesystem this story). Provide
module-level helpers mirroring `test_photos_endpoint.py`:
- `_make_plant(client, name="Fern") -> int` - POST a plant, return its id.
- `_schedules_url(plant_id) -> str` → `/api/v1/plants/{plant_id}/schedules`.
- `_EXPECTED_RESPONSE_KEYS = {plant_id, care_type, interval_days, winter_interval_days,
  dormancy, enabled, created_at, updated_at}` - note **no `id`** (ARCH-007, AC10).

### 4b. HEADLINE - `(plant, care_type)` uniqueness / idempotent replace (AC1/AC2)

The single most important test of this story. The DB unique constraint is structurally
unhittable from the API (keyed PUT, CS1), so the *behavioural* proof is: a second PUT to
the same `care_type` **replaces** and never adds a second row.

| test | input | expectation |
|---|---|---|
| `test_put_water_twice_replaces_never_adds_a_second_row` | `PUT .../water {interval_days: 7}` then `PUT .../water {interval_days: 14}` | both 200; `GET .../schedules` returns **exactly one** `water` row, and its `interval_days == 14` (the **second** value). Assert `len(list) == 1` **and** the value - the create-or-replace, never-a-2nd-row invariant. |

This is **critical-100%** (§11). The assertion is on the observable list count + value, not
on the DB constraint directly (the constraint is also proven structurally by the migration
test §7).

### 4c. PUT / GET happy inventory (AC1)

| test | asserts |
|---|---|
| `test_put_water_creates_and_returns_body` | `PUT .../water {interval_days: 7}` → 200; body keys == `_EXPECTED_RESPONSE_KEYS` (**no `id`**); `plant_id` matches; `care_type == "water"`; `interval_days == 7`; `created_at`/`updated_at` present |
| `test_put_feed_creates_second_schedule` | after creating water, `PUT .../feed {interval_days: 30}` → 200; `GET .../schedules` returns **two** rows |
| `test_get_list_empty_when_none` | fresh plant → `GET .../schedules` → 200, `[]` (0 rows) |
| `test_get_list_orders_water_then_feed` | create feed first, then water; `GET .../schedules` → list ordered **water, then feed** (portable `case()` order, design repo) regardless of insert order |
| `test_get_single_returns_one` | `GET .../water` after creating it → 200, single object (not a list), keys == `_EXPECTED_RESPONSE_KEYS` |
| `test_put_replace_updates_value` | `PUT .../water` twice; `GET .../water` reflects the second `interval_days`; `updated_at >= created_at` |
| `test_enabled_defaults_true` | `PUT .../water {interval_days: 7}` (no `enabled`) → body `enabled is true` (AC6) |
| `test_enabled_explicit_false_persists` | `PUT .../water {interval_days: 7, enabled: false}` → body `enabled is false`; survives a `GET` |

### 4d. DELETE (AC6)

| test | asserts |
|---|---|
| `test_delete_then_get_404` | create water; `DELETE .../water` → 204 (empty body); subsequent `GET .../water` → 404 |
| `test_delete_leaves_sibling` | create water + feed; `DELETE .../water` → 204; `GET .../schedules` still returns the `feed` row |

### 4e. Dormancy default + override matrix (AC4, TEST-007)

This use case has **≥6 logical cells** (care_type × dormancy-input), so it gets an explicit
input-state matrix with named branch-priority order, driven by `pytest.mark.parametrize`.

**Branch-priority order** (design CS2, router `_to_new_schedule`): if the body supplies a
`dormancy` value, it **wins** (user-editable, PO Q1); otherwise the **care-type default**
applies - `feed → paused`, `water → winter_interval`. The due engine (US-3.3) reads this
one field and never branches on care_type, so the *default-at-the-boundary* must be proven.

Dimensions: **{care_type: water, feed} × {dormancy-input: omitted, paused, winter_interval}**.

| id | care_type | dormancy in body | expected stored `dormancy` | proves |
|---|---|---|---|---|
| `omitted-feed` | feed | (omitted) | `paused` | **default**: feed → paused (named cell) |
| `omitted-water` | water | (omitted) | `winter_interval` | **default**: water → winter_interval (named cell) |
| `explicit-feed-winter` | feed | `winter_interval` | `winter_interval` | **override persists**: a winter-grower keeps feeding (named cell) |
| `explicit-water-paused` | water | `paused` | `paused` | **override persists**: water can pause (named cell) |
| `explicit-feed-paused` | feed | `paused` | `paused` | explicit == default still persists |
| `explicit-water-winter` | water | `winter_interval` | `winter_interval` | explicit == default still persists |

Test name `test_dormancy_default_and_override_matrix` parametrized over the six rows;
asserts the **stored** value via a follow-up `GET` (round-trip, not just the PUT echo).

### 4f. allow-null-winter-interval (AC5, CS3, PO Q2)

| test | input | expectation |
|---|---|---|
| `test_winter_interval_dormancy_with_null_days_is_accepted` | `PUT .../water {interval_days: 7, dormancy: "winter_interval", winter_interval_days: null}` | **200** (NOT 422); body `winter_interval_days is null`, `dormancy == "winter_interval"`. No cross-field validation. This is the explicit no-422 contract (spec "uses the winter interval *if set*"). |
| `test_winter_interval_dormancy_with_days_persists` | same but `winter_interval_days: 21` | 200; `winter_interval_days == 21` |

### 4g. Validation / 422 inventory (AC3)

| test | input | expectation |
|---|---|---|
| `test_put_bad_care_type_path_returns_422` | `PUT .../schedules/banana` | 422 (path enum `CareType` auto-422); `{"detail"}` only |
| `test_get_bad_care_type_path_returns_422` | `GET .../schedules/banana` | 422 |
| `test_delete_bad_care_type_path_returns_422` | `DELETE .../schedules/banana` | 422 |
| `test_interval_days_zero_returns_422` | `PUT .../water {interval_days: 0}` | 422 (ge=1) |
| `test_interval_days_negative_returns_422` | `PUT .../water {interval_days: -1}` | 422 |
| `test_interval_days_over_max_returns_422` | `PUT .../water {interval_days: 3651}` | 422 (le=3650) |
| `test_winter_interval_days_out_of_range_returns_422` | `PUT .../water {interval_days: 7, winter_interval_days: 3651}` | 422 (le=3650 when present) |
| `test_bad_dormancy_value_returns_422` | `PUT .../water {interval_days: 7, dormancy: "hibernate"}` | 422 (enum) |
| `test_care_type_in_body_returns_422` | `PUT .../water {interval_days: 7, care_type: "feed"}` | 422 (`extra="forbid"`; care_type is path-only, design CS1) |

(Boundary-valid companions, proven via the happy cases above: `interval_days == 1` and
`interval_days == 3650` are accepted; not re-listed as separate sad tests.)

### 4h. 404 inventory + no-PII discipline (AC6 - CRITICAL)

| test | input | expectation |
|---|---|---|
| `test_put_unknown_plant_returns_404` | `PUT /plants/999999/schedules/water {...}` | 404 |
| `test_get_list_unknown_plant_returns_404` | `GET /plants/999999/schedules` | 404 |
| `test_get_single_unknown_plant_returns_404` | `GET /plants/999999/schedules/water` | 404 |
| `test_delete_unknown_plant_returns_404` | `DELETE /plants/999999/schedules/water` | 404 |
| `test_get_unknown_schedule_returns_404` | real plant, `GET .../feed` when no feed schedule exists | 404 |
| `test_delete_unknown_schedule_returns_404` | real plant, `DELETE .../water` when none exists | 404 |

**No-PII (critical-100%, §11):** for **every** 404 above, assert the JSON body keys are
exactly `{"detail"}` and the detail is **id + care_type only** - it MUST NOT echo the plant
name. Seed the plant with a distinctive name (e.g. `"Secret Orchid"`) and assert that
string is **absent** from `response.text` on the unknown-schedule 404 (SEC-007 / DoR item
6). Care_type and the plant id are non-PII identifiers and may appear.

### 4i. OpenAPI assertion (TEST-008, AC10)

| test | asserts |
|---|---|
| `test_openapi_exposes_schedule_paths_and_schema_omits_id` | the emitted `/api/v1/openapi.json` `paths` contain `/api/v1/plants/{plant_id}/schedules` and `/api/v1/plants/{plant_id}/schedules/{care_type}` (both the list and the keyed path); `components.schemas.CareScheduleResponse.properties` keys == `{plant_id, care_type, interval_days, winter_interval_days, dormancy, enabled, created_at, updated_at}` and **does NOT contain `id`** (ARCH-007) |

The design's REST delta lists four logical operations across **two** path templates
(`schedules` carries GET-list; `schedules/{care_type}` carries GET/PUT/DELETE). The test
asserts both path templates are present and that the keyed path exposes the PUT + DELETE +
GET methods.

---

## 5. Dual-engine: edit `test_fk_cross_engine.py` (`integration`)

Add one test mirroring `test_deleting_a_plant_cascades_its_photo_rows`, resolving the
engine from `DATABASE_URL` via the existing `fk_engine` fixture (SQLite locally,
PostgreSQL on the CI postgres leg):

| test | asserts |
|---|---|
| `test_deleting_a_plant_cascades_its_care_schedule_rows` | build a plant via `SqlAlchemyPlantRepository`; upsert a water + a feed schedule via `SqlAlchemyCareScheduleRepository` (add a `_count_care_schedule_rows` helper counting `CareScheduleModel.plant_id == plant.id`, mirroring `_count_photo_rows`); assert the count is 2; delete the plant; assert the care_schedule-row count is `0` (FK `ON DELETE CASCADE` fired on the **real engine**, AC7). Self-contained: cleans up its own rows; no shared postgres state. |

**Scope note:** this proves the DB-row CASCADE on **both** engines. No app-level cleanup
half this story (no files), so the SQLite endpoint suite does not need a separate
plant-delete-cascades-schedules test - the dual-engine test is the cascade proof.

---

## 6. Migration: edit `test_migrations.py` (`integration`)

Mirror the existing `0004` (photo) up/down test. `0005` down_revision is `0004`.

| test | asserts |
|---|---|
| `test_upgrade_creates_care_schedule_table_and_downgrade_drops_it` | upgrade head; `inspect(engine)` shows the `care_schedule` table with columns `{id, plant_id, care_type, interval_days, winter_interval_days, dormancy, enabled, created_at, updated_at}`; the FK to `plant` is `ON DELETE CASCADE`; an index on `plant_id` (`ix_care_schedule_plant_id`); a **unique constraint on `(plant_id, care_type)`** (`uq_care_schedule_plant_id_care_type`) - inspect via `get_unique_constraints` / unique indexes for the tuple `("plant_id", "care_type")`. Downgrade to `0004` drops `care_schedule` but leaves `photo`/`plant`/`plant_tag`. |

The unique-constraint assertion is the **structural** half of the AC2 headline (the
behavioural half is §4b). CI runs the same DDL on the postgres leg (no separate test).

---

## 7. Frontend (vitest)

Mirror `photos.test.ts` / `usePhotos.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson`/`fail` helpers, `afterEach(unstubAllGlobals + restoreAllMocks)`. **fetch is the
mock boundary** (TEST-003 FE equivalent - no MSW needed for these unit-level client/hook
tests). A `SAMPLE: CareSchedule` constant carries the full response shape (no `id`).

### 7a. `careSchedules.test.ts`

| test | asserts |
|---|---|
| `test fetchSchedules GETs the collection path` | `GET /api/v1/plants/{id}/schedules`, `Accept: application/json`; resolves the parsed array |
| `test upsertSchedule PUTs the keyed path with the JSON body` | `upsertSchedule(plantId, careType, input)` calls `fetch` with method **PUT**, path `/api/v1/plants/{id}/schedules/{careType}`, `Content-Type: application/json`, body == `JSON.stringify(input)` (carrying `interval_days`/`winter_interval_days`/`dormancy`/`enabled`, **no `care_type`** - it is in the path) |
| `test deleteSchedule DELETEs the keyed path` | `DELETE /api/v1/plants/{id}/schedules/{careType}`; resolves void on 204 |
| `test fetchSchedules throws ApiError on non-2xx (incl. 404)` | a 404 response → rejects `instanceof ApiError` |
| `test upsertSchedule throws ApiError on non-2xx (incl. 422)` | a 422 response → rejects `instanceof ApiError` |
| `test deleteSchedule throws ApiError on non-2xx (incl. 404)` | a 404 response → rejects `instanceof ApiError` |

### 7b. `useCareSchedules.test.ts`

| test | asserts |
|---|---|
| `test reload populates schedules and clears loading/error` | mount → fetch list → `schedules` populated, `loading` false, `error` null |
| `test empty when the plant has no schedules` | list `[]` → `schedules == []`, no error |
| `test upsert PUTs then reloads (mutation→reload contract)` | `upsert(careType, input)` → fetch call #2 is a **PUT** to the keyed path, then a reload; the updated schedule appears (mirrors the `usePhotos` upload→reload pattern) |
| `test remove DELETEs then reloads` | `remove(careType)` → fetch call #2 is a **DELETE** to the keyed path, then a reload; the row disappears |
| `test surfaces a human error on a failed load` | mount fetch fails (500) → `error` not null, `schedules == []` |
| `test propagates an error on a failed upsert` | upsert returns 422 → the hook surfaces a non-null `error` (mutation error propagation) |

### 7c. `CareScheduleModal` no-winter-interval hint (AC9, component assertion)

The dismissible hint is the FE-side of PO Q2 (CS3). Playwright is deferred (§10), so cover
it with a component-level vitest/RTL assertion:

| test | asserts |
|---|---|
| `test hint shows when winter_interval dormancy + empty winter interval` | render the modal section with `dormancy == "winter_interval"` and the winter-interval field empty → a small **non-blocking** hint is visible (the form is still submittable; the hint is not an error) |
| `test hint hides when a winter interval is set` | set the winter-interval field → the hint disappears |
| `test hint is dismissible` | click the hint's dismiss control → it disappears and stays gone for that session; submitting is never blocked by the hint |

This is a component assertion only (noted per the seed); the full journey is the deferred
Playwright §10.

---

## 8. Mocking boundary (TEST-003) - explicit

- **Integration (`test_care_schedules_endpoint.py`):** real DB through the real
  composition root. Nothing internal mocked - no faked repository, service, or session.
  The uniqueness/replace, the dormancy defaults, and the 404 no-PII checks are only
  meaningful end-to-end against the real DB.
- **Dual-engine / migration:** real engines (SQLite local, Postgres CI), real Alembic.
- **Unit (`test_care_schedule_use_case.py`):** a fake `CareScheduleRepository` only
  (faking the port is allowed; the fake's `plant_exists` is backed by a configurable set).
  No app, no DB, no I/O.
- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. The
  component-hint test (§7c) renders the real React component (RTL), no network.

---

## 9. Coverage targets (QG-002)

- **Overall floor 85%**; **new/changed code ≥80% diff-cover**.
- **Branch coverage:** **≥95% in domain + application** (`domain/care_schedule.py`,
  `application/care_schedules.py` - the plant-exists guard + propagation branches),
  **≥80% in adapters/outbound** (`care_schedule_repository.py` - the select-then-write
  upsert update-vs-insert branch, the water-first `case()` ordering).
- **Critical paths flagged 100%** (spec-flagged → QG-002 100%):
  1. **`(plant, care_type)` uniqueness / idempotent replace** (§4b headline, AC2) - a
     second PUT replaces, never adds a second row; structurally backed by the unique
     constraint (§6).
  2. **404 no-PII** (§4h, AC6) - every 404/422 reject returns a `{"detail"}` body keyed by
     id + care_type only, with **no plant name / free-text PII** echoed.
- The combined pytest run (unit + integration) scores the union (TEST-001); the integration
  bulk plus the targeted service unit clears the floor without brittle
  implementation-mirroring units (TEST-004).

---

## 10. Playwright (TEST-009) - DEFERRED, journey recorded only

Per proposal deviation #2 (FE-015 Audit Spaces + TEST-009 Playwright deferred to the infra
story), the acceptance test is **not built here**, covered instead by integration + the
prod-path smoke + FE-012 screenshots. The intended journey, recorded so the future story
can implement it verbatim:

1. From the plants page, click the **Schedules** ghost button on a plant card → the
   schedules modal opens (the water + feed sections visible, empty state).
2. In the water section: set `interval_days` (e.g. 7), leave defaults → submit → the value
   **persists** (re-open the modal, the 7 is still there).
3. Replace it: change the water interval (e.g. to 14) → submit → the new value persists
   and there is still exactly one water schedule (the uniqueness/replace behaviour visible
   in the UI).
4. Set the water section's dormancy to `winter_interval` and leave the winter-interval
   field empty → the **small dismissible hint** appears (non-blocking); fill the winter
   interval → the hint disappears; or click dismiss → the hint goes away and submit still
   works.
5. **Console-error fail-on (TEST-010):** the journey fails on any page error or
   error-level console output; warnings ignored; any allowlist needs an inline
   justification.

The driver MUST use real UI affordances (real inputs, real buttons) - never inject values
directly.

---

## 11. Required pytest markers (TEST-012)

Module-level `pytestmark` on every new/edited Python test file:
- `test_care_schedule_use_case.py` → `pytestmark = pytest.mark.unit`
- `test_care_schedules_endpoint.py` → `pytestmark = pytest.mark.integration`
- `test_fk_cross_engine.py` (edited) → already `pytestmark = pytest.mark.integration`
- `test_migrations.py` (edited) → already `pytestmark = pytest.mark.integration`

Frontend `*.test.ts` run under vitest (no marker). File-size: keep
`test_care_schedules_endpoint.py` under the QG-009 **500-LOC hard max**; if it grows past
that, split by group (happy/replace / dormancy-matrix / validation-sad / 404+openapi).

---

## 12. TEST-014 - Test-first evidence (the red), per lane

Test-first is **auditable from artifacts, not trusted from a claim** (TEST-014). Each lane
records, in `worklog.md`, the **failing run that precedes the implementation** - the test
names plus the failing assertion/error output (the "red") - before the commit that turns
them green:

- **Backend lane red:** run `test_care_schedule_use_case.py`,
  `test_care_schedules_endpoint.py`, the new
  `test_fk_cross_engine.py::test_deleting_a_plant_cascades_its_care_schedule_rows`, and the
  `0005` migration test against the *unimplemented* code → expect collection/import errors
  or assertion failures (no `domain.care_schedule`, no `/schedules` routes, no
  `care_schedule` table). Capture the names + the first failing line per group.
- **Frontend lane red:** run `careSchedules.test.ts` + `useCareSchedules.test.ts` (+ the
  `CareScheduleModal` hint test) against the *unimplemented* `lib/api/careSchedules.ts` /
  `useCareSchedules.ts` / `CareScheduleModal.tsx` → expect module-not-found / assertion
  failures. Capture the names + errors.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain.

---

## 13. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this
foundation and issues the **test-foundation approval** (DoD §3 item: "Test-foundation
re-audit approved"), checking:
- Every surface in §1 has its happy + sad (TEST-005); the dormancy matrix §4e is present
  and **parametrized** with the six named cells (TEST-007).
- The two **critical-100%** paths (§9) are actually exercised end-to-end against the real
  DB: the uniqueness/replace headline (§4b) asserts list-count-1 + second-value, and every
  404/422 body (§4h, §4g) is `{"detail"}`-only with the plant name proven absent.
- `CareScheduleResponse` **omits `id`** at every boundary (body §4c + OpenAPI §4i), and the
  migration carries the `(plant_id, care_type)` unique constraint (§6).
- The dual-engine CASCADE (§5) ran on both engines (the CI postgres leg), and `0005`
  applies + rolls back (§6, ARCH-011).
- The TEST-014 red is recorded per lane (§12); the markers (§11) are present; the suite is
  parallel-safe (TEST-006) with per-test plant seeding.
- The Playwright journey (§10) remains deferred with the proposal-deviation note intact,
  and the prod-path smoke (configure water+feed, the uniqueness/replace, the
  no-winter-interval hint) ran before merge.

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
