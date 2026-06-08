# Worklog - plant-crud (US-2.1)

Per-change trail (`TRACE-001`). Entries **newest-first**: `time · actor · action · artifact · ref`.
**Public-repo hygiene:** story ids only (e.g. US-2.1), no tracker UUIDs/hostnames here.

## AI logging guidance (`TRACE-004`)

Log forks/design decisions, gate-checks, the **TEST-014 red-run** per lane, review verdicts,
commits, lifecycle transitions, comply-or-explain deviations. Not routine edits/reads.

---

## Entries

- `~21:55 · orchestrator/HIGH · DoD gate PASS posted; full quality-gates green (backend 122 tests 99.22% + frontend 82); H1 resolved, M1/L1/harness to TD · templates/dod.md · QG-012`
- `~21:50 · orchestrator/HIGH · review H1 FIXED: added test_fk_cross_engine.py - dedicated SET-NULL+CASCADE test resolving its engine from DATABASE_URL, so the runtime behaviour runs on Postgres in CI (AC7/D1 now met by an automated test, not just manual smoke) · tests/integration/test_fk_cross_engine.py · REV-008/AC7/D1`
- `~21:48 · orchestrator/HIGH · M1 (mutation resets filter) + L1 (422 field heuristic) + dual-engine integration-harness gap filed to TD · project board Backlog, Inventory · REV-003`
- `~21:45 · code-reviewer/HIGH · code-review VERDICT: CHANGES NEEDED - 1 HIGH (H1: FK runtime behaviour untested on Postgres - conftest pins SQLite); enum fix confirmed complete+consistent, pragma correct+isolated, filter query injection-safe, scope clean · backend/ + frontend/ · REV-008`
- `~21:42 · test-engineer/HIGH · re-audit VERDICT: APPROVED (DoD §3); 99.22% cov, critical paths 100%, enum fix reflected in tests · test-foundation.md · SPEC-003`
- `~21:30 · code-reviewer/HIGH + test-engineer/HIGH · review + re-audit launched (DoD §2/§3) · backend/ + frontend/ · REV-008/SPEC-003`
- `~21:25 · orchestrator/HIGH · prod-path smoke PASS (backend-served build, port 8138): plant+homeless create, 422 on bad enum + unknown location_id, homeless/tag filters, AC7 LIVE room-delete->Monstera homeless+alive; only the 2 pre-existing CSP errors (a5203b45), none new; FE-012 screenshots committed · screenshots/ · DoD §3 prod-path`
- `~21:18 · orchestrator/HIGH · contract cross-check PASS: live OpenAPI plant paths + PlantResponse + enum values + list query params match the typed client · - · API-001`
- `~21:15 · orchestrator/HIGH · SPEC-001 deviation CAUGHT+FIXED: backend invented enum values (pot_material glass/metal/concrete, light_level low/medium) vs product-spec §3 (self-watering/other; dark/indirect). Corrected domain/plant.py + frontend plants.ts to spec values both lanes; gate re-run green (matrix parametrization 122->120 tests, confirms tests iterate the enum) · domain/plant.py + plants.ts · PRIN-IV/SPEC-001`
- `~21:05 · orchestrator/HIGH · independent gate re-run PASS (make quality-gates): backend 120 tests 99.22% cov + frontend 82; ownership boundaries clean · - · QG-001/PRIN-VIII`
- `~20:00 · frontend/HIGH · lane green: 82 vitest (+24); TEST-014 red recorded (tests failed on missing imports pre-impl); no deps, no per-lane fallback, no new UI primitive (feature-local FieldSelect below FE-010 threshold) · frontend/ · QG-004/TEST-014`
- `~19:55 · backend/HIGH · TEST-014 green: PRAGMA foreign_keys=ON connect-listener added to engine.py (SQLite-only); SET-NULL + CASCADE tests now pass; full slice green · adapters/outbound/db/engine.py · TEST-014 / D1`
- `~19:52 · backend/HIGH · TEST-014 red #2 (the headline, D1): SET-NULL test failed on SQLite BEFORE the engine.py pragma - test_deleting_room_orphans_its_plants_to_homeless -> AssertionError "assert 1 is None" (location_id stayed 1; SQLite silently ignored ON DELETE SET NULL). CASCADE test test_deleting_plant_cascades_its_tag_rows also red - sqlite3.IntegrityError UNIQUE constraint plant_tag.plant_id,tag (deleted plant's tag rows never cascaded). Slice present, models/repo/migration/router wired, engine pragma NOT yet added · tests/integration/test_plants_endpoint.py · TEST-014 / D1 / AC7 / AC8`
- `~19:40 · backend/HIGH · TEST-014 red #1 (baseline): plants endpoint + matrix + filter + lifecycle tests failed against the absent slice (64 failed, 1 passed) - unregistered /api/v1/plants route -> 404s / missing schemas before domain/application/router/migration existed · tests/integration/test_plants_endpoint.py · TEST-014`
- `~19:35 · backend/HIGH · unit FK-existence guard tests written first (test_plant_use_case.py): homeless allowed, existing-loc allowed, nonexistent-loc raises LocationNotFoundForPlantError, plant-not-found propagation · tests/unit/test_plant_use_case.py · TEST-014 / S14`
- `~19:20 · orchestrator/HIGH · build fan-out launched: backend + frontend lanes (disjoint, test-first, TEST-014 red-run required) · backend/ + frontend/ · PRIN-VI`
- `~19:15 · test-engineer/HIGH · test-foundation authored: 10-dim matrix (14 sad cells x POST+PUT), dual-engine SET-NULL headline test, search/filter cases, TEST-014 section · test-foundation.md · SPEC-003`
- `~19:05 · test-engineer/HIGH · test-foundation pass launched (G0), emphasizing the dual-engine SET NULL test + TEST-014 · test-foundation.md · SPEC-003`
- `~19:02 · orchestrator/HIGH · DoR PASS posted (deviations: engine.py pragma necessary; room-delete=SET NULL per D-009; per-lane budget; Audit-Spaces deferred) · proposal.md · QG-011`
- `~19:00 · orchestrator/HIGH · spec authored (proposal/design/tasks); D-009 consequences note appended (SET NULL baseline + SQLite pragma) · specs/changes/plant-crud + D-009 · SPEC-002`
- `~18:55 · architect/HIGH · design returned: FK SET NULL + the SQLite PRAGMA foreign_keys gap (cross-engine ARCH-011 catch), normalized plant_tag, StrEnum-as-String, search/filter contract; sizing under per-lane budget · design.md · -`
- `~18:40 · architect/HIGH · Plant CRUD architect pass launched (reuses the Location template; FK-on-delete + tags-modeling + search/filter to decide) · - · sprint-2 retro template`
- `~18:38 · orchestrator/HIGH · US-2.1 picked up: Todo -> In Progress + starting comment; branched feat/us-2.1-plant-crud off the US-2.2 tip (PO OK, rebase to main after #15 merges) · git/board · PRIN-VI`
- `~18:38 · orchestrator/HIGH · change opened · specs/changes/plant-crud/ · SPEC-002`
