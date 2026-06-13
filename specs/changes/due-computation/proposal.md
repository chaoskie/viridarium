# Proposal - due-computation (US-3.3)

Status: in progress. Story US-3.3 "Due computation" - THE core read rule. Spec:
product-spec §3 (Due computation) + §4 US-3.3. Consumes the CareEvent history from
US-3.2 and the CareSchedule config from US-3.1; feeds US-4.1 (Today view), US-4.3
(detail), and US-5.2 (`/due` endpoint - NOT this story).

## Story (SPEC-004)

As a plant owner, I want every plant read to tell me when each care type is next due
(and how overdue it is), so that the app can show me what needs water or feed today
without my tracking it by hand.

## The rule (spec §3, verbatim contract)

`next_due = date(last matching CareEvent) + effective_interval`

- **last matching CareEvent** = the most recent event whose `type` equals the schedule's
  `care_type` (a `water` schedule consumes `water` events; `feed` consumes `feed`;
  `repot`/`observe` never match a schedule). "Most recent" = max `happened_on`.
- **no matching event** -> due immediately (surfaces new plants): `next_due = today`,
  `overdue_days = 0`.
- **overdue_days** = `(today - next_due).days` when positive, else `0`.
- **effective_interval**:
  - in winter window AND `dormancy = winter_interval` AND `winter_interval_days` set
    -> `winter_interval_days`
  - in winter window AND `dormancy = winter_interval` AND `winter_interval_days` unset
    -> falls back to `interval_days` (confirmed at pickup: no seasonal slowdown
    configured = stay on the normal cadence; matches the US-3.1 model docstring)
  - in winter window AND `dormancy = paused` -> **never due**: `next_due = null`,
    `overdue_days = null`
  - otherwise -> `interval_days`
- **disabled schedules** (`enabled = false`) excluded entirely (not in the due output).
- **archived plants** excluded entirely (D-009 forward-link; reuse the archived flag):
  no due output for an archived plant.

### Winter window

Read from an injected settings source. Until US-3.5 lands, the source returns the spec
default **Nov 1 - Mar 1** (northern hemisphere). The window is month/day, year-agnostic,
and **wraps the new year** (Nov 1 >= start OR <= Mar 1 means "in window"). Both endpoints
inclusive. US-3.5 will replace the default provider with persisted settings (and, per the
PO direction on #14, an eventual global seasonal on/off toggle) - that drops in additively
because this story already reads the window through a port, never a constant.

### "today"

Server local date (`date.today()`), injected as a parameter into the pure domain function
for testability. No per-user timezone in v1 (single-instance, trusted-network; SEC-003).

## Architecture (ARCH-006: dedicated query module)

A read joining 2+ contexts (plant + schedule + event + settings) MUST live in a dedicated
query module with no writes. Split:

- **`domain/due.py`** - framework-free pure logic: `compute_due(schedule, last_event_on,
  today, window) -> ScheduleDue`. Exhaustively unit-tested. No I/O.
- **`application/due.py`** - `DueQueryService`: orchestrates, **batch-loads** to avoid
  N+1 (see below), assembles per-plant due lists. No writes.
- **`adapters/outbound/db/care_event_repository`** - add a batch read
  `latest_event_dates(plant_ids, types) -> {(plant_id, care_type): date}` via a single
  grouped `MAX(happened_on)` query (dual-engine portable, ARCH-011).
- **schedule repo** - add a batch read of enabled schedules for a set of plant ids.

### N+1 / performance (NFR: p95 < 200 ms for 500 plants)

Computing due per plant on the **list** endpoint must not issue per-plant queries. The
query service loads all enabled schedules and all latest-event dates for the page's plant
ids in **two grouped queries**, then computes in memory. Recorded as an explicit design
constraint so the list path stays flat.

## API / contract (API-001, additive only -> non-breaking)

`PlantResponse` gains one additive field:

```
schedules: [ { care_type, next_due, overdue_days } ]
```

- `care_type`: `water | feed`
- `next_due`: date (ISO) or `null` (null = dormant this window / paused)
- `overdue_days`: int >= 0, or `null` when `next_due` is null

Present on **both** `GET /plants` (list) and `GET /plants/{id}` (detail), per the spec
("exposed on every plant read"). Entry per **enabled** schedule of a **non-archived**
plant; archived plant or disabled schedule -> the entry is absent. Additive field, no
status-code or path change -> not a breaking change (API-004 not triggered). The standalone
`/plants/{id}/schedules` config endpoint is unchanged (config, not due).

## Out of scope (SPEC-001)

The `/api/v1/due` endpoint (US-5.2), the Today view and any UI rendering of due
(US-4.1/US-4.3), snooze/skip (US-3.6), bulk watering (US-3.7), US-3.5 winter-window
settings UI/persistence and the global seasonal toggle (#14), the seasonal indicator UI
(#61). No change to CareSchedule/CareEvent write paths or their config endpoints.

## Acceptance criteria (each input -> observable outcome)

- **AC1**: a plant with a water schedule (interval 7) and a water event on day D ->
  `next_due = D+7`; on day `D+9` `overdue_days = 2`.
- **AC2**: a plant with an enabled schedule and **no** matching event -> `next_due = today`,
  `overdue_days = 0` (surfaces immediately).
- **AC3**: inside the winter window, `dormancy = winter_interval` with a winter interval
  set -> due uses the winter interval; with winter interval unset -> due uses the normal
  interval.
- **AC4**: inside the winter window, `dormancy = paused` -> `next_due = null`,
  `overdue_days = null`; the same schedule **outside** the window computes normally.
- **AC5**: window edges - the day before start / start / end / day after end classified
  correctly, including the new-year wrap (a Jan date is in-window for a Nov 1 - Mar 1
  window).
- **AC6**: a disabled schedule produces no entry; an archived plant produces no `schedules`
  entries at all.
- **AC7**: `GET /plants` and `GET /plants/{id}` both include the `schedules` due field;
  the list path issues a bounded number of queries regardless of plant count (no N+1).
- **AC8**: only matching event types count - a `feed`/`repot`/`observe` event never moves
  a `water` schedule's `next_due`.

## Open questions

none. (Both flagged product decisions resolve to the US-3.1-confirmed model; recorded
above. Exposure shape, "today" semantics, and null representation are recorded design
decisions, not open scope.)
