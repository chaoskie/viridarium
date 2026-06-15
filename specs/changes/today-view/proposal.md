# Proposal - today-view (US-4.1)

Status: in progress. Story US-4.1 "Today view" - the v0.1 payoff. Spec: product-spec §4
US-4.1. Depends on US-3.3 (due data) + US-3.2 (event logging) - both merged. Completes
the v0.1 feature scope (then the release gate: cut v0.1.0).

## Story (SPEC-004)

As a plant owner, I open the app and know in five seconds what needs water or feed today,
and I log it in one tap, so that daily care is effortless and away-from-desk friendly.

## PO-resolved UX decisions (2026-06-15)

1. **Layout**: grouped by location, overdue styled inline. One section per location
   (homeless plants get their own "No location" group, D-009). Within each group, plants
   needing attention are listed most-overdue-first; overdue entries carry a distinct
   style + "N days overdue" badge, due-today a neutral "due today" badge.
2. **Data source**: frontend-only over the existing `GET /api/v1/plants` (already returns
   per-schedule `next_due`/`overdue_days` + `location_id` from US-3.3, N+1-safe) plus
   `GET /api/v1/locations` for names. No new endpoint; the machine-readable
   `/api/v1/due` stays US-5.2 (v0.2). **US-4.1 is frontend-only.**
3. **One-tap model**: one card per plant; a **Water** and/or **Feed** button for each care
   type currently due; **plus a "Both" button when both are due** (logs both for today).
   A tap logs the CareEvent(s) (`happened_on` = today) via the existing events endpoint
   and the card updates live - the satisfied care type drops, and the card leaves the
   list when nothing is left due. Backdate / note / observe still go through the existing
   log modal (US-3.2).

### Deferred (filed as candidate #66, NOT this story)

Per-plant **feeding mode** (liquid feed couples watering vs solid feed tracked separately).
Until ratified, US-4.1 treats water and feed as independent; the "Both" button logs two
independent events. When #66 lands, a liquid-mode feed will also cover water and the UI
adjusts. No coupling logic in this story.

## What "needs attention today" means (derived client-side)

For each plant, for each **enabled** schedule entry returned by the API: it needs attention
when `next_due <= today` - i.e. `overdue_days > 0` (overdue) OR (`overdue_days == 0` and
`next_due == today`, due today). `next_due == null` (paused/dormant) is never due. A plant
appears if any of its schedules needs attention; the card shows a per-care-type button only
for the care types that do.

## Frontend (UI story - FE-012 screenshots, TEST-010 production path)

- Add `schedules: ScheduleDue[]` (`{care_type, next_due, overdue_days}`) to the frontend
  `Plant` type (the API already returns it; only the type + consumption are new here).
- `TodayPage` (replace the walking-skeleton placeholder): fetch plants + locations; derive
  the due/overdue set; group by location (homeless own group); sort groups by location
  name, entries most-overdue-first; render cards with the one-tap actions; **empty state**
  celebrating "nothing due" when the set is empty; phone-first, one-handed.
- One-tap actions reuse the existing `careEvents` client (`POST /plants/{id}/events`,
  type=water|feed, happened_on=today); on success, refetch or locally update so the card
  reflects the new due state without a full reload.
- Reuse existing card/badge/Button recipes; no new heavy dependency.

## Out of scope (SPEC-001)

The Upcoming/7-day view (US-4.2), the plant detail page (US-4.3), the `/api/v1/due`
endpoint (US-5.2), snooze/skip (US-3.6), bulk "mark all in a location" (US-3.7), the
feeding-mode coupling (#66). No backend change (no endpoint, no migration, no contract
change). The existing log modal is unchanged.

## Acceptance criteria

- **AC1**: due + overdue plants are grouped by location; homeless plants form their own
  group; groups render in a stable order.
- **AC2**: overdue entries are visually distinct and show the correct days-overdue count
  (matches `overdue_days` from US-3.3); due-today entries show a neutral due badge; within
  a group, most-overdue sorts first.
- **AC3**: a card shows a one-tap button per due care type; a "Both" button appears only
  when both water and feed are due; tapping Water/Feed/Both logs the event(s) for today and
  the card updates without a full page reload (the satisfied type drops; the card leaves
  when nothing is due).
- **AC4**: paused/dormant (`next_due == null`) and future (`next_due > today`) schedules do
  not appear; archived plants do not appear (the API already excludes their due).
- **AC5**: empty state renders when nothing is due/overdue.
- **AC6**: verified on the production path (built SPA through the backend), phone + desktop
  breakpoints, zero console errors; screenshots committed (FE-012).

## Open questions

none. (Layout, data source, and the one-tap model incl. the "Both" button are PO-resolved;
the feeding-mode coupling is deferred to #66. Sort order and empty-state copy are recorded
design decisions.)
