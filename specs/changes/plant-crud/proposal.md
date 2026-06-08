# Proposal - plant-crud (US-2.1)

Status: applied (PR open, pending maintainer merge). Epic E2 (Plant inventory), US-2.1, high priority (project board).
Second persisted entity; reuses the Location CRUD template (repository-port vertical slice,
ADRs A-E). Built on `feat/us-2.1-plant-crud` off the US-2.2 branch tip (PO-approved; rebase
to main after #15 merges).

## Story (SPEC-004)

> As a plant owner, I want to add, view, edit, and remove my plants with all their details,
> and find them by room, tag, or species, so that I can keep an accurate inventory of what
> I'm growing and where.

## Problem / why

US-2.2 gave us rooms. The core entity of the app is the plant. This story adds it with the
full product-spec §3 attribute set, makes a plant's room **optional** (the "homeless" state,
D-009), and gives the list a search/filter so the inventory stays usable as it grows.

## Scope (exact, PRIN-IV)

**In:**
- Full CRUD on `/api/v1/plants` with all product-spec §3 attributes: `name` (required),
  `species`, `location` (**optional** FK - homeless), `acquired_on`, `pot_size_cm`,
  `pot_material` (enum), `light_level` (enum), `notes`, `tags` (free-form, filterable),
  `archived` (bool field only - see Out).
- **List with search/filter** by `q` (name/species substring), `location_id`, `tag`,
  `species`, and `homeless` (location-less only). AND-combined, portable across engines.
- Domain `Plant` + enums + `PlantRepository` port + typed errors; `SqlAlchemyPlantRepository`
  (search/filter + tags); normalized `plant_tag` child table; Alembic `0003`; `PlantService`
  (with the FK-existence guard); schemas; router; DI wiring; 404 + 422 handlers.
- **`PRAGMA foreign_keys=ON` for SQLite** in `engine.py` so `ON DELETE SET NULL`/`CASCADE`
  actually fire (dual-engine correctness, ARCH-011).
- Real **Plants** page (list + search/filter controls + create/edit/delete), with a location
  picker offering "No room (homeless)", enum selects, and a tags input. Reuses the shared
  `Button`/`TextField`/`Modal` primitives.
- Unit + integration tests per the test-foundation, incl. the **ON DELETE SET NULL
  cross-entity test on both engines**; committed FE-012 screenshots; **TEST-014 red-run
  evidence** per lane.

**Out (YAGNI, PRIN-IX / SPEC-001):**
- Photos (US-2.3); species-info provider (US-6/v1.5); care schedules/events/due (E3).
- **Archive *behavior*** (exclusion from due/default lists) - US-2.4; the `archived` field is
  persisted + exposed here, but the list does NOT filter archived out.
- The rich room-delete **A/B/C prompt** (delete plants / move / decide-later) and **bulk
  move** - the dedicated follow-up. The baseline on room delete is ON DELETE SET NULL
  (= D-009 option C: plants go homeless), which needs no UI and no Location-code change.
- A new `Select` UI primitive - native `<select>` styled with existing tokens (FE-010: only
  an ADR-worthy archetype if duplicated 3+ times; raise then, don't add silently).

## Contract impact (API-001)

New REST surface `/api/v1/plants` + list query params; additive within v1 (API-004),
non-breaking. Full delta in `design.md` §1. OpenAPI assertion extended (TEST-008).

## Architecture (DoR §7)

Fits the existing single inventory hexagon (ARCH-002): Plant is the second aggregate in the
same context; one cross-aggregate read (`location_exists`) is normal intra-context coupling,
not a carving signal (ARCH-004). Dual-engine portable (ARCH-011): String-stored enums,
normalized tags (portable `EXISTS` filter, no engine-specific JSON SQL), lowered-`LIKE`
search, and the SQLite FK pragma. No stack amendment (PRIN-V): no new dep either lane.

## Logging / security (DoR §6)

Reads non-destructive, no PII. Error bodies `{"detail": ...}` carry only an id (404 plant,
422 unknown location_id), no PII (SEC-001). No new secrets. Trust boundary unchanged.

## Deviations (comply-or-explain, PRIN-X)

1. **Touches shipped infra `engine.py`** (the SQLite FK pragma). PRIN-IX limits unrelated
   edits, but this is *required* for the story's dual-engine correctness (without it SET NULL
   silently no-ops on SQLite). Engine-isolated (SQLite-only), harmless to Postgres, covered by
   a dual-engine test. Necessary, not a drive-by.
2. **Changes US-2.2's room-delete effect**: deleting a room now SET-NULLs its plants to
   homeless rather than being a pure no-op. This is the ratified **D-009 option C** baseline,
   not a new decision; recorded as a consequences note on D-009. The rich A/B/C prompt stays
   deferred.
3. **Per-lane LOC budget** (sprint-2 amendment): backend ~430-480, frontend ~430-500, each
   under the ~500 per-lane soft cap; 1000 hard ceiling per story respected. Pre-agreed
   fallback if the frontend lane crosses ~500 during build: defer the **filter *controls*** (not
   the API) to a thin follow-up - search/filter is the clean seam.
4. **FE-015 Audit Spaces + TEST-009 Playwright** still deferred to the infra story (the
   harness doesn't exist yet), consistent with US-2.2. Covered by unit+integration + the
   prod-path smoke test + FE-012 screenshots.

## Definition of Ready (QG-011)

1. Approved to start - PASS (top of board; PO directed continuing to US-2.1 this session).
2. Story format - PASS (above).
3. Sized & independent - PASS (per-lane budget; depends only on US-2.2 which is the branch base).
4. Testable ACs - PASS (below).
5. Dependencies known - PASS (base = US-2.2 Location; downstream: room-delete A/B/C flow + bulk move follow-up; US-2.4 archive behavior; E3 schedules reference Plant).
6. Logging/trust-boundary - PASS (above).
7. Architecture conform - PASS (above; the engine pragma is the one justified infra touch).
8. Estimate + responsibilities - PASS (architect done; test-engineer foundation; backend+frontend lanes; orchestrator gates+commit; PO merge).
9. Contract impact - PASS (design §1; additive).
10. Test-foundation - PASS (scheduled with test-engineer; SPEC-003).
11. Worklog - PASS (worklog.md exists; TRACE-001).

**DoR verdict: PASS** (deviations 1-4 recorded; 1-2 are necessary/ratified, 3-4 carry the sprint-2 + US-2.2 precedents).

## Acceptance criteria

- AC1: POST a plant with full attributes (incl. tags, enums, a room) returns 201 with the full body; it appears in GET list.
- AC2: A plant can be created with **no room** (`location_id: null`) - homeless - and round-trips as such.
- AC3: POST/PUT with empty/whitespace name, a bad enum value, a malformed date, out-of-range pot size, or an over-long field returns 422.
- AC4: POST/PUT referencing a non-existent `location_id` returns **422** (id-only detail), not 404.
- AC5: GET list supports `q`, `location_id`, `tag`, `species`, `homeless`, AND-combined; no params returns all ordered by name; no match returns `[]`.
- AC6: GET/PUT/DELETE on an unknown plant id returns 404 (no-PII detail). PUT full-replaces (incl. the tag set) and bumps `updated_at`. DELETE returns 204, then GET → 404.
- AC7: **Deleting a room that holds plants sets those plants to homeless** (location_id null), the plants and their history survive - verified on **both SQLite and Postgres**.
- AC8: Deleting a plant removes its tag rows (no orphans).
- AC9: Migrations `0003` apply + roll back on both engines; `plant` + `plant_tag` match the models incl. the FK ondelete.
- AC10: The Plants page lists plants with room name + tags, supports add/edit/delete and search/filter through real UI (incl. choosing "No room"), with loading/empty/error states.
- AC11: OpenAPI exposes `/api/v1/plants` paths, the list query params, and the `PlantResponse` schema.
