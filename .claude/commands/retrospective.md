---
description: Per-story retrospective - capture workflow learnings, apply accepted changes immediately
---
Retrospective for: $ARGUMENTS

Per `LANG-009`:
1. **What happened vs plan:** story scope drift, gate failures (`QG-004` history), circuit-breaker trips (`QG-007`), review finding patterns - pull from the change's worklog.
2. **Cost/effort:** model-tier usage, retry counts, where time went.
3. **Workflow changes:** what should change in rules, agents, or commands? Each proposal cites the rule/agent it amends.
4. **Apply immediately:** accepted changes are applied now (rule edit, agent edit, ADR), not queued. Deferred ones get a `/td` entry.
5. **Distill (`LANG-008`):** write the learnings into the project knowledge notes directly; git is the audit trail.
6. Log the retrospective outcome + any applied amendments to the worklog (`TRACE-003`).
