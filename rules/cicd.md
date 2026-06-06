# CI/CD (`CI-*`)

**Enforces:** the pipeline that gives [[00-constitution#PRIN-VII Pipeline Must Be Green|PRIN-VII]] its teeth - job layout, gate wiring (QG-001/002), supply-chain reproducibility, release immutability, and dependency automation. Runner: **GitHub Actions** (ARCH-001). Consumed by pipeline-medic, reviewer-gate, and CI itself. Every gate is a Makefile target run identically locally and in CI.

---

### CI-001 — Pipeline shape & merge gate
GitHub Actions workflow jobs: **lint → test → security → build**. The workflow is a required status check on the default branch (branch protection); concurrent runs on the same ref cancel in-progress (`concurrency` group). A red workflow blocks merge - no exceptions, no "pre-existing failures" (QG-006 / PRIN-VII). Pull requests, not merge requests.
*Targets:* ci, pipeline-medic, reviewer-gate.

### CI-002 — Pipeline runs the full mechanical gate
The workflow executes everything QG-001 requires, via the Makefile targets:
- **Python:** `ruff check` + `ruff format --check`; `ruff` security (`S`) rules; `mypy --strict` (domain + application); `import-linter` boundary contracts (`ARCH-003`).
- **Tests:** `pytest` unit + integration with combined coverage (floor 85%, QG-002) on **both** SQLite and PostgreSQL service paths (ARCH-011); `diff-cover` ≥80% vs the default branch (QG-002).
- **Frontend:** `eslint` (incl. FE-008 module-boundary rules) + Prettier check (FE-006); `tsc --noEmit` (FE-004); vitest unit tests.
- **Contracts:** exported-OpenAPI ↔ generated-artifact drift check (API-007, TEST-008).
*Targets:* ci, developers.

### CI-003 RETIRED (not applicable: no external SonarQube service)
The source ran SonarQube analysis per merge request. This project has no external code-quality service; per-PR quality is the Makefile gates (CI-002) run by GitHub Actions on every PR.

### CI-004 RETIRED (not applicable: no external Sigrid service)
The source ran Sigrid maintainability analysis per merge request. No equivalent here; see QG-014 RETIRED.

### CI-005 — Dependency CVE scanning
**`pip-audit`** scans Python dependencies, and the frontend dependency audit (`npm audit` / equivalent) scans JS dependencies, as a `security` job on every workflow run. Additionally a **daily scheduled CVE audit** runs against the default branch. Findings policy per `SEC-*`.
*Targets:* ci, security-reviewer.

### CI-006 — Reproducible builds
Lockfiles are committed: a Python lockfile (`uv.lock` / `requirements.txt` with hashes / `poetry.lock`) and `package-lock.json`. Any container base image is pinned by **SHA-256 digest**, not floating tags. Same source SHA + lockfiles ⇒ equivalent artifact.
*Targets:* ci, developers.

### CI-007 — Releases immutable
A released artifact/version is never overwritten - the pipeline **fails** on a duplicate release push (e.g. re-pushing an existing tag/version). Pre-release/dev artifacts MAY be overwritten. (Pairs with API-004 published-API stability.)
*Targets:* ci.

### CI-008 — Auto-changelog
The changelog is generated from Conventional Commits (`LANG-*`), grouped by type, committed to `CHANGELOG.md`, and included in the release. (The `CHANGELOG.md` and release tooling are owned by the repo-hygiene workstream; this rule mandates the source-of-truth is Conventional Commits, not hand-edits.)
*Targets:* ci, spec-archive.

### CI-009 — Dependency-update automation policy
Automated dependency updates (Dependabot / Renovate) run off-hours. **Auto-merge:** minor / patch / pin / digest updates (green workflow required). **Never auto-merge majors** - they get a reviewed PR. Vulnerability alerts are prioritized and labeled `security` + `dependencies`.
*Targets:* ci, td workflow.

### CI-010 — Acceptance-gated promotion
Promotion to a release requires a **passing Playwright acceptance suite (TEST-009)** against a running build. No release without green acceptance.
*Targets:* ci, DoD template.
