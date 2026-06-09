# Proposal - archive-plant (US-2.4)

Status: applied (PR open, pending merge). Epic E2 (Plant inventory), US-2.4, high priority (project board).
Small behaviour-only story on the merged Plant slice; no new entity, no migration.

## Story (SPEC-004)

> As a plant owner, I want to archive a plant that has died or that I've given away,
> so that it drops out of my active list (and future due reminders) while its history
> and photos are kept, and I can still find or restore it.

## Problem / why

US-2.1 persists+exposes the `archived` flag but does nothing with it - the default list
still returns archived plants. This story adds the behaviour: archived plants leave the
default list, with a one-click archive/unarchive affordance and a view to see/restore them.

## Scope (exact, PRIN-IV)

**In:**
- `POST /api/v1/plants/{id}/archive` and `/unarchive` - idempotent state-set actions
  returning the updated `PlantResponse` (200; 404 unknown plant, id-only no PII).
- `GET /api/v1/plants` defaults to **active only**; `?archived=true` = archived only;
  `?include_archived=true` = all. AND-composed with the existing filters.
- `PlantFilter` gains `archived: bool | None` + `include_archived: bool`; repository list
  clause (portable `is_()`); `PlantService.archive/unarchive`; two routes + two query params.
- Frontend: a view control (Active default / Archived / All) in the filter bar; a per-card
  Archive/Unarchive button (reversible -> no confirm dialog); `usePlants` retains the active
  filter so an archived row doesn't incoherently vanish/reappear (`lastFilterRef`).
- Unit + integration tests (incl. default-excludes-archived, lifecycle, idempotency,
  filter composition); committed FE-012 screenshots; TEST-014 red-runs.

**Out (YAGNI / SPEC-001):**
- Due-computation exclusion (E3, not built). Forward-link: when E3 lands, the due query
  filters the SAME `archived` flag - no new field. Recorded so E3 doesn't re-invent it.
- No new entity, table, or migration (the column exists).
- No undo-toast; no bulk archive (could be a later story).
- No new UI primitive (the view control reuses the native `<select>` + token pattern).

## Contract impact (API-001/004)

Additive within v1: two new POST sub-resource actions + two optional list query params.
Non-breaking for create/read/update/delete. **Behaviour change (intended):** the default
`GET /plants` switches from "all" to "active only" - this is the US-2.4 deliverable that
US-2.1 explicitly deferred (design D5), not a regression.

## Architecture (DoR §7)

Modify-only within the existing hexagon: domain `PlantFilter` + port methods, application
service methods, repository list clause + archive/unarchive, router routes. No layer/boundary
change. Dual-engine portable (`is_()`, ARCH-011). No stack amendment.

## Deviations (comply-or-explain, PRIN-X)

1. **First targeted sub-resource action vs ADR-D** ("PUT full-replace, no PATCH until a story
   needs partial semantics"). US-2.4 is that story: archive/unarchive are modeled as
   idempotent state-set POSTs returning the resource (not PATCH - no partial-body merge
   needed). PUT still works as the full-replace/bulk path. Recorded as an ADR-delta note.
2. **Default-list behaviour change** to US-2.1's `GET /plants` (all -> active only). Intended
   per design D5; the test-foundation re-documents the contract intent.
3. **FE-015 Audit Spaces + TEST-009 Playwright** deferred to the infra story (unchanged from
   US-2.1/2.2); covered by unit+integration + the prod-path smoke + FE-012 screenshots.

## Definition of Ready (QG-011)

1. Approved - PASS (board top; PO directed "knock out 2.4"). 2. Story format - PASS.
3. Sized & independent - PASS (small, modify-only; depends on merged US-2.1). 4. Testable ACs - PASS (below).
5. Dependencies - PASS (none upstream; E3 due-exclusion inherits the flag). 6. Logging/trust - PASS (404 id-only, no PII).
7. Architecture - PASS (modify-only, dual-engine). 8. Estimate/roles - PASS (architect done; test-engineer; one backend + one frontend lane; orchestrator gates+merge).
9. Contract impact - PASS (additive + the documented default-list change). 10. Test-foundation - PASS (scheduled, test-engineer). 11. Worklog - PASS.

**DoR verdict: PASS** (deviations 1-3 recorded; all benign/intended).

## Acceptance criteria

- AC1: `POST /plants/{id}/archive` -> 200, `archived=true`, persisted (GET confirms). Unarchive -> `archived=false`.
- AC2: Both actions are idempotent (archiving twice -> 200/true; no 409).
- AC3: Archive/unarchive on an unknown id -> 404 with a no-PII `{"detail": ...}` body.
- AC4: `GET /plants` (no params) returns **active only**; `?archived=true` -> archived only; `?include_archived=true` -> all.
- AC5: Lifecycle: a plant is in the default list -> archive -> absent from default -> unarchive -> present again; history (tags etc.) intact throughout.
- AC6: `archived` composes (AND) with the other filters (e.g. `?archived=true&tag=rare`).
- AC7: The Plants page defaults to active; a view control switches to Archived/All; a per-card button archives/unarchives in one click and the visible list stays coherent.
- AC8: OpenAPI exposes the `/archive` + `/unarchive` paths and the `archived`/`include_archived` list params.
