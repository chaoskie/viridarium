# Proposal - photo-missing-file-404 (bugfix, from Fable 5 review)

Status: applied (PR open). Bugfix surfaced by the independent "Fable 5" cross-epic review of E2.

## Problem

`GET /api/v1/plants/{id}/photos/{photo_id}` returns **500** (and logs the absolute file path)
when the photo ROW exists but its backing FILE is missing on disk. Row/file desync is reachable:
a crash between the DB-delete and file-unlink (the documented DB-first ordering accepts the
inverse), a backup/restore mismatch, or external file loss. `FileResponse` raises lazily at send
time, so no exception handler catches it today.

## Fix (exact scope, PRIN-IX)

Split path resolution from existence in the storage adapter: `_resolve` does the traversal guard
(within-root) only; `open_path` resolves + asserts the file exists, raising `FileNotFoundError`
(carrying only the stored name, never the absolute path). `delete` uses `_resolve` (stays
idempotent on a missing file). `PhotoService.storage_path` catches `FileNotFoundError` → raises
`PhotoNotFoundError` → the existing 404 handler. Serving a missing-file photo now returns a clean
404 (consistent with every other unresolvable-photo case) and leaks no path (SEC-007).

## Out of scope
No behavior change to upload/list/cover/delete; no new endpoint; no schema change.

## Acceptance
- AC1: a photo row whose file was removed → `GET .../photos/{id}` returns 404 (`{"detail"}` only), not 500.
- AC2: delete stays idempotent; the traversal guard still rejects escapes; all existing photo tests stay green.

## DoR: PASS (review-surfaced correctness/robustness bug; tiny, test-first, no contract change).
