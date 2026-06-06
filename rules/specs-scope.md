# Specs & Scope (`SPEC-*`)

**Enforces:** scope discipline and the spec artifacts a change must carry. This project runs a **self-contained** spec lifecycle (no external spec tool): changes live in `specs/changes/<change-name>/` with `proposal.md`, `design.md`, `tasks.md`, and `worklog.md`; `spec-archive` moves a completed change to `specs/archive/`. The lifecycle is **propose → apply → archive**, gated at each end. Consumed by design work and the `spec-*` commands. Implements [[00-constitution#PRIN-IV Specs Are Exact Scope|PRIN-IV]], [[00-constitution#PRIN-V Stack Lock-In|PRIN-V]], [[00-constitution#PRIN-VI Story-Gated Iteration|PRIN-VI]].

---

### SPEC-001 — Spec is the contract
The implementation MUST contain everything the spec describes and MUST NOT contain anything it does not. Extra files, endpoints, or fields are **HIGH-severity** findings; missing items are **blocking**. No interpretation, no improvement, no extras. (The enforceable detail of [[00-constitution#PRIN-IV Specs Are Exact Scope|PRIN-IV]].)
*Targets:* scope review, design work, all developer agents.

### SPEC-002 — Spec lifecycle & artifacts (full track only, for now)
Every change uses the **full** ceremony before implementation begins. A change is a directory `specs/changes/<change-name>/` containing:
- `proposal.md` - the why, the story, scope in/out, comply-or-explain deviations, contract delta if any.
- `design.md` - approach, affected hexagon/contexts, ADR links.
- `tasks.md` - the ordered task groups (checkboxes), implemented one group at a time (PRIN-VI).
- `worklog.md` - the per-change trail (`TRACE-001`).
At completion, `spec-archive` moves the directory to `specs/archive/<change-name>/`. There is no lightweight path yet.
> **Deferred:** a Light track is planned for later. When added, the Light/Full boundary will be a **combined trigger** - Full if ANY of: >5 files, >500 LOC new logic, new endpoint, DB migration, contract change, or cross-module. Until then, treat all changes as Full.
*Targets:* spec-propose, spec-apply, spec-archive, design work.

### SPEC-003 — Test-foundation before implementation
Before implementation, a change carries a **test-foundation** document (in its change folder): input-state matrices, sad-paths, and coverage targets. It is authored by the test-engineer agent. The *content* rules (matrix thresholds, happy/sad pairing, required markers) live in `rules/testing.md` (`TEST-*`); this rule mandates the artifact exists and gates implementation.
*Targets:* test-engineer, spec-propose, DoR template.

### SPEC-004 — Story format & sizing
A story is written as **"As `<role>`, I want `<what>`, so that `<why>`"** and sized to **1-3 days OR ~400-500 LOC of new logic**. Larger work MUST be split into multiple stories. (Repetitive changes within one logical segment are excluded from the LOC count.)
*Targets:* design work, spec-propose.

### SPEC-005 — Multi-story look-ahead (MAY)
Design work MAY batch-draft several story specs upfront for a single approval, then implement them sequentially under the standard story-gated cycle ([[00-constitution#PRIN-VI Story-Gated Iteration|PRIN-VI]]). Optional capability, not required.
*Targets:* design work, spec-propose.
