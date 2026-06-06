---
description: Run the parallel three-reviewer gate and consolidate the verdict
---
Review the current change: $ARGUMENTS

1. **Dispatch in parallel, independently (`REV-002`):** delegate to the code-reviewer subagent, the security-reviewer subagent, and the scope-reviewer subagent - each reviews the full diff without seeing the others' findings.
2. **Consolidate:** merge the three reports, dedupe overlapping findings (keep the highest severity), group by `REV-003` class (CRITICAL/HIGH/MEDIUM/LOW).
3. **Verdict (`REV-008`):** CRITICAL/HIGH open → REJECTED with the fix-list; MEDIUM/LOW → record as deferred items for `/td`. An implementer never solely approves their own change (`REV-004`).
4. After rework, re-run the same parallel pattern - reviewers re-review fresh.
5. Log the verdict + finding counts to the change's worklog (`TRACE-003`).
