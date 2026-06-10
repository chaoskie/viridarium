# Tasks - care-schedules (US-3.1)

Disjoint lanes (backend G1-G4, frontend G5-G6), parallel under the orchestrator. G0 first.
TEST-014: each lane records its failing run in the worklog before the green.

## G0 - Test-foundation (test-engineer)
- [ ] test-foundation.md: the (plant,care_type) uniqueness headline, enum/range matrix, dormancy default+override (AC4), allow-null-winter-interval (AC5), 404 no-PII, migration 0005, dual-engine CASCADE, OpenAPI (omits id), FE client+hook, TEST-014.

## G1 - Domain (backend)
- [ ] domain/care_schedule.py: CareType/Dormancy StrEnums, CareSchedule/NewCareSchedule, errors, CareScheduleRepository Protocol.
- [ ] Unit (red->green): test_care_schedule_use_case.py (service plant-exists guard + not-found propagation vs fake repo).

## G2 - Persistence (backend)
- [ ] models.py: CareScheduleModel (unique (plant_id,care_type), CASCADE). care_schedule_repository.py: upsert (select-then-write), list (water-first), get/delete (raise not-found), plant_exists.
- [ ] migrations/0005_create_care_schedule.py (down_rev 0004). Extend test_fk_cross_engine.py (schedule-row CASCADE) + test_migrations.py (0005).

## G3 - Web surface (backend)
- [ ] schemas.py: CareScheduleUpsert/CareScheduleResponse (keyed by care_type, omits id, extra=forbid). dependencies.py: get_care_schedule_service. care_schedules.py router (PUT/GET-list/GET-one/DELETE; care_type enum path param; dormancy default in _to_new_schedule).
- [ ] Integration (red->green): test_care_schedules_endpoint.py (AC1-AC6, AC10 + the uniqueness headline + dormancy matrix).

## G4 - Wiring (backend)
- [ ] container.py + app.py (router, app.state, 2 handlers). Gate: make lint format-check typecheck imports test-coverage audit.

## G5 - API client + hook (frontend)
- [ ] lib/api/careSchedules.ts + careSchedules.test.ts. useCareSchedules.ts (+ test).

## G6 - Schedules modal (frontend)
- [ ] features/plants/CareScheduleModal.tsx (water+feed sections; dismissible no-winter-interval hint). PlantsPage.tsx: Schedules action. Gate: make fe-*.

## G7 - Evidence + close (orchestrator)
- [ ] Full gate + live OpenAPI cross-check + prod-path smoke (configure water/feed, replace-not-duplicate, the hint). FE-012 screenshots; re-audit; code-review; DoD; branch->PR->merge; ticket Done.
