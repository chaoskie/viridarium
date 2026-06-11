# Bug Report Template

> **How to file a bug**
> 1. Copy this file to `bugs/BUG-NNN-short-title.md` (e.g. `BUG-001-schedule-off-by-one.md`)
> 2. Fill in all fields below
> 3. Set `status: open` - open bugs are picked up by the `/bug` workflow
>
> **Ticket-as-brief standard:** a bug report is a complete brief - a fixer (agent or human) picking it up needs nothing beyond this file. Filing time is where review quality is bought; the root cause, fix sketch, acceptance criteria, and dedupe check below are not optional garnish. *(Adopted 2026-06-11 from sibling-project retros.)*

---

## Frontmatter to copy

```yaml
---
title: <short descriptive title>
tags:
  - bug
  - <backend / frontend / contract / db / pipeline / security / a11y / performance>
status: open
severity: <critical / high / medium / low>   # REV-003 scale
evidence: <reproduced / static-read>         # static-read = claim unverified; reproduce before fixing
created: <YYYY-MM-DD>
related-change: <change name or "unknown">
work-item: <tracker id or "-">
---
```

## Body sections to fill in

### Observed behavior
What actually happens. Be specific: exact error message, response code, wrong value.

### Expected behavior
What should happen instead. Cite the spec/AC or rule if applicable (`SPEC-001`).

### Steps to reproduce
1. Step one (exact request / click path / command)
2. ...

### Root cause
File, function, and mechanism. With `evidence: reproduced`, state the cause as verified fact. With `evidence: static-read`, label it **suspected** - the fixer re-verifies before changing code, and refuting the claim is a first-class outcome.

### Fix sketch
The smallest change that addresses the cause: files to touch, approach, blast radius. A sketch, not a patch - the fixer may deviate with a one-line justification in the worklog.

### Acceptance criteria
- [ ] The reproduction exists as a failing test at the right layer and now passes (`/bug` step 2, `PRIN-III`)
- [ ] <observable outcome restating the expected behavior, one per line>

### Dedupe check
`bugs/` and the change index searched for the same symptom or cause; nearest matches listed here (or "none"). A duplicate gets a cross-reference on the existing ticket, not a second ticket.

### Context
- **Environment:** local / CI / production
- **DB engine:** SQLite / PostgreSQL (note if engine-specific - `ARCH-011`)
- **Version/commit:** app version or commit SHA
- **Surface:** endpoint (`/api/v1/...`) or page/route
- **Browser/OS:** (UI bugs only)
- **Logs/trace:** relevant log lines or correlation id (no sensitive data / no PII - `SEC-007`)
- **Screenshot/recording:** path or attachment (ephemeral, not committed - `TEST-011`)

### Notes
Related bugs, workarounds, first suspicion of the affected layer/context.
