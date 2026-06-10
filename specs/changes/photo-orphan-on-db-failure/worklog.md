# Worklog - photo-orphan-on-db-failure

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~02:50 · orchestrator/Fable · fix applied: make_cover read moved before the disk write; repository.add wrapped w/ compensating storage.delete + re-raise. GREEN: 246 backend tests, static gates clean. No three-reviewer cycle (reviewer-originated small fix, test-first + full gate; precedent photo-missing-file-404) · backend/src/viridarium/application/photos.py · PRIN-IX/REV-003`
- `~02:45 · orchestrator/Fable · TEST-014 red recorded: test_upload_failed_insert_removes_saved_file failed (ghost file left in storage fake after simulated insert failure; calls [save] with no delete) · backend/tests/unit/test_photo_use_case.py · TEST-014`
- `~02:40 · orchestrator/Fable · bugfix opened from 2026-06-10 review pass finding 1; branch fix/photo-orphan-on-db-failure off main · specs/changes/photo-orphan-on-db-failure · REV-003`
