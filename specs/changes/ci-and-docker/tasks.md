# Tasks - ci-and-docker

## Story A - GitHub Actions
- [x] A1 `quality-gates.yml`: backend + frontend + cross-engine (sqlite/postgres) jobs,
      gitleaks job, concurrency cancel-in-progress, uv + npm caches.
- [x] A2 `commitlint.yml`: PR-title Conventional-Commit lint (semantic-pull-request).
- [x] A3 `audit.yml`: daily scheduled pip-audit + npm audit on main.
- [x] A4 `release-please.yml`: release-please simple.
- [x] A5 `publish.yml`: multi-arch GHCR build+push on release, provenance attestation,
      minimal per-job permissions.
- [x] A6 Validate with actionlint if available; otherwise note.

## Story B - Docker
- [x] B1 `infrastructure/static.py` + `Settings.static_dir` + wire into `create_app`.
- [x] B2 Unit/integration test for static serving (no-op absent, index served present,
      API precedence).
- [x] B3 Multi-stage `Dockerfile` (digest-pinned), non-root, /data volume, HEALTHCHECK,
      OCI labels.
- [x] B4 `.dockerignore`.
- [x] B5 `docker-compose.yml` quickstart.
- [x] B6 Build image locally, smoke test (health, index at /, SQLite lands in /data).
- [x] B7 Update README quickstart with real compose content.

## Gate
- [x] G1 `make quality-gates` green at end.
- [x] G2 PASS/FAIL checklist posted.
