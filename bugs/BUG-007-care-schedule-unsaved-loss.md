---
title: Editing care schedules loses unsaved values (water cleared when feeding saved)
tags:
  - bug
  - frontend
status: open
severity: high
evidence: reproduced
created: 2026-06-17
related-change: care-schedules (US-3.1)
work-item: VIRIDARIUM-72
---

## Observed behavior
In the per-plant care-schedule editor (`CareScheduleModal`): type watering details
into the Water section, then - without clicking the Water "Save" - switch to the
Feed section and click its "Save". The watering values just typed are wiped back
to their server/default state.

## Expected behavior
Saving one care-type section MUST NOT discard unsaved local edits in the sibling
section. After saving Feed, the values typed into Water remain intact (AC).

## Steps to reproduce
1. Open a plant's "Schedules" modal (plant with no existing schedules is enough).
2. In the Water section type an interval (e.g. `7`).
3. In the Feed section type an interval (e.g. `14`) and click Feed "Save".
4. Observe: the Water interval field is now empty again.

## Root cause
`frontend/src/features/plants/CareScheduleModal.tsx` + `useCareSchedules.ts`.
Mechanism (verified): every `upsert`/`remove` calls `reload()`
(`useCareSchedules.ts:52`), which sets `loading = true`. The modal gates the
*entire* section list behind `loading` (`CareScheduleModal.tsx:283`), so during
the post-save refetch BOTH `ScheduleSection`s unmount and are replaced by the
"Loading schedules..." placeholder. When the reload resolves they remount fresh,
each re-initializing its `useState` from `existing` (server data) - so the
sibling section's typed-but-unsaved local state is gone. The per-section `key`
(`...updated_at ?? "new"`) correctly resets only the *saved* section; the loss is
caused purely by the blanket loading-placeholder swap.

## Fix sketch
Gate the loading placeholder on the **initial** load only, not on
reload-after-mutation. Add an `initialLoading` flag to `useCareSchedules` (true
until the first fetch resolves; never re-armed by `reload()`), and have the modal
render the placeholder on `initialLoading` instead of `loading`. Sections then
stay mounted across a sibling save; the saved section still re-keys on its new
`updated_at`. Smallest change: hook + one line in the modal. `usePhotos` shares
the identical reload-sets-loading shape - check whether it has the same
user-visible defect before widening scope (PRIN-IX: only fix it if reproducible).

## Acceptance criteria
- [ ] The reproduction exists as a failing component test and now passes (`PRIN-III`)
- [ ] After saving the Feed section, unsaved Water values remain intact
- [ ] The initial "Loading schedules..." placeholder still shows on first open
- [ ] No remount/refetch regression: a saved section still reflects server data

## Dedupe check
`bugs/` searched: BUG-001..006 are the mobile-soak batch (header overflow, theme
toggle, modal scroll, optional date, long-value wrap, starlette CVEs) - none
touch care-schedule form state. Nearest: none. Single ticket.

## Context
- **Environment:** reported in soak (mobile), reproduces in jsdom component test
- **DB engine:** n/a (pure frontend state)
- **Version/commit:** main @ cachepot merge (#49)
- **Surface:** `/plants/:id` Schedules modal
- **Browser/OS:** Galaxy S25+ (soak); not device-specific
