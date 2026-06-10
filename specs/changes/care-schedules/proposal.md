# Proposal - care-schedules (US-3.1)

Status: applied (PR open, pending merge). Epic E3 (Care schedules & logging), US-3.1, high priority (project board).
First E3 story. New `CareSchedule` owned-child aggregate of Plant. Config only - NOT due
computation (US-3.3), event logging (US-3.2), or snooze/skip (US-3.6).

## Story (SPEC-004)

> As a plant owner, I want to set a watering and feeding schedule for each plant (how often,
> a different winter cadence, and whether feeding pauses in winter), so that the app can later
> tell me what's due.

## Scope (exact, PRIN-IV)

**In:**
- `CareSchedule` entity: `plant_id` FK (ON DELETE CASCADE), `care_type` (enum `water`/`feed`),
  `interval_days` (required), `winter_interval_days` (optional), `dormancy` (enum
  `paused`/`winter_interval` - **stored + user-editable**, defaulted by care type), `enabled`.
  One per `(plant, care_type)` - DB unique constraint.
- Sub-resource endpoints under `/plants/{id}/schedules`: `GET` list (0-2, water-first), `GET
  /{care_type}`, **`PUT /{care_type}`** (idempotent create-or-replace - the address is the
  closed-enum care_type, so create==replace), `DELETE /{care_type}`. 404 on unknown plant /
  unknown schedule; 422 on bad enum / out-of-range intervals.
- Domain `care_schedule.py` (entity, ports, errors), application service, repository,
  `CareScheduleModel`, Alembic `0005`, web router/schemas/deps, wiring - mirroring the E2 slice.
- Frontend: a "Schedules" modal opened from the plant card (mirrors the Photos modal), with a
  water and a feed section (enabled / interval / optional winter interval / dormancy select),
  plus a **small, dismissible, non-blocking inline hint** when a section picks `winter_interval`
  dormancy but leaves the winter interval empty (PO decision Q2).
- Unit + integration tests incl. the `(plant, care_type)` uniqueness invariant, enum/range
  validation, the dormancy default+override matrix, dual-engine CASCADE; FE-012 screenshots; TEST-014.

**Out (YAGNI / SPEC-001):**
- Due computation (US-3.3), care-event logging (US-3.2), snooze/skip (US-3.6) - this is config only.
- The **winter-window dates** + the climate questionnaire → **US-3.5** (app settings). US-3.1 stores
  per-schedule intervals + dormancy; the due engine (US-3.3) will read the global window from US-3.5.
- No `snoozed_until` / skip columns (each later story adds its own columns in its own migration;
  PO-confirmed direction). The closed `water`/`feed` enum is v1 (spec §3).

## PO decisions (this story)

- **Dormancy is a stored, user-editable per-schedule enum** (default feed→`paused`, water→
  `winter_interval`; overridable - e.g. keep feeding a winter-grower). Honors spec §3 "the schedule
  stays transparent and user-editable; the user wins the argument with the algorithm." (Q1.)
- **A `winter_interval` dormancy with no `winter_interval_days` is allowed** (not a 422) - in winter
  it falls back to the normal interval (spec: water "uses the winter interval *if set*"). The
  frontend shows a small closeable hint nudging the user to set one; nothing blocking. (Q2.)
- **Forward (US-3.5):** a climate/winter-period questionnaire (multi-season climates); the
  "known winter climate" version of the hint lands there. Recorded on the US-3.5 ticket.

## Contract / architecture

Additive sub-resource surface under `/api/v1` (API-004). New owned child aggregate in the existing
inventory/care hexagon (ARCH-002/004 - no context carve; the due-engine 2-aggregate read is a US-3.3
concern, noted). Dual-engine portable (ARCH-011): String-stored enums, FK CASCADE, select-then-write
upsert (no engine-specific ON CONFLICT). `CareScheduleResponse` is keyed by `care_type` and omits the
surrogate `id` (ARCH-007). No stack amendment.

## Deviations (comply-or-explain, PRIN-X)

1. **`PUT`-to-create (not `POST`)** for the schedule sub-resource - the address is the closed
   `care_type` enum, so create and replace are the same idempotent op (keyed-PUT); makes the
   `(plant, care_type)` uniqueness structurally unhittable from the API. A deliberate, justified
   shape vs the plant template's POST.
2. **FE-015 Audit Spaces + TEST-009 Playwright** deferred to the infra story (unchanged); covered by
   integration + the prod-path smoke + FE-012 screenshots.

## Definition of Ready (QG-011)

1. Approved - PASS (board top; PO answered the two build-blocking decisions). 2. Story format - PASS.
3. Sized - PASS (per-lane ~320-380 backend / ~220-280 frontend, well under budget). 4. Testable ACs - PASS (below).
5. Dependencies - PASS (config feeds US-3.2/3.3; winter dates from US-3.5). 6. Logging/trust - PASS (404/422 id+care_type only, no PII).
7. Architecture - PASS (owned child aggregate, dual-engine). 8. Roles - PASS (architect done; test-engineer; backend+frontend lanes; orchestrator gates+merge).
9. Contract - PASS (additive sub-resource). 10. Test-foundation - PASS (scheduled). 11. Worklog - PASS.

**DoR verdict: PASS.**

## Acceptance criteria

- AC1: `PUT /plants/{id}/schedules/water` with `{interval_days}` → 200; a second PUT replaces it (no 2nd row); `GET .../schedules` returns it.
- AC2: `(plant, care_type)` uniqueness holds — never two `water` rows for one plant (the headline invariant).
- AC3: 422 on bad `care_type` (path enum), `interval_days` ≤0 or >3650, bad `dormancy` value.
- AC4: Dormancy defaults — omitted on `feed` → `paused`; omitted on `water` → `winter_interval`; an explicit override (feed→`winter_interval`, water→`paused`) persists. (Editable, Q1.)
- AC5: `dormancy=winter_interval` with `winter_interval_days=null` is accepted (no 422). (Q2.)
- AC6: `GET`/`DELETE` on unknown plant or unknown schedule → 404 (id/care_type only, no PII). `enabled` defaults true.
- AC7: Deleting a plant removes its schedule rows (CASCADE, both engines).
- AC8: Migration `0005` applies + rolls back on both engines.
- AC9: The plant card has a Schedules action → a modal configuring water/feed (enabled/interval/winter-interval/dormancy); the no-winter-interval hint is a small dismissible note, never blocking.
- AC10: OpenAPI exposes the schedule endpoints; `CareScheduleResponse` keyed by `care_type`, omits `id`.
