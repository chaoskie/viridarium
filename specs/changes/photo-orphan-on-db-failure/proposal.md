# Proposal - photo-orphan-on-db-failure (bugfix, from 2026-06-10 review pass)

Status: in progress. Bugfix surfaced by the 2026-06-10 quick review pass; tracked as VIRIDARIUM-46.

## Problem

`PhotoService.upload` writes the file to disk (`storage.save`) and only then inserts the
metadata row (`repository.add`). If the insert fails (engine error, constraint violation,
crash window), the exception propagates as a 500 and the bytes stay on disk with no row
pointing at them: orphaned storage that nothing in the app can find or reclaim. The
module's own P5 rule ("disk matches DB") covers delete but not the upload failure path.

## Fix (exact scope, PRIN-IX)

- Compute `make_cover` (a repo read) *before* the disk write, shrinking the post-save
  window to the single `repository.add` call.
- Wrap `repository.add` in try/except: on any failure, `storage.delete(stored_filename)`
  (already idempotent since photo-missing-file-404), then re-raise.

## Out of scope

No transaction-boundary redesign (moving storage into the repo transaction crosses the
hexagonal layer); no change to validation order, delete path, or API behavior.

## Acceptance

- AC1: when the metadata insert raises, the saved file is removed and the original
  exception propagates unchanged.
- AC2: happy path unchanged (file saved, row added, first-photo cover logic intact);
  all existing photo tests stay green.

## DoR: PASS (review-surfaced data-integrity bug on a failure path; tiny, test-first, no contract change).
