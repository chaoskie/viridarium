# Tasks - care-events (US-3.2)

Recorded post-hoc to close review finding HIGH-2; statuses reflect the actual build.

## Foundation

- [x] Test foundation (67 numbered cases) before implementation (`test-foundation.md`)

## Backend lane (disjoint: backend/ only)

- [x] Red tests: unit (B-U) + integration endpoint suite (B-I1..34) - red recorded
- [x] `domain/care_event.py` (enums, aggregate, errors, port)
- [x] Migration `0006_create_care_event` (CASCADE/SET NULL, reversible, dual-engine)
- [x] `adapters/outbound/db/care_event_repository.py` + `models.py` CareEventModel
- [x] `application/care_events.py` (guard order: plant -> health rule -> photo)
- [x] `adapters/inbound/web/care_events.py` + schemas (POST/GET/DELETE, no update)
- [x] Wiring: container, dependencies, app router + 4 exception handlers
- [x] B-I35/36 cross-engine FK tests + B-I37 migration test (TEST-014 deviation
      ratified in proposal.md)
- [x] Full suite + static gates + alembic up/down proof

## Frontend lane (disjoint: frontend/ only)

- [x] Red tests per component before implementation (client/hook/modal/quick-actions)
- [x] `lib/api/careEvents.ts` (types + fetch/create/delete + todayIsoDate)
- [x] `features/plants/useCareEvents.ts` (mutation hook)
- [x] `features/plants/LogCareModal.tsx` (type/date/note/photo/health-on-observe)
- [x] `features/plants/QuickCareActions.tsx` (one-tap water/feed + modal entry)
- [x] PlantsPage integration kept thin (+import, +wrapper, +1 component line)
- [x] Suite + lint + tsc + prettier + build

## Orchestrator gate

- [x] Re-ran both suites independently (308 backend / 160 frontend)
- [x] Live OpenAPI cross-check (no PUT/PATCH on events)
- [x] API probes (shape, 422s, 404 reason)
- [x] Production-path browser smoke, zero console errors
- [x] test-engineer re-audit: APPROVED
- [x] code-review: findings HIGH-1..3 + MEDIUM-1..2 + LOW-1 resolved (this commit)
- [x] FE-012 screenshots at locked breakpoints (`screenshots/`)
- [ ] PR + CI green + merge (QG-010 per-run auto-merge authorization)
- [ ] Ticket to Done with merge SHA
