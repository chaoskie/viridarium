# Proposal - care-events (US-3.2)

Status: in progress. Story US-3.2 "Log care events (quick action)" - the append-only
CareEvent history. Spec: product-spec §3 (CareEvent) + §4 US-3.2. First story of the E3
core; **blocks US-3.3** (due computation consumes events).

PO decision recorded 2026-06-11: event photo = **inline upload** - the log form accepts
an optional photo, it goes through the existing US-2.3 upload pipeline (landing in the
plant's gallery), and the event links the resulting photo.

## Domain (exact spec vocabulary, SPEC-001)

`CareEvent` (new aggregate, append-only):

- `id`, `plant_id`
- `type`: closed enum `CareEventType` = `water | feed | repot | observe`
  (NOT the schedule `CareType` - schedules stay water/feed; do not widen either enum)
- `happened_on`: date, defaults to today, backdating allowed, **future dates 422**
  (confirmable default, noted for the PO; spec is silent on future)
- `note`: optional, max 10000 (mirrors plant notes bound)
- `photo_id`: optional FK to an existing photo **of the same plant** (cross-plant 422);
  photo deletion nulls the link (history preserved, photo row rules unchanged)
- `health`: optional `good | fair | bad`, **only valid when type=observe** (else 422);
  a journal input, never aggregated
- `created_at` server timestamp

Events are never updated (no PUT/PATCH); delete is allowed (mistakes). Ordering
contract: `happened_on` desc, then `created_at` desc (stable for backdated entries).

## API (both lanes build against exactly this)

- `POST /api/v1/plants/{plant_id}/events` body
  `{type, happened_on?, note?, photo_id?, health?}` -> 201 CareEventResponse
  `{id, plant_id, type, happened_on, note, photo_id, health, created_at}`
- `GET /api/v1/plants/{plant_id}/events` -> 200 list, newest first (ordering contract)
- `DELETE /api/v1/plants/{plant_id}/events/{event_id}` -> 204; cross-plant/missing 404
- Guards mirror the schedule slice: missing plant -> 404 "Plant {id} not found"
  (plant-exists guard FIRST, per the VIRIDARIUM-48 convention); missing event -> 404;
  validation -> 422; no PII in errors (ids only).

## Migration

`0006_create_care_event`: `care_event` table; FK plant CASCADE on delete (history dies
with the plant, like photos); FK photo SET NULL. Runs on SQLite + PostgreSQL
(ARCH-011). `health` and `type` stored as short strings, enum-validated at the edge.

## Frontend

- `lib/api/careEvents.ts` client (types + list/create/delete) mirroring existing slices.
- Quick action on each plant card (PlantsPage): one-tap "Water" / "Feed" logs the event
  for today; toast/inline confirmation; list state refreshes.
- `LogCareModal` (new component; PlantsPage stays thin - its oversize is filed debt):
  type select (4 event kinds), date (defaults today, max=today), note, optional photo
  file (uploads via the existing photos endpoint, then creates the event with
  `photo_id`), health select shown ONLY when type=observe.
- Events render newest-first; full timeline UI is US-3.4 (NOT this story) - this story
  only needs the log actions and a minimal "last logged" feedback, not a history view.

## Out of scope

Due computation (US-3.3), timeline rendering (US-3.4), snooze/skip (US-3.6), bulk
logging (US-3.7), any change to CareSchedule or the schedule UI.

## Acceptance

- AC1: one-tap water/feed from the plant list creates today's event (UI + API).
- AC2: expanded form supports backdate (not future), note, observe+health, inline photo
  upload that lands in the gallery and links to the event.
- AC3: health on a non-observe type and future dates are 422; cross-plant photo_id 422.
- AC4: events list newest-first per the ordering contract; delete works; append-only
  (no update route exists; OpenAPI cross-checked).
- AC5: both engines green in CI; everything UI-reachable is API-reachable.

## Implementation notes and ratified deviations (comply-or-explain, PRIN-X)

- **Ordering third key:** the repository orders by `happened_on` desc, `created_at`
  desc, **then `id` desc**. The third key is a permitted extension of the two-key
  contract above: `created_at` is second-granular on SQLite, so same-second appends
  would otherwise tie; `id` desc preserves the created-at-desc intent
  deterministically on both engines. (Review LOW-1, ratified 2026-06-11.)
- **TEST-014 exception for B-I35/B-I36/B-I37** (dual-engine CASCADE / SET NULL +
  migration reversibility tests): authored alongside the implementation, without an
  independent red run. Cause: the original build lane was killed by a session usage
  limit after writing the endpoint/unit reds but before these three; the finisher
  agent wrote them with the code. The deviation is recorded in the worklog, the
  story-complete re-audit read all three and judged they assert structural facts a
  wrong migration/FK would fail (and they mirror the proven 0005 precedent).
  **Approved as a one-off; not a precedent.** (Review HIGH-1, ratified 2026-06-11.)

## Sizing

Two disjoint-file lanes (backend/ vs frontend/), ~400-500 LOC new logic per lane
(PRIN-VI per-lane budget), 1000 LOC story ceiling.

## DoR: PASS (spec-backed story, contract above is exact, photo decision ratified by PO 2026-06-11, lanes disjoint, test-foundation precedes implementation).
