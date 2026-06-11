---
description: Per-story retrospective - capture workflow learnings, apply accepted changes immediately
---
Retrospective for: $ARGUMENTS

Per `LANG-009`:
1. **What happened vs plan:** story scope drift, gate failures (`QG-004` history), circuit-breaker trips (`QG-007`), review finding patterns - pull from the change's worklog.
2. **WATCH sweep (`QG-004`):** collect every WATCH caveat logged since the last retro and dispose of each one explicitly - resolved, converted to a `/td` item, or escalated. A WATCH caveat that leaves this retro without a disposition is a violation.
3. **Cost/effort:** model-tier usage, retry counts, where time went.
4. **Workflow changes:** what should change in rules, agents, or commands? Each proposal cites the rule/agent it amends.
5. **Apply immediately:** accepted changes are applied now (rule edit, agent edit, ADR), not queued. Deferred ones get a `/td` entry.
6. **Distill (`LANG-008`):** write the learnings into the project knowledge notes directly; git is the audit trail.
7. Log the retrospective outcome + any applied amendments to the worklog (`TRACE-003`).
