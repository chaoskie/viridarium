# Definition of Done

Run at archive-time (`/spec-archive`, `QG-012`). Every item posts PASS/WATCH/FAIL (`QG-004`); any FAIL blocks archive/merge; any WATCH records its caveat in the worklog for the next retro. Until this checklist is posted with results, the change is not "done" - completion language is gate-bound (`QG-016`).

## 1. Functional
- [ ] Every acceptance criterion met and verified (story-complete check)
- [ ] Demo step recorded / demo-able
- [ ] **Claims audit:** every security / logging / perf control the proposal *asserts* is actually implemented - or the proposal is corrected. No aspirational claims left standing. *(Added 2026-06-10, E2 retro: a proposal over-claimed SEC-008 logging.)*

## 2. Code Quality
- [ ] Mechanical gate green: ruff lint+format, ruff S, mypy strict (domain+app), import-linter boundaries (`QG-001`)
- [ ] Review verdict clean: no open CRITICAL/HIGH (`REV-008`); MEDIUM/LOW handed to `/td` (`REV-003`)
- [ ] Independent review evidenced: the reviewing actor in the worklog differs from the implementing actor (`REV-004`, `TRACE-006`)
- [ ] File ceilings respected or justified inline (`QG-009`)

## 3. Test & Validate
- [ ] Coverage: overall floor 85%; diff-cover ≥80%; domain/app branch ≥95% (`QG-002`)
- [ ] Required pytest layer markers present in every test file (`TEST-012`)
- [ ] Test-foundation re-audit **approved** by the test-engineer subagent (`SPEC-003`)
- [ ] Scenario-to-test traceability: every test-foundation scenario maps to a named implemented test or an explicit worklogged deferral; neither blocks (`TEST-015`) *(Added 2026-06-11, cross-pollinated from sibling-project retros.)*
- [ ] Test-first evidence: the failing run (the "red") is recorded in the worklog before the green commit (`TEST-014`)
- [ ] Empirical review done: red-verify of the new tests + ≥1 mutation spot-check on new wiring, run in a throwaway copy, outcomes in the worklog (`REV-010`)
- [ ] If the change adds or repairs a quality gate: bites-proof recorded - the gate demonstrably failed against the broken property in a throwaway copy (`QG-015`)
- [ ] No paper gates: every numeric/mechanical bar this change relies on is enforced by a tool that fails the pipeline on breach, and the enforced run's output is referenced here - never assumed (`QG-017`) *(Added 2026-06-11, cross-pollinated from sibling-project retros.)*
- [ ] Playwright acceptance green (`TEST-009`, `CI-010`); ran on both SQLite and PostgreSQL paths (`ARCH-011`)
- [ ] UI story: verified via the **production path** - built SPA served *through the backend* (not just vite dev / in-process TestClient), **zero page/console errors** (`TEST-010`). Catches CSP-class bugs (security headers vs external assets/inline scripts) invisible to dev-mode + API-only tests. *(Added 2026-06-08, sprint-2 retro.)*
- [ ] Audit Spaces green: a11y / perf (`FE-015`) + event-logging (`SEC-008`)

## 4. DevOps Ready
- [ ] Pipeline fully green (PRIN-VII)
- [ ] Logging operational for the new functionality; no PII in logs (`SEC-007`)
- [ ] Alembic migrations apply + roll back on both SQLite and PostgreSQL (`ARCH-011`); release immutability respected (`CI-007`)
- [ ] End-of-feature security review done if at a feature boundary (`SEC-010`)

## 5. Documentation
- [ ] **Artifact completeness:** every mandatory change artifact exists and is non-stub - `proposal.md`, `design.md`, `tasks.md`, `worklog.md`, test-foundation, plus `screenshots/` for UI stories (`SPEC-002`, `FE-012`). Existence is checked mechanically here so the review gate judges content, never absence. *(Added 2026-06-11 retro.)*
- [ ] Glossary updated for new domain terms (`LANG-007`); ADRs recorded (`ARCH-010`)
- [ ] Worklog complete (`TRACE-001`) + change-index entry written (`TRACE-002`)
- [ ] UI story: breakpoint screenshots committed as design evidence (`FE-012`)
- [ ] Story sign-off recorded (`QG-005`)
