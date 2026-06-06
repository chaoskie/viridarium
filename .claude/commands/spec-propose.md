---
description: Start a change - DoR gate + worklog + sizing, then scaffold the change folder
---
Open a new change for: $ARGUMENTS

1. **DoR gate (`QG-011`):** run the DoR checklist (`templates/dor.md`); post PASS/FAIL per item (`QG-004`). Any FAIL → stop and report exactly what is missing.
2. **Scaffold the change (`SPEC-002`):** create `specs/changes/<change-name>/` with `proposal.md`, `design.md`, and `tasks.md` (full track). Use the worklog template for step 3.
3. **Worklog (`TRACE-001`):** create `specs/changes/<change-name>/worklog.md` from `templates/worklog.md` with its first entry (actor attribution per `TRACE-006`).
4. **Story check (`SPEC-004`):** "As <role>, I want <what>, so that <why>"; sized 1-3 days / ~400-500 LOC new logic - propose a split if larger.
5. **Contracts first (`API-001`):** if the change touches any REST surface, the OpenAPI delta (paths, request/response schemas, status codes) is part of `proposal.md`/`design.md`; a breaking change triggers planning mode (`API-004`).
6. **Test-foundation (`SPEC-003`):** delegate to the test-engineer subagent to author the test-foundation, or schedule it before `/spec-apply`.
7. Update the work item in the project tracker per docs in `.claude/docs/` if present.
8. Log all steps to the worklog (`TRACE-003/004`).
