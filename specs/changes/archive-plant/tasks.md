# Tasks - archive-plant (US-2.4)

Disjoint lanes (backend G1-G3, frontend G4-G5), parallel under the orchestrator. G0 precedes
implementation. TEST-014: each lane records its failing run in the worklog before the green.

## G0 - Test-foundation (test-engineer)
- [ ] `test-foundation.md`: happy+sad per surface, the default-excludes-archived headline,
      lifecycle, idempotency, filter composition, 404 no-PII, OpenAPI assertion; coverage
      targets; TEST-014 expectation.

## G1 - Domain + application (backend)
- [ ] `domain/plant.py`: `PlantFilter` += `archived`/`include_archived`; port += `archive`/`unarchive`.
- [ ] `application/plants.py`: `PlantService.archive/unarchive` (pass-through, propagate not-found).
- [ ] Unit (red->green): extend `test_plant_use_case.py` fake + archive/unarchive + not-found propagation.

## G2 - Persistence (backend)
- [ ] `plant_repository.py`: list archived clause (portable `is_()`); `archive`/`unarchive` (session-per-call).

## G3 - Web surface (backend)
- [ ] `plants.py`: list `archived`/`include_archived` query params -> `PlantFilter`; `POST /{id}/archive` + `/unarchive` routes.
- [ ] Integration (red->green): `test_plants_endpoint.py` += archive/unarchive (200/404/idempotent), default-excludes-archived, lifecycle, `?archived`/`?include_archived`, composition; extend the OpenAPI assertion.
- [ ] Gate: `make lint format-check typecheck imports test-coverage audit`.

## G4 - API client + hook (frontend)
- [ ] `lib/api/plants.ts`: `PlantFilter` += params; `buildQuery`; `archivePlant`/`unarchivePlant`.
- [ ] `usePlants.ts`: `archive`/`unarchive` with `lastFilterRef` reload (+ test: posts then reloads with the retained filter).

## G5 - Plants page (frontend)
- [ ] `PlantsPage.tsx`: view control (Active/Archived/All) in the filter bar; per-card Archive/Unarchive ghost button (aria-label, no confirm).
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test fe-build`.

## G6 - Evidence + close (orchestrator)
- [ ] Independent full-gate re-run + live OpenAPI vs typed-client cross-check + prod-path smoke (archive via UI -> leaves default -> view Archived -> unarchive -> returns; zero new console errors).
- [ ] FE-012 screenshots; test-engineer re-audit approved; code-review CLEAN; DoD PASS/FAIL.
- [ ] Branch -> PR -> merge (green); ticket -> Done + SHA; worklog complete.
