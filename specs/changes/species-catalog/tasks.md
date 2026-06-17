# Tasks - species-catalog (Botanicum Phase 1A)

Ordered groups (PRIN-VI). Mostly a backend slice; the only frontend in 1A is the typed
client (G5). G0 precedes implementation. **TEST-014: record the failing run (the red)
in the worklog before the green, per lane.**

## G0 - Test-foundation (test-engineer, before implementation)
- [ ] `test-foundation.md`: read-path matrix (list all / by category / by `q` /
      empty), detail + 404, seed dual-engine parity (row count + spot row), lowered-LIKE
      portability, OpenAPI codegen delta (TEST-008), coverage targets (QG-002), markers
      (TEST-012), TEST-014 expectation, scenario→test traceability (TEST-015).

## G1 - Domain (backend)
- [ ] `domain/species.py`: `Category` StrEnum; `Species` value object; `SpeciesNotFoundError`;
      `SpeciesRepository` Protocol (reuse `LightLevel`/`Dormancy`).
- [ ] Unit test (red→green): service read + not-found (with a fake repo).

## G2 - Application (backend)
- [ ] `application/species.py`: `SpeciesService.list_species(category?, q?)` + `get_species(id)`.

## G3 - Persistence + seed (backend)
- [ ] `models.py`: `SpeciesModel` (slug unique; nullable defaults).
- [ ] `seed/species_seed.py`: curated ~25-30 entries (incl. category-level rows). Per
      species: watering range (min/max days) + a conservative applied average leaning
      to the drier/longer end (D7); optional `care_notes` raw text (D8). Maintainer to
      confirm the species list (see worklog: "30 most common houseplants" to draft).
- [ ] `migrations/versions/0009_create_species_and_seed.py`: create + bulk_insert seed;
      downgrade drops table; batch mode; down_rev = head.
- [ ] `species_repository.py`: repo + `_to_domain` + portable filter query.
- [ ] Integration (red→green): migration 0009 up/down on SQLite **and** PostgreSQL;
      seed parity (count + spot row); `q`/`category` filter behaviour.

## G4 - Web surface + wiring (backend)
- [ ] `schemas.py`: `SpeciesResponse`.
- [ ] `species.py` router: `GET /species` (+ `?category`/`?q`) and `GET /species/{id}`.
- [ ] `dependencies.py` + `container.py` + `app.py`: service wiring, router mount,
      not-found handler.
- [ ] Integration (red→green): `test_species_endpoint.py` (AC1-AC4, 404, filters).
- [ ] Extend the OpenAPI codegen-output assertion (TEST-008) for the new paths/schema.
- [ ] Gate: `make lint format-check typecheck imports test-coverage audit` green.

## G5 - API client (frontend, 1A scope)
- [ ] `lib/api/species.ts`: `Species` type + `listSpecies`/`getSpecies`; client test
      (happy + ApiError 404). No UI (picker = Phase 1B).
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test` green.

## G6 - Acceptance + evidence (orchestrator)
- [ ] Independent full-gate re-run + live OpenAPI vs typed-client cross-check.
- [ ] (No UI in 1A → no FE-012 screenshots; note this in the DoD.)
- [ ] DoD gate + reviewer gate; worklog the trail; archive on close.
- [ ] Open the Phase 1B proposal (`plant-species-prefill`) as the dependent follow-up.
