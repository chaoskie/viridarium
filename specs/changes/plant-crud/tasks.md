# Tasks - plant-crud (US-2.1)

Ordered groups (PRIN-VI). Backend (G1-G4) + Frontend (G5-G6) are disjoint lanes, parallel
under the gating orchestrator. G0 (test-foundation) precedes implementation. **TEST-014:
each lane records its failing run (the red) in the worklog before the green.**

## G0 - Test-foundation (test-engineer, before implementation)
- [ ] `test-foundation.md`: the Plant validation input-state matrix (TEST-007), happy+sad per
      surface, search/filter cases, the dual-engine SET NULL cross-entity test, plant_tag
      CASCADE, coverage targets (QG-002), markers (TEST-012), TEST-014 expectation.

## G1 - Domain + application (backend)
- [ ] `domain/plant.py`: enums, `Plant`/`NewPlant`/`PlantFilter`, `PlantNotFoundError`,
      `LocationNotFoundForPlantError`, `PlantRepository` Protocol.
- [ ] `application/plants.py`: `PlantService` (CRUD + the FK-existence guard).
- [ ] Unit test (red→green): `tests/unit/test_plant_use_case.py` (FK-guard branches, homeless allowed).

## G2 - Persistence (backend)
- [ ] `engine.py`: SQLite `PRAGMA foreign_keys=ON` connect listener (D1).
- [ ] `models.py`: `PlantModel` (FK ondelete SET NULL) + `PlantTagModel` (FK CASCADE, composite PK).
- [ ] `plant_repository.py`: `SqlAlchemyPlantRepository` + `_to_domain` + portable filter query + tag write/replace + `location_exists`.
- [ ] `migrations/0003_create_plant.py`: plant + plant_tag, FK ondelete, down_rev 0002.
- [ ] Integration: extend `test_migrations.py` (0003 up/down); the **SET NULL cross-entity test on both engines** + plant_tag CASCADE.

## G3 - Web surface (backend)
- [ ] `schemas.py`: `PlantCreate`/`PlantUpdate`/`PlantResponse` (reuse `_trim_non_empty_name`).
- [ ] `plants.py` router: 5 routes + list query→`PlantFilter`.
- [ ] `dependencies.py`: `get_plant_service`.
- [ ] Integration (red→green): `tests/integration/test_plants_endpoint.py` (AC1-AC6, AC11 + search/filter matrix, parametrized POST+PUT bad-body, 422 unknown location_id, 404 plant).

## G4 - Wiring (backend)
- [ ] `container.py` + `app.py` (router, app.state, both exception handlers).
- [ ] Gate: `make lint format-check typecheck imports test-coverage audit` green.

## G5 - API client (frontend)
- [ ] `lib/api/plants.ts`: types + 5 typed fns + query-string builder; `plants` client test (happy + ApiError sad).

## G6 - Plants feature (frontend)
- [ ] `features/plants/usePlants.ts` (+ test: list/empty/error/filter).
- [ ] `PlantsPage.tsx` (list + filter controls), `PlantFormModal.tsx` (all fields + homeless picker + enum selects + tags), `DeletePlantDialog.tsx`.
- [ ] `App.tsx`: `/plants` → `PlantsPage`.
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test fe-build` green. (Fallback: if FE >~500 LOC, defer filter *controls* to a follow-up, comply-or-explain.)

## G7 - Evidence + close (orchestrator)
- [ ] Independent full-gate re-run + live OpenAPI vs typed-client cross-check + **prod-path smoke test** (backend-served build, zero console errors, exercise homeless + filter).
- [ ] FE-012 screenshots committed; test-engineer re-audit approved; code-review CLEAN; DoD PASS/FAIL posted.
- [ ] D-009 consequences note appended; branch → PR; worklog complete; ticket comment.
