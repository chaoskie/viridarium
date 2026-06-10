# Testing (`TEST-*`)

**Enforces:** the test strategy for the locked stack ([[architecture#ARCH-001 — Stack lock|ARCH-001]]: Python/FastAPI/SQLAlchemy/Playwright/React) - the HoneyComb shape, the meaningful-test bar (the teeth of [[00-constitution#PRIN-III Test-First|PRIN-III]]), real-datastore discipline, the required unit/integration markers, and the Playwright acceptance format. Consumed by the test-engineer agent, developers, and the reviewer-gate.

Coverage *numbers* live in `QG-002`; the deterministic gate commands live in `quality-gates.md` and `cicd.md`. This file cites them, it does not restate them.

---

### TEST-001 — HoneyComb strategy (investment shape)
Integration tests are the **primary** layer: by default, cover behaviour with an integration test exercising a real slice (application + adapters + a real database). Write a **unit** test only for (a) genuinely complex or pure domain/application logic, or (b) branches/cells integration cannot economically reach. Keep **acceptance/e2e thin** (full journeys only).

This is **not** a pyramid-under-honeycomb: the coverage gate is met by **combined** coverage (pytest measures unit + integration together; the floor scores the union), so the integration bulk + targeted units clear the floor without the brittle implementation-detail unit tests the honeycomb exists to avoid.
*Targets:* test-engineer.

### TEST-002 — Layer definitions
- **Unit:** pure Python domain/application logic. No FastAPI app, no DB, no I/O.
- **Integration:** a slice through application + adapters against a **real database** (SQLite in-memory/file for the default path; a PostgreSQL service for the cross-engine path per ARCH-011) via real SQLAlchemy, FastAPI app wired through its composition root.
- **E2E / acceptance:** Playwright driving the running app against a real backend.
*Targets:* test-engineer, developers.

### TEST-003 — "What is real" (mocking boundary)
Integration tests use real internals and a real database. **Mock only true external dependencies** (third-party HTTP services, e.g. a home-automation consumer callback), via a stub/responses-style fake. Do **not** mock repositories, use cases, or the persistence layer inside integration/endpoint tests.
*Targets:* developers, test-engineer, reviewer-gate.

### TEST-004 — Meaningful-test bar (per test)
Every test must answer: (1) does it describe a user-meaningful scenario? - **yes**; (2) would it pass against a completely different implementation? - **no**; (3) is it redundant with another test? - **no**. Tests that mirror the implementation are noise ([[00-constitution#PRIN-III Test-First|PRIN-III]]).
*Targets:* test-engineer, reviewer-gate.

### TEST-005 — Happy + sad per surface
Each public surface (REST endpoint, use case, repository/domain method) has **≥1 happy** and **≥1 sad-path** test.
*Targets:* test-engineer, developers.

### TEST-006 — Test independence (parallel-safe & performant)
Every test passes **individually, in parallel, and chained**, in any order. No shared mutable state, no order dependence. Cleanup is scoped to rows the test created; never global truncation. The full suite is fast enough to run routinely.
*Targets:* developers, test-engineer.

### TEST-007 — Input-state matrices
A use case with **≥3 input dimensions OR ≥6 logical cells** gets an explicit input-state matrix with **named branch-priority order**, and parametrized tests (`pytest.mark.parametrize`) driven from it. (Complements TEST-005: the minimum pairing does not excuse untested combinations.)
*Targets:* test-engineer.

### TEST-008 — Codegen build-output assertion
Any gitignored generated/built artifact on the critical path (the OpenAPI schema FastAPI emits, any TypeScript client generated from it, the Vite production bundle) has a test that runs the generation/build and asserts on the **output content** (e.g. the emitted OpenAPI contains the expected paths/schemas).
*Targets:* developers, ci.

### TEST-009 — Acceptance tests in Playwright (always)
Acceptance/regression tests are **always** implemented in **Playwright**, even when the scenario is also exercised in other test phases. They drive real UI affordances - never bypass via direct value injection.
*Targets:* test-engineer, frontend.

### TEST-010 — Playwright console-error fail-on
E2E/acceptance **fail** on page errors and error-level console output; warnings are ignored. Any allowlisted pattern requires an inline justification comment.
*Targets:* test-engineer, frontend.

### TEST-011 — Snapshot testing
**DOM/HTML structural snapshots:** allowed and encouraged for stable markup. **Pixel/image screenshot baselines:** NOT used. **Failure-capture screenshots** (UI captured when a test breaks): allowed as ephemeral CI artifacts, **never committed** to the repo. (Distinct: *design-review evidence* screenshots ARE committed - see `FE-012`.)
*Targets:* test-engineer, frontend.

### TEST-012 — Required pytest markers
Every Python test file MUST declare its layer marker via a module-level `pytestmark`: `pytestmark = pytest.mark.unit` for unit tests, `pytestmark = pytest.mark.integration` for integration tests. The markers are registered in the pytest config and are not optional; a test file without a layer marker fails the gate. Frontend unit tests run under **vitest**.
*Targets:* developers, test-engineer, ci.

### TEST-013 — Binding coverage/quality gates (cite)
The suite MUST satisfy `QG-002` (overall coverage floor 85%; diff-cover 80% on new code; branch coverage targets per layer). Enforced deterministically in the Makefile and mirrored in CI (`cicd.md`).
*Targets:* reviewer-gate, ci, DoD template.

### TEST-014 — Test-first evidence (the red)
Test-first ([[00-constitution#PRIN-III Test-First|PRIN-III]]) is **auditable from artifacts, not trusted from a claim**. For each story (or lane), the build agent records the **failing-test run that precedes the implementation** in the change worklog: the test names plus the failing assertion/error output (the "red"), before the commit that turns them green. Coverage + a passing suite prove the tests exist and pass; this proves they were written first. A story whose worklog shows no red-before-green is a PRIN-III deviation requiring comply-or-explain. *(Added 2026-06-08, sprint-2 retro, closing the sprint-1 carry-forward.)*
*Targets:* developers, test-engineer, reviewer-gate, DoD template.
