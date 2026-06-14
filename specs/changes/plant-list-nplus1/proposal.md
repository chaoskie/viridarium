# Proposal - plant-list-nplus1 (tech debt)

Status: in progress. Tech-debt change (not a user story): eliminate the two N+1 query
patterns on the plant-list read path. Board: #62 (tag N+1, broadened) + the CoverThumb
sub-item of #41. Relevant NFR: product-spec §7 (p95 < 200 ms for 500 plants). Design is
folded into this proposal (lean tech-debt change).

## Problem

The plant list issues O(N) queries/requests for N plants:

1. **Backend tag N+1**: `plant_repository.list` / `list_archived` call `_load_tags(session,
   m.id)` once per row.
2. **Frontend CoverThumb N+1**: `PlantsPage`'s `CoverThumb` calls `fetchPhotos(plant.id)`
   on mount per card, so the browser fires N photo-list requests to find each `is_cover`.

## Fix (additive, no behaviour change beyond efficiency)

Follow the US-3.3 composition pattern (router composes cross-context read data into
`PlantResponse`; the `Plant` domain stays free of photo concerns).

### Backend

- `plant_repository`: add `_load_tags_batch(session, plant_ids) -> dict[int, tuple[str,
  ...]]` (one grouped query) and use it in `list` + `list_archived`. Single-row reads
  (`get`, etc.) keep `_load_tags` (no N+1 there). Behaviour identical; query count drops
  from N+1 to 2.
- `photo_repository`: add `cover_ids_for_plants(plant_ids) -> dict[int, int]` - one query
  selecting `(plant_id, id)` where `is_cover` and `plant_id IN (...)`. Empty-ids safe.
  Dual-engine portable (ARCH-011).
- `PlantResponse`: additive `cover_photo_id: int | None`. The plants router composes it
  (list: one batch call over the page's ids; detail: the single id) - NOT via
  `model_validate` off the domain `Plant`, exactly like the `schedules` field.
- A `get_*`/dependency for the cover batch mirroring existing providers.

### Frontend

- `CoverThumb` reads `plant.cover_photo_id` and renders `photoUrl(plant.id,
  cover_photo_id)` or the existing "No photo" placeholder. Remove the per-card
  `fetchPhotos` effect. The plant list no longer fetches photos at all.
- `Plant` type gains `cover_photo_id: number | null`.

## Out of scope (PRIN-IX)

PlantsPage decomposition (#41, separate), SEC-008 logging, the due/schedules field,
photo gallery behaviour, any change to the cover-setting flow. No new endpoint (cover id
rides on the existing plant reads).

## Acceptance / tests

- **AC1 (BE tag batch)**: `list` over N plants with tags issues a bounded query count
  (no per-row tag query); tags returned identically to before (per-plant correctness).
- **AC2 (BE cover batch)**: `cover_ids_for_plants` returns the `is_cover` photo id per
  plant, omits plants with no cover, empty-ids safe; runs on SQLite + Postgres.
- **AC3 (contract)**: `GET /plants` and `GET /plants/{id}` include `cover_photo_id`
  (the cover's id, or null when the plant has no cover/photos). Additive; no other shape
  change. List path query count bounded regardless of N (no N+1), asserted via the
  statement-count listener used by the due tests.
- **AC4 (FE)**: `CoverThumb` renders the cover image from `plant.cover_photo_id` without
  any photos fetch; shows the placeholder when null; the plant list fires zero
  per-card photo requests.

## Deviations (comply-or-explain, PRIN-X)

- **Lean track**: this tech-debt change folds `design.md`/`tasks.md` into this proposal
  rather than scaffolding the full SPEC-002 set. The design is present above; the change
  is a focused two-N+1 fix, not a story. (SPEC-002 notes a Light track is anticipated.)
- **`CoverThumb` exported**: the previously module-private `CoverThumb` in `PlantsPage.tsx`
  is now exported so its no-fetch behaviour can be unit-tested in isolation (mirrors the
  already-standalone `QuickCareActions`). Accepted as minimal; the only widened surface.
- **Write-path responses omit `cover_photo_id`** (defaults to `null` on create/update/
  archive/unarchive), exactly like the existing `schedules` field - those handlers don't
  compose read-model data. Callers needing it use `GET /plants/{id}`. AC3 covers the GET
  paths only.

## Open questions

none. (Internal perf/contract improvement; the additive `cover_photo_id` shape is the
recorded design decision, consistent with the existing id-based response boundary.)
