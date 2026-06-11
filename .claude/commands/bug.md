---
description: Bug workflow - triage, reproduce as failing test, fix under the circuit breaker
---
Bug: $ARGUMENTS

1. **Intake:** if no report exists yet, file one from `templates/bug-report.md` (`bugs/BUG-NNN-...`) as a **complete brief** - evidence label, root cause (verified or marked suspected), fix sketch, acceptance criteria, dedupe check. A fixer must need nothing beyond the ticket. **Triage:** delegate to the triage subagent for reproduce path, affected context/layer, suspected cause, severity suggestion (`REV-003` scale). No fixing yet.
2. **Reproduce as a failing test (`PRIN-III`):** the bug becomes a red test at the right honeycomb layer (`TEST-001/002`, marker per `TEST-012`) before any fix. If it can't be reproduced in a test, escalate.
3. **Fix:** minimal change (PRIN-IX), red → green, no drive-by refactors. Circuit breaker applies (`QG-007`): 3 retries / 5 distinct failures → stop and escalate with state.
4. **Review:** run `/review` on the fix.
5. Update the work item in the project tracker per docs in `.claude/docs/` if present.
6. Worklog the trail (`TRACE-003`); if the bug revealed a rule/process gap, note it for `/retrospective`.
