# Quality Gates (`QG-*`)

**Enforces:** the gates a change passes from "code written" to "merged" - mechanical checks, coverage bars, the agent failure circuit-breaker, commit discipline, and the DoR/DoD gate points. Consumed by the reviewer-gate, test-engineer, and the spec/CI/template workflows.

Load this file on demand when running a gate, a review, or a DoD check. Principles: governs [[00-constitution#PRIN-VI Story-Gated Iteration|PRIN-VI]], [[00-constitution#PRIN-VII Pipeline Must Be Green|PRIN-VII]], [[00-constitution#PRIN-VIII Self-Verifying Advancement|PRIN-VIII]].

The concrete commands behind each gate live in the `Makefile` (one target per gate, `make quality-gates` aggregate) and are mirrored in GitHub Actions (`cicd.md`). This file defines the gates; it does not restate the commands.

---

### QG-001 — Mechanical gate before AI review
The mechanical gate MUST pass before any AI review runs. Deterministic checks come first; AI review never substitutes for them. The mechanical gate is the union of:
- `ruff check` + `ruff format --check` (lint + format)
- `ruff` security rules (the `S`/bandit ruleset)
- `mypy --strict` on the domain + application layers
- `import-linter` boundary contracts (`ARCH-003`)
- `pytest` with coverage + `diff-cover` (`QG-002`)
- `pip-audit` (dependency CVEs, `SEC-009`)
- `eslint` + `tsc --noEmit` (frontend)

*Targets:* reviewer-gate, pipeline-medic, DoD template.

### QG-002 — Coverage gate
Overall coverage floor is **85%**. New/changed code MUST meet **80% diff-cover**. Branch coverage MUST be **≥95% in domain and application layers**, **≥80% in adapters/outbound**. Critical paths flagged in the spec require 100%.
*Targets:* test-engineer, reviewer-gate, DoD template.

### QG-003 → testing.md
"Each public API surface has ≥1 happy + ≥1 sad test" lives as `TEST-*` in `rules/testing.md` (single source). Cited here because the DoD gate checks it.
*Targets:* test-engineer.

### QG-004 — Gate-check matrix between phases
Before advancing a phase or story, the agent MUST post an explicit PASS/WATCH/FAIL checklist (one line + justification per item). Verdict semantics:
- **PASS** - the item is met, no reservations.
- **WATCH** - the item passes **with a recorded caveat** (a known weakness, an assumption taken on, a concern deferred). A WATCH does not block advancement, but its caveat MUST be logged in the worklog and MUST surface in the next retrospective (`LANG-009`); a WATCH whose caveat never reaches a retro is a violation. WATCH is never a euphemism for FAIL.
- **FAIL** - halts advancement. No exceptions.
Implements [[00-constitution#PRIN-VIII Self-Verifying Advancement|PRIN-VIII]]. *(Amended 2026-06-11: WATCH added, cross-pollinated from sibling-project retros.)*
*Targets:* all agents, spec-apply, retrospective.

### QG-005 — Story sign-off
At story completion a sign-off is recorded (who/what/gate results). For human-in-the-loop work this is a human sign-off; for autonomous-loop work it is the posted gate-check (QG-004) plus the worklog (`TRACE-*`).
*Targets:* DoD template, pull-request template.

### QG-006 → PRIN-VII + cicd.md
"Pipeline green, no exceptions, no pre-existing failures" is the principle [[00-constitution#PRIN-VII Pipeline Must Be Green|PRIN-VII]], detailed in `CI-*`. Not restated here.
*Targets:* cicd, reviewer-gate.

### QG-007 — Failure circuit breaker
An agent fixing a failure MUST stop and escalate after **3 retries on the same fix** OR **5 distinct test failures** in one task. Stopping reports the state; it does not thrash. Prevents runaway loops.
*Targets:* all agents, bug workflow, pipeline-medic.

### QG-008 — WIP rollback points
Commit a WIP checkpoint after each completed task group so any failure has a clean rollback point. (Subject to the commit-gating posture in QG-010.) **Destructive experiments** (reverting diffs to prove a test red, mutating code to trip a gate, bulk deletions, history surgery) run only in a **throwaway copy of the repo** (e.g. under `/tmp`), never in the working tree. *(Amended 2026-06-11, cross-pollinated from sibling-project retros.)*
*Targets:* developers, spec-apply, reviewer-gate.

### QG-009 — File-size ceilings
New source files: **250 LOC soft ceiling** (exceed only with inline justification). Test files: **500 LOC hard max** (split by endpoint / scenario group).
*Targets:* developers, reviewer-gate.

### QG-010 — Commit gating (configurable per workflow)
**Default:** an agent may edit and run freely (autonomous permissions) but MUST NOT commit until the user confirms the change works. **Override:** an autonomous-loop workflow MAY opt into autonomous commit by declaring it explicitly in its command definition, in which case commit is gated on a green DoD (QG-012) instead of human confirmation.
*Targets:* developers, DoD template, autonomous-loop commands.

### QG-011 — Definition of Ready gate
Work on a change MUST NOT start until its DoR is satisfied. Criteria live in the DoR workflow-template; this rule mandates the gate exists and fires at propose-time (`/spec-propose`).
*Targets:* spec-propose, DoR template.

### QG-012 — Definition of Done gate
A change MUST NOT merge until its DoD is satisfied. Criteria live in the DoD workflow-template; DoD aggregates QG-001/002/004/005, the worklog (`TRACE-*`), and a green pipeline. Fires at archive-time (`/spec-archive`).
*Targets:* DoD template, pull-request template.

### QG-013 RETIRED (not applicable: no external SonarQube gate in this project)
The source project mandated a SonarQube quality gate as a binding external gate. This project's deterministic quality is enforced entirely by the in-repo Makefile gates (QG-001/002) and GitHub Actions; there is no external code-quality service. The coverage and clean-code intent is preserved by QG-001 (ruff/mypy) + QG-002 (coverage floor + diff-cover).

### QG-014 RETIRED (not applicable: no external Sigrid gate in this project)
The source project mandated a Sigrid maintainability star bar as a binding external gate. No equivalent external maintainability service is used here; maintainability is upheld by PRIN-I, the file-size ceilings (QG-009), and code review (`REV-*`).

### QG-015 - Gates must bite (bites-proof)
A new or repaired quality gate (CI job, Makefile target, perf/a11y/event-logging audit, custom check) MUST ship with a **demonstrated red**: break the guarded property in a throwaway copy (QG-008) and show the gate failing, with the red recorded in the worklog. Corollaries:
- **Instrument the app's own resources** - the gate measures the engine/connection/build the application actually uses at runtime, never a test-only stand-in.
- **Trippable fixtures** - gate fixtures are seeded with real data so the failure path is reachable; a gate that has never fired is presumed broken until red-proven.
- **One expected outcome per assertion** - never widen an assertion (e.g. `assert x in (a, b)`) to make a gate tolerant.
A gate without a bites-proof is advisory, not a gate. *(Added 2026-06-11, cross-pollinated from sibling-project retros: a sibling project discovered a perf gate that had counted zero queries since inception - instrumentation attached to a test-only engine, fixtures with no data.)*
*Targets:* developers, test-engineer, pipeline-medic, ci, reviewer-gate.

### QG-016 - Completion language is gate-bound
An agent MUST NOT declare a story, phase, or change "done", "complete", or "ready" until the matching gate checklist (QG-004 for phase/story advancement, the DoD for merge/archive) has been **posted with its results**. Until that moment, status language states exactly what is pending - e.g. "implementation complete; review and DoD gates pending". A premature completion claim is a gate violation in itself, even if the work later passes every gate. Implements [[00-constitution#PRIN-VIII Self-Verifying Advancement|PRIN-VIII]]. *(Added 2026-06-11, cross-pollinated from sibling-project retros: "Phase 1 done" was claimed with the reviewer, test-engineer, and security gates all unrun.)*
*Targets:* all agents, reviewer-gate, retrospective, DoD template.

### QG-017 - No paper gates
Every numeric or mechanical bar the rules cite (coverage floors, lint/format, boundary contracts, audit levels) MUST be enforced by a tool that **fails the build/pipeline on breach** - a Makefile target plus its CI mirror. The wiring is verified when the bar is introduced (bites-proof, QG-015), and the **enforced run's output is referenced at the DoD gate** - never assumed from the rule text. A bar that exists only in prose is not a gate. *(Added 2026-06-11, cross-pollinated from sibling-project retros: a sibling project carried an 80% coverage rule on paper while an entire layer sat at 0% under a green build - no coverage check was wired anywhere.)*
*Targets:* ci, pipeline-medic, test-engineer, reviewer-gate, DoD template.
