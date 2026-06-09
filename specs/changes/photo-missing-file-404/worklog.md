# Worklog - photo-missing-file-404

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~00:55 · orchestrator/HIGH · bugfix opened from Fable 5 (independent E2 review) Finding 1; branch fix/photo-missing-file-404 off main · specs/changes/photo-missing-file-404 · REV-008/SEC-007`
- `~01:05 · orchestrator/HIGH · TEST-014 red: test_get_bytes_missing_file_returns_404 -> 500 (RuntimeError "File at path .../<uuid>.jpg does not exist", path-leaking) before the fix · test_photos_endpoint.py · TEST-014`
- `~01:10 · orchestrator/HIGH · fix applied (Fable 5 Finding 1): photo_storage split _resolve (traversal-only) vs open_path (resolve+exists->FileNotFoundError); delete uses _resolve (idempotent); PhotoService.storage_path maps FileNotFoundError->PhotoNotFoundError(404). GREEN: 195 backend tests, 99.28%, all gates. No re-audit/code-review cycle (reviewer-originated 20-line fix, test-first + full-gate) · backend/ · REV-003/SEC-007`
