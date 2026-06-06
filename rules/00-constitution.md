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
Work proceeds one story at a time, each on its own branch. Story N+1 MUST NOT begin until story N passes its gate. Per-story change budget ~400-500 lines new logic, 1000 LOC hard ceiling. Governs `QG-*`, `SPEC-*`.

### PRIN-VII Pipeline Must Be Green
Every push results in a fully green pipeline. No "pre-existing failures". A pull request MUST NOT merge on a red pipeline. Governs `CI-*`, `QG-*`.

### PRIN-VIII Self-Verifying Advancement
An agent MAY advance autonomously only after running an explicit gate-check whose PASS/FAIL results are posted before advancing. Any FAIL halts. Silent advancement is a violation. Governs `QG-*`, `TRACE-*`.

### PRIN-IX Minimal Changes
Change only what the task requires. Unrelated refactors, renames, dependency bumps, and formatter cascades MUST NOT ride along. Formatters run only on touched files. Governs `REV-*`, `SPEC-*`.

### PRIN-X Comply or Explain
Restated for emphasis: deviation from a MUST requires written approval and a written record. Governs all topics.

### PRIN-XI Traceability
Every unit of work keeps a worklog capturing the AI and user steps that produced it. Work whose path from request to result cannot be reconstructed is not done. Governs `TRACE-*`.
