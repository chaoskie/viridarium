# Tasks - location-crud (US-2.2)

Ordered task groups (PRIN-VI). Backend (G1-G4) and Frontend (G5-G7) have disjoint file
ownership and run in parallel under the gating orchestrator; the orchestrator gates each before
the single commit/PR. Test-foundation (G0) precedes implementation (SPEC-003 / PRIN-III).

## G0 - Test-foundation (test-engineer, before implementation)
- [ ] Author `test-foundation.md`: input-state matrix for name×notes validation (TEST-007),
      happy+sad per surface (TEST-005), coverage targets (QG-002), required markers (TEST-012).

## G1 - Domain + application (backend)
- [ ] `domain/location.py`: `Location`, `NewLocation`, `LocationNotFoundError`, `LocationRepository` Protocol.
- [ ] `application/locations.py`: `LocationService` (create/list/get/update/delete).
- [ ] Unit tests (red→green): `tests/unit/test_location_use_case.py` against a dict-backed fake port.

## G2 - Persistence (backend)
- [ ] `adapters/outbound/db/models.py`: `LocationModel`.
- [ ] `adapters/outbound/db/location_repository.py`: `SqlAlchemyLocationRepository` + `_to_domain`.
- [ ] `migrations/versions/0002_create_location.py`: create/drop `location`.
- [ ] Migration integration test: upgrade creates table / downgrade drops (SQLite; Postgres in CI).

## G3 - Web surface (backend)
- [ ] `adapters/inbound/web/schemas.py`: add `LocationCreate`/`LocationUpdate`/`LocationResponse`.
- [ ] `adapters/inbound/web/locations.py`: the five routes.
- [ ] `adapters/inbound/web/dependencies.py`: `get_location_service`.
- [ ] Integration tests (red→green): `tests/integration/test_locations_endpoint.py` (all AC1-AC6, AC9);
      extend the OpenAPI assertion for `/locations` (TEST-008).

## G4 - Wiring (backend)
- [ ] `infrastructure/container.py`: build + register repo + service.
- [ ] `infrastructure/app.py`: include router, `app.state` wiring, `LocationNotFoundError` handler.
- [ ] Gate: `make lint format-check typecheck imports test-coverage audit` green.

## G5 - API client + UI primitives (frontend)
- [ ] `lib/api/client.ts`: add `postJson`/`putJson`/`deleteResource`.
- [ ] `lib/api/locations.ts`: interfaces + typed endpoint functions; `locations.test.ts` (happy + ApiError sad).
- [ ] `components/ui/`: `Button`, `TextField`, `Modal`.

## G6 - Rooms feature (frontend)
- [ ] `features/rooms/useLocations.ts` (+ test: list/empty/error).
- [ ] `features/rooms/RoomsPage.tsx`, `RoomFormModal.tsx`, `DeleteRoomDialog.tsx`.
- [ ] `App.tsx`: route `/rooms` -> `RoomsPage`.
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test fe-build` green.

## G7 - Evidence + close (orchestrator)
- [ ] FE-012 breakpoint screenshots committed to this change folder.
- [ ] Test-foundation re-audit approved (test-engineer); DoD gate (templates/dod.md) PASS/FAIL posted.
- [ ] Branch -> PR; worklog + change-index updated (TRACE-002); ticket comment with PR URL.
