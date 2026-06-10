# Worklog - schedule-wrong-reason-404

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~01:20 · orchestrator/Fable · fix applied: _guard_plant added to get/delete (+docstrings that documented the asymmetry). GREEN: 243 backend tests, lint/format/mypy/import-linter clean. No three-reviewer cycle (reviewer-originated 2-line fix, test-first + full gate; precedent photo-missing-file-404) · backend/src/viridarium/application/care_schedules.py · PRIN-IX/REV-003`
- `~01:15 · orchestrator/Fable · TEST-014 red recorded: 4 failures - unit get/delete missing plant expected PlantNotFoundForScheduleError got CareScheduleNotFoundError; integration unknown-plant GET/DELETE detail was "No water schedule for plant 999999" · tests/unit/test_care_schedule_use_case.py, tests/integration/test_care_schedules_endpoint.py · TEST-014`
- `~01:05 · orchestrator/Fable · bugfix opened from 2026-06-10 review pass finding 3; branch fix/schedule-wrong-reason-404 off main · specs/changes/schedule-wrong-reason-404 · REV-003`
