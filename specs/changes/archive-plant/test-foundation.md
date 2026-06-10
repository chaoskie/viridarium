---
title: Test Foundation - archive-plant (US-2.4)
type: test-foundation
change: archive-plant
status: authored
date: 2026-06-09
---

# Test Foundation - archive-plant (US-2.4)

Pre-implementation, prescriptive (no test code). This is the SPEC-003 artifact that gates
implementation: the build lanes implement against this matrix, and the story-complete re-audit
checks the implementation back against it. Authored by `test-engineer/HIGH`.

Scope is **behaviour-only** on the merged Plant slice. The `archived` column, the
`PlantResponse.archived` field, and `NewPlant.archived` already exist and round-trip (verified in
the merged `test_plants_endpoint.py::test_post_archived_true_round_trips` and
`test_post_creates_plant_full_and_round_trips`). This story adds: two idempotent sub-resource
actions, the default-active list behaviour, two list query params, and the frontend affordances.
No migration, no new entity, no schema field change.

References: design.md (A1-A4, file plan, §1 contract), proposal.md (ACs 1-8), rules/testing.md
(TEST-001/003/005/007/008/009/010/012/014), rules/quality-gates.md (QG-002).

---

## 1. Surface inventory - happy + sad per surface (TEST-005)

Every public surface touched by this story, each with at least one happy and one sad case. "New"
marks a surface this story adds; "changed" marks an existing surface whose contract changes.

### Backend HTTP surfaces

| # | Surface | Happy | Sad |
|---|---------|-------|-----|
| H1 | `POST /api/v1/plants/{id}/archive` (new) | known id -> 200, body `archived=true`, persisted (GET confirms) | unknown id -> 404, body keys == `{"detail"}`, id in detail, no PII |
| H2 | `POST /api/v1/plants/{id}/unarchive` (new) | known id -> 200, body `archived=false`, persisted (GET confirms) | unknown id -> 404, body keys == `{"detail"}`, id in detail, no PII |
| H3 | `GET /api/v1/plants` default (changed) | seeded active+archived -> returns active only (**headline**) | (covered by the default-exclusion assertion itself; no error mode - empty store still `[]`, already covered) |
| H4 | `GET /api/v1/plants?archived=true` (new param) | returns archived only | active+other-tag and archived+other-tag excluded under AND composition |
| H5 | `GET /api/v1/plants?include_archived=true` (new param) | returns all (active + archived) | (n/a - override is a widening, no error mode) |
| H6 | OpenAPI schema (`/api/v1/openapi.json`) | `/archive` + `/unarchive` paths present; list `get` params include `archived` + `include_archived` | (assertion failure is the sad signal; TEST-008/AC8) |

### Backend application surfaces (`PlantService`)

| # | Surface | Happy | Sad |
|---|---------|-------|-----|
| A1 | `PlantService.archive(id)` (new) | known id -> returns Plant with `archived=true` | unknown id -> `PlantNotFoundError` propagates (carries the id) |
| A2 | `PlantService.unarchive(id)` (new) | known id -> returns Plant with `archived=false` | unknown id -> `PlantNotFoundError` propagates (carries the id) |

### Frontend surfaces

| # | Surface | Happy | Sad |
|---|---------|-------|-----|
| F1 | `archivePlant(id)` client fn (new, `lib/api/plants.ts`) | POSTs `/api/v1/plants/{id}/archive` with empty body, parses returned Plant | non-2xx -> `ApiError` thrown |
| F2 | `unarchivePlant(id)` client fn (new) | POSTs `/api/v1/plants/{id}/unarchive` with empty body, parses returned Plant | non-2xx -> `ApiError` thrown |
| F3 | `buildQuery` with `archived` / `include_archived` (changed) | renders `archived=true` / `include_archived=true` only when set | unset/false fields omitted from query string |
| F4 | `usePlants().archive(id)` callback (new) | calls API then reloads **with the retained active filter** (reload URL carries the last filter, not bare `/plants`) | underlying `ApiError` propagates out of the callback |
| F5 | `usePlants().unarchive(id)` callback (new) | symmetric to F4: API then reload-with-retained-filter | `ApiError` propagates |

Surface count: 6 HTTP + 2 application + 5 frontend = 13 surfaces, each with happy + sad.

---

## 2. Layer assignment with HoneyComb justification (TEST-001/002)

HoneyComb: integration is the **primary** layer; units only where integration cannot
economically reach a branch or where logic is genuinely complex/pure; acceptance kept thin.

| Surface | Layer | Justification |
|---------|-------|---------------|
| H1-H6 | **Integration** (real DB, real composition root, nothing internal mocked - TEST-003) | These are behaviour through the whole slice (router -> service -> repository -> SQLAlchemy -> SQLite). Persistence, the archived WHERE-clause, AND-composition, and OpenAPI emission are exactly what integration is the primary layer for. The default-exclusion, idempotency, lifecycle, and filter composition are only meaningfully observable end-to-end. |
| A1-A2 | **Unit** (`PlantService` against the hand-written `_FakePlantRepository`) | The service methods are thin pass-throughs whose *only* economically-unit-reachable contract is "call the port, propagate `PlantNotFoundError`". A unit pins the pass-through + propagation cheaply and independent of DB. Per design and TEST-004 #2 we do **not** unit-test the list archived WHERE-clause: it is repository SQL, integration-covered; the fake's `list` ignores filters, so a unit there would be meaningless (would pass against any implementation). |
| F1-F3 | **Frontend unit** (vitest, `plants.test.ts`) | Client fns are pure URL/method/body construction over a stubbed `fetch`; mirrors the existing client test structure (stubFetch + path/method/body assertions). |
| F4-F5 | **Frontend unit** (vitest, `usePlants.test.ts`, `renderHook`) | The retained-filter reload behaviour (`lastFilterRef`) is the load-bearing logic; asserting the reload fetch URL carries the active filter is the only way to prove it without driving the real UI. |
| Playwright journey | **Acceptance (DEFERRED)** | TEST-009 requires the journey in Playwright, but FE-015/TEST-009 infra is deferred to the infra story (proposal deviation 3). Recorded in §8, not built this story; covered meanwhile by integration + the hook/client units + the prod-path smoke + FE-012 screenshots. |

---

## 3. Backend integration plan (`backend/tests/integration/test_plants_endpoint.py`)

Real DB, real wiring (TEST-003). Each test seeds via the API inside its own temp-file SQLite
`client` fixture (TEST-006 independence; reuse the existing `client` + `_make_room` helpers).
Module already carries `pytestmark = pytest.mark.integration` (TEST-012).

Add a new section (e.g. `# --- archive / unarchive (US-2.4)`). Prescribed tests:

**Actions - happy + persistence (H1/H2, AC1):**
1. `test_archive_sets_flag_and_persists` - create active plant; POST `/{id}/archive` -> 200,
   body `archived is True`; follow-up `GET /{id}` confirms `archived is True` (persisted, not
   just echoed).
2. `test_unarchive_clears_flag_and_persists` - create, archive, then POST `/{id}/unarchive`
   -> 200, body `archived is False`; `GET /{id}` confirms `archived is False`.

**Actions - 404 no-PII (H1/H2 sad, AC3) - critical:**
3. `test_archive_unknown_id_returns_404_no_pii` - POST `/424242/archive` -> 404; body keys
   == `{"detail"}`; `"424242"` in `body["detail"]`; assert no other keys (no stack/PII). Mirror
   the existing `test_get_unknown_id_returns_404_no_pii`.
4. `test_unarchive_unknown_id_returns_404_no_pii` - symmetric on `/unarchive`.

**Idempotency (AC2):**
5. `test_archive_is_idempotent` - create; archive twice -> both 200, both `archived is True`;
   assert neither is 409.
6. `test_unarchive_is_idempotent` - create (active); unarchive twice -> both 200, both
   `archived is False`; assert neither is 409. (Unarchiving an already-active plant is a no-op
   200, never an error.)

**Default exclusion (H3, AC4) - HEADLINE, critical:**
7. `test_list_excludes_archived_by_default` - seed exactly one active plant and one archived
   plant (create active normally; create the second then archive it via the action). Default
   `GET /plants` (no params) returns **only the active** plant. This is the intended US-2.1
   contract change (default switches from "all" to "active only"); document inline that this is
   the US-2.4 deliverable US-2.1 deferred (design D5 / proposal deviation 2), not a regression.

**Param filters (H4/H5, AC4):**
8. `test_list_archived_true_returns_archived_only` - one active + one archived;
   `?archived=true` -> archived only.
9. `test_list_include_archived_returns_all` - one active + one archived;
   `?include_archived=true` -> both (order-by-name preserved; assert by name set/list).

**Filter composition - AND semantics (H4, AC6):**
10. `test_list_archived_and_tag_composes_and` - seed: (a) archived + tag `rare`,
    (b) active + tag `rare`, (c) archived + tag `common`. `?archived=true&tag=rare` returns only
    (a). Proves AND: active+rare excluded (wrong archived state) and archived+common excluded
    (wrong tag). Mirror the existing `test_filter_combined_*` shape.

**Lifecycle with history intact (H3, AC5):**
11. `test_lifecycle_archive_unarchive_keeps_history` - create with tags (e.g. `["rare","fern"]`)
    -> present in default list -> archive -> absent from default list -> unarchive -> present
    again. Assert tags (and any history-bearing fields, e.g. `created_at` unchanged) are intact at
    each stage. Confirms archive/unarchive never touch tags or drop the row.

**OpenAPI (H6, AC8, TEST-008):**
12. `test_openapi_exposes_archive_paths_and_list_params` - GET `/api/v1/openapi.json`; assert
    `/api/v1/plants/{plant_id}/archive` and `/api/v1/plants/{plant_id}/unarchive` are in
    `schema["paths"]`; assert the list `get` `parameters` names include `archived` and
    `include_archived` (superset assertion, like the existing
    `{"q","location_id","tag","species","homeless"} <= param_names`). Note: the existing
    `test_openapi_exposes_..._and_schema` asserts the **exact** `PlantResponse` property set
    `== {...}`; `archived` is already in that set, so that test stays green unchanged - do not
    expand the PlantResponse schema assertion.

Integration test count: 12.

---

## 4. Backend unit plan (`backend/tests/unit/test_plant_use_case.py`)

Module already carries `pytestmark = pytest.mark.unit` (TEST-012). Pure `PlantService` against
`_FakePlantRepository`; no app, no DB, no I/O.

**Extend `_FakePlantRepository`** with the two new port methods so the fake satisfies the updated
`PlantRepository` Protocol:
- `archive(self, plant_id)` - look up via `self.get(plant_id)` (which already raises
  `PlantNotFoundError` on missing), then store and return a copy with `archived=True`. Use
  `dataclasses.replace(existing, archived=True, updated_at=datetime.now(UTC))` (Plant is a frozen
  dataclass) and write it back into `self._rows`.
- `unarchive(self, plant_id)` - symmetric, `archived=False`.
- (`dataclasses.replace` keeps the rest of the row, including tags, intact - mirrors the design's
  repository semantics without re-listing every field.)

Prescribed tests:
1. `test_archive_sets_flag` (A1 happy) - create plant; `service.archive(id)` returns Plant with
   `archived is True`.
2. `test_unarchive_clears_flag` (A2 happy) - create, archive, then `service.unarchive(id)`
   returns Plant with `archived is False`.
3. `test_archive_propagates_plant_not_found` (A1 sad) - `service.archive(999)` raises
   `PlantNotFoundError`; assert the raised error carries the id (mirror
   `test_delete_propagates_plant_not_found`, optionally `exc_info.value` id check).
4. `test_unarchive_propagates_plant_not_found` (A2 sad) - symmetric.

**Do NOT** add a unit test for the list archived WHERE-clause: it is repository SQL
(integration-covered, §3 tests 7-10); the fake's `list` ignores `PlantFilter`, so a unit there
would pass against any implementation (TEST-004 #2). Recorded as an explicit non-goal.

Unit test count: 4 (+ the fake-repo extension).

---

## 5. Frontend plan

### 5a. Client fns (`frontend/src/lib/api/plants.test.ts`)

Mirror the existing client test structure (`stubFetch`, `okJson`, `fail`, path/method/body
asserts). Add two `describe` blocks. `archivePlant`/`unarchivePlant` are `postJson` to the
sub-resource path with an empty body `{}` (per design `postJson(.../archive, {})`).

- `archivePlant`: (happy) returns parsed Plant on 200; (path/body) POSTs
  `"/api/v1/plants/{id}/archive"` with `method: "POST"` and `body: JSON.stringify({})`,
  Accept + Content-Type headers; (sad) `fail(404)` -> rejects with `ApiError`.
- `unarchivePlant`: symmetric on `"/api/v1/plants/{id}/unarchive"`.
- `buildQuery` / `fetchPlants` (F3): one test that `?archived=true` is rendered when
  `archived: true` is set, one that `include_archived=true` is rendered when set, and one that
  both are omitted when unset/false (extend the existing "omits unset/empty" assertion). Render
  `archived` only when it is a boolean that is set (mirror how `homeless` renders only when
  `true`; note `archived` is a tri-state `true | false | undefined` per design - confirm with the
  built `buildQuery`: `false` must still render `archived=false` because it selects archived-only
  semantics differ from unset; the build lane must keep the test and impl consistent - prescribe:
  render `archived` when it is not `undefined`, render `include_archived` only when `true`).

### 5b. Hook (`frontend/src/features/plants/usePlants.test.ts`)

Mirror the existing `renderHook` + `fetchMock.mockResolvedValueOnce(...)` chaining and the
`toHaveBeenLastCalledWith` URL assertion already used in
`"reloads the list with the active filter applied"`.

- `test: archive(id) reloads with the retained filter` (F4 happy) - the load-bearing assertion.
  Mount the hook; drive a `reload({ q: "mons" })` (or similar active filter) so `lastFilterRef`
  holds it; then `await result.current.archive(PLANT.id)`. Stub fetch with ordered responses:
  initial mount load, the filtered reload, the POST archive response (Plant with `archived:true`),
  then the post-archive reload. Assert the **final** reload fetch was called with the URL carrying
  the retained active filter (e.g. `"/api/v1/plants?q=mons"`), **not** bare `"/api/v1/plants"`.
  This proves the `lastFilterRef` behaviour (an archived row crossing the boundary does not make
  the visible list incoherent), which is the whole point of the design's retained-filter rule.
- `test: unarchive(id) reloads with the retained filter` (F5 happy) - symmetric.
- `test: archive propagates the error` (F4/F5 sad) - stub the POST as a failing response; assert
  `result.current.archive(id)` rejects / surfaces the error (mutations let `ApiError` propagate,
  per the hook's documented contract; the load path traps into `error`, mutations do not).

Add `archive`/`unarchive` to the `UsePlantsResult` type expectations as needed.

Frontend test count: ~5 client + ~3 hook = ~8.

---

## 6. Required markers, mocking boundary, matrices

- **pytestmark (TEST-012):** both Python files already declare the correct module-level marker
  (`integration` / `unit`). New tests inherit it; do not add per-test markers. Frontend runs under
  vitest (no pytest marker).
- **Mocking boundary (TEST-003):** integration tests mock **nothing internal** - real DB, real
  composition root, seed via API. The unit fake `_FakePlantRepository` is an allowed fake of the
  **port**, not of the persistence layer. Frontend stubs only the global `fetch` (the true
  external boundary); no mocking of the client or hook internals.
- **Input-state matrices (TEST-007):** the archive actions are single-dimension (known/unknown id)
  and do not trip the >=3-dimension / >=6-cell threshold, so no new parametrized matrix is
  required for them. The list-filter composition (archived x tag) is exercised explicitly by the
  AND-composition test (§3 #10) rather than a full cross-product, consistent with the existing
  `test_filter_combined_*` approach. The merged `_BAD_BODIES` validation matrix is unchanged by
  this story (no new request schema).

---

## 7. TEST-014 - the red before green (test-first evidence)

Each lane records its failing run in `worklog.md` before the green commit (PRIN-III / TEST-014).
Expected reds for this story:

- **Backend actions:** the `/archive` and `/unarchive` routes do not exist yet, so the action
  tests fail with **404 (route not found)** or **405 (method not allowed)** rather than the
  asserted 200/404-with-detail. The not-found tests will not yet see the id-only `{"detail"}`
  body. Record the failing test names + the actual status/error.
- **Backend default exclusion (headline):** `test_list_excludes_archived_by_default` fails
  **red** because today's default list still returns archived plants (US-2.1 deferred the
  behaviour) - the seeded archived plant appears in the default response. This is the most
  important red to capture: it proves the behaviour change was test-driven.
- **Backend param filters:** `?archived=true` / `?include_archived=true` are ignored until the
  repo clause + router params land, so the filter tests return the wrong set (red).
- **Backend OpenAPI:** the path/param assertions fail because the routes and query params are not
  yet emitted.
- **Backend unit:** `service.archive/unarchive` and the fake-repo methods do not exist yet ->
  `AttributeError` / failing assertions (red) until added.
- **Frontend:** `archivePlant`/`unarchivePlant` and `usePlants().archive/unarchive` are
  undefined -> type/runtime errors (red) until implemented; the retained-filter reload assertion
  fails until `lastFilterRef` is wired.

Record the test names plus the failing assertion/error output per lane in the worklog ahead of the
green commit.

---

## 8. Playwright journey - DEFERRED (TEST-009), recorded only

Do **not** build this story. Recorded for the deferred FE-015/TEST-009 infra story so it is not
re-invented:

> **Archive lifecycle journey.** From the Plants page (defaults to Active): a plant is visible in
> the active list. Click the per-card **Archive** button -> the row leaves the default list
> (archive is one-click, reversible, no confirm dialog per A4). Switch the view control to
> **Archived** -> the row appears there with its Archived badge. Click **Unarchive** -> the row
> returns to the active view. Drive only real UI affordances (the card button + the view
> `<select>`), never inject state directly. **Fail-on console errors / page errors** (TEST-010);
> warnings ignored; any allowlist needs an inline justification.

Meanwhile this journey's behaviour is covered by the integration lifecycle test (§3 #11), the hook
retained-filter tests (§5b), the client tests (§5a), the prod-path smoke, and committed FE-012
screenshots (proposal deviation 3).

---

## 9. Coverage targets (QG-002)

- **Overall floor: >= 85%** (combined unit + integration union; pytest measures them together per
  TEST-001).
- **Branch coverage: >= 95% in domain + application** layers. The new `PlantService.archive` /
  `unarchive` are thin, so their happy + not-found branches must both be exercised (the §4 units
  do this).
- **Branch coverage: >= 80% in adapters/outbound.** The repository `archive` / `unarchive` and the
  `if not include_archived: ... where(archived.is_(...))` clause must have both branches hit: the
  §3 tests 7/8/9 hit include-archived-on (no clause), archived-true (clause `is_(True)`), and
  default/archived-false (clause `is_(False)`).
- **Diff-cover: >= 80%** on the new/changed lines (router routes, service methods, repo methods,
  domain filter fields, frontend client + hook).
- **Critical paths flagged for 100% (spec-flagged):**
  1. **404 no-PII on both actions** (§3 #3, #4) - the trust boundary; body must be exactly
     `{"detail"}` with the id and no PII.
  2. **Default-excludes-archived** (§3 #7) - the headline contract change; the single most
     important behaviour of the story.

---

## 10. Closing note - re-audit / approval (DoD §3)

This foundation is authored and gates implementation. At story-complete the test-engineer runs the
second pass: re-audit the implemented tests against §1-§9 (every surface has its happy + sad; the
two critical paths are at 100%; the TEST-014 reds are recorded in `worklog.md` before the green
commit; QG-002 floors met; markers present; mocking boundary respected). On a clean re-audit the
test-engineer issues the **test-foundation approval** recorded in the worklog, which feeds the DoD
gate (QG-012). Any gap (missing sad path, absent red evidence, a unit that pins implementation
detail, the list-clause smuggled into a unit test) is a finding that must be resolved before
approval.
