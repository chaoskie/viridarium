---
title: Test Foundation - due-computation (US-3.3)
type: test-foundation
change: due-computation
status: authored
date: 2026-06-13
---

# Test Foundation - due-computation (US-3.3)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for the
**core read rule**: `next_due = date(last matching CareEvent) + effective_interval`. This
story consumes the `CareEvent` history (US-3.2) and `CareSchedule` config (US-3.1) and
feeds US-4.1 / US-4.3 / US-5.2 downstream. A wrong branch here silently corrupts **every**
dashboard read, so the branch logic is the critical-100% target. Authored by
`test-engineer` against `proposal.md` (the verbatim rule + AC1-AC8) and `design.md` (the
pure `compute_due`, the two batch reads, the `DueQueryService`, the additive
`PlantResponse.schedules` field). Mirrors the structure of
`care-events/test-foundation.md`.

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mocking boundary). It contains **no test code**.

**Scope note - backend-only, no frontend lane.** The proposal/design define only a read
model + one additive response field; the UI that *renders* due (Today view US-4.1, detail
US-4.3) is explicitly out of scope (proposal §Out of scope). There is therefore **no
frontend test lane** in this foundation - unlike care-events, which had a `LogCareModal`
lane. The single build lane records its TEST-014 red in `worklog.md` before turning green.

Cases are numbered so the lane can cite them and the re-audit can diff:
`B-Un` (backend unit - the pure domain function + window), `B-In` (backend integration -
repositories, query service, web API). The re-audit checks every numbered case is present,
meaningful (TEST-004), and on its assigned layer, and maps every AC1-AC8 (§9).

**Critical paths for this story** (flagged 100% in §8) - the four places a wrong branch
silently corrupts a dashboard, where mutation probes (story-complete) carry more weight than
assertion-reading:
1. The **effective-interval branch table** (AC3) - winter-interval vs winter-fallback vs
   normal interval. A swapped branch silently waters on the wrong cadence all winter.
2. The **paused null-path** (AC4) - in-window paused returns `next_due=None`/`overdue=None`;
   the *same* schedule out-of-window computes normally. A leaked non-null here invents a due
   date for a dormant plant.
3. The **window-wrap classification** (AC5) - `WinterWindow.contains` for the wrapping
   default (Nov 1 - Mar 1) and the four edge days. A broken wrap mis-seasons half the year.
4. The **matching-type filter** (AC8) - a `feed`/`repot`/`observe` event must not move a
   `water` schedule's `next_due` (and vice versa). A leaky filter resets the clock off the
   wrong event.

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test. The pure domain function is
the behaviour core; two new repository batch reads, one query-service method, and the two
augmented plant-read endpoints are the integration surfaces.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| D1 | `compute_due(schedule, last_event_on, today, window)` | pure domain fn | event present -> `last + interval`; no event -> today | paused in-window -> `(None, None)`; overdue accrual when past-due |
| D2 | `WinterWindow.contains(date)` | value-object method | a date inside the window -> True | a date outside -> False; the four edge days both window kinds |
| R1 | `care_event_repository.latest_event_dates(plant_ids, types)` | repo batch read | MAX(happened_on) per `(plant_id, type)` | empty `plant_ids` -> `{}`; non-water/feed type ignored; no events -> key absent |
| R2 | `care_schedule_repository.enabled_for_plants(plant_ids)` | repo batch read | enabled schedules grouped per plant | disabled excluded; empty `plant_ids` -> `{}`; unknown id -> key absent |
| Q1 | `DueQueryService.for_plants(plant_ids)` | query service | per-plant `[ScheduleDue]` assembled | id with no schedules -> empty list; empty input -> `{}`; bounded query count (no N+1) |
| E1 | `GET /plants` (list) | endpoint | 200, each plant carries `schedules` | archived plant -> `schedules == []`; disabled schedule absent |
| E2 | `GET /plants/{id}` (detail) | endpoint | 200, `schedules` present | archived plant -> `schedules == []`; 404 unknown plant (existing behaviour unchanged) |

The exact method/identifier names (`for_plants`, `latest_event_dates`, `enabled_for_plants`,
`ScheduleDue`, `ScheduleDueResponse`) are pinned by `design.md`; the re-audit checks the
**behaviour and the response contract** (§7), accepting the lane's final spelling where the
design left a choice.

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Unit is exceptionally the primary layer for `compute_due` + `WinterWindow`**
  (TEST-001 (a): genuinely complex pure logic with a wide branch table). These are
  framework-free, I/O-free, and have a >6-cell branch matrix (§3 M1, §4 M2) that integration
  cannot economically enumerate. `pytestmark = pytest.mark.unit`. This is the one place
  exhaustive unit testing is correct - the branch table IS the user-meaningful behaviour, and
  it survives any reimplementation of the surrounding wiring (TEST-004).
- **Integration is primary for everything with I/O** (TEST-001): the two batch reads against
  a **real DB** (the grouped `MAX` + the enabled filter), the `DueQueryService` assembly, and
  the two augmented endpoints through the real composition root
  (router -> `DueQueryService` -> repositories -> SQLAlchemy -> SQLite). The query-count /
  N+1 bound (AC7) is only meaningful end-to-end and is asserted there.
- **`DueQueryService` unit tests against fake ports** (TEST-001 (b)): the assembly logic
  (group-by-plant, `events.get((pid, care_type))` lookup, empty-list for a schedule-less
  plant, today + window injection) is unit-testable against a fake schedule repo + fake event
  repo, cheaply pinning the orchestration without a DB. The same behaviour is re-proven
  end-to-end in integration. (Optional but recommended: integration alone clears coverage; the
  unit slice de-risks the assembly branch points.)
- **Dual-engine** (`test_fk_cross_engine.py` or a dedicated cross-engine test, ARCH-011): the
  grouped `MAX(happened_on) ... GROUP BY plant_id, type` and the `enabled = true` filter run
  identically on the engine resolved from `DATABASE_URL` (SQLite locally, PostgreSQL on the CI
  postgres leg). `GROUP BY` + `MAX` + `IN (:ids)` is standard SQL; the dual-engine test proves
  it portable rather than trusting it (§5).
- **No migration** - this story adds **no tables, no columns, no migration** (design: "Read-side
  only"). No `test_migrations.py` edit. If the lane finds itself writing a migration, that is a
  scope deviation to halt and flag (PRIN-IV / SPEC-001).
- **No frontend lane** (§ scope note). The `schedules` field is consumed by later UI stories.
- **Acceptance (Playwright, TEST-009): DEFERRED**, consistent with the care-events / care-
  schedules precedent (no due-rendering UI in scope). The intended journey is recorded in §6,
  **not built**.

---

## 3. Backend unit: `test_due.py` - `compute_due` (`unit`)

`pytestmark = pytest.mark.unit`. The pure function against hand-built `CareSchedule` value
objects and a `WinterWindow`. No app, no DB, no I/O. `today` and `window` are injected
(proposal §"today"), so every case is deterministic with no clock dependence (TEST-006).

Fixtures: a `_schedule(care_type=WATER, interval=7, winter=None, dormancy=WINTER_INTERVAL,
enabled=True)` builder; a `_in_window_day` and `_out_of_window_day` derived from a fixed test
window; a non-wrapping window and the wrapping default for the matrix.

### 3a. Core rule - next_due + overdue (AC1, AC2)

| # | test | setup | expectation |
|---|---|---|---|
| B-U1 | no matching event -> due today | `last_event_on = None`, out-of-window | `next_due == today`, `overdue_days == 0` (AC2, surfaces new plants) |
| B-U2 | event present -> last + interval | water interval 7, `last_event_on = D`, `today = D` | `next_due == D + 7`, `overdue_days == 0` (not yet due) |
| B-U3 | overdue accrual (positive) | interval 7, `last = D`, `today = D + 9` | `next_due == D + 7`, `overdue_days == 2` (AC1: today-next_due, positive) |
| B-U4 | overdue clamped to 0 when next_due future | interval 7, `last = D`, `today = D + 3` | `next_due == D + 7`, `overdue_days == 0` (max(0, negative) = 0) |
| B-U5 | overdue 0 exactly on the due day | interval 7, `last = D`, `today = D + 7` | `next_due == D + 7`, `overdue_days == 0` (boundary: due today is not overdue) |
| B-U6 | overdue 1 the day after due | interval 7, `last = D`, `today = D + 8` | `overdue_days == 1` (boundary above the due day) |

`B-U5`/`B-U6` pin the off-by-one boundary of the `max(0, (today - next_due).days)` rule.

### 3b. Effective-interval branch matrix M1 (AC3, CRITICAL) - TEST-007

The effective interval crosses **3 dimensions** (`in_window` x `dormancy` x
`winter_interval_days` set/None) -> explicit parametrized matrix. **Branch-priority order**
(matches the design pseudocode top-to-bottom): (1) in-window + `paused` short-circuits to the
null-path (covered in §3c, listed here for completeness of the table); (2) in-window +
`winter_interval` + `winter_interval_days` set -> winter interval; (3) every other case ->
`interval_days` (normal cadence / winter fallback). To isolate the *interval* selection from
the overdue arithmetic, fix `last_event_on = D` and `today = D` so the only observable that
moves is `next_due == D + effective_interval`.

Dimensions: **{in_window: yes, no} x {dormancy: winter_interval, paused} x
{winter_interval_days: set(=14), None}**. 2x2x2 = 8 cells; the paused cells defer their full
assertion to §3c but appear here so the table is exhaustive.

| id | in_window | dormancy | winter_days | effective interval | next_due | proves |
|---|---|---|---|---|---|---|
| `in-wi-set` | yes | winter_interval | 14 | **14** (winter) | `D+14` | winter interval applied (named CRITICAL) |
| `in-wi-none` | yes | winter_interval | None | **7** (fallback) | `D+7` | winter fallback to interval_days (named CRITICAL) |
| `out-wi-set` | no | winter_interval | 14 | **7** (normal) | `D+7` | out-of-window ignores winter even when set |
| `out-wi-none` | no | winter_interval | None | **7** (normal) | `D+7` | out-of-window normal |
| `in-paused-set` | yes | paused | 14 | n/a (null-path) | None | paused short-circuits before interval selection (§3c B-U10) |
| `in-paused-none` | yes | paused | None | n/a (null-path) | None | paused short-circuits regardless of winter_days (§3c) |
| `out-paused-set` | no | paused | 14 | **7** (normal) | `D+7` | out-of-window paused computes normally (§3c B-U12) |
| `out-paused-none` | no | paused | None | **7** (normal) | `D+7` | out-of-window paused normal (§3c) |

Cases: `B-U7` (parametrized over the four non-paused rows, asserting `next_due == D + expected`
and `overdue_days == 0`). The four paused rows are asserted by `B-U10`-`B-U12` in §3c (so the
null vs normal distinction is named, not buried in a matrix cell). The headline pair is
`in-wi-set` (14) vs `in-wi-none` (7): the fallback row is the one a naive implementation gets
wrong by defaulting winter to 0 or to a hardcoded value.

### 3c. Paused null-path (AC4, CRITICAL)

| # | test | setup | expectation |
|---|---|---|---|
| B-U10 | paused in-window -> null due | `dormancy = paused`, in-window, `last = D` | `next_due is None` **and** `overdue_days is None` (never-due; the both-null invariant, §7) |
| B-U11 | paused in-window ignores winter_days | `dormancy = paused`, `winter_days = 14`, in-window | still `(None, None)` - paused wins over winter_interval selection (branch order) |
| B-U12 | **SAME paused schedule out-of-window computes normally** | `dormancy = paused`, out-of-window, `last = D`, `today = D + 9`, interval 7 | `next_due == D + 7`, `overdue_days == 2` - paused only suppresses *inside* the window |

`B-U10`-`B-U12` are the paused critical proof: the null-path fires only in-window, and the
both-null invariant holds. `B-U12` reuses an otherwise-identical schedule to prove the gate is
`in_window`, not `dormancy` alone.

### 3d. Matching-type filter at the domain seam (AC8, CRITICAL)

`compute_due` receives `last_event_on` already filtered to the schedule's `care_type` by the
query service (the type filter physically lives in `latest_event_dates`, proven in §4). At the
domain level the contract is: the function uses `schedule.care_type` for the result's
`care_type` and treats `last_event_on=None` as "no matching event". The end-to-end proof that a
*wrong-type* event does not leak is `B-I7`/`B-I8` (§4). Domain-level:

| # | test | setup | expectation |
|---|---|---|---|
| B-U13 | result carries the schedule's care_type | water schedule | `ScheduleDue.care_type == WATER`; feed schedule -> `FEED` (the result is keyed by the schedule, not the event) |

### 3e. WinterWindow.contains edge matrix M2 (AC5, CRITICAL) - TEST-007

Two window kinds x four edge days = a >6-cell boundary matrix -> explicit parametrized table.
The window is **year-agnostic** (month/day tuples), so every case asserts with a date whose
year is irrelevant, and the wrapping case MUST include a **January** date proven in-window for
the Nov 1 - Mar 1 default. **Branch-priority:** non-wrapping (`start <= end`) uses
`start <= md <= end`; wrapping (`start > end`) uses `md >= start or md <= end`. Both endpoints
inclusive.

Window A (non-wrapping): **start = Apr 1, end = Sep 1**.
Window B (wrapping default): **start = Nov 1, end = Mar 1**.

| id | window | test date | expected | proves |
|---|---|---|---|---|
| `A-before-start` | Apr 1 - Sep 1 | Mar 31 | False | day before start excluded |
| `A-start` | Apr 1 - Sep 1 | Apr 1 | **True** | start inclusive |
| `A-mid` | Apr 1 - Sep 1 | Jun 15 | True | interior |
| `A-end` | Apr 1 - Sep 1 | Sep 1 | **True** | end inclusive |
| `A-after-end` | Apr 1 - Sep 1 | Sep 2 | False | day after end excluded |
| `B-before-start` | Nov 1 - Mar 1 | Oct 31 | False | day before start (wrap) excluded |
| `B-start` | Nov 1 - Mar 1 | Nov 1 | **True** | wrap start inclusive |
| `B-january` | Nov 1 - Mar 1 | Jan 15 | **True** | **new-year wrap: a Jan date is in-window** (named CRITICAL, AC5) |
| `B-feb-late` | Nov 1 - Mar 1 | Feb 27 | True | deep into the wrapped tail |
| `B-end` | Nov 1 - Mar 1 | Mar 1 | **True** | wrap end inclusive |
| `B-after-end` | Nov 1 - Mar 1 | Mar 2 | False | day after wrap end excluded |
| `B-summer` | Nov 1 - Mar 1 | Jul 1 | False | clearly-out interior of the gap |
| `B-year-agnostic` | Nov 1 - Mar 1 | Jan 15 of a **different year** | True | result independent of the year component |

Case: `B-U14` (parametrized `test_winter_window_contains` over all rows). `B-january` +
`B-end` + `B-after-end` are the wrap critical cells; `A-start`/`A-end` pin the inclusive
endpoints on the simple kind so the wrap logic can't accidentally pass by being permissive.

---

## 4. Backend integration: `test_due_endpoint.py` + repository tests (`integration`)

`pytestmark = pytest.mark.integration`. Real DB, nothing internal mocked (TEST-003). Each test
seeds its own plant(s), schedule(s), and event(s) via the real services/endpoints for TEST-006
independence; cleanup scoped to created rows, never global truncation. Helpers mirror the
existing suites: `_make_plant(client, name="Fern") -> int`, `_put_schedule(client, plant_id,
care_type, interval, ...)`, `_log_event(client, plant_id, type, happened_on) -> int`.

### 4a. Repository batch reads - `latest_event_dates` (R1, AC8)

Against `SqlAlchemyCareEventRepository` through the real session (no endpoint needed for the
repo-level cases; the type filter is structural).

| # | test | setup | asserts |
|---|---|---|---|
| B-I1 | groups MAX(happened_on) per (plant, type) | plant with water events on D1 and D2 (D2 later) and a feed event on D3 | returns `{(pid, WATER): D2, (pid, FEED): D3}` - the MAX per type, not the latest overall |
| B-I2 | only the latest counts within a type | three water events D1<D2<D3 (inserted out of date order) | `{(pid, WATER): D3}` - MAX, independent of insertion order |
| B-I3 | ignores non-water/feed event types | a single `repot` and a single `observe` event, no water/feed | the result has **no key** for that plant (repot/observe never appear; AC8 at the source) |
| B-I4 | batches multiple plant ids | two plants each with water events | one query returns both plants' keys; both present |
| B-I5 | empty plant_ids is safe | `latest_event_dates([], {WATER, FEED})` | returns `{}`; issues no query or one trivially-empty query (no crash) |
| B-I6 | plant with no events -> key absent | a plant id with zero events | no key for that plant (the `.get` in the service yields None -> due-today) |

### 4b. Matching-type filter end-to-end (AC8, CRITICAL)

The headline proof that a wrong-type event does not move a schedule's clock, driven through
the endpoint so it exercises the full filter + assembly.

| # | test | setup | asserts |
|---|---|---|---|
| B-I7 | **feed/repot/observe event does NOT move a water schedule** | plant with a water schedule (interval 7) and **only** a `feed` event (and a `repot`, an `observe`) on a recent date, no water event | the water schedule's `next_due == today`, `overdue_days == 0` (treated as no matching event - AC2/AC8), proving the non-water events were ignored |
| B-I8 | **water event does NOT move a feed schedule** | plant with a feed schedule (interval 14) and only a `water` event on date D | the feed schedule's `next_due == today` (no matching feed event); the water event is irrelevant to feed |

`B-I7`/`B-I8` are the matching-type critical proof end-to-end (the domain seam is `B-U13`; the
SQL filter is `B-I3`; this proves the whole path doesn't cross-contaminate).

### 4c. Repository batch reads - `enabled_for_plants` (R2, AC6)

| # | test | setup | asserts |
|---|---|---|---|
| B-I9 | returns enabled schedules grouped per plant | plant with an enabled water + enabled feed schedule | `{pid: [water, feed]}` (both present) |
| B-I10 | **excludes disabled schedules** | plant with an enabled water schedule and a **disabled** feed schedule | result for that plant contains water only; the disabled feed is absent (AC6) |
| B-I11 | batches multiple plant ids | two plants each with schedules | both plants' keys present from one query |
| B-I12 | empty plant_ids safe | `enabled_for_plants([])` | `{}`; no crash |
| B-I13 | unknown / schedule-less plant -> key absent | a plant id with no schedules | no key (the service yields an empty due list, B-I16) |

### 4d. DueQueryService assembly (Q1, AC6, AC7)

Through the real service against the real DB (unit-against-fakes variant optional per §2).

| # | test | setup | asserts |
|---|---|---|---|
| B-I14 | assembles per-plant due lists | plant with water (interval 7, water event D) + feed (interval 14, feed event E) | `for_plants([pid])` returns `{pid: [ScheduleDue(water, D+7, ...), ScheduleDue(feed, E+14, ...)]}` (both schedules, each with its own last-event) |
| B-I15 | new plant (no events) -> all due today | plant with an enabled water schedule, zero events | `{pid: [ScheduleDue(water, today, 0)]}` (AC2 through the assembly) |
| B-I16 | schedule-less plant -> empty list | plant with no schedules | `{pid: []}` (present key, empty list - NOT missing) |
| B-I17 | disabled schedule omitted from output | plant with enabled water + disabled feed | the returned list has the water entry only (AC6 through the assembly) |
| B-I18 | empty input -> empty mapping | `for_plants([])` | `{}` |
| B-I19 | **bounded query count - no N+1** (AC7, NFR) | seed **N plants** (e.g. 10), each with a water + feed schedule and events | `for_plants` issues a **bounded, plant-count-independent** number of queries (the design's two grouped reads). Asserted by counting executed statements via a SQLAlchemy event listener (`before_cursor_execute`) over the call: the count MUST NOT scale with N (assert `<=` a small constant, e.g. `<= 3`, and that the same count holds for N and 2N). This is the verifiable N+1 guard, not an eyeball. |

`B-I19` is the AC7 proof. Approach pinned: attach a counter to the engine/connection for the
duration of the `for_plants` call, run it for N and 2N plants, assert the statement count is
constant and small. If the lane's DI makes a listener awkward, an equivalent
`sqlalchemy` `Engine`-level `event.listen` on a throwaway counting connection is acceptable -
the re-audit checks the count is asserted **constant across plant counts**, however captured.

### 4e. Web API - `GET /plants/{id}` detail (E2, AC4, AC6, AC7)

| # | test | setup | asserts |
|---|---|---|---|
| B-I20 | detail includes schedules (happy) | plant with a water schedule (interval 7) + a water event on D | `GET /plants/{id}` 200; body has `schedules` array; the water entry has `care_type == "water"`, `next_due == (D+7).isoformat()`, `overdue_days` an int `>= 0` |
| B-I21 | new plant detail -> due today | plant with a water schedule, no events | `schedules[0].next_due == today.isoformat()`, `overdue_days == 0` (AC2) |
| B-I22 | disabled schedule -> no entry | plant with enabled water + disabled feed | `schedules` has the water entry only; no feed entry (AC6) |
| B-I23 | **paused in-window serializes as JSON null** | a paused schedule with `today` forced inside the window (window provider injected/overridden in the test app) | the entry's `next_due` is JSON `null` **and** `overdue_days` is JSON `null` (not absent, not 0) - the both-null contract over the wire (AC4, §7) |
| B-I24 | archived plant detail -> empty schedules | an archived plant (with schedules configured) | `GET /plants/{id}` 200; `schedules == []` (archived excluded entirely, AC6); the archived plant's schedules are NOT computed |
| B-I25 | unknown plant detail -> 404 unchanged | `GET /plants/999999` | 404 (existing behaviour; the additive field did not change the not-found path); `{"detail"}`-only, no PII |

### 4f. Web API - `GET /plants` list (E1, AC6, AC7)

| # | test | setup | asserts |
|---|---|---|---|
| B-I26 | list includes schedules per plant (happy) | two active plants, each with a water schedule + event | 200; each plant in the list carries its own `schedules` array with the correct `next_due` per that plant's last event (no cross-plant bleed) |
| B-I27 | list excludes archived plant schedules | one active + one archived plant (use `include_archived=true`) | the active plant has populated `schedules`; the archived plant has `schedules == []` (AC6) |
| B-I28 | list disabled schedule omitted | a plant with enabled water + disabled feed | that plant's `schedules` has water only (AC6 on the list path) |
| B-I29 | empty plant list -> no crash | no active plants | 200, `[]`; the due assembly handles the empty page (AC7 degenerate) |
| B-I30 | **list query count bounded regardless of plant count** (AC7, CRITICAL for NFR) | seed N then 2N active plants with schedules + events | the statement count for `GET /plants` does **not** scale with the plant count (constant delta between N and 2N within the due-assembly portion) - the list path stays flat (no per-plant due query). Captured via the same listener approach as `B-I19`. |

`B-I30` is the list-path N+1 guard end-to-end (the NFR p95 < 200 ms for 500 plants depends on
it). It complements `B-I19` (service-level) by proving the *router* wiring also batches.

### 4g. Response contract assertion (§7, additive-field shape) - TEST-008 cross-check

| # | test | asserts |
|---|---|---|
| B-I31 | OpenAPI exposes the additive schedules field | the emitted `/api/v1/openapi.json` `components.schemas.PlantResponse.properties` contains `schedules`, an array of an object with exactly `{care_type, next_due, overdue_days}`; `next_due` is `string($date)`-or-null, `overdue_days` is `integer`-or-null. No path/status change vs the prior schema (additive only, API-001/API-004 not triggered) |
| B-I32 | schedules entry key-set is exact | any populated `schedules` entry from B-I20 | the entry's JSON keys are **exactly** `{"care_type", "next_due", "overdue_days"}` - no extra leakage (no schedule id, no interval, no dormancy - those are config, not due; ARCH-007 surrogate-id discipline) |

`B-I31`/`B-I32` pin the response contract (§7) structurally so a future field addition can't
silently widen the dashboard payload.

---

## 5. Dual-engine: cross-engine test (`integration`, ARCH-011)

Add to `test_fk_cross_engine.py` (or a small dedicated cross-engine test) one test resolving
the engine from `DATABASE_URL` via the existing `fk_engine` fixture (SQLite locally,
PostgreSQL on the CI postgres leg). The grouped `MAX ... GROUP BY plant_id, type` + the
`enabled = true` filter are standard SQL but MUST be proven portable, not trusted.

| # | test | asserts |
|---|---|---|
| B-I33 | `latest_event_dates` grouped-MAX runs identically on the real engine | build a plant; add water events on D1, D2 and a feed event on D3 via the repository on the **real engine**; call `latest_event_dates([pid], {WATER, FEED})` -> `{(pid, WATER): D2, (pid, FEED): D3}` on **both** engines (CI postgres leg proves PostgreSQL; locally SQLite). Self-cleans its own rows. |

Optionally fold the `enabled_for_plants` filter into the same cross-engine test (one extra
assert) since it shares the `IN (:ids)` + boolean-filter shape that differs most between
engines (SQLite has no native boolean). The re-audit checks the **grouped MAX** ran on both
engines at minimum (it is the one nontrivial-portability query in the story).

---

## 6. Playwright (TEST-009) - DEFERRED, journey recorded only

No due-rendering UI is in scope (proposal §Out of scope: Today view US-4.1, detail US-4.3).
The acceptance test is **not built here**; it lands with the UI story that renders due. The
intended future journey, recorded for verbatim implementation:

1. With a plant that has a water schedule and a logged water event, open the plant detail ->
   the due indicator shows the computed next-due date / overdue count.
2. A brand-new plant (no events) shows "due today".
3. A paused plant in winter shows no due date (dormant), not an overdue badge.
4. **Console-error fail-on (TEST-010):** the journey fails on any page error or error-level
   console output; warnings ignored.

Driver MUST use real UI affordances - never inject values directly.

---

## 7. Response contract (pinned)

`ScheduleDueResponse` (the `schedules[]` entry on `PlantResponse`) has **exactly** these
fields, no more:

| field | type | rule |
|---|---|---|
| `care_type` | `"water" \| "feed"` | the schedule's care type (closed enum) |
| `next_due` | `date (ISO string) \| null` | `null` only when paused-in-window (dormant this window) |
| `overdue_days` | `int (>= 0) \| null` | `null` **iff** `next_due` is null; otherwise `>= 0`, never negative |

**Both-null invariant:** `next_due is null  <=>  overdue_days is null`. There is no state where
one is null and the other is not. A non-null `next_due` always pairs with `overdue_days >= 0`
(clamped, never negative). Asserted at the domain seam (`B-U10`), the service (`B-I14`-`B-I17`),
and over the wire (`B-I23` null path, `B-I32` key-set, `B-I31` OpenAPI types). The entry never
exposes the schedule id, interval, winter interval, dormancy, or enabled flag - those are
config, surfaced by the separate `/plants/{id}/schedules` endpoint (ARCH-007: surrogate config
does not cross the due boundary).

---

## 8. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; repo currently ~99% backend - this story **MUST NOT** drop that
  floor. New/changed code **≥80% diff-cover**.
- **Branch coverage:** **≥95% in domain + application** - `compute_due` and
  `WinterWindow.contains` are nearly pure branch logic and should land at or near 100%; the
  `DueQueryService` assembly branches (empty input, schedule-less plant, the `events.get`
  None-vs-present fork) all exercised. **≥80% in adapters/outbound** (the grouped-MAX read,
  the enabled filter, the router merge incl. the archived-empty branch).
- **Critical paths flagged 100%** (spec-flagged -> QG-002 100% required). These four are where
  a wrong branch silently corrupts every dashboard; **mutation evidence outranks
  assertion-reading** at story-complete:
  1. **Effective-interval branch table** (AC3) - matrix M1 (`B-U7`) incl. the winter-set vs
     winter-fallback pair + the out-of-window-ignores-winter rows; mutate the branch (swap
     winter/normal, drop the `is not None` guard) -> a targeted M1 case must go red.
  2. **Paused null-path** (AC4) - `B-U10`-`B-U12` + `B-I23`; mutate the in-window paused guard
     to fall through -> `B-U10`/`B-I23` must go red; mutate the gate to `dormancy`-only ->
     `B-U12` must go red.
  3. **Window-wrap classification** (AC5) - matrix M2 (`B-U14`) the four edge days both window
     kinds + the January wrap; mutate `>= start or <= end` to `and` (or to a non-wrapping
     comparison) -> `B-january`/`B-end` must go red.
  4. **Matching-type filter** (AC8) - `B-I7`/`B-I8` end-to-end + `B-I3` at the SQL + `B-U13` at
     the seam; mutate the `type IN ('water','feed')` / the per-type grouping so a feed event
     leaks into water -> `B-I7` must go red.
- The re-audit (§10) runs sanctioned mutation probes on these four and logs each (file,
  mutation, test that failed), restoring byte-identically and verifying `git status` clean.
- Combined pytest run (unit + integration) scores the union (TEST-001); the unit branch matrix
  + the integration assembly/endpoint slice clear the floor without brittle
  implementation-mirroring tests (TEST-004).

---

## 9. AC traceability (TEST-015) - every AC -> ≥1 named case

| AC | scenario | covering cases |
|---|---|---|
| **AC1** | water interval 7 + event D -> next_due D+7; at D+9 overdue 2 | `B-U2`, `B-U3` (domain); `B-I20` (endpoint) |
| **AC2** | enabled schedule, no matching event -> next_due today, overdue 0 | `B-U1` (domain); `B-I15` (service); `B-I21` (endpoint); `B-I7`/`B-I8` (no-matching via wrong type) |
| **AC3** | in-window winter_interval: set -> winter interval; unset -> normal interval | matrix M1 `B-U7` rows `in-wi-set` / `in-wi-none` (+ out-of-window rows) |
| **AC4** | in-window paused -> null/null; same schedule out-of-window computes normally | `B-U10`, `B-U11`, `B-U12` (domain); `B-I23` (JSON null over the wire) |
| **AC5** | window edges incl. new-year wrap (Jan in-window for Nov 1 - Mar 1), year-agnostic | matrix M2 `B-U14` (all 13 rows; `B-january`, `B-start`, `B-end`, `B-after-end`, `B-year-agnostic`) |
| **AC6** | disabled schedule -> no entry; archived plant -> no schedules entries | `B-I10`/`B-I17`/`B-I22`/`B-I28` (disabled); `B-I24`/`B-I27` (archived empty) |
| **AC7** | both `GET /plants` and `/plants/{id}` include schedules; list path bounded queries (no N+1) | `B-I20`/`B-I26` (both endpoints carry it); `B-I19` (service bounded); `B-I30` (list-path bounded across N/2N) |
| **AC8** | only matching event types count - feed/repot/observe never moves a water schedule (and vice versa) | `B-U13` (seam); `B-I3` (SQL ignores repot/observe); `B-I7`/`B-I8` (end-to-end) |

No AC is uncovered. Every numbered case maps to at least one AC or pins the response contract
(§7: `B-I31`/`B-I32`), the dual-engine portability (§5: `B-I33`), or a boundary the ACs imply
(`B-U4`-`B-U6` overdue boundaries, `B-I5`/`B-I12`/`B-I18`/`B-I29` empty-input safety).

---

## 10. Mocking boundary (TEST-003) - explicit

- **Unit (`test_due.py`, + optional `test_due_query_service.py`):** the pure `compute_due` /
  `WinterWindow` take plain value objects; the optional service unit uses **fake** schedule +
  event repos and a fake `WinterWindowProvider` (faking ports allowed). No app, no DB, no I/O,
  no real clock (`today` injected).
- **Integration (`test_due_endpoint.py`, repo tests):** real DB through the real composition
  root; nothing internal mocked. The window provider is the only thing the test may **override
  via DI** to force in-window/out-of-window deterministically (it is an injected port, not a
  mock of internal logic - `B-I23` depends on this). Schedules/events seeded via the real
  services/endpoints.
- **Dual-engine:** real engines (SQLite local, Postgres CI), real SQLAlchemy.
- **N+1 capture:** a SQLAlchemy `before_cursor_execute` event listener counting real statements
  on the real engine - it observes, it does not mock.

---

## 11. Required pytest markers (TEST-012)

Module-level `pytestmark` on every new/edited Python test file:
- `test_due.py` -> `pytestmark = pytest.mark.unit`
- `test_due_query_service.py` (if the optional service-unit slice is added) -> `pytestmark = pytest.mark.unit`
- `test_due_endpoint.py` -> `pytestmark = pytest.mark.integration`
- `test_fk_cross_engine.py` (edited) -> already `pytestmark = pytest.mark.integration`

File-size: keep each test file under the QG-009 **500-LOC hard max**; if `test_due_endpoint.py`
grows past that, split by group (repository reads / service assembly / list endpoint / detail
endpoint / contract+openapi). No `test_migrations.py` edit (no migration, §2).

---

## 12. TEST-014 - Test-first evidence (the red), single lane

The build lane records in `worklog.md` the **failing run that precedes the implementation** -
the test names plus the failing assertion/error output (the "red") - before the green commit:

- Run `test_due.py`, `test_due_endpoint.py`, the cross-engine addition (`B-I33`), and the
  optional service-unit against the *unimplemented* code -> expect collection/import errors
  (no `domain.due`, no `application.due`, no `latest_event_dates` / `enabled_for_plants`
  methods, no `schedules` field on `PlantResponse`). Capture the names + the first failing line
  per group.

A worklog showing **no red-before-green** is a PRIN-III deviation requiring comply-or-explain.

---

## 13. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this foundation
and issues the **test-foundation approval**, checking:
- Every surface in §1 has its happy + sad (TEST-005); matrices M1 (§3b) and M2 (§3e) are
  present and **parametrized** with the named cells (TEST-007).
- The four **critical-100%** paths (§8) are exercised, and each survives a **sanctioned
  mutation probe** (effective-interval swap, paused-guard fallthrough, window-wrap `or`->`and`,
  type-filter leak) - each probe logged (file, mutation, failing test) and the tree restored
  byte-identically, `git status` clean.
- The both-null invariant (§7) holds at the seam (`B-U10`), the service, and over the wire
  (`B-I23`); the `schedules` entry key-set is exactly `{care_type, next_due, overdue_days}`
  (`B-I32`) and the OpenAPI is additive-only (`B-I31`).
- The N+1 bound is asserted as a **constant statement count across plant counts** at both the
  service (`B-I19`) and the list endpoint (`B-I30`) - not eyeballed.
- The grouped-MAX read ran on **both engines** (CI postgres leg, `B-I33`, ARCH-011).
- No migration was authored and no write path changed (scope, PRIN-IV).
- Every AC1-AC8 maps to a named implemented test (§9, TEST-015); the TEST-014 red is recorded
  (§12); markers (§11) present; the suite is parallel-safe (TEST-006) with per-test seeding and
  injected `today` (no real-clock dependence).
- The Playwright journey (§6) remains deferred with the precedent note intact.

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
