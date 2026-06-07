# Proposal - ci-and-docker

## Summary

Deliver the two remaining E1 Foundation infrastructure slices from
`docs/product-spec.md` section 4 / section 7:

- **Story A - Quality gates: Makefile + GitHub Actions.** Mirror the already-green
  `make quality-gates` aggregate into GitHub Actions workflows (CI-001/002/005/006/007),
  add the cross-engine migration + integration check on both SQLite and PostgreSQL
  (ARCH-011), Conventional-Commit enforcement (LANG-002), a daily CVE audit
  (CI-005 / SEC-009), full-history secret scanning, release-please changelog/release
  automation (CI-008), and a multi-arch GHCR publish on release (CI-006/007, SEC-012).
- **Story B - Docker image + compose quickstart.** A multi-stage Dockerfile that builds
  the frontend, resolves backend deps with uv, and ships a slim non-root Python 3.12
  runtime that serves the FastAPI API and the built SPA from one container with a SQLite
  `/data` volume (product-spec section 7); a README-grade `docker-compose.yml`; a
  `.dockerignore`; and the README quickstart wired to the real compose file.

The GitHub repo does not exist yet (name pending), so the workflows are authored to be
correct by inspection with all actions pinned, and validated with `actionlint` where
available. The Docker image is built and smoke-tested locally.

## Scope (in)

### Story A
- `.github/workflows/quality-gates.yml`: PR + push-to-main; backend gate (uv + make
  targets), frontend gate (npm ci + make fe-* targets), cross-engine job running
  `alembic upgrade head` + integration tests against SQLite and a pinned
  `postgres:17-alpine` service container; gitleaks full-history scan; `concurrency`
  group cancelling in-progress runs on the same ref; uv + npm caches.
- `.github/workflows/commitlint.yml`: PR-title Conventional-Commit lint (squash-merge
  flow). See design for the action choice and rationale.
- `.github/workflows/audit.yml`: daily scheduled `pip-audit` + `npm audit` against the
  default branch (CI-005, SEC-009).
- `.github/workflows/release-please.yml`: release-please (simple non-monorepo) producing
  the release PR + tag/CHANGELOG (CI-008).
- `.github/workflows/publish.yml`: on published release, build and push a multi-arch
  (amd64 + arm64) image to GHCR with `docker/metadata-action` tags
  (`latest`, X, X.Y, X.Y.Z) and `attest-build-provenance`. Minimal per-job permissions.

### Story B
- Root `Dockerfile` (multi-stage: node FE build -> uv deps -> slim runtime), non-root,
  `/data` volume, HEALTHCHECK on `/api/v1/health`, OCI labels, base images pinned by
  digest (CI-006, SEC-012).
- Static-file serving in the FastAPI app for the built SPA with `index.html` fallback,
  added in the infrastructure layer to keep import-linter contracts green.
- Root `docker-compose.yml` quickstart with `/data` volume, port mapping, image
  placeholder + build fallback, commented Postgres block wiring `DATABASE_URL`.
- `.dockerignore`.
- README quickstart updated to the real compose content (OWNER/REPO placeholders kept).
- A test that `/` serves `index.html` when the static dir exists and is a no-op when it
  does not (the static change adds logic, so it gets coverage per the process note).

## Scope (out)

- Creating the GitHub repository or running the workflows in CI (repo name pending).
- Branch-protection configuration (a GitHub repo setting, documented as a follow-up).
- Playwright acceptance suite (CI-010) - not yet authored; referenced as a follow-up.
- diff-cover and OpenAPI drift gate (QG-002 / API-007) - the Makefile aggregate does not
  yet expose targets for these; wiring them is out of scope for this slice and flagged.

## Stack affirmation (PRIN-V / ARCH-001)

No stack amendment. GitHub Actions is the mandated runner (ARCH-001). Single multi-arch
container, SQLite default at `/data/app.db`, PostgreSQL via `DATABASE_URL` - exactly the
product-spec section 7 deployment shape. No new runtime components.

## Trust boundary (SEC-001)

The container default posture is safe for trusted-network deployment (SEC-012): non-root
user, no privilege escalation in compose, pinned digests (no floating `latest` base),
`/api/v1/health` is the only probe. Serving the SPA static files is a non-destructive
read with no PII. CORS/headers posture is unchanged from the scaffold (SEC-003/011); the
SPA is served same-origin so no CORS relaxation is needed.

## Accepted dependency advisory (SEC-009)

Inherits the existing **PYSEC-2026-161** Starlette accept-and-document entry from
`scaffold-backend` (justification + revisit 2026-09-01 inline in the Makefile). The CI
`audit` and per-PR security jobs run the same `make audit` target so the ignore policy is
applied identically. No new advisories introduced.

## Deviations (comply-or-explain, PRIN-X)

- **CI-010 (acceptance-gated promotion)** is not satisfiable yet: no Playwright suite
  exists (E1 has no UI flows beyond the skeleton). `publish.yml` triggers on a published
  release, which release-please only creates after the green required checks merge, so
  promotion is still gated on the mechanical gate. Acceptance gating is a follow-up when
  the Playwright suite lands. Flagged, not silently skipped (SPEC-001).
- **CI-002 diff-cover / OpenAPI-drift** targets do not exist in the Makefile yet; the CI
  runs every gate the Makefile exposes today. Adding those targets is tracked as a
  follow-up rather than improvised here (SPEC-001, PRIN-IX).
