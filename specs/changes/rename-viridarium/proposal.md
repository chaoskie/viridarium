# Proposal - `rename-viridarium`

## Problem

The project shipped under the working name `plant-care` (code package `plant_care`,
frontend wordmark `plantkeep`). Before the repository goes public it needs its final
public identity: **Viridarium** (GitHub `chaoskie/viridarium`, image
`ghcr.io/chaoskie/viridarium`). This is the last pre-publish change.

## Goal

A clean, consistent rename across code, build, CI, docs, and the UI wordmark, with no
stray `plant_care` / `plantkeep` references in shippable, tracked files. No personal info
beyond the GitHub handle `chaoskie` may appear.

## Scope

- Backend Python package `plant_care` -> `viridarium`: directory, all imports, pyproject
  (name, packages, mypy overrides, import-linter, coverage), `alembic.ini` script path,
  Makefile (`--cov`, `uvicorn` target, typecheck path), Dockerfile (`CMD`, OCI labels),
  tests, `uv.lock`.
- Frontend: `package.json` + `package-lock.json` name to `viridarium-frontend`,
  `index.html` `<title>` to `Viridarium` and the inline pre-paint theme key to
  `viridarium.theme`, AppShell wordmark `plantkeep` -> `virid`+`arium` (accent split),
  `themeController` storage key to `viridarium.theme`, client comment.
- README.md: title `Viridarium`, the viridarium wink line, `ghcr.io/chaoskie/viridarium`,
  compose-snippet names.
- docker-compose.yml: service / container / image / volume names to `viridarium`
  (volume `viridarium-data`).
- `.github/ISSUE_TEMPLATE/config.yml` Discussions URL; `publish.yml` image name.
- Dockerfile OCI title + source URL.
- backend/README.md, frontend/README.md product-name mentions; CLAUDE.md project line.

## Out of scope (DO NOT TOUCH)

`docs/design/themes/*.html` + `*.png` (historical artifacts, old wordmark stays),
`specs/changes/*` and `specs/retros/*` (history), `.claude/docs/` (local vault),
`CHANGELOG.md`, `LICENSE`.

## Deliberate survivors (generic, not the product name)

- `plantcare` as the optional PostgreSQL DB / user / password in `quality-gates.yml` and
  the commented compose block - a generic DB identifier, kept consistent across CI and the
  compose example, not the product name.
- Generic phrases like "plant care web app" / "houseplant care tracker" as descriptive
  prose (CLAUDE.md project line, OCI description, package descriptions).

## Acceptance

- `make quality-gates` green (backend + frontend).
- `docker build` succeeds; container starts, `GET /api/v1/health` returns `ok`, `/`
  serves the SPA showing the new wordmark.
- Tracked-file grep (excluding the do-not-touch list) shows no `plant_care` / `plantkeep`.
- One screenshot of the renamed app shell at
  `docs/design/themes/implemented-viridarium.png`.
