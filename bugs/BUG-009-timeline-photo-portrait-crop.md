---
title: Care timeline crops portrait (taller-than-wide) photos into a wide band
tags:
  - bug
  - frontend
status: open
severity: medium
evidence: reproduced
created: 2026-06-17
related-change: care-timeline (US-3.4)
work-item: VIRIDARIUM-73
---

## Observed behavior
On the plant detail page, the care timeline renders each photo with
`max-h-64 w-full ... object-cover`. `object-cover` fills the full-width,
256px-tall box by cropping, so a portrait (taller-than-wide) photo is cut down
to a wide centre band and most of the image is hidden.

## Expected behavior
The timeline shows the whole photo, uncropped, regardless of its aspect ratio.
A tall photo is contained within the height cap (letterboxed), not cropped.

## Steps to reproduce
1. Upload a portrait photo to a plant.
2. Open the plant detail page and view the timeline.
3. Observe the photo is cropped to a wide band (top/bottom of the image lost).

## Root cause
`frontend/src/features/plants/CareTimeline.tsx`, `TimelinePhotoImage`
(line ~64): `object-cover` crops the image to fill the `w-full max-h-64` box.
This is the same crop class family as the photo-gallery grid (BUG-008) but a
SEPARATE surface - BUG-008 fixed `PhotoGalleryModal`, not the timeline.

## Fix sketch
Change the timeline photo image from `object-cover` to `object-contain` so the
whole image fits within the `max-h-64` cap without cropping. One className
change on `TimelinePhotoImage`. No API change. (Timeline photos are a history
feed, meant to show the actual photo, unlike a deliberately-square cover
thumbnail where cropping is acceptable.)

## Acceptance criteria
- [ ] The reproduction exists as a failing test and now passes (`PRIN-III`)
- [ ] Timeline photos render uncropped (object-contain), portrait included
- [ ] FE-012 design-review screenshot of a portrait photo in the timeline committed

## Dedupe check
`bugs/` searched: BUG-008 is the photo-gallery MODAL crop + full view (different
component). This ticket is the detail-page TIMELINE. Related, not duplicate.

## Context
- **Environment:** reported by maintainer from a live portrait upload (Anthurium Oma)
- **DB engine:** n/a (frontend display)
- **Version/commit:** main @ #51
- **Surface:** `/plants/:id` care timeline
- **Browser/OS:** not device-specific
