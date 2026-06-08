# Proposal - location-crud (US-2.2)

Status: applied (PR open, pending maintainer merge). Epic E2 (Plant inventory), US-2.2, high priority (tracked on the project board).
First persisted domain entity; establishes the reusable CRUD vertical-slice pattern that
US-2.1 (Plant) and US-2.4 (Archive) inherit.

## Story (SPEC-004)

> As a plant owner, I want to create, view, rename, annotate, and delete rooms
> (locations), so that I can organize my plants by where they live.

## Problem / why

The walking skeleton (E1) persists nothing beyond a bootstrap table. Inventory (E2) needs
its first real entity. Locations are the thinnest E2 slice and the natural first one
(plants reference a location), so building it first both delivers value and shapes the
persistence + repository + use-case + router + React pattern every later entity copies.

## Scope (exact, PRIN-IV)

**In:**
- Full CRUD on `/api/v1/locations` (POST/GET-list/GET-one/PUT/DELETE), persisted on SQLite
  and Postgres, with the OpenAPI delta in `design.md` (contract is the artifact, API-001).
- Domain `Location` entity + `LocationRepository` port + typed `LocationNotFoundError`.
- SQLAlchemy `LocationModel` + concrete `SqlAlchemyLocationRepository` + Alembic `0002`
  creating the `location` table (dual-engine, ARCH-011).
- `LocationService` use cases; request/response Pydantic schemas; router; DI wiring;
  a registered not-found exception handler (404).
- Real **Rooms** UI replacing the `/rooms` placeholder: list + create + edit + delete-confirm,
  plain `fetch` via the typed client, a minimal shared UI primitive set (Button, TextField,
  Modal) reusable by US-2.1.
- Unit + integration tests per the test-foundation; committed FE-012 breakpoint screenshots.

**Out (explicit YAGNI, PRIN-IX / SPEC-001):**
- No plant-count delete guard, no `PlantCounter` port, no reassignment-on-delete flow.
  Plants do not exist yet; every location is trivially empty, so DELETE is a plain delete.
  The rich "delete the plants / move them / leave them homeless" flow and the optional
  (homeless) plant location are deferred to US-2.1. See D-009.
- No list search/filter (that is US-2.1 Plant scope).
- No unique constraint on `name` (the spec allows duplicate room names).
- No PATCH/partial update (PUT full-replace; recorded as the convention).
- Playwright/axe/perf Audit-Spaces (see deviation below).

## Contract impact (API-001)

New REST surface `/api/v1/locations`; additive within v1 (API-004), no breaking change.
Full path/method/schema/status delta in `design.md` §1. OpenAPI assertion extended (TEST-008).

## Architecture (DoR §7)

Fits the existing single hexagon (ARCH-002): new code spans domain / application /
adapters.inbound.web / adapters.outbound.db / infrastructure, dependencies inward only,
import-linter contracts unchanged and still satisfied. Dual-engine portable (ARCH-011):
portable column types, server-default timestamps, batch-mode migration. No stack amendment
(ARCH-001 / PRIN-V): no new backend or frontend dependency.

## Logging / security (DoR §6)

Reads are non-destructive, no PII. Error responses are `{"detail": "..."}` carrying only an
id, never PII (PRIN-II / SEC-001). Secure-headers middleware already applies. No new secrets.

## Deviations (comply-or-explain, PRIN-X)

1. **Over the ~400-500 LOC soft budget (PRIN-VI / SPEC-004).** Estimated ~780 LOC new logic
   (~350 backend, ~430 frontend), under the 1000 hard ceiling. **Justification:** it is one
   user-meaningful slice (managing rooms) and splitting it by layer would produce a
   backend-only "story" with no user-facing value, violating the SPEC-004 story format. Much
   of the LOC is repetitive CRUD/boilerplate (excluded from the count per SPEC-004). The work
   is mechanically separable along the backend/frontend file boundary and is delivered by two
   disjoint-file parallel build agents under one gating orchestrator (PRIN-VI 2026-06-07
   amendment; [[parallel-build-agents]]). Approved by the maintainer at pickup.
2. **FE-015 Audit Spaces (axe a11y + perf-budget) and TEST-009 Playwright acceptance
   deferred.** No Playwright harness exists yet; standing it up is a cross-cutting infra story,
   not Location-specific. Consistent with `scaffold-frontend` and the sprint-2 handoff, which
   list this infra as a non-blocking follow-up. Covered instead by real-DB integration tests +
   targeted units + committed FE-012 screenshots. A dedicated infra story will add the harness.
   Approved by the maintainer at pickup.

## Definition of Ready (QG-011) - gate result

1. **Approved to start** - PASS (maintainer picked US-2.2 at sprint-2 kickoff; PO-confirmed scope/deviations in-session).
2. **Story format** - PASS (story above, SPEC-004 form).
3. **Sized & independent** - PASS-with-deviation (~780 LOC; deviation #1 recorded + approved; no dependency on unfinished work - it is itself the first inventory story).
4. **Testable acceptance criteria** - PASS (see below; each AC is input -> observable outcome).
5. **Dependencies known** - PASS (none upstream; downstream: US-2.1 plants reference Location and add the plant-aware delete flow + optional location, D-009).
6. **Logging / trust-boundary considered** - PASS (section above; no PII, secure-by-default unchanged).
7. **Architecture conform** - PASS (section above; hexagon-fit, dual-engine, no stack amendment).
8. **Estimate + responsibilities** - PASS (architect: design done; test-engineer: test-foundation; two build agents: backend + frontend; orchestrator: gates + commit; PO: merge).
9. **Contract impact known** - PASS (OpenAPI delta drafted in design.md §1; additive, non-breaking).
10. **Test-foundation** - PASS (scheduled with the test-engineer subagent before implementation; SPEC-003).
11. **Worklog created** - PASS (`worklog.md` exists with first entries; TRACE-001).

**DoR verdict: PASS** (deviations #1/#2 recorded and maintainer-approved per comply-or-explain).

## Acceptance criteria

- AC1: `POST /api/v1/locations` with a valid name returns 201 and the created location
  (id, name, notes, timestamps); it then appears in `GET /api/v1/locations`.
- AC2: `POST`/`PUT` with empty or whitespace-only name returns 422; notes over the max returns 422.
- AC3: `GET /api/v1/locations` returns all rooms ordered by name; an empty store returns `[]`.
- AC4: `GET`/`PUT`/`DELETE` on an unknown id returns 404 with a no-PII `{"detail": ...}` body.
- AC5: `PUT` updates name and notes and bumps `updated_at`; the change is reflected on read.
- AC6: `DELETE` returns 204 and the location is gone (subsequent `GET` -> 404).
- AC7: The Rooms page lists rooms, and supports add / edit / delete through real UI
  affordances, with loading, empty, and error states. Delete is a plain confirm (no plant
  warning yet; comment notes the US-2.1 flow).
- AC8: Migrations apply and roll back on both SQLite and Postgres; `location` table matches the model.
- AC9: OpenAPI at `/api/v1/openapi.json` exposes the `/api/v1/locations` paths and the `LocationResponse` schema.
