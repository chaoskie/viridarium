---
title: Test Foundation - plant-detail (US-4.3)
type: test-foundation
change: plant-detail
status: authored
date: 2026-07-06
---

# Test Foundation - plant-detail (US-4.3)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for the
**expanded plant detail page**: the US-3.4 minimal `/plants/{id}` route (header + back
link + `CareTimeline`) grows into the full US-4.3 page - an omit-empty **attributes card**
(incl. cachepot), a **schedules card** with next-due/overdue/paused states, an inline
**gallery** (cover + thumbnail strip + "+N" overflow opening `PhotoGalleryModal`), and
**action wiring** to the already-built modals (`PlantFormModal`, `LogCareModal`/
`QuickCareActions`, `CareScheduleModal`, `DeletePlantDialog`, `PhotoGalleryModal`), with a
`reload()` refetch after every mutation and a delete-navigates-to-`/plants` behaviour.
Authored by `test-engineer` against `proposal.md` (PO-resolved gallery + actions
decisions, AC1-AC6, the one flagged residual assumption about the ~8-thumb "+N" count) and
`design.md` (the `usePlantDetail(plantId)` state machine + `reload()` as the mutation
callback, the thin-page component split, the reused-as-is modals).

**This is a frontend-only story. No backend delta, no API change (API-001: none), no
migration - `GET /api/v1/plants/{id}` already returns attributes, tags, `schedules[]`
(`next_due`/`overdue_days` per ARCH-007), `cover_photo_id`, and the cachepot fields.** No
backend tests are authored by this foundation; the backend contract is a fixed input.

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mock boundary). It contains **no test code**. Two lanes implement against it -
**frontend** (`frontend/`: the new cards + gallery + the expanded page + `usePlantDetail`)
and **acceptance** (the production-path Playwright/live smoke). Each lane records its
TEST-014 red in `worklog.md` before turning green. The story-complete pass re-audits the
implementation and issues the DoD §3 approval.

Cases are numbered so the lane can cite them and the re-audit can diff: `F-n` (frontend
component/hook/page, vitest + RTL) and `A-n` (acceptance / production path). The re-audit
checks every numbered case is present, meaningful (TEST-004), and on its assigned layer,
and maps every AC1-AC6 (§9).

**Critical paths for this story** (flagged 100% in §8; mutation evidence outranks
assertion-reading here, §11) - the four places a regression silently corrupts what the
page shows or does:

1. **The omit-empty attributes invariant** (AC1) - a field with no value is *omitted*, not
   rendered as an empty/`null`/"—" row. A regression that renders empty rows (or, worse,
   the literal `null`/`"null cm"`) lies about what is known and clutters the page; the
   cachepot pair (outer material + outer size) is the sharpest case (size shown only when
   material is set).
2. **The schedules next-due state machine** (AC2) - each `ScheduleDue` renders in exactly
   one of {due-with-date, overdue-emphasized, paused/dormant-reason}, keyed on `next_due`
   (null -> paused) and `overdue_days` (`> 0` -> overdue). A regression that shows a date
   for a paused schedule, drops the overdue emphasis, or renders "null" invents care state
   the user will act on wrongly. The **both-null invariant** (`overdue_days` null iff
   `next_due` null) must never surface as an overdue badge with no date.
3. **The mutation -> refetch contract** (AC4) - after edit/log/schedule/photo/delete the
   page calls `reload()` (refetches the plant) so schedules/next-due/cover stay fresh; a
   broken wiring leaves stale next-due or a stale cover after the user just changed it.
4. **Delete navigates to `/plants`** (AC4) - a successful delete leaves the detail route
   (no orphaned view of a deleted plant). A regression that stays on `/plants/{id}` shows
   a 404/error shell for a plant that no longer exists.

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| S1 | `usePlantDetail(plantId)` hook (or the inline page state machine) | FE hook (loading/ready/error + `reload()`) | fetch resolves -> `ready` with the plant; `reload()` refetches and re-exposes fresh data | fetch rejects (`ApiError`) -> `error`; an invalid/non-positive id -> `error` without a network call |
| S2 | `PlantAttributesCard` | FE component (omit-empty) | a fully-populated plant renders every attribute row (species, acquired, pot inner + cachepot, light, notes, tags, location) | a plant with all-optional-null renders NO empty rows (the card is minimal or absent); a cachepot with material but null size shows material without a "(null cm)" |
| S3 | `PlantSchedulesCard` | FE component (state machine) | enabled water + feed schedules render with their next-due dates; an overdue one is emphasized; a paused (`next_due:null`) one states why | a plant with `schedules:[]` shows the empty-state linking to schedule setup (no crash, no blank card) |
| S4 | `PlantGallery` | FE component | cover photo prominent + a thumbnail strip; a strip over the cap shows a "+N" affordance; tapping cover/thumb/"+N" opens `PhotoGalleryModal` | a plant with no photos shows the gallery empty-state (no broken `<img>`, no modal auto-open) |
| S5 | `PlantDetailPage` action wiring | FE page (modal orchestration) | each action (edit, log-care, schedules, gallery, delete) opens its existing modal; a mutation triggers `reload()`; the timeline refresh-key bumps on care/photo mutations | a failed mutation surfaces the modal's own error and does NOT navigate/refetch-to-blank; closing a modal without mutating does not refetch spuriously |
| S6 | `PlantDetailPage` page states | FE page (route + state machine) | `/plants/:id` mounts the full page for a valid id; delete success navigates to `/plants` | loading state renders (no flash of "not found"); a fetch error renders an error/not-found shell; an invalid/absent id renders the existing not-found handling |
| A1 | `/plants/{id}` journey | acceptance (Playwright / live, production path) | open the built page -> header + attributes + schedules + gallery + timeline render; open a modal, mutate, see the page refresh; zero console errors at 390 + 1280 | (failure = any console error / a non-rendering section / a stale value after mutation; both breakpoints) |

The exact identifier names (`usePlantDetail`, `PlantAttributesCard`, `PlantSchedulesCard`,
`PlantGallery`) are the design's proposed split; the re-audit checks the **behaviour**, not
the file boundary - if the lane keeps a card inlined in the page it still must pin the
behaviour somewhere. The reused modals (`PlantFormModal`, `LogCareModal`/
`QuickCareActions`, `CareScheduleModal`, `DeletePlantDialog`, `PhotoGalleryModal`) are
**already tested** in their own suites; this story tests the **wiring** (they open, the
mutation callback refetches, delete navigates), NOT their internals (TEST-004: no
re-testing the shared component's form validation here).

**Modal-wiring note (design nuance the lane must resolve, not paper over).** The reused
modals do **not** all expose a uniform `onMutated` prop:
- `PlantFormModal` takes `onSubmit(input) => Promise<void>` + `onClose`.
- `DeletePlantDialog` takes `onConfirm(id) => Promise<void>` + `onClose`.
- `LogCareModal` takes `onLogged(event)` + `onClose`; `QuickCareActions` self-manages its
  own `LogCareModal` and does not surface the created event to a parent.
- `CareScheduleModal` and `PhotoGalleryModal` take only `onClose` - they self-manage their
  mutations via `useCareSchedules` / `usePhotos` internally and report nothing to a parent.

So the page's `reload()` cannot hang off a single `onMutated` for every modal. The design's
`reload()`-as-`onMutated` intent is satisfied by wiring `reload()` into the `onSubmit`/
`onConfirm` handlers the page owns (edit, delete) AND on the `onClose` of the
self-managing modals (schedules, gallery) - closing them is the only signal the page gets
that a mutation may have happened. `F-13`..`F-17` pin the required behaviour (a refetch
occurs after each action); the re-audit accepts whatever mechanism the lane chose so long
as the observable refetch happens (TEST-004). If a reused modal genuinely cannot signal a
mutation without modification, the lane STOPS and flags (PRIN-IX: do not modify the shared
modal; adapt the page).

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

This is a frontend story; the standard backend "integration is primary" applies to the
Python layers, which this story does not touch. The FE testing shape mirrors the existing
`features/plants/*.test.tsx` convention:

- **Component / hook tests (vitest + RTL) are the primary layer here** - each new card, the
  gallery, the `usePlantDetail` hook, and the page's modal-orchestration + state machine
  are rendered with the **real components** (RTL), routing via a **memory router**, and
  **`fetch` stubbed at the boundary** (`vi.stubGlobal`, the `okJson`/`fail` helpers already
  used across the suite - §6). This is where the omit-empty matrix, the schedules state
  machine, the gallery overflow, and the mutation-refetch wiring live. `fetch` is the ONLY
  mock (TEST-003 FE equivalent); no component or hook is mocked.
- **No unit-only slice is warranted** - there is no framework-free pure-logic island here
  (the schedule-state selection and the omit-empty decision are trivial rendering
  branches best asserted through the rendered component, TEST-001 (a) not met). IF the lane
  extracts a pure `scheduleState(due) -> "due"|"overdue"|"paused"` helper, a tiny unit
  slice is acceptable but not required; the re-audit checks the **behaviour** is pinned via
  the component render regardless.
- **Acceptance (Playwright, TEST-009): performed this story** as the **live production-path
  smoke** that is the project's standing pattern (per the care-timeline / app-settings
  precedent: a built SPA served through the real backend, driven via the browser, zero
  console errors, committed breakpoint screenshots - NOT a committed-in-CI `.spec.ts`,
  the known systemic gap, debt #63). The journey opens `/plants/{id}` on the built SPA and
  asserts every section renders, a mutation refreshes the page, and there are zero console
  errors at 390 + 1280 (§8).
- **No backend test, no migration, no repository change.** If the lane finds itself editing
  a backend test or a Python module, that is a scope deviation to halt and flag (PRIN-IV /
  SPEC-001).

---

## 3. Input-state matrix M-ATTR (omit-empty attributes card, AC1) - TEST-007

The attributes card crosses well over 6 logical cells (each of ~7 optional fields present
or absent, plus the cachepot pair's material/size interdependency), so it gets an explicit
matrix with a **named branch-priority order**. Priority order (render top-to-bottom, each
row omitted entirely when its value is null/empty):

1. **species** (string|null) - omit when null.
2. **location** (`location_id`/name) - omit when `location_id` is null (homeless).
3. **acquired** (`acquired_on`, ISO date|null) - omit when null.
4. **pot (inner)** - `pot_size_cm` + `pot_material`; omit the row when both null; render the
   parts that are set.
5. **cachepot (outer pot)** - `outer_pot_material` + `outer_pot_size_cm`; the material
   gates the row (size shown only alongside a material; size-without-material is NOT a row).
6. **light** (`light_level`|null) - omit when null.
7. **notes** (string|null) - omit when null/empty.
8. **tags** (`string[]`) - omit the tags block when the array is empty.

| id | scenario | expected in the attributes card |
|---|---|---|
| `attr-full` | every optional field set (species, location, acquired, inner pot size+material, outer pot material+size, light, notes, 2 tags) | every row renders with its value; the cachepot renders material + "(N cm)"; both tags render as chips |
| `attr-empty` | all optionals null / tags `[]` / homeless | NO attribute rows render (empty rows are the CRITICAL failure); the card is minimal or absent, never a list of blank/"null"/"—" rows |
| `attr-cachepot-material-only` | `outer_pot_material:"ceramic"`, `outer_pot_size_cm:null` | the cachepot renders "ceramic outer pot" WITHOUT a "(null cm)" / "(cm)" suffix (CRITICAL - mirrors the existing header test that asserts "in a ceramic outer pot" with the size only when set) |
| `attr-cachepot-full` | `outer_pot_material:"ceramic"`, `outer_pot_size_cm:18` | the cachepot renders material + "(18 cm)" |
| `attr-inner-pot-partial` | `pot_size_cm:14`, `pot_material:null` | the inner-pot row renders the size; no "null" material text |
| `attr-notes-only` | only `notes` set, everything else null | exactly one row (notes) renders; no other rows, no empty tags block |
| `attr-tags-empty` | `tags:[]`, some other field set | no tags block/heading renders (an empty tags heading with no chips is a fail) |
| `attr-single-tag` | `tags:["office"]` | one tag chip renders |

The headline critical cells are `attr-empty` (no empty rows at all) and
`attr-cachepot-material-only` (the size suffix is gated on the size, not the material).

---

## 4. Input-state matrix M-SCHED (schedules card, AC2) - TEST-007

Each `ScheduleDue` (`care_type: "water"|"feed"`, `next_due: string|null`,
`overdue_days: number|null`) renders in exactly one visual state, plus the card-level empty
state. The **both-null invariant** (`overdue_days` null iff `next_due` null) is a contract
guarantee (documented in `plants.ts`), so the matrix does not test the illegal
`next_due:null` + `overdue_days:5` cell as a valid input; instead `sched-invariant` asserts
the render never fabricates an overdue badge without a date. Priority order:

1. **`next_due === null`** -> **paused/dormant**: state the reason (paused inside the
   window), NO date, NO overdue emphasis.
2. **`next_due` set AND `overdue_days > 0`** -> **overdue**: the date with overdue emphasis
   (mirrors the Today view's overdue tokens).
3. **`next_due` set AND `overdue_days === 0`** -> **due today / on-schedule**: the date, no
   overdue emphasis.
4. **`schedules.length === 0`** -> the **empty-state** linking to schedule setup.

| id | schedules input | expected |
|---|---|---|
| `sched-due` | `[{water, next_due:"2026-07-10", overdue_days:0}]` | one row: water, its next-due date, no overdue emphasis |
| `sched-overdue` | `[{feed, next_due:"2026-07-01", overdue_days:5}]` | one row: feed, its date, overdue emphasis present (CRITICAL) + the overdue count/emphasis distinguishable NOT by color alone (FE-011) |
| `sched-paused` | `[{water, next_due:null, overdue_days:null}]` | one row: water, a paused/dormant reason, NO date rendered, NO overdue emphasis (CRITICAL) |
| `sched-both` | `[{water, next_due:"2026-07-10", overdue_days:0}, {feed, next_due:"2026-07-01", overdue_days:3}]` | two rows: water due, feed overdue-emphasized; both `care_type`s labelled distinctly |
| `sched-empty` | `[]` | the empty-state renders with a link/affordance to set up a schedule (CRITICAL - no blank card, no crash) |
| `sched-invariant` | `[{water, next_due:null, overdue_days:null}]` | the paused row shows neither a date NOR an overdue badge - the both-null pair never yields an overdue affordance without a date |

`sched-overdue` (emphasis present + not color-only) and `sched-paused` (no date, reason
shown) are the critical cells; `sched-empty` guards the empty-state link.

---

## 5. Input-state matrix M-GALLERY (gallery, AC3) - TEST-007

The gallery crosses {cover present/absent} x {thumb count: 0 / 1..cap / over cap} and the
open-modal action. The thumbnail cap is the proposal's **residual assumption** (~8 thumbs +
a "+N" overflow); the exact cap is a build-time layout call. The matrix pins the
*behaviour* (a cover, a bounded strip, a "+N" affordance when over the cap, the modal opens
on tap); the re-audit checks the confirmed cap value the worklog records.

| id | photos / cover input | expected |
|---|---|---|
| `gal-cover-thumbs` | cover set + several (< cap) photos | the cover renders prominently (its `url`); a thumbnail strip renders one thumb per remaining photo; no "+N" |
| `gal-overflow` | more photos than the cap | the strip renders exactly `cap` thumbs and a "+N" affordance where N = (total - shown) (CRITICAL: the count is correct, not off-by-one); tapping "+N" opens `PhotoGalleryModal` |
| `gal-cover-only` | cover set, no other photos | the cover renders; the strip is empty or absent; no "+N"; no broken thumbs |
| `gal-no-cover-has-photos` | `cover_photo_id:null` but photos exist | the gallery still renders the available photos (a fallback prominent image or the first photo); tapping opens the modal |
| `gal-empty` | no photos at all (`cover_photo_id:null`, `usePhotos` -> `[]`) | the gallery empty-state renders (mirrors `CoverThumb`'s "No photo" placeholder convention); NO broken `<img>`, NO `PhotoGalleryModal` auto-opening |
| `gal-open-modal` | cover + thumbs; user taps the cover (and separately a thumb) | `PhotoGalleryModal` opens (its title `Photos - {name}` / the modal role appears); the page did not navigate away |

`gal-overflow` (the "+N" count correctness + open) and `gal-empty` (no broken image / no
auto-open) are the critical cells. The gallery sources photos from the existing
`usePhotos(plantId)` hook (design §data-flow); `fetch` is stubbed to return the photo list
(§6). Cover-photo URL recipe is the existing `/api/v1/plants/{id}/photos/{photoId}`
(`CoverThumb` convention).

---

## 6. Frontend (vitest + RTL) - named cases

Mirror `PlantDetailPage.test.tsx` / `PhotoGalleryModal.test.tsx` / `useCareSchedules.test.ts`:
stub `fetch` via `vi.stubGlobal`, `okJson(status, body)` / `fail(status)` helpers,
`afterEach(unstubAllGlobals + restoreAllMocks)`, route via `MemoryRouter`. A `stubByPath`
helper routes the plant GET vs `/timeline` vs `/photos` (the existing page test already
does this). Shared fixtures: a `PLANT_FULL` (every optional set incl. cachepot + tags +
schedules), a `PLANT_EMPTY` (all-null, `schedules:[]`), and a `PHOTOS` list long enough to
exceed the thumb cap.

### 6a. `usePlantDetail` hook (S1)

| # | test | asserts |
|---|---|---|
| F-1 | resolves to ready with the plant (happy) | mount -> `loading` false, exposes the fetched plant, `error` null |
| F-2 | rejects to error (sad) | the plant GET rejects (`ApiError`) -> `error` state; no crash |
| F-3 | invalid/non-positive id -> error, no fetch | id `0`/`NaN`/negative -> `error` immediately; `fetch` not called for the plant |
| F-4 | `reload()` refetches and re-exposes fresh data | after a successful mount, calling `reload()` fires a second plant GET and surfaces the updated plant (e.g. a changed `cover_photo_id`/next-due) |

### 6b. `PlantAttributesCard` (S2, matrix M-ATTR §3)

Parametrized from M-ATTR (TEST-007). At minimum the named cells:

| # | test | asserts |
|---|---|---|
| F-5 | `attr-full` renders every attribute row | all rows present with their values; cachepot material + "(N cm)"; both tag chips |
| F-6 | **`attr-empty` renders NO empty rows** (CRITICAL) | mount with `PLANT_EMPTY` -> none of the attribute rows render; no literal "null"/"—"/"(cm)"; the tags block is absent |
| F-7 | **`attr-cachepot-material-only`** (CRITICAL) | outer material set + null size -> the cachepot text has no "(null cm)"/"(cm)" suffix (mirrors the existing header assertion) |
| F-8 | `attr-cachepot-full` + `attr-inner-pot-partial` | cachepot shows "(18 cm)"; inner pot shows size with no "null" material |
| F-9 | `attr-tags-empty` / `attr-single-tag` | empty tags -> no tags heading; one tag -> one chip |

### 6c. `PlantSchedulesCard` (S3, matrix M-SCHED §4)

Parametrized from M-SCHED. At minimum:

| # | test | asserts |
|---|---|---|
| F-10 | `sched-due` + `sched-both` render dates, distinct care types | each enabled schedule row shows its `care_type` label + next-due date |
| F-11 | **`sched-overdue` emphasized, not color-only** (CRITICAL) | overdue schedule carries the overdue emphasis distinguishable by label/icon/text, not hue alone (FE-011) |
| F-12 | **`sched-paused` shows reason, no date, no overdue** (CRITICAL) | `next_due:null` -> a paused/dormant reason, no date, no overdue badge (the both-null invariant, `sched-invariant`) |
| F-12b | **`sched-empty` renders the setup link** (CRITICAL) | `schedules:[]` -> an empty-state with an affordance to set up a schedule (opens `CareScheduleModal` or links to it) |

### 6d. `PlantGallery` (S4, matrix M-GALLERY §5)

| # | test | asserts |
|---|---|---|
| F-13a | `gal-cover-thumbs` renders cover + strip | cover `<img>` with its url; one thumb per remaining photo; no "+N" |
| F-13b | **`gal-overflow` shows a correct "+N" that opens the modal** (CRITICAL) | over-cap list -> exactly `cap` thumbs + a "+N" affordance (N correct); tapping "+N" opens `PhotoGalleryModal` |
| F-13c | **`gal-empty` renders the empty-state, no auto-open** (CRITICAL) | no photos -> the gallery empty-state; no broken `<img>`; `PhotoGalleryModal` is NOT auto-rendered |
| F-13d | `gal-open-modal` tap opens the gallery modal | tapping the cover (and a thumb) opens `PhotoGalleryModal` (its title/modal role appears); no navigation |

### 6e. `PlantDetailPage` action wiring + refetch (S5, critical path #3/#4)

| # | test | asserts |
|---|---|---|
| F-14 | **each action opens its modal** | the header exposes edit / log-care / schedules / gallery / delete affordances (accessible names, FE-011); activating each opens the corresponding modal (`PlantFormModal` "Edit plant", `LogCareModal`/`QuickCareActions`, `CareScheduleModal` "Schedules - {name}", `PhotoGalleryModal` "Photos - {name}", `DeletePlantDialog` "Delete plant") |
| F-15 | **edit mutation triggers a plant refetch** (CRITICAL #3) | open edit, submit a valid update -> `updatePlant` PUT fires, THEN the plant GET is re-issued (`reload()`); the header/attributes reflect the new value (stub the second GET with the updated plant) |
| F-16 | **schedule/photo mutation refetches on close** (CRITICAL #3) | after `CareScheduleModal` (or `PhotoGalleryModal`) closes following a mutation, the page re-issues the plant GET so next-due/cover are fresh; the `CareTimeline` refresh-key bumps on a care/photo mutation |
| F-17 | **delete navigates to `/plants`** (CRITICAL #4) | open delete, confirm -> `deletePlant` DELETE fires and the router navigates to `/plants` (the list landing renders); the detail view is gone |
| F-18 | closing a modal without mutating does NOT refetch spuriously (sad) | open then cancel edit -> no extra plant GET beyond the mount; no navigation |
| F-19 | a failed mutation keeps the page (sad) | a delete/update that rejects -> the modal surfaces its own error, the page does NOT navigate to `/plants` and does NOT blank out |

### 6f. `PlantDetailPage` page states (S6)

| # | test | asserts |
|---|---|---|
| F-20 | valid id mounts the FULL page | render at `/plants/3` -> header + attributes card + schedules card + gallery + `CareTimeline` all present (the minimal-page precursor is superseded, §7) |
| F-21 | loading state (no false not-found flash) | before the plant GET resolves, a loading affordance renders (NOT the "could not be found" alert) |
| F-22 | fetch error renders an error/not-found shell | the plant GET rejects -> a graceful error/not-found state (no crash); the timeline's own state covers its side |
| F-23 | invalid/absent id keeps the existing not-found handling | id `0`/non-numeric -> the existing "That plant could not be found." alert path (AC5), no fetch |
| F-24 | the plant name + back link still work (kept from the precursor) | header shows the name; the back link (accessible name "back to plants") navigates to `/plants` |

### 6g. `PlantsPage` entry-point (already covered - kept)

`PlantsPageLink.test.tsx` already asserts each plant links to `/plants/{id}` (the US-3.4
reachability entry point). This story does NOT change that; the re-audit confirms it stays
green and is NOT duplicated here (TEST-004 non-redundancy).

---

## 7. Existing `PlantDetailPage.test.tsx` - keep vs supersede (explicit)

The current `PlantDetailPage.test.tsx` has three tests written for the **minimal US-3.4
precursor**. Explicit disposition:

| existing test | disposition | why |
|---|---|---|
| "is reachable at /plants/:id and hosts the timeline for that id (F-10)" | **KEEP** (fold into / keep alongside F-20) | still true - the full page still hosts `<CareTimeline>` and fires one `/timeline` GET; the reachability assertion is unchanged. It may be broadened to also assert the new sections, but the timeline-hosting assertion stays. |
| "shows the decorative outer pot in the header when set (cachepot)" | **SUPERSEDE** by `PlantAttributesCard` F-7 (+ keep a header/attributes cachepot assertion) | the cachepot text moves from the header into the attributes card per the US-4.3 design (attributes card owns pot + cachepot, §3). The *behaviour* (material shown, size only when set) MUST remain asserted - relocate it to F-7/F-8, do NOT simply delete it. If the build keeps the cachepot line in the header, keep this test; if it moves to the card, this assertion lives in F-7. The re-audit checks the cachepot omit-empty behaviour is asserted **somewhere**, and that no assertion was dropped silently. |
| "shows the plant name in the header and a back link to the list (F-11)" | **KEEP** as F-24 | the header name + back link survive the reimplementation unchanged (TEST-004 survives-reimplementation); still a valid, meaningful assertion. |

**Rule for the lane:** no existing assertion may be *deleted* without either (a) a
replacement case in this foundation that covers the same user-meaningful behaviour, or (b)
a worklog note explaining the behaviour is genuinely gone from the spec. The default is
**keep**; supersede only where US-4.3 deliberately moves a behaviour (the cachepot ->
attributes card). The minimal page's `state.kind === "ready" ? name : "Plant"` /
`"error"` degrade path is retained (F-21/F-22/F-23).

---

## 8. Acceptance (Playwright, TEST-009 - BUILT as the live production-path smoke) - TEST-010

The detail page is real UI in scope, so the acceptance check is **performed this story** as
the project's standing pattern (care-timeline / app-settings precedent): a **live
production-path smoke** against the **built SPA served through the real backend** (NOT the
Vite dev server) - the artifact users get (TEST-010). The driver uses **real UI affordances
only** - never inject values directly. Absent the CI e2e harness (debt #63, §12), the smoke
is driven via the browser tool and evidenced by committed breakpoint screenshots.

| # | test | journey | asserts |
|---|---|---|---|
| A-1 | **full page renders on the production path, zero console errors** | seed a plant with a populated attribute set (incl. cachepot), a water + an overdue feed schedule, several photos incl. a cover, and a mixed care history; build the SPA; serve through the backend; open `/plants/{id}` from the list | header + attributes card (omit-empty verified against a partially-populated plant) + schedules card (a due date + an overdue emphasis) + gallery (cover + strip) + `CareTimeline` all render; **zero page errors / error-level console output** across load + render (TEST-010; warnings ignored), at BOTH breakpoints |
| A-2 | **mutation refreshes the page on the production path** (critical #3) | open the edit modal, change a value (e.g. the name or a schedule), save | the page refreshes and shows the new value without a manual reload; zero console errors |
| A-3 | **delete navigates to the list** (critical #4) | open the delete dialog, confirm | lands back on `/plants`; the deleted plant is gone from the list; zero console errors |
| A-4 | gallery opens the modal | tap the cover / a thumbnail / "+N" | `PhotoGalleryModal` opens on the built SPA; zero console errors |
| A-5 | empty-state variants render | open the detail page for a plant with no schedules AND no photos | the schedules empty-state (with the setup link) and the gallery empty-state render; no crash, no broken image; zero console errors |

**Breakpoints:** A-1 runs at **both locked breakpoints** - phone **390 px** and desktop
**1280 px**. The single-column phone stack (header -> attributes -> schedules -> gallery ->
timeline) and the optional two-column desktop attributes/schedules both render with no
horizontal scroll at 390 (FE-011).

**FE-012 design-review screenshots (committed, required evidence)** in
`specs/changes/plant-detail/screenshots/`:

- `detail-phone-390.png` - the full detail page at 390 px (populated: attributes + a due &
  an overdue schedule + a gallery with cover + a "+N").
- `detail-tablet-820.png` - the detail page at 820 px.
- `detail-desktop-1280.png` - the detail page at 1280 px.
- `detail-empty-390.png` - the schedules + gallery empty-states at 390 px (a bare plant).

FE-012 evidence (deliberate, curated, committed) - distinct from TEST-011 failure-capture
screenshots (ephemeral, never committed).

### 8a. FE-015 Audit Spaces (per-story mandatory)

US-4.3 ships UI, so the two Audit Spaces are asserted (no opt-out justification in the
proposal):

| # | test | asserts |
|---|---|---|
| A-6 | **a11y space** - axe-core scan + FE-011 | an axe-core scan of `/plants/{id}` (populated AND the empty-state variant) reports no violations; the back link + every action button + the "+N" affordance have accessible names; the cover/thumbnail `<img>`s have meaningful `alt`; the overdue schedule emphasis is NOT color-only (label/icon too); tap targets >=44x44 px; no horizontal scroll at 390 px |
| A-7 | **perf-budget space** - FE-007 | the production bundle-size budget holds (the FE-007 CI/test assertion); adding the detail page + the three cards + the gallery must not regress past the budget - enforced as a **test/CI assertion**, not merely a build warning (FE-015) |

The `A-6` color-not-only check is the a11y teeth of the overdue-emphasis requirement (`F-11`
proves emphasis; `A-6` proves it is accessible).

### 8b. Event-logging Audit Space (SEC-008)

The proposal (DoR 6) states: **no new endpoints, no trust-boundary change, no
logging-relevant events beyond the existing mutations** - SEC-008 status quo, tracked v0.3.
This story adds no server surface, so there is **no new event-logging assertion**; the
re-audit records that SEC-008 is a no-op for this frontend-only story and confirms no new
loggable server event was introduced. (Mutations go through the already-built, already-
logged endpoints.)

---

## 9. AC traceability (TEST-015) - every AC -> ≥1 named case

| AC | scenario | covering cases |
|---|---|---|
| **AC1** | attribute set shown (species, acquired, pot + cachepot, light, notes, tags, location); absent optional fields OMITTED | `F-5`..`F-9` (M-ATTR incl. omit-empty + cachepot), `A-1` (production path) |
| **AC2** | each enabled schedule renders next-due; overdue emphasized; paused/dormant states why (null `next_due`); no schedules -> empty state | `F-10`..`F-12b` (M-SCHED: due / overdue / paused / empty + invariant), `A-1`/`A-5` |
| **AC3** | cover + thumbnails render; tapping opens the gallery modal; no photos -> empty state | `F-13a`..`F-13d` (M-GALLERY: cover+strip / "+N" / cover-only / no-cover / empty / open), `A-4`/`A-5` |
| **AC4** | edit/log/schedule/delete work via existing modals; each mutation refreshes visible data without reload; delete -> `/plants` | `F-14` (modals open), `F-15`/`F-16` (mutation refetch), `F-17` (delete navigates), `F-18`/`F-19` (no spurious refetch / failed mutation keeps page), `A-2`/`A-3` (production path) |
| **AC5** | invalid/missing id keeps existing not-found handling; loading + error states match foundation patterns | `F-3`/`F-23` (invalid id), `F-21` (loading), `F-22` (error), `F-24` (name + back link) |
| **AC6 (FE-012)** | verified on the production path, phone + desktop, zero console errors; screenshots committed | `A-1`..`A-5` (production path, both breakpoints, zero console errors), `A-6` (a11y), `A-7` (perf); FE-012 screenshots (§8) |

No AC is uncovered. Every numbered case maps to an AC or pins a matrix cell / the mutation-
refetch contract / a page state.

---

## 10. Mocking boundary (TEST-003) - explicit

- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. The plant
  GET, the `/timeline` GET, the `/photos` GET, and the mutation calls (PUT/POST/DELETE) are
  all routed by a `stubByPath` helper returning `okJson`/`fail` responses. Components + the
  page render the **real** components (RTL); routing via a **memory router**. No component,
  hook, or modal is mocked - only `fetch`. The reused modals render for real (their
  behaviour is their own suite's; this story asserts the wiring).
- **Acceptance (Playwright / live smoke):** the built SPA served through the **real
  backend** + real DB (the production path); nothing mocked - every section's render and
  every refetch depends on the real endpoints.

---

## 11. Mutation probes (story-complete re-audit) - sanctioned, restored byte-identically

At story-complete the test-engineer runs sanctioned probes on the four critical-100% paths
(§8/§1), logging each (file, mutation, failing test), restoring byte-identically, and
verifying `git status` clean. The orchestrator independently verifies the clean tree.
Mutation evidence outranks assertion-reading on these paths. The exact new-file paths are
the FE lane's to finalize (the design proposes `PlantAttributesCard.tsx`,
`PlantSchedulesCard.tsx`, `PlantGallery.tsx`, `usePlantDetail.ts`, plus the expanded
`PlantDetailPage.tsx`); the re-audit locates the implemented file and probes the named
behaviour.

| critical path | file (lane finalizes) | mutation | test that MUST go red |
|---|---|---|---|
| 1. omit-empty attributes | `PlantAttributesCard.tsx` | drop the null-guard so an absent field renders its (empty/"null") row anyway | `F-6` (empty plant would render rows) + `F-7` (cachepot "(null cm)") |
| 2a. schedule state - overdue | `PlantSchedulesCard.tsx` | drop the `overdue_days > 0` emphasis branch (render every due the same) | `F-11` (overdue no longer emphasized) |
| 2b. schedule state - paused | `PlantSchedulesCard.tsx` | render `next_due` even when null (skip the paused branch) | `F-12` (a paused schedule would show a date / "null" instead of the reason) |
| 3. mutation -> refetch | `PlantDetailPage.tsx` / `usePlantDetail.ts` | remove the `reload()` call from the edit `onSubmit` (or the schedule/photo `onClose`) | `F-15`/`F-16` (no second plant GET; stale value) |
| 4. delete navigates | `PlantDetailPage.tsx` | drop the `navigate("/plants")` on delete success (stay on the route) | `F-17` (the list landing would not render) |
| (gallery) "+N" open | `PlantGallery.tsx` | disconnect the "+N" affordance from opening `PhotoGalleryModal` | `F-13b` (tapping "+N" no longer opens the modal) |

---

## 12. Required test markers + file-size (TEST-012, QG-009)

Frontend `*.test.ts(x)` run under **vitest** (no `pytestmark` - the FE convention; TEST-012
markers apply to Python only). Keep each new test file under the QG-009 **500-LOC hard
max**; if the page test grows past it, split by concern (attributes / schedules / gallery /
action-wiring + page-states). **No Python test file is created or edited** (frontend-only,
§2); **no `test_migrations.py` edit**; **no edit to the reused modals' own test suites**
(their internals are out of scope, PRIN-IV).

**Build-pickup risks (carry into the session):**
1. **Residual assumption (proposal §open questions).** The thumbnail cap (~8 + "+N") is a
   build-time layout call. `F-13b`/`gal-overflow` pin the *behaviour* (bounded strip +
   correct "+N" that opens the modal); the lane records the confirmed cap in the worklog
   and the re-audit checks `F-13b` uses it.
2. **Modal-wiring non-uniformity (§1 note).** The reused modals expose different callbacks
   (`onSubmit`/`onConfirm`/`onLogged`/`onClose`); the page's `reload()` must hook the owned
   handlers (edit/delete) AND the `onClose` of the self-managing modals (schedules/gallery).
   Do NOT modify a shared modal to add an `onMutated` (PRIN-IX); if one genuinely cannot
   signal a mutation, STOP and flag. `F-15`/`F-16` pin the observable refetch regardless of
   mechanism.
3. **No committed-in-CI e2e harness** (project-wide gap, debt #63). The acceptance lane
   (§8) is a LIVE production-path browser smoke + committed screenshots, NOT a `.spec.ts`
   in CI - exactly as care-timeline / app-settings did.
4. **File ownership.** FE-only. New `features/plants/*` files + the expanded
   `PlantDetailPage.tsx`. `PlantsPage.tsx` is NOT modified (the per-plant link already
   exists, `PlantsPageLink.test.tsx`); if the lane finds a reason to touch it, that is a
   scope check.

---

## 13. TEST-014 - Test-first evidence (the red)

The FE lane records in `worklog.md` the **failing run that precedes implementation** - the
test names plus the failing assertion/error output (the "red") - before the green commit:
run the new `PlantAttributesCard` / `PlantSchedulesCard` / `PlantGallery` /
`usePlantDetail` / expanded `PlantDetailPage` tests against the *unimplemented* components
-> expect module-not-found / assertion failures (the cards don't exist; the page has no
attributes/schedules/gallery sections; no `reload()` wiring). Capture the names + the first
failing line per group. A worklog showing no red-before-green is a PRIN-III deviation
requiring comply-or-explain.

---

## 14. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; the repo must not drop the floor. New/changed FE code **>=80%
  diff-cover**.
- **Branch coverage:** the omit-empty forks (M-ATTR §3: each field's null-guard, the
  cachepot size-suffix gate), the schedule-state forks (M-SCHED §4: paused / overdue /
  due / empty), the gallery forks (M-GALLERY §5: cover-present / over-cap "+N" / empty),
  and the page state machine (loading / ready / error / invalid-id) all exercised.
- **Critical paths flagged 100%** (spec-flagged -> QG-002 100%): the four of §11 (omit-empty
  invariant, schedule next-due state machine incl. paused/overdue/both-null, mutation ->
  refetch, delete -> navigate). Mutation evidence outranks assertion-reading at
  story-complete (§11).
- FE-007 bundle budget enforced as a **test/CI assertion** (`A-7`), not a build warning
  (FE-015 / QG-014 spirit).

---

## 15. Re-audit note (DoD §3)

At story-complete the test-engineer re-audits the implemented suite against this foundation
and issues the **test-foundation approval**, checking:

- Every surface in §1 has its happy + sad (TEST-005); matrices M-ATTR (§3), M-SCHED (§4),
  M-GALLERY (§5) are present and **parametrized** with the named cells (TEST-007).
- The four **critical-100%** paths (§11) are exercised and each survives a **sanctioned
  mutation probe** (omit-empty guard drop, schedule-state branch drop, `reload()` removal,
  delete-navigate removal) - each probe logged (file, mutation, failing test), tree
  restored byte-identically, `git status` clean.
- The omit-empty invariant holds (`F-6`/`F-7`): an absent field renders NO row and the
  cachepot size suffix is gated on the size.
- The schedules card renders paused (`F-12`, no date/no overdue), overdue (`F-11`,
  emphasized + not color-only), due (`F-10`), and the empty-state setup link (`F-12b`); the
  both-null invariant never yields an overdue badge without a date.
- The gallery renders cover + strip (`F-13a`), a correct "+N" that opens the modal
  (`F-13b`), and the empty-state with no auto-open / no broken image (`F-13c`).
- Every action opens its modal (`F-14`); an edit refetches (`F-15`); schedule/photo close
  refetches + the timeline key bumps (`F-16`); delete navigates to `/plants` (`F-17`); a
  cancelled modal does not refetch (`F-18`); a failed mutation keeps the page (`F-19`).
- The page states are covered: full page mounts (`F-20`), loading (`F-21`), error (`F-22`),
  invalid id keeps the existing not-found handling (`F-23`), name + back link (`F-24`).
- The existing `PlantDetailPage.test.tsx` disposition (§7) is honoured: no assertion
  deleted without a replacement; the cachepot behaviour is asserted somewhere (header or
  card); `PlantsPageLink.test.tsx` stays green and un-duplicated.
- The acceptance smoke ran on the **production path** (built SPA through the backend) with
  **zero console errors** at **both breakpoints** (`A-1`..`A-5`, TEST-009/010); FE-012
  screenshots committed (§8); the FE-015 a11y + perf spaces asserted (`A-6`/`A-7`); SEC-008
  is a no-op for this frontend-only story (§8b).
- **No backend test, no migration, no repository change, no reused-modal internals
  re-tested** (scope, PRIN-IV / SPEC-001).
- Every AC1-AC6 maps to a named implemented test (§9, TEST-015); the TEST-014 red is
  recorded (§13); the suite is parallel-safe (TEST-006) with per-test `fetch` stubs and
  explicit fixture data (no real-clock dependence for the schedule-state assertions).

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature review.
