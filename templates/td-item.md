# Tech-Debt Item Template

> Small, well-scoped work items - most originate from the `/td` sweep (deferred MEDIUM/LOW findings, dependency majors, expired audit-ignore entries, accumulated justifications). One item per file: `td/TD-NNN-short-title.md`.

---

## Frontmatter to copy

```yaml
---
title: <short descriptive title>
tags:
  - tech-debt
  - <backend / frontend / contract / db / pipeline / security / tooling / rules>
status: open            # open / scheduled / done / wont-do
effort: <S / M / L>     # S = under an hour, M = part of a story, L = own story
priority: <high / medium / low>
source: <rule ID or review finding, e.g. REV-003 MEDIUM, SEC-009, CI-009-major>
created: <YYYY-MM-DD>
revisit-by: <YYYY-MM-DD or "-">   # hard date for time-boxed debt (e.g. an audit-ignore entry)
---
```

## Body sections to fill in

### What
The debt in one or two sentences.

### Why it's debt
Which rule/standard it strains (cite the ID) and what it costs while it lives.

### Where
Files / module / pipeline job.

### Suggested fix
Sketch of the resolution; note if it needs a `/spec-propose` (L) or rides along a related story (S/M).

### Exit criteria
Observable condition that closes the item (e.g. "finding no longer reported", "dependency on vX.Y", "audit-ignore entry removed").
