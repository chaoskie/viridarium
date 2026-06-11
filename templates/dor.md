# Definition of Ready

Run at propose-time (`/spec-propose`, `QG-011`). Every item posts PASS/WATCH/FAIL (`QG-004`); any FAIL stops intake; any WATCH records its caveat for the next retro.

1. [ ] **Approved to start** - the maintainer agrees this change should happen now
2. [ ] **Story format** - "As `<role>`, I want `<what>`, so that `<why>`" (`SPEC-004`)
3. [ ] **Sized & independent** - 1-3 days / ~400-500 LOC new logic; no blocking dependency on unfinished work; split proposed if larger (`SPEC-004`)
4. [ ] **Testable acceptance criteria** - each AC = input → observable outcome
5. [ ] **Dependencies known** - upstream/downstream impacts listed in the proposal
6. [ ] **Logging considered** - required events identified (`SEC-008`); trust-boundary/exposure impact noted (`SEC-001`)
7. [ ] **Architecture conform** - fits the hexagon/context layout (`ARCH-002/004`); dual-engine portable (`ARCH-011`); no hidden stack amendment (`ARCH-001`, PRIN-V)
8. [ ] **Estimate + responsibilities** - effort recorded; agent roles assigned (who specs, implements, reviews)
9. [ ] **Contract impact known** - OpenAPI delta drafted if any REST surface changes (`API-001`); breaking change → planning mode completed (`API-004`)
10. [ ] **Test-foundation** - authored or scheduled with the test-engineer subagent (`SPEC-003`)
11. [ ] **Worklog created** - `specs/changes/<change-name>/worklog.md` exists with first entry (`TRACE-001`)
12. [ ] **All mandatory artifacts scaffolded** - `proposal.md`, `design.md`, `tasks.md`, `worklog.md` exist (stubs acceptable at this gate), plus `screenshots/` for UI-touching stories (`SPEC-002`, `FE-012`). Applies equally when the change folder is created by hand instead of `/spec-propose`. *(Added 2026-06-11 retro: a hand-rolled change folder skipped design/tasks/screenshots; caught only at the review gate.)*
13. [ ] **Open questions zeroed** - every ambiguity and unknown in the change is enumerated in the proposal; each **scope-affecting** question was asked to the maintainer and answered **before** this gate passes; the proposal states `Open questions: none` explicitly (silence or an absent section is not a pass). Non-scope-affecting unknowns may stay listed as assumptions, each with the answer the work proceeds on. *(Added 2026-06-11, cross-pollinated from sibling-project retros: implementing past an unasked scope question is the most expensive class of rework.)*
