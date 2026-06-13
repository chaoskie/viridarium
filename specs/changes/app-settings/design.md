# Design - app-settings (US-3.5)

Two lanes, disjoint files: **backend** (settings persistence + due wiring) and **frontend**
(settings page). Backend lands first - the frontend lane builds against the API contract below.

## Backend

### Layers

```
domain/app_settings.py     SeasonalSettings (frozen): seasonal_aware: bool, window: WinterWindow
                           AppSettingsRepository Protocol: get() -> SeasonalSettings | None, put(...)
domain/due.py  (edit)      compute_due gains seasonal_aware: bool param (additive)
application/settings.py    AppSettingsService: get() (lazy default), update(...)
application/due.py (edit)  SeasonalSettingsProvider replaces the hardcoded WinterWindowProvider;
                           DueQueryService reads window + flag once, passes flag to compute_due
adapters/outbound/db       AppSettingsModel (singleton id=1) + migration 0007 + repository
adapters/inbound/web       SettingsResponse / SettingsUpdate schemas; settings router GET/PUT;
                           get_app_settings_service dependency + provider wiring in the factory
```

### `compute_due` change (the only US-3.3 edit)

```python
def compute_due(schedule, last_event_on, today, window, seasonal_aware) -> ScheduleDue:
    if not seasonal_aware:
        interval = schedule.interval_days          # ignore window + paused entirely
        return _due_from(schedule.care_type, last_event_on, today, interval)
    # ... existing US-3.3 body unchanged (paused short-circuit, winter fallback, etc.)
```

Factor the no-event/overdue tail into a small `_due_from` helper so both paths share it (keeps
`compute_due` under the line ceiling and DRY). The `seasonal_aware` param is threaded from the
provider; default it to `True` only at call sites that legitimately predate settings (none here -
all callers pass it).

### Singleton repository

- `app_settings` table: `id` PK (always 1), `seasonal_aware` bool, `start_month/start_day/
  end_month/end_day` smallint, `updated_at`.
- `get()` -> the row mapped to `SeasonalSettings`, or `None` if absent.
- `AppSettingsService.get()` -> repo row or the spec default (`True`, Nov1-Mar1) when `None`.
- `put(settings)` -> upsert id=1 (insert-or-update; portable: select-then-insert/update, not
  engine-specific UPSERT, ARCH-011).

### Validation (web edge)

`SettingsUpdate` Pydantic: `start_month/end_month` 1-12; `start_day/end_day` 1-31 with a
month-aware validator rejecting impossible day/month combos (Feb<=29, Apr/Jun/Sep/Nov<=30);
`seasonal_aware` bool. 422 carries field names only, no PII.

### Migration

`0007_create_app_settings` - create table only, no seed. Down-migration drops it. Verified
apply+rollback on SQLite + PostgreSQL (the cross-engine CI leg).

## Frontend

```
lib/api/settings.ts        types + getSettings() / updateSettings()
pages/SettingsPage.tsx      load on mount, form state, save, "return to default", feedback
  (route /settings + a nav link; keep the page thin, components if it grows)
```

- Toggle = a checkbox/switch bound to `seasonal_aware`.
- Window = month + day number inputs (start, end); "Return to default" sets them to 11/1 and
  3/1 without touching the toggle; Save calls `PUT /settings`, shows inline success/error.
- No new heavy dep; reuse the existing fetch client + toast/inline pattern from other slices.

## API contract (both lanes build to this)

```
GET /api/v1/settings -> 200
  { "seasonal_aware": true,
    "winter_window": { "start_month": 11, "start_day": 1, "end_month": 3, "end_day": 1 } }
PUT /api/v1/settings  (same body) -> 200 (echoes the stored value); 422 on invalid month/day
```

## Test focus (-> test-foundation)

backend: lazy-default get; put+get round-trip + restart persistence (both engines); migration
up/down both engines; compute_due seasonal_aware=False ignores window+paused (matrix vs the
US-3.3 on-path); window validation sad paths; DueQueryService still bounded (no per-plant
settings read). frontend: load/edit/save, return-to-default resets only the window, error path.
acceptance (Playwright, production path): open /settings, toggle off, set a window, save, reload
-> values persisted, zero console errors, both breakpoints.

## What this does NOT change

The `schedules` response shape, CareSchedule/CareEvent, the plant endpoints. The only US-3.3
code edit is the additive `seasonal_aware` parameter + provider swap.
