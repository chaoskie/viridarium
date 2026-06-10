# Design - care-schedules (US-3.1)

New `CareSchedule` owned-child aggregate of Plant; mirrors the E2 Photo sub-resource slice.
Config only (feeds US-3.2/3.3/3.5/3.6, builds none of them).

## Decisions

- **CS1 - keyed PUT upsert.** Resource addressed by the closed `care_type` enum:
  `PUT/GET/DELETE /plants/{plant_id}/schedules/{care_type}` + `GET .../schedules` (list 0-2).
  PUT is idempotent create-or-replace (the `(plant, care_type)` uniqueness is structurally
  unhittable from the API). DB keeps a surrogate `id` PK + a unique `(plant_id, care_type)`.
- **CS2 - dormancy stored + editable** (`paused`|`winter_interval`), defaulted by care type at the
  HTTP boundary (feed→paused, water→winter_interval), user-overridable (PO Q1). The due engine
  (US-3.3) reads one field, never branches on care_type.
- **CS3 - allow `winter_interval` + null `winter_interval_days`** (PO Q2, spec "if set"); no
  cross-field 422. Frontend nudges with a dismissible hint.
- **CS4 - winter-window DATES are US-3.5** (app settings / climate questionnaire); not on this table.
- **CS5 - US-3.1 adds only its own columns**; later stories (snooze `snoozed_until` on schedule,
  skip as an event) add their own in their own migrations.

## REST / OpenAPI delta (`/api/v1/plants/{plant_id}/schedules`, tag `care-schedules`)

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `` | - | 200 list[CareScheduleResponse] (water, then feed) | 404 plant |
| GET | `/{care_type}` | - | 200 | 404 plant; 404 no-schedule; 422 enum |
| PUT | `/{care_type}` | CareScheduleUpsert | 200 (create-or-replace) | 404 plant; 422 validation/enum |
| DELETE | `/{care_type}` | - | 204 | 404 plant; 404 no-schedule |

`CareScheduleUpsert`: `interval_days` (req, ge=1 le=3650), `winter_interval_days` (opt, ge=1 le=3650,
default null), `dormancy` (`paused`|`winter_interval`, optional → defaulted from path care_type in the
router), `enabled` (bool, default true). `care_type` comes from the PATH only (not the body;
`extra="forbid"`). `CareScheduleResponse` (ARCH-007, keyed by care_type, **omits surrogate id**):
`plant_id`, `care_type`, `interval_days`, `winter_interval_days`, `dormancy`, `enabled`,
`created_at`, `updated_at`.

## Backend file plan (mirror the Photo slice)

**New:** `domain/care_schedule.py` (`CareType`/`Dormancy` StrEnums [spec vocab verbatim];
`CareSchedule`/`NewCareSchedule` frozen dataclasses; `CareScheduleNotFoundError(plant_id, care_type)`→404,
`PlantNotFoundForScheduleError(plant_id)`→404; `CareScheduleRepository` Protocol:
`upsert(plant_id, new)`, `list_for_plant(plant_id)`, `get(plant_id, care_type)`, `delete(plant_id, care_type)`,
`plant_exists(plant_id)`). `application/care_schedules.py` (`CareScheduleService` - upsert/list guard
`plant_exists`→404, else pass-through; returns domain types). `adapters/outbound/db/care_schedule_repository.py`
(`SqlAlchemyCareScheduleRepository`, session-per-call, sole `_to_domain`; `upsert` = select-by-(plant,care_type)
then update-or-insert [portable, no ON CONFLICT]; `list_for_plant` ordered water-first via a portable `case()`).
`adapters/inbound/web/care_schedules.py` (router prefix `/plants/{plant_id}/schedules`; `care_type` path param
typed as `CareType` enum → auto-422; `_to_new_schedule(care_type, body)` resolves the dormancy default).
`migrations/versions/0005_create_care_schedule.py` (down_rev 0004; `care_schedule` table, `pk_care_schedule`,
`fk_care_schedule_plant_id_plant` CASCADE, `uq_care_schedule_plant_id_care_type`, `ix_care_schedule_plant_id`).

**Edit:** `models.py` (+`CareScheduleModel`: enums as String(10/20), `enabled` Boolean server_default true,
ADR-A timestamps, the unique constraint). `schemas.py` (+`CareScheduleUpsert`/`CareScheduleResponse`).
`dependencies.py` (+`get_care_schedule_service`). `container.py` (+repo+service+field). `app.py` (+router,
+`app.state.care_schedule_service`, +2 handlers `CareScheduleNotFoundError`/`PlantNotFoundForScheduleError`→404).

## Frontend file plan

`lib/api/careSchedules.ts` (`CareType`/`Dormancy` unions + `CARE_TYPES`; `CareSchedule`/`CareScheduleInput`;
`fetchSchedules`/`upsertSchedule(plantId, careType, input)`/`deleteSchedule`). `features/plants/useCareSchedules.ts`
(hook: schedules/loading/error + reload/upsert/remove). `features/plants/CareScheduleModal.tsx` (opened from the
plant card like PhotoGalleryModal; a water + a feed section: enabled checkbox, interval number, optional winter
interval number, dormancy `<select>` reusing the established control classes - no new FE-010 primitive; **a small
dismissible non-blocking hint** when dormancy=winter_interval & winter interval empty). `PlantsPage.tsx` (+`{kind:"schedules"}`
modal state + a "Schedules" ghost button per card). No new UI primitive.

## Test seed → test-foundation

Headline: the `(plant, care_type)` uniqueness (PUT water twice → exactly one row, second value). Enum/range
validation matrix (TEST-007): care_type × dormancy{paused,winter_interval,omitted} × winter_interval_days{set,null}
+ interval_days ranges. Dormancy default+override cases (AC4). allow-null-winter-interval (AC5). 404s id/care_type-only
(no PII). Migration 0005 up/down. Dual-engine CASCADE (extend `test_fk_cross_engine.py`). OpenAPI (omits id).
Frontend: client paths/PUT/DELETE + ApiError; hook reload/upsert/remove + error; (the dismissible hint can be a
component assertion). Unit: service plant-exists guard + not-found propagation against a fake repo. TEST-014 red per lane.

## Sizing / delivery

Per-lane within budget (backend ~320-380, frontend ~220-280). One story, two disjoint lanes (backend/ vs
frontend/). FE builds against §1; orchestrator full-gate + live OpenAPI cross-check + prod-path smoke
(configure water+feed, the uniqueness/replace, the no-winter-interval hint) before merge.
