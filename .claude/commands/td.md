---
description: Tech-debt sweep - collect, prioritize, and ticket deferred debt
---
Tech-debt sweep: $ARGUMENTS

Delegate to the triage subagent to collect into one prioritized list:
1. Deferred MEDIUM/LOW review findings (`REV-003`) not yet ticketed.
2. Dependency-update **major** PRs awaiting review (`CI-009`).
3. Dependency-audit ignore/allow entries past their revisit date (`SEC-009`).
4. File-ceiling and complexity justifications that have accumulated (`QG-009`, PRIN-I).
5. OPEN markers in rules/specs (e.g. pending decisions) older than one iteration.

For each item: file/update a `td/TD-NNN-...` item from `templates/td-item.md` (what, why-it's-debt w/ rule ID, where, suggested fix, exit criteria, effort S/M/L). Output the prioritized list. Do not fix anything - fixes go through `/spec-propose` or `/bug`.

Update the project tracker per docs in `.claude/docs/` if present, and log the sweep to the worklog if it attaches to an active change (`TRACE-003`).
