# Design - plant-detail (US-4.3)

Frontend-only expansion of `frontend/src/features/plants/PlantDetailPage.tsx`. No
backend delta; data sources are the existing clients.

## Data flow

- `fetchPlant(id)` (existing) - attributes, tags, `schedules: ScheduleDue[]`
  (`next_due`, `overdue_days`), `cover_photo_id`, cachepot fields.
- `usePhotos(plantId)` (existing hook) - gallery list + mutations, already powers
  `PhotoGalleryModal`.
- `CareTimeline` (existing) - history feed, unchanged.
- Locations: plant carries its location id/name via the existing response shape; the
  header links to the rooms view.

A single `usePlantDetail(plantId)` local hook (or extension of the current inline
state machine) owns `loading | ready | error` plus a `reload()` used as the
`onMutated` callback for every modal, mirroring the `usePlants` reload-after-mutation
pattern.

## Component structure (PRIN-I: keep PlantDetailPage thin)

```
PlantDetailPage            - route shell, state machine, modal orchestration
├─ PlantDetailHeader       - name, species, location, archived badge, action buttons
├─ PlantAttributesCard     - acquired, pot + cachepot, light, notes, tags (omit-empty)
├─ PlantSchedulesCard      - per-schedule row: type icon, interval, next-due/overdue
│                            emphasis, paused/dormant reason; empty state
├─ PlantGallery            - cover + thumbnail strip (~8 + "+N"), opens PhotoGalleryModal
└─ CareTimeline            - existing, unchanged
```

Reused as-is: `PlantFormModal`, `LogCareModal`, `QuickCareActions` (or `LogCareModal`
directly if QuickCareActions is Today-specific), `CareScheduleModal`,
`DeletePlantDialog`, `PhotoGalleryModal`. Any prop mismatch is resolved by adapting
the detail page to the component, not by modifying the shared component (PRIN-IX);
if a shared component genuinely cannot be reused without change, stop and flag.

## Behaviour notes

- Next-due emphasis mirrors the Today view's overdue styling tokens (consistency over
  novelty; usability-over-flourish).
- Delete success navigates to `/plants` (`useNavigate`), no orphaned detail view.
- Mutations refetch the plant (`reload()`); `CareTimeline` gets a refresh key bump on
  care-event/photo mutations so the feed stays consistent.
- Empty/error/loading states copy the foundation patterns from PlantsPage/Today.
- Phone-first layout: single column stacking header → attributes → schedules →
  gallery → timeline; desktop may two-column attributes/schedules.

## Tests (TEST-*)

Component tests per new card (rendering matrix incl. omit-empty, overdue, paused,
empty states), page-level integration test (modals open, mutation triggers refetch,
delete navigates), keeping the existing PlantDetailPage tests green or consciously
superseded. E2E: extend the existing Playwright acceptance flow with a detail-page
pass; FE-012 phone+desktop screenshots on the production path.
