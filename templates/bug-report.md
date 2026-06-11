# Bug Report Template

> **How to file a bug**
> 1. Copy this file to `bugs/BUG-NNN-short-title.md` (e.g. `BUG-001-schedule-off-by-one.md`)
> 2. Fill in all fields below
> 3. Set `status: open` - open bugs are picked up by the `/bug` workflow

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
