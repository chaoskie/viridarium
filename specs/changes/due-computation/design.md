# Design - due-computation (US-3.3)

Read-side only. No migrations, no write paths, no new tables.

## Layers (ARCH-002/004/006)

```
domain/due.py            pure: compute_due(schedule, last_event_on, today, window)
  WinterWindow           value object (start_md, end_md), .contains(date) with wrap
  ScheduleDue            result: care_type, next_due: date|None, overdue_days: int|None
application/due.py       DueQueryService.for_plants(plant_ids) -> {plant_id: [ScheduleDue]}
  WinterWindowProvider   Protocol; default impl returns Nov 1 - Mar 1 (US-3.5 replaces)
adapters/outbound/db     batch reads (no writes):
  care_schedule_repo.enabled_for_plants(ids) -> {plant_id: [CareSchedule]}
  care_event_repo.latest_event_dates(ids, types) -> {(plant_id, CareType): date}
adapters/inbound/web     PlantResponse += schedules: list[ScheduleDueResponse]
                         router merges DueQueryService output into responses
```

## Pure domain function

```python
def compute_due(schedule, last_event_on, today, window) -> ScheduleDue | None:
    # caller already filtered: schedule.enabled is True, plant not archived
    in_window = window.contains(today)
    if in_window and schedule.dormancy is Dormancy.PAUSED:
        return ScheduleDue(schedule.care_type, next_due=None, overdue_days=None)
    if in_window and schedule.dormancy is Dormancy.WINTER_INTERVAL \
            and schedule.winter_interval_days is not None:
        interval = schedule.winter_interval_days
    else:
        interval = schedule.interval_days           # normal cadence / winter fallback
    if last_event_on is None:
        return ScheduleDue(schedule.care_type, next_due=today, overdue_days=0)
    next_due = last_event_on + timedelta(days=interval)
    overdue = max(0, (today - next_due).days)
    return ScheduleDue(schedule.care_type, next_due, overdue)
```

`WinterWindow.contains(d)` - compare `(d.month, d.day)` against `(start)` and `(end)`:
- non-wrapping window (start <= end): `start <= md <= end`
- wrapping window (start > end, e.g. Nov 1 > Mar 1): `md >= start or md <= end`
Both endpoints inclusive. Year-agnostic (md tuple), so Feb 29 handled by the date itself.

## Batch reads (ARCH-011 dual-engine)

`latest_event_dates`: one query, standard SQL, runs on SQLite + Postgres:
```sql
SELECT plant_id, type, MAX(happened_on)
FROM care_event
WHERE plant_id IN (:ids) AND type IN ('water','feed')
GROUP BY plant_id, type
```
Only `happened_on` (a date) is needed - the created_at tiebreak from the ordering contract
is irrelevant to due math (we add an interval to the latest date). `enabled_for_plants`:
one `SELECT ... WHERE plant_id IN (:ids) AND enabled = true`.

`DueQueryService.for_plants(plant_ids)`:
1. `schedules = enabled_for_plants(plant_ids)`
2. `events = latest_event_dates(plant_ids, {WATER, FEED})`
3. for each schedule, `compute_due(schedule, events.get((pid, care_type)), today, window)`
4. group by plant_id. Archived plants are not passed in (router filters) -> empty.

Two queries total, independent of plant count -> no N+1 (AC7, NFR p95).

## Router wiring

- `list_plants`: get plants, collect non-archived ids, `DueQueryService.for_plants(ids)`,
  attach `schedules` to each `PlantResponse` (archived -> empty list).
- `get_plant`: same for the single id (archived -> empty list).
- `DueQueryService` injected via a new `get_due_query_service` dependency mirroring the
  existing `get_*_service` providers; `WinterWindowProvider` default wired in the factory.

`PlantResponse.schedules` is built by the router from the merged data, not by
`model_validate` off the domain Plant (Plant has no due) - the router composes the two.

## Edge cases -> tests (see test-foundation)

new plant (no event) due today; overdue accrual; winter-interval applied; winter fallback
when unset; paused null in-window + normal out-of-window; all four window-edge days incl.
new-year wrap; disabled omitted; archived empty; non-matching event types ignored;
list path query-count bounded (dual-engine).

## What this does NOT change

CareSchedule/CareEvent domain, their write services, their config/log endpoints, any
migration. Purely additive read model + one additive response field.
