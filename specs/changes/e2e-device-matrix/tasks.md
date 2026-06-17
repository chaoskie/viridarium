# Tasks - `e2e-device-matrix`

One task group; test/CI infra (PRIN-VI). No product logic.

## T1 - Matrix wiring + tagging (DONE)

- [x] Add `E2E_DEVICE_MATRIX`-gated 5-viewport `matrixProjects` to
      `frontend/playwright.config.ts` (`grep: /@layout/`).
- [x] Tag the read-only layout specs `@layout`
      (`mobile-layout.spec.ts` describe; `add-plant-modal.spec.ts` BUG-003).
      Leave write specs untagged (single-device).
- [x] `fe-e2e-matrix` Makefile target.
- [x] `.github/workflows/device-matrix.yml` (release + workflow_dispatch).

## T2 - Verify (DONE)

- [x] AC1: per-PR `--list` = `galaxy-s25-plus` + `desktop` only.
- [x] AC2/AC3: matrix `--list` adds 5 mobile projects x 4 `@layout` specs;
      write specs excluded.
- [x] AC4: workflow triggers on `release: published` + `workflow_dispatch`.
- [x] `make fe-e2e-matrix` => 36 passed (16 base + 20 matrix); invariants hold
      at 360/390/393/412/430.
- [x] AC5 / QG-015 bites-proof: transient 2000px overflow injected ->
      BUG-001 fails on mobile-360x800 and mobile-430x932 -> reverted.
- [x] lint / format / typecheck clean; workflow YAML valid.
