---
description: Start a change - DoR gate + worklog + sizing, then scaffold the change folder
---
Open a new change for: $ARGUMENTS

1. **Open-questions interview (DoR item 13):** enumerate every ambiguity and unknown in the requested change. Ask the maintainer the **scope-affecting** ones now, before any gate verdict; record the answers in `proposal.md`, list remaining non-scope unknowns as explicit assumptions, and close with a literal `Open questions: none`.
2. **DoR gate (`QG-011`):** run the DoR checklist (`templates/dor.md`); post PASS/WATCH/FAIL per item (`QG-004`). Any FAIL → stop and report exactly what is missing; any WATCH → log the caveat in the worklog.
3. **Scaffold the change (`SPEC-002`):** create `specs/changes/<change-name>/` with `proposal.md`, `design.md`, and `tasks.md` (full track), plus an empty `screenshots/` directory when the story touches UI (`FE-012`). Use the worklog template for step 4. Hand-rolled change folders (outside this command) must scaffold the same set - DoR item 12 checks it.
4. **Worklog (`TRACE-001`):** create `specs/changes/<change-name>/worklog.md` from `templates/worklog.md` with its first entry (actor attribution per `TRACE-006`).
5. **Story check (`SPEC-004`):** "As <role>, I want <what>, so that <why>"; sized 1-3 days / ~400-500 LOC new logic - propose a split if larger.
6. **Contracts first (`API-001`):** if the change touches any REST surface, the OpenAPI delta (paths, request/response schemas, status codes) is part of `proposal.md`/`design.md`; a breaking change triggers planning mode (`API-004`).
7. **Test-foundation (`SPEC-003`):** delegate to the test-engineer subagent to author the test-foundation, or schedule it before `/spec-apply`.
8. Update the work item in the project tracker per docs in `.claude/docs/` if present.
9. Log all steps to the worklog (`TRACE-003/004`).
