# Constitution

**Status:** always-on. This file loads into every session. It holds the immutable *principles* (the why) and governance. Concrete enforceable *standards* (the what) live in the topic files (`rules/<topic>.md`) and load on demand. A principle never restates a standard.

---

## Governance

- **Severity language.** **MUST / MUST NOT** = hard requirement; violation blocks merge. **SHOULD / SHOULD NOT** = strong default; deviation needs written justification. **MAY** = permitted option.
- **Comply or explain.** Any deviation from a MUST requires written approval recorded in the change's `proposal.md` (or an ADR). Silent deviation is a violation.
- **Audience.** Every rule applies equally to a human developer and to an AI agent acting in the developer role.
- **Authority.** This constitution supersedes ad-hoc preference and conflicting docs. When it conflicts with a downstream spec, the constitution wins unless the spec records a ratified deviation.

---

## Immutable Principles

### PRIN-I Code Quality
Code MUST be clean, readable, single-responsibility. Functions over 20 lines or branching depth over 3 MUST be justified inline. No dead code, no commented-out blocks, no unused imports. Governs `ARCH-*`, `REV-*`.

### PRIN-II Privacy & Security
The app ships secure-by-default for trusted-network deployment: no PII in logs or error responses, no secrets in the repo, safe bind/CORS posture, and the documented trust boundary respected. There is no user authentication in v1 by design (`SEC-003`); any future auth feature is opt-in. OWASP-relevant risks (injection, dependency CVEs, header hygiene) mitigated every release. Governs `SEC-*`.

### PRIN-III Test-First
Tests precede implementation; red-green-refactor is mandatory. Tests that would pass against any implementation are noise, not tests. Governs `TEST-*`.

### PRIN-IV Specs Are Exact Scope
The spec is the contract: the implementation contains everything the spec describes and nothing it does not. Extras are high-severity findings; omissions are blocking. Governs `SPEC-*`.

### PRIN-V Stack Lock-In
The stack is decided once, in writing, and re-affirmed per change. Adding or replacing a locked component requires a written amendment. No ad-hoc "let me just try X". Governs `ARCH-*`, `SPEC-*`.

### PRIN-VI Story-Gated Iteration
Work proceeds story-gated, each story on its own branch. A dependent story MUST NOT begin until the story it depends on passes its gate. Independent stories with disjoint file ownership MAY proceed in parallel when a single orchestrator gates and integrates the results; each story still passes its own gate before its result merges, and any file-ownership overlap discovered mid-flight halts the later story. Per-story change budget ~400-500 lines new logic, 1000 LOC hard ceiling. **When one story is delivered as parallel disjoint-file lanes (e.g. a backend lane and a frontend lane), the ~400-500 soft budget applies per lane; the 1000 LOC hard ceiling remains per story.** Governs `QG-*`, `SPEC-*`. *(Amended 2026-06-07 sprint-1 retro F1; per-lane budget added 2026-06-08 sprint-2 retro.)*

### PRIN-III evidence (operative note)
Test-first is auditable, not trusted: a build agent records the **failing-test run (the red)** in the change worklog before the code that turns it green (see `TEST-014` and the agent-brief preflight). *(Added 2026-06-08, sprint-2 retro, closing sprint-1 carry-forward.)*

### PRIN-VII Pipeline Must Be Green
Every push results in a fully green pipeline. No "pre-existing failures". A pull request MUST NOT merge on a red pipeline. Governs `CI-*`, `QG-*`.

### PRIN-VIII Self-Verifying Advancement
An agent MAY advance autonomously only after running an explicit gate-check whose PASS/WATCH/FAIL results are posted before advancing. Any FAIL halts. A WATCH passes only with its caveat recorded for the next retrospective (semantics in `QG-004`). Silent advancement is a violation. Governs `QG-*`, `TRACE-*`. *(Amended 2026-06-11: WATCH verdict added, cross-pollinated from sibling-project retros.)*

### PRIN-IX Minimal Changes
Change only what the task requires. Unrelated refactors, renames, dependency bumps, and formatter cascades MUST NOT ride along. Formatters run only on touched files. Governs `REV-*`, `SPEC-*`.

### PRIN-X Comply or Explain
Restated for emphasis: deviation from a MUST requires written approval and a written record. Governs all topics.

### PRIN-XI Traceability
Every unit of work keeps a worklog capturing the AI and user steps that produced it. Work whose path from request to result cannot be reconstructed is not done. Governs `TRACE-*`.

---

## Amendments

| Date | Principle | Change | Source |
|---|---|---|---|
| 2026-06-07 | PRIN-VI | Parallel execution of independent, disjoint-file stories permitted under a single gating orchestrator | Sprint-1 retro, fork F1 |
| 2026-06-08 | PRIN-VI | LOC soft budget applies per disjoint delivery lane when one story runs as parallel lanes (hard ceiling stays per story) | Sprint-2 retro, fork |
| 2026-06-08 | PRIN-III | Test-first requires a recorded red-run in the worklog before the green commit (see TEST-014) | Sprint-2 retro, fork |
| 2026-06-11 | PRIN-VIII | Gate-check vocabulary extended to PASS/WATCH/FAIL; WATCH = pass with a recorded caveat that must surface in the next retrospective (QG-004) | Cross-pollination from sibling-project retros |
