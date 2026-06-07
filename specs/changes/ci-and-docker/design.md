# Design - ci-and-docker

## Story A: GitHub Actions

### Workflow shape (CI-001)
Pipeline order lint -> test -> security -> build is realised across jobs.
`quality-gates.yml` carries lint+test+security for every PR and push to `main`; `build`
(the image) is intentionally deferred to `publish.yml` on release, because there is no
registry to push to on a PR and the multi-arch build is slow. The PR build correctness
is instead covered by the local docker smoke test in Story B and a buildx dry path is
out of scope (flagged). Each workflow declares a `concurrency` group keyed on
`${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true`.

### quality-gates.yml jobs
1. **backend** - `astral-sh/setup-uv` (built-in uv cache via lockfile) + `make
   backend-install lint format-check typecheck imports test-coverage audit`. Runs the
   identical Makefile targets so local == CI (CI-002).
2. **frontend** - `actions/setup-node` with `cache: npm` + lockfile path, then `make
   fe-install fe-lint fe-format-check fe-typecheck fe-test`.
3. **cross-engine** - matrix `engine: [sqlite, postgres]`. The `postgres` leg starts a
   `postgres:17-alpine` (digest-pinned) service with a healthcheck, exports
   `DATABASE_URL=postgresql+psycopg://...`, runs `alembic upgrade head`, then the
   integration test layer. The SQLite leg runs the same steps against the default URL.
   This satisfies ARCH-011 in CI (the migration test file already notes CI owns the
   Postgres path).
   - **psycopg dependency**: the backend does not yet declare a Postgres driver. To avoid
     mutating `pyproject.toml` for a non-runtime CI concern, the Postgres leg
     `uv pip install psycopg[binary]` into the synced venv at job time and is documented
     inline. Adding psycopg to the backend extras is a follow-up for when Postgres is a
     supported first-class runtime path in the image.
4. **gitleaks** - `gitleaks/gitleaks-action` with `fetch-depth: 0` for full-history secret
   scanning on PRs.

### commitlint.yml (LANG-002)
**Choice: PR-title lint via `amannn/action-semantic-pull-request`.** Rationale: the repo
uses squash-merge (one commit per PR -> the PR title becomes the squash commit subject),
so enforcing Conventional Commits on the *PR title* is the correct lever, lighter than
wiring commitlint over every WIP commit on the branch. Documented inline in the workflow.

### audit.yml (CI-005, SEC-009)
`schedule: cron` daily off-hours against `main`. Two jobs: `make audit` (pip-audit, same
ignore policy) and `npm audit --audit-level=high` in `frontend/`. Also `workflow_dispatch`
for manual runs.

### release-please.yml + publish.yml (CI-006/007/008, SEC-012)
- `release-please.yml`: `googleapis/release-please-action`, `release-type: simple`
  (non-monorepo, language-agnostic; the repo is polyglot py+ts so `simple` versions the
  whole repo and maintains root `CHANGELOG.md` from Conventional Commits - CI-008).
- `publish.yml`: triggers on `release: published`. `docker/login-action` to GHCR,
  `docker/metadata-action` to compute tags (`latest`, `{{major}}`, `{{major}}.{{minor}}`,
  `{{version}}`), `docker/setup-qemu-action` + `docker/setup-buildx-action` for arm64,
  `docker/build-push-action` with `platforms: linux/amd64,linux/arm64`, then
  `actions/attest-build-provenance`. Per-job permissions: `contents: read` everywhere,
  `packages: write` + `id-token: write` + `attestations: write` only on the publish job.
  Immutability (CI-007) is inherent: release-please never re-tags an existing version, and
  the build pushes the immutable version tags computed from that release.

### Action version pinning
Pinned to major-version tags (`@v4`, `@v5`, ...) per the task's "major versions or SHAs"
allowance. Major tags are the GitHub-recommended balance for first-party actions and let
Dependabot's `github-actions` ecosystem (already configured) bump them. Third-party
actions (gitleaks, semantic-pull-request, release-please) are also pinned to majors;
hardening to full SHAs is a documented follow-up if the security posture demands it.

## Story B: Docker

### Dockerfile stages
1. `frontend-build` (`node:20-bookworm-slim`@digest): `npm ci` + `npm run build` -> `dist`.
2. `backend-deps` (`ghcr.io/astral-sh/uv:python3.12-bookworm-slim`@digest):
   `uv sync --no-dev --frozen` into `/app/.venv` from the committed `uv.lock` (CI-006
   reproducibility).
3. `runtime` (`python:3.12-slim-bookworm`@digest): copy the venv + `src/` + the built
   `dist/`, create a non-root `app` user, `chown` `/data`, set `STATIC_DIR` env to the
   bundled SPA, `VOLUME /data`, `HEALTHCHECK` curl-less Python probe on
   `/api/v1/health`, OCI labels, `USER app`, run uvicorn binding `0.0.0.0:8000` (the
   container's documented deliberate bind per SEC-003 - the trust boundary is the host
   network/proxy, not the container).

### Static serving (infrastructure layer)
`create_app` gains an optional static mount. A new `infrastructure/static.py` exposes
`mount_spa(app, static_dir)`: if `static_dir` exists, it mounts a `StaticFiles(html=True)`
app at `/` with an SPA `index.html` fallback for client-side routes; if it does not exist
(dev/test default), it is a no-op so the API-only app is unchanged. `Settings` gains
`static_dir: str | None`. This lives in `infrastructure` (the outermost hexagon layer that
already owns app wiring), so import-linter's inward-only contract stays green - no domain
or application import is added. The API router is mounted *before* the catch-all static
mount so `/api/v1/*` always wins.

### compose + dockerignore + README
- `docker-compose.yml`: `image: ghcr.io/OWNER/REPO:latest` with a `# build: .` fallback
  comment, `ports: 8000:8000`, named `plant-care-data` volume at `/data`, healthcheck,
  and a commented `postgres` service + `DATABASE_URL` wiring block.
- `.dockerignore`: excludes VCS, node_modules, venvs, caches, tests, specs, docs, the
  local SQLite/db files - keeping the build context small and secrets out.
- README quickstart: replace the empty yaml placeholder with the real compose content
  (OWNER/REPO kept as placeholders since the project name is pending).

## Test impact
The static change adds branching logic, so it gets:
- a unit test that `mount_spa` is a no-op when the dir is absent and serves `index.html`
  when present (using a tmp static dir + TestClient), and
- that `/api/v1/health` still resolves with a static mount present (API precedence).
Coverage floor 85 and all existing gates must stay green (QG-001/002).
