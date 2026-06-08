# Definition of Done

Run at archive-time (`/spec-archive`, `QG-012`). Every item posts PASS/FAIL (`QG-004`); any FAIL blocks archive/merge.

## 1. Functional
- [ ] Every acceptance criterion met and verified (story-complete check)
- [ ] Demo step recorded / demo-able

## 2. Code Quality
- [ ] Mechanical gate green: ruff lint+format, ruff S, mypy strict (domain+app), import-linter boundaries (`QG-001`)
- [ ] Review verdict clean: no open CRITICAL/HIGH (`REV-008`); MEDIUM/LOW handed to `/td` (`REV-003`)
- [ ] File ceilings respected or justified inline (`QG-009`)

## 3. Test & Validate
- [ ] Coverage: overall floor 85%; diff-cover ≥80%; domain/app branch ≥95% (`QG-002`)
- [ ] Required pytest layer markers present in every test file (`TEST-012`)
- [ ] Test-foundation re-audit **approved** by the test-engineer subagent (`SPEC-003`)
- [ ] Test-first evidence: the failing run (the "red") is recorded in the worklog before the green commit (`TEST-014`)
- [ ] Playwright acceptance green (`TEST-009`, `CI-010`); ran on both SQLite and PostgreSQL paths (`ARCH-011`)
- [ ] UI story: verified via the **production path** - built SPA served *through the backend* (not just vite dev / in-process TestClient), **zero page/console errors** (`TEST-010`). Catches CSP-class bugs (security headers vs external assets/inline scripts) invisible to dev-mode + API-only tests. *(Added 2026-06-08, sprint-2 retro.)*
- [ ] Audit Spaces green: a11y / perf (`FE-015`) + event-logging (`SEC-008`)

## 4. DevOps Ready
- [ ] Pipeline fully green (PRIN-VII)
- [ ] Logging operational for the new functionality; no PII in logs (`SEC-007`)
- [ ] Alembic migrations apply + roll back on both SQLite and PostgreSQL (`ARCH-011`); release immutability respected (`CI-007`)
- [ ] End-of-feature security review done if at a feature boundary (`SEC-010`)

## 5. Documentation
- [ ] Glossary updated for new domain terms (`LANG-007`); ADRs recorded (`ARCH-010`)
- [ ] Worklog complete (`TRACE-001`) + change-index entry written (`TRACE-002`)
- [ ] UI story: breakpoint screenshots committed as design evidence (`FE-012`)
- [ ] Story sign-off recorded (`QG-005`)
