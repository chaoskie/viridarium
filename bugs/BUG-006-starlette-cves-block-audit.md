---
title: pip-audit gate red on 4 starlette CVEs (pre-existing, blocks pipeline)
tags:
  - bug
  - security
  - pipeline
  - dependencies
status: open
severity: high
evidence: reproduced
created: 2026-06-16
related-change: unknown
work-item: "-"
---

### Observed behavior
`make audit` (the SEC-009 dependency-CVE gate, run in the `backend` job of
`quality-gates.yml`) fails with 4 unignored advisories in **starlette 0.49.3**:

```
starlette 0.49.3  CVE-2026-48818  Fix: 1.1.0
starlette 0.49.3  CVE-2026-48817  Fix: 1.1.0
starlette 0.49.3  CVE-2026-54283  Fix: 1.3.1
starlette 0.49.3  CVE-2026-54282  Fix: 1.3.0
```

### Expected behavior
`make audit` passes (or the advisories are explicitly ignored with a SEC-009
justification + revisit date, as PYSEC-2026-161 already is). PRIN-VII: the pipeline
must be green; a PR must not merge on a red `quality-gates`.

### Steps to reproduce
1. `make audit` (or `make quality-gates`) on `main`.
2. The `audit` target exits non-zero on the four starlette CVEs above.

### Root cause
**Pre-existing on `main`, not introduced by any feature branch.** starlette is a
transitive dependency of FastAPI; the resolved version (0.49.3) is whatever the
pinned FastAPI line (`fastapi>=0.119.0,<0.137.0`) admits. These are
recently-published 2026 advisories that pip-audit's database now reports against
the already-locked version - the surfacing is advisory-DB drift, not a version
change. Discovered while running the DoD gate for the `mobile-soak-fixes` batch
(which changed no backend code).

### Fix sketch (decision needed - not done here)
Two routes, both a backend/security call outside the mobile-soak scope:
1. **Bump.** `pyproject.toml` already allows `starlette>=0.49.1,<1.3.0`, so
   `starlette` 1.1.0 (fixes CVE-2026-48818/48817) is in range - but a `uv lock`
   bump is gated by what the installed FastAPI permits, and CVE-2026-54283/54282
   need >=1.3.0/1.3.1 (outside the current cap, likely needs a FastAPI bump too).
   Verify FastAPI+starlette compatibility, re-lock on both SQLite and PostgreSQL
   (ARCH-011), run the full suite.
2. **Justified ignore (SEC-009).** If each advisory is below the CVSS>7.5 block bar
   AND off the critical path for a no-auth, trusted-network app (SEC-003) - assess
   each CVE - add `--ignore-vuln` entries with an inline justification + revisit
   date, mirroring the existing PYSEC-2026-161 handling in the Makefile `audit`
   target.

### Acceptance criteria
- [ ] `make audit` is green on `main` (CVEs fixed or each explicitly justified-ignored
      with a revisit date).
- [ ] If bumped: lock works on SQLite **and** PostgreSQL; full backend suite green.

### Dedupe check
`bugs/` searched - none. Related to the existing accepted advisory PYSEC-2026-161
(starlette Host-header), documented in the Makefile `audit` target and
`specs/changes/scaffold-backend/proposal.md`.

### Context
- **Environment:** local + CI (`quality-gates.yml` backend job)
- **DB engine:** n/a (dependency advisory)
- **Version/commit:** f041608 (main); starlette 0.49.3 via fastapi <0.137.0
- **Surface:** dependency graph / CI audit gate

### Notes
Surfaced by, but unrelated to, the `mobile-soak-fixes` batch. That batch's PR will
show a red `audit` step for this reason until this ticket is resolved; the failure
predates the branch and touches no code it changed.
