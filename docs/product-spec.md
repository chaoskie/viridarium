# Product specification

Status: draft v1, 2026-06-07. This document is the product-level contract. Individual changes refine it through `specs/changes/<name>/` proposals; conflicts resolve in favor of ratified change specs.

## 1. Vision

A self-hosted, single-user houseplant tracker that knows what every plant needs and when, and exposes that knowledge to the rest of your home through an open API. No accounts, no cloud, one container.

The reminder problem is deliberately delegated: the app computes and publishes what is due (UI, ICS, webhooks, REST); your existing tools (calendar, Home Assistant, ntfy, task systems) do the notifying. We render a great dashboard, but we do not build a notification empire.

## 2. Users

- **The plant owner**: one person on a trusted network. Wants to know "what needs water today", log it in two taps, and see each plant's history.
- **The automation consumer**: Home Assistant, Node-RED, n8n, cron scripts, task-management services. Wants machine-readable due-state and event hooks without scraping.

## 3. Domain model

```
Location 1──* Plant 1──* CareSchedule
                  │ 1
                  └────* CareEvent
Plant *──0..1 SpeciesInfo (optional, cached from a pluggable provider)
```

### Plant
- `name` (required, the household name: "Monstera living room left")
- `species` (free text) + optional `species_info` link
- `location` (optional FK; a plant may be **homeless** - no location - as a deliberate first-class state, e.g. a dead plant kept for its history/photos. See D-009)
- `acquired_on` (optional date)
- `pot_size_cm`, `pot_material` (enum: terracotta, plastic, ceramic, self-watering, other)
- `light_level` (enum: dark, indirect, bright-indirect, full-sun)
- `notes` (markdown), `tags` (free-form list)
- `photos` (ordered; newest is the cover)
- `archived` flag (death/given away; history preserved, excluded from due computation)

### CareSchedule
One per care type per plant. Care types in v1: `water`, `feed`. (Repotting is logged as an event but not scheduled; intervals of 1 to 3 years with high variance make schedule support a later feature.)
- `interval_days` (required)
- `winter_interval_days` (optional; used during the winter window)
- `dormancy` behavior: during winter window, `feed` schedules can be `paused` (default for feed), `water` schedules use winter interval if set
- Winter window: configurable app-wide, default Nov 1 to Mar 1 (northern hemisphere; both dates configurable so southern hemisphere works)
- `enabled` flag

**Due computation (the core rule):** `next_due = date(last matching CareEvent) + effective_interval`. No matching event yet → due immediately (surfaces new plants). `overdue_days = today - next_due` when positive. Effective interval = winter interval when today is in the winter window and one is set; a paused schedule is never due during the window.

### CareEvent
The append-only history: `plant_id`, `type` (`water`, `feed`, `repot`, `observe`), `happened_on` (date, defaults today, backdating allowed), `note`, optional `photo`. `observe` events carry an optional `health` rating (`good`/`fair`/`bad`): a journal input, never aggregated into a judgmental score. Deleting is allowed (mistakes) but events are never auto-modified.

### Due-task actions (competitive lesson, 2026-06-07 recon)
A due task supports four actions: **done** (logs the event; next due recomputes from it, so doing it early or late self-corrects), **done with backdate**, **snooze** (shifts this occurrence by N days without logging care; stored as `snoozed_until` on the schedule), and **skip** (dismisses this occurrence; next due recomputes as if done, but no care event is logged and the skip is recorded). The schedule model stays transparent and user-editable at all times: the user always wins the argument with the algorithm. This is deliberate: the category leader's top complaint is uneditable frequencies, and the runner-up's loved feature is exactly this correction loop.

### Location
`name` ("Living room", "Office windowsill"), optional `notes`. Deleting an empty room
removes it directly. Deleting a room that still holds plants prompts the user to choose:
delete those plants too, move them (to an existing room or a new one created inline), or
leave them homeless (location cleared). The app never silently strands or deletes plant
history. See D-009; the plant-aware flow lands with the Plant story (US-2.1), since
locations are built first.

### SpeciesInfo (v1.5, optional)
Cached lookup from a pluggable provider (Perenual first candidate; provider behind a port, fully optional, app works 100% without a key). Never auto-overwrites user-set values; suggestions only.

## 4. Epics and stories

### E1 Foundation
Walking skeleton: FastAPI + React build, SQLite/Postgres via DATABASE_URL, Alembic migrations, hexagonal layout enforced by import-linter, quality gates in Makefile + GitHub Actions, Docker image, `/api/v1/health`.

### E2 Plant inventory
- US-2.1 CRUD plants with all attributes; list view with search/filter by location, tag, species.
- US-2.2 CRUD locations.
- US-2.3 Photo upload (filesystem storage, volume-mounted), cover photo, gallery per plant.
- US-2.4 Archive a plant (excluded from due, history retained).

### E3 Care schedules and logging
- US-3.1 Configure water/feed schedule per plant (interval, optional winter interval, feed dormancy pause).
- US-3.2 Log care events (quick action from list/dashboard: "watered today", with optional backdate/note/photo).
- US-3.3 Due computation per the core rule, exposed on every plant read.
- US-3.4 Care history timeline per plant (events + photos interleaved).
- US-3.5 App settings: winter window dates.
- US-3.6 Snooze and skip on due tasks per the due-task action model.
- US-3.7 Bulk action: "mark all due plants in a location as watered" (one tap after the watering round).
- US-3.8 Suggested starting intervals from plant attributes (pot size/material/drainage + light level), via a transparent lookup table; suggestions only, always editable. (v1.5)

### E4 Dashboard
- US-4.1 "Today" view: due and overdue plants grouped by location, one-tap logging.
- US-4.2 Upcoming view (next 7 days).
- US-4.3 Plant detail page: attributes, schedules, next-due, history, gallery.

### E5 Integration surface (the differentiator)
- US-5.1 REST API `/api/v1` for everything above, OpenAPI docs at `/api/v1/docs`.
- US-5.2 `GET /api/v1/due?on=<date>&location=<id>` : machine-readable due/overdue list (the endpoint an automation polls each morning).
- US-5.3 ICS feed per instance and per location (`/api/v1/calendar.ics?location=<id>`): future due dates as all-day events, subscribable from any calendar app.
- US-5.4 Outbound webhooks: configurable URL(s), fired on due/overdue transitions (daily evaluation) and optionally on logged events; JSON payload documented; retry with backoff; ntfy-compatible example in docs.
- US-5.5 API stability rules: versioned path, additive changes only within v1, contract tests.
- US-5.6 Full data export: one endpoint returning the complete dataset (JSON + photo archive). Your data is never stranded; this is a stated feature, not an afterthought.

### E6 Species lookup (v1.5)
- US-6.1 Pluggable species provider port + Perenual adapter behind an optional API key.
- US-6.2 Care-value suggestions (interval hints) on plant create, never auto-applied.

## 5. Release scope

- **v0.1 (first usable)**: E1, E2 (minus photos), E3, E4.1
- **v0.2**: photos, E4 complete, E5.1-5.3
- **v0.3**: E5.4-5.5, polish, theming
- **v1.0**: E6, docs complete, awesome-selfhosted submission (requires 4 months public history)

## 6. Out of scope (deliberate)

Accounts/auth/multi-user, social features/gamification/points, AI care advice and disease diagnosis (link out at most; reviewers call the in-app versions inaccurate), computed "care scores" (the health slider is a journal input, not a grade), opaque scheduling the user cannot override, aggressive repot/fertilize nagging (repotting is logged, not scheduled, in v1), live weather integration (seasonal modifiers give most of the value; weather can arrive later through the open API), native mobile apps, MQTT/sensor ingestion (possible later via the API; a sensor-driven trailing-window light/moisture model is a natural fit once ingestion exists), push notifications (delegated to consumers via webhooks/ICS), cloud sync.

## 7. Non-functional requirements

- Single Docker container, multi-arch (amd64 + arm64), SQLite default at `/data/app.db`.
- Works fully offline (no hard external dependencies).
- Responsive UI, usable one-handed on a phone (watering happens away from the desk).
- p95 < 200 ms for list/due endpoints with 500 plants on a Raspberry Pi class machine.
- All quality gates per `rules/` enforced in CI.
