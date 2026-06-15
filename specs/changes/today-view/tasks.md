# Tasks - today-view (US-4.1)

Single frontend lane (no backend). TDD, red-before-green (TEST-014). UI story: screenshots
+ production-path verification.

## Frontend lane (FE)

- [ ] FE-1 `lib/api/plants.ts`: add `ScheduleDue {care_type, next_due, overdue_days}` +
      `Plant.schedules: ScheduleDue[]` (additive; the API already returns it). Update Plant
      fixtures across existing tests under TS strict.
- [ ] FE-2 `features/today/buildTodayGroups.ts` (or co-located): the PURE derivation
      (filter attention set, card model with worstOverdue, group by location incl. homeless,
      order groups + cards). `today` injected.
- [ ] FE-3 `TodayPage`: replace the placeholder; load plants + locations, derive via
      buildTodayGroups, render groups/cards/badges, empty state, loading/error states.
- [ ] FE-4 `TodayCard` + one-tap: Water/Feed buttons per due care type + Both when both due;
      log via the careEvents client (happened_on=today); live card update (no full reload);
      in-flight disable + inline error.
- [ ] FE-5 unit tests for buildTodayGroups (grouping, sort, classification, null/future
      excluded, both-due, empty) + component tests (render, buttons-per-due-set, tap logs +
      updates, empty state, error).
- [ ] FE-6 breakpoint screenshots (FE-012); production-path verification, zero console
      errors (TEST-010).

## Gate (orchestrator)

- [ ] FE gate green (lint, prettier, tsc, vitest, build under budget).
- [ ] Three-reviewer gate + test-engineer re-audit.
- [ ] No backend change (verify the diff touches no backend file).
- [ ] Production-path screenshots committed.
