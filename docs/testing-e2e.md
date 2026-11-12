# Acceptance testing patterns (Playwright)

Conventions and known traps for the Playwright acceptance layer (`frontend/e2e/`, run
with `make fe-e2e`). The enforceable rules are in [`rules/testing.md`](../rules/testing.md)
and [`rules/frontend.md`](../rules/frontend.md); this page explains the patterns behind
the suite.

## One shared backend, one worker

The suite boots a single FastAPI backend on a throwaway SQLite file. Parallel workers
contend on writes ("database is locked"), so `playwright.config.ts` sets
`fullyParallel: false` and `workers: 1`. Two consequences:

- **Names must be unique per Playwright project.** All projects (phone, desktop, the
  device matrix) hit the same backend in one run. A test that creates `"Gallery demo"`
  on two projects produces two rows and a strict-mode locator violation. Include the
  project: `` `Gallery demo ${testInfo.project.name}` ``. The database is wiped on each
  run by `frontend/e2e/run-backend.sh`, so the problem is within a run, not across runs.
- **Write specs stay single-device.** Only read-only specs run across multiple devices.

## Throwaway directories for filesystem features

`run-backend.sh` must point file-storage settings at a wiped throwaway directory, not at
the production default. Photo upload first failed in e2e because `PHOTOS_DIR` defaulted
to `/data/photos`, which is not writable in dev or CI. The script now exports a
directory under `frontend/.e2e/` and recreates it on each boot, like the SQLite file.
The first spec to exercise a side-effect path often reveals a setting the unit tests
never needed.

## Real fixture images

A fake PNG with only valid magic bytes passes the backend sniff but does not render in a
browser. Fixtures under `frontend/e2e/fixtures/` are real images. The portrait one is
deliberately non-square, with corner markers and bands, so a crop-versus-contain
regression is visible in a screenshot.

## Do not stack modals

`Modal` binds a `document` Escape listener on mount. A second Modal on top (for example
a lightbox over a gallery) means one Escape closes both. For a detail or lightbox view,
toggle an in-modal view inside the existing Modal, and resolve the viewed item by id so
a background reload cannot leave a stale object (BUG-008).

## `object-cover` versus `object-contain`

- **Crop on purpose** (`object-cover`): square grid thumbnails and the cover thumbnail.
  A uniform grid is the point.
- **Show the whole image** (`object-contain`): the full-image view and the care
  timeline. The timeline is a history feed, so the actual photo must be visible, even if
  letterboxed (BUG-009).

## Release-gated device matrix

More widths are tested without taxing every PR:

- `E2E_DEVICE_MATRIX=1` adds the mobile-resolution projects. Unset, only the primary
  phone and desktop projects run.
- Read-only, width-sensitive specs are tagged `@layout`; matrix projects use
  `grep: /@layout/`. Write specs stay untagged.
- The matrix runs at release time only: `.github/workflows/device-matrix.yml` on a
  published release or manual dispatch, running `make fe-e2e-matrix`.
- Proof that the gate bites (`QG-015`): temporarily add an element with `w-[2000px]`,
  watch the no-overflow check fail on the matrix devices, revert.

## Fixed bottom navigation clearance

A `fixed bottom-0` mobile nav hides the last element on the page. Put the clearance
padding on the always-present last element (the footer), not on `<main>`, so nothing is
obscured and there is no double gap.

## Related traps outside Playwright

- **Verify the build as the backend serves it.** Some defects only exist on the
  single-container path, because `vite dev` sends no CSP and the in-process test client
  serves no SPA. For UI changes, build the frontend, start the backend with
  `STATIC_DIR=frontend/dist`, drive it in a browser and require zero console errors. A
  CSP rule blocking fonts and the theme script was found this way (fixed in #28).
- **`backend/uv.lock` rides along.** A `make` or `uv sync` run on a feature branch can
  regenerate the lockfile. Check `git status` before committing and restore the file
  unless the change is a deliberate, reviewed lock refresh. CI installs with `--frozen`.
- **Do not prove a tiebreak at the integration layer.** `created_at` has one-second
  granularity there, so two rows created in the same second cannot be ordered by it and a
  passing test is a coincidence. Pin ordering at the unit layer with exact injected
  datetimes; let the integration test assert only stability.
- **Stacked PRs and `--delete-branch`.** Squash-merging a base PR with
  `gh pr merge --delete-branch` while another PR is stacked on that branch makes GitHub
  close the stacked PR, and it cannot be reopened. Rebase the child onto `main` and
  retarget it before deleting the base, or branch each story off `main` once the
  previous one is merged.
