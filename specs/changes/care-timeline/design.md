# Design - care-timeline (US-3.4)

Two lanes: backend (the `/timeline` read) then frontend (the page + component). Backend
lands first; the frontend builds to the contract below.

## Backend

```
application/timeline.py    TimelineQueryService.for_plant(plant_id) -> list[TimelineEntry]
                           (ARCH-006 read-only join of events + photos; no writes)
domain (or app) types      TimelineEntry: a tagged shape (event | photo)
adapters/inbound/web       timeline router GET /plants/{id}/timeline + response schema
                           get_timeline_query_service dependency + factory wiring
```

Reuse existing repos (no new persistence): `CareEventRepository.list_for_plant` (already
ordered happened_on desc, created_at desc) and `PhotoRepository.list_for_plant`. The
service:
1. events = event_repo.list_for_plant(id)
2. photos = photo_repo.list_for_plant(id)
3. linked = {e.photo_id for e in events if e.photo_id} - photo ids shown via their event
4. emit event entries (each carrying its inline photo when photo_id set) +
   photo entries for photos whose id not in `linked`
5. sort by (date, created_at) desc; date = happened_on for events, created_at.date() for
   photos. Plant-exists guard first -> 404 if missing.

Bounded queries (two list reads + the in-memory merge); no per-entry query. Dual-engine
portable (the repos already are).

### Response contract (the FE builds to this)

```
GET /api/v1/plants/{id}/timeline -> 200
[ { "kind":"event","date":"2026-06-10","event_type":"observe","note":"new leaf",
    "health":"good","photo":{"id":12,"url":"/api/v1/plants/3/photos/12"} },
  { "kind":"photo","date":"2026-06-09","photo":{"id":11,"url":".../photos/11"} } ]
```
404 `{detail}` (plant-reason, no PII) when the plant is missing.

## Frontend

```
lib/api/timeline.ts        types (discriminated union) + getTimeline(plantId)
features/plants/PlantDetailPage.tsx   /plants/:id route; header (name + back) + <CareTimeline>
features/plants/CareTimeline.tsx      the feed component
App.tsx                    add the /plants/:id route
PlantsPage                 link each card/row to /plants/{id}
```

- `CareTimeline`: load on mount; entries newest-first; per-`event_type` icon+label
  (water/feed/repot/observe distinct); observe shows the health chip; event photo + photo
  entries render the thumbnail (reuse `photoUrl`/existing thumb recipe); empty state;
  phone-first layout (single column, touch targets).
- Keep `PlantDetailPage` minimal - it is a US-4.3 precursor; do not build attributes/
  schedules/next-due/gallery here.

## Test focus (-> test-foundation)

backend: merge order incl. backdated event by happened_on; event-with-photo emits once
(not duplicated as a photo entry); standalone photo emits as kind:photo; mixed same-day
tiebreak; empty history -> []; missing plant -> 404 plant-reason; bounded query count;
dual-engine. frontend: each event type renders distinctly; observe health; inline photo;
photo entry; empty state; route reachable + back link; client maps the union correctly.
acceptance (production path): open /plants/{id}, see the feed, zero console errors, phone
+ desktop screenshots.

## What this does NOT change

events/photos write paths or their endpoints; the schedules/due field; the plant list
shape (only adds a navigation link). No migration (read-only). The photobook is separate.
