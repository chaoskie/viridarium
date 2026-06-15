---
title: Test Foundation - today-view (US-4.1)
type: test-foundation
change: today-view
status: authored
date: 2026-06-15
---

# Test Foundation - today-view (US-4.1)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for the
**Today view**: the v0.1 payoff screen at `/` that derives, from the existing
`GET /api/v1/plants` (per-schedule `next_due`/`overdue_days` from US-3.3) plus
`GET /api/v1/locations`, the set of plants needing **water or feed today**, groups them by
location (homeless plants in their own "No location" group), sorts most-overdue-first, and
offers a **one-tap** Water / Feed / Both action per card that logs the CareEvent(s) for
today via the existing `careEvents` client and updates the card **without a full reload**.
Authored by `test-engineer` against `proposal.md` (the PO-resolved layout / data-source /
one-tap model, the "needs attention today" derivation, AC1-AC6, the deferred feeding-mode
#66) and `design.md` (the pure `buildTodayGroups(plants, locations, today)` + the `TodayCard`
one-tap). Mirrors the structure + numbering and the FE + acceptance lanes of
`care-timeline/test-foundation.md` and `app-settings/test-foundation.md`; the locked
breakpoints are 390 phone / 1280 desktop.

**This story is frontend-only.** No backend file, no endpoint, no migration, no contract
change (proposal §"Out of scope", design §"What this does NOT change"). The single net-new
type change is additive: `ScheduleDue {care_type, next_due, overdue_days}` + `Plant.schedules`
added to `frontend/src/lib/api/plants.ts` (the field is already on the wire from US-3.3).

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. Three lanes -
**unit** (`U-n`: the pure `buildTodayGroups`, the only non-trivial logic, TEST-001(a)),
**component** (`C-n`: `TodayPage` + `TodayCard` via Testing Library, the api clients
stubbed), and **acceptance** (`A-n`: the production-path live smoke + screenshots) -
implement against it. The story is a **single FE lane** (no backend lane to land first),
but the foundation is authored before any code. The lane records its TEST-014 red in
`worklog.md` before turning green. The story-complete pass re-audits the implementation
and issues the DoD §3 approval.

Cases are numbered so the lane can cite them and the re-audit can diff:
`U-n` (unit - the pure `buildTodayGroups`), `C-n` (component - `TodayPage`/`TodayCard`,
vitest + RTL), `A-n` (acceptance / production path). The re-audit checks every numbered
case is present, meaningful (TEST-004), and on its assigned layer, and maps every AC1-AC6
(§9).

**Critical paths for this story** (flagged 100% in §10) - the four places a regression
silently corrupts the headline "what needs water or feed today" promise or the one-tap
contract; **mutation evidence outranks assertion-reading** here (§11):

1. **The attention-set classification incl. null/future exclusion** (AC1, AC4) - a schedule
   is "needs attention" iff `next_due != null` AND `next_due <= today` (overdue:
   `overdue_days > 0`; due-today: `overdue_days == 0`). A paused/dormant schedule
   (`next_due == null`) and a future schedule (`next_due > today`) MUST be excluded; a plant
   with no due schedule MUST NOT appear. A broken filter either floods the Today view with
   not-yet-due plants (eroding the 5-second promise) or, worse, surfaces paused plants the
   user deliberately silenced.
2. **The both-due -> both-care-types** (AC3) - a plant whose water AND feed schedules are
   both due yields BOTH care types in `dueCareTypes` (driving the "Both" button); a plant
   due on only one care type yields only that one. A regression that collapses to a single
   care type loses the second task silently (the user thinks they are done after one tap).
3. **The group/homeless ordering** (AC1) - cards group by `location_id`, the null-location
   group is the "No location" group, groups order by location name with the homeless group
   **last**, and within a group cards sort `worstOverdue` desc then plant name. A broken
   ordering scatters a room's plants or buries the most-overdue plant.
4. **The one-tap-updates-without-reload** (AC3) - tapping Water/Feed/Both calls
   `createEvent` with `{type, happened_on: today}` for each chosen type (Both = both types),
   and on success the satisfied care type drops from the card (the card leaves the list when
   nothing is left due) **without a full page reload**. A regression that needs a manual
   reload, or that drops the wrong care type, breaks the one-tap promise.

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| P1 | `buildTodayGroups(plants, locations, today)` | pure derivation (the only non-trivial logic, TEST-001(a)) | due + overdue plants grouped by location, ordered, classified | paused(`next_due==null`)/future(`next_due>today`) schedules excluded; a plant with no due schedule absent; empty input -> `[]` |
| C1 | `TodayPage` (replaces the placeholder) | FE page (fetch plants + locations, derive, render) | loads + renders grouped cards with location headers + badges | loading state; load error degrades (no crash); empty-state when nothing due |
| C2 | `TodayCard` | FE component (per-plant card + one-tap) | shows the per-due-care-type button(s) + a Both button iff both due; tap logs + updates live | a failed log surfaces inline (no crash); buttons disabled in-flight |
| A1 | `/` Today journey | acceptance (production path, built SPA through the backend) | grouped due/overdue render with correct overdue counts; one-tap updates the card live; zero console errors at 390 + 1280 | (failure = any console error / a wrong overdue count / a non-updating card; both breakpoints) |

The exact identifier names (`buildTodayGroups`, `TodayPage`, `TodayCard`, the card model
`{plant, dueCareTypes, worstOverdue}`) are pinned by `design.md`; the re-audit checks the
**behaviour and the card model** (§7), accepting the lane's final spelling where the design
left a choice (e.g. whether the page refetches plants on a successful tap or locally drops
the satisfied care type - both are sanctioned by design §One-tap, and `C2` asserts the
*observable* "no full reload + the satisfied type drops" either way).

**`ScheduleDue` type-addition note.** The lane adds, to `frontend/src/lib/api/plants.ts`,
`export interface ScheduleDue { care_type: "water" | "feed"; next_due: string | null;
overdue_days: number | null }` and `readonly schedules: readonly ScheduleDue[]` to `Plant`.
This is additive and already on the wire (US-3.3); the re-audit checks it is **additive**
(no other `Plant` field changed) and that `care_type` is the closed `water|feed` schedule
vocabulary (NOT the four-member `CareEventType` - they differ; the one-tap maps the schedule
`care_type` to the event `type`, which for water/feed is the same string).

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Unit is exceptionally the primary layer for `buildTodayGroups`** (TEST-001 (a): the one
  piece of genuinely non-trivial pure logic in this story - the per-schedule classification,
  the exclusion of null/future, the grouping incl. the homeless group, the two-level group
  ordering, the within-group most-overdue-first sort, the both-due fan-out into
  `dueCareTypes`, and `worstOverdue = max(overdue_days)`). Framework-free, no fetch, no DOM,
  with **`today` injected explicitly** (no real clock - TEST-006). This IS the
  user-meaningful behaviour and survives any reimplementation of the page wiring (TEST-004).
  The classification matrix (§3 M-CLS) is exhaustively pinned here cheaply. **This is the
  only unit slice**; the page/card wiring is component-tested, not unit-tested.
- **Component is the primary layer for the page + card** (TEST-001): `TodayPage` and
  `TodayCard` rendered with Testing Library, the **api clients (`fetchPlants`,
  `fetchLocations`, `createEvent`) as the mock boundary** (TEST-003 FE equivalent - stub
  `fetch` via `vi.stubGlobal`, mirroring `careEvents.test.ts` / `QuickCareActions.test.tsx`).
  The render of groups + badges, the per-due-care-type button set + the Both button, the
  one-tap call shape, the live card update without reload, the empty/loading/error states,
  and the in-flight disable are all only meaningful through the rendered component and
  asserted here.
- **No backend layer** - this story adds no endpoint, no repository, no migration, no domain
  function. There is **no integration test** and **no dual-engine concern** (the data the
  page reads is produced by US-3.3, already proven dual-engine). If the lane finds itself
  editing any `backend/` file, a migration, or an API client beyond the additive `Plant`
  type, that is a scope deviation to halt and flag (PRIN-IV / SPEC-001).
- **Acceptance (Playwright, TEST-009): BUILT this story** as the **live production-path
  smoke** that is the project's standing pattern (per the app-settings / care-timeline
  precedent: a built SPA served through the real backend, driven via the browser, zero
  console errors, committed breakpoint screenshots - NOT a committed-in-CI `.spec.ts`,
  which is a known systemic gap, debt #63, see §13 risk note). The journey seeds
  due/overdue/homeless plants, opens `/` on the built SPA, and asserts the grouped feed
  renders with correct overdue counts, a one-tap updates the card live, and zero console
  errors at 390 + 1280 (§8).

---

## 3. Input-state matrix M-CLS (the per-schedule classification, AC1/AC2/AC4) - TEST-007

`buildTodayGroups` classifies each schedule by crossing **3 dimensions**
({`next_due` relation to `today`: past, today, future, null} x {`overdue_days`: >0, ==0,
null} x {care_type: water, feed}) and well exceeds 6 logical cells, so it gets an explicit
matrix with a **named branch-priority order** matching the design pseudocode (design §"The
pure derivation"):

1. **Exclude** schedules where `next_due == null` (paused/dormant) - the FIRST filter,
   short-circuiting before any date comparison.
2. **Exclude** schedules where `next_due > today` (future, not yet due).
3. **Classify** the surviving schedules: `overdue_days > 0` -> **overdue**;
   `overdue_days == 0` (and `next_due == today`) -> **due-today**.
4. **Fan out** the surviving schedules per plant into `dueCareTypes` (one entry per due
   care type), compute `worstOverdue = max(overdue_days)`; a plant with zero surviving
   schedules produces **no card**.

`today` is injected; all `next_due` strings are built relative to it (no real clock).

| id | next_due vs today | overdue_days | care_type | classified as | in card? |
|---|---|---|---|---|---|
| `overdue-water` | `today - 3` | 3 | water | **overdue** (3 days) | yes - water in dueCareTypes, worstOverdue>=3 |
| `overdue-feed` | `today - 1` | 1 | feed | **overdue** (1 day) | yes - feed in dueCareTypes |
| `due-today-water` | `today` | 0 | water | **due-today** | yes - water in dueCareTypes |
| `due-today-feed` | `today` | 0 | feed | **due-today** | yes - feed in dueCareTypes |
| `future-water` | `today + 5` | 0 | water | **excluded** (future) | NO |
| `future-feed` | `today + 2` | 0 | feed | **excluded** (future) | NO |
| `paused-water` | `null` | `null` | water | **excluded** (paused/dormant - CRITICAL) | NO |
| `paused-feed` | `null` | `null` | feed | **excluded** (paused/dormant - CRITICAL) | NO |

The headline critical cells are `paused-water`/`paused-feed` (the null exclusion - a paused
plant the user silenced must NEVER surface) and `future-water`/`future-feed` (the
not-yet-due exclusion - the 5-second promise). `overdue-*` vs `due-today-*` pins the two
classifications and that the days-overdue count equals `overdue_days`.

### 3a. Plant-level fan-out cases (built on the per-schedule classification)

| id | plant's schedules | expected card |
|---|---|---|
| `both-due` | water `today-2` (od 2) + feed `today` (od 0) | ONE card, `dueCareTypes` == `[water, feed]` (drives the Both button), `worstOverdue == 2` (CRITICAL) |
| `water-only` | water `today-1` (od 1) + feed `today+3` (od 0, future) | ONE card, `dueCareTypes` == `[water]` only (the future feed excluded) |
| `feed-only` | water `null` (paused) + feed `today` (od 0) | ONE card, `dueCareTypes` == `[feed]` only (the paused water excluded) |
| `worst-overdue` | water `today-5` (od 5) + feed `today-1` (od 1) | ONE card, `worstOverdue == 5` (`max` across due schedules), both care types present |
| `nothing-due` | water `today+1` + feed `null` | **NO card** (the plant is absent entirely - CRITICAL: a plant with no due schedule does not appear) |
| `empty-input` | `plants == []` | `buildTodayGroups([], [], today)` -> `[]` (no groups) |

`both-due` is the critical fan-out cell (both care types -> the Both button); `worst-overdue`
pins `worstOverdue = max(overdue_days)`; `nothing-due` pins the plant-absent rule.

### 3b. Grouping + ordering matrix M-GRP (AC1, CRITICAL)

| id | setup | expected ordering |
|---|---|---|
| `group-by-location` | 2 plants in loc "Kitchen" (id 2), 1 in "Bath" (id 1), all due | three group memberships; "Bath" group + "Kitchen" group, each carrying its plants |
| `homeless-group` | a due plant with `location_id == null` + a due plant in a named location | a "No location" group holds the homeless plant; the named-location group holds the other |
| `group-order-by-name` | due plants in "Zen room", "Atrium", "Kitchen" (no homeless) | groups ordered `[Atrium, Kitchen, Zen room]` (by location name asc) |
| `homeless-last` | due plants in "Atrium" + a homeless plant | groups ordered `[Atrium, "No location"]` - the homeless group is **LAST regardless of name** (CRITICAL) |
| `within-group-most-overdue-first` | one location with plant A (worstOverdue 1) + plant B (worstOverdue 4) | within the group, ordered `[B (4), A (1)]` - `worstOverdue` desc |
| `within-group-name-tiebreak` | one location, plant "Yarrow" + plant "Aloe", both worstOverdue 2 | within the group, ordered `[Aloe, Yarrow]` - name asc when `worstOverdue` ties |

`homeless-last` is the critical ordering cell (the "No location" group sorts after every
named group by rule, not by name); `within-group-most-overdue-first` + the name tiebreak
pin the two-level intra-group sort.

---

## 4. Unit: `buildTodayGroups.test.ts` (`vitest`, pure - the only unit slice)

The pure function against hand-built `Plant` + `Location` value objects. **No app, no DOM,
no fetch.** `today` is the third argument, injected explicitly (no `new Date()` inside the
test or the function under test - TEST-006). A `_plant(name, location_id, schedules)` +
`_schedule(care_type, next_due, overdue_days)` builder keeps the fixtures terse; `next_due`
strings are computed relative to a fixed `TODAY = "2026-06-15"` (e.g. `today-3` is
`"2026-06-12"`).

### 4a. Classification matrix (M-CLS, AC1/AC2/AC4)

| # | test | drives | asserts |
|---|---|---|---|
| U-1 | **classification + exclusion matrix** (parametrized over M-CLS rows) | each row of §3 M-CLS | overdue rows appear with their care type and `overdue_days`; due-today rows appear with `overdue_days == 0`; **future and paused (`next_due==null`) rows produce NO card** (CRITICAL: the excluded rows leave the plant absent) |

`U-1` is the `pytest.mark.parametrize` equivalent (vitest `it.each`) driven from the M-CLS
table - it pins every classification cell cheaply (TEST-007).

### 4b. Plant-level fan-out (M-CLS §3a, AC2/AC3/AC4)

| # | test | setup | asserts |
|---|---|---|---|
| U-2 | **both-due yields both care types** (CRITICAL) | the `both-due` plant (water od 2 + feed od 0) | the card's `dueCareTypes` contains BOTH `water` and `feed` (the Both-button driver); `worstOverdue == 2` |
| U-3 | water-only excludes the future feed | the `water-only` plant | `dueCareTypes == [water]` only; the future feed is absent |
| U-4 | feed-only excludes the paused water | the `feed-only` plant | `dueCareTypes == [feed]` only; the paused water is absent |
| U-5 | `worstOverdue == max(overdue_days)` | the `worst-overdue` plant (od 5 + od 1) | `worstOverdue == 5`; both care types present |
| U-6 | **a plant with no due schedule is absent** (CRITICAL) | the `nothing-due` plant (future water + paused feed) | the plant produces NO card; it appears in NO group |
| U-7 | **empty input -> no groups** | `buildTodayGroups([], [], TODAY)` | returns `[]` (not null, no phantom groups) |

### 4c. Grouping + ordering (M-GRP §3b, AC1, CRITICAL)

| # | test | setup | asserts |
|---|---|---|---|
| U-8 | group by location + the homeless "No location" group | the `homeless-group` setup | one group per distinct `location_id`; the `null`-location plant is in a group labelled "No location"; each group carries its own plants |
| U-9 | **groups order by location name, homeless LAST** (CRITICAL) | the `homeless-last` setup (Atrium + homeless) plus a `group-order-by-name` variant (Zen/Atrium/Kitchen) | named groups in name-asc order (`Atrium, Kitchen, Zen room`); the "No location" group is **last regardless of its label's alphabetical position** |
| U-10 | within-group most-overdue-first then name | the `within-group-most-overdue-first` + `within-group-name-tiebreak` setups | within a group, cards ordered by `worstOverdue` desc; ties broken by plant name asc |
| U-11 | location-name resolution from `locations` | a plant in `location_id == 7`; `locations` carries `{id:7, name:"Greenhouse"}` | the group's display name is "Greenhouse" (resolved from the `locations` list, not the raw id); a plant whose `location_id` has no matching location row falls into "No location" (defensive - the re-audit checks the lane's documented choice; default: treat an unresolved id as homeless) |

`U-9` is the critical ordering proof; `U-11` pins the name resolution + the
unresolved-id fallback (a defensive edge the design implies via "resolve names from
locations").

---

## 5. (No backend / dual-engine / migration layer)

This story is frontend-only. There is **no** backend integration test, **no** cross-engine
test, **no** migration test, **no** new API client beyond the additive `Plant.schedules`
type. The due data the page consumes (`next_due`/`overdue_days`) is produced and proven by
US-3.3 (`due-computation`) and wired by US-3.5 (`app-settings`); this story neither
re-implements nor re-tests that derivation - it consumes the values faithfully. A lane that
finds itself touching `backend/`, a migration, or `compute_due` is in a scope deviation
(PRIN-IV / SPEC-001) and halts.

---

## 6. Component (vitest + RTL): `TodayPage` + `TodayCard`

Mirror `QuickCareActions.test.tsx` / `careEvents.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson(status, body)` / `fail(status)` helpers, `afterEach(unstubAllGlobals +
restoreAllMocks)`. **fetch is the mock boundary** (TEST-003 FE equivalent) - the page calls
the real `fetchPlants` / `fetchLocations` / `createEvent` clients, which hit the stubbed
`fetch`. A `SAMPLE_PLANTS` + `SAMPLE_LOCATIONS` fixture carries: an overdue plant, a
due-today plant, a both-due plant, a homeless plant, and a not-due plant (to prove it is
filtered out at render). An independent `localToday()` oracle (mirroring
`QuickCareActions.test.tsx`) computes the expected `happened_on`. Affordances are driven via
accessible names / labels / roles (FE-011 / FE-014).

### 6a. `TodayPage.test.tsx` (page render + states)

| # | test | asserts |
|---|---|---|
| C-1 | **renders groups with location headers** | mount with `SAMPLE_PLANTS` + `SAMPLE_LOCATIONS` (a single `GET /plants` + `GET /locations` fired) -> a section/heading per location group renders with the resolved location name; the homeless group renders under a "No location" header; the not-due plant in the fixture renders in NO group |
| C-2 | **overdue entry shows the distinct style + "N days overdue" matching `overdue_days`** | the overdue plant (`overdue_days == 3`) renders an overdue marker (warning glyph / distinct class - not colour-only, FE-011) AND the text "3 days overdue" (the count equals `overdue_days`, not a hardcoded number); a `overdue_days == 1` plant reads "1 day overdue" (singular) |
| C-3 | **due-today entry shows the neutral badge** | the due-today plant renders a neutral "due today" badge, visually distinct from the overdue marker (a different label/marker, not merely a different hue - FE-011) |
| C-4 | **empty-state renders when nothing is due** | mount with the plants stub returning a list whose schedules are all future/paused (or `[]`) -> the friendly empty-state panel renders ("Nothing due ..."), no group headers, no cards, no perpetual spinner |
| C-5 | **loading state** | mount with the fetch never resolving (a pending promise) -> a loading affordance renders (not a crash, not the empty-state); resolves to content once the promise settles |
| C-6 | **load error degrades gracefully** | mount with the `GET /plants` (or `/locations`) stub rejecting (ApiError) -> an inline error/empty-ish state renders; the page does not throw |
| C-7 | render order matches `buildTodayGroups` | mount with a fixture spanning two locations + homeless -> the DOM order of group sections and of cards within a group matches `buildTodayGroups`'s output order (the page does not re-sort; AC1) |

### 6b. `TodayCard.test.tsx` (the per-plant card + one-tap, CRITICAL)

| # | test | asserts |
|---|---|---|
| C-8 | **button set: Water iff water due, Feed iff feed due** | a card whose `dueCareTypes == [water]` renders a **Water** button and **no** Feed button and **no** Both button; a `[feed]`-only card renders **Feed** only; (pins the per-due-care-type button rule, §7) |
| C-9 | **Both button appears ONLY when both due** (CRITICAL) | a card whose `dueCareTypes == [water, feed]` renders Water, Feed, AND a **Both** button; a single-care-type card renders NO Both button (the Both button is present **iff** the due set is exactly {water, feed}) |
| C-10 | **tapping Water logs water for today** | tap the Water button -> a single `POST /api/v1/plants/{id}/events` with body `{type:"water", happened_on: localToday()}` (the one-tap quick-path body shape; no note/photo/health) |
| C-11 | **tapping Feed logs feed for today** | tap Feed -> a single `POST .../events` with `{type:"feed", happened_on: localToday()}` |
| C-12 | **tapping Both logs BOTH types for today** (CRITICAL) | tap Both -> `createEvent` called for `water` AND for `feed`, each with `happened_on: localToday()` (two events; Both = both types per proposal §"Both") |
| C-13 | **the card updates WITHOUT a full reload: the satisfied care type drops** (CRITICAL) | a both-due card; tap Water -> on success the Water button disappears (water satisfied) while the Feed button remains; the card stays in the list (feed still due); **no full-page navigation/reload occurs** (asserted via the satisfied type dropping in-place, the card still mounted - mirror `QuickCareActions` live-update) |
| C-14 | **the card LEAVES the list when nothing is left due** (CRITICAL) | a water-only card; tap Water -> on success the card is removed from the rendered list (the plant has nothing due left); no reload |
| C-15 | **a failed log surfaces inline, the card stays** | tap Water with the `createEvent` stub returning `fail(500)` -> an inline error is shown; the card and its buttons stay (the care type does NOT drop on failure); no crash, no navigation |
| C-16 | **buttons disabled in-flight** | tap Water with a pending (unresolved) `createEvent` -> the card's action buttons are disabled while the request is in flight (prevents a double-log); re-enabled (or removed) on settle |

`C-9`/`C-12`/`C-13`/`C-14` are the one-tap critical proofs: the Both button presence rule,
the Both = two-events call, and the two live-update directions (type drops in place vs card
leaves). `C-13`'s "no full reload" is asserted behaviourally (the card component instance
stays mounted and only the satisfied affordance disappears) - if the lane chose the
"refetch plants on success" implementation, the assertion still holds (the refetch is a
client call through the stubbed `fetch`, not a `window.location` reload); the re-audit
checks **no `window.location`/`reload` is invoked** and the update is observable in-place.

### 6c. fetch-mock contract fixtures (shared)

`SAMPLE_PLANTS` (overdue + due-today + both-due + homeless + not-due), `SAMPLE_LOCATIONS`,
the `okJson`/`fail` helpers and the `localToday()` oracle from `QuickCareActions.test.tsx`.
Component tests render the real `TodayPage` / `TodayCard` (RTL); buttons are driven via
their accessible names ("Water", "Feed", "Both" / `getByRole("button", {name})`),
group headers via heading role + name (FE-011 / FE-014). No real network.

---

## 7. Card model + button-set rule (pinned)

`buildTodayGroups(plants, locations, today)` returns an ordered list of groups; each group is
`{ locationName: string, cards: Card[] }` and each card is:

```
{ plant: Plant,
  dueCareTypes: { care_type: "water"|"feed", overdue_days: number, next_due: string }[],
  worstOverdue: number }   // = max(overdue_days) across dueCareTypes
```

- A schedule is in `dueCareTypes` **iff** `next_due != null` AND `next_due <= today`.
- `worstOverdue = max(d.overdue_days for d in dueCareTypes)` (0 when only due-today).
- A plant with empty `dueCareTypes` produces **no card**.
- Groups order: named locations by `locationName` asc, the "No location" group **last**.
- Cards within a group: `worstOverdue` desc, then `plant.name` asc.

**Button-set rule (pinned, the `TodayCard` contract):**

| due set (`dueCareTypes` care types) | buttons rendered |
|---|---|
| `{water}` | **Water** only |
| `{feed}` | **Feed** only |
| `{water, feed}` | **Water**, **Feed**, **and Both** |

The **Both** button is present **iff** the due set is exactly `{water, feed}`. Each
per-care-type button taps to `createEvent(plant.id, {type, happened_on: today})`; **Both**
taps to a `createEvent` for `water` AND a `createEvent` for `feed` (two independent events -
the feeding-mode coupling is deferred to #66, proposal §Deferred; no coupling logic this
story). On success the satisfied care type(s) drop and the card re-derives; the card leaves
the list when `dueCareTypes` becomes empty. No full page reload.

The exact `today` value passed to `createEvent` is the local calendar date (`todayIsoDate()`
from `careEvents.ts`, the existing helper that uses local not UTC time so a late tap never
logs tomorrow); the component tests assert against the independent `localToday()` oracle.

---

## 8. Acceptance (Playwright, TEST-009 - BUILT as the live production-path smoke) - TEST-010

The Today view is real UI in scope, so the acceptance check is **performed this story** as
the project's standing pattern (per the app-settings / care-timeline precedent, worklog §13
note): a **live production-path smoke** against the **built SPA served through the real
backend** (NOT the Vite dev server) - the same artifact users get (TEST-010 production-path
discipline). The driver uses **real UI affordances only** - never inject values directly. If
a committed `.spec.ts` + POM (`today.po.ts`, FE-013/FE-014) is stood up, it follows the
locator priority; absent the CI harness (see §13 risk, debt #63), the smoke is driven via
the browser tool and evidenced by the committed screenshots below.

| # | test | journey | asserts |
|---|---|---|---|
| A-1 | **Today renders grouped with correct overdue counts, zero console errors** | seed (via the real plants/locations/events/schedules endpoints) a mix: a plant overdue on water (a known N days), a plant due-today on feed, a both-due plant, a homeless due plant, and a not-due plant; build the SPA, serve it through the backend, navigate to `/` | the view renders grouped by location with a "No location" group present; the overdue plant shows "N days overdue" with **N matching the seeded `overdue_days`**; the due-today plant shows the neutral due badge; the not-due plant is ABSENT; the empty-state does NOT show. **Zero page errors / error-level console output** across load + render (TEST-010; warnings ignored) |
| A-2 | **one-tap logs and updates the card live** | on `/` with the both-due plant rendered, tap its **Water** button | the Water button disappears (water satisfied) while Feed remains, **without a full page reload**; a follow-up reload of `/` confirms the water event persisted (the schedule is no longer water-due); zero console errors across the tap + the confirm reload |
| A-3 | **empty-state on the production path** | open `/` for a database whose due/overdue set is empty (no plant has a due/overdue schedule) | the friendly empty-state renders (no crash, no spinner-forever, no group headers); zero console errors |

**Breakpoints:** A-1 runs at **both locked breakpoints** - phone **390 px** and desktop
**1280 px** (the two that bracket the responsive range; the precedent set carries
390/820/1280). The journey + assertions are identical at each width; no horizontal scroll at
390 (FE-011); the layout is phone-first single-column at 390 (proposal §Frontend).

**FE-012 design-review screenshots (committed, required evidence).** Captured at the locked
breakpoints and committed to `specs/changes/today-view/screenshots/` (the folder exists,
currently a `.gitkeep`). Enumerated required files:

- `today-phone-390.png` - the Today view at 390 px (a populated grouped feed: an overdue
  card with "N days overdue", a due-today card, a both-due card with Water/Feed/Both, and
  the "No location" group).
- `today-desktop-1280.png` - the Today view at 1280 px (the same populated feed).
- `today-empty-390.png` - the empty-state at 390 px (nothing due).

These are FE-012 design-review evidence (deliberate, curated, committed) - distinct from
TEST-011 failure-capture screenshots (ephemeral, never committed).

### 8a. FE-015 Audit Spaces (per-story mandatory)

US-4.1 ships UI, so the two Audit Spaces are asserted (no opt-out justification in the
proposal):

| # | test | asserts |
|---|---|---|
| A-4 | **a11y space** - axe-core scan + FE-011 | an axe-core scan of `/` (with a populated grouped feed AND the empty-state) reports no violations; every action button has an accessible name ("Water"/"Feed"/"Both"); the overdue vs due-today distinction is NOT colour-only (FE-011 - distinguishable by glyph/label, not hue alone); group headers are real headings; tap targets >=44x44 px; no horizontal scroll at 390 px |
| A-5 | **perf-budget space** - FE-007 | the production bundle-size budget holds (the FE-007 CI/test assertion); replacing the placeholder `TodayPage` + adding `TodayCard` + `buildTodayGroups` must not regress past the budget |

A-5 is the existing repo-wide budget assertion (the Today view replaces an existing
placeholder route + adds a thin card + a pure helper); the re-audit checks it is enforced as
a **test/CI assertion**, not merely a build warning (FE-015). A-4's colour-not-only check is
the a11y teeth of the "overdue distinct from due-today" requirement (C-2/C-3 prove the
distinction; A-4 proves it is accessible).

---

## 9. AC traceability (TEST-015) - every AC -> ≥1 named case

| AC | scenario | covering cases |
|---|---|---|
| **AC1** | due + overdue grouped by location; homeless its own group; stable group order; most-overdue-first within a group | `U-8` (group + homeless), `U-9` (group order, homeless last), `U-10` (within-group sort), `U-11` (name resolution); `C-1` (group headers render), `C-7` (render order matches derivation); `A-1` (production path grouped) |
| **AC2** | overdue visually distinct + correct days-overdue (matches `overdue_days`); due-today neutral badge; most-overdue first | `U-1` (classification: overdue vs due-today + the count), `U-5` (worstOverdue=max); `C-2` ("N days overdue" == `overdue_days`, distinct + not colour-only), `C-3` (neutral due-today badge); `A-1` (count matches seeded overdue_days) |
| **AC3** | one-tap button per due care type; Both only when both due; tap logs for today + card updates without reload (type drops; card leaves when nothing due) | `U-2` (both-due -> both care types); `C-8` (per-type button), `C-9` (Both iff both), `C-10`/`C-11`/`C-12` (tap logs water/feed/both for today), `C-13` (type drops, no reload), `C-14` (card leaves), `C-15` (failed log inline), `C-16` (disabled in-flight); `A-2` (production-path live update) |
| **AC4** | paused (`next_due==null`) + future (`next_due>today`) excluded; archived absent (API already excludes) | `U-1` (matrix: future + paused rows produce NO card), `U-3` (water-only excludes future feed), `U-4` (feed-only excludes paused water), `U-6` (no-due plant absent); `C-1` (not-due plant absent in render); `A-1` (not-due plant absent). *(Archived exclusion is the API's job - US-2.4 - not re-tested here; the re-audit notes it is upstream.)* |
| **AC5** | empty state renders when nothing is due | `U-7` (empty input -> `[]`); `C-4` (empty-state render); `A-3` (production-path empty-state) |
| **AC6** | verified on the production path (built SPA through the backend), phone + desktop, zero console errors; screenshots committed (FE-012) | `A-1` (production path, zero console errors, both breakpoints), `A-2` (one-tap live), `A-3` (empty-state), `A-4` (a11y), `A-5` (perf); FE-012 screenshots (§8) |

No AC is uncovered. Every numbered case maps to an AC, pins the card model + button-set rule
(§7: `C-8`/`C-9`), or the classification/ordering matrices (§3: `U-1`/`U-9`).

---

## 10. Critical-100% paths (QG-002 - spec-flagged -> 100% required)

The four paths flagged in the header; mutation evidence outranks assertion-reading at
story-complete (§11):

1. **Attention-set classification incl. null/future exclusion** (AC1/AC4) - `U-1` (the M-CLS
   matrix: paused + future rows produce no card), `U-3`/`U-4`/`U-6`; `C-1` (not-due absent).
2. **Both-due -> both care types** (AC3) - `U-2` (the fan-out), `C-9` (Both button iff both),
   `C-12` (Both = two events).
3. **Group / homeless ordering** (AC1) - `U-9` (homeless last, name-asc), `U-8`, `U-10`.
4. **One-tap updates without reload** (AC3) - `C-13` (type drops in place, no reload),
   `C-14` (card leaves when nothing due), `C-10`/`C-11`/`C-12` (the call shape).

These four MUST hit 100% (branch + line on the relevant code); the rest clears the QG-002
floors (§12).

---

## 11. Mutation probes (story-complete re-audit) - sanctioned, restored byte-identically

At story-complete, the test-engineer runs sanctioned mutation probes on the four
critical-100% paths (§10), logging each (file, mutation, failing test), restoring
byte-identically, and verifying `git status` clean. The orchestrator independently verifies
the clean tree. Mutation evidence outranks assertion-reading on these paths.

| critical path | file (lane finalizes the exact path) | mutation | test that MUST go red |
|---|---|---|---|
| 1. null exclusion | `frontend/src/features/today/buildTodayGroups.ts` | drop the `next_due != null` filter (let paused schedules through, treating null as due) | `U-1` (the `paused-*` rows would produce a card) + `C-1` |
| 1b. future exclusion | `buildTodayGroups.ts` | change the `next_due <= today` filter to `>= today` (or remove it) | `U-1` (the `future-*` rows would appear) + `U-3` |
| 1c. plant-absent rule | `buildTodayGroups.ts` | emit a card even when `dueCareTypes` is empty | `U-6` (the `nothing-due` plant would appear) + `C-1` |
| 2. both-due fan-out | `buildTodayGroups.ts` | collapse `dueCareTypes` to the first due schedule only (drop the second care type) | `U-2` (only one care type) + `C-9` (no Both button rendered) |
| 2b. worstOverdue | `buildTodayGroups.ts` | use `min` instead of `max` for `worstOverdue` | `U-5` (would be 1 not 5) + `U-10` (within-group order flips) |
| 3. homeless ordering | `buildTodayGroups.ts` | sort the homeless group by name with the others (drop the "homeless last" rule) | `U-9` (the "No location" group would not be last) |
| 3b. group name sort | `buildTodayGroups.ts` | drop the location-name sort (insertion order) | `U-9` (`group-order-by-name` would fail) |
| 4. type-drops-on-tap | `frontend/src/features/today/TodayCard.tsx` | on a successful tap, do NOT drop the satisfied care type (leave both buttons) | `C-13` (the Water button would not disappear) + `C-14` |
| 4b. Both = two events | `TodayCard.tsx` | make Both call `createEvent` once (water only) | `C-12` (feed event would not fire) |
| 4c. button-set rule | `TodayCard.tsx` | render a Both button even for a single-care-type card | `C-9` (the single-type card would show a Both button) |

The exact file paths (`buildTodayGroups.ts` as a standalone module vs inlined in `TodayPage`,
`TodayCard.tsx`) are the lane's to finalize (the design names a pure `buildTodayGroups` +
`TodayCard`); the re-audit locates the implemented file and probes the named behaviour. If
`buildTodayGroups` is inlined into `TodayPage`, the §4 unit cases fold into component tests
that call the page with a stub feed - the re-audit accepts either, checking the **behaviour**
(classification, fan-out, ordering) is pinned somewhere, but **strongly prefers** the pure
extraction (design §"The pure derivation" - keeping it pure makes the logic exhaustively
testable without the DOM or a clock).

---

## 12. Required test markers + file-size (TEST-012, QG-009)

- Frontend `*.test.ts(x)` run under **vitest** (no pytest marker required - TEST-012 applies
  the `pytestmark` rule to Python only; the FE suite is layered by file location +
  description). The unit slice (`buildTodayGroups.test.ts`) is a pure-logic test; the
  component slices (`TodayPage.test.tsx`, `TodayCard.test.tsx`) are RTL.
- The acceptance smoke runs on the production path (TEST-009/010); no committed CI `.spec.ts`
  exists (debt #63) - the smoke is the live browser run + the committed screenshots (§8).
- **No Python test file** is added or edited (frontend-only story); **no `pytestmark`**
  concern; **no migration test**, **no `test_fk_cross_engine.py`** edit (§5).
- File-size: keep each test file under the QG-009 **500-LOC hard max**; if
  `TodayCard.test.tsx` grows past it, split by group (button-set / one-tap call / live-update
  / error+disable). **No edit to the plants/locations/events client tests** beyond what the
  additive `Plant.schedules` type forces (their existing behaviour is unchanged, PRIN-IX).

---

## 13. TEST-014 - Test-first evidence (the red)

The single FE lane records in `worklog.md` the **failing run that precedes the
implementation** - the test names plus the failing assertion/error output (the "red") -
before the green commit:

- **FE lane red:** run `buildTodayGroups.test.ts` + `TodayPage.test.tsx` +
  `TodayCard.test.tsx` against the *unimplemented* `features/today/buildTodayGroups.ts` /
  the still-placeholder `TodayPage.tsx` / the not-yet-existing `TodayCard.tsx` (and the
  not-yet-added `Plant.schedules` / `ScheduleDue` type) -> expect module-not-found /
  type / assertion failures. Capture the names + the first failing line per group.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain.

**Build-pickup risks (carry into the build session):**
1. **No committed-in-CI e2e harness exists** (project-wide systemic gap, debt #63, flagged
   in the app-settings + care-timeline worklogs). The acceptance lane (§8) follows the
   standing pattern: a LIVE production-path browser smoke + committed breakpoint screenshots,
   NOT a `.spec.ts` running in CI. If the build agent tries to "run the Playwright spec",
   there isn't one - perform the live smoke and commit screenshots, exactly as plant-crud /
   care-events / app-settings / care-timeline did. (Standing up a CI e2e harness is out of
   THIS story's scope - it is debt #63.)
2. **`schedules` must be on the wire.** The proposal asserts `GET /api/v1/plants` already
   returns per-schedule `next_due`/`overdue_days`/`care_type` (US-3.3, N+1-safe). The build
   agent MUST confirm the live response actually carries `schedules` at pickup (a quick curl
   against the running backend); if it does NOT (a contract gap), the story is blocked on a
   backend change that is OUT of this story's scope - halt and flag (PRIN-IV). The
   acceptance seed (`A-1`) is the natural place this surfaces.
3. **`care_type` vocab vs `CareEventType`.** Schedules carry `water|feed`; the events API
   carries `water|feed|repot|observe`. The one-tap maps the schedule `care_type` to the
   event `type` (identity for water/feed). Do NOT widen `ScheduleDue.care_type` to the
   four-member enum (§1 note).
4. **`buildTodayGroups` purity.** Keep it pure with `today` injected (no `new Date()`
   inside). The §4 unit cases depend on it - a clock read inside the function makes them
   flaky and breaks TEST-006. The page passes `todayIsoDate()` (local date) at the call site.
5. **Feeding-mode #66 is deferred.** Both = two independent events. No coupling logic this
   story (proposal §Deferred); a build agent that "helpfully" couples water+feed is a scope
   extra (PRIN-IV).

---

## 14. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; the FE suite must not drop the floor. New/changed code
  **>=80% diff-cover**.
- **`buildTodayGroups` (the pure logic):** branch coverage **>=95%** - every classification
  fork (null / future / overdue / due-today), the both-due fan-out, the homeless-group
  branch, the two-level sort, the name-resolution fallback all exercised by §4.
- **`TodayPage` / `TodayCard`:** the render branches (loading / error / empty / populated),
  the button-set branches (water-only / feed-only / both), and the live-update branches (type
  drops / card leaves / error keeps) exercised by §6.
- **Critical paths flagged 100%** (§10 -> QG-002 100% required): the attention-set
  classification incl. null/future exclusion, the both-due fan-out, the group/homeless
  ordering, and the one-tap-updates-without-reload. Mutation evidence outranks
  assertion-reading at story-complete (§11).
- The combined vitest run scores the union (TEST-001); the pure-logic unit slice + the
  component slices clear the floor without brittle implementation-mirroring tests (TEST-004).

---

## 15. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this foundation
and issues the **test-foundation approval**, checking:

- Every surface in §1 has its happy + sad (TEST-005); matrices M-CLS (§3) and M-GRP (§3b)
  are present and **parametrized** with the named cells (TEST-007), in `buildTodayGroups.test.ts`.
- The four **critical-100%** paths (§10) are exercised, and each survives a **sanctioned
  mutation probe** (§11: the null/future filter drop, the both-due collapse, the
  homeless-ordering drop, the type-drops-on-tap removal) - each probe logged (file, mutation,
  failing test) and the tree restored byte-identically, `git status` clean.
- The attention-set classification holds: paused (`next_due==null`) and future
  (`next_due>today`) schedules produce NO card; a plant with no due schedule is absent
  (`U-1`/`U-3`/`U-4`/`U-6`).
- A both-due plant yields BOTH care types (`U-2`) -> the card renders a **Both** button only
  when both are due (`C-9`), and Both logs two events for today (`C-12`).
- The group/homeless ordering is correct: groups by location name, the "No location" group
  last, within-group most-overdue-first then name (`U-8`/`U-9`/`U-10`).
- The one-tap updates the card WITHOUT a full reload: the satisfied care type drops in place
  (`C-13`), the card leaves when nothing is left due (`C-14`), a failed log surfaces inline
  and keeps the card (`C-15`), buttons disable in-flight (`C-16`); the call shape is
  `{type, happened_on: today}` (`C-10`/`C-11`/`C-12`).
- The overdue entry shows "N days overdue" with N == `overdue_days` and a not-colour-only
  distinction from the neutral due-today badge (`C-2`/`C-3`, A-4).
- The acceptance smoke ran on the **production path** (built SPA through the backend) with
  **zero console errors** at **both breakpoints** (`A-1`/`A-2`/`A-3`, TEST-009/010); the
  overdue counts matched the seeded `overdue_days` (`A-1`); the one-tap updated live (`A-2`);
  FE-012 screenshots committed (§8); the FE-015 a11y + perf spaces asserted (`A-4`/`A-5`).
- **No backend file** edited, **no migration**, **no new API client** beyond the additive
  `Plant.schedules` / `ScheduleDue` type; the feeding-mode coupling (#66) is NOT implemented
  (scope, PRIN-IV / SPEC-001).
- `buildTodayGroups` is **pure** with `today` injected (no real-clock dependence); the suite
  is parallel-safe (TEST-006) with stubbed fetch + explicit dates.
- Every AC1-AC6 maps to a named implemented test (§9, TEST-015); the TEST-014 red is recorded
  (§13).

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
