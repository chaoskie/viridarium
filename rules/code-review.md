# Code Review (`REV-*`)

**Enforces:** the review gate - which reviewer roles run, how they execute, how findings are classified, and what blocks a merge. This is the operating spec for the reviewer agents and feeds the Pull Request template. Implements [[00-constitution#PRIN-I Code Quality|PRIN-I]], [[00-constitution#PRIN-IV Specs Are Exact Scope|PRIN-IV]], [[00-constitution#PRIN-IX Minimal Changes|PRIN-IX]].

Reviewers' *checks* cite `ARCH-*` / `SEC-*` / `TEST-*` - the rules live there (single source); this file defines roles, flow, and verdicts.

---

### REV-001 — Three reviewer roles
Every change is reviewed by three distinct roles before merge:
- **code-reviewer** - architecture, style, patterns (checks per REV-005/006)
- **security-reviewer** - OWASP-relevant risks, input validation, secure-by-default posture (checks per `SEC-*`)
- **scope-reviewer** - spec compliance: nothing missing, nothing extra (process per REV-007)
*Targets:* reviewer agents, pull-request template.

### REV-002 — Parallel execution, then consolidate
The three reviewers run **in parallel and independently** (no reviewer sees another's findings while reviewing - preserves perspective diversity). Findings are then **merged and deduped**; blockers are resolved; the gate verdict follows. Re-review after rework repeats the same parallel pattern.
*Targets:* reviewer-gate orchestration, review workflow.

### REV-003 — Finding severity & verdicts
Findings are classified **CRITICAL / HIGH / MEDIUM / LOW**. CRITICAL and HIGH MUST be fixed before merge; MEDIUM and LOW MAY be deferred (logged as tech-debt). Remark intent maps as: BLOCKING = CRITICAL/HIGH, ADVISORY = MEDIUM, NOTE = LOW.
*Targets:* all reviewers, pull-request template, td workflow.

### REV-004 — Independent reviewer
At least one full review pass MUST be performed by a reviewer (agent or human) that did **not** write the code under review. An implementer never solely approves their own change. **Auditable, not trusted:** the worklog records both actors (`TRACE-006`), and the reviewing actor MUST differ from the implementing actor - the DoD checks this mechanically. *(Amended 2026-06-11, cross-pollinated from sibling-project retros.)*
*Targets:* reviewer-gate, DoD template.

### REV-005 — code-reviewer mandatory checks (pointers)
The code-reviewer verifies compliance with, at minimum:
- `ARCH-*` - layer boundaries, module isolation, no business logic in routers, no persistence access outside adapters, dual-engine portability (ARCH-011)
- `SEC-*` - no injection vectors, no secrets in code, secure-by-default posture, no PII in logs
- `TEST-*` - no tautological tests (TEST-004), no mocked persistence in integration tests (TEST-003), required layer markers (TEST-012), file-size ceilings (QG-009)
The rules themselves live in those files; the reviewer cites violated IDs in findings.
*Targets:* code-reviewer.

### REV-006 — Seven review dimensions (embedded)
The code-reviewer addresses each dimension below that is not obviously fine. Source: Google's engineering practices review guide ("What to look for in a code review"), embedded here so the practice is self-contained even if the upstream changes.

1. **Design** - Is the overall design of the change sound? Do the pieces belong here (vs another module)? Does it integrate well with the rest of the system? Is now the right time to add it?
2. **Functionality** - Does the change do what the author intended, and is that good for the users (end users *and* future developers, *and* home-automation API consumers)? Edge cases, concurrency problems, user-visible behaviour.
3. **Complexity** - Is it more complex than it needs to be? Can a future reader understand it quickly? No over-engineering: don't solve problems that don't need solving now.
4. **Tests** - Are there appropriate tests (per `TEST-*`)? Are they correct, sensible, and useful - would they actually fail if the code broke?
5. **Naming** - Are names clear and communicative - long enough to convey meaning, short enough to stay readable?
6. **Comments** - Are comments necessary, clear, and do they explain *why* rather than *what*? Stale or commented-out content removed ([[00-constitution#PRIN-I Code Quality|PRIN-I]]).
7. **Style** - Does it follow the project style (`LANG-*`)? No style/formatting changes mixed into functional changes ([[00-constitution#PRIN-IX Minimal Changes|PRIN-IX]]).
*Targets:* code-reviewer.

### REV-007 — scope-reviewer process
The scope-reviewer: (1) extracts the spec's requirements into an exhaustive checklist; (2) verifies the backend - files exist where specified, endpoints exist with correct method/path, response schemas match the contract; (3) verifies the frontend against the spec; (4) runs a diff analysis and flags **any file not in the spec as EXTRA - HIGH severity**. Missing items are BLOCKING. Enforces `SPEC-001`.
*Targets:* scope-reviewer.

### REV-008 — No approval with open blockers
A change MUST NOT be approved (no "thumb up", no gate pass) while any CRITICAL/HIGH finding is open. Deferred MEDIUM/LOW findings are recorded before approval.
*Targets:* reviewer-gate, pull-request template.

### REV-009 → QG-010
Commit/merge gating (human confirm vs autonomous-loop opt-in) is defined in `QG-010`. Not restated.

### REV-010 - Empirical review (mechanical teeth)
Review is adversarial and empirical, briefed to refute rather than confirm. For any change that adds or modifies tests or wiring, the review gate MUST execute, in a throwaway copy of the repo (QG-008):
1. **Red-verify** - revert the production diff (keep the new tests) and run the new tests: they MUST fail against the reverted code. A new test that still passes is tautological (`TEST-004`) and a HIGH finding. (Complements `TEST-014`: that rule audits the author's red; this one has the reviewer reproduce it independently.)
2. **Mutation spot-check** - break at least one newly added wiring line (a route registration, a handler call, a query filter, an event hook) and confirm a test fails. Minimum one per review.
3. **Browser-verify** - any UX-affecting claim is verified against a running build via the production path (per the DoD), not inferred from reading components. Playwright output counts; reading JSX does not.
Findings from these checks carry `REPRODUCED` evidence by construction. *(Added 2026-06-11, cross-pollinated from sibling-project retros, where empirical review caught two would-have-shipped defects that green gates had passed.)*
*Targets:* code-reviewer, reviewer-gate, review workflow, DoD template.
