# Worklog - BUG-007 care-schedule unsaved-state loss

Per-fix trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.

## Gate-check (QG-004, 2026-06-17)

Review gate (3 reviewers, read-only):

- **Security** - PASS (0 findings). Frontend-only state toggle; no new outbound calls, no trust-boundary / PII / dependency impact (SEC-003/010).
- **Scope** - APPROVED (0 findings). Diff confined to the two in-scope files; all 4 ACs satisfied; `usePhotos` correctly excluded (no reproducible data-loss there, only a benign flicker - PRIN-IX).
- **Code** - no CRITICAL/HIGH. 1 MEDIUM (missing worklog / TEST-014 red-run record) - resolved by this file. 1 LOW (theoretical `plantId`-change-on-mounted-instance path; does not exist at the current call site since the modal mounts per-plant; documented in the hook docstring) - accepted.

DoD gate (QG-004):

1. Reproduction is a failing test that now passes (`PRIN-III`/`TEST-014`) - **PASS** (red + green recorded below)
2. Tests green - **PASS** (frontend: lint, format, typecheck clean; 234 vitest; build OK)
3. Boundaries clean (`ARCH-003`) - **PASS** (change isolated to the plants feature hook)
4. Dual-engine (`ARCH-011`) - **N/A** (pure frontend; no persistence/migration touched)
5. Scope unchanged (`SPEC-001`) - **PASS** (scope reviewer APPROVED)
6. Minimal change (PRIN-IX) - **PASS** (8-line hook change + regression test; no drive-by)

**Verdict: PASS** (0 FAIL, 0 WATCH). Ready for PR.

## Entries

- `14:13 · claude/OPUS · REVIEW GATE: security PASS / scope APPROVED / code no-CRITICAL-HIGH (1 MEDIUM worklog -> this file; 1 LOW plantId-path accepted, documented) · /review · QG-004`
- `14:12 · claude/OPUS · GREEN: removed setLoading(true) from useCareSchedules.reload() so loading reflects the INITIAL load only; mutation refetch is now silent and sibling sections stay mounted. Full FE gate green: lint/format/typecheck clean, 234 vitest pass, build OK · useCareSchedules.ts · PRIN-III/PRIN-IX`
- `14:10 · claude/OPUS · RED (TEST-014): new CareScheduleModal test "keeps unsaved Water values after the Feed section is saved" fails against unfixed code - expect(interval).toHaveValue(7) received null (Water section remounted + reset when Feed save triggered the loading-placeholder swap) · CareScheduleModal.test.tsx · PRIN-III`
- `14:09 · claude/OPUS · root cause confirmed (evidence: reproduced): reload() sets loading=true on every upsert/remove; CareScheduleModal gates the whole section list on loading, unmounting both ScheduleSections behind the placeholder; on remount each re-inits from server data, discarding the sibling's unsaved local state. usePhotos shares the shape but has no unsaved-form child to lose · useCareSchedules.ts, CareScheduleModal.tsx · -`
- `14:08 · claude/OPUS · intake: filed BUG-007 from template (severity high, evidence reproduced); dedupe vs BUG-001..006 = none · bugs/BUG-007-care-schedule-unsaved-loss.md · VIRIDARIUM-72`
