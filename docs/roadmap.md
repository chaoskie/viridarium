# Roadmap

Status: v1, 2026-06-10. Companion to [product-spec.md](product-spec.md): the spec is the contract (what each feature is), this document is the sequencing (what ships when, and why in that order). Conflicts resolve in favor of the spec; scope refinements made here are flagged explicitly. The project board mirrors this document: modules map to epics, `Todo` holds the active phase, `Backlog` holds later phases, and every ticket carries a `Phase:` marker.

## Where we are (2026-06-10)

Delivered and merged to `main`:

- **E1 Foundation**: backend scaffold (FastAPI + SQLAlchemy + Alembic, hexagonal layout), frontend scaffold (React + TypeScript strict + Vite + Tailwind), quality gates (Makefile + GitHub Actions), Docker image + compose quickstart, release automation.
- **Theming and responsiveness** (pulled forward from the v0.3 "polish, theming" bucket): Roman theme as primary, dark theme, dual fallback themes, mobile-first responsive pass.
- **E2 Plant inventory complete**: US-2.1 plant CRUD + search/filter, US-2.2 location CRUD, US-2.3 photo upload/gallery/cover (shipped early; spec §5 had photos in v0.2), US-2.4 archive/unarchive.
- **US-3.1** per-plant water/feed schedule config (interval, winter interval, feed dormancy pause).

Snapshot: migrations 0001-0005, backend ~241 tests at 99.4% coverage, frontend 129 tests, CI green.

## Phase v0.1 - first usable

Goal: a plant owner can run one container, add plants and schedules, log care, and open the app to see what needs water today.

Ordered stories (each depends on the one before it unless noted):

1. **US-3.2 Log care events** - the append-only CareEvent history (water/feed/repot/observe). Must land first: due computation consumes events.
2. **US-3.3 Due computation** - the core rule (`next_due = last matching event + effective interval`). Read-side logic joining schedules, events, and the winter window.
3. **US-3.5 App settings: winter window** - the climate/winter-period settings US-3.3 reads. Until this lands, US-3.3 uses the spec default window (Nov 1 - Mar 1).
4. **US-3.4 Care history timeline** - events and photos interleaved per plant. Depends on US-3.2 only; can run parallel to US-3.5.
5. **US-4.1 Today view** - due/overdue grouped by location with one-tap logging. The v0.1 payoff.

Release-gate items (block the v0.1 tag, not the stories):

- **CSP bug**: backend-served SPA blocks Google Fonts and the inline theme pre-paint script. Must be fixed before any "usable" claim.
- **CI Node 20 deprecation**: bump `setup-uv` before 2026-06-16 (hard external deadline, falls inside this phase).
- **Cut v0.1.0**: sync version fields, tag, convert CHANGELOG `[Unreleased]`, per the ratified bump-gate policy.

Scope refinement vs spec §5: the spec lists all of E3 in v0.1. This roadmap takes the E3 core (US-3.2 through US-3.5) into v0.1 and moves US-3.6 (snooze/skip) and US-3.7 (bulk watering) to v0.2: both are conveniences layered on top of due computation, and neither is needed for the app to be usable. US-3.8 was already marked v1.5 in the spec.

## Phase v0.2 - dashboard complete + read API

Goal: the dashboard is finished and automations can read due-state without scraping.

- **US-4.2** Upcoming view (next 7 days)
- **US-4.3** Plant detail page (attributes, schedules, next-due, history, gallery in one place)
- **US-3.6** Snooze and skip on due tasks (the due-task action model)
- **US-3.7** Bulk: mark all due in a location as watered
- **US-5.1** REST API `/api/v1` + OpenAPI docs. Largely satisfied incrementally (every story ships its endpoints and the OpenAPI docs already serve); the remaining story is formalization: completeness check against the UI surface, doc polish, and the "everything UI-reachable is API-reachable" audit.
- **US-5.2** `GET /api/v1/due` endpoint (the automation poll)
- **US-5.3** ICS calendar feed (per instance and per location)
- **A11y contrast audit** across all themes (WCAG AA), folded into the FE gate

## Phase v0.3 - automation, hardening, polish

Goal: write-side automation, API guarantees, and the quality backlog.

- **US-5.4** Outbound webhooks on due/overdue transitions (retry/backoff, ntfy example)
- **US-5.5** API stability rules + contract test suite (additive-only within v1)
- **US-5.6** Full data export endpoint (JSON + photo archive)
- **Bulk plant location management** + orphaned/homeless plant handling (D-009 follow-up)
- **Phone layout polish**: floating/overflowing elements
- **Tech-debt burn-down**: upload body-size limit, CoverThumb N+1, PlantsPage decomposition, dual-engine integration harness, Modal focus-trap, filter-reset on mutation, 422 field heuristic, schema length-vs-trim

## Phase v1.0 - public-ready

Goal: optional species intelligence, complete docs, and the public listing.

- **US-6.1** Species provider port + Perenual adapter (fully optional, app works without a key)
- **US-6.2** Care-value suggestions on plant create (never auto-applied)
- **US-3.8** Suggested starting intervals from plant attributes (transparent lookup table)
- **Docs complete**: install, configuration, API guide, integration recipes (Home Assistant, ntfy, calendar)
- **awesome-selfhosted submission** (requires 4 months of public history; clock started June 2026)

Note: spec §4 tags E6 and US-3.8 as "v1.5" while spec §5 puts E6 in the v1.0 release. This roadmap follows §5 (they are v1.0 scope); the spec should drop the stale v1.5 tags on its next revision.

## Open product decisions (confirm at story pickup, never bake in silently)

Carried from the US-3.1 architect pass and the E3 handoff:

- **US-3.3**: water due in winter with no winter interval falls back to the normal interval; `paused` means "never due inside the window", not "due but suppressed". Confirm both.
- **US-3.5**: one global winter window per instance; month/day (year-agnostic, wraps new year) modeling; the climate-questionnaire UX shape.
- **US-3.6**: snooze is a schedule column (`snoozed_until`, added by its own migration); skip is a recorded event, not a schedule column. Confirm the split.
- **Care types** stay closed at water/feed for v1 (repotting is logged, never scheduled).
- **SEC-008 observability fork**: build a structured-logging/observability story and formally defer it, or accept status quo. Decision pending; see feature candidates.

## Feature candidates (unratified)

Ideas with a ticket on the board but no spec backing yet. Each needs PO ratification plus a spec amendment before it enters a phase.

- **Data import / restore**: the counterpart to US-5.6 export. Export without import is half a data-freedom story (restore after disaster, migrate between instances, seed from another tool). Natural phase: v0.3, alongside US-5.6.
- **Observability / structured logging**: resolves the SEC-008 gap as a real story (request logging with no PII, log levels, optional JSON output for log shippers) instead of piecemeal debt. Natural phase: v0.3.

Parked ideas (deliberately out of scope per spec §6, revisit only post-v1): weather-aware scheduling via the open API, MQTT/sensor ingestion, repot scheduling, native notifications (stay delegated to webhook/ICS consumers).

## Known bugs and tech debt

All tracked on the board. Severity-ordered register as of 2026-06-10:

| Item | Severity | Phase |
|---|---|---|
| CSP blocks Google Fonts + inline theme script when SPA served by backend | high | v0.1 gate |
| CI actions on deprecated Node 20 (deadline 2026-06-16) | low (time-boxed) | v0.1 gate |
| Upload body-size limit missing (defense-in-depth) | medium | v0.3 |
| SEC-008 structured logging gap | medium | v0.3 (or candidate story) |
| CoverThumb N+1 on plant list | medium | v0.3 |
| PlantsPage component oversized | low | v0.3 |
| Dual-engine integration harness missing (ARCH-011 risk) | medium | v0.3 |
| Modal focus-trap + schema length-vs-trim | low | v0.3 |
| Filter-reset on mutation + 422 field heuristic | low | v0.3 |
| Photo upload writes the file to disk before the DB insert; a failure orphans the file | medium | v0.3 |
| Plant form accepts a decimal pot size; backend silently truncates it to an int | medium | v0.3 |
| Schedule GET/DELETE return a wrong-reason 404 when the plant itself is missing | low | v0.3 |

The last three rows come from the 2026-06-10 code review pass; each is filed as an individual bug ticket on the board with file/line evidence and a fix direction.
