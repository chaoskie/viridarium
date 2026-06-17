# Proposal - `e2e-device-matrix`

**Work item:** VIRIDARIUM-77
**Type:** test / CI infrastructure (no product code, no API, no persistence)

## Story

As the maintainer, I want the width-sensitive layout acceptance checks to run
across the most common mobile screen resolutions at release time, so that a
layout regression at a width other than the Galaxy S25+ primary is caught before
a release ships - without slowing down every PR.

## Background

The acceptance suite (TEST-009) runs per-PR on a single primary viewport
(Galaxy S25+, 384x740) plus a desktop project for the FE-012 screenshots. The
soak surfaced width-driven regressions (BUG-001 horizontal overflow, BUG-002
off-screen control, BUG-003 modal reachability); these are exactly the failures
that vary by viewport width. Running them across more widths every PR would add
meaningful CI minutes for little per-PR value, so the maintainer chose to gate
the matrix to release time.

## Scope

In scope:
- A release-gated Playwright project matrix over the top-5 mobile CSS viewports.
- The matrix runs only the read-only, width-sensitive `@layout` specs.
- A release-triggered CI workflow + a `make` target to drive it.

Out of scope (explicit):
- Per-PR behaviour is unchanged (primary + desktop only).
- Write specs (form submit, upload) stay single-device - the shared SQLite
  acceptance backend runs `workers:1`, so multi-device writes would contend.
- No new product code, no API change, no persistence change (`ARCH-011` N/A).

## OpenAPI delta

None - no REST surface touched (`API-001` not triggered).

## Acceptance criteria

- **AC1** Per-PR run (no `E2E_DEVICE_MATRIX`) lists exactly the existing
  `galaxy-s25-plus` + `desktop` projects - no added per-PR cost.
- **AC2** With `E2E_DEVICE_MATRIX=1`, 5 mobile-resolution projects are added,
  each running only the `@layout`-tagged specs.
- **AC3** The matrix runs the read-only layout checks; the add-plant write specs
  (BUG-005, cachepot A1) are NOT in the matrix.
- **AC4** A CI workflow runs the matrix on release (`release: published`) and on
  manual `workflow_dispatch`, not per-PR.
- **AC5** The matrix demonstrably catches a layout regression at the new widths
  (QG-015 bites-proof).

## Open questions: none

Design confirmed with the maintainer 2026-06-17 (release-gated; top-5
resolutions; read-only specs parallel-eligible, writes single-device).
