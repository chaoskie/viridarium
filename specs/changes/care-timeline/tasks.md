# Tasks - care-timeline (US-3.4)

Two disjoint lanes; backend first (contract), then frontend. TDD, red-before-green
(TEST-014). PRE-STAGED: proposal/design/test-foundation ready; build resumes next session.

## Build pickup checklist (next session)

- [ ] Confirm the residual assumption (proposal): standalone photos interleave into the
      timeline (default yes) vs events-only. 5-second PO confirm.
- [ ] Re-affirm DoR gate, then run the lanes.

## Backend lane (BE)

- [ ] BE-1 `application/timeline.py`: `TimelineEntry` shape + `TimelineQueryService.for_plant`
      (ARCH-006 read-only; reuse event + photo repos; dedup event-linked photos; sort by
      (date, created_at) desc; plant-exists guard -> 404).
- [ ] BE-2 web: timeline response schema (discriminated event|photo) + router
      `GET /plants/{id}/timeline` + `get_timeline_query_service` dependency + factory wiring.
- [ ] BE-3 tests: merge/order incl. backdated, dedup-once, standalone photo entry, same-day
      tiebreak, empty -> [], missing-plant 404 plant-reason, bounded query count, dual-engine.

## Frontend lane (FE) - after the BE contract is in the tree

- [ ] FE-1 `lib/api/timeline.ts` client (union types + getTimeline).
- [ ] FE-2 `PlantDetailPage` + `/plants/:id` route (minimal: name header + back + timeline);
      link each plant card/row to it.
- [ ] FE-3 `CareTimeline` component: per-event-type distinct render, observe health, inline
      + standalone photos, empty state, phone-first.
- [ ] FE-4 component/client tests (union mapping, each event type, empty, reachable route).
- [ ] FE-5 breakpoint screenshots (FE-012); production-path verification, zero console
      errors (TEST-010).

## Gate (orchestrator)

- [ ] Both lanes green; coverage non-regressing; static gates clean.
- [ ] Three-reviewer gate + test-engineer re-audit.
- [ ] OpenAPI delta verified (GET /plants/{id}/timeline; no other shape change).
- [ ] Production-path screenshots committed.
