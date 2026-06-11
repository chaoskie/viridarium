---
description: Implement the next task(s) of the active change - TDD, gated, logged
---
Apply tasks for change: $ARGUMENTS

1. **Test-foundation check (`SPEC-003`):** verify a test-foundation exists for this story in `specs/changes/<change-name>/`; if missing, delegate to the test-engineer subagent to author it first. Implementation does not start without it.
2. Pick the next unchecked task from the change's `tasks.md` (one task group at a time, PRIN-VI).
3. **TDD (`PRIN-III`):** failing test with red output → implementation with green output. Honeycomb placement per `TEST-001/002`; required layer marker per `TEST-012`.
4. WIP checkpoint per completed task group (`QG-008`); commit gating per `QG-010`.
5. **Gate-check (`QG-004`):** post PASS/WATCH/FAIL (tests green, boundaries clean `ARCH-003`, dual-engine portable `ARCH-011`, scope unchanged `SPEC-001`) before the next task group; WATCH caveats go to the worklog for the next retro. Circuit breaker applies (`QG-007`).
6. Update the work item in the project tracker per docs in `.claude/docs/` if present.
7. Log to the change's worklog (`TRACE-003/004`).
