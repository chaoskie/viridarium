---
title: Long unbroken field values break mobile layout (display-side)
tags:
  - bug
  - frontend
  - a11y
status: open
severity: medium
evidence: static-read
created: 2026-06-16
related-change: mobile-soak-fixes
work-item: "-"
---

### Observed behavior
A plant whose name, species, tag, or notes contains a long *unbroken* string (a
spaceless 120-char name, a 50-char tag, a pasted URL) renders as a single long line
and pushes the layout wider than a phone screen, causing horizontal scroll.

### Expected behavior
Long values wrap (or truncate where a single line is intended) and never cause
horizontal overflow at phone width (FE-011: "no horizontal scroll").

### Steps to reproduce
1. Create a plant with a long no-space name/species/tag (each within the input caps:
   name ≤120, species ≤200, tag ≤50).
2. View the Plants list / plant detail at S25+ width - the row/header overflows
   horizontally.

### Root cause
**Verified by code read.** *Input* validation is already complete and dual-engine
safe - Pydantic caps every field (`schemas.py`: name 1-120, species ≤200, notes
≤10000, `pot_size_cm` 1-500, tags ≤50 items × ≤50 chars each, matching the
`String(50)` tag column) and the form mirrors with `maxLength` / number `min/max` /
422 handling. The defect is **display-side**: a grep of `frontend/src/features/plants/`
finds **no** `break-words` / `truncate` / `overflow-wrap` on any component that
renders user values, so a long unbroken value overflows its container.

### Fix sketch
Add render-side wrapping to the plant value components in
`frontend/src/features/plants/`: `break-words` on multi-line values (detail header,
notes), `truncate` / `line-clamp` where a single line is intended (list rows, tag
chips). No backend / validation change - input side is already correct.

### Acceptance criteria
- [ ] A Playwright spec at S25+ creates a plant with a long unbroken value and
      asserts no horizontal overflow on the list and detail views (red first).
- [ ] Long values are visibly wrapped/truncated, not clipped off-screen.

### Dedupe check
`bugs/` searched. Same failure *class* as `BUG-001-mobile-header-horizontal-overflow`
(horizontal overflow at phone width) but a distinct cause (content, not chrome);
filed separately, cross-referenced.

### Context
- **Environment:** local (soak)
- **DB engine:** n/a (display); input validation verified on both engines via the
  per-tag cap matching `String(50)`
- **Version/commit:** f041608
- **Surface:** Plants list, plant detail, tag chips
- **Browser/OS:** Samsung Internet / Chrome, Android (Galaxy S25+)

### Notes
Surfaced from the user's input-hardening question during soak. The input side needs
no change; only rendering. Edge-case form tests (partial-fill, empty-required,
over-length) are added alongside in this batch.
