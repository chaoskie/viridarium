# Proposal - care-timeline (US-3.4)

Status: PRE-STAGED 2026-06-14 (DoR-ready; build resumes next session). Story US-3.4
"Care history timeline per plant". Spec: product-spec §4 US-3.4. Depends on US-3.2
(events) - merged. PO answered the placement questions 2026-06-14 (below).

## Story (SPEC-004)

As a plant owner, I want to open a plant and see everything that ever happened to it
(care events with their photos, newest first), so that I have its full history at a glance.

## PO-resolved decisions (2026-06-14, ticket #13)

1. **Where it renders**: on the plant's **details page**, as its own component. The full
   details page is US-4.3 (v0.2) and does not exist yet, so US-3.4 introduces a **minimal
   `/plants/{id}` route** (plant-name header + back link + the timeline component) - an
   explicit **US-4.3 precursor** that US-4.3 later expands (attributes, schedules,
   next-due, gallery).
2. **Data**: **API-first** - a backend `GET /api/v1/plants/{id}/timeline` read merges the
   sources server-side; the frontend renders the merged feed (no client-side join).
3. **Photos**: a photo attached to a care event (US-3.2 inline upload) renders **inline
   with that event**, shown **once** (never also as a standalone entry). Richer photo
   browsing is a **separate future feature**: a per-plant **photobook** with tabbed
   sections (filed as a candidate, NOT this story).

### Residual assumption to confirm at build (low-cost to flip)

Standalone photos (uploaded directly, not linked to any event) **do** interleave into the
timeline by their `created_at` date, per the spec's "photos appear inline at their date."
If the PO prefers an **events-only timeline** (all photo browsing deferred to the
photobook), dropping standalone-photo entries is a small change. Proceeding on the
spec-faithful interleave; flag confirmed at build pickup.

## Backend (ARCH-006 query module)

`GET /api/v1/plants/{id}/timeline` -> 200, a reverse-chronological list of entries; 404
if the plant is missing (plant-exists guard first, the VIRIDARIUM-48 convention).

A read joining two contexts (care events + photos) -> a dedicated query module
`application/timeline.py` (no writes). Entry as a discriminated shape:

```
{ "kind": "event", "date": <happened_on>, "event_type": water|feed|repot|observe,
  "note": str|null, "health": good|fair|bad|null, "photo": {id, url}|null }
{ "kind": "photo", "date": <created_at date>, "photo": {id, url} }
```

- **Sort**: by `date` desc (events use `happened_on`, photos use `created_at`'s date);
  tiebreak on the underlying `created_at` timestamp desc so backdated events and
  same-day items order stably (reuse the US-3.2 ordering contract intent).
- **Dedup**: a photo whose id is referenced by some event's `photo_id` is emitted ONLY in
  that event entry, never as a `kind:"photo"` entry. Standalone photos (unreferenced) emit
  as `kind:"photo"`.
- Bounded query count (load the plant's events once + photos once + the set of
  event-referenced photo ids; merge in memory). Dual-engine portable (ARCH-011).

## Frontend (UI story - FE-012 screenshots, TEST-010 production path)

- New `/plants/{id}` route -> `PlantDetailPage`: a thin header (plant name, back to list)
  hosting `<CareTimeline plantId>`. Reachable via a link on each plant card/row in the list.
- `CareTimeline` component: fetches `/timeline`, renders entries newest-first;
  **distinct rendering per event type** (water/feed/repot/observe) with an icon/label;
  observe entries show the health rating; event photos render inline; `kind:"photo"`
  entries render the image with its date; **empty state** for a plant with no history;
  **phone-first**, usable one-handed (NFR §7).
- `lib/api/timeline.ts` client mirroring existing slices.

## Out of scope (SPEC-001)

The full details page (US-4.3: attributes/schedules/next-due/gallery), the **photobook**
feature (separate candidate), snooze/skip, any write path, any change to events/photos
endpoints. The `/plants/{id}` route is intentionally minimal here.

## Acceptance criteria

- **AC1**: `GET /plants/{id}/timeline` returns events + standalone photos merged, newest
  first; backdated events sort by `happened_on`, not creation time.
- **AC2**: an event with an attached photo emits one entry (the event, photo inline); that
  photo never appears as a separate `kind:"photo"` entry.
- **AC3**: a standalone photo (no event link) appears as a `kind:"photo"` entry at its date.
- **AC4**: missing plant -> 404 (plant-reason, no PII); bounded query count regardless of
  history size; runs on SQLite + Postgres.
- **AC5 (FE)**: all four event types render distinctly; observe shows health; photos render
  inline; empty state for a new plant; the `/plants/{id}` page is reachable from the list.
- **AC6 (FE)**: verified on the production path (built SPA through the backend), phone +
  desktop breakpoints, zero console errors; screenshots committed (FE-012).

## Open questions

none blocking. (Placement/data/photo decisions PO-resolved; the standalone-photo-interleave
assumption above is flagged for a 5-second confirm at build pickup, default = interleave.)
