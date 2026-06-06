# Pull Request - `<title>`

<!-- Severity language per REV-003. Use as the GitHub PR description. -->

## What
One paragraph. Link the change folder: `specs/changes/<change-name>/`.

## Why
The problem / story reference (work-item id, AC summary).

## How
Approach in 3-5 bullets. ADRs touched/created (`ARCH-010`). Contract changes + version impact (`API-004`).

## Test plan
Link the test-foundation doc (`SPEC-003`). What the Playwright acceptance suite covers (`TEST-009`). Confirm tests ran on both SQLite and PostgreSQL paths (`ARCH-011`). Anything intentionally untested + why.

## Risk
Blast radius, feature flags, data migration notes, affected API consumers, trust-boundary impact (`SEC-001`).

## Rollback
How to undo: revert strategy, Alembic downgrade (both engines), API version rollback (`API-004`, `CI-007`).

---

**Checklist**
- [ ] DoD green (`templates/dod.md`, `QG-012`)
- [ ] No open CRITICAL/HIGH findings (`REV-008`)
- [ ] GitHub Actions pipeline green (PRIN-VII)
- [ ] Conventional Commit history clean - no `wip` on the default branch, no AI-attribution trailers (`LANG-002`)
