# Proposal - plant-detail (US-4.3)

Status: PROPOSED 2026-07-06. Story US-4.3 "Plant detail page". Spec: product-spec §4
US-4.3 ("attributes, schedules, next-due, history, gallery"). Roadmap phase v0.2.
Expands the minimal `/plants/{id}` route that US-3.4 (care-timeline) introduced as an
explicit US-4.3 precursor.

## Story (SPEC-004)

As a plant owner, I want a plant's detail page to show everything about that plant in
one place (attributes, care schedules with next-due, photo gallery, care history) and
let me act from there (log care, edit, manage schedules), so that I don't have to hunt
across the list view for a plant I'm already looking at.

## PO-resolved decisions (2026-07-06, at pickup)

1. **Gallery**: inline on the page - cover photo prominent plus a thumbnail strip;
   tapping opens the existing `PhotoGalleryModal` for full view/manage.
2. **Actions**: not read-only. Reuse the already-built modals from the list page:
   `PlantFormModal` (edit), `LogCareModal` / `QuickCareActions` (log care),
   `CareScheduleModal` (schedules), `DeletePlantDialog` (delete). No new mutation
   surfaces are invented; the detail page wires existing components.

## Scope

Frontend-only. `GET /api/v1/plants/{id}` already returns attributes, tags,
`schedules[]` (with `next_due`/`overdue_days` per ARCH-007), `cover_photo_id`, and
cachepot fields; photos come from the existing photos client (`usePhotos`); history is
the merged `CareTimeline` already on the page. **No backend change, no API delta
(API-001: none), no migration.**

Sections on the expanded page (phone-first, NFR §7):

- **Header**: name, species, location link, archived badge; actions (edit, log care,
  schedules, delete) - existing modals.
- **Attributes card**: acquired date, pot (inner + cachepot), light level, notes, tags.
  Fields with no value are omitted, not rendered empty.
- **Schedules card**: per enabled schedule - type and next-due date with overdue
  emphasis; paused/dormant state shown when `next_due` is null. Empty state links to
  schedule setup. *(Amended at review 2026-07-06: "interval summary" dropped - the
  `ScheduleDue` API contract carries no interval data and a backend delta is out of
  scope; scope-reviewer ruled the omission the correct reading.)*
- **Gallery**: cover photo + thumbnail strip; opens `PhotoGalleryModal`.
- **Timeline**: the existing `CareTimeline`, unchanged.

After any mutation (edit/log/schedule/photo/delete) the page refetches the plant so
schedules/next-due/cover stay fresh; delete navigates back to the list.

## Out of scope (SPEC-001)

US-4.2 Upcoming view, US-3.6 snooze/skip, US-3.7 bulk actions, any backend change, the
photobook candidate, archive/unarchive UI beyond what the existing modals already do,
and any redesign of the reused modals.

## Acceptance criteria

- **AC1**: `/plants/{id}` shows the attribute set (species, acquired, pot + cachepot,
  light, notes, tags, location); absent optional fields are omitted.
- **AC2**: each enabled schedule renders with its next-due date; an overdue schedule is
  visually emphasized; a paused/dormant schedule (null `next_due`) states why instead
  of showing a date; a plant with no schedules shows an empty state.
- **AC3**: cover photo and thumbnails render; tapping opens the existing gallery modal;
  a plant with no photos shows the gallery empty state.
- **AC4**: edit, log-care, schedule, and delete actions work from the detail page via
  the existing modals; after each mutation the visible data refreshes without a manual
  reload; delete returns to `/plants`.
- **AC5**: invalid/missing plant id keeps the existing not-found handling; loading and
  error states match foundation patterns.
- **AC6 (FE-012)**: verified on the production path (built SPA through the backend),
  phone + desktop breakpoints, zero console errors; screenshots committed.

## Sizing (SPEC-004)

~300-400 LOC new frontend logic + tests; 1 day. Single lane (frontend only), within
the per-story budget. Agent roles: main session specs + orchestrates; build agent
implements; test-engineer authors the foundation; three-reviewer gate before merge.

## Logging / security (DoR 6)

No new endpoints, no trust-boundary change, no logging-relevant events beyond existing
mutations (SEC-008 status quo, tracked v0.3).

## Open questions

Assumption (non-scope-affecting): the thumbnail strip shows up to the first ~8 photos
with a "+N" overflow opening the modal; exact count is a layout call at build time.

Open questions: none
