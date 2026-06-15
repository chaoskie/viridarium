---
title: Test Foundation - care-timeline (US-3.4)
type: test-foundation
change: care-timeline
status: authored
date: 2026-06-14
---

# Test Foundation - care-timeline (US-3.4)

Pre-implementation test foundation (SPEC-003 artifact, gates implementation) for the
**per-plant care history timeline**: a read-only `GET /api/v1/plants/{id}/timeline` that
merges the plant's care events (US-3.2) and photos (US-2.3) server-side into one
reverse-chronological, discriminated `event | photo` feed, plus a minimal `/plants/{id}`
page (US-4.3 precursor) that renders it. Authored by `test-engineer` against
`proposal.md` (the PO-resolved placement/data/photo decisions, the response contract,
AC1-AC6, and the ONE flagged residual assumption about standalone-photo interleave) and
`design.md` (the `TimelineQueryService` merge/dedup/sort, the discriminated response, the
FE page+component). Mirrors the structure + numbering of
`due-computation/test-foundation.md` and the two-lane + acceptance shape of
`app-settings/test-foundation.md`.

This document is **prescriptive** (input matrices, named/numbered cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. Three lanes -
**backend** (`backend/`: the timeline query module + endpoint), **frontend**
(`frontend/`: the page + component + client), and **acceptance** (the production-path
Playwright smoke) - implement against it; backend lands first (the frontend lane builds
to the API contract). Each lane records its TEST-014 red in `worklog.md` before turning
green. The story-complete pass re-audits the implementation and issues the DoD §3
approval.

Cases are numbered so the lanes can cite them and the re-audit can diff:
`B-In` (backend integration - the query service + endpoint through a real DB),
`B-Un` (backend unit - the in-memory merge/dedup/sort, the one place a pure unit slice is
exceptionally warranted, §2), `F-n` (frontend - client + component), `A-n` (acceptance /
production path). The re-audit checks every numbered case is present, meaningful
(TEST-004), and on its assigned layer, and maps every AC1-AC6 (§9).

**Critical paths for this story** (flagged 100% in §8) - the four places a regression
silently corrupts the history feed or its contract; mutation evidence outranks
assertion-reading here (§11):

1. **The event-photo dedup invariant** (AC2) - a photo referenced by some event's
   `photo_id` is emitted ONLY inline on that event entry, NEVER also as a `kind:"photo"`
   entry. A broken dedup double-shows every event photo (once inline, once standalone),
   doubling the user's history and lying about what happened.
2. **The backdated-sort-by-`happened_on`** (AC1) - events sort by `happened_on`, NOT
   `created_at`; a backdated event (logged today for last week) must sort to its
   `happened_on` slot, not the top. A sort keyed on the wrong field puts backfilled
   history in the wrong place - the headline US-3.4 promise ("everything that ever
   happened, newest first") silently wrong.
3. **The missing-plant 404 + plant-reason (no PII)** (AC4) - an unknown plant id returns
   404 with a `{"detail"}`-only, plant-reason body and no PII; the plant-exists guard
   fires FIRST (before any merge). A leaked 200-with-empty-list or a PII-bearing 500
   breaks the VIRIDARIUM-48 convention and the privacy posture (PRIN-II/SEC-001).
4. **The discriminated-union shape contract** (AC1-AC3) - every entry is exactly one of
   `event` / `photo` with the pinned key-set (§7); `kind` discriminates; an event carries
   `photo:{id,url}|null`, a photo entry carries `photo:{id,url}`. A widened/leaked shape
   (a stored_filename, a raw event id where none is contracted, a missing `kind`) breaks
   the FE union map and can leak the on-disk filename security boundary (ARCH-007).

---

## 1. Surface inventory (happy + sad per surface, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| Q1 | `TimelineQueryService.for_plant(plant_id)` | query service (read-only, ARCH-006) | events + standalone photos merged, newest-first | missing plant -> raises the not-found domain error (no merge attempted); plant with no history -> `[]` |
| M1 | the in-memory merge/dedup/sort step | pure transform (events, photos, linked-id set -> ordered entries) | event-with-photo emits one inline entry; standalone photo emits `kind:photo`; backdated event sorts by `happened_on` | a photo whose id is in `linked` is NEVER emitted as `kind:photo`; same-day event+photo tiebreak deterministic by `created_at` desc |
| E1 | `GET /api/v1/plants/{id}/timeline` | endpoint | 200, the ordered discriminated feed; all four event types carried; bounded query count | 404 (plant-reason, no PII) for an unknown plant; empty history -> 200 `[]` |
| F1 | `lib/api/timeline.ts` (`getTimeline`) + the union types | FE client | GET parses the discriminated `(TimelineEvent \| TimelinePhoto)[]`; the union narrows on `kind` | `ApiError` on non-2xx |
| F2 | `CareTimeline` component | FE component | renders entries newest-first; each event type a distinct marker/label; observe shows health; inline + standalone photos render | empty-state renders for no history; a failed load degrades (no crash) |
| F3 | `PlantDetailPage` + `/plants/:id` route | FE page/route | the route is reachable; header shows the plant name; a back link returns to the list; hosts `<CareTimeline>` | (route-level: an unknown/absent plant id degrades gracefully - no crash; the timeline empty/error state covers the data side) |
| A1 | `/plants/{id}` journey | acceptance (Playwright, production path) | open the page on the built SPA -> the feed renders; zero console errors at 390 + 1280 | (failure = any console error / a non-rendering feed; both breakpoints) |

The exact identifier names (`TimelineQueryService.for_plant`, `TimelineEntry`,
`TimelineEvent`/`TimelinePhoto`, `getTimeline`, `CareTimeline`, `PlantDetailPage`) are
pinned by `design.md`; the re-audit checks the **behaviour and the response contract**
(§7), accepting the lane's final spelling where the design left a choice.

**Plant-exists guard reuse note.** Both `CareEventRepository` and `PhotoRepository`
already expose `plant_exists(plant_id) -> bool` (domain). The service MUST guard with one
of these FIRST (the VIRIDARIUM-48 convention) and raise the plant-not-found domain error
mapped to 404 by the registered handler - it does NOT introduce a new persistence read.

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Integration is the primary layer** (TEST-001): the `TimelineQueryService` through the
  **real composition root** against a **real DB** (router -> `TimelineQueryService` ->
  the existing `CareEventRepository` + `PhotoRepository` -> SQLAlchemy -> SQLite), seeding
  events/photos via the real services/endpoints (TEST-006 independence). The merge,
  dedup, sort, the all-four-event-types pass-through, the 404 guard, the bounded
  query-count, and the dual-engine read are all only meaningful end-to-end and asserted
  there (§4). This is where the bulk of the cases live.
- **Unit is exceptionally warranted for the in-memory merge/dedup/sort** (TEST-001 (a):
  the one piece of genuinely non-trivial pure logic in the story - the dedup set
  membership, the `happened_on`-vs-`created_at.date()` sort-key selection, and the
  `(date, created_at)` desc tiebreak). IF the lane factors this into a pure function
  (e.g. `_merge(events, photos, linked) -> list[TimelineEntry]`, framework-free, no I/O),
  it gets a `pytestmark = pytest.mark.unit` slice (§4f, `B-U1`-`B-U5`) that exhaustively
  pins the sort/dedup table without DB round-trips. IF the lane keeps the merge inlined in
  the service method (also acceptable - it is small), `B-U1`-`B-U5` fold into the
  integration cases (`B-I1`-`B-I6`) instead. The re-audit accepts either, checking the
  **behaviour** (dedup invariant + backdated sort + tiebreak) is pinned somewhere, not the
  function's visibility. **This is the only unit slice**; there is no widely-branching
  domain function here (contrast due-computation's `compute_due`).
- **No new persistence, no migration** - the story reuses `CareEventRepository.
  list_for_plant` (already `happened_on` desc, `created_at` desc) and
  `PhotoRepository.list_for_plant` (already `created_at` desc). It adds **no tables, no
  columns, no migration, no write path**. No `test_migrations.py` edit. If the lane finds
  itself writing a migration or a new repository method, that is a scope deviation to halt
  and flag (PRIN-IV / SPEC-001).
- **Dual-engine** (`test_fk_cross_engine.py` or a dedicated cross-engine test, ARCH-011):
  the merged read runs identically on the engine resolved from `DATABASE_URL` (SQLite
  locally, PostgreSQL on the CI postgres leg). The two underlying list reads are already
  dual-engine (US-2.3 / US-3.2); this story's net-new portability concern is that the
  **merge produces the same ordered feed on both engines** - in particular the
  `created_at` tiebreak is a `datetime` comparison and the photo date is
  `created_at.date()`, which must compare identically across engines (§5).
- **Frontend lane** (vitest + RTL): the `timeline.ts` client contract + the union mapping,
  and the `CareTimeline` / `PlantDetailPage` render behaviour, `fetch` stubbed (§6).
- **Acceptance (Playwright, TEST-009): BUILT this story** as the **live production-path
  smoke** that is the project's standing pattern (per the app-settings precedent: a built
  SPA served through the real backend, driven via the browser, zero console errors,
  committed breakpoint screenshots - NOT a committed-in-CI `.spec.ts`, which is a known
  systemic gap, see §13 risk note). The journey opens `/plants/{id}` on the built SPA and
  asserts the feed renders with zero console errors at 390 + 1280 (§8).

---

## 3. Input-state matrix M-TL (the merge, AC1-AC3) - TEST-007

The merge crosses **3 dimensions** ({source: event, standalone-photo} x {event has a
linked photo: yes, no} x {date basis collides same-day: yes, no}) and well exceeds 6
logical cells, so it gets an explicit matrix with a **named branch-priority order**. The
priority order matches the design pseudocode:

1. **Compute `linked = {e.photo_id for e in events if e.photo_id}`** (the dedup set).
2. **Emit one entry per event** (`kind:event`), carrying its inline photo
   `{id,url}` when `photo_id` is set, else `photo:null`. The event's `date` is its
   `happened_on`; its tiebreak key is its `created_at`.
3. **Emit one entry per photo whose id is NOT in `linked`** (`kind:photo`). Its `date` is
   `created_at.date()`; its tiebreak key is its `created_at`.
4. **Sort the merged list by `(date, created_at)` descending** - newest-first, with the
   `created_at` timestamp breaking same-`date` ties deterministically.

| id | source | linked? | scenario | expected in feed |
|---|---|---|---|---|
| `evt-plain` | event (water) | no photo | a water event on D | one `kind:event`, `photo:null`, `date=D` |
| `evt-with-photo` | event (observe) + photo P | P linked to it | the event references P | one `kind:event` carrying `photo:{id:P, url}`; **P NOT a `kind:photo` entry** (dedup - CRITICAL) |
| `photo-standalone` | photo Q | unlinked | a photo with no event referencing it | one `kind:photo` `{id:Q, url}`, `date=Q.created_at.date()` |
| `backdated-evt` | event | (any) | event with `happened_on = D-7` but `created_at = today` | sorts to the **D-7** slot, NOT the top (sort by `happened_on`, CRITICAL) |
| `same-day-tiebreak` | event on D (`created_at` t2) + standalone photo dated D (`created_at` t1 < t2) | mixed | both fall on calendar date D | deterministic order: the later `created_at` (t2, the event) precedes the earlier (t1, the photo) - `created_at` desc within the same `date` |
| `all-four-types` | water, feed, repot, observe events | no photos | one event of each type | four `kind:event` entries; each carries its `event_type`; observe carries `health`, the other three carry `health:null` |
| `empty` | none | n/a | a plant with zero events and zero photos | `[]` |
| `interleave` | events + standalone photos on different dates | mixed | the residual-assumption default | standalone photos appear, interleaved by their `created_at` date, newest-first among the events (§ residual assumption, AC3) |

The headline critical cells are `evt-with-photo` (dedup - the linked photo appears exactly
once, inline), `backdated-evt` (sort key is `happened_on`), and `same-day-tiebreak`
(deterministic `created_at` desc). `all-four-types` proves every event type and the
observe-only `health` carry through with the right per-type field.

### Residual-assumption switch (proposal §"Residual assumption to confirm at build")

The `interleave` row encodes the **default** (spec-faithful): standalone (unlinked) photos
DO interleave into the timeline by their `created_at` date. Cases `B-I3` / `B-U3` / `F-7`
assert this.

**If the PO flips to events-only at build pickup** (the 5-second confirm in `tasks.md`):
the `interleave` / `photo-standalone` expectation inverts to **"standalone photos are
ABSENT from the timeline"** (only event entries, each with its inline photo, are emitted;
unlinked photos never appear). In that case the build agent KEEPS `B-I3`/`B-U3`/`F-7` as
the named cases but flips their assertion to *absence* (the standalone photo id appears in
NO entry), and the `photo-standalone` row's expected becomes "no entry produced". The
dedup invariant (`evt-with-photo`) is UNCHANGED either way - an event's inline photo still
shows once. The re-audit checks which interpretation the worklog records as PO-confirmed
and verifies the matching assertion direction. **Default = interleave (present); flip =
absent.** Exactly one of the two is live; the build agent records the confirmed choice in
the worklog before turning the case green.

---

## 4. Backend integration: `test_timeline_endpoint.py` (+ optional service/merge unit) (`integration`)

`pytestmark = pytest.mark.integration`. Real DB, nothing internal mocked (TEST-003). Each
test seeds its own plant(s), event(s), and photo(s) via the real services/endpoints for
TEST-006 independence; cleanup scoped to created rows, never global truncation. Helpers
mirror the existing suites: `_make_plant(client, name="Fern") -> int`,
`_log_event(client, plant_id, type, happened_on=None, note=None, health=None,
photo_id=None) -> int`, `_upload_photo(client, plant_id) -> int` (returns the photo id),
`_timeline(client, plant_id) -> (status, body)`.

### 4a. Merge order + sort (Q1, E1; AC1)

| # | test | setup | asserts |
|---|---|---|---|
| B-I1 | newest-first merge of events + standalone photos | a plant with events on D1<D2 and a standalone photo dated D3 (D1<D2<D3) | 200; the feed is ordered `[D3-photo, D2-event, D1-event]` (descending by `date`); each entry has the right `kind` |
| B-I2 | **backdated event sorts by `happened_on`, not `created_at`** (CRITICAL) | log event A `happened_on=D2` then log event B `happened_on=D1` (D1<D2) so B's `created_at` is LATER than A's though its `happened_on` is EARLIER | the feed orders A (D2) before B (D1) - sorted on `happened_on`, NOT on insertion/`created_at` order. (A naive `created_at`-sort would put B first.) |
| B-I3 | **standalone photo emits as `kind:photo` at its date** (residual default) | a plant with one standalone (unlinked) photo and one unrelated event | the photo appears as a `kind:photo` entry with `date == photo.created_at.date()` and `photo:{id,url}`. **[FLIP target: if PO chooses events-only, assert the photo id appears in NO entry.]** |
| B-I4 | same-day event + standalone photo tiebreak is deterministic | an event with `happened_on=D` (`created_at` t2) and a standalone photo on calendar date D (`created_at` t1 < t2) | both entries present, ordered with the later `created_at` first (the event before the photo) - the `created_at` desc tiebreak within the same `date`; the order is stable across repeated calls |
| B-I5 | empty history -> `[]` | a freshly-created plant, no events, no photos | 200, body is exactly `[]` (not null, not 404) |

### 4b. Dedup invariant (Q1, E1; AC2, CRITICAL)

| # | test | setup | asserts |
|---|---|---|---|
| B-I6 | **event with a linked photo emits ONE entry, photo inline; the photo is NOT a `kind:photo` entry** (CRITICAL) | upload a photo P for the plant, then log an event with `photo_id=P` | the feed has exactly ONE entry referencing P: a `kind:event` whose `photo` is `{id:P, url:".../photos/P"}`; there is **NO** `kind:photo` entry with `id==P`. Count of entries == 1 (the single event), not 2 |
| B-I7 | a mix: one linked photo + one standalone photo | photo P linked to an event, photo Q standalone (unlinked) | the feed has the event (carrying P inline) AND a `kind:photo` entry for Q; P never appears as a `kind:photo` entry, Q never appears inline on any event. (The dedup set is exactly `{P}`.) |
| B-I8 | two events linking the SAME photo id | (edge) if the schema allows two events to reference one photo_id, log two such events | the photo is still never a `kind:photo` entry (its id is in `linked`); it renders inline on each event that references it. (If the data model forbids shared photo_id, this case is N/A and the worklog records that; otherwise it pins the `linked`-is-a-set semantics.) |

### 4c. Event-type + field pass-through (Q1, E1; AC1)

| # | test | setup | asserts |
|---|---|---|---|
| B-I9 | **all four event types carried through with their fields** | log one each of water, feed, repot, observe (observe with `health="good"` + a note; others with notes, no health) | the feed has four `kind:event` entries; their `event_type` values are exactly `{water, feed, repot, observe}`; the observe entry's `health == "good"`; the water/feed/repot entries' `health` is `null`; each entry's `note` round-trips |
| B-I10 | event with a note but no photo -> `photo:null` | a water event, note set, no `photo_id` | the entry's `photo` is JSON `null` (the inline-photo slot is null, not absent) |

### 4d. Missing plant + privacy (E1; AC4, CRITICAL)

| # | test | setup | asserts |
|---|---|---|---|
| B-I11 | **unknown plant -> 404, plant-reason, no PII** (CRITICAL) | `GET /api/v1/plants/999999/timeline` (no such plant) | status 404; body keys are exactly `{"detail"}`; the detail is the plant-not-found reason (carries only the integer id / the closed reason, no free text, no stack, no PII - SEC-001/SEC-007); the plant-exists guard fired before any merge (no 500, no empty 200) |
| B-I12 | plant-exists guard fires first (no leak of a sibling plant's data) | plant A with history; request `/plants/{B}/timeline` for a non-existent B | 404, NOT plant A's feed; the guard does not fall through to a bare merge |

### 4e. Bounded query count + contract shape (Q1, E1; AC4)

| # | test | setup | asserts |
|---|---|---|---|
| B-I13 | **bounded query count regardless of history size** (CRITICAL for NFR) | seed a plant with N events + N photos, then 2N events + 2N photos | the SQL statement count for `GET .../timeline` does **NOT** scale with the history size - it is a small constant (the design's two list reads + the plant-exists guard), and the count is **the same for N and 2N entries** (no per-entry query). Captured via the `before_cursor_execute` listener pattern of `test_plant_list_nplus1.py` (the `_count_statements` context manager) on a counting engine over the call; assert `<=` a small constant (e.g. `<= 4`) AND equal across N/2N |
| B-I14 | response contract key-set is exact (event entry) | any populated event entry from B-I9 | the JSON keys of a `kind:event` entry are **exactly** `{"kind","date","event_type","note","health","photo"}`; `kind == "event"`; when a photo is inline, the `photo` object's keys are exactly `{"id","url"}` and `url` matches `/api/v1/plants/{plant_id}/photos/{id}` (the §7 shape; no `stored_filename`, no `created_at`, no `is_cover` leak - ARCH-007) |
| B-I15 | response contract key-set is exact (photo entry) | any `kind:photo` entry from B-I3 | the JSON keys of a `kind:photo` entry are **exactly** `{"kind","date","photo"}`; `kind == "photo"`; the `photo` object's keys are exactly `{"id","url"}`; no `event_type`/`note`/`health` keys on a photo entry |
| B-I16 | OpenAPI exposes the timeline path additively | the emitted `/api/v1/openapi.json` | `paths` contains `GET /api/v1/plants/{plant_id}/timeline`; its 200 response schema is an array of the discriminated `event|photo` shape (the union with the pinned key-sets); no other path/schema changed (additive only; API-001/API-004 not triggered). (TEST-008 codegen build-output assertion.) |

`B-I13` is the AC4 N+1 guard end-to-end - the verifiable bound, not an eyeball (reuses the
existing `_count_statements` helper). `B-I14`/`B-I15` pin the discriminated-union shape
(critical path #4) structurally so a future addition can't silently widen the feed or leak
the on-disk filename.

### 4f. Optional pure merge unit slice: `test_timeline_merge.py` (`unit`) - §2

IF the lane factors the merge into a pure function, `pytestmark = pytest.mark.unit`,
framework-free, against hand-built `CareEvent` / `Photo` value objects (no app, no DB). It
exhaustively pins matrix M-TL's sort/dedup table cheaply. If not factored, these fold into
the integration cases above (the re-audit accepts either - §2).

| # | test | setup | expectation |
|---|---|---|---|
| B-U1 | dedup: a linked photo id is not a `kind:photo` entry | events=[event linking P], photos=[P], linked={P} | output has one `event` entry (photo P inline), zero `photo` entries |
| B-U2 | standalone photo emitted as `kind:photo` | events=[], photos=[Q], linked={} | output is one `photo` entry for Q at `Q.created_at.date()` |
| B-U3 | interleave default: standalone photo present among events | events=[E on D2], photos=[Q on D3 standalone], linked={} | output ordered `[photo Q (D3), event E (D2)]`. **[FLIP target: events-only -> Q absent, output `[event E]`.]** |
| B-U4 | backdated event sorts by `happened_on` | events=[A happened_on=D2 created_at=t1, B happened_on=D1 created_at=t2>t1] | output ordered `[A (D2), B (D1)]` - by `happened_on`, regardless of `created_at` order |
| B-U5 | same-date tiebreak by `created_at` desc | an event on date D (`created_at` t2) + standalone photo on date D (`created_at` t1<t2) | output ordered `[event (t2), photo (t1)]` - deterministic `created_at` desc within the same `date` |

---

## 5. Dual-engine: cross-engine test (`integration`, ARCH-011)

Add to `test_fk_cross_engine.py` (or a small dedicated cross-engine test) one test
resolving the engine from `DATABASE_URL` via the existing `fk_engine` fixture (SQLite
locally, PostgreSQL on the CI postgres leg). The two underlying list reads are already
proven dual-engine; this story's net-new portability concern is that the **merged feed
orders identically on both engines** (the `created_at` datetime tiebreak + the
`created_at.date()` photo date must compare the same).

| # | test | asserts |
|---|---|---|
| B-I17 | **the merged timeline orders identically on the real engine** | via the repositories on the **real engine**: build a plant; add a backdated event (`happened_on` earlier than a later-created event), a standalone photo, and an event with a linked photo; call `TimelineQueryService.for_plant(pid)` (or the merge over the real reads) -> the SAME ordered, deduped feed on **both** engines (CI postgres leg proves PostgreSQL; locally SQLite): the backdated event in its `happened_on` slot, the linked photo inline-only, the standalone photo present (default). Self-cleans its own rows. |

The re-audit checks `B-I17` ran on **both** engines at minimum (the ordered/deduped merge
over real reads is the one nontrivial-portability concern this story adds, ARCH-011).

---

## 6. Frontend (vitest + RTL)

Mirror `careEvents.test.ts` / `settings.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson`/`fail` helpers, `afterEach(unstubAllGlobals + restoreAllMocks)`. **fetch is the
mock boundary** (TEST-003 FE equivalent). A `SAMPLE_TIMELINE` constant carries a feed with
at least: one event of each of the four types, an event with an inline photo, and a
standalone `kind:photo` entry, so the component tests render the full discriminated shape.

### 6a. `timeline.test.ts` (client contract + union mapping)

| # | test | asserts |
|---|---|---|
| F-1 | `getTimeline` GETs the timeline path | `GET /api/v1/plants/{id}/timeline`, `Accept: application/json`; resolves the parsed `(TimelineEvent \| TimelinePhoto)[]` |
| F-2 | **the client maps the discriminated union correctly** (mirrors §7) | given a stub feed with both kinds -> the `event` entry narrows to carry `event_type`/`note`/`health`/`photo`, the `photo` entry narrows to carry only `photo`; narrowing is keyed on `kind` (a consumer switching on `entry.kind` type-checks and reads the right fields). No runtime coercion beyond the shape mirror |
| F-3 | `getTimeline` throws ApiError on non-2xx | a 404 / 500 -> rejects `instanceof ApiError` (the page surfaces the empty/error state; F-6) |

### 6b. `CareTimeline.test.tsx` (component, RTL)

| # | test | asserts |
|---|---|---|
| F-4 | **each of the four event types renders a DISTINCT marker/label** | mount with `SAMPLE_TIMELINE` (one water, feed, repot, observe) -> four entries render, each with a distinguishable label/icon/test-id per `event_type` (water != feed != repot != observe); no two types share the same rendered marker |
| F-5 | **observe renders the health rating; an event photo renders inline** | an observe entry with `health:"good"` and an inline `photo:{id,url}` -> the health rating is visible AND an `<img>` (or thumb) with the photo `url` is rendered within that entry; a water entry with `photo:null` renders no image and no health chip |
| F-6 | **a `kind:photo` entry renders the image** | a standalone `kind:photo` entry -> its image renders with the entry's `photo.url`; it is visually a photo entry (not mislabelled as an event) |
| F-7 | **empty-state renders for no history** | mount with the stub returning `[]` -> a clear empty-state message renders (no crash, no perpetual spinner). **[FLIP note: the empty-state is unchanged by the residual-assumption flip; only B-I3/B-U3 invert.]** |
| F-8 | newest-first order preserved in render | mount with a feed already ordered newest-first -> the DOM order matches the array order (the FE does not re-sort; it trusts the server contract, AC1) |
| F-9 | load error surfaced inline | mount with the GET stub rejecting (ApiError) -> an inline error/empty-ish state renders (the component degrades gracefully, does not throw) |

### 6c. `PlantDetailPage.test.tsx` (page/route, RTL)

| # | test | asserts |
|---|---|---|
| F-10 | **the `/plants/:id` route is reachable and renders the page** | render the app router at `/plants/3` (memory router) -> `PlantDetailPage` mounts (not the `*` not-found placeholder, not the bare plants list); it hosts `<CareTimeline plantId={3}>` (a single `GET .../3/timeline` fires) |
| F-11 | **header shows the plant name and a back link returns to the list** | the page renders a header with the plant's name and a back affordance (accessible name) whose target is `/plants` (FE-011 accessible name); clicking it navigates back to the list |
| F-12 | each plant card/row in the list links to its detail page | render `PlantsPage` with stubbed plants -> each plant has a link/affordance whose href/navigation target is `/plants/{that plant's id}` (the reachability entry point, AC5) |

### 6d. fetch-mock contract fixtures (shared)

A `SAMPLE_TIMELINE` (the full discriminated feed) and the `okJson(status, body)` /
`fail(status)` helpers from `careEvents.test.ts`. Component tests render the real
components (RTL); affordances are driven via accessible names / labels / test-ids
(FE-011 / FE-014). The plant name for `F-11` is sourced however the page sources it
(a `getPlant` call or a passed prop) - the re-audit checks the **behaviour** (name + back
link present), not the data-source mechanism.

---

## 7. Response contract (pinned)

`GET /api/v1/plants/{id}/timeline -> 200` returns a JSON array of entries; each entry is
**exactly one** of the two discriminated shapes below, no more (the §4e key-set assertions
enforce it structurally). `kind` is the discriminator.

```
// event entry
{ "kind": "event",
  "date": "YYYY-MM-DD",                 // = happened_on
  "event_type": "water"|"feed"|"repot"|"observe",
  "note": string | null,
  "health": "good"|"fair"|"bad" | null, // non-null only on observe
  "photo": { "id": int, "url": string } | null }

// photo entry (standalone, unlinked)
{ "kind": "photo",
  "date": "YYYY-MM-DD",                 // = created_at.date()
  "photo": { "id": int, "url": string } }
```

| entry | field | type | rule |
|---|---|---|---|
| both | `kind` | `"event" \| "photo"` | the closed discriminator |
| both | `date` | `date` (ISO string) | event -> `happened_on`; photo -> `created_at.date()` |
| event | `event_type` | `"water"\|"feed"\|"repot"\|"observe"` | the spec event vocab verbatim (closed enum) |
| event | `note` | `string \| null` | the event's note, faithfully |
| event | `health` | `"good"\|"fair"\|"bad" \| null` | non-null **only** on observe events (else null) |
| event | `photo` | `{id,url} \| null` | the inline linked photo, or null |
| photo | `photo` | `{id,url}` | the standalone photo (always present on a photo entry) |
| nested `photo` | `id` / `url` | `int` / `string` | `url == /api/v1/plants/{plant_id}/photos/{id}` (the existing `PhotoResponse.url` recipe) |

The nested `photo` object exposes **only** `{id, url}` - never `stored_filename` (the
on-disk security boundary, ARCH-007), never `content_type`/`size_bytes`/`is_cover`/
`created_at`. Sorted by `(date, created_at)` descending; the `created_at` timestamp is the
deterministic same-`date` tiebreak but is NOT itself a response field. 404 bodies are
`{"detail"}`-only with the plant-not-found reason, no PII.

---

## 8. Acceptance (Playwright, TEST-009 - BUILT as the live production-path smoke) - TEST-010

The timeline page is real UI in scope, so the acceptance check is **performed this story**
as the project's standing pattern (per the app-settings precedent, worklog §13 note): a
**live production-path smoke** against the **built SPA served through the real backend**
(NOT the Vite dev server) - the same artifact users get (TEST-010 production-path
discipline). The driver uses **real UI affordances only** - never inject values directly.
If a committed `.spec.ts` + POM (`timeline.po.ts`, FE-013/FE-014) is stood up, it follows
the locator priority; absent the CI harness (see §13 risk), the smoke is driven via the
browser tool and evidenced by the committed screenshots below.

| # | test | journey | asserts |
|---|---|---|---|
| A-1 | **timeline renders on the production path, zero console errors** | seed a plant with a mixed history (an event of each type, an event with an inline photo, a standalone photo), build the SPA, serve it through the backend, navigate to the plant from the list -> open `/plants/{id}` | the feed renders newest-first; the four event types are visually distinct; the observe health shows; the inline + standalone photos render their images; the empty-state does NOT show (there is history). **Zero page errors / error-level console output** across load + render (TEST-010; warnings ignored) |
| A-2 | reachable from the list + back link works | from the plants list, click the plant's link -> lands on `/plants/{id}`; click back -> returns to the list | navigation works end-to-end on the built SPA; no console errors on either transition |
| A-3 | empty-state on the production path | open `/plants/{id}` for a plant with no history | the empty-state renders (no crash, no spinner-forever); zero console errors |

**Breakpoints:** A-1 runs at **both locked breakpoints** - phone **390 px** and desktop
**1280 px** (the two that bracket the responsive range; the precedent set carries
390/820/1280). The journey + assertions are identical at each width; no horizontal scroll
at 390 (FE-011).

**FE-012 design-review screenshots (committed, required evidence).** Captured at the
locked breakpoints and committed to `specs/changes/care-timeline/screenshots/` (the folder
exists, currently a `.gitkeep`). Enumerated required files:

- `timeline-phone-390.png` - the timeline page at 390 px (a mixed-history feed: the four
  event types + an inline photo + a standalone photo).
- `timeline-tablet-820.png` - the timeline page at 820 px.
- `timeline-desktop-1280.png` - the timeline page at 1280 px.
- `timeline-empty-390.png` - the empty-state at 390 px (a plant with no history).

These are FE-012 design-review evidence (deliberate, curated, committed) - distinct from
TEST-011 failure-capture screenshots (ephemeral, never committed).

### 8a. FE-015 Audit Spaces (per-story mandatory)

US-3.4 ships UI, so the two Audit Spaces are asserted (no opt-out justification in the
proposal):

| # | test | asserts |
|---|---|---|
| A-4 | **a11y space** - axe-core scan + FE-011 | an axe-core scan of `/plants/{id}` (with a populated feed AND the empty-state) reports no violations; the back link has an accessible name; every entry's photo `<img>` has meaningful `alt` text; per-event-type markers are not color-only (FE-011 - distinguishable by label/icon, not hue alone); tap targets >=44x44 px; no horizontal scroll at 390 px |
| A-5 | **perf-budget space** - FE-007 | the production bundle-size budget holds (the FE-007 CI/test assertion); adding the `/plants/:id` page + `CareTimeline` must not regress past the budget |

A-5 is the existing repo-wide budget assertion (the timeline page adds a thin route +
component); the re-audit checks it is enforced as a **test/CI assertion**, not merely a
build warning (FE-015). A-4's color-not-only-marker check is the a11y teeth of the
"distinct per event type" requirement (F-4 proves distinctness; A-4 proves it is
accessible).

---

## 9. AC traceability (TEST-015) - every AC -> ≥1 named case

| AC | scenario | covering cases |
|---|---|---|
| **AC1** | events + standalone photos merged newest-first; backdated events sort by `happened_on` not creation time | `B-I1` (merge order), `B-I2` (backdated by happened_on), `B-I4` (same-day tiebreak), `B-I9` (all event types), `B-U1`-`B-U5` (merge unit, if factored); `F-8` (FE preserves order) |
| **AC2** | event with an attached photo emits one entry (photo inline); that photo never a separate `kind:photo` entry | `B-I6` (dedup, one entry), `B-I7` (linked + standalone mix), `B-I8` (shared photo_id edge), `B-U1` (merge unit); `F-5` (inline render) |
| **AC3** | a standalone photo (no event link) appears as a `kind:photo` entry at its date | `B-I3` (standalone emits), `B-U2`/`B-U3` (merge unit); `F-6` (FE renders the photo entry). **[Residual flip: events-only -> assert absent; §3 switch]** |
| **AC4** | missing plant -> 404 (plant-reason, no PII); bounded query count regardless of history size; runs on SQLite + Postgres | `B-I11`/`B-I12` (404 plant-reason, no PII, guard-first), `B-I13` (bounded query count N/2N), `B-I17` (dual-engine merge order, ARCH-011) |
| **AC5 (FE)** | all four event types render distinctly; observe shows health; photos render inline; empty state; the `/plants/{id}` page reachable from the list | `F-4` (distinct types), `F-5` (observe health + inline photo), `F-6` (photo entry), `F-7` (empty state), `F-10`/`F-12` (route reachable from the list), `F-11` (back link); `A-1`/`A-3` (production path) |
| **AC6 (FE)** | verified on the production path (built SPA through the backend), phone + desktop, zero console errors; screenshots committed (FE-012) | `A-1` (production path, zero console errors, both breakpoints), `A-2` (navigation), `A-4` (a11y), `A-5` (perf); FE-012 screenshots (§8) |

No AC is uncovered. Every numbered case maps to an AC, pins the response contract (§7:
`B-I14`/`B-I15`/`B-I16`), the dual-engine portability (§5: `B-I17`), the N+1 bound
(`B-I13`), or the discriminated-union client map (`F-2`).

---

## 10. Mocking boundary (TEST-003) - explicit

- **Backend integration (`test_timeline_endpoint.py`, the cross-engine test):** real DB
  through the real composition root; nothing internal mocked. Events/photos seeded via the
  real services/endpoints. The 404 guard is exercised against the real plant table.
- **Backend unit (`test_timeline_merge.py`, optional):** the pure merge over plain
  `CareEvent`/`Photo` value objects + the `linked` id set. No app, no DB, no I/O. `date`s
  built explicitly (no real clock).
- **Dual-engine:** real engines (SQLite local, Postgres CI), real SQLAlchemy.
- **N+1 capture:** a SQLAlchemy `before_cursor_execute` listener counting real statements
  on a real counting engine (the `_count_statements` helper from
  `test_plant_list_nplus1.py`) - it observes, it does not mock.
- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. Component +
  page tests render the real components (RTL); routing via a memory router.
- **Acceptance (Playwright / live smoke):** the built SPA served through the **real
  backend** + real DB (the production path); nothing mocked - the render depends on the
  real merged read.

---

## 11. Mutation probes (story-complete re-audit) - sanctioned, restored byte-identically

At story-complete, the test-engineer runs sanctioned mutation probes on the four
critical-100% paths (§8/§1), logging each (file, mutation, failing test), restoring
byte-identically, and verifying `git status` clean. The orchestrator independently
verifies the clean tree. Mutation evidence outranks assertion-reading on these paths.

| critical path | file (lane finalizes the exact path) | mutation | test that MUST go red |
|---|---|---|---|
| 1. event-photo dedup | `backend/src/viridarium/application/timeline.py` | drop the `if photo.id not in linked` filter (emit a `kind:photo` for EVERY photo, including linked ones) | `B-I6` (entry count would be 2, the linked photo also a `kind:photo`) + `B-U1` (if the merge unit is factored) |
| 1b. dedup set source | `timeline.py` | build `linked` from `[]` (never populate it) so no photo is ever deduped | `B-I6`/`B-I7` (the linked photo P appears as a `kind:photo` entry) |
| 2. backdated sort key | `timeline.py` | sort events by `created_at` instead of `happened_on` (use the wrong date for the sort key on event entries) | `B-I2` (the backdated event would sort to the top instead of its `happened_on` slot) + `B-U4` (merge unit) |
| 2b. tiebreak determinism | `timeline.py` | drop the `created_at` secondary sort key (sort by `date` only) | `B-I4` / `B-U5` (the same-`date` order becomes nondeterministic / wrong) |
| 3. missing-plant guard | `timeline.py` | delete the `plant_exists` guard / the not-found raise (let a missing plant fall through to an empty merge) | `B-I11` (would return 200 `[]` instead of 404) + `B-I12` |
| 4. union shape contract | `backend/src/viridarium/adapters/inbound/web/...timeline schema/router` | add `stored_filename` (or another field) to the nested photo object, OR drop the `kind` discriminator | `B-I14`/`B-I15` (the exact key-set assertion goes red - extra key or missing `kind`) |
| (FE) distinct event types | `frontend/src/features/plants/CareTimeline.tsx` | render the same marker/label for two event types (collapse the per-type switch) | `F-4` (two types would share a marker) |

The exact adapter/application file paths are the backend lane's to finalize (the design
names `application/timeline.py` for the service and `adapters/inbound/web` for the
schema+router); the re-audit locates the implemented file and probes the named behaviour.

---

## 12. Required test markers + file-size (TEST-012, QG-009)

Module-level `pytestmark` on every new/edited Python test file:
- `test_timeline_endpoint.py` -> `pytestmark = pytest.mark.integration`
- `test_timeline_merge.py` (if the optional pure-merge unit slice is added) ->
  `pytestmark = pytest.mark.unit`
- `test_fk_cross_engine.py` (edited) -> already `pytestmark = pytest.mark.integration`

Frontend `*.test.ts(x)` run under vitest (no marker); the acceptance smoke runs on the
production path (TEST-009/010). File-size: keep each test file under the QG-009 **500-LOC
hard max**; if `test_timeline_endpoint.py` grows past it, split by group (merge/order /
dedup / event-type pass-through / missing-plant + contract / bounded-count). **No
`test_migrations.py` edit** (no migration, §2); **no edit to the events/photos endpoint
tests** (their write paths are out of scope, §13/PRIN-IV).

---

## 13. TEST-014 - Test-first evidence (the red), per lane

Each lane records in `worklog.md` the **failing run that precedes the implementation** -
the test names plus the failing assertion/error output (the "red") - before the green
commit:

- **Backend lane red:** run `test_timeline_endpoint.py` (+ the optional merge unit + the
  cross-engine addition `B-I17`) against the *unimplemented* code -> expect
  collection/import errors (no `application.timeline`, no `TimelineQueryService`, no
  `/api/v1/plants/{id}/timeline` route, no timeline response schema). Capture the names +
  the first failing line per group.
- **Frontend lane red:** run `timeline.test.ts` + `CareTimeline.test.tsx` +
  `PlantDetailPage.test.tsx` against the *unimplemented* `lib/api/timeline.ts` /
  `CareTimeline.tsx` / `PlantDetailPage.tsx` (the `/plants/:id` route is currently the `*`
  not-found placeholder) -> expect module-not-found / assertion failures. Capture the
  names + errors.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain.

**Build-pickup risks (carry into the next session):**
1. **Residual assumption (proposal §residual).** Confirm with the PO at pickup: standalone
   photos interleave (DEFAULT) vs events-only. §3 + `B-I3`/`B-U3`/`F-7` carry the explicit
   flip instruction; record the confirmed choice in the worklog before turning those cases
   green. The dedup invariant (`B-I6`) is unaffected either way.
2. **No committed-in-CI e2e harness exists** (project-wide systemic gap, flagged in the
   app-settings worklog, debt #63). The acceptance lane (§8) follows the standing pattern:
   a LIVE production-path browser smoke + committed breakpoint screenshots, NOT a
   `.spec.ts` running in CI. If the build agents try to "run the Playwright spec", there
   isn't one - they perform the live smoke and commit screenshots, exactly as
   plant-crud / care-events / app-settings did. (Standing up a CI e2e harness is out of
   THIS story's scope - it is debt #63.)
3. **Lane ordering / file ownership.** Backend lands first (the FE builds to the §7
   contract). The FE lane touches `App.tsx` (route), `PlantsPage.tsx` (the per-plant
   link), and new `features/plants/*` + `lib/api/timeline.ts` files. `PlantsPage.tsx` and
   `App.tsx` are shared-ish surfaces - if the BE lane has no reason to touch them
   (it doesn't), the lanes are disjoint; any mid-flight overlap halts the later lane
   (PRIN-VI).

---

## 14. Coverage targets (QG-002) - do not drop the floor

- **Overall floor 85%**; repo currently ~99% backend - this story **MUST NOT** drop the
  floor. New/changed code **>=80% diff-cover**.
- **Branch coverage:** **>=95% in domain + application** - the `TimelineQueryService`
  merge/dedup/sort branches (the `linked` membership fork, the event-has-photo fork, the
  empty-history path, the plant-exists guard) all exercised. **>=80% in adapters/outbound**
  (the router, the response schema serialization of both union arms).
- **Critical paths flagged 100%** (spec-flagged -> QG-002 100% required): the four of §11
  (dedup invariant, backdated-sort-by-`happened_on`, missing-plant-404-reason, union-shape
  contract). Mutation evidence outranks assertion-reading at story-complete (§11).
- Combined pytest run (unit + integration) scores the union (TEST-001); the integration
  endpoint slice + the optional merge unit clear the floor without brittle
  implementation-mirroring tests (TEST-004).

---

## 15. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this
foundation and issues the **test-foundation approval**, checking:

- Every surface in §1 has its happy + sad (TEST-005); matrix M-TL (§3) is present and
  **parametrized** with the named cells (TEST-007), either as the merge unit (§4f) or
  folded into the integration cases.
- The four **critical-100%** paths (§11) are exercised, and each survives a **sanctioned
  mutation probe** (dedup-filter drop, sort-key swap to `created_at`, guard deletion,
  union-shape widen) - each probe logged (file, mutation, failing test) and the tree
  restored byte-identically, `git status` clean.
- The dedup invariant holds: a linked photo appears inline exactly once and NEVER as a
  `kind:photo` entry (`B-I6`/`B-I7`/`B-U1`).
- The backdated event sorts by `happened_on` (`B-I2`/`B-U4`) and the same-`date` tiebreak
  is deterministic `created_at` desc (`B-I4`/`B-U5`).
- The missing-plant path is 404 with a `{"detail"}`-only plant-reason body and no PII,
  guard-first (`B-I11`/`B-I12`).
- The response shape is exactly the §7 discriminated union (event/photo key-sets,
  `photo:{id,url}` only, no `stored_filename` leak) at the endpoint (`B-I14`/`B-I15`) and
  additive-only in OpenAPI (`B-I16`); the FE client maps the union on `kind` (`F-2`).
- The bounded query count is asserted as a **constant statement count across N/2N**
  (`B-I13`) - not eyeballed; the merged read ran on **both engines** (`B-I17`, ARCH-011).
- The **residual assumption** is recorded as PO-confirmed in the worklog, and
  `B-I3`/`B-U3`/`F-7` assert the matching direction (interleave-present DEFAULT, or
  events-only-absent on the flip).
- The frontend renders each event type distinctly (`F-4`), observe health + inline photo
  (`F-5`), the photo entry (`F-6`), the empty state (`F-7`); the `/plants/:id` route is
  reachable from the list (`F-10`/`F-12`) with a working back link (`F-11`).
- The acceptance smoke ran on the **production path** (built SPA through the backend) with
  **zero console errors** at **both breakpoints** (`A-1`/`A-2`/`A-3`, TEST-009/010);
  FE-012 screenshots committed (§8); the FE-015 a11y + perf spaces asserted (`A-4`/`A-5`).
- **No migration** authored, **no new repository method** added, **no events/photos write
  path** changed (scope, PRIN-IV / SPEC-001).
- Every AC1-AC6 maps to a named implemented test (§9, TEST-015); the TEST-014 red is
  recorded per lane (§13); markers (§12) present; the suite is parallel-safe (TEST-006)
  with per-test seeding and explicit dates (no real-clock dependence).

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the SEC-010
end-of-feature security review.
