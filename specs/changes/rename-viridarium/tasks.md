# Tasks - `rename-viridarium`

- [x] T1 Preflight: report toolchain, compare against repo pins, flag mismatches.
- [x] T2 `git mv backend/src/plant_care backend/src/viridarium`; clear stale `__pycache__`.
- [x] T3 Rewrite `plant_care` -> `viridarium` in all backend `.py` imports + test imports.
- [x] T4 Backend prose strings: package docstring, FastAPI title, static-SPA test fixture
      + assertions.
- [x] T5 `pyproject.toml`: name, description, packages, mypy overrides, import-linter
      root + per-file-ignores, coverage source/omit.
- [x] T6 `alembic.ini` header + `script_location`.
- [x] T7 Regenerate `uv.lock` (`uv lock`).
- [x] T8 Makefile: header, typecheck path, `--cov`, `uvicorn` dev target.
- [x] T9 Dockerfile: header, OCI title + source URL, `CMD` uvicorn target.
- [x] T10 docker-compose.yml: service / container / image / volume names + comments.
- [x] T11 README.md: title, wink line, ghcr image, compose snippet, placeholder prose.
- [x] T12 backend/README.md + frontend/README.md product-name mentions + theme key.
- [x] T13 Frontend: package.json + package-lock.json name, index.html title + inline key,
      AppShell wordmark, themeController key, client comment.
- [x] T14 `.github/ISSUE_TEMPLATE/config.yml` Discussions URL; `publish.yml` image name.
- [x] T15 CLAUDE.md project line.
- [x] T16 Gate: `make quality-gates` (backend + frontend) green.
- [x] T17 Gate: `docker build` + smoke test (health ok, SPA wordmark) + cleanup.
- [x] T18 Gate: tracked-file grep shows no `plant_care` / `plantkeep`; list survivors.
- [x] T19 Screenshot to `docs/design/themes/implemented-viridarium.png`.
