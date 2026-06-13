---
title: Test Foundation - app-settings (US-3.5)
type: test-foundation
change: app-settings
status: authored
date: 2026-06-13
---

# Test Foundation - app-settings (US-3.5)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for
**persisted app settings + the global seasonal toggle + the editable winter window**, and
the **additive `seasonal_aware` parameter** that wires US-3.3's `compute_due` to read them.
Authored by `test-engineer` against `proposal.md` (the ratified decisions + AC1-AC6) and
`design.md` (two disjoint-file lanes, the singleton repo + lazy default, migration 0007,
the `compute_due` edit, the `SeasonalSettingsProvider` swap, the GET/PUT API contract).
Mirrors the structure + numbering of `due-computation/test-foundation.md` (the US-3.3 code
this story extends) and the two-lane shape of `care-events/test-foundation.md`.

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. The two lanes - **backend**
(`backend/`: settings persistence + due wiring) and **frontend** (`frontend/`: the settings
page) - implement against it; backend lands first (the frontend lane builds to the API
contract). Each lane records its TEST-014 red in `worklog.md` before turning green. The
story-complete pass re-audits the implementation and issues the DoD §3 approval.

Cases are numbered so the lanes can cite them and the re-audit can diff:
`B-Un` (backend unit - the pure domain function), `B-In` (backend integration - repo,
migration, query service, web API), `F-n` (frontend), `A-n` (acceptance / Playwright). The
re-audit checks every numbered case is present, meaningful (TEST-004), and on its assigned
layer, and maps every AC1-AC6 (§10).

**Critical paths for this story** (flagged 100% in §9) - the four places a regression
silently corrupts every dashboard read or the persisted-settings contract; mutation evidence
outranks assertion-reading here (§11):

1. **The `seasonal_aware=False` branch** (AC3) - when the toggle is off, `compute_due`
   ignores BOTH the winter window AND `paused` and returns the plain-interval due. A
   paused-in-window schedule that returned `(None, None)` under US-3.3 MUST become due
   normally (never null) when the flag is off. A leaked window/paused branch here re-seasons
   a user who explicitly turned seasonality off.
2. **The `seasonal_aware=True` regression-equivalence to US-3.3** (AC3) - with the flag on,
   `compute_due` reproduces the *exact* US-3.3 behaviour (the §3b/§3c branch table from the
   due-computation foundation). The added branch must not perturb the on-path. This is the
   guard that the additive parameter is genuinely additive.
3. **The singleton-upsert-doesn't-duplicate invariant** (AC2) - `put()` always targets the
   SAME id=1 row; a second `put` UPDATEs, never INSERTs a 2nd row. A broken upsert
   silently forks settings and `get()` becomes nondeterministic.
4. **The month/day validation table** (AC5) - month 0/13, day 0/32, Feb 30, Apr 31 -> 422
   with field-names only, no PII. A missing month-aware day validator lets impossible dates
   into a persisted window.

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| D1 | `compute_due(schedule, last_event_on, today, window, seasonal_aware)` | pure domain fn (edited, additive param) | `seasonal_aware=True` reproduces US-3.3; `False` -> plain interval | `seasonal_aware=False` + paused-in-window -> due **normally** (never null) |
| D2 | `_due_from(care_type, last_event_on, today, interval)` | shared tail helper | event present -> `last+interval`; no event -> today | overdue clamp `max(0,...)`; boundary on the due day |
| R1 | `AppSettingsRepository.get()` | repo read | persisted row -> `SeasonalSettings` | no row -> `None` (lazy-default lives above the repo) |
| R2 | `AppSettingsRepository.put(settings)` | repo upsert | first put inserts id=1; round-trips via `get` | second put **UPDATEs** id=1 (no 2nd row, the singleton invariant) |
| S1 | `AppSettingsService.get()` | use case | row present -> that value | **no row -> the spec default** (`seasonal_aware=True`, Nov1-Mar1) |
| S2 | `AppSettingsService.update(...)` | use case | persists + returns the stored value | (validation lives at the web edge; service stores faithfully) |
| Q1 | `DueQueryService.for_plants(plant_ids)` | query service (edited) | reads settings ONCE, passes the flag into every `compute_due` | bounded query count with settings in play (no per-plant settings read; N+1 bound survives) |
| E1 | `GET /api/v1/settings` | endpoint | 200 + lazy-default shape on a fresh install | (read-only; shape contract asserted) |
| E2 | `PUT /api/v1/settings` | endpoint | 200 echoes the stored value | 422 on month 0/13, day 0/32, Feb 30, Apr 31; field-names only, no PII |
| F1 | `lib/api/settings.ts` (`getSettings`/`updateSettings`) | FE client | GET parses the shape; PUT sends the body | `ApiError` on non-2xx |
| F2 | `SettingsPage` | FE component | loads current values; edits + saves (PUT with the right body); "Return to default" | error-path rendering on a failed load/save |
| A1 | `/settings` journey | acceptance (Playwright) | toggle off + set window + save + reload -> persisted, zero console errors | (failure = console error / persistence loss; both breakpoints) |

The exact identifier names (`SeasonalSettings`, `AppSettingsService`, `SeasonalSettingsProvider`,
`getSettings`/`updateSettings`) are pinned by `design.md`; the re-audit checks the **behaviour
and the response contract** (§7), accepting the lane's final spelling where the design left a
choice.

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Unit is exceptionally the primary layer for `compute_due` + `_due_from`** (TEST-001 (a):
  genuinely complex pure logic, a branch table widened by the new `seasonal_aware` dimension).
  Framework-free, I/O-free, `today`/`window` injected. `pytestmark = pytest.mark.unit`. The
  `seasonal_aware` matrix (§3a M1) IS the user-meaningful behaviour and survives any
  reimplementation of the wiring (TEST-004). The US-3.3 equivalence cases (§3b) re-assert the
  on-path so the added branch is provably additive.
- **Integration is primary for everything with I/O** (TEST-001): the singleton repository
  against a **real DB** (lazy-`None`, put+get round-trip, restart persistence, the
  no-2nd-row upsert), the `DueQueryService` settings-read-once + bounded-count, the GET/PUT
  endpoints through the real composition root (router -> service -> repository -> SQLAlchemy ->
  SQLite), and the migration up/down. The settings-read-once / N+1 bound is only meaningful
  end-to-end and asserted there.
- **`DueQueryService` settings-read-once may also be unit-tested against fake ports**
  (TEST-001 (b)): a fake `SeasonalSettingsProvider` that counts calls proves the service reads
  it **once per `for_plants`**, not per plant, cheaply pinning the orchestration. The same
  bound is re-proven end-to-end via the statement-count listener (§4d).
- **Dual-engine** (`test_fk_cross_engine.py` or a dedicated cross-engine test, ARCH-011): the
  portable select-then-insert/update upsert (NOT an engine-specific `UPSERT`) and the
  singleton round-trip run identically on the engine resolved from `DATABASE_URL` (SQLite
  locally, PostgreSQL on the CI postgres leg). The smallint month/day columns + the boolean
  `seasonal_aware` (SQLite has no native boolean) are exactly the shapes that differ between
  engines, so portability is **proven, not trusted** (§5).
- **Migration** (`test_migrations.py`, edited): `0007` up/down DDL on SQLite; CI runs the
  postgres leg. `0007` down_revision is `0006`. **No row seeded** (lazy default lives in the
  service) - the test asserts the table exists with no seeded row.
- **Frontend lane** (vitest + RTL): the `settings.ts` client contract and the `SettingsPage`
  load/edit/save/return-to-default/error behaviour, fetch stubbed (§7).
- **Acceptance (Playwright, TEST-009): BUILT this story** (not deferred). Unlike the
  due-computation foundation (which had no UI), US-3.5 ships a settings *page*, so the journey
  is real: open `/settings` on the **built SPA served through the backend** (the production
  path, TEST-010), toggle off, set a window, save, reload, assert persistence + zero console
  errors at both locked breakpoints (§8).

---

## 3. Backend unit: `test_due.py` (edited) - `compute_due(..., seasonal_aware)` (`unit`)

`pytestmark = pytest.mark.unit`. The pure function against hand-built `CareSchedule` value
objects and a `WinterWindow`. No app, no DB, no I/O. `today` and `window` are injected, so
every case is deterministic (TEST-006). Reuse the existing US-3.3 fixtures (`_schedule(...)`,
`_in_window_day`, `_out_of_window_day`, the non-wrapping + wrapping windows).

**Signature note:** the new param is the 5th positional/keyword `seasonal_aware: bool`. The
existing US-3.3 cases (B-U1..B-U14 in the due-computation foundation) MUST be updated to pass
`seasonal_aware=True` (their behaviour is unchanged - that is exactly §3b's regression guard).
The cases below are the **net-new** US-3.5 cases; they keep going from the next free numbers.

### 3a. `seasonal_aware=False` matrix M1 (AC3, CRITICAL) - TEST-007

With the toggle **off**, `compute_due` MUST ignore BOTH the window AND `paused` and return the
plain `interval_days` due via the shared tail (`_due_from`). This crosses **3 dimensions**
({in_window: yes,no} x {dormancy: paused, winter_interval} x {winter_interval_days: set(=14),
None}) = 8 cells -> explicit parametrized matrix (TEST-007). **Branch-priority:** the
`seasonal_aware=False` guard is the *first* branch in the function (design pseudocode), short-
circuiting before any window/paused/winter selection. To isolate the interval selection from
overdue arithmetic, fix `last_event_on = D` and `today = D`; the only observable is
`next_due == D + interval_days` (always 7 here, never 14, never null).

Window injected = the wrapping default (Nov 1 - Mar 1) so the in-window rows are genuinely
inside it (a Jan/Dec `today`); the out-of-window rows use a summer `today`.

| id | in_window | dormancy | winter_days | seasonal_aware | next_due | proves |
|---|---|---|---|---|---|---|
| `off-in-paused-set` | yes | paused | 14 | **False** | `D+7` | **paused-in-window is due NORMALLY when off** (never null - named CRITICAL) |
| `off-in-paused-none` | yes | paused | None | **False** | `D+7` | off ignores paused regardless of winter_days |
| `off-in-wi-set` | yes | winter_interval | 14 | **False** | `D+7` | **off ignores the winter interval** even in-window (not 14 - named CRITICAL) |
| `off-in-wi-none` | yes | winter_interval | None | **False** | `D+7` | off in-window normal |
| `off-out-paused-set` | no | paused | 14 | **False** | `D+7` | off out-of-window paused normal |
| `off-out-wi-set` | no | winter_interval | 14 | **False** | `D+7` | off out-of-window normal (matches the on-path here, but proven independent) |
| `off-no-event` | (any) | (any) | (any) | **False** | `today` | off + no matching event -> due today (`_due_from` no-event arm, overdue 0) |
| `off-overdue` | yes | paused | 14 | **False** | `D+7`, overdue 2 | off + `today=D+9` -> overdue accrues normally (paused did NOT suppress) |

Cases: `B-U15` (parametrized over the interval-selection rows, asserting `next_due == D+7` /
`overdue_days == 0`); `B-U16` (`off-no-event` -> `next_due == today`, `overdue == 0`); `B-U17`
(`off-overdue`: `today = D+9`, paused-in-window schedule, off -> `next_due == D+7`,
`overdue_days == 2`). The headline trio is `off-in-paused-set` / `off-in-paused-none` /
`off-in-wi-set`: a US-3.3-correct implementation would return null or 14 here; the toggle-off
branch MUST return the plain-interval due.

### 3b. `seasonal_aware=True` regression-equivalence to US-3.3 (AC3, CRITICAL)

With the toggle **on**, `compute_due` MUST reproduce the exact US-3.3 result for every
US-3.3 scenario. Rather than restate the full M1/M2/null-path tables, this lane **re-runs the
existing US-3.3 cases with `seasonal_aware=True`** (they are already in `test_due.py`; updating
their call site to pass `True` and seeing them stay green IS the regression guard). Plus three
explicit equivalence cases that pin the two-branch fork at the boundary:

| # | test | setup | expectation |
|---|---|---|---|
| B-U18 | on + paused-in-window still nulls | `dormancy=paused`, in-window, `seasonal_aware=True` | `next_due is None` and `overdue_days is None` (the US-3.3 null-path survives the new branch) |
| B-U19 | on + in-window winter_interval still applies winter cadence | `winter_interval`, `winter_days=14`, in-window, `True` | `next_due == D+14` (the US-3.3 winter branch survives) |
| B-U20 | on vs off divergence on the SAME schedule | `dormancy=paused`, `winter_days=14`, in-window, `last=D`, `today=D` | with `True` -> `(None, None)`; with `False` -> `next_due == D+7`. The single case that proves the flag is the *only* difference (the on/off fork is exercised against one fixture). |

`B-U20` is the headline equivalence/divergence proof: one fixture, two flag values, the only
moving part is the toggle. The re-audit verifies the pre-existing US-3.3 case bodies were
updated to pass `seasonal_aware=True` and still assert the same results (no silent behaviour
drift).

### 3c. `_due_from` shared-tail behaviour (AC3)

The design factors the no-event/overdue tail into `_due_from(care_type, last_event_on, today,
interval)` so both the on-path and the off-path share it (DRY + keeps `compute_due` under the
QG-009 line ceiling). The tail is the same arithmetic US-3.3 already proves (B-U1..B-U6); these
pin it as a **named helper** so a refactor that breaks DRY is caught:

| # | test | setup | expectation |
|---|---|---|---|
| B-U21 | `_due_from` no event -> due today | `last_event_on=None`, interval 7 | `next_due == today`, `overdue_days == 0` |
| B-U22 | `_due_from` event present -> last+interval | `last=D`, `today=D`, interval 7 | `next_due == D+7`, `overdue_days == 0` |
| B-U23 | `_due_from` overdue clamp + boundary | `last=D`, interval 7; `today=D+7` -> 0; `today=D+8` -> 1; `today=D+9` -> 2 | overdue `max(0, today-next_due)`; the due-day boundary is NOT overdue |
| B-U24 | `_due_from` carries the schedule's care_type | water vs feed schedule | result `care_type` matches the schedule (keyed by the schedule, not the event) |

If the lane chooses **not** to extract a public `_due_from` (it stays inlined), B-U21..B-U24
fold into the `compute_due` cases instead - the re-audit accepts either, checking the
*behaviour* (the off-path and on-path share identical no-event/overdue arithmetic), not the
helper's visibility.

---

## 4. Backend integration: settings repo + service + query-service + web API (`integration`)

`pytestmark = pytest.mark.integration`. Real DB, nothing internal mocked (TEST-003). Each test
seeds its own settings/plants via the real services/endpoints for TEST-006 independence;
cleanup scoped to created rows, never global truncation. **Independence caveat:** the settings
table is a *singleton* (one shared id=1 row), so tests that mutate it MUST either reset it (put
the default back) or assert relative to the row they wrote within the test - never assume a
pristine table. The re-audit checks the suite is parallel-safe given the shared singleton (each
settings-mutating test owns its full read-after-write, no cross-test ordering assumption).

### 4a. Singleton repository + lazy default (R1, R2, S1; AC1, AC2)

Against the real `AppSettingsModel`/repository + `AppSettingsService` through the real session.

| # | test | setup | asserts |
|---|---|---|---|
| B-I1 | repo `get()` returns None when no row | empty `app_settings` table | `repository.get() is None` (the lazy default lives ABOVE the repo, not in it) |
| B-I2 | **service `get()` lazy default when no row** | no row | `service.get()` -> `seasonal_aware=True`, window Nov1-Mar1 (11/1-3/1) - the spec default, no seeding (AC1) |
| B-I3 | **put then get round-trip** | `put(seasonal_aware=False, May1-Sep1)` then `get()` | the stored value round-trips exactly (`seasonal_aware=False`, 5/1-9/1); `service.get()` returns it (not the default) |
| B-I4 | **persistence across a fresh repository/session** (restart proxy) | put a non-default value via repo A; construct a **new** repository on a **fresh session/engine** bound to the same DB; `get()` | the new repo reads the persisted row (real durable row, not in-memory state) - the AC2 "survives a process restart" proof at the repo layer |
| B-I5 | **portable upsert updates the SAME row, never inserts a 2nd** (CRITICAL) | `put(A)` then `put(B)` (different values); then count rows in `app_settings` | row count == **1** after both puts; `get()` returns B (the last write). The singleton invariant: second put UPDATEs id=1, never INSERTs (AC2) |
| B-I6 | upsert is portable select-then-update (not engine UPSERT) | inspect that `put` works on the default-path engine without `ON CONFLICT`/`INSERT OR REPLACE` engine-specific SQL | round-trip succeeds; the dual-engine proof is §5 (this case just exercises the happy upsert on the local engine) |

`B-I5` is the singleton-upsert critical proof (counts rows, asserts exactly one). `B-I4` is the
restart-persistence proof at the repo layer (the API-level restart proof is `B-I14`).

### 4b. Migration 0007 (AC2)

Edit `test_migrations.py`. `0007_create_app_settings` down_revision is `0006`.

| # | test | asserts |
|---|---|---|
| B-I7 | **`0007` creates app_settings + downgrade drops it** | upgrade head; `inspect` shows the `app_settings` table with columns `{id, seasonal_aware, start_month, start_day, end_month, end_day, updated_at}`; `id` is the PK; month/day columns are smallint/integer; `seasonal_aware` is boolean; **no row is seeded** (a select returns 0 rows). Downgrade to `0006` drops `app_settings` but leaves `care_event`/`care_schedule`/`photo`/`plant`/`plant_tag`. |

CI runs the same DDL on the postgres leg (no separate test). The dual-engine *data* round-trip
(boolean + smallint portability) is `B-I8` (§5).

### 4c. Web API - GET/PUT /settings (E1, E2; AC1, AC5)

Through the real composition root. Helper: `_settings_url() -> "/api/v1/settings"`,
`_reset_settings(client)` (PUT the default back, for independence).

#### 4c-i. GET lazy-default shape (AC1)

| # | test | asserts |
|---|---|---|
| B-I9 | **GET on a fresh install returns the lazy default** | no row in `app_settings`; `GET /api/v1/settings` -> 200; body == `{"seasonal_aware": true, "winter_window": {"start_month": 11, "start_day": 1, "end_month": 3, "end_day": 1}}` (AC1); top-level keys are exactly `{seasonal_aware, winter_window}`; `winter_window` keys exactly `{start_month, start_day, end_month, end_day}` (§7 shape) |

#### 4c-ii. PUT round-trip echo (AC2)

| # | test | asserts |
|---|---|---|
| B-I10 | **PUT persists + echoes; follow-up GET returns it** | `PUT {"seasonal_aware": false, "winter_window": {5,1,9,1}}` -> 200, body echoes the stored value; a subsequent `GET` returns the same (the persisted, not the default) |
| B-I11 | PUT toggle-only round-trip | `PUT {"seasonal_aware": false, winter_window: default}` -> 200; GET -> `seasonal_aware=false`, window still the default (the toggle and window are independent fields) |
| B-I12 | PUT a southern-hemisphere non-wrapping window | `PUT {seasonal_aware:true, winter_window:{5,1,9,1}}` -> 200; GET round-trips May1-Sep1 (AC4 storage half: a non-wrapping window persists; the *classification* of wrap-vs-non-wrap is the US-3.3 `WinterWindow.contains` matrix, already proven) |

#### 4c-iii. Validation matrix M2 - month/day (AC5, CRITICAL) - TEST-007

`SettingsUpdate` rejects impossible month/day combos. Two value-objects (start, end) x the
day-vs-month rule -> a >6-cell matrix -> explicit parametrized table. **Branch-priority:**
month range (1-12) is checked first (independent), then the month-aware day validator
(Feb<=29, Apr/Jun/Sep/Nov<=30, others<=31, day>=1). Each 422 asserts the body keys are exactly
`{"detail"}` and that the validation field-names (e.g. `start_month`) MAY appear but **no PII**
(no free text - settings carry none, so this is structurally satisfied; the case asserts the
422 body contains no value beyond Pydantic's field-location detail).

| id | field/value | expected | proves |
|---|---|---|---|
| `valid-default` | 11/1 - 3/1 | 200 | the default round-trips (B-I9/B-I10 cover the happy path) |
| `valid-feb-29` | start 2/29 | 200 | Feb 29 accepted (leap-year-agnostic upper bound, design §validation) |
| `start-month-0` | start_month 0 | **422** | month lower bound (named CRITICAL) |
| `start-month-13` | start_month 13 | **422** | month upper bound (named CRITICAL) |
| `end-month-13` | end_month 13 | **422** | end month independently validated |
| `start-day-0` | start_day 0 | **422** | day lower bound (named CRITICAL) |
| `start-day-32` | start_day 32 | **422** | day upper bound (named CRITICAL) |
| `feb-30` | start 2/30 | **422** | **Feb 30 rejected** (month-aware day validator - named CRITICAL) |
| `apr-31` | start 4/31 | **422** | **Apr 31 rejected** (30-day month - named CRITICAL) |
| `sep-31` | end 9/31 | **422** | Sep 31 rejected (another 30-day month, on the end field) |
| `feb-30-end` | end 2/30 | **422** | the month-aware rule applies to the END value too (not only start) |
| `seasonal-not-bool` | seasonal_aware "yes" | **422** | bool coercion guard (design: `seasonal_aware` a bool) |

Cases: `B-I13` (parametrized `test_settings_validation_matrix` over all rows; the 200 rows
assert round-trip, the 422 rows assert status 422 + `{"detail"}`-only body + no PII).
`feb-30`/`apr-31`/`sep-31`/`feb-30-end` are the month-aware critical cells (a naive `1-31`
range validator passes these incorrectly); `start-month-0/13` + `start-day-0/32` pin the plain
ranges.

#### 4c-iv. API restart persistence (AC2)

| # | test | asserts |
|---|---|---|
| B-I14 | **PUT then GET on a fresh app instance** | `PUT` a non-default value; build a **second** FastAPI app/client over the **same DB**; `GET /settings` on the fresh app -> the persisted value (not the default). The end-to-end "survives a process restart" proof (AC2), complementing the repo-level `B-I4`. |

### 4d. DueQueryService settings-read-once + bounded count (Q1; AC3, NFR)

The US-3.3 N+1 bound MUST survive: the service reads settings **once per query** (replacing the
old `WinterWindowProvider.current_window()` single read with a single
`SeasonalSettingsProvider` read that yields both the window AND the flag), and passes the flag
into every `compute_due`. **No per-plant settings read.**

| # | test | setup | asserts |
|---|---|---|---|
| B-I15 | **provider read exactly ONCE per `for_plants`** (unit-against-fake variant per §2) | a fake `SeasonalSettingsProvider` counting `current()` calls; seed N=10 plant ids each with schedules | `for_plants` calls the provider **once** regardless of N; the count is 1 for N and 1 for 2N (not per-plant) |
| B-I16 | flag threaded into compute_due | `seasonal_aware=False` from the provider; a paused-in-window schedule with a recent event | the assembled `ScheduleDue` for that schedule is **due normally** (non-null `next_due`), proving the service passed `False` through (the integration echo of B-U15) |
| B-I17 | **bounded statement count across N/2N with seasonal settings in play** (CRITICAL for NFR) | seed N then 2N plants with water+feed schedules + events, a persisted settings row present | the SQL statement count for `for_plants` does **not** scale with the plant count - it stays the US-3.3 bound **plus at most one** settings select, and the *delta* between N and 2N is constant. Captured via the same `before_cursor_execute` listener approach as the US-3.3 `B-I19`. The settings read does NOT introduce a per-plant query. |

`B-I15` (the fake-counter, read-once) + `B-I17` (the real statement count, constant across
N/2N) together prove the settings wiring did not regress the N+1 bound. `B-I17` is the NFR
critical guard (p95 < 200 ms for 500 plants depends on the flat list path).

### 4e. Endpoint behaviour through the due path with the toggle (AC3 end-to-end)

| # | test | setup | asserts |
|---|---|---|---|
| B-I18 | **toggle off flips a paused-in-window schedule to due** (end-to-end) | seed a plant with a paused schedule + a recent water event; force `today` inside the window (inject the today-provider in the test app, mirroring US-3.3 `B-I23`); `PUT {seasonal_aware:false}`; `GET /plants/{id}` | the schedule's `next_due` is **non-null** (due normally) with the toggle off; then `PUT {seasonal_aware:true}` + re-GET -> the same schedule's `next_due` is JSON `null` again (paused-in-window). The single end-to-end proof that the persisted toggle drives `compute_due` (AC3). |

`B-I18` is the AC3 end-to-end headline: it exercises the full path
(PUT settings -> persisted row -> provider -> DueQueryService -> compute_due -> response)
and proves the SAME plant's due state flips with the toggle, in both directions.

---

## 5. Dual-engine: cross-engine test (`integration`, ARCH-011)

Add to `test_fk_cross_engine.py` (or a small dedicated cross-engine test) one test resolving
the engine from `DATABASE_URL` via the existing `fk_engine` fixture (SQLite locally,
PostgreSQL on the CI postgres leg). The boolean `seasonal_aware` (SQLite has no native boolean)
+ the smallint month/day columns + the **portable select-then-insert/update upsert** are
exactly the shapes that differ most between engines - proven, not trusted.

| # | test | asserts |
|---|---|---|
| B-I8 | **singleton upsert round-trips identically on the real engine** | via the repository on the **real engine**: `put(seasonal_aware=False, May1-Sep1)`; `get()` -> the exact value (boolean + smallints round-trip on **both** engines); then `put(seasonal_aware=True, default)` and assert the `app_settings` row count is still **1** (the portable upsert UPDATEs the singleton on both engines, never inserts a 2nd). Self-cleans its own row (resets to default or deletes). |

The re-audit checks `B-I8` ran on **both** engines at minimum (the upsert + the boolean
round-trip are the two nontrivial-portability concerns in this story, ARCH-011).

---

## 6. Frontend (vitest + RTL)

Mirror `careEvents.test.ts` / `careSchedules.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson`/`fail` helpers, `afterEach(unstubAllGlobals + restoreAllMocks)`. **fetch is the mock
boundary** (TEST-003 FE equivalent). A `SAMPLE: AppSettings` constant carries the full shape
(`{seasonal_aware, winter_window:{start_month, start_day, end_month, end_day}}`).

### 6a. `settings.test.ts` (client contract)

| # | test | asserts |
|---|---|---|
| F-1 | `getSettings` GETs the settings path | `GET /api/v1/settings`, `Accept: application/json`; resolves the parsed `AppSettings` (shape `{seasonal_aware, winter_window:{...}}`) |
| F-2 | `updateSettings` PUTs the body | method **PUT**, path `/api/v1/settings`, `Content-Type: application/json`, body == `JSON.stringify(input)` carrying `seasonal_aware` + the four window fields; resolves the echoed `AppSettings` (200) |
| F-3 | `getSettings` throws ApiError on non-2xx | a 500 -> rejects `instanceof ApiError` |
| F-4 | `updateSettings` throws ApiError on non-2xx (incl. 422) | a 422 -> rejects `instanceof ApiError` (the page surfaces it; F-9) |

### 6b. `SettingsPage.test.tsx` (component, RTL)

| # | test | asserts |
|---|---|---|
| F-5 | **loads + displays current values on mount** | mount with the fetch stub returning `{seasonal_aware:false, winter_window:{5,1,9,1}}` -> the toggle reflects `false`; the four window inputs show 5/1/9/1 (a single `GET /settings` fired on mount) |
| F-6 | **edits + saves: PUT called with the right body** | from the loaded default, switch the toggle off and change start to 12/15, then Save -> a single `PUT /settings` whose body is `{seasonal_aware:false, winter_window:{start_month:12, start_day:15, end_month:3, end_day:1}}` (the assembled current form state); inline success feedback shown |
| F-7 | **"Return to default" resets ONLY the window inputs to 11/1 and 3/1** (CRITICAL) | load with `{seasonal_aware:false, window:{5,1,9,1}}`; click "Return to default" -> the window inputs become 11/1/3/1 **and the toggle stays `false`** (the button does NOT touch the toggle, proposal §FE); then Save -> PUT body has the default window but `seasonal_aware:false` (proves reset is window-only) |
| F-8 | save error surfaced inline | Save with the fetch stub returning 422 -> an inline error is rendered; the form stays editable (no crash, no navigation) |
| F-9 | load error surfaced inline | mount with the GET stub returning 500 -> an inline error/empty-state is rendered (the page degrades gracefully, does not throw) |

`F-7` is the return-to-default critical proof: it asserts the toggle is **unchanged** and the
subsequent PUT body carries the default window WITH the untouched toggle value (so a regression
that also resets the toggle is caught).

### 6c. fetch-mock contract fixtures (shared)

An `AppSettings` SAMPLE (default + a non-default variant) and the `okJson(status, body)` /
`fail(status)` helpers from `careEvents.test.ts`. The component tests render the real
`SettingsPage` (RTL); the toggle is driven via its label (`getByLabel`), the window inputs via
their labels, "Return to default" + "Save" via their accessible names (FE-011 / FE-014).

---

## 7. Response contract (pinned)

Both `GET` and `PUT /api/v1/settings` use **exactly** this shape, no more (the §4c key-set
assertions enforce it structurally):

```
{ "seasonal_aware": bool,
  "winter_window": { "start_month": int, "start_day": int,
                     "end_month": int, "end_day": int } }
```

| field | type | rule |
|---|---|---|
| `seasonal_aware` | `bool` | default `true`; the global toggle |
| `winter_window.start_month` / `end_month` | `int` 1-12 | month, inclusive endpoint |
| `winter_window.start_day` / `end_day` | `int` valid for the month | day, month-aware upper bound (Feb<=29, 30-day months<=30) |

The response never exposes `id` (the singleton surrogate, ARCH-007) or `updated_at` (server
bookkeeping) - those stay below the boundary. PUT echoes the stored value (it is the same shape
as GET). 422 bodies are `{"detail"}`-only with field-locations, no PII (settings carry no free
text, so this is structurally satisfied; B-I13 asserts it).

---

## 8. Acceptance (Playwright, TEST-009 - BUILT) - the production path (TEST-010)

The settings page is real UI in scope, so the acceptance test is **built this story** (not
deferred). It runs against the **built SPA served through the backend** (the production path,
TEST-010 / TEST-009/010 production-path discipline) - NOT the Vite dev server - so the journey
exercises the same artifact users get. POM (FE-013): a `settings.po.ts` carrying only locators
(the toggle, the four window inputs, "Return to default", "Save", the success/error feedback),
preferring `getByTestId`/`getByLabel`/`getByRole` (FE-014). The driver uses **real UI
affordances only** - never inject values directly.

| # | test | journey | asserts |
|---|---|---|---|
| A-1 | **settings persist across reload, zero console errors** | open `/settings` on the built SPA -> the page loads the current settings; **toggle seasonal-aware OFF**; **set a window** (e.g. start May 1, end Sep 1) via the inputs; **Save** -> inline success; **reload the page** | after reload the toggle is OFF and the window inputs show the saved May1-Sep1 (values persisted through the real backend + DB, AC2/AC6) |
| A-2 | "Return to default" resets the window in the running app | on `/settings`, with a non-default window loaded, click "Return to default" -> the window inputs show 11/1 and 3/1; the toggle is unchanged; Save + reload -> the default window persisted, the toggle still as it was (AC6, the end-to-end echo of F-7) |

**Console-error fail-on (TEST-010):** both journeys **fail** on any page error or error-level
console output across the whole flow (load, edit, save, reload); warnings are ignored; any
allowlisted pattern needs an inline justification comment.

**Breakpoints:** A-1 runs at **both locked breakpoints** - phone **390 px** and desktop
**1280 px** (the two that bracket the responsive range; the precedent set carries
390/820/1280). The journey + assertions are identical at each width; no horizontal scroll at
390 (FE-011).

**FE-012 design-review screenshots (committed, required evidence).** Captured at the locked
breakpoints and committed to `specs/changes/app-settings/screenshots/` (the folder already
exists). Enumerated required files:

- `settings-phone-390.png` - the settings page at 390 px (toggle + window inputs + buttons).
- `settings-tablet-820.png` - the settings page at 820 px.
- `settings-desktop-1280.png` - the settings page at 1280 px.
- `settings-saved-1280.png` - the success-feedback state after a Save at 1280 px.

These are FE-012 design-review evidence (deliberate, curated, committed) - distinct from
TEST-011 failure-capture screenshots (ephemeral, never committed).

### 8a. FE-015 Audit Spaces (per-story mandatory)

US-3.5 ships UI, so the two Audit Spaces are asserted (no opt-out justification in the proposal):

| # | test | asserts |
|---|---|---|
| A-3 | **a11y space** - axe-core scan + FE-011 | an axe-core scan (via Playwright) of `/settings` reports no violations; the toggle has an accessible name, every window input has an associated `<label>`, "Return to default" + "Save" have accessible names, tap targets >=44x44 px, no horizontal scroll at 390 px (FE-011) |
| A-4 | **perf-budget space** - FE-007 | the production bundle-size budget holds (the FE-007 CI/test assertion); adding the settings page must not regress past the budget |

A-4 is the existing repo-wide budget assertion (the settings page adds a thin route); the
re-audit checks it is enforced as a **test/CI assertion**, not merely a build warning (FE-015).

---

## 9. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; repo currently ~99% backend - this story **MUST NOT** drop the floor.
  New/changed code **>=80% diff-cover**.
- **Branch coverage:** **>=95% in domain + application** - the new `seasonal_aware` branch in
  `compute_due`, the `_due_from` arms, the `AppSettingsService.get()` row-vs-default fork, and
  the `DueQueryService` provider read are all exercised. **>=80% in adapters/outbound** (the
  singleton upsert select-then-insert/update fork, the lazy-`None` repo read, the router
  GET/PUT, the Pydantic validators).
- **Critical paths flagged 100%** (spec-flagged -> QG-002 100% required). These four are where
  a regression silently corrupts a dashboard or the persisted-settings contract; **mutation
  evidence outranks assertion-reading** at story-complete (§11):
  1. **`seasonal_aware=False` branch** (AC3) - matrix M1 (`B-U15`-`B-U17`) + `B-I16`/`B-I18`.
  2. **`seasonal_aware=True` US-3.3 equivalence** (AC3) - the updated US-3.3 cases + `B-U18`-
     `B-U20`.
  3. **Singleton-upsert no-duplicate** (AC2) - `B-I5` (count==1) + `B-I8` (both engines).
  4. **Month/day validation table** (AC5) - matrix M2 (`B-I13`) incl. Feb 30 / Apr 31.
- Combined pytest run (unit + integration) scores the union (TEST-001); the unit branch matrix
  + the integration repo/endpoint slice clear the floor without brittle implementation-mirroring
  tests (TEST-004).

---

## 10. AC traceability (TEST-015) - every AC -> >=1 named case

| AC | scenario | covering cases |
|---|---|---|
| **AC1** | fresh install GET -> `seasonal_aware=true` + Nov1-Mar1 | `B-I2` (service default); `B-I9` (endpoint lazy-default shape) |
| **AC2** | PUT persists window + toggle; follow-up GET returns them; survives a restart (real row, both engines) | `B-I3`/`B-I10` (round-trip); `B-I4`/`B-I14` (restart persistence repo + API); `B-I5`/`B-I8` (singleton no-2nd-row, both engines); `B-I7` (migration) |
| **AC3** | toggle on -> winter/paused exactly as US-3.3; toggle off -> plain interval, paused due normally (no null) | `B-U15`-`B-U17` (off matrix); `B-U18`-`B-U20` (on equivalence + on/off divergence); `B-I16`/`B-I18` (end-to-end flip); `B-I15`/`B-I17` (settings read once, bound survives) |
| **AC4** | southern-hemisphere window classifies correctly; default wraps the new year | storage half: `B-I12` (non-wrapping window persists); classification half: the US-3.3 `WinterWindow.contains` matrix (M2 `B-U14` in due-computation, unchanged + reused) - this story does not re-implement `contains`, it persists the window the classifier reads |
| **AC5** | invalid month/day (13/01, 02/30, etc.) -> 422, no PII | matrix M2 `B-I13` (start-month-0/13, start-day-0/32, feb-30, apr-31, sep-31, feb-30-end, seasonal-not-bool) |
| **AC6** | settings page loads + edits + saves; "return to default" resets the window; production path, zero console errors, both breakpoints | `F-5` (load), `F-6` (save body), `F-7` (return-to-default window-only); `A-1` (persist + reload + zero console errors, both breakpoints); `A-2` (return-to-default end-to-end); FE-012 screenshots (§8); `A-3` a11y, `A-4` perf (FE-015) |

No AC is uncovered. Every numbered case maps to an AC, pins the response contract (§7:
`B-I9` key-set), the dual-engine portability (§5: `B-I8`), the N+1 bound (`B-I15`/`B-I17`), or
a boundary the ACs imply (`B-U21`-`B-U24` `_due_from` arithmetic, `B-I1` lazy-`None` repo).

**AC4 note (scope boundary):** US-3.5 *persists* the window; the wrap/non-wrap *classification*
was built + proven exhaustively in US-3.3 (`WinterWindow.contains`, due-computation foundation
matrix M2). This story does NOT touch `contains`, so AC4's classification is covered by reusing
the existing matrix; the net-new AC4 obligation is that a southern (non-wrapping) window
*persists and round-trips* (`B-I12`), and that the default that wraps is what a fresh install
returns (`B-I2`/`B-I9`). If the lane finds itself editing `WinterWindow.contains`, that is a
scope deviation to halt and flag (PRIN-IV / SPEC-001).

---

## 11. Mutation probes (story-complete re-audit) - sanctioned, restored byte-identically

At story-complete, the test-engineer runs sanctioned mutation probes on the four critical-100%
paths (§9), logging each (file, mutation, failing test), restoring byte-identically, and
verifying `git status` clean. The orchestrator independently verifies the clean tree.

| critical path | file | mutation | test that MUST go red |
|---|---|---|---|
| 1. `seasonal_aware=False` branch | `backend/src/viridarium/domain/due.py` | delete the `if not seasonal_aware:` early-return (let it fall through to the US-3.3 body) | `B-U15` (`off-in-paused-set` -> would return null instead of `D+7`) and `B-I18` (toggle-off no longer flips the paused schedule to due) |
| 1b. off-path interval source | `due.py` | in the off branch, use `winter_interval_days` instead of `interval_days` | `B-U15` (`off-in-wi-set` expects 7, would get 14) |
| 2. on-path equivalence | `due.py` | invert the guard to `if seasonal_aware:` early-return-plain (flip the flag's meaning) | the updated US-3.3 cases + `B-U18`/`B-U19`/`B-U20` (the on-path would now skip winter/paused) |
| 3. singleton upsert | `backend/src/viridarium/adapters/outbound/db/...settings repository` | change the upsert to always INSERT (drop the select-then-update / id=1 targeting) | `B-I5` (row count would become 2) and `B-I8` (both engines) |
| 4. month/day validation | `backend/src/viridarium/adapters/inbound/web/...settings schema` | remove the month-aware day validator (keep only `1-31`) | `B-I13` rows `feb-30` / `apr-31` / `sep-31` / `feb-30-end` (would now return 200) |
| 4b. month range | settings schema | widen `start_month`/`end_month` to allow 0-13 | `B-I13` rows `start-month-0` / `start-month-13` / `end-month-13` |
| (FE) return-to-default | `frontend/src/.../SettingsPage.tsx` | make "Return to default" also reset `seasonal_aware` to true | `F-7` (asserts the toggle is unchanged) |

The exact adapter file paths are the backend lane's to finalize (the design names
`adapters/outbound/db` for the repo and `adapters/inbound/web` for the schema); the re-audit
locates the implemented file and probes the named behaviour.

---

## 12. Mocking boundary (TEST-003) - explicit

- **Unit (`test_due.py`, edited; optional `test_due_query_service.py`):** the pure
  `compute_due` / `_due_from` take plain value objects + `seasonal_aware: bool`. The optional
  service-unit uses a **fake** `SeasonalSettingsProvider` (a call-counter for `B-I15`) + fake
  schedule/event repos. No app, no DB, no I/O, no real clock (`today` injected).
- **Integration (settings repo + endpoint + query-service tests):** real DB through the real
  composition root; nothing internal mocked. The today-provider is the only thing the test may
  **override via DI** to force in-window/out-of-window deterministically (`B-I18`, mirroring
  US-3.3 `B-I23`) - it is an injected port, not a mock of internal logic.
- **Dual-engine / migration:** real engines (SQLite local, Postgres CI), real SQLAlchemy /
  Alembic.
- **N+1 capture:** a SQLAlchemy `before_cursor_execute` listener counting real statements on
  the real engine (`B-I17`) - it observes, it does not mock.
- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. Component tests
  render the real `SettingsPage` (RTL).
- **Acceptance (Playwright):** the built SPA served through the **real backend** + real DB (the
  production path); nothing mocked - the persistence reload (A-1) depends on real durability.

---

## 13. Required test markers + file-size (TEST-012, QG-009)

Module-level `pytestmark` on every new/edited Python test file:
- `test_due.py` (edited) -> `pytestmark = pytest.mark.unit`
- `test_due_query_service.py` (if the optional service-unit slice is added) -> `pytestmark = pytest.mark.unit`
- the new settings integration test file(s) (e.g. `test_settings_endpoint.py`, settings repo
  test) -> `pytestmark = pytest.mark.integration`
- `test_fk_cross_engine.py` (edited) -> already `pytestmark = pytest.mark.integration`
- `test_migrations.py` (edited) -> already `pytestmark = pytest.mark.integration`

Frontend `*.test.ts(x)` run under vitest (no marker); Playwright specs under the e2e config
(TEST-009). File-size: keep each test file under the QG-009 **500-LOC hard max**; if the
settings endpoint test grows past it, split by group (repo+migration / GET-PUT happy /
validation matrix / due-wiring). No edit to `WinterWindow.contains` tests (out of scope, §10).

---

## 14. TEST-014 - Test-first evidence (the red), per lane

Each lane records in `worklog.md` the **failing run that precedes the implementation** - the
test names plus the failing assertion/error output (the "red") - before the green commit:

- **Backend lane red:** run the edited `test_due.py` (the new `seasonal_aware` cases +
  the US-3.3 cases now passing `seasonal_aware=True`), the settings integration tests, the
  `0007` migration test (`B-I7`), and the cross-engine addition (`B-I8`) against the
  *unimplemented* code -> expect collection/import + signature errors (`compute_due` has no
  `seasonal_aware` param, no `domain.app_settings`, no `application.settings`, no
  `/api/v1/settings` routes, no `app_settings` table). Capture the names + the first failing
  line per group.
- **Frontend lane red:** run `settings.test.ts` + `SettingsPage.test.tsx` against the
  *unimplemented* `lib/api/settings.ts` / `SettingsPage.tsx` (the route is currently a
  `PlaceholderPage`) -> expect module-not-found / assertion failures. Capture the names + errors.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain.

---

## 15. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this foundation
and issues the **test-foundation approval**, checking:

- Every surface in §1 has its happy + sad (TEST-005); matrices M1 (§3a) and M2 (§4c-iii) are
  present and **parametrized** with the named cells (TEST-007).
- The four **critical-100%** paths (§9) are exercised, and each survives a **sanctioned
  mutation probe** (§11: the off-branch deletion, the on/off guard inversion, the always-INSERT
  upsert, the month-aware-validator removal) - each probe logged (file, mutation, failing test)
  and the tree restored byte-identically, `git status` clean.
- The US-3.3 cases were updated to pass `seasonal_aware=True` and still assert their original
  results (no behaviour drift); `B-U20` proves the toggle is the only moving part.
- The singleton invariant holds: `put` twice -> exactly **one** row (`B-I5`), on **both
  engines** (`B-I8`); lazy default returns Nov1-Mar1 with no seeded row (`B-I2`/`B-I9`); `0007`
  applies + rolls back with no seed (`B-I7`).
- The settings read is **once per query** (`B-I15`) and the N+1 bound is asserted as a
  **constant statement count across N/2N** (`B-I17`) - not eyeballed.
- The response shape is exactly `{seasonal_aware, winter_window:{start_month, start_day,
  end_month, end_day}}` at both endpoints (`B-I9` key-set); no `id`/`updated_at` leak (§7).
- The frontend "Return to default" resets the window only and leaves the toggle untouched
  (`F-7`); the page loads/saves/error-renders (`F-5`/`F-6`/`F-8`/`F-9`).
- The acceptance journey runs on the **production path** (built SPA through the backend),
  persists across reload with **zero console errors** at **both breakpoints** (`A-1`/`A-2`,
  TEST-009/010); FE-012 screenshots committed (§8); the FE-015 a11y + perf spaces asserted
  (`A-3`/`A-4`).
- No edit to `WinterWindow.contains`; no write path changed beyond the additive settings
  table + the `compute_due` parameter (scope, PRIN-IV).
- Every AC1-AC6 maps to a named implemented test (§10, TEST-015); the TEST-014 red is recorded
  per lane (§14); markers (§13) present; the suite is parallel-safe (TEST-006) given the shared
  singleton (each settings test owns its read-after-write; `today` injected, no real-clock
  dependence).

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
