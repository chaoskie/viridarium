# Worklog - care-schedules (US-3.1)

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~08:35 · orchestrator/HIGH · re-audit + code-review launched (DoD §2/§3) · backend/ + frontend/ · REV-008/SPEC-003`
- `~08:32 · orchestrator/HIGH · prod-path smoke PASS (8142): dormancy defaults (water->winter_interval, feed->paused), uniqueness/replace (PUT water x2 -> one row interval 10), id not leaked, allow-null-winter 200, 422 set (bad care_type/interval0/bad dormancy/stray-body), 404 id+care_type-only no-PII, delete->404, plant-delete cascade; UI: Schedules modal w/ editable dormancy + dismissible non-blocking hint (Save gated only on the required interval); only pre-existing CSP errors; FE-012 screenshots committed · screenshots/ · DoD §3 prod-path`
- `~08:28 · orchestrator/HIGH · independent full gate PASS (backend 241/99.40% + frontend 129); live OpenAPI schedule paths + CareScheduleResponse(omits id) match the typed client; ownership clean · - · QG-001/API-001`
- `~08:25 · frontend/HIGH · lane green: 129 vitest (+16); TEST-014 red recorded; Schedules modal (water/feed, editable dormancy, dismissible role=note hint, Save gated on interval not hint), no new primitive · frontend/ · QG-004/TEST-014`
- `~08:20 · backend/HIGH · TEST-014 red recorded (backend lane, tests written before impl): collection ImportError "No module named 'viridarium.application.care_schedules'" (test_care_schedule_use_case.py) + "No module named 'viridarium.adapters.outbound.db.care_schedule_repository'" (test_fk_cross_engine.py); endpoint test_put_water_twice_replaces_never_adds_a_second_row FAILED (no /schedules routes -> 404); migration test_upgrade_creates_care_schedule_table_and_downgrade_drops_it FAILED ("care_schedule" not in {location,photo,plant,plant_tag,schema_meta}). 4 test groups red before green. · backend/tests · TEST-014`
- `~08:05 · orchestrator/HIGH · build fan-out launched: backend + frontend lanes (disjoint, test-first, TEST-014) · backend/ + frontend/ · PRIN-VI`
- `~08:03 · test-engineer/HIGH · test-foundation authored: uniqueness headline + 2x3 dormancy matrix + ~30 integration/9 unit/dual-engine CASCADE/0005 migration/FE; critical-100% = uniqueness + 404-no-PII · test-foundation.md · SPEC-003`
- `~01:00 · orchestrator/HIGH · DoR PASS; spec authored (proposal/design/tasks); PO decisions: dormancy editable per-schedule (Q1), allow null winter-interval + dismissible hint (Q2); climate questionnaire noted for US-3.5 · specs/changes/care-schedules · QG-011/SPEC-002`
- `~00:51 · Lars (PO) · decided: dormancy editable+overridable per schedule; allow null winter-interval with a small non-blocking hint; US-3.5 to be a climate/winter-period questionnaire · - · E3 product decisions`
- `~00:50 · architect/HIGH · US-3.1 design returned (keyed-PUT schedule sub-resource, stored editable dormancy, CASCADE, migration 0005) + the §6 PO decision enumeration · design.md · -`
- `~00:44 · orchestrator/HIGH · US-3.1 picked up: Todo -> In Progress + comment; branched feat/us-3.1-care-schedules off main (E2 + Fable5 fix merged) · git/board · PRIN-VI`
- `~08:40 · orchestrator/HIGH · DoD gate PASS; ready to PR · templates/dod.md · QG-012`
- `~08:38 · code-reviewer/HIGH · code-review VERDICT: CLEAN (no CRITICAL/HIGH, no tech-debt; conforms CS1-CS5 + PO Q1/Q2; hint never blocks save) · backend/ + frontend/ · REV-008`
- `~08:36 · test-engineer/HIGH · re-audit VERDICT: APPROVED (DoD §3); 241 tests 99.40%, all care-schedule modules 100%, no gaps · test-foundation.md · SPEC-003`
