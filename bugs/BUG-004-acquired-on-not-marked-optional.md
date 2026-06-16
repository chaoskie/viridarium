---
title: "Acquired on" date is not marked optional
tags:
  - bug
  - frontend
status: open
severity: low
evidence: static-read
created: 2026-06-16
related-change: mobile-soak-fixes
work-item: "-"
---

### Observed behavior
Users who have owned a plant for a long time don't know its acquisition date, and
the "Acquired on" field gives no signal that it can be left blank - it reads as
required.

### Expected behavior
The field clearly communicates it is optional; leaving it blank saves the plant
without error.

### Steps to reproduce
1. Open Add-plant.
2. Note "Acquired on" has no "(optional)" marker or hint, unlike its actual
   (optional) nature.

### Root cause
**Verified by code read.** The field is already optional end-to-end -
`domain/plant.py` `acquired_on: date | None`, the DB column is `nullable=True`, the
Pydantic schema defaults it to `None`, and `PlantFormModal.tsx` renders a bare
`<input type="date">` with no `required`. The gap is purely communicative: no label
hint tells the user it's optional.

### Fix sketch
In `frontend/src/features/plants/PlantFormModal.tsx`: label the field
"Acquired on (optional)" and add a short hint ("Leave blank if you don't know").
No backend change. Blast radius: one form field.

### Acceptance criteria
- [ ] A Vitest test asserts the optional marker/hint renders for the date field.
- [ ] Submitting with "Acquired on" blank succeeds (already true; covered by the
      partial-fill test added in this batch).

### Dedupe check
`bugs/` searched - none.

### Context
- **Environment:** local (soak)
- **DB engine:** n/a
- **Version/commit:** f041608
- **Surface:** add/edit plant form
- **Browser/OS:** any

### Notes
A future enhancement (approximate / year-only acquisition) is out of scope here; this
ticket is the label/hint only.
