# Design - care-events (US-3.2)

Approach and hexagon placement for the CareEvent slice. Written against the merged
E2/US-3.1 slice template (the ratified CRUD/sub-resource pattern); recorded post-hoc to
close review finding HIGH-2 - content reflects the decisions actually taken at build
time and ratified in the proposal.

## Hexagon placement

| Concern | Layer | File |
|---|---|---|
| CareEventType/Health enums, CareEvent/NewCareEvent, domain errors, repository port | domain (pure, framework-free) | `domain/care_event.py` |
| Use cases + guards (plant-exists FIRST, health-only-on-observe, same-plant photo) | application | `application/care_events.py` |
| SQLAlchemy repo (ordering contract lives here), ORM model | outbound adapter | `adapters/outbound/db/care_event_repository.py`, `models.py` |
| Routes POST/GET/DELETE, request/response schemas, happened_on default + future-date 422 | inbound adapter | `adapters/inbound/web/care_events.py`, `schemas.py` |
| DI + exception handler registration | infrastructure | `container.py`, `dependencies.py`, `app.py` |

## Key decisions

- **Two closed enums, not one.** `CareEventType` (water/feed/repot/observe) is distinct
  from the schedule `CareType` (water/feed). Neither references the other; widening
  either is a spec change (SPEC-001).
- **Validation layering** mirrors the sibling slices: wire-shape concerns (today
  default, future-date rejection, note bound) live in the Pydantic schema; conditional
  domain rules (health-only-on-observe, same-plant photo) live in the application
  service behind domain errors; FK integrity lives in the migration.
- **Cross-aggregate reads** (`plant_exists`, `photo_plant_id`) are methods on the
  CareEventRepository port (precedent: care_schedule's plant_exists), not a second
  injected port - keeps the service single-dependency like its siblings.
- **Append-only enforced structurally**: no update route exists; OpenAPI is
  cross-checked by test (B-I33). Corrections = delete + re-log.
- **FK behavior**: plant delete CASCADEs events (history dies with the plant, like
  photos); photo delete SET NULLs the event link (care history outlives its
  illustration). Migration 0006, reversible, both engines (ARCH-011).
- **Frontend split**: page stays thin; `QuickCareActions` (one-tap + modal entry) and
  `LogCareModal` (full form incl. inline photo upload sequencing: photo POST first,
  then event POST with `photo_id`; either failure surfaced distinctly) are
  self-contained components; `useCareEvents` wraps mutations per the existing hook
  pattern. No list state in the hook - the timeline is US-3.4.

## ADR cross-references

ADR-B (thin application services), ADR-C (domain errors mapped at the boundary,
registered centrally in app.py), ADR-D not applicable (no full-replace semantics here:
append-only), D-009 (archived/homeless handling untouched - events attach to any
existing plant).
