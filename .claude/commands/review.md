---
description: Run the parallel three-reviewer gate and consolidate the verdict
---
Review the current change: $ARGUMENTS

1. **Dispatch in parallel, independently (`REV-002`):** delegate to the code-reviewer subagent, the security-reviewer subagent, and the scope-reviewer subagent - each reviews the full diff without seeing the others' findings.
2. **Empirical checks (`REV-010`):** in a throwaway copy of the repo (`QG-008`) - red-verify the new tests against the reverted production diff (they must fail); mutation spot-check at least one newly added wiring line; browser-verify any UX-affecting claim against a running build. Record outcomes as REPRODUCED evidence.
3. **Consolidate:** merge the three reports plus the empirical-check outcomes, dedupe overlapping findings (keep the highest severity), group by `REV-003` class (CRITICAL/HIGH/MEDIUM/LOW).
4. **Verdict (`REV-008`):** CRITICAL/HIGH open → REJECTED with the fix-list; MEDIUM/LOW → record as deferred items for `/td`. An implementer never solely approves their own change (`REV-004`); the worklog must show the reviewing actor differs from the implementing actor (`TRACE-006`).
5. After rework, re-run the same parallel pattern - reviewers re-review fresh.
6. Log the verdict + finding counts to the change's worklog (`TRACE-003`).
