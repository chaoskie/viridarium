# Tasks - due-computation (US-3.3)

Backend-only, single lane. TDD per story; red recorded in the worklog before green
(TEST-014, PRIN-III). Order respects dependencies.

## T1 - domain pure logic (test-first)

- [ ] `domain/due.py`: `WinterWindow` (value object + `.contains`), `ScheduleDue`,
      `compute_due(schedule, last_event_on, today, window)`.
- [ ] Unit tests: no-event-due-today, overdue accrual, winter interval applied, winter
      fallback when unset, paused null in-window vs normal out-of-window, all window-edge
      days + new-year wrap. (AC1-AC5, AC8)

## T2 - batch repository reads (test-first, dual-engine)

- [ ] `care_event_repository.latest_event_dates(plant_ids, types)` grouped MAX query.
- [ ] `care_schedule_repository.enabled_for_plants(plant_ids)`.
- [ ] Integration tests on SQLite **and** Postgres (ARCH-011): grouping correctness,
      only-matching-types, enabled filter, empty-id safety.

## T3 - query service (test-first)

- [ ] `application/due.py`: `WinterWindowProvider` Protocol + default (Nov 1 - Mar 1)
      impl; `DueQueryService.for_plants(plant_ids)`.
- [ ] Tests: assembly per plant, two-query bound (no N+1), archived not passed.

## T4 - API exposure (test-first, additive contract)

- [ ] `schemas.py`: `ScheduleDueResponse`; `PlantResponse.schedules: list[...]`.
- [ ] Wire `get_due_query_service` dependency + factory default provider.
- [ ] `plants` router: merge due into list + detail responses; archived -> empty list.
- [ ] API tests: list + detail include `schedules`; disabled omitted; archived empty;
      list query-count bounded. (AC6, AC7)

## T5 - gate

- [ ] Full backend suite green, coverage non-regressing, new modules ~100%.
- [ ] Static gates (ruff, mypy, import-linter) clean.
- [ ] Three-reviewer gate (scope / code / security) + test-engineer re-audit.
- [ ] OpenAPI delta verified live (additive `schedules` field on plant reads only).
