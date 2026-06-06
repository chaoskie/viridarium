# Knowledge & Language (`LANG-*`)

**Enforces:** the shared vocabulary layer - language policy and domain-language integrity, Conventional Commits (CI-008 depends on it), branch naming, editor/formatter alignment, the domain glossary, and knowledge upkeep. Consumed by every agent that writes code or commits, plus spec-archive and retrospective workflows.

---

### LANG-001 — Language policy & domain-language integrity
**English** for: source code, comments, docstrings, commits, PRs, spec artifacts, docs, API field names, enum values, log messages, error codes. The UI language is locked per project at start.

**Domain-data pass-through:** information received from external systems and shown in our UI is **NOT translated** to the environment language - domain language is authoritative and most domain terms do not translate correctly. Translation happens only where it is **explicitly programmed** as a deliberate feature (and then via the glossary table, LANG-007). No implicit/incidental translation, ever.
*Targets:* all agents, frontend developer, code-reviewer.

### LANG-002 — Conventional Commits
Commits follow Conventional Commits v1.0: `<type>(scope): <description>` - imperative subject ≤72 chars; optional body; footer carries the work-item reference (e.g. `Refs: <id>`) and `BREAKING CHANGE:` when applicable. Allowed types: `build, chore, ci, dependencies, docs, feat, fix, misc, refactor, revert, style, test, wip` - `wip` MUST NOT appear on the default branch. **No AI-attribution trailers** (`Co-Authored-By: ...` and similar are forbidden). Feeds CI-008 changelog generation.
*Targets:* all agents, ci.

### LANG-003 — Branch naming
`<type>/<short-slug>` (optionally `<type>/<work-item-id>-<short-slug>` when a tracker id exists) - slug lowercase with hyphens, total ≤50 chars. Example: `feat/per-plant-watering-schedule`.
*Targets:* all agents.

### LANG-004 — `.editorconfig` at repo root
Indentation: **4 spaces** Python; **2 spaces** TS/JS/JSON/CSS/YAML. No tabs. Line endings LF. (The `.editorconfig` file itself is owned by the repo-hygiene workstream; this rule fixes the conventions it must encode.)
*Targets:* developers, ci.

### LANG-005 → CI-002 + FE-006
Formatters (`ruff format` for Python; Prettier for TS) are defined in `cicd.md` and `frontend.md`. Not restated.

### LANG-006 — Naming
Prefer descriptive over short names. An excessively long name signals the construct does too much - refactor instead of abbreviating.
*Targets:* developers, code-reviewer.

### LANG-007 — Domain glossary
A discoverable glossary defines domain entities and state terminology (plant, schedule, watering/feeding cadence, care event, etc.). When any deliberate translation surface exists (LANG-001), it includes the translation table: `code entity ↔ UI term ↔ meaning`. New domain terms introduced by a change are added to the glossary in that same change.
*Targets:* design work, developers, spec-propose.

### LANG-008 — Knowledge upkeep
Agents read the project knowledge notes freely as context and **write to them directly** - edits ride the normal review rounds and git history provides the audit trail. Distill moments (end of a significant session; after `spec-archive`) prompt a knowledge sync so learnings land while fresh.
*Targets:* all agents, spec-archive, retrospective.

### LANG-009 — Retrospectives recorded
Each run/story closes with a retrospective note (what changed in the workflow, cost/effort data, deferred improvements). Accepted workflow changes are applied immediately, not queued.
*Targets:* retrospective workflow, design work.
