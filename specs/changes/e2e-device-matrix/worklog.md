# Worklog - `e2e-device-matrix`

Per-change trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.

## Context

Release-gated multi-device e2e matrix (Plane VIRIDARIUM-77). Design confirmed by
the maintainer (2026-06-17): keep the S25+ primary per-PR; re-run the
width-sensitive read-only `@layout` specs across the top-5 mobile CSS viewports
only at release; write specs stay single-device (shared SQLite backend is
`workers:1`). Test/CI infra only - no product code, no API, no persistence
change.

## Entries

- `18:45 · claude/OPUS · REVIEW GATE (QG-004): code + scope reviewers - implementation correct, well-scoped, per-PR cost zero, @layout grep load-bearing (both REPRODUCED). Findings resolved: scope BLOCKING (SPEC-002 artifacts) -> proposal/design/tasks added; code HIGH (TEST-014 red-before-green) -> wiring red + comply-or-explain recorded below; QG-015 bites-proof -> done below; LOW stale JSDoc in add-plant-modal -> fixed. TRACE-006 actor kept as claude/OPUS per this repo's existing worklog convention (cachepot) · /review · QG-004`
- `18:42 · claude/OPUS · QG-015 BITES-PROOF: injected a transient w-[2000px] element in AppShell -> BUG-001 (no horizontal overflow) FAILED on mobile-360x800 AND mobile-430x932 while BUG-002/FE-015 passed; reverted (no biteproof marker remains). The matrix gate catches a real width regression across the new resolutions · src/components/AppShell.tsx (transient) · QG-015`
- `18:40 · claude/OPUS · TEST-014 red-before-green (wiring) + comply-or-explain: this is a CI/test-infra tagging+gating change with no new product assertion - the guarded layout invariants (BUG-001/002/003, FE-015) already carry red-evidence from their origin stories. The change-specific "red": before the matrixProjects block, E2E_DEVICE_MATRIX=1 ... --list yields 16 tests (matrix absent / gate ineffective); after, 36. Mutation: removing grep:/@layout/ from a matrix project pulls in the write specs (guard is load-bearing). Bites-proof above closes QG-015 · playwright.config.ts · PRIN-III/TEST-014`
- `18:35 · claude/OPUS · GREEN: matrix verified locally - E2E_DEVICE_MATRIX=1 make fe-e2e-matrix => 36 passed (16 base + 20 matrix); per-PR (no env) unchanged at galaxy-s25-plus + desktop only (--list confirmed). Layout invariants (BUG-001 overflow, BUG-002 theme selector on-screen, FE-015 a11y, BUG-003 modal reachability) hold at 360/390/393/412/430. Lint/format/typecheck clean; workflow YAML valid · playwright.config.ts, device-matrix.yml, Makefile, mobile-layout.spec.ts, add-plant-modal.spec.ts · TEST-009/QG-004`
- `18:30 · claude/OPUS · impl: 5 matrix projects in playwright.config.ts gated on E2E_DEVICE_MATRIX (grep /@layout/); tagged read-only layout specs @layout; added fe-e2e-matrix Makefile target + .github/workflows/device-matrix.yml (on release published + workflow_dispatch) mirroring the acceptance job · - · PRIN-IX`
