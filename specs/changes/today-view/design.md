# Design - today-view (US-4.1)

Frontend-only, single lane. No backend change. Reuses existing clients.

## Data flow

```
lib/api/plants.ts     add ScheduleDue {care_type, next_due, overdue_days} + Plant.schedules
features/today/        TodayPage: load plants (fetchPlants) + locations (fetchLocations);
                       derive the attention set; group + sort; render; one-tap via careEvents
                       (small helpers extracted so TodayPage stays thin):
  buildTodayGroups(plants, locations, today) -> ordered groups of cards (PURE, unit-tested)
  TodayCard            one plant's card: name, room (implicit via group), per-care-type
                       Water/Feed buttons + a Both button when both due, badges
```

## The pure derivation (unit-tested, the only non-trivial logic)

`buildTodayGroups(plants, locations, today)`:
1. For each plant, collect its `schedules` where `next_due != null` and `next_due <= today`
   (overdue: `overdue_days > 0`; due-today: `overdue_days == 0`). Skip plants with none.
2. Card model: `{ plant, dueCareTypes: [{care_type, overdue_days, next_due}], worstOverdue }`
   where `worstOverdue = max(overdue_days)` across the plant's due schedules.
3. Group by `location_id` (null -> the "No location" group). Resolve names from locations.
4. Order groups by location name (the homeless group last); within a group, cards by
   `worstOverdue` desc then plant name.

Keeping this pure (no fetch, `today` injected) makes the grouping/sorting/overdue logic
exhaustively testable without the network or a clock.

## One-tap

`TodayCard` shows a button per care type in `dueCareTypes` (label "Water"/"Feed"); when the
set is exactly {water, feed}, also a "Both" button. Handler -> `createCareEvent(plantId,
{type, happened_on: today})` for each chosen type (Both = two calls or sequential), then the
page re-derives: on success refetch plants (simplest, correct) or locally drop the satisfied
care type and recompute the card; either way no full reload. Buttons disable while in-flight;
inline error on failure (reuse the existing toast/inline pattern).

## Layout (matches the PO-approved mock)

```
<Room name>
  [⚠] <Plant>   <care> · N days overdue   [Water] [Feed] [Both]
  [•] <Plant>   <care> · due today         [Feed]
No location
  ...
```
Overdue row: warning glyph + distinct style + "N days overdue" (not colour-only, FE-011).
Due-today row: neutral marker + "due today". Phone-first single column; touch-target sizing.
Empty state: a friendly "Nothing due - enjoy the view" panel when there are no groups.

## Test focus (-> test-foundation)

unit (buildTodayGroups): grouping incl. homeless group; most-overdue-first sort; group
order; due-today vs overdue classification; paused(null)/future excluded; a plant due on
both water+feed yields both care types (drives the Both button); empty input -> no groups.
component (TodayPage/TodayCard): renders groups + badges; Water/Feed/Both buttons present
per due set; tap logs the event(s) and the card updates without reload; empty state; error
path. acceptance (production path): real built SPA, due/overdue render grouped, one-tap
works end-to-end, zero console errors, phone + desktop screenshots.

## What this does NOT change

Any backend file, the events/plants/locations endpoints, the log modal, the plant list page.
No new dependency. The `Plant.schedules` type addition is additive (the field is already on
the wire).
