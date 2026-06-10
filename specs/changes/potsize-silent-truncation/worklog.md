# Worklog - potsize-silent-truncation

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~02:20 · orchestrator/Fable · fix applied: pot-size integer validation w/ field error + step=1 + aria-invalid + form noValidate (native bubbles would preempt the custom-error pattern); parser tightened to Number.isInteger. GREEN: 245 backend + 131 frontend tests, lint/format/tsc clean. No three-reviewer cycle (reviewer-originated small fix, test-first + full gate; precedent photo-missing-file-404) · frontend/src/features/plants/PlantFormModal.tsx · PRIN-IX/REV-003`
- `~02:10 · orchestrator/Fable · TEST-014 red recorded: form test "rejects a decimal pot size" failed (no whole-number alert; decimal reached the API path). Backend float case 3.7->422 passed immediately: triage claim "Pydantic truncates" REFUTED (lax mode rejects non-integral floats); test kept as regression pin, proposal corrected, backend production code untouched · frontend PlantFormModal.test.tsx, backend test_plants_endpoint.py · TEST-014`
- `~01:45 · orchestrator/Fable · bugfix opened from 2026-06-10 review pass finding 2; branch fix/potsize-silent-truncation off main · specs/changes/potsize-silent-truncation · REV-003`
