# Traceability (`TRACE-*`)

**Enforces:** the concrete standard behind [[00-constitution#PRIN-XI Traceability|PRIN-XI]]: every unit of work leaves a reconstructable trail - who (agent/user) did what, when, to which artifact, under which decision. The worklog *template* (layout + AI logging guidance) is a separate artifact; this file defines what it must satisfy.

---

### TRACE-001 — Worklog per change
Every change maintains a worklog at **`specs/changes/<change-name>/worklog.md`**, created at propose-time and archived with the change (moves to `specs/archive/<change-name>/worklog.md`). A change without a complete worklog is not done.
*Targets:* all agents, spec-propose, spec-archive, DoD template.

### TRACE-002 — Central change index
A thin index lists every change in one glance: *what* was done, *why* (one line each), and *where* the details live (link to the change folder/worklog). Updated at archive-time (`spec-archive`); newest first. (The index file lives where the docs workstream places it; if a project change-index doc exists under `.claude/docs/`, update it there.)
*Targets:* spec-archive, design work.

### TRACE-003 — Entry fields
Every worklog entry carries at minimum: **timestamp · actor · action · artifact touched · decision/rule reference**. Layout and phrasing are defined by the worklog template.
*Targets:* worklog template, all agents.

### TRACE-004 — What gets logged
Logging scope is governed by the **worklog template's AI logging guidance**. The minimum set is: fork/design decisions, gate-check results (QG-004), escalations (QG-007), review verdicts (REV-003), commits, and spec lifecycle transitions.
*Targets:* all agents, worklog template.

### TRACE-005 — Decisions link to their records
Every logged decision references its record (ADR per ARCH-010, design note, or spec section). A gate-check entry links the posted PASS/FAIL results. No naked "we decided X".
*Targets:* all agents, design work.

### TRACE-006 — Actor attribution
Every AI-authored entry names the **agent role and model tier** that acted (e.g. `test-engineer/HIGH`); human entries name the actor. "Actor" must be auditable, not generic.
*Targets:* all agents.

### TRACE-007 → QG-012
Worklog presence + completeness is a DoD checklist item - aggregated by the DoD gate. Not restated.
