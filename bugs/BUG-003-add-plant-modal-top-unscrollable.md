---
title: Add-plant modal top is cut off and unscrollable on mobile
tags:
  - bug
  - frontend
  - a11y
status: open
severity: high
evidence: static-read
created: 2026-06-16
related-change: mobile-soak-fixes
work-item: "-"
---

### Observed behavior
Opening "Add plant" on the Galaxy S25+ spawns a modal whose first visible field is
"Room". The fields above it (Name, Species) are off the top of the screen and there
is no way to scroll up to them, so the plant cannot be named.

### Expected behavior
The whole add-plant form is reachable on a phone: the modal fits the viewport and
its body scrolls so every field (starting at Name) can be seen and filled.

### Steps to reproduce
1. On a phone-width viewport, go to Plants and tap "Add plant".
2. The modal opens bottom-aligned; the top fields are clipped above the viewport and
   the modal does not scroll.

### Root cause
**Verified by code read.** `frontend/src/components/ui/Modal.tsx:32-47`: the
backdrop is `flex items-end justify-center ... sm:items-center` (bottom-aligned on
phones) and the dialog is `flex w-full max-w-md flex-col gap-4 ... p-5` with **no
max-height and no scroll container**. When the form is taller than the viewport the
dialog grows past the top edge with nothing to scroll, so the upper fields are
unreachable.

### Fix sketch
In `Modal.tsx`: cap the dialog height (`max-h-[calc(100dvh-2rem)]` - the backdrop
has `p-4`), keep the title row `shrink-0`, and wrap `{children}` in a
`min-h-0 flex-1 overflow-y-auto` scroll container. Generic primitive fix - benefits
every modal (incl. edit-plant, log-care). Blast radius: `Modal.tsx` only.

### Acceptance criteria
- [ ] A Playwright spec at S25+ reproduces the unreachable top field (red) and now
      passes: after opening Add-plant, the "Name" field is in-viewport (scrolled to
      if needed) and fillable.
- [ ] The modal never exceeds the viewport height; its body scrolls.

### Dedupe check
`bugs/` searched - no prior modal-scroll ticket. Distinct from BUG-001/002
(header overflow) though both are mobile-layout.

### Context
- **Environment:** local (soak)
- **DB engine:** n/a
- **Version/commit:** f041608
- **Surface:** Plants page, add-plant modal (`PlantFormModal` in `Modal`)
- **Browser/OS:** Samsung Internet / Chrome, Android (Galaxy S25+)

### Notes
Fixing the shared `Modal` primitive fixes all modals at once (single
responsibility, PRIN-IX).
