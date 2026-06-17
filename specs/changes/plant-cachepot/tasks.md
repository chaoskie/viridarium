# Tasks - plant-cachepot (US-2.x)

Ordered groups (PRIN-VI). Backend (G1-G4) + Frontend (G5-G6) are disjoint lanes,
parallel under the gating orchestrator. G0 (test-foundation) precedes implementation.
**TEST-014: each lane records its failing run (the red) in the worklog before the green.**

## G0 - Test-foundation (test-engineer, before implementation)
- [ ] `test-foundation.md`: outer-pot input-state matrix (valid/invalid material,
      size 0/1/500/501/non-int/null), null-default cases, migration 0008 up/down
      dual-engine, OpenAPI codegen delta (TEST-008), coverage targets (QG-002),
      markers (TEST-012), TEST-014 expectation, scenario→test traceability (TEST-015).

## G1 - Domain (backend)
- [ ] `domain/plant.py`: `OuterPotMaterial` StrEnum (D2); add `outer_pot_material` +
      `outer_pot_size_cm` to the entity + create/update carriers.
- [ ] Unit test (red→green): enum values + entity carries/threads the fields.

## G2 - Persistence (backend)
- [ ] `models.py`: two nullable columns + `_to_domain` mapping.
- [ ] `migrations/versions/0008_add_cachepot_columns.py`: add_column x2 (batch mode),
      down drops both; down_rev = current head.
- [ ] Integration: extend migration test (0008 up/down on SQLite **and** PostgreSQL).

## G3 - Web surface (backend)
- [ ] `schemas.py`: add the two optional fields to `PlantCreate`/`PlantUpdate`/`PlantResponse`
      (`ge=1, le=500` on size).
- [ ] Integration (red→green): extend `test_plants_endpoint.py` - accept valid
      outer material+size; echo in response; null defaults; extend the parametrized
      bad-body matrix (bad enum, size 0/501/non-int).
- [ ] Extend the OpenAPI codegen-output assertion (TEST-008) for the new properties.

## G4 - Wiring + gate (backend)
- [ ] No new DI (reuses the plant service). Gate: `make lint format-check typecheck
      imports test-coverage audit` green.

## G5 - API client (frontend)
- [ ] `lib/api/plants.ts`: add fields to `Plant`/`PlantInput`; export `OUTER_POT_MATERIALS`;
      extend the client test (round-trips the new fields).

## G6 - Plants feature (frontend)
- [ ] `PlantFormModal.tsx`: relabel inner-pot controls "Nursery (inner) pot"; add the
      "Outer / decorative pot (optional)" material select + optional size input
      (reuse `parseOptionalInt`, `min/max/step`); submit null when unset.
- [ ] Optional: show the outer pot on the plant detail when set.
- [ ] Unit (red→green): form sets/clears outer fields; submits null when unset.
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test fe-build` green.

## G7 - Acceptance + evidence (orchestrator)
- [ ] Playwright (TEST-009): add-plant with an outer pot persists + reads back; modal
      still passes S25+ reachability + axe a11y with the extra fields.
- [ ] FE-012 screenshots (phone + desktop) of the updated form → `screenshots/`.
- [ ] Independent full-gate re-run + live OpenAPI vs typed-client cross-check.
- [ ] DoD gate + reviewer gate; worklog the trail; archive on close.
