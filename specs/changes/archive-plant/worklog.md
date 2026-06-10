# Worklog - archive-plant (US-2.4)

Per-change trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.
Public-repo hygiene: story ids only, no tracker UUIDs/hostnames.

## AI logging guidance (`TRACE-004`)
Log forks/design decisions, gate-checks, the TEST-014 red-run per lane, review verdicts,
commits, lifecycle transitions, comply-or-explain deviations. Not routine edits/reads.

---

## Entries

- `~20:38 · orchestrator/HIGH · DoD gate PASS; full gate green (backend 137/99.26% + frontend 94); ready to PR · templates/dod.md · QG-012`
- `~20:36 · orchestrator/HIGH · review MEDIUM fixed (create/update/remove now reload with lastFilterRef so mutations retain the active view) + re-audit gap fixed (added hook archive/unarchive ApiError-propagation tests, F4/F5 sad); frontend re-gate green 94 tests. LOW (no-op archive doesn't bump updated_at) noted as a documented non-issue, no action · usePlants.ts + usePlants.test.ts · REV-003/SPEC-003`
- `~20:35 · code-reviewer/HIGH · code-review VERDICT: CLEAN (no CRITICAL/HIGH; conforms A1-A4 + scope); 2 MEDIUM + 1 LOW tech-debt · backend/ + frontend/ · REV-008`
- `~20:34 · test-engineer/HIGH · re-audit: CHANGES NEEDED -> APPROVED after the missing hook sad-path test was added; 99.26%, both critical paths 100% · test-foundation.md · SPEC-003`
- `~20:30 · orchestrator/HIGH · review + re-audit launched (DoD §2/§3) · backend/ + frontend/ · REV-008/SPEC-003`
- `~20:29 · orchestrator/HIGH · prod-path smoke PASS (8139): default excludes archived, ?archived/?include_archived scopes, idempotent double-archive (200), archived+tag AND, unarchive restores w/ tags intact, 404 no-PII; UI: clicked Archive -> row left Active view, list coherent; only pre-existing CSP errors; FE-012 screenshots committed · screenshots/ · DoD §3 prod-path`
- `~20:28 · orchestrator/HIGH · independent full gate PASS (backend 137 tests 99.26% + frontend 92); live OpenAPI archive/unarchive paths + archived/include_archived params match the typed client; ownership clean · - · QG-001/API-001`
- `~20:27 · frontend/HIGH · lane green: 92 vitest (+10); TEST-014 red recorded; view control + per-card Archive button (no new primitive, FE-010); lastFilterRef reload · frontend/ · QG-004/TEST-014`
- `~20:25 · backend/HIGH · TEST-014 RED recorded (tests-first, before impl): 15 failed / 2 passed. Unit: test_archive_sets_flag / test_unarchive_clears_flag / test_archive_propagates_plant_not_found / test_unarchive_propagates_plant_not_found -> AttributeError 'PlantService' object has no attribute 'archive' (service+fake-repo methods absent). Integration: test_archive_sets_flag_and_persists / test_unarchive_clears_flag_and_persists / test_archive_is_idempotent / test_unarchive_is_idempotent -> POST /plants/{id}/archive 404 (route not found); test_archive_unknown_id_returns_404_no_pii / test_unarchive_unknown_id_returns_404_no_pii likewise 404 (no route, not the asserted detail body); test_list_excludes_archived_by_default (HEADLINE) -> AssertionError ['Active','Archived']==['Active'] (default still returns archived, US-2.1 deferred behaviour); test_list_archived_true_returns_archived_only + test_list_archived_and_tag_composes_and -> wrong set (param ignored); test_openapi_exposes_plant_paths_query_params_and_schema -> archive/unarchive paths + archived/include_archived params absent; test_lifecycle_archive_unarchive_keeps_history -> archive POST 404. (test_list_include_archived_returns_all passed coincidentally: today's default = all.) · backend/tests · TEST-014/PRIN-III`
- `~20:18 · orchestrator/HIGH · build fan-out launched: backend + frontend lanes (disjoint, test-first, TEST-014) · backend/ + frontend/ · PRIN-VI`
- `~20:17 · test-engineer/HIGH · test-foundation authored: 12 integration + 4 unit + ~8 vitest; headline default-excludes-archived; idempotency, lifecycle, 404 no-PII, lastFilterRef reload · test-foundation.md · SPEC-003`
- `~20:15 · test-engineer/HIGH · test-foundation pass launched (G0) · test-foundation.md · SPEC-003`
- `~20:14 · orchestrator/HIGH · DoR PASS; spec authored (proposal/design/tasks); ADR-delta: first targeted sub-resource action (archive/unarchive POST, idempotent state-set) per ADR-D escape hatch · specs/changes/archive-plant · QG-011/SPEC-002`
- `~20:13 · architect/HIGH · design returned: dedicated idempotent archive/unarchive POST + list default=active (archived/include_archived params); no migration/entity; reversible->no confirm; lastFilterRef FE subtlety · design.md · -`
- `~20:10 · architect/HIGH · US-2.4 architect pass launched (archive/unarchive action + default-list exclusion; reuses the Plant slice) · - · sprint`
- `~20:08 · orchestrator/HIGH · US-2.4 picked up: Todo -> In Progress + comment; branched feat/us-2.4-archive-plant off main (US-2.2 #15 + US-2.1 #17 merged) · git/board · PRIN-VI`
- `~20:08 · orchestrator/HIGH · change opened · specs/changes/archive-plant/ · SPEC-002`
