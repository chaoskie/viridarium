---
title: Test Foundation - care-events (US-3.2)
type: test-foundation
change: care-events
status: authored
date: 2026-06-11
---

# Test Foundation - care-events (US-3.2)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for the
`CareEvent` append-only aggregate of Plant. First story of the E3 core; **blocks US-3.3**
(due computation consumes events). Authored by `test-engineer` against
`proposal.md` (the exact contract: domain vocabulary, the REST surface, the `0006`
migration, the two-lane frontend scope, AC1-AC5) and `docs/product-spec.md` §3 (CareEvent)
+ §4 (US-3.2 / US-3.4 boundary). Mirrors the structure of `care-schedules/test-foundation.md`.

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. The two disjoint-file lanes
(backend `backend/`, frontend `frontend/`) implement against it and each records its
TEST-014 red in `worklog.md` before turning green. The story-complete pass re-audits the
implementation against this foundation and issues the DoD §3 approval.

Cases are numbered so the lanes can cite them and the re-audit can diff:
`B-Un` (backend unit), `B-In` (backend integration), `F-n` (frontend). The re-audit checks
every numbered case is present, meaningful (TEST-004), and on its assigned layer.

**Critical paths for this story** (flagged 100% in §9):
1. The **append-only invariant** (AC4): no `PUT`/`PATCH` route exists - asserted both as
   the absence of any update route and via the OpenAPI cross-check (`B-I33`).
2. The **conditional `health`-only-on-observe** rule (AC3): `health` on a non-observe type
   is 422; the full type x health matrix (`B-I` matrix M2, `§4e`).
3. The **404 plant-reason / no-PII discipline** (VIRIDARIUM-48 + SEC-007): plant-exists
   guard fires FIRST, the missing-plant 404 detail is `"Plant {id} not found"`, and no
   reject body echoes the plant name or any free-text note PII.

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test. Three endpoints + three
service methods are the behaviour-bearing backend surfaces; three frontend modules.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| E1 | `POST /plants/{id}/events` (create, append) | endpoint | 201 + body (each type) | 404-plant / 422 enum / 422 future-date / 422 health-on-non-observe / 422 cross-plant photo |
| E2 | `GET /plants/{id}/events` (list, newest-first) | endpoint | 200 ordered list | 404-plant |
| E3 | `DELETE /plants/{id}/events/{event_id}` | endpoint | 204 | 404-plant / 404 missing-event / 404 cross-plant event |
| S1 | `CareEventService.create` | use case | persists, returns domain | `PlantNotFoundForEventError` (guard first); `PhotoNotForPlantError` (cross-plant photo) |
| S2 | `CareEventService.list` | use case | rows for plant, ordered | `PlantNotFoundForEventError` |
| S3 | `CareEventService.delete` | use case | row gone | `CareEventNotFoundError` propagates |
| F1 | `careEvents.ts` client (list/create/delete) | FE client | POST/GET/DELETE path+body | `ApiError` on non-2xx |
| F2 | `LogCareModal` component | FE component | quick-tap + expanded submit | future-date blocked; health hidden off-observe; upload-then-create failure surfaced |
| F3 | plant-card quick action / hook | FE hook/page | one-tap water/feed POSTs today | error surfaced inline |

The exact service method names / error-type names are the design lane's to finalize; this
foundation pins the **behaviour** and the error-to-status mapping (404 vs 422), not the
identifiers. The re-audit checks the behaviour, accepting the lane's chosen names.

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Integration is the primary layer** (TEST-001). The real-DB slice
  router -> `CareEventService` -> `SqlAlchemyCareEventRepository` -> SQLAlchemy -> SQLite
  carries the bulk: every endpoint, every field matrix cell, the ordering contract
  (including the backdated-entry tiebreak), the append-only route-absence, all 404/422
  rejects with no-PII, the photo-link + photo-deletion-nulls-link behaviour, and the
  OpenAPI shape. The photo cases reuse the existing photos endpoint to seed a real photo
  (no filesystem assertions needed here beyond what photos already proves).
- **Unit only where integration cannot economically reach** (TEST-001 (b)):
  `CareEventService` orchestration against **fake ports** (a fake `CareEventRepository`
  with a configurable `plant_exists` set, plus a fake photo-lookup port) - the
  plant-exists guard (-> `PlantNotFoundForEventError`), the cross-plant-photo guard
  (-> `PhotoNotForPlantError`), the `health`-only-on-observe domain rule, and the
  not-found propagation on delete. These pin the error-type mapping cheaply; the same
  behaviour is re-proven end-to-end as 404/422 in integration. The frozen domain
  dataclasses + the `CareEventType`/`Health` StrEnums get **no pure-data unit test**
  (TEST-004 #2: would pass against any implementation).
- **Dual-engine** (`test_fk_cross_engine.py`, edited): two FK actions on the real engine
  resolved from `DATABASE_URL` - plant-delete **CASCADE** of event rows, and
  photo-delete **SET NULL** of the event's `photo_id`. The CI postgres leg proves both on
  PostgreSQL; locally on SQLite.
- **Migration** (`test_migrations.py`, edited): `0006` up/down DDL on SQLite; CI runs the
  postgres leg.
- **Acceptance (Playwright, TEST-009): DEFERRED** to the infra story, consistent with the
  care-schedules precedent (proposal deviation). Covered here by integration + the
  component tests + FE-012 screenshots. The intended journey is recorded in §8, **not built**.

---

## 3. Backend unit: `test_care_event_use_case.py` (`unit`)

`pytestmark = pytest.mark.unit`. `CareEventService.create/list/delete` against hand-written
dict-backed fakes (TEST-003: faking ports is allowed; only the real persistence layer must
not be mocked in *integration*). Mirror `_FakeCareScheduleRepository`: a `plant_exists`
backed by a configurable set, and a photo-ownership lookup the service consults for the
cross-plant guard (a fake mapping `photo_id -> plant_id`, plus an "unknown photo" gap).

The economically-unit-reachable logic is the guards + the `health` domain rule + delete
propagation (NOT round-trip persistence - that is integration's job).

| # | test | setup | expectation |
|---|---|---|---|
| B-U1 | create with existing plant persists | `plant_exists` True, no photo | returns a `CareEvent` carrying the input values (happy guard branch) |
| B-U2 | create missing plant raises | `plant_exists` False | raises `PlantNotFoundForEventError`; `.plant_id` carries the queried id; repo.add **not** reached |
| B-U3 | create with valid same-plant photo persists | photo maps to the same plant | event carries `photo_id`; no error |
| B-U4 | create with cross-plant photo raises | photo maps to a **different** plant | raises `PhotoNotForPlantError`; repo.add **not** reached |
| B-U5 | create with nonexistent photo raises | `photo_id` absent from the fake | raises the photo-not-for-plant / not-found error (422 at the edge); repo.add **not** reached |
| B-U6 | health on observe accepted | type=observe, health=good | event carries `health == good` |
| B-U7 | health on non-observe rejected | type=water, health=good | raises the domain validation error mapped to 422; repo.add **not** reached |
| B-U8 | observe without health accepted | type=observe, health=None | event persists, `health is None` (health optional even on observe) |
| B-U9 | happened_on defaults to today | type=water, happened_on omitted | event `happened_on == date.today()` (the default lives where the matrix below proves it - service or router; assert the stored default) |
| B-U10 | list missing plant raises | `plant_exists` False | raises `PlantNotFoundForEventError`; repo.list **not** reached |
| B-U11 | list happy returns rows | `plant_exists` True, rows present | returns the events (ordering is the repo's job, asserted in integration) |
| B-U12 | delete propagates not-found | repo.delete raises `CareEventNotFoundError` | propagates unchanged (service does not swallow/remap) |
| B-U13 | delete happy removes row | row present | repo.delete called; no error |

**Guard-order note:** `create`/`list` check `plant_exists` **first** (-> plant 404 reason,
VIRIDARIUM-48) before touching the repo or the photo lookup. The cross-plant-photo guard
runs after the plant guard (a missing plant must not be masked by a photo error).

---

## 4. Backend integration: `test_care_events_endpoint.py` (`integration`)

`pytestmark = pytest.mark.integration`. Real DB, nothing internal mocked (TEST-003). Each
test seeds its own plant (and, where needed, its own photo) via the API for TEST-006
independence. Helpers mirror the existing endpoint suites:
- `_make_plant(client, name="Fern") -> int`
- `_events_url(plant_id) -> str` -> `/api/v1/plants/{plant_id}/events`
- `_upload_photo(client, plant_id) -> int` - POST to the photos endpoint, return its id
  (reuses the JPEG magic-byte payload from `test_photos_endpoint.py`)
- `_EXPECTED_RESPONSE_KEYS = {id, plant_id, type, happened_on, note, photo_id, health,
  created_at}` (CareEvent **does** expose `id` - unlike CareSchedule - because DELETE is
  keyed by event id, per the proposal response shape).

### 4a. Create happy inventory (AC1, AC2)

| # | test | input | asserts |
|---|---|---|---|
| B-I1 | create water returns 201 + body | `POST .../events {type: "water"}` | 201; keys == `_EXPECTED_RESPONSE_KEYS`; `plant_id` matches; `type == "water"`; `happened_on == today` (default); `note`/`photo_id`/`health` null; `created_at` present |
| B-I2 | create feed | `{type: "feed"}` | 201; `type == "feed"` |
| B-I3 | create repot | `{type: "repot"}` | 201; `type == "repot"` |
| B-I4 | create observe (no health) | `{type: "observe"}` | 201; `type == "observe"`; `health is null` |
| B-I5 | create observe with health | `{type: "observe", health: "good"}` | 201; `health == "good"` |
| B-I6 | create with explicit past happened_on | `{type: "water", happened_on: "2026-01-01"}` | 201; `happened_on == "2026-01-01"` (backdating allowed) |
| B-I7 | create with today happened_on | `{type: "water", happened_on: <today>}` | 201 (today is the boundary, allowed) |
| B-I8 | create with note | `{type: "observe", note: "leaf drop"}` | 201; `note == "leaf drop"` |
| B-I9 | create with max-length note | `note` of exactly 10000 chars | 201 (boundary accepted) |
| B-I10 | create with valid same-plant photo | upload a photo to the plant, then `{type: "observe", photo_id: <id>}` | 201; `photo_id == <id>` |

### 4b. Field input matrix M1 - `happened_on` (TEST-007)

`happened_on` x {validity classes}: a single dimension but enumerated for the boundary
discipline. Branch-priority: malformed shape (Pydantic 422) before semantic future-date 422.

| id | input | expected | proves |
|---|---|---|---|
| `today` | today's date | 201 | boundary inclusive (B-I7) |
| `past` | a past date | 201 | backdating (B-I6) |
| `future` | today + 1 day | **422** | future rejected (the named semantic rule) |
| `far-future` | today + 365 days | **422** | future rejected at scale |
| `omitted` | (field absent) | 201, stored == today | default (B-I1) |
| `malformed` | `"not-a-date"` | 422 | type/shape reject (Pydantic) |

Cases `B-I11` (future +1 -> 422), `B-I12` (far-future -> 422), `B-I13` (malformed -> 422).
The 201 rows are covered by B-I6/B-I7/B-I1; not duplicated. Each 422 asserts the body keys
are exactly `{"detail"}`.

### 4c. Field input matrix M2 - `type` x `health` (TEST-007, CRITICAL)

The conditional rule (`health` valid only when `type == observe`) crosses two dimensions
with > 6 logical cells -> explicit parametrized matrix. Branch-priority: invalid `type`
enum (422) is independent; for a valid type, `health` present + non-observe -> 422;
`health` present + observe -> persists; `health` absent -> persists for any valid type.

Dimensions: **{type: water, feed, repot, observe, unknown} x {health: omitted, good, fair, bad, invalid}**.

| id | type | health | expected | proves |
|---|---|---|---|---|
| `water-no-health` | water | omitted | 201, health null | non-observe, no health (named) |
| `feed-no-health` | feed | omitted | 201, health null | |
| `repot-no-health` | repot | omitted | 201, health null | |
| `observe-no-health` | observe | omitted | 201, health null | observe, health optional (named) |
| `observe-good` | observe | good | 201, health good | observe + valid (named) |
| `observe-fair` | observe | fair | 201, health fair | |
| `observe-bad` | observe | bad | 201, health bad | |
| `observe-invalid-health` | observe | "meh" | **422** | health enum reject (named) |
| `water-with-health` | water | good | **422** | health-on-non-observe (named CRITICAL) |
| `feed-with-health` | feed | good | **422** | health-on-non-observe |
| `repot-with-health` | repot | good | **422** | health-on-non-observe |
| `unknown-type` | "prune" | omitted | **422** | type enum reject incl. unknown value (named) |

Parametrized as `test_type_health_matrix` (`B-I14`), asserting the **stored** value via the
201 body and `{"detail"}`-only on the 422 rows. The three `*-with-health` rows are the
critical-100% conditional guard.

### 4d. Field input matrix M3 - `note` (TEST-007)

| id | note | expected | proves |
|---|---|---|---|
| `empty-string` | `""` | 201, note == "" (or normalized null per design - assert the design's choice) | empty accepted |
| `omitted` | absent | 201, note null | default |
| `max` | 10000 chars | 201 | boundary inclusive (B-I9) |
| `over-max` | 10001 chars | **422** | upper bound (mirrors plant notes 10000) |

Cases: `B-I15` (empty), `B-I16` (over-max -> 422). The omitted + max rows are B-I1 / B-I9.
The design lane decides empty-string normalization; the re-audit accepts either as long as
it is consistent and documented.

### 4e. Field input matrix M4 - `photo_id` (TEST-007, plant-scoped)

| id | photo_id | expected | proves |
|---|---|---|---|
| `omitted` | absent | 201, photo_id null | default (B-I1) |
| `valid-same-plant` | a photo uploaded to this plant | 201, photo_id set | link (B-I10) |
| `cross-plant` | a photo of a **different** plant | **422** | cross-plant guard (named CRITICAL) |
| `nonexistent` | `999999` | **422** | unknown photo |

Cases: `B-I17` (cross-plant photo -> 422; seed plant B + its photo, post to plant A),
`B-I18` (nonexistent photo_id -> 422). Each 422 asserts `{"detail"}`-only and that neither
plant's name leaks.

### 4f. List + ordering contract (AC4)

| # | test | asserts |
|---|---|---|
| B-I19 | list empty when none | fresh plant -> `GET .../events` -> 200, `[]` |
| B-I20 | list newest-first by created_at | create three events same `happened_on` (today) in sequence -> list returns them in reverse insertion order (created_at desc tiebreak) |
| B-I21 | list orders happened_on desc | create event A happened_on=today, then B happened_on=2026-01-01 (backdated) -> list returns A (today) **before** B (past): happened_on desc dominates created_at |
| B-I22 | **backdated entry sorts correctly** (ORDERING CONTRACT) | create today's event, then create a backdated event (happened_on in the past) created *later in wall-clock* -> the backdated entry sorts **below** today's despite a newer created_at; then create a *future-of-the-others-but-past-of-today* backdated entry -> it slots between by happened_on. Asserts the full `(happened_on desc, created_at desc)` tuple order on the observable list. |

`B-I22` is the headline ordering proof: it exercises the tiebreak by inserting in an order
that would be wrong under either single key alone.

### 4g. Delete (AC4)

| # | test | asserts |
|---|---|---|
| B-I23 | delete then list excludes it | create event; `DELETE .../events/{id}` -> 204 (empty body); subsequent list omits it |
| B-I24 | delete leaves siblings | create two events; delete one -> 204; list still returns the other |
| B-I25 | delete missing event -> 404 | real plant, `DELETE .../events/4242` (no such event) -> 404, `{"detail"}`-only |
| B-I26 | **delete cross-plant event -> 404** | create event under plant A; `DELETE /plants/{B}/events/{A_event_id}` -> 404 (cross-plant isolation, mirrors photos `test_delete_cross_plant_returns_404`); the event still exists under A |

### 4h. 404 inventory + plant-reason + no-PII discipline (AC3, CRITICAL)

| # | test | input | expectation |
|---|---|---|---|
| B-I27 | create unknown plant -> 404 plant-reason | `POST /plants/999999/events {type: water}` | 404; `detail == "Plant 999999 not found"` (plant-exists guard FIRST, VIRIDARIUM-48) |
| B-I28 | list unknown plant -> 404 plant-reason | `GET /plants/999999/events` | 404; `detail == "Plant 999999 not found"` |
| B-I29 | delete unknown plant -> 404 plant-reason | `DELETE /plants/999999/events/1` | 404; `detail == "Plant 999999 not found"` (plant guard precedes the missing-event check) |
| B-I30 | create note does not leak in any reject | seed plant `"Secret Orchid"`; trigger a 422 (e.g. health-on-water) with a distinctive `note` | `{"detail"}`-only; the plant name AND the note string are **absent** from `response.text` (SEC-007) |
| B-I31 | missing-event 404 no-PII | seed plant `"Secret Orchid"`; `DELETE .../events/4242` | `{"detail"}`-only; `"Secret Orchid"` absent from `response.text` |

`B-I27`-`B-I29` pin the **plant-reason** convention (the 404 says the *plant* is missing,
not the event, when the plant itself is absent). The event id and plant id are non-PII
identifiers and may appear; the plant name and note free-text MUST NOT.

### 4i. Append-only invariant (AC4, CRITICAL)

| # | test | asserts |
|---|---|---|
| B-I32 | no update route at runtime | `PUT /plants/{id}/events/{event_id}` and `PATCH .../events/{event_id}` both return **405** (or 404) - the route does not exist; events are immutable |
| B-I33 | OpenAPI exposes only the append-only surface (TEST-008) | the emitted `/api/v1/openapi.json` `paths` contain `/api/v1/plants/{plant_id}/events` (with `post`, `get`) and `/api/v1/plants/{plant_id}/events/{event_id}` (with `delete`) and **no `put`/`patch`** on either path; `components.schemas.CareEventResponse.properties` keys == `_EXPECTED_RESPONSE_KEYS` (includes `id`, `photo_id`, `health`) |

`B-I32` + `B-I33` are the critical append-only proof: no update path exists, cross-checked
structurally in the schema.

### 4j. Photo-deletion nulls the event link (proposal §domain, app-level)

| # | test | asserts |
|---|---|---|
| B-I34 | deleting a linked photo nulls the event's photo_id | upload a photo, create an observe event linking it (`photo_id` set), `DELETE` the photo via the photos endpoint, then `GET .../events` -> the event still exists and its `photo_id is null` (history preserved, link severed). The SET NULL FK behaviour observed end-to-end on SQLite; the dual-engine proof is §5. |

---

## 5. Dual-engine: edit `test_fk_cross_engine.py` (`integration`)

Add two tests resolving the engine from `DATABASE_URL` via the existing `fk_engine`
fixture (SQLite locally, PostgreSQL on the CI postgres leg). Add a
`_count_care_event_rows` helper mirroring `_count_photo_rows`.

| # | test | asserts |
|---|---|---|
| B-I35 | plant delete cascades event rows | build a plant; add 2 care events via `SqlAlchemyCareEventRepository`; assert count 2; delete the plant; assert count 0 (FK `ON DELETE CASCADE` on the **real engine**, AC5) |
| B-I36 | photo delete nulls event photo_id | build a plant; add a photo; add an event linking the photo; delete the **photo** row; reload the event -> its `photo_id is None` (FK `ON DELETE SET NULL` on the **real engine**). Self-cleans its own rows. |

`B-I36` is the dual-engine half of `B-I34` (the SQLite endpoint test proves it app-level;
this proves the SET NULL fires on both engines per ARCH-011).

---

## 6. Migration: edit `test_migrations.py` (`integration`)

Mirror the `0005` (care_schedule) up/down test. `0006` down_revision is `0005`.

| # | test | asserts |
|---|---|---|
| B-I37 | `0006` creates care_event + downgrade drops it | upgrade head; `inspect` shows the `care_event` table with columns `{id, plant_id, type, happened_on, note, photo_id, health, created_at}`; the FK to `plant` is `ON DELETE CASCADE`; the FK to `photo` is `ON DELETE SET NULL`; an index on `plant_id` (`ix_care_event_plant_id`). Downgrade to `0005` drops `care_event` but leaves `care_schedule`/`photo`/`plant`/`plant_tag`. |

The two FK actions are the structural complement of the dual-engine `B-I35`/`B-I36`. CI runs
the same DDL on the postgres leg (no separate test).

---

## 7. Frontend (vitest)

Mirror `careSchedules.test.ts` / `usePhotos.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson`/`fail` helpers, `afterEach(unstubAllGlobals + restoreAllMocks)`. **fetch is the
mock boundary** (TEST-003 FE equivalent). A `SAMPLE: CareEvent` constant carries the full
response shape (with `id`, nullable `photo_id`/`health`/`note`).

### 7a. `careEvents.test.ts` (client contract)

| # | test | asserts |
|---|---|---|
| F-1 | fetchEvents GETs the collection path | `GET /api/v1/plants/{id}/events`, `Accept: application/json`; resolves the parsed array |
| F-2 | createEvent POSTs the collection path with the JSON body | method **POST**, path `/api/v1/plants/{id}/events`, `Content-Type: application/json`, body == `JSON.stringify(input)` carrying `type`/`happened_on`/`note`/`photo_id`/`health`; resolves the created `CareEvent` (201) |
| F-3 | createEvent quick-tap body carries type + today only | `createEvent(id, {type:"water", happened_on:<today>})` -> the body's `happened_on` is today's ISO date and `type` is water (the quick-action contract) |
| F-4 | deleteEvent DELETEs the keyed path | `DELETE /api/v1/plants/{id}/events/{eventId}`; resolves void on 204 |
| F-5 | fetchEvents throws ApiError on non-2xx (incl. 404) | a 404 -> rejects `instanceof ApiError` |
| F-6 | createEvent throws ApiError on non-2xx (incl. 422) | a 422 -> rejects `instanceof ApiError` |
| F-7 | deleteEvent throws ApiError on non-2xx (incl. 404) | a 404 -> rejects `instanceof ApiError` |

### 7b. `LogCareModal.test.tsx` (component, RTL)

| # | test | asserts |
|---|---|---|
| F-8 | renders the four event types | the type select offers water, feed, repot, observe |
| F-9 | health select shown ONLY for observe | with type=observe the health select is present; switching to water/feed/repot removes it (the conditional UI mirrors the 422 rule, AC2/AC3) |
| F-10 | date defaults to today, max=today | the date input's value defaults to today and its `max` attribute is today (future dates blocked at the input, AC2/AC3) |
| F-11 | future date blocked on submit | enter a future date -> submit is prevented / an inline validation message shows; no POST fires (the client never sends a known-422 body) |
| F-12 | expanded submit POSTs the assembled event | fill note + observe + health -> submit -> a single POST with `{type:"observe", note, health, happened_on}`; success path clears/closes |
| F-13 | **inline photo upload sequencing** (AC2) | with a photo file selected: submit fires the **photo POST first**, and only on its success fires the **event POST carrying the returned `photo_id`** (assert call order + that the second call's body has the id from the first response) |
| F-14 | photo-upload failure surfaced, event not created | the photo POST fails (415/413) -> an error is surfaced and the event POST does **not** fire (no orphaned event without its intended photo) |
| F-15 | event-create failure surfaced | the photo POST succeeds but the event POST fails (422) -> the error is surfaced to the user (the photo already landed in the gallery per the pipeline; the event simply was not created) |

### 7c. quick-action on the plant card (`F-16`, `F-17`)

| # | test | asserts |
|---|---|---|
| F-16 | one-tap Water logs today's water event | clicking the card's Water quick action POSTs `{type:"water", happened_on:<today>}` to the plant's events; confirmation/inline feedback appears |
| F-17 | one-tap quick action surfaces an error | the POST fails (500) -> a non-blocking error/toast is surfaced; the card stays usable |

These live wherever the quick action is wired (the page or a small hook); the test drives
the real affordance, fetch stubbed.

### 7d. fetch-mock contract fixtures (shared)

A `CareEvent` SAMPLE and an input fixture, plus the `okJson(status, body)` / `fail(status)`
helpers from `careSchedules.test.ts`. For the sequencing tests (F-13..F-15), the fetch mock
must distinguish the photo POST (multipart, path `/photos`) from the event POST
(JSON, path `/events`) and return the photo's `{id}` so the event body can reference it.

---

## 8. Playwright (TEST-009) - DEFERRED, journey recorded only

Consistent with the care-schedules precedent, the acceptance test is **not built here**
(deferred to the infra story), covered by integration + the component tests + FE-012
screenshots. The intended journey, recorded for verbatim future implementation:

1. From the plants page, click a plant card's **Water** quick action -> an inline/toast
   confirmation; the event is logged for today (re-open the log/history -> today's water
   event is present).
2. Open the **Log care** modal -> select `observe`, the **health** select appears; select
   a past **happened_on** (backdate); attempt a future date -> it is blocked.
3. Attach a photo file -> submit -> the photo lands in the plant's gallery (US-2.3 pipeline)
   AND the event links it (the event shows the photo).
4. Switch the type to `water` -> the health select disappears.
5. **Console-error fail-on (TEST-010):** the journey fails on any page error or error-level
   console output; warnings ignored; any allowlist needs an inline justification.

Driver MUST use real UI affordances - never inject values directly.

---

## 9. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; the repo currently sits ~99% backend - this story **MUST NOT** drop
  that floor. New/changed code **≥80% diff-cover**.
- **Branch coverage:** **≥95% in domain + application** (the plant-exists guard, the
  cross-plant-photo guard, the `health`-only-on-observe rule, the future-date rule, delete
  propagation - all the branch points), **≥80% in adapters/outbound** (the
  `(happened_on desc, created_at desc)` ordering, the photo SET NULL handling on read).
- **Critical paths flagged 100%** (spec-flagged -> QG-002 100%):
  1. **Append-only** (`B-I32`, `B-I33`) - no update route, cross-checked in OpenAPI.
  2. **health-only-on-observe** (`B-I14` M2 rows `*-with-health` + `observe-invalid-health`,
     unit `B-U6`/`B-U7`) - every non-observe-with-health is 422.
  3. **404 plant-reason / no-PII** (`B-I27`-`B-I31`) - plant guard first, plant-reason
     detail, no plant name / note free-text in any reject body.
  4. **cross-plant photo guard** (`B-I17`, unit `B-U4`) - a photo of another plant is 422.
- Combined pytest run (unit + integration) scores the union (TEST-001); the integration
  bulk + targeted service units clear the floor without brittle implementation-mirroring
  units (TEST-004).

---

## 10. Mocking boundary (TEST-003) - explicit

- **Integration (`test_care_events_endpoint.py`):** real DB through the real composition
  root; nothing internal mocked. Photos are seeded via the real photos endpoint. The
  matrices, ordering, append-only, 404 no-PII, and photo-link/null behaviour are only
  meaningful end-to-end.
- **Dual-engine / migration:** real engines (SQLite local, Postgres CI), real Alembic.
- **Unit (`test_care_event_use_case.py`):** fake `CareEventRepository` + fake photo-lookup
  port only (faking ports allowed). No app, no DB, no I/O.
- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. Component
  tests render the real React components (RTL).

---

## 11. Required pytest markers (TEST-012)

Module-level `pytestmark` on every new/edited Python test file:
- `test_care_event_use_case.py` -> `pytestmark = pytest.mark.unit`
- `test_care_events_endpoint.py` -> `pytestmark = pytest.mark.integration`
- `test_fk_cross_engine.py` (edited) -> already `pytestmark = pytest.mark.integration`
- `test_migrations.py` (edited) -> already `pytestmark = pytest.mark.integration`

Frontend `*.test.ts(x)` run under vitest (no marker). File-size: keep
`test_care_events_endpoint.py` under the QG-009 **500-LOC hard max**; if it grows past that,
split by group (happy / matrices / ordering / delete+404 / append-only+openapi).

---

## 12. TEST-014 - Test-first evidence (the red), per lane

Each lane records in `worklog.md` the **failing run that precedes the implementation** - the
test names plus the failing assertion/error output (the "red") - before the green commit:

- **Backend lane red:** run `test_care_event_use_case.py`, `test_care_events_endpoint.py`,
  the new `test_fk_cross_engine.py` events tests (`B-I35`/`B-I36`), and the `0006` migration
  test (`B-I37`) against the *unimplemented* code -> expect collection/import errors
  (no `domain.care_event`, no `/events` routes, no `care_event` table). Capture the names +
  the first failing line per group.
- **Frontend lane red:** run `careEvents.test.ts`, `LogCareModal.test.tsx`, and the
  quick-action tests against the *unimplemented* `lib/api/careEvents.ts` / `LogCareModal.tsx`
  -> expect module-not-found / assertion failures. Capture the names + errors.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain.

---

## 13. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this foundation
and issues the **test-foundation approval**, checking:
- Every surface in §1 has its happy + sad (TEST-005); matrices M1-M4 (§4b-4e) + M2 (§4c) are
  present and **parametrized** with the named cells (TEST-007).
- The four **critical-100%** paths (§9) are exercised end-to-end against the real DB:
  append-only route absence + OpenAPI (`B-I32`/`B-I33`), the health-on-non-observe 422 rows,
  the plant-reason 404 with the plant name + note proven absent, and the cross-plant photo 422.
- `CareEventResponse` exposes `id`/`photo_id`/`health` at every boundary (body §4a + OpenAPI
  §4i); the `0006` migration carries CASCADE (plant) + SET NULL (photo) (`B-I37`).
- The dual-engine CASCADE + SET NULL ran on both engines (CI postgres leg, `B-I35`/`B-I36`),
  and `0006` applies + rolls back (ARCH-011).
- The ordering contract `B-I22` actually inserts in a wrong-under-either-single-key order and
  asserts the full tuple order (not a trivially-passing single-key list).
- The photo-deletion-nulls-link (`B-I34` app-level + `B-I36` dual-engine) preserves the
  event and severs only the link.
- The TEST-014 red is recorded per lane (§12); markers (§11) present; suite is parallel-safe
  (TEST-006) with per-test plant/photo seeding.
- The Playwright journey (§8) remains deferred with the precedent note intact.

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
