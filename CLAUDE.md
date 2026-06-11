@rules/00-constitution.md

# Project Agent Instructions

This project runs a rules-driven, spec-first workflow. The **constitution** (`rules/00-constitution.md`, imported above and always loaded) holds the principles; the **topic files** in `rules/` hold the enforceable standards. Cite rules by ID (e.g. `TEST-003`); load a topic file when your task touches it - your agent definition names your required reading.

**Project:** Viridarium - an open-source, self-hosted plant care web app (plant inventory, per-plant watering/feeding schedules, and an open REST API for home-automation integration). Developed in public by a solo maintainer plus AI agents. **No user authentication in v1 by design** (trusted-network deployment, `SEC-003`).

## Operating constraints (every agent, every task)

- **Gate before advancing** - post an explicit PASS/WATCH/FAIL checklist before moving to a next phase/story; any FAIL halts, every WATCH caveat is worklogged and surfaces in the next retro (`QG-004`, PRIN-VIII).
- **Completion language is gate-bound** - never declare a story/phase/change "done", "complete", or "ready" before the matching gate checklist has been posted with results; until then, state what is pending ("implementation complete; review and DoD gates pending") (`QG-016`).
- **Circuit breaker** - stop and escalate after 3 retries on the same fix or 5 distinct test failures (`QG-007`). Report state; don't thrash.
- **Commit gating** - don't commit until the user confirms the change works, unless the running workflow explicitly opted into autonomous commits gated on a green DoD (`QG-010`).
- **Minimal changes** - only what the task requires; no drive-by refactors, renames, or formatting cascades (PRIN-IX). Formatters run on touched files only.
- **Worklog** - log significant steps (decisions, gate results, escalations, reviews, commits) to the change's `worklog.md` with actor attribution (`TRACE-001/003/006`).
- **Spec is the contract** - build only what the spec describes; flag gaps instead of improvising (`SPEC-001`, PRIN-IV).
- **Commits** - Conventional Commits, imperative ≤72 chars, work-item reference in footer, **no AI-attribution trailers** (`LANG-002`).
- **Secrets** - never read into context or edit `.env*`/credential files (`SEC-006`).
- **Dual-engine** - persistence and migrations must work on both SQLite and PostgreSQL (`ARCH-011`).

## Layout

- `rules/` - the rule library (single source of truth, IDs stable)
- `.claude/agents/` - subagent roles (test-engineer, code-reviewer, security-reviewer, scope-reviewer, triage)
- `.claude/commands/` - the workflow library (spec lifecycle, review, bug, td, pipeline-medic, retrospective)
- `templates/` - DoR, DoD, pull-request, worklog, bug-report, td-item
- `specs/changes/<change-name>/` - per-change artifacts (`proposal.md`, `design.md`, `tasks.md`, `worklog.md`); archived to `specs/archive/<change-name>/`
