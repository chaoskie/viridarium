model: opus
summary: The genius of viridarium
---
# The genius of viridarium

## Domain
A self-hosted, single-user plant care app: plant inventory, per-plant watering and feeding schedules with a winter adjustment, and an open REST API (`/api/v1`) for home automation. Python (FastAPI, SQLAlchemy, Alembic) backend in a hexagonal layout, React and TypeScript frontend, one container, SQLite or PostgreSQL. It is pre-alpha and in active development; there is no login by design.

## Repo
- Remote: https://github.com/chaoskie/viridarium (public). Default branch: main. Merges: the genius opens the pull request and the maintainer merges.
- Docs: `AGENTS.md` first (operating constraints and the rule library in `rules/`), then `docs/roadmap.md`, `docs/product-spec.md`, `docs/decisions/`. Commits are Conventional Commits, imperative, at most 72 characters, no ticket references and no attribution trailers (`LANG-002`). The repo is public, so write nothing private into it.

## Tests
- Backend tests: `make test-coverage` (pytest, coverage floor 85). Layers alone: `make test-unit`, `make test-integration`.
- Lint and types: `make lint format-check typecheck imports` (ruff, mypy, import-linter boundaries). Frontend: `make fe-lint fe-format-check fe-typecheck fe-test`.
- `make quality-gates` runs all of it plus `make audit`. CI also runs the Playwright suite (`make fe-e2e`) and the integration tests against PostgreSQL.

## Lares
Only these serve here. The repo ships its own subagents in `.claude/agents/` (code-reviewer, scope-reviewer, security-reviewer, test-engineer, triage): where one covers the same job as a lar below, use the repo's own, since it knows the rule library.
- `lar-developer`: features and fixes in `backend/src/viridarium` (domain, application, adapters) and `frontend/src/features`, with migrations that work on both SQLite and PostgreSQL (`ARCH-011`).
- `lar-reviewer`: reviews every diff against the rules in `rules/` and the spec in `docs/product-spec.md`.
- `lar-architect`: changes to the hexagonal boundaries, the schema or the API contract; the outcome is written as a decision in `docs/decisions/`.
- `lar-tester`: stories with due-date, season or schedule logic (`domain/due.py`), planned against `rules/testing.md` before building.
- `lar-security`: the app is public and has no auth (`SEC-003`), so photo upload, outbound webhooks, the container image and new dependencies get an assessment.
- `lar-investigator`: failures that only show on one database or in the e2e device matrix.
