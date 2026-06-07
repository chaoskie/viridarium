# Worklog - ci-and-docker

## Actor: delivery-agent (Claude)

### Baseline
- Verified `make quality-gates` green before any change (backend + frontend, all targets).
- Read required: CLAUDE.md, rules/cicd.md, rules/quality-gates.md, rules/security.md,
  Makefile, backend/pyproject.toml, frontend/package.json, docs/product-spec.md s7.
- Tooling: docker present; uv/npm/node present; `actionlint`/`gitleaks` NOT installed
  locally -> used `rhysd/actionlint` docker image for workflow linting.

### Story B - Docker (done first; backend change affects tests)
- Added `infrastructure/static.py` (`mount_spa` + `_SpaStaticFiles` with index.html
  fallback on 404), `Settings.static_dir`, wired `mount_spa` into `create_app` AFTER the
  API router so `/api/v1/*` always wins. import-linter contracts stayed green (the change
  is in the outermost infrastructure layer, imports no inner layer).
- Added `tests/integration/test_static_spa.py` (5 tests: no-op when absent, index at /,
  SPA fallback for deep routes, asset served, API precedence).
- First test run: deep-route fallback 404'd because stock `StaticFiles(html=True)` only
  serves index.html for the dir root. Fixed by subclassing to map 404 -> index.html
  (and ONLY 404; other statuses re-raise). Retry 1 -> green.
- Multi-stage Dockerfile (frontend-build / backend-deps / runtime). Base images pinned by
  digest (see report). Non-root uid/gid 10001, /data volume, HEALTHCHECK on
  /api/v1/health, OCI labels, uvicorn CMD.
- FINDING: `docker build` failed on `npm ci` - committed package-lock.json
  (lockfileVersion 3, produced by npm 11) is rejected by node:20's bundled npm 10 as
  out-of-sync (tinyglobby/picomatch tree). Confirmed npm 11 resolves it cleanly (0 vuln).
  Fix: pin `npm install -g npm@11` in the build stage AND the CI frontend/audit jobs.
  Lockfile itself is fine; it just needs npm 11. Did not regenerate/modify the lockfile.
- Built `plant-care:smoke`, ran with a /data volume on port 18000.
  - /api/v1/health -> {"status":"ok","version":"0.1.0"} (200)
  - / -> index.html (200 text/html); /plants/42 -> index.html (SPA fallback, 200);
    /assets/*.js -> 200 text/javascript
  - container user: uid=10001(app); security headers present on /
  - SQLite: /health does not touch the DB (in-memory probe), so the file is lazily
    created. Triggered a real connection as `app` -> /data/app.db created, app-owned,
    writable. Confirms the default DATABASE_URL + volume + non-root posture works.
  - Cleaned up container, volume, and throwaway images.
- `docker-compose.yml` (image placeholder + build fallback comment, /data volume,
  healthcheck, no-new-privileges, commented Postgres block + DATABASE_URL wiring).
  `docker compose config -q` validates.
- `.dockerignore` added (VCS, node_modules, venvs, caches, tests, specs, docs, dbs,
  secrets).
- README quickstart: replaced the empty yaml placeholder with the real compose content
  (OWNER/REPO kept as placeholders).

### Story A - GitHub Actions
- `quality-gates.yml`: backend / frontend / cross-engine (sqlite+postgres matrix) /
  gitleaks jobs; concurrency cancel-in-progress; uv cache via setup-uv, npm cache via
  setup-node. Cross-engine runs `alembic upgrade head` + `make test-integration` against
  both engines; postgres leg installs `psycopg[binary]` at job time (CI-only; not added
  to pyproject.toml) and uses a digest-pinned postgres:17-alpine service.
- `commitlint.yml`: PR-title Conventional-Commit lint via amannn/action-semantic-pull-
  request (squash-merge flow; documented rationale inline).
- `audit.yml`: daily cron + workflow_dispatch; `make audit` (pip-audit, same ignore
  policy) + `npm audit --audit-level=high`.
- `release-please.yml`: googleapis/release-please-action, release-type simple.
- `publish.yml`: on release published; QEMU+Buildx, GHCR login, metadata-action tags
  (latest, {{major}}, {{major}}.{{minor}}, {{version}}), multi-arch build-push, provenance
  + sbom + attest-build-provenance. Per-job minimal permissions (contents:read default;
  packages/id-token/attestations write only on publish).
- actionlint (docker rhysd/actionlint) -> 0 errors across all 5 workflows (includes
  shellcheck on run blocks).

### Final gate
- `make quality-gates` green. Coverage 98% total; static.py 93%; floor 85 satisfied.
- No git commands run (commit gating per QG-010).

### Circuit breaker
- One retry on a single failure (SPA fallback 404). Well under the 3-retry breaker.
