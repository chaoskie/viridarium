# Proposal - app-settings (US-3.5)

Status: in progress. Story US-3.5 "App settings: winter window + global seasonal toggle".
Spec: product-spec §3 (Seasonal-aware care toggle + Winter window) + §4 US-3.5, **PO-ratified
2026-06-13** (the global toggle was a candidate; ratified and spec-amended this change).
Replaces the hardcoded default winter window that US-3.3 reads.

## Story (SPEC-004)

As a plant owner, I want one settings page where I turn seasonal-aware care on or off and
set my own winter window (with a reset to the default), so that the app's due dates match my
climate and my preference instead of a fixed northern-hemisphere assumption.

## Ratified decisions (the scope-affecting calls, locked with the PO 2026-06-13)

1. **Seasonal-aware toggle is ON by default** - preserves the behaviour US-3.3 shipped; no
   change for existing data.
2. **Toggle OFF = ignore BOTH winter interval AND paused** - every schedule uses its plain
   `interval_days` year-round; per-schedule settings are retained, just not applied.
3. **US-3.5 build scope = settings only**: persisted app settings + a settings page (toggle,
   editable window start/end as month-day, "return to default" = Nov 1 - Mar 1) + wiring the
   due engine to read it. The season **indicator + info-bulb** dashboard UI stays board #61.
   **No climate questionnaire** (deferred; direct date inputs only).

## Domain / data

`AppSettings` - a singleton (one row, `id = 1`):
- `seasonal_aware: bool` (default `True`)
- `winter_window`: `start_month, start_day, end_month, end_day` (ints; month/day, year-agnostic,
  wraps the new year, both endpoints inclusive - same model US-3.3's `WinterWindow` already uses)
- `updated_at` (server-set)

Singleton handling: the settings repository `get()` returns the persisted row, or the spec
**default** (`seasonal_aware=True`, Nov 1 - Mar 1) when no row exists yet - so a fresh install
works with no seeding. `put()` upserts the single row. (No data-seeding in the migration: avoids
cross-engine seed quirks, ARCH-011.)

## Migration

`0007_create_app_settings`: `app_settings` table; runs + rolls back on SQLite **and** PostgreSQL
(ARCH-011). No row seeded (lazy default in the repo).

## Due-engine wiring (the behaviour change)

US-3.3 left a `WinterWindowProvider` port with a hardcoded default impl. US-3.5:
- `compute_due` gains a `seasonal_aware: bool` parameter. When `False`, it ignores the window
  and `paused` entirely and returns the plain-interval due (`next_due = last + interval_days`,
  or today if no event; never null). When `True`, behaviour is exactly as shipped.
- A new settings-backed provider supplies both the window **and** the `seasonal_aware` flag;
  `DueQueryService` reads it once per query (not per plant - the N+1 bound is preserved) and
  passes the flag into `compute_due`. The hardcoded default provider is replaced in the factory.

This is the only change to US-3.3 code: an **additive** parameter + one new branch + the provider
swap. No change to the response contract shape (`schedules` field unchanged).

## API (API-001, additive; no breaking change)

- `GET /api/v1/settings` -> 200
  `{seasonal_aware: bool, winter_window: {start_month, start_day, end_month, end_day}}`
  (returns the lazy default when unset).
- `PUT /api/v1/settings` body = same shape -> 200 updated. Validation (422 on bad input,
  ids/enums only, no PII): months 1-12; days valid for the month ignoring leap-year
  (Feb allows 1-29; reject Feb 30, Apr 31, etc.); `seasonal_aware` a bool.

## Frontend

- New `/settings` route + nav entry. A settings page (Pico CSS, existing patterns):
  - the seasonal-aware on/off toggle;
  - window **start** and **end** as month + day inputs;
  - a **"Return to default"** button (fills Nov 1 - Mar 1; does not touch the toggle);
  - save -> `PUT /settings`; load -> `GET /settings`; inline success/error feedback.
- `lib/api/settings.ts` client mirroring existing slices.
- Breakpoint screenshots committed (FE-012); verified via the production path (built SPA served
  through the backend, zero console errors, TEST-010).

## Out of scope (SPEC-001)

The season indicator + info-bulb (#61); any per-location or per-plant window override; the climate
questionnaire; multiple windows; weather. No change to CareSchedule/CareEvent or their endpoints.

## Acceptance criteria

- **AC1**: `GET /settings` on a fresh install returns `seasonal_aware=true` + Nov 1 - Mar 1.
- **AC2**: `PUT /settings` persists a new window + toggle; a follow-up `GET` returns them; survives
  a process restart (real row, both engines).
- **AC3**: with the toggle **on** and today inside a user-set window, due uses the winter
  interval / paused exactly as US-3.3; with the toggle **off**, the same plant's due uses the
  plain `interval_days` and a `paused` schedule is due normally (no null).
- **AC4**: a southern-hemisphere window (e.g. May 1 - Sep 1, non-wrapping) classifies correctly;
  the default (Nov 1 - Mar 1) wraps the new year.
- **AC5**: invalid month/day (e.g. 13/01, 02/30) -> 422, no PII.
- **AC6**: the settings page loads current values, edits + saves them, "return to default" resets
  the window inputs; verified on the production path with zero console errors at both breakpoints.

## Open questions

none. (Scope-affecting decisions PO-ratified 2026-06-13 and spec-amended. Storage shape, lazy
default, validation rules, and the `compute_due` parameter are recorded design decisions.)
