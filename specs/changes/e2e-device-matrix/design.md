# Design - `e2e-device-matrix`

## Mechanism

A single env flag, `E2E_DEVICE_MATRIX`, conditionally injects extra Playwright
projects in `frontend/playwright.config.ts`:

- Unset (per-PR / local default): `matrixProjects` resolves to `[]`; the
  `projects` array is exactly `galaxy-s25-plus` + `desktop` as before.
- `=1` (release / `make fe-e2e-matrix`): 5 mobile-resolution projects are
  appended, each with `grep: /@layout/`.

This keeps the per-PR pipeline byte-for-byte identical and makes the matrix an
additive, opt-in layer.

## Device list (top-5 mobile CSS viewports)

| Project | Viewport (CSS px) |
|---|---|
| `mobile-360x800` | 360 x 800 |
| `mobile-390x844` | 390 x 844 |
| `mobile-393x852` | 393 x 852 |
| `mobile-412x915` | 412 x 915 |
| `mobile-430x932` | 430 x 932 |

The primary `galaxy-s25-plus` (384x740) already covers a tight usable-height
case, so the matrix focuses on width coverage. Each project uses a mobile
Chromium base (`devices["Galaxy S9+"]`) with the viewport overridden; for CSS
layout, width is the variable that matters (the UA does not affect layout).

## Spec selection: the `@layout` tag

The matrix must run only **read-only, width-sensitive** specs - running write
specs across devices would contend on the shared SQLite backend (`workers:1`)
and would duplicate screenshot evidence. Tagging:

- `mobile-layout.spec.ts` - whole describe tagged `@layout` (BUG-001 overflow,
  BUG-002 theme-selector on-screen, FE-015 a11y; all read-only).
- `add-plant-modal.spec.ts` - only the BUG-003 reachability test tagged
  `@layout` (fills a field, never submits). BUG-005 and cachepot A1 submit and
  stay single-device (untagged).

`galaxy-s25-plus` has no `grep`, so it still runs everything per-PR; `desktop`
greps `@desktop`, so the layout specs don't run there.

## CI

`.github/workflows/device-matrix.yml` mirrors the `acceptance` job in
`quality-gates.yml` (same action versions, npm 11 pin, uv cache, Playwright
Chromium install) but triggers on `release: published` (same gate point as
`publish.yml`) plus `workflow_dispatch` as a manual escape hatch. It runs
`make fe-e2e-matrix` (`E2E_DEVICE_MATRIX=1 npx playwright test`) and uploads the
HTML report as an artifact. `permissions: contents: read`; concurrency group
matches the established pattern.

## Parallelism note

The suite stays `workers:1` (the existing shared-SQLite constraint). The matrix
adds wall-clock at release time only; the read-only layout specs carry no write
contention, so serial execution is safe and the release-gating keeps the cost
off every PR. True cross-device parallelism was not adopted because the single
shared backend cannot take concurrent writes (consistent with the existing
config rationale).
