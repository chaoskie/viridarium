---
title: Photo gallery shows only a cropped thumbnail segment with no way to view the full image
tags:
  - bug
  - frontend
status: open
severity: medium
evidence: reproduced
created: 2026-06-17
related-change: photos (US-2.3)
work-item: VIRIDARIUM-73
---

## Observed behavior
In the per-plant photo gallery (`PhotoGalleryModal`), each photo renders as a
96x96 `object-cover` square (`THUMB_CLASSES`), so a non-square photo shows only a
cropped centre segment. There is no way to open the whole image - the full-size
bytes are shipped to the grid and then CSS-cropped, so the user can neither see
the full photo nor benefit from the bytes downloaded.

## Expected behavior
The user can view the full, uncropped image. Selecting a thumbnail opens the
complete photo (contained, not cropped); they can return to the grid.

## Steps to reproduce
1. Open a plant's "Photos" modal with at least one non-square photo.
2. Observe each grid cell shows only a cropped square segment.
3. There is no control to view the full image.

## Root cause
`frontend/src/features/plants/PhotoGalleryModal.tsx`. The grid renders each photo
directly as a small `object-cover` `<img>` (`THUMB_CLASSES`, line 26-27) with no
"open full image" affordance. The crop is the intended thumbnail behaviour; the
real defect is the absence of any full-image view.

## Fix sketch
Add a full-image view inside the existing gallery modal (do NOT stack a second
`Modal` - two dialogs both bind a document `Escape` listener, so one Esc would
close both). Make each thumbnail a `<button>` that selects a photo into local
`viewing` state; when set, the modal body swaps the grid for the full image
(`object-contain`, height-capped, `w-full`) plus a "Back to all photos" control.
Reuses `Modal` + `Button` (FE-010), frontend-only, no API change.

Out of scope (deferred): server-side thumbnail *generation* to avoid shipping
full-size bytes into the grid. That needs an image library (Pillow) = a stack
amendment (PRIN-V); filed separately as a candidate. The ticket's fix direction
explicitly allows "generated OR constrained" thumbnails, so the constrained +
full-view approach satisfies it.

## Acceptance criteria
- [ ] The reproduction exists as a failing component test and now passes (`PRIN-III`)
- [ ] Selecting a thumbnail opens the full, uncropped image of that photo
- [ ] A control returns from the full image to the grid
- [ ] The grid, upload, set-cover and delete flows are unchanged
- [ ] FE-012 design-review screenshots (grid + full view) committed

## Dedupe check
`bugs/` searched: BUG-001..007 cover the mobile-soak batch and the care-schedule
state loss - none touch the photo gallery. Nearest: none. Single ticket.

## Context
- **Environment:** reported in soak (mobile)
- **DB engine:** n/a (frontend display)
- **Version/commit:** main @ #50
- **Surface:** `/plants/:id` Photos modal
- **Browser/OS:** Galaxy S25+ (soak); not device-specific
